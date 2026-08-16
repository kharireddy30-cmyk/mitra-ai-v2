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
# 1. పేజీ సెట్టింగ్స్ & UI స్టైల్స్
# ==========================================
st.set_page_config(
    page_title="BRAHMA AI", 
    layout="wide", 
    page_icon="🕉️"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mandali&display=swap');
    * { font-family: 'Mandali', 'Segoe UI', Tahoma, sans-serif; }
    .diag-box {
        background-color: #0f172a;
        color: #38bdf8;
        border-radius: 8px;
        padding: 10px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 12px;
        height: 130px;
        overflow-y: auto;
        border: 1px solid #334155;
    }
    .diag-log { margin-bottom: 3px; line-height: 1.3; border-bottom: 1px solid #1e293b; padding-bottom: 2px; }
    .log-time { color: #94a3b8; font-size: 11px; margin-right: 6px; }
    
    /* మొబైల్ బటన్ సైజ్ ఆప్టిమైజేషన్ */
    div.stButton > button, div.stDownloadButton > button {
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

st.subheader("🕉️ BRAHMA AI : Studio")

# సెషన్ స్టేట్స్
if "main_text" not in st.session_state:
    st.session_state.main_text = ""
if "audio_bytes_data" not in st.session_state:
    st.session_state.audio_bytes_data = None
if "last_mic_text" not in st.session_state:
    st.session_state.last_mic_text = ""
if "diag_logs" not in st.session_state:
    st.session_state.diag_logs = [
        {"time": datetime.now().strftime("%H:%M:%S"), "msg": "System Ready. DSP & STT Online.", "color": "#38bdf8"}
    ]

def add_log(msg, color="#38bdf8"):
    t_str = datetime.now().strftime("%H:%M:%S")
    st.session_state.diag_logs.append({"time": t_str, "msg": msg, "color": color})


# ==========================================
# 2. కోర్ హెల్పర్ & DSP ఫంక్షన్లు
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
        return "⚠️ Voice not recognized"
    except Exception as e:
        return f"⚠️ Error: {e}"
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
    html_content = f"""<!DOCTYPE html>
<html lang="te">
<head>
    <meta charset="utf-8">
    <title>Print Document</title>
    <style>
        body {{ font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6; padding: 25px; color: #000; }}
        @media print {{ body {{ padding: 0; }} }}
    </style>
</head>
<body onload="window.print()">
    <div>{formatted_body}</div>
</body>
</html>"""
    return html_content


# ==========================================
# 3. ఇన్ పుట్ విభాగం (DOC | STT | MIC)
# ==========================================
c_file, c_audio_stt, c_mic = st.columns([0.33, 0.34, 0.33])

# 1. DOC / TXT
with c_file:
    st.markdown("**📁 DOC / TXT**")
    uploaded_file = st.file_uploader("Upload DOCX/TXT", type=["docx", "txt"], key="doc_file_uploader", label_visibility="collapsed")
    if uploaded_file is not None:
        try:
            f_text = extract_text_from_file(uploaded_file)
            if f_text and f_text != st.session_state.main_text:
                st.session_state.main_text = f_text
                add_log(f"DOC Loaded: {uploaded_file.name}", "#4ade80")
                st.toast(f"✅ {uploaded_file.name} Loaded!")
        except Exception as fe:
            add_log(f"DOC Error: {fe}", "#f87171")
            st.error(f"Error: {fe}")

# 2. AUDIO STT
with c_audio_stt:
    st.markdown("**🎵 AUDIO STT**")
    uploaded_audio = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a", "ogg"], key="audio_stt_file_uploader", label_visibility="collapsed")
    use_dsp = st.checkbox("✨ DSP Booster", value=True)
    
    if uploaded_audio is not None:
        if st.button("🚀 RUN STT", use_container_width=True):
            add_log(f"STT Started: {uploaded_audio.name}", "#c084fc")
            with st.spinner("Processing STT..."):
                transcribed_txt = transcribe_audio_file(uploaded_audio, lang_code="te-IN", enable_dsp=use_dsp)
                if transcribed_txt and not transcribed_txt.startswith("⚠️"):
                    st.session_state.main_text = (st.session_state.main_text + " " + transcribed_txt).strip()
                    add_log(f"STT Success ({len(transcribed_txt)} chars)", "#4ade80")
                    st.toast("✅ STT Complete!")
                    st.rerun()
                else:
                    add_log(f"STT Error: {transcribed_txt}", "#f87171")
                    st.error(transcribed_txt)

# 3. LIVE MIC
with c_mic:
    st.markdown("**🎙️ LIVE MIC**")
    mic_lang = st.selectbox("Lang:", options=["TE (తెలుగు)", "HI (हिंदी)", "EN (English)"], label_visibility="collapsed")
    mic_code_map = {"TE (తెలుగు)": "te-IN", "HI (हिंदी)": "hi-IN", "EN (English)": "en-IN"}
    
    spoken_result = speech_to_text(
        start_prompt="🎙️ START",
        stop_prompt="⏹️ STOP",
        language=mic_code_map[mic_lang],
        use_container_width=True,
        key='perfect_mic_recorder'
    )
    
    if spoken_result and spoken_result != st.session_state.last_mic_text:
        st.session_state.main_text = (st.session_state.main_text + " " + spoken_result).strip()
        st.session_state.last_mic_text = spoken_result
        add_log(f"MIC: '{spoken_result}'", "#4ade80")
        st.rerun()

# ==========================================
# 4. DIAGNOSTICS CONSOLE
# ==========================================
with st.expander("🔍 DIAGNOSTICS", expanded=False):
    log_html = "<div class='diag-box'>"
    for item in st.session_state.diag_logs[-15:]:
        log_html += f"<div class='diag-log'><span class='log-time'>[{item['time']}]</span> <span style='color:{item['color']};'>{item['msg']}</span></div>"
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)
    if st.button("🗑️ CLEAR LOGS", use_container_width=True):
        st.session_state.diag_logs = [{"time": datetime.now().strftime("%H:%M:%S"), "msg": "Logs cleared.", "color": "#38bdf8"}]
        st.rerun()

# ==========================================
# 5. MAIN TEXT EDITOR
# ==========================================
user_input_text = st.text_area(
    "Content Editor", 
    value=st.session_state.main_text, 
    height=160,
    placeholder="Text content here...",
    label_visibility="collapsed"
)

if user_input_text != st.session_state.main_text:
    st.session_state.main_text = user_input_text


# ==========================================
# 6. ACTION CONTROLS (ROW 1 & ROW 2)
# ==========================================
active_text = st.session_state.main_text.strip()

# బటన్లను మొబైల్‌లో 3 + 3 గ్రిడ్‌గా అమర్చాం
b1, b2, b3 = st.columns(3)
b4, b5, b6 = st.columns(3)

# Row 1
with b1:
    convert_btn = st.button("🔊 TTS", type="primary", use_container_width=True)

with b2:
    if active_text:
        html_trans_page = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body><p style='font-size:18px; line-height:1.6;'>{active_text.replace(chr(10), '<br>')}</p></body></html>"
        st.download_button("🌐 HTML", data=html_trans_page.encode('utf-8'), file_name="translate_page.html", mime="text/html", use_container_width=True)
    else:
        st.button("🌐 HTML", disabled=True, use_container_width=True)

with b3:
    if active_text:
        printable_pdf = create_printable_pdf_html(active_text)
        st.download_button("📄 PDF", data=printable_pdf.encode('utf-8'), file_name="note.html", mime="text/html", use_container_width=True)
    else:
        st.button("📄 PDF", disabled=True, use_container_width=True)

# Row 2
with b4:
    if active_text:
        docx_data = create_docx_bytes(active_text)
        st.download_button("📝 DOCX", data=docx_data, file_name="note.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else:
        st.button("📝 DOCX", disabled=True, use_container_width=True)

with b5:
    if active_text:
        if st.button("📋 COPY", use_container_width=True):
            st.code(active_text, language=None)
            add_log("Text ready to copy.", "#facc15")
            st.toast("✅ Ready to copy!", icon="📋")
    else:
        st.button("📋 COPY", disabled=True, use_container_width=True)

with b6:
    if st.button("🧹 CLEAR", use_container_width=True):
        st.session_state.main_text = ""
        st.session_state.audio_bytes_data = None
        st.session_state.last_mic_text = ""
        add_log("Cleared.", "#facc15")
        gc.collect()
        st.rerun()


# ==========================================
# 7. VOICE & AUDIO SETTINGS
# ==========================================
with st.expander("⚙️ SETTINGS (Voice, Speed, Pitch & BGM)", expanded=False):
    col_lang, col_voice = st.columns(2)
    with col_lang:
        selected_lang = st.selectbox("Language:", options=["Telugu", "Hindi", "English"])

    with col_voice:
        if "Telugu" in selected_lang:
            voice_option = st.radio("Voice:", options=["👨 Mohan", "👩 Shruti"], horizontal=True)
        elif "Hindi" in selected_lang:
            voice_option = st.radio("Voice:", options=["👨 Madhur", "👩 Swara"], horizontal=True)
        else:
            voice_option = st.radio("Voice:", options=["👨 Prabhat", "👩 Neerja"], horizontal=True)

    col_opt_speed, col_opt_pitch, col_opt_pause = st.columns(3)
    with col_opt_speed:
        audio_speed = st.select_slider("Speed:", options=[0.75, 0.85, 1.0, 1.15, 1.25, 1.5], value=0.85)
    with col_opt_pitch:
        pitch_custom = st.select_slider("Pitch:", options=["Normal", "Deep Base", "Heavy Base"], value="Normal")
    with col_opt_pause:
        pause_duration = st.slider("Pause (Sec):", min_value=0.3, max_value=2.0, value=0.6, step=0.1)
        
    col_bgm_1, col_bgm_2 = st.columns([0.4, 0.6])
    with col_bgm_1:
        enable_bgm = st.checkbox("🎶 Enable BGM", value=True)
    with col_bgm_2:
        bgm_volume = st.slider("BGM Vol (%):", min_value=2, max_value=20, value=6)


# ==========================================
# 8. TTS ENGINE
# ==========================================
if convert_btn:
    if active_text:
        add_log("TTS Processing...", "#c084fc")
        with st.spinner("Generating Voice..."):
            try:
                clean_txt = re.sub(r'[*#_~`]', '', active_text)
                
                voice_map = {
                    "👨 Mohan": "te-IN-MohanNeural",
                    "👩 Shruti": "te-IN-ShrutiNeural",
                    "👨 Madhur": "hi-IN-MadhurNeural",
                    "👩 Swara": "hi-IN-SwaraNeural",
                    "👨 Prabhat": "en-IN-PrabhatNeural",
                    "👩 Neerja": "en-IN-NeerjaNeural"
                }
                selected_voice = voice_map[voice_option]

                rate_str = f"{int((audio_speed - 1.0) * 100):+d}%"
                pitch_val_map = {
                    "Normal": "+0Hz",
                    "Deep Base": "-5Hz",
                    "Heavy Base": "-10Hz"
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
                    add_log("TTS Complete!", "#4ade80")
                    gc.collect()
                    st.toast("🎉 TTS Ready!")
                else:
                    add_log("TTS Failed.", "#f87171")
                    st.error("❌ Audio Generation Failed")

            except Exception as e:
                add_log(f"TTS Error: {e}", "#f87171")
                st.error("❌ TTS Error:")
                st.code(traceback.format_exc())
    else:
        st.warning("Please enter text or record audio.")

# AUDIO PLAYER & DOWNLOAD
if st.session_state.audio_bytes_data is not None:
    st.divider()
    st.audio(st.session_state.audio_bytes_data, format="audio/mp3")
    st.download_button(
        label="📥 DOWNLOAD MP3", 
        data=st.session_state.audio_bytes_data, 
        file_name="audio.mp3", 
        mime="audio/mp3",
        key="permanent_download_btn",
        use_container_width=True
    )
