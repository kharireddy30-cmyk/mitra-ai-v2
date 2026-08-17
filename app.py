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
from services.groq_polisher import polish_speech_script
from services.image_poster import generate_ai_poster_html

# ==========================================
# 1. పేజీ సెట్టింగ్స్ & UI స్టైల్స్
# ==========================================
st.set_page_config(
    page_title="BRAHMA AI", 
    layout="wide", 
    page_icon="🕉️",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mandali&display=swap');
    * { font-family: 'Mandali', 'Segoe UI', Tahoma, sans-serif; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    div.stButton > button, div.stDownloadButton > button {
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 6px 10px !important;
    }
    .diag-box {
        background-color: #0f172a;
        color: #38bdf8;
        border-radius: 6px;
        padding: 8px;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        height: 100px;
        overflow-y: auto;
    }
    .diag-log { margin-bottom: 2px; }
</style>
""", unsafe_allow_html=True)

st.subheader("🕉️ BRAHMA AI : Studio (Voiceover & AI Poster)")

# సెషన్ స్టేట్స్
if "main_text" not in st.session_state:
    st.session_state.main_text = ""
if "audio_bytes_data" not in st.session_state:
    st.session_state.audio_bytes_data = None
if "poster_html_data" not in st.session_state:
    st.session_state.poster_html_data = None
if "last_mic_text" not in st.session_state:
    st.session_state.last_mic_text = ""
if "diag_logs" not in st.session_state:
    st.session_state.diag_logs = [
        {"time": datetime.now().strftime("%H:%M:%S"), "msg": "System Ready. AI Magic Stickers & Audio Online.", "color": "#38bdf8"}
    ]

def add_log(msg, color="#38bdf8"):
    t_str = datetime.now().strftime("%H:%M:%S")
    st.session_state.diag_logs.append({"time": t_str, "msg": msg, "color": color})


# ==========================================
# 2. కోర్ DSP, STT & డాక్యుమెంట్ ఇంజిన్
# ==========================================

def detect_chunk_language(text):
    te_count = len(re.findall(r'[\u0C00-\u0C7F]', text))
    hi_count = len(re.findall(r'[\u0900-\u097F]', text))
    en_count = len(re.findall(r'[a-zA-Z]', text))

    if te_count > hi_count and te_count > en_count:
        return "te"
    elif hi_count > te_count and hi_count > en_count:
        return "hi"
    elif en_count > 0:
        return "en"
    return "te"

def apply_audio_dsp(audio_segment: AudioSegment) -> AudioSegment:
    try:
        processed = high_pass_filter(audio_segment, cutoff=300)
        processed = low_pass_filter(processed, cutoff=3800)
        processed = compress_dynamic_range(processed, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
        processed = normalize(processed) + 6.0
        return processed
    except Exception:
        return audio_segment

def transcribe_audio_file(uploaded_audio_file, lang_code="auto", enable_dsp=True, style="📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)", pause="మధ్యస్థం (Normal Pauses)", custom_note=""):
    uploaded_audio_file.seek(0)
    file_ext = os.path.splitext(uploaded_audio_file.name)[1].lower()
    if not file_ext:
        file_ext = ".m4a"
        
    temp_in = f"temp_stt_in{file_ext}"
    with open(temp_in, "wb") as f:
        f.write(uploaded_audio_file.read())

    full_transcript = []
    recognizer = sr.Recognizer()
    target_langs = ["te-IN", "hi-IN", "en-IN"] if lang_code == "auto" else [lang_code]

    try:
        sound = AudioSegment.from_file(temp_in)
        if enable_dsp:
            sound = apply_audio_dsp(sound)
        
        sound = sound.set_channels(1).set_frame_rate(16000)
        chunk_length_ms = 45 * 1000
        total_len = len(sound)
        
        for i in range(0, total_len, chunk_length_ms):
            chunk_audio = sound[i:i + chunk_length_ms]
            temp_chunk_wav = f"temp_chunk_{i}.wav"
            chunk_audio.export(temp_chunk_wav, format="wav")
            
            for test_lang in target_langs:
                try:
                    with sr.AudioFile(temp_chunk_wav) as source:
                        audio_data = recognizer.record(source)
                        part_text = recognizer.recognize_google(audio_data, language=test_lang)
                        if part_text and part_text.strip():
                            full_transcript.append(part_text.strip())
                            break
                except Exception:
                    continue
            
            if os.path.exists(temp_chunk_wav):
                try:
                    os.remove(temp_chunk_wav)
                except Exception:
                    pass

        if full_transcript:
            raw_text = " ".join(full_transcript)
            polished_text = polish_speech_script(raw_text, style_mode=style, pause_level=pause, user_instruction=custom_note)
            return polished_text
        else:
            return "⚠️ Voice not recognized. Try selecting a specific language."

    except Exception as e:
        return f"⚠️ STT Error: {e}"
    finally:
        if os.path.exists(temp_in):
            try:
                os.remove(temp_in)
            except Exception:
                pass

async def generate_voice_file(text, voice, pitch_val, rate_val, output_filename):
    communicate = edge_tts.Communicate(text, voice, pitch=pitch_val, rate=rate_val)
    await communicate.save(output_filename)

def split_text_into_chunks(text, max_chars=200):
    clean_text = re.sub(r'[\r]+', '', text).strip()
    if not clean_text:
        return []
    raw_sentences = re.split(r'(?<=[.!?\n।])\s+|(?<=\.\.\.)\s+', clean_text)
    chunks = []
    for sentence in raw_sentences:
        s_clean = sentence.strip()
        if not s_clean:
            continue
        if len(s_clean) <= max_chars:
            chunks.append(s_clean)
        else:
            words = s_clean.split(' ')
            curr_chunk = ""
            for word in words:
                if len(curr_chunk) + len(word) + 1 <= max_chars:
                    curr_chunk += word + " "
                else:
                    if curr_chunk.strip():
                        chunks.append(curr_chunk.strip())
                    curr_chunk = word + " "
            if curr_chunk.strip():
                chunks.append(curr_chunk.strip())
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
    return f"""<!DOCTYPE html><html lang="te"><head><meta charset="utf-8"><title>Speech Script</title>
    <style>body {{ font-family: Arial, sans-serif; font-size: 17px; line-height: 1.8; padding: 25px; color: #000; }}</style></head>
    <body onload="window.print()"><div>{formatted_body}</div></body></html>"""


# ==========================================
# 3. AI స్పీచ్ స్టైల్ & స్టిక్కర్ మ్యాజిక్ సెట్టింగ్స్
# ==========================================
with st.expander("⚙️ AI CONTROLS & MAGIC STICKERS (స్టైల్, థీమ్ & స్టిక్కర్లు)", expanded=False):
    col_style, col_pause = st.columns(2)
    with col_style:
        selected_style = st.selectbox("🎭 స్పీచ్ స్టైల్:", options=["📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)", "🧘 ఆధ్యాత్మికం (Spiritual & Calm)", "📰 న్యూస్ రీడర్ (News Bulletin)", "🗣️ సంభాషణ / కబుర్లు (Conversational)"])
    with col_pause:
        selected_pause = st.selectbox("⏱️ శ్వాస విరామాలు:", options=["మధ్యస్థం (Normal Pauses)", "ఎక్కువ (Deep Breathing / Heavy Pauses)", "స్వల్పం (Fast / Light Pauses)"])

    col_th, col_stk = st.columns(2)
    with col_th:
        poster_theme = st.selectbox("🎨 పోస్టర్ కలర్ థీమ్:", options=["ఆధ్యాత్మికం (Golden Divine)", "రక్తదానం / సేవా కార్యక్రమం (Red & White)", "ప్రకృతి / పచ్చదనం (Nature Green)", "రాయల్ బ్లూ (Corporate & Formal)"])
    with col_stk:
        sticker_choice = st.selectbox(
            "🏷️ AI స్టిక్కర్స్ / బ్యాడ్జ్ ఎంపిక:",
            options=[
                "🪄 AI మ్యాజిక్ (Auto Select)",
                "🕉️ ఓం (Divine Om)",
                "🪷 పద్మం (Sacred Lotus)",
                "🩸 రక్తదానం (Blood Drop)",
                "🕊️ శాంతి కపోతం (Peace Dove)",
                "🌟 గోల్డెన్ స్టార్ (Golden Star)",
                "📜 రాయల్ సీల్ (Royal Seal)",
                "❤️ సేవా హస్తం (Loving Care)"
            ]
        )

    custom_sticker_file = st.file_uploader("🖼️ కస్టమ్ లోగో/స్టిక్కర్ అప్‌లోడ్ (Optional Custom Sticker):", type=["png", "jpg", "jpeg", "webp"], key="cust_sticker_up")
    custom_ai_note = st.text_input("💡 AIకి ప్రత్యేక ఆదేశం (Optional):", placeholder="ఉదా: తేదీలు, ముఖ్యమైన పిలుపుల వద్ద పాజ్ ఇవ్వాలి...")


# ==========================================
# 4. ఇన్‌పుట్ విభాగాలు (DOC | AUDIO | MIC)
# ==========================================
with st.expander("📥 INPUT SOURCES (DOC / AUDIO STT / MIC)", expanded=True):
    c_file, c_audio_stt, c_mic = st.columns([0.33, 0.34, 0.33])

    with c_file:
        st.markdown("**📁 DOC / TXT**")
        uploaded_file = st.file_uploader("Upload Doc", type=["docx", "txt"], key="doc_file_uploader", label_visibility="collapsed")
        if uploaded_file is not None:
            try:
                f_text = extract_text_from_file(uploaded_file)
                if f_text and f_text != st.session_state.main_text:
                    with st.spinner("AI Speech Formatting..."):
                        polished = polish_speech_script(f_text, selected_style, selected_pause, custom_ai_note)
                        st.session_state.main_text = polished if polished else f_text
                    add_log(f"DOC Loaded: {uploaded_file.name}", "#4ade80")
                    st.toast(f"✅ {uploaded_file.name} Loaded!")
            except Exception as fe:
                st.error(f"Error: {fe}")

    with c_audio_stt:
        st.markdown("**🎵 AUDIO STT (Multi-min)**")
        stt_lang_choice = st.selectbox("Audio Lang:", options=["🔄 Auto (Multi-Lang)", "HI (हिंदी)", "TE (తెలుగు)", "EN (English)"], key="stt_lang_choice", label_visibility="collapsed")
        stt_lang_map = {"🔄 Auto (Multi-Lang)": "auto", "TE (తెలుగు)": "te-IN", "HI (हिंदी)": "hi-IN", "EN (English)": "en-IN"}
        selected_stt_lang = stt_lang_map[stt_lang_choice]

        uploaded_audio = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a", "ogg", "aac", "opus", "3gp"], key="audio_stt_file_uploader", label_visibility="collapsed")
        if uploaded_audio is not None:
            st.audio(uploaded_audio)
            use_dsp = st.checkbox("✨ DSP Booster", value=True, key="stt_dsp_chk")
            if st.button("🚀 RUN STT", use_container_width=True):
                add_log(f"STT Started: {uploaded_audio.name} ({stt_lang_choice})", "#c084fc")
                with st.spinner("Transcribing & Formatting with AI..."):
                    transcribed_txt = transcribe_audio_file(uploaded_audio, lang_code=selected_stt_lang, enable_dsp=use_dsp, style=selected_style, pause=selected_pause, custom_note=custom_ai_note)
                    if transcribed_txt and not transcribed_txt.startswith("⚠️"):
                        st.session_state.main_text = transcribed_txt.strip()
                        add_log(f"STT Ready ({len(transcribed_txt)} chars)", "#4ade80")
                        st.toast("✅ స్క్రిప్ట్ సిద్ధమైంది!")
                        st.rerun()
                    else:
                        st.error(transcribed_txt)

    with c_mic:
        st.markdown("**🎙️ LIVE MIC**")
        mic_lang = st.selectbox("Mic Lang:", options=["TE (తెలుగు)", "HI (हिंदी)", "EN (English)"], label_visibility="collapsed")
        mic_code_map = {"TE (తెలుగు)": "te-IN", "HI (हिंदी)": "hi-IN", "EN (English)": "en-IN"}
        spoken_result = speech_to_text(
            start_prompt="🎙️ START",
            stop_prompt="⏹️ STOP",
            language=mic_code_map[mic_lang],
            use_container_width=True,
            key='mic_rec'
        )
        if spoken_result and spoken_result != st.session_state.last_mic_text:
            with st.spinner("Formatting Voice with AI..."):
                polished_live = polish_speech_script(spoken_result, selected_style, selected_pause, custom_ai_note)
                st.session_state.main_text = (st.session_state.main_text + "\n\n" + (polished_live if polished_live else spoken_result)).strip()
            st.session_state.last_mic_text = spoken_result
            add_log(f"MIC: '{spoken_result}' (Polished)", "#4ade80")
            st.rerun()


# ==========================================
# 5. MAIN TEXT CONTENT & RE-POLISH BAR
# ==========================================
col_hdr, col_polish = st.columns([0.65, 0.35])
with col_hdr:
    st.markdown("##### 📝 స్పీచ్ స్క్రిప్ట్ ఎడిటర్ (Speech Script)")
with col_polish:
    if st.button("✨ స్క్రిప్ట్ మార్చు (Re-Polish AI)", use_container_width=True):
        if st.session_state.main_text.strip():
            with st.spinner("AI ద్వారా స్క్రిప్ట్ సరిచేస్తోంది..."):
                polished = polish_speech_script(st.session_state.main_text, selected_style, selected_pause, custom_ai_note)
                if polished:
                    st.session_state.main_text = polished
                    add_log("స్క్రిప్ట్ రీ-పాలిష్ చేయబడింది!", "#38bdf8")
                    st.toast("✨ స్క్రిప్ట్ సిద్ధమైంది!", icon="✨")
                    st.rerun()
        else:
            st.warning("దయచేసి టెక్స్ట్‌ను ఎంటర్ చేయండి.")

user_input_text = st.text_area(
    "Content Editor", 
    value=st.session_state.main_text, 
    height=160,
    placeholder="Formatted speech script appears here...",
    label_visibility="collapsed"
)
if user_input_text != st.session_state.main_text:
    st.session_state.main_text = user_input_text


# ==========================================
# 6. TTS SETTINGS
# ==========================================
with st.expander("⚙️ TTS SETTINGS (స్వరం, స్పీడ్ & BGM)", expanded=True):
    col_tts_lang, col_tts_voice = st.columns([0.45, 0.55])
    with col_tts_lang:
        tts_lang = st.selectbox("🌐 TTS Mode:", options=["🔄 Auto Detect (Multi-Lang)", "Hindi (हिंदी)", "Telugu (తెలుగు)", "English"], key="main_tts_lang_select")
    with col_tts_voice:
        gender_choice = st.radio("Voice Gender:", options=["👨 Male (పురుష)", "👩 Female (స్త్రీ)"], horizontal=True, key="gender_sel")

    col_opt_speed, col_opt_pitch, col_opt_pause = st.columns(3)
    with col_opt_speed:
        audio_speed = st.select_slider("🔊 Play Speed:", options=[0.75, 0.85, 1.0, 1.15, 1.25, 1.5], value=0.85, key="main_tts_speed")
    with col_opt_pitch:
        pitch_custom = st.select_slider("🎚️ Voice Pitch:", options=["Normal", "Deep Base", "Heavy Base"], value="Normal", key="main_tts_pitch")
    with col_opt_pause:
        pause_duration = st.slider("⏸️ Line Pause (Sec):", min_value=0.2, max_value=1.5, value=0.4, step=0.1, key="main_tts_pause")
        
    col_bgm_1, col_bgm_2 = st.columns([0.4, 0.6])
    with col_bgm_1:
        enable_bgm = st.checkbox("🎶 Enable BGM", value=True, key="main_tts_bgm_chk")
    with col_bgm_2:
        bgm_volume = st.slider("🎵 BGM Volume (%):", min_value=2, max_value=20, value=6, key="main_tts_bgm_vol")


# ==========================================
# 7. యాక్షన్ కంట్రోల్స్
# ==========================================
active_text = st.session_state.main_text.strip()
b1, b2, b3, b4 = st.columns(4)
b5, b6, b7 = st.columns(3)

# Row 1
with b1:
    convert_btn = st.button("🔊 TTS", type="primary", use_container_width=True)

with b2:
    if active_text:
        if st.button("🖼️ AI POSTER", use_container_width=True):
            with st.spinner("Groq AI & స్టిక్కర్ ఇంజిన్ ద్వారా పోస్టర్ డిజైన్ అవుతోంది..."):
                poster_html = generate_ai_poster_html(
                    active_text, 
                    theme=poster_theme, 
                    sticker_choice=sticker_choice, 
                    custom_sticker_file=custom_sticker_file
                )
                st.session_state.poster_html_data = poster_html
                add_log(f"AI పోస్టర్ సిద్ధమైంది! (Sticker: {sticker_choice})", "#4ade80")
                st.toast("🖼️ AI పోస్టర్ సిద్ధమైంది!", icon="🖼️")
    else:
        st.button("🖼️ AI POSTER", disabled=True, use_container_width=True)

with b3:
    if active_text:
        html_trans_page = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body><p style='font-size:18px; line-height:1.8;'>{active_text.replace(chr(10), '<br>')}</p></body></html>"
        st.download_button("🌐 HTML", data=html_trans_page.encode('utf-8'), file_name="speech_script.html", mime="text/html", use_container_width=True)
    else:
        st.button("🌐 HTML", disabled=True, use_container_width=True)

with b4:
    if active_text:
        printable_pdf = create_printable_pdf_html(active_text)
        st.download_button("📄 PDF", data=printable_pdf.encode('utf-8'), file_name="speech_script.html", mime="text/html", use_container_width=True)
    else:
        st.button("📄 PDF", disabled=True, use_container_width=True)

# Row 2
with b5:
    if active_text:
        docx_data = create_docx_bytes(active_text)
        st.download_button("📝 DOCX", data=docx_data, file_name="speech_script.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else:
        st.button("📝 DOCX", disabled=True, use_container_width=True)

with b6:
    if active_text:
        if st.button("📋 COPY", use_container_width=True):
            st.code(active_text, language=None)
            st.toast("✅ Copied!", icon="📋")
    else:
        st.button("📋 COPY", disabled=True, use_container_width=True)

with b7:
    if st.button("🧹 CLEAR", use_container_width=True):
        st.session_state.main_text = ""
        st.session_state.audio_bytes_data = None
        st.session_state.poster_html_data = None
        st.session_state.last_mic_text = ""
        add_log("Cleared.", "#facc15")
        gc.collect()
        st.rerun()


# ==========================================
# 8. AI పోస్టర్ ప్రివ్యూ & సేవ్ విభాగం
# ==========================================
if st.session_state.poster_html_data is not None:
    st.divider()
    st.markdown("### 🖼️ AI గ్రాఫిక్ పోస్టర్ కార్డ్ (Graphic Poster Card)")
    st.components.v1.html(st.session_state.poster_html_data, height=800, scrolling=True)
    
    st.download_button(
        label="📥 పోస్టర్ డౌన్‌లోడ్ చేసుకోండి (Download Poster HTML/Card)",
        data=st.session_state.poster_html_data.encode('utf-8'),
        file_name="ai_graphic_poster.html",
        mime="text/html",
        use_container_width=True
    )


# ==========================================
# 9. ఆటో మల్టీ-లాంగ్వేజ్ TTS జనరేషన్ ఇంజిన్
# ==========================================
if convert_btn:
    if active_text:
        add_log(f"TTS Started: Mode={tts_lang}", "#c084fc")
        with st.spinner("Generating Natural Voice..."):
            try:
                clean_txt = re.sub(r'[*#_~`]', '', active_text)
                rate_str = f"{int((audio_speed - 1.0) * 100):+d}%"
                pitch_val_map = {"Normal": "+0Hz", "Deep Base": "-5Hz", "Heavy Base": "-10Hz"}
                pitch_str = pitch_val_map[pitch_custom]

                voice_dict = {
                    "te": "te-IN-MohanNeural" if "Male" in gender_choice else "te-IN-ShrutiNeural",
                    "hi": "hi-IN-MadhurNeural" if "Male" in gender_choice else "hi-IN-SwaraNeural",
                    "en": "en-IN-PrabhatNeural" if "Male" in gender_choice else "en-IN-NeerjaNeural"
                }

                text_chunks = split_text_into_chunks(clean_txt, max_chars=200)
                speech_sound = AudioSegment.empty()
                silence_pause = AudioSegment.silent(duration=int(pause_duration * 1000))

                for i, chunk in enumerate(text_chunks):
                    if "Auto" in tts_lang:
                        detected_l = detect_chunk_language(chunk)
                        chosen_voice = voice_dict[detected_l]
                    elif "Telugu" in tts_lang:
                        chosen_voice = voice_dict["te"]
                    elif "Hindi" in tts_lang:
                        chosen_voice = voice_dict["hi"]
                    else:
                        chosen_voice = voice_dict["en"]

                    temp_file = f"temp_tts_{i}.mp3"
                    try:
                        asyncio.run(generate_voice_file(chunk, chosen_voice, pitch_str, rate_str, temp_file))
                        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                            chunk_sound = AudioSegment.from_file(temp_file)
                            speech_sound += chunk_sound + silence_pause
                            os.remove(temp_file)
                    except Exception as ce:
                        add_log(f"Chunk {i} note: {ce}", "#facc15")

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
                    add_log("TTS Audio Ready!", "#4ade80")
                    gc.collect()
                    st.toast("🎉 TTS Audio Ready!")
                else:
                    add_log("TTS Failed", "#f87171")
                    st.error("❌ Audio Generation Failed.")

            except Exception as e:
                add_log(f"TTS Error: {e}", "#f87171")
                st.error("❌ TTS Error:")
                st.code(traceback.format_exc())
    else:
        st.warning("Please provide text.")

# ఆడియో ప్లేయర్ & డౌన్‌లోడ్
if st.session_state.audio_bytes_data is not None:
    st.divider()
    st.audio(st.session_state.audio_bytes_data, format="audio/mp3")
    st.download_button(
        label="📥 DOWNLOAD MP3", 
        data=st.session_state.audio_bytes_data, 
        file_name="speech_audio.mp3", 
        mime="audio/mp3",
        key="download_btn",
        use_container_width=True
    )

# డయాగ్నొస్టిక్స్
with st.expander("🔍 DIAGNOSTICS", expanded=False):
    log_html = "<div class='diag-box'>"
    for item in st.session_state.diag_logs[-15:]:
        log_html += f"<div class='diag-log'><span style='color:#94a3b8;'>[{item['time']}]</span> <span style='color:{item['color']};'>{item['msg']}</span></div>"
    log_html += "</div>"
    st.markdown(log_html, unsafe_allow_html=True)
