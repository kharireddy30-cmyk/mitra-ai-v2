import streamlit as st
import edge_tts
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range, high_pass_filter, low_pass_filter
import speech_recognition as sr
import asyncio
import io
import re
import os
import gc
import traceback
from datetime import datetime
import docx
from streamlit_mic_recorder import speech_to_text

# ==========================================
# 1. పేజీ సెట్టింగ్స్ & మొబైల్ రెస్పాన్సివ్ CSS
# ==========================================
st.set_page_config(
    page_title="ఆధ్యాత్మిక వాయిస్ యంత్రం", 
    layout="wide", 
    page_icon="🕉️",
    initial_sidebar_state="collapsed"
)

# మొబైల్ & డెస్క్‌టాప్ అడాప్టివ్ CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mandali&display=swap');
    * { font-family: 'Mandali', 'Segoe UI', sans-serif !important; }
    
    /* మొబైల్ కార్డ్ బాక్సులు */
    .input-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* డయాగ్నొస్టిక్స్ బాక్స్ */
    .diag-box {
        background-color: #0f172a;
        color: #38bdf8;
        border-radius: 10px;
        padding: 12px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        height: 140px;
        overflow-y: auto;
        border: 1px solid #334155;
    }
    .diag-log { margin-bottom: 3px; line-height: 1.4; border-bottom: 1px solid #1e293b; padding-bottom: 2px; }
    
    /* బటన్లను మొబైల్ స్క్రీన్‌పై పెద్దవిగా చేయడం */
    div.stButton > button {
        border-radius: 8px !important;
        font-size: 16px !important;
        padding: 8px 14px !important;
        font-weight: 600 !important;
    }
    div.stDownloadButton > button {
        border-radius: 8px !important;
        font-size: 15px !important;
        padding: 8px 12px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔱 ఆధ్యాత్మిక వాయిస్ సిస్టమ్")
st.caption("మొబైల్ & డెస్క్‌టాప్ అనుకూల ఆడియో, టెక్స్ట్, PDF, Word & వాయిస్ కన్వర్టర్")

# సెషన్ స్టేట్స్
if "main_text" not in st.session_state:
    st.session_state.main_text = ""
if "audio_bytes_data" not in st.session_state:
    st.session_state.audio_bytes_data = None
if "last_mic_text" not in st.session_state:
    st.session_state.last_mic_text = ""
if "diag_logs" not in st.session_state:
    st.session_state.diag_logs = [
        {"time": datetime.now().strftime("%H:%M:%S"), "msg": "సిస్టమ్ సిద్ధంగా ఉంది. మొబైల్ ఇంటర్‌ఫేస్ ఆన్ చేయబడింది.", "color": "#38bdf8"}
    ]

def add_log(msg, color="#38bdf8"):
    t_str = datetime.now().strftime("%H:%M:%S")
    st.session_state.diag_logs.append({"time": t_str, "msg": msg, "color": color})


# ==========================================
# 2. కోర్ DSP & STT ఇంజిన్
# ==========================================
def apply_audio_dsp(audio_segment: AudioSegment) -> AudioSegment:
    try:
        processed = high_pass_filter(audio_segment, cutoff=300)
        processed = low_pass_filter(processed, cutoff=3800)
        processed = compress_dynamic_range(processed, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
        processed = normalize(processed) + 6.0
        return processed
    except Exception:
        return audio_segment

def transcribe_audio_file(uploaded_audio_file, lang_code="te-IN", enable_dsp=True):
    uploaded_audio_file.seek(0)
    temp_in = "temp_stt_in.audio"
    temp_wav = "temp_stt_out.wav"
    
    with open(temp_in, "wb") as f:
        f.write(uploaded_audio_file.read())

    try:
        sound = AudioSegment.from_file(temp_in)
        if enable_dsp:
            sound = apply_audio_dsp(sound)
        
        sound = sound.set_channels(1).set_frame_rate(16000)
        sound.export(temp_wav, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            text_result = recognizer.recognize_google(audio_data, language=lang_code)
            return text_result
    except sr.UnknownValueError:
        return "⚠️ ఆడియోలోని మాటలను ఇంజిన్ గుర్తించలేకపోయింది."
    except Exception as e:
        return f"⚠️ STT ఎర్రర్: {e}"
    finally:
        for p in [temp_in, temp_wav]:
            if os.path.exists(p):
                os.remove(p)

async def generate_voice_file(text, voice, pitch_val, rate_val, output_filename):
    communicate = edge_tts.Communicate(text, voice, pitch=pitch_val, rate=rate_val)
    await communicate.save(output_filename)

def split_text_into_chunks(text, max_chars=300):
    clean_text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?\n।])\s+', clean_text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return [c.strip() for c in chunks if len(c.strip()) > 0]

def extract_text_from_file(uploaded_file):
    extracted = ""
    if uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        extracted = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    elif uploaded_file.name.endswith(".txt"):
        extracted = uploaded_file.read().decode("utf-8")
    return extracted

def create_docx_bytes(text):
    doc = docx.Document()
    for paragraph in text.split("\n"):
        if paragraph.strip():
            doc.add_paragraph(paragraph.strip())
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()

def create_printable_pdf_html(text):
    formatted_body = text.replace('\n', '<br>')
    return f"""<!DOCTYPE html><html lang="te"><head><meta charset="utf-8"><title>Spiritual Note</title>
    <style>body {{ font-family: Arial, sans-serif; font-size: 18px; line-height: 1.8; padding: 25px; color: #000; }}</style></head>
    <body onload="window.print()"><h2>🕉️ ఆధ్యాత్మిక నోట్</h2><hr><div>{formatted_body}</div></body></html>"""


# ==========================================
# 3. ఇన్‌పుట్ కార్డ్స్ విభాగం (మొబైల్ అనుకూలం)
# ==========================================
st.markdown("### 📥 ఇన్‌పుట్ ఎంపికలు")

tab_audio, tab_doc, tab_mic = st.tabs(["🎵 1. ఆడియో ఫైల్ (MP3/WAV)", "📁 2. టెక్స్ట్ ఫైల్ (.docx/.txt)", "🎙️ 3. లైవ్ మైక్రోఫోన్"])

# ట్యాబ్ 1: ఆడియో ఫైల్
with tab_audio:
    st.markdown("**ఆడియో ఫైల్‌ను అప్‌లోడ్ చేసి టెక్స్ట్‌గా మార్చండి:**")
    uploaded_audio = st.file_uploader("ఆడియో ఫైల్ ఎంచుకోండి (.mp3, .wav, .m4a)", type=["mp3", "wav", "m4a", "ogg"], key="audio_tab_uploader")
    use_dsp = st.checkbox("✨ DSP వాయిస్ బూస్టర్ (మృదువైన గొంతులను క్లియర్ చేయడానికి)", value=True, key="dsp_check")
    
    if uploaded_audio is not None:
        if st.button("🚀 ఆడియోని టెక్స్ట్‌గా మార్చు (Extract Text)", type="primary", use_container_width=True, key="btn_audio_stt"):
            add_log(f"ఆడియో ప్రాసెసింగ్: {uploaded_audio.name}", "#c084fc")
            with st.spinner("ఆడియోను టెక్స్ట్‌గా మారుస్తోంది... దయచేసి వేచి ఉండండి..."):
                transcribed_txt = transcribe_audio_file(uploaded_audio, lang_code="te-IN", enable_dsp=use_dsp)
                if transcribed_txt and not transcribed_txt.startswith("⚠️"):
                    st.session_state.main_text = (st.session_state.main_text + " " + transcribed_txt).strip()
                    add_log(f"టెక్స్ట్ వచ్చింది ({len(transcribed_txt)} అక్షరాలు)", "#4ade80")
                    st.success("✅ ఆడియో విజయవంతంగా టెక్స్ట్‌గా మార్చబడింది!")
                    st.rerun()
                else:
                    add_log(f"STT లోపం: {transcribed_txt}", "#f87171")
                    st.error(transcribed_txt)

# ట్యాబ్ 2: డాక్యుమెంట్ ఫైల్
with tab_doc:
    st.markdown("**Word లేదా Text ఫైల్ నుండి టెక్స్ట్ లోడ్ చేయండి:**")
    uploaded_file = st.file_uploader("ఫైల్ ఎంచుకోండి (.docx, .txt)", type=["docx", "txt"], key="doc_tab_uploader")
    if uploaded_file is not None:
        if st.button("📂 ఫైల్ లోపలి టెక్స్ట్‌ని తెరిచి చూపించు", type="primary", use_container_width=True, key="btn_doc_load"):
            try:
                f_text = extract_text_from_file(uploaded_file)
                if f_text:
                    st.session_state.main_text = f_text
                    add_log(f"డాక్యుమెంట్ లోడ్ అయింది: {uploaded_file.name}", "#4ade80")
                    st.success(f"✅ '{uploaded_file.name}' లోడ్ అయింది!")
                    st.rerun()
            except Exception as fe:
                add_log(f"డాక్యుమెంట్ ఎర్రర్: {fe}", "#f87171")
                st.error(f"ఫైల్ లోపం: {fe}")

# ట్యాబ్ 3: లైవ్ మైక్రోఫోన్
with tab_mic:
    st.markdown("**నోటితో మాట్లాడి టైప్ చేయండి:**")
    mic_lang = st.selectbox("మాట్లాడే భాష:", options=["తెలుగు (Telugu)", "హిందీ (Hindi)", "ఇంగ్లీష్ (English)"], key="mic_lang_select")
    mic_code_map = {"తెలుగు (Telugu)": "te-IN", "హిందీ (Hindi)": "hi-IN", "ఇంగ్లీష్ (English)": "en-IN"}
    
    spoken_result = speech_to_text(
        start_prompt="🎙️ మాట్లాడటం ప్రారంభించండి (Start)",
        stop_prompt="⏹️ ఆపండి (Stop)",
        language=mic_code_map[mic_lang],
        use_container_width=True,
        key='mobile_mic_recorder'
    )
    if spoken_result and spoken_result != st.session_state.last_mic_text:
        st.session_state.main_text = (st.session_state.main_text + " " + spoken_result).strip()
        st.session_state.last_mic_text = spoken_result
        add_log(f"లైవ్ మాట: '{spoken_result}'", "#4ade80")
        st.rerun()


# ==========================================
# 4. ప్రధాన టెక్స్ట్ ఏరియా (మొబైల్ బిగ్ వ్యూ)
# ==========================================
st.divider()
st.markdown("### 📝 ప్రధాన టెక్స్ట్ (Main Text Content)")
user_input_text = st.text_area(
    "టెక్స్ట్ ఎడిటర్ (ఇక్కడ ఎడిట్ చేసుకోవచ్చు లేదా చదువుకోవచ్చు):", 
    value=st.session_state.main_text, 
    height=200,
    placeholder="మార్చబడిన టెక్స్ట్ ఇక్కడ కనిపిస్తుంది...",
    key="main_text_area"
)
if user_input_text != st.session_state.main_text:
    st.session_state.main_text = user_input_text


# ==========================================
# 5. ఆరు ప్రధాన యాక్షన్ కంట్రోల్స్ (మొబైల్ రెస్పాన్సివ్ గ్రిడ్)
# ==========================================
st.markdown("### 🎯 యాక్షన్ కంట్రోల్స్")
active_text = st.session_state.main_text.strip()

# మొబైల్‌లో 2 వరుసలుగా 3+3 బటన్లు స్పష్టంగా కనిపించేలా సెట్ చేశాం
row1_col1, row1_col2, row1_col3 = st.columns(3)
row2_col1, row2_col2, row2_col3 = st.columns(3)

# Row 1
with row1_col1:
    convert_btn = st.button("🔊 ఆడియో చేయి", type="primary", use_container_width=True)

with row1_col2:
    if active_text:
        html_trans_page = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body><p style='font-size:20px; line-height:1.8;'>{active_text.replace(chr(10), '<br>')}</p></body></html>"
        st.download_button("🌐 HTML పేజీ", data=html_trans_page.encode('utf-8'), file_name="translate_page.html", mime="text/html", use_container_width=True)
    else:
        st.button("🌐 HTML పేజీ", disabled=True, use_container_width=True)

with row1_col3:
    if active_text:
        printable_pdf = create_printable_pdf_html(active_text)
        st.download_button("📄 PDF ఫైల్", data=printable_pdf.encode('utf-8'), file_name="spiritual_note.html", mime="text/html", use_container_width=True)
    else:
        st.button("📄 PDF ఫైల్", disabled=True, use_container_width=True)

# Row 2
with row2_col1:
    if active_text:
        docx_data = create_docx_bytes(active_text)
        st.download_button("📝 Word (.docx)", data=docx_data, file_name="spiritual_note.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else:
        st.button("📝 Word (.docx)", disabled=True, use_container_width=True)

with row2_col2:
    if active_text:
        if st.button("📋 టెక్స్ట్ కాపీ", use_container_width=True):
            st.code(active_text, language=None)
            st.toast("✅ టెక్స్ట్‌ని కాపీ చేసుకోండి!", icon="📋")
    else:
        st.button("📋 టెక్స్ట్ కాపీ", disabled=True, use_container_width=True)

with row2_col3:
    if st.button("🧹 క్లియర్", use_container_width=True):
        st.session_state.main_text = ""
        st.session_state.audio_bytes_data = None
        st.session_state.last_mic_text = ""
        add_log("డేటా క్లియర్ చేయబడింది.", "#facc15")
        gc.collect()
        st.rerun()


# ==========================================
# 6. ఆడియో ఎంపికలు & కస్టమైజేషన్
# ==========================================
with st.expander("⚙️ వాయిస్ సెట్టింగ్స్ & BGM (స్వరాలు, పిచ్, స్పీడ్)", expanded=False):
    col_lang, col_voice = st.columns(2)
    with col_lang:
        selected_lang = st.selectbox("🌐 వాయిస్ భాష:", options=["తెలుగు (Telugu)", "హిందీ (Hindi)", "ఇంగ్లీష్ (English)"])
    with col_voice:
        if "తెలుగు" in selected_lang:
            voice_option = st.radio("🎙️ స్వరం:", options=["👨 మోహన్ (పురుష)", "👩 శ్రుతి (స్త్రీ)"], horizontal=True)
        elif "హిందీ" in selected_lang:
            voice_option = st.radio("🎙️ స్వరం:", options=["👨 మధుర్ (పురుష)", "👩 స్వర్ణ (స్త్రీ)"], horizontal=True)
        else:
            voice_option = st.radio("🎙️ స్వరం:", options=["👨 ప్రభాత్ (పురుష)", "👩 నీరజ (స్త్రీ)"], horizontal=True)

    col_opt_speed, col_opt_pitch, col_opt_pause = st.columns(3)
    with col_opt_speed:
        audio_speed = st.select_slider("🔊 స్పీడ్:", options=[0.75, 0.85, 1.0, 1.15, 1.25, 1.5], value=0.85)
    with col_opt_pitch:
        pitch_custom = st.select_slider("🎚️ పిచ్:", options=["సాధారణ (Normal)", "గంభీరం (Deep Base)", "అత్యంత గంభీరం (Heavy Base)"], value="సాధారణ (Normal)")
    with col_opt_pause:
        pause_duration = st.slider("⏸️ విరామం (సెకన్లు):", min_value=0.3, max_value=2.0, value=0.6, step=0.1)
        
    col_bgm_1, col_bgm_2 = st.columns([0.4, 0.6])
    with col_bgm_1:
        enable_bgm = st.checkbox("🎶 BGM జోడించు", value=True)
    with col_bgm_2:
        bgm_volume = st.slider("🎵 BGM సౌండ్ (%):", min_value=2, max_value=20, value=6)


# ==========================================
# 7. TTS వాయిస్ జనరేషన్ లాజిక్
# ==========================================
if convert_btn:
    if active_text:
        add_log("TTS వాయిస్ తయారీ ప్రారంభమైంది...", "#c084fc")
        with st.spinner("ఆడియో సిద్ధమవుతోంది... దయచేసి వేచి ఉండండి..."):
            try:
                clean_txt = re.sub(r'[*#_~`]', '', active_text)
                voice_map = {
                    "👨 మోహన్ (పురుష)": "te-IN-MohanNeural",
                    "👩 శ్రుతి (స్త్రీ)": "te-IN-ShrutiNeural",
                    "👨 మధుర్ (పురుష)": "hi-IN-MadhurNeural",
                    "👩 స్వర్ణ (స్త్రీ)": "hi-IN-SwaraNeural",
                    "👨 ప్రభాత్ (పురుష)": "en-IN-PrabhatNeural",
                    "👩 నీరజ (స్త్రీ)": "en-IN-NeerjaNeural"
                }
                selected_voice = voice_map[voice_option]
                rate_str = f"{int((audio_speed - 1.0) * 100):+d}%"
                pitch_val_map = {
                    "సాధారణ (Normal)": "+0Hz",
                    "గంభీరం (Deep Base)": "-5Hz",
                    "అత్యంత గంభీరం (Heavy Base)": "-10Hz"
                }
                pitch_str = pitch_val_map[pitch_custom]

                text_chunks = split_text_into_chunks(clean_txt, max_chars=300)
                speech_sound = AudioSegment.empty()
                silence_pause = AudioSegment.silent(duration=int(pause_duration * 1000))

                for i, chunk in enumerate(text_chunks):
                    temp_file = f"temp_{i}.mp3"
                    try:
                        asyncio.run(generate_voice_file(chunk, selected_voice, pitch_str, rate_str, temp_file))
                        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                            chunk_sound = AudioSegment.from_file(temp_file)
                            speech_sound += chunk_sound + silence_pause
                            os.remove(temp_file)
                    except Exception:
                        pass

                if len(speech_sound) > 0:
                    final_sound = speech_sound
                    if enable_bgm and os.path.exists("bgm.mp3"):
                        try:
                            bgm_sound = AudioSegment.from_file("bgm.mp3")
                            if len(bgm_sound) < len(speech_sound):
                                bgm_sound = bgm_sound * ((len(speech_sound) // len(bgm_sound)) + 1)
                            bgm_sound = bgm_sound[:len(speech_sound) + 1000]
                            reduction_db = 22 - (bgm_volume * 1.5)
                            bgm_sound = bgm_sound - reduction_db
                            final_sound = speech_sound.overlay(bgm_sound)
                        except Exception:
                            pass

                    final_fp = io.BytesIO()
                    final_sound.export(final_fp, format="mp3")
                    st.session_state.audio_bytes_data = final_fp.getvalue()
                    add_log("TTS ఆడియో ఫైల్ విజయవంతంగా సిద్ధమైంది!", "#4ade80")
                    gc.collect()
                    st.success("🎉 ఆడియో విజయవంతంగా సిద్ధమైంది!")
                else:
                    st.error("❌ ఆడియో డేటా ఏదీ జనరేట్ కాలేదు!")

            except Exception as e:
                add_log(f"TTS లోపం: {e}", "#f87171")
                st.error("❌ ఆడియో సిస్టమ్‌లో లోపం వచ్చింది:")
                st.code(traceback.format_exc())
    else:
        st.warning("దయచేసి టెక్స్ట్ ఎంటర్ చేయండి లేదా మాట్లాడండి.")

# ప్లేయర్ & డౌన్‌లోడ్
if st.session_state.audio_bytes_data is not None:
    st.divider()
    st.audio(st.session_state.audio_bytes_data, format="audio/mp3")
    st.download_button(
        label="📥 MP3 ఆడియో ఫైల్‌ని డౌన్‌లోడ్ చేయండి", 
        data=st.session_state.audio_bytes_data, 
        file_name="spiritual_audio.mp3", 
        mime="audio/mp3",
        key="permanent_download_btn",
        use_container_width=True
    )

# ==========================================
# 8. డయాగ్నొస్టిక్స్ మానిటర్ (క్రింద భాగంలో)
# ==========================================
with st.expander("🔍 లైవ్ డయాగ్నొస్టిక్స్ లాగ్స్ (Diagnostics Console)", expanded=False):
    log_html = "<div class='diag-box'>"
    for item in st.session_state.diag_logs[-15:]:
        log_html += f"<div class='diag-log'><span style='color:#94a3b8;'>[{item['time']}]</span> <span style='color:{item['color']};'>{item['msg']}</span></div>"
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)
