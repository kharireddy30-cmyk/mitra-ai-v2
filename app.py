import streamlit as st
import edge_tts
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
from services.divine_canvas_pro import render_divine_canvas_pro

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

st.subheader("🕉️ BRAHMA AI : Divine Studio Pro (Voice & Canvas)")

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
        {"time": datetime.now().strftime("%H:%M:%S"), "msg": "System Ready. Pure Stream Engine Online.", "color": "#38bdf8"}
    ]

def add_log(msg, color="#38bdf8"):
    t_str = datetime.now().strftime("%H:%M:%S")
    st.session_state.diag_logs.append({"time": t_str, "msg": msg, "color": color})


# ==========================================
# 2. కోర్ లాంగ్వేజ్ & డాక్యుమెంట్ ఇంజిన్
# ==========================================

def detect_language(text):
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

async def generate_voice_stream(text, voice, pitch_val, rate_val):
    communicate = edge_tts.Communicate(text, voice, pitch=pitch_val, rate=rate_val)
    audio_stream = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream.extend(chunk["data"])
    return bytes(audio_stream)

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
# 3. AI కంట్రోల్స్ & మ్యాన్యువల్ లేఅవుట్ సెట్టింగ్స్
# ==========================================
with st.expander("⚙️ AI CONTROLS, STICKERS & CANVAS SETTINGS", expanded=False):
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

    col_mode, col_align, col_fsize = st.columns(3)
    with col_mode:
        content_mode = st.selectbox("📝 కంటెంట్ మోడ్:", options=["📜 పూర్తి మ్యాటర్ (Full Exact Text)", "🤖 AI సారాంశం (Summary Points)"])
    with col_align:
        text_align = st.selectbox("📐 టెక్స్ట్ అమరిక (Alignment):", options=["ఎడమ వైపు (Left)", "మధ్యలో (Center)", "సమానంగా (Justify)"])
    with col_fsize:
        font_size_choice = st.selectbox("🔤 అక్షరాల సైజు (Font Size):", options=["మధ్యస్థం (Medium - 18px)", "చిన్నది (Small - 15px)", "పెద్దది (Large - 22px)", "చాలా పెద్దది (X-Large - 26px)"])

    col_bg_up, col_stk_up = st.columns(2)
    with col_bg_up:
        custom_bg_file = st.file_uploader("🖼️ కస్టమ్ బ్యాక్‌గ్రౌండ్ ఇమేజ్ / యానిమేటెడ్ GIF:", type=["png", "jpg", "jpeg", "webp", "gif"], key="cust_bg_up")
    with col_stk_up:
        custom_sticker_file = st.file_uploader("🏷️ కస్టమ్ లోగో/స్టిక్కర్ అప్‌లోడ్ (GIF/PNG):", type=["png", "jpg", "jpeg", "webp", "gif"], key="cust_sticker_up")

    custom_ai_note = st.text_input("💡 AIకి ప్రత్యేక ఆదేశం (Optional):", placeholder="ఉదా: ఆధ్యాత్మిక శైలిలో తేదీలు, ముఖ్యమైన లైన్లను హైలైట్ చేయండి...")


# ==========================================
# 4. ఇన్‌పుట్ విభాగాలు (DOC | MIC)
# ==========================================
with st.expander("📥 INPUT SOURCES (DOC / LIVE MIC)", expanded=True):
    c_file, c_mic = st.columns([0.5, 0.5])

    with c_file:
        st.markdown("**📁 DOC / TXT ఫైల్ అప్‌లోడ్**")
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

    with c_mic:
        st.markdown("**🎙️ LIVE MIC రికార్డింగ్**")
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
with st.expander("⚙️ TTS SETTINGS (స్వరం & స్పీడ్)", expanded=True):
    col_tts_lang, col_tts_voice = st.columns([0.45, 0.55])
    with col_tts_lang:
        tts_lang = st.selectbox("🌐 TTS Mode:", options=["🔄 Auto Detect (Multi-Lang)", "Hindi (हिंदी)", "Telugu (తెలుగు)", "English"], key="main_tts_lang_select")
    with col_tts_voice:
        gender_choice = st.radio("Voice Gender:", options=["👨 Male (పురుష)", "👩 Female (స్త్రీ)"], horizontal=True, key="gender_sel")

    col_opt_speed, col_opt_pitch = st.columns(2)
    with col_opt_speed:
        audio_speed = st.select_slider("🔊 Play Speed:", options=[0.75, 0.85, 1.0, 1.15, 1.25, 1.5], value=0.85, key="main_tts_speed")
    with col_opt_pitch:
        pitch_custom = st.select_slider("🎚️ Voice Pitch:", options=["Normal", "Deep Base", "Heavy Base"], value="Normal", key="main_tts_pitch")


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
        if st.button("🖼️ DIVINE CANVAS", use_container_width=True):
            with st.spinner("డివైన్ కాన్వాస్ ప్రో సిద్ధమవుతోంది..."):
                poster_html = render_divine_canvas_pro(
                    active_text, 
                    theme=poster_theme, 
                    sticker_choice=sticker_choice, 
                    content_mode=content_mode, 
                    text_align=text_align, 
                    font_size_choice=font_size_choice, 
                    custom_sticker_file=custom_sticker_file, 
                    custom_bg_file=custom_bg_file, 
                    user_prompt=custom_ai_note
                )
                st.session_state.poster_html_data = poster_html
                add_log("డివైన్ కాన్వాస్ ప్రో సిద్ధమైంది!", "#4ade80")
                st.toast("🖼️ కాన్వాస్ సిద్ధమైంది!", icon="🖼️")
    else:
        st.button("🖼️ DIVINE CANVAS", disabled=True, use_container_width=True)

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
# 8. DIVINE CANVAS PRO ప్రివ్యూ విభాగం
# ==========================================
if st.session_state.poster_html_data is not None:
    st.divider()
    st.markdown("### 🖼️ డివైన్ కాన్వాస్ ప్రో (Divine Spiritual Canvas Pro)")
    st.components.v1.html(st.session_state.poster_html_data, height=980, scrolling=True)


# ==========================================
# 9. ప్యూర్ స్ట్రీమ్ TTS జనరేషన్ ఇంజిన్ (No FFmpeg)
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

                if "Auto" in tts_lang:
                    detected_l = detect_language(clean_txt)
                    chosen_voice = voice_dict[detected_l]
                elif "Telugu" in tts_lang:
                    chosen_voice = voice_dict["te"]
                elif "Hindi" in tts_lang:
                    chosen_voice = voice_dict["hi"]
                else:
                    chosen_voice = voice_dict["en"]

                # డైరెక్ట్ న్యూరల్ స్ట్రీమ్ జనరేషన్
                audio_bytes = asyncio.run(generate_voice_stream(clean_txt, chosen_voice, pitch_str, rate_str))

                if audio_bytes and len(audio_bytes) > 0:
                    st.session_state.audio_bytes_data = audio_bytes
                    add_log("TTS Audio Ready (Direct Stream)!", "#4ade80")
                    gc.collect()
                    st.toast("🎉 TTS Audio Ready!")
                else:
                    add_log("TTS Failed", "#f87171")
                    st.error("❌ Audio Generation Failed.")

            except Exception as e:
                add_log(f"TTS Error: {e}", "#f87171")
                st.error(f"❌ TTS Error: {e}")
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
