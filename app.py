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
# 1. పేజీ సెట్టింగ్స్ & పర్మనెంట్ స్టేట్స్
# ==========================================
st.set_page_config(
    page_title="ఆధ్యాత్మిక వాయిస్ యంత్రం", 
    layout="wide", 
    page_icon="🕉️"
)

# కస్టమ్ డయాగ్నొస్టిక్స్ & UI స్టైల్స్
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mandali&display=swap');
    * { font-family: 'Mandali', 'Segoe UI', Tahoma, sans-serif; }
    .diag-box {
        background-color: #0f172a;
        color: #38bdf8;
        border-radius: 10px;
        padding: 12px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        height: 150px;
        overflow-y: auto;
        border: 1px solid #334155;
    }
    .diag-log { margin-bottom: 4px; line-height: 1.4; border-bottom: 1px solid #1e293b; padding-bottom: 2px; }
    .log-time { color: #94a3b8; font-size: 11px; margin-right: 6px; }
</style>
""", unsafe_allow_html=True)

st.header("🔱 ఆధ్యాత్మిక వాయిస్ సిస్టమ్")
st.caption("వాయిస్ కన్వర్షన్ (TTS), ఆడియో టు టెక్స్ట్ (STT), DSP వాయిస్ బూస్టర్, HTML అనువాద పేజీ, PDF, Word & Copy - 100% పరిపూర్ణ వ్యవస్థ")

# సెషన్ స్టేట్స్
if "main_text" not in st.session_state:
    st.session_state.main_text = ""
if "audio_bytes_data" not in st.session_state:
    st.session_state.audio_bytes_data = None
if "last_mic_text" not in st.session_state:
    st.session_state.last_mic_text = ""
if "diag_logs" not in st.session_state:
    st.session_state.diag_logs = [
        {"time": datetime.now().strftime("%H:%M:%S"), "msg": "సిస్టమ్ సిద్ధంగా ఉంది. DSP ఆడియో ఫిల్టర్లు & STT ఇంజిన్ యాక్టివ్‌గా ఉన్నాయి.", "color": "#38bdf8"}
    ]

def add_log(msg, color="#38bdf8"):
    t_str = datetime.now().strftime("%H:%M:%S")
    st.session_state.diag_logs.append({"time": t_str, "msg": msg, "color": color})


# ==========================================
# 2. కోర్ హెల్పర్ & DSP ఫంక్షన్లు
# ==========================================

def apply_audio_dsp(audio_segment: AudioSegment) -> AudioSegment:
    """మృదువైన, పల్చటి స్త్రీ గొంతులను స్పష్టంగా మార్చే DSP ఫిల్టర్లు"""
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
    html_content = f"""
    <!DOCTYPE html>
    <html lang="te">
    <head>
        <meta charset="utf-8">
        <title>Spiritual Note</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 16px;
                line-height: 1.6;
                padding: 30px;
                color: #000;
            }}
            @media print {{
                body {{ padding: 0; }}
            }}
        </style>
    </head>
    <body onload="window.print()">
        <h2>🕉️ ఆధ్యాత్మిక నోట్</h2>
        <hr>
        <div>{formatted_body}</div>
    </body>
    </html>
    """
    return html_content


# ==========================================
# 3. ఇన్‌పుట్ విభాగం (డాక్స్, ఆడియో STT & లైవ్ మైక్)
# ==========================================
st.divider()
c_file, c_audio_stt, c_mic = st.columns([0.34, 0.33, 0.33])

# 1. డాక్యుమెంట్ ఫైల్ అప్‌లోడ్
with c_file:
    st.markdown("**📁 మీ ఫైల్‌ను అప్‌లోడ్ చేయండి (.docx, .txt):**")
    uploaded_file = st.file_uploader(
        "గరిష్ఠ సైజు 10MB వరకు అనుకూలం", 
        type=["docx", "txt"],
        key="doc_file_uploader",
        help="కేవలం Microsoft Word (.docx) లేదా Text (.txt) ఫైల్స్ మాత్రమే సపోర్ట్ చేయబడతాయి."
    )
    
    if uploaded_file is not None:
        max_mb = 10
        if uploaded_file.size > max_mb * 1024 * 1024:
            st.error(f"⚠️ ఫైల్ సైజు {max_mb} MB కంటే తక్కువగా ఉండాలి!")
        else:
            try:
                f_text = extract_text_from_file(uploaded_file)
                if f_text and f_text != st.session_state.main_text:
                    st.session_state.main_text = f_text
                    add_log(f"డాక్యుమెంట్ లోడ్ అయింది: {uploaded_file.name}", "#4ade80")
                    st.success(f"✅ '{uploaded_file.name}' విజయవంతంగా లోడ్ అయింది!")
            except Exception as fe:
                add_log(f"డాక్యుమెంట్ ఎర్రర్: {fe}", "#f87171")
                st.error(f"ఫైల్ చదవడంలో లోపం: {fe}")

# 2. ఆడియో ఫైల్ టు టెక్స్ట్ (Audio STT)
with c_audio_stt:
    st.markdown("**🎵 ఆడియో ఫైల్ టు టెక్స్ట్ (STT):**")
    uploaded_audio = st.file_uploader(
        "ఆడియో ఫైల్ (.mp3, .wav, .m4a)", 
        type=["mp3", "wav", "m4a", "ogg"],
        key="audio_stt_file_uploader"
    )
    use_dsp = st.checkbox("✨ DSP వాయిస్ బూస్టర్ (ఆన్)", value=True)
    
    if uploaded_audio is not None:
        if st.button("🚀 ఆడియోని టెక్స్ట్‌గా మార్చు", use_container_width=True):
            add_log(f"ఆడియో ప్రాసెసింగ్ ప్రారంభం: {uploaded_audio.name}", "#c084fc")
            with st.spinner("ఆడియోను టెక్స్ట్‌గా మారుస్తోంది... దయచేసి వేచి ఉండండి..."):
                transcribed_txt = transcribe_audio_file(uploaded_audio, lang_code="te-IN", enable_dsp=use_dsp)
                if transcribed_txt and not transcribed_txt.startswith("⚠️"):
                    st.session_state.main_text = (st.session_state.main_text + " " + transcribed_txt).strip()
                    add_log(f"టెక్స్ట్ గుర్తించబడింది ({len(transcribed_txt)} అక్షరాలు)", "#4ade80")
                    st.success("✅ ఆడియో విజయవంతంగా టెక్స్ట్‌గా మార్చబడింది!")
                    st.rerun()
                else:
                    add_log(f"STT లోపం: {transcribed_txt}", "#f87171")
                    st.error(transcribed_txt)

# 3. లైవ్ మైక్రోఫోన్
with c_mic:
    st.markdown("**🎙️ మైక్రోఫోన్ ద్వారా మాట్లాడండి (Live Voice Typing):**")
    mic_lang = st.selectbox("మాట్లాడే భాష:", options=["తెలుగు (Telugu)", "హిందీ (Hindi)", "ఇంగ్లీష్ (English)"])
    mic_code_map = {"తెలుగు (Telugu)": "te-IN", "హిందీ (Hindi)": "hi-IN", "ఇంగ్లీష్ (English)": "en-IN"}
    
    spoken_result = speech_to_text(
        start_prompt="🎙️ మాట్లాడటం ప్రారంభించండి (Start)",
        stop_prompt="⏹️ ఆపండి (Stop)",
        language=mic_code_map[mic_lang],
        use_container_width=True,
        key='perfect_mic_recorder'
    )
    
    if spoken_result and spoken_result != st.session_state.last_mic_text:
        st.session_state.main_text = (st.session_state.main_text + " " + spoken_result).strip()
        st.session_state.last_mic_text = spoken_result
        add_log(f"లైవ్ మాట: '{spoken_result}'", "#4ade80")
        st.rerun()

# ==========================================
# 4. డయాగ్నొస్టిక్స్ మానిటర్ కన్సోల్
# ==========================================
with st.expander("🔍 లైవ్ డయాగ్నొస్టిక్స్ & ఈవెంట్ మానిటర్ (Diagnostics Console)", expanded=True):
    log_html = "<div class='diag-box'>"
    for item in st.session_state.diag_logs[-15:]:
        log_html += f"<div class='diag-log'><span class='log-time'>[{item['time']}]</span> <span style='color:{item['color']};'>{item['msg']}</span></div>"
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)
    if st.button("🗑️ లాగ్స్ క్లియర్ చేయి"):
        st.session_state.diag_logs = [{"time": datetime.now().strftime("%H:%M:%S"), "msg": "లాగ్స్ క్లియర్ చేయబడ్డాయి.", "color": "#38bdf8"}]
        st.rerun()

# ప్రధాన టెక్స్ట్ ఏరియా
user_input_text = st.text_area(
    "ఆడియో/ఫైల్స్‌గా మార్చాలనుకుంటున్న టెక్స్ట్:", 
    value=st.session_state.main_text, 
    height=180,
    placeholder="ఇక్కడ టెక్స్ట్ పేస్ట్ చేయండి లేదా పైన ఉన్న మైక్రోఫోన్ / ఫైల్ అప్‌లోడ్ ఉపయోగించండి..."
)

if user_input_text != st.session_state.main_text:
    st.session_state.main_text = user_input_text


# ==========================================
# 5. ఆడియో ఎంపికలు & ఆప్షనల్ కంట్రోల్స్
# ==========================================
st.divider()
col_lang, col_voice = st.columns([0.5, 0.5])

with col_lang:
    selected_lang = st.selectbox("🌐 ఆడియో భాషను ఎంచుకోండి:", options=["తెలుగు (Telugu)", "హిందీ (Hindi)", "ఇంగ్లీష్ (English)"])

with col_voice:
    if "తెలుగు" in selected_lang:
        voice_option = st.radio("🎙️ స్వరాన్ని ఎంచుకోండి:", options=["👨 మోహన్ (పురుష)", "👩 శ్రుతి (స్త్రీ)"], horizontal=True)
    elif "హిందీ" in selected_lang:
        voice_option = st.radio("🎙️ స్వరాన్ని ఎంచుకోండి:", options=["👨 మధుర్ (పురుష)", "👩 స్వర్ణ (స్త్రీ)"], horizontal=True)
    else:
        voice_option = st.radio("🎙️ స్వరాన్ని ఎంచుకోండి:", options=["👨 ప్రభాత్ (పురుష)", "👩 నీరజ (స్త్రీ)"], horizontal=True)

# 🎛️ ఆప్షనల్ ఆడియో సెట్టింగ్స్
with st.expander("⚙️ ఆప్షనల్ ఆడియో సెట్టింగ్స్ (స్పీడ్, పిచ్ & BGM ఫైన్-ట్యూనింగ్)"):
    col_opt_speed, col_opt_pitch, col_opt_pause = st.columns(3)
    
    with col_opt_speed:
        audio_speed = st.select_slider("🔊 ప్లే స్పీడ్ (Play Speed):", options=[0.75, 0.85, 1.0, 1.15, 1.25, 1.5], value=0.85)
    
    with col_opt_pitch:
        pitch_custom = st.select_slider("🎚️ వాయిస్ గంభీరత (Pitch/Base):", options=["సాధారణ (Normal)", "గంభీరం (Deep Base)", "అత్యంత గంభీరం (Heavy Base)"], value="సాధారణ (Normal)")
        
    with col_opt_pause:
        pause_duration = st.slider("⏸️ వాక్యాల మధ్య విరామం (Pause Sec):", min_value=0.3, max_value=2.0, value=0.6, step=0.1)
        
    col_bgm_1, col_bgm_2 = st.columns([0.4, 0.6])
    with col_bgm_1:
        enable_bgm = st.checkbox("🎶 BGM (బ్యాక్‌గ్రౌండ్ మ్యూజిక్) జోడించు", value=True)
    with col_bgm_2:
        bgm_volume = st.slider("🎵 BGM శబ్దం (Volume %):", min_value=2, max_value=20, value=6)


# ==========================================
# 6. ఆరు ప్రధాన ఆప్షన్ల వరుస (Action Controls)
# ==========================================
st.markdown("##### 🎯 యాక్షన్ కంట్రోల్స్ (Action Controls)")

active_text = st.session_state.main_text.strip()

c1, c2, c3, c4, c5, c6 = st.columns([0.18, 0.18, 0.16, 0.16, 0.16, 0.16])

# 1. 🔊 ఆడియో బటన్
with c1:
    convert_btn = st.button("🔊 ఆడియో చేయి", type="primary", use_container_width=True)

# 2. 🌐 HTML ట్రాన్స్‌లేట్ పేజీ (బ్రౌజర్‌లో ఆటో-ట్రాన్స్‌లేట్ కోసం)
with c2:
    if active_text:
        html_trans_page = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body><p style='font-size:18px; line-height:1.6;'>{active_text.replace(chr(10), '<br>')}</p></body></html>"
        st.download_button(
            label="🌐 HTML (ట్రాన్స్‌లేట్)",
            data=html_trans_page.encode('utf-8'),
            file_name="translate_page.html",
            mime="text/html",
            use_container_width=True,
            help="బ్రౌజర్‌లో ఓపెన్ చేసి సులభంగా అనువదించుకోవచ్చు"
        )
    else:
        st.button("🌐 HTML (ట్రాన్స్‌లేట్)", disabled=True, use_container_width=True)

# 3. 📄 ప్రింటబుల్ PDF
with c3:
    if active_text:
        printable_pdf = create_printable_pdf_html(active_text)
        st.download_button(
            label="📄 PDF ఫైల్",
            data=printable_pdf.encode('utf-8'),
            file_name="spiritual_note.html",
            mime="text/html",
            use_container_width=True,
            help="డైరెక్ట్‌గా ప్రింట్ లేదా PDF గా సేవ్ అవుతుంది"
        )
    else:
        st.button("📄 PDF ఫైల్", disabled=True, use_container_width=True)

# 4. 📝 Word (.docx) బటన్
with c4:
    if active_text:
        docx_data = create_docx_bytes(active_text)
        st.download_button(
            label="📝 Word ఫైల్",
            data=docx_data,
            file_name="spiritual_note.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    else:
        st.button("📝 Word ఫైల్", disabled=True, use_container_width=True)

# 5. 📋 కాపీ బటన్
with c5:
    if active_text:
        if st.button("📋 కాపీ", use_container_width=True):
            st.code(active_text, language=None)
            add_log("టెక్స్ట్ క్లిప్‌బోర్డ్‌కు సిద్ధమైంది.", "#facc15")
            st.toast("✅ పైన ఉన్న టెక్స్ట్‌ని క్లిక్ చేసి కాపీ చేసుకోండి!", icon="📋")
    else:
        st.button("📋 కాపీ", disabled=True, use_container_width=True)

# 6. 🧹 క్లియర్ బటన్
with c6:
    if st.button("🧹 క్లియర్", use_container_width=True):
        st.session_state.main_text = ""
        st.session_state.audio_bytes_data = None
        st.session_state.last_mic_text = ""
        add_log("డేటా క్లియర్ చేయబడింది.", "#facc15")
        gc.collect()
        st.rerun()


# ==========================================
# 7. హై-స్పీడ్ TTS ఆడియో ప్రాసెసింగ్ లాజిక్
# ==========================================
if convert_btn:
    if active_text:
        add_log("TTS ప్రాసెసింగ్ మొదలైంది...", "#c084fc")
        with st.spinner("ఆడియో వేగంగా ప్రాసెస్ అవుతోంది... దయచేసి వేచి ఉండండి..."):
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
                    add_log("TTS ఆడియో ఫైల్ సిద్ధమైంది!", "#4ade80")
                    gc.collect()
                    st.success("🎉 ఆడియో విజయవంతంగా సిద్ధమైంది!")
                else:
                    add_log("ఆడియో జనరేషన్ విఫలమైంది.", "#f87171")
                    st.error("❌ ఆడియో డేటా ఏదీ జనరేట్ కాలేదు!")

            except Exception as e:
                add_log(f"TTS లోపం: {e}", "#f87171")
                st.error("❌ ఆడియో సిస్టమ్‌లో లోపం వచ్చింది:")
                st.code(traceback.format_exc())
    else:
        st.warning("దయచేసి టెక్స్ట్ ఎంటర్ చేయండి లేదా మాట్లాడండి.")

# 📥 స్థిరమైన ఆడియో ప్లేయర్ & డౌన్‌లోడ్
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
