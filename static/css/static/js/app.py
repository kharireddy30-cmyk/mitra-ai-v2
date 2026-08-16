import streamlit as st
import asyncio
import io
import re
import os
import gc
import traceback
from pydub import AudioSegment
from streamlit_mic_recorder import speech_to_text

# మన కస్టమ్ మొడ్యూల్స్ నుండి ఇంపోర్ట్
from document_utils import (
    extract_text_from_file,
    create_docx_bytes,
    create_printable_pdf_html
)
from audio_engine import (
    generate_voice_file,
    split_text_into_chunks,
    transcribe_audio_file
)

# ==========================================
# 1. పేజీ సెట్టింగ్స్ & CSS లోడ్ చేయడం
# ==========================================
st.set_page_config(
    page_title="ఆధ్యాత్మిక వాయిస్ యంత్రం", 
    layout="wide", 
    page_icon="🕉️"
)

# కస్టమ్ CSS ఇంజెక్ట్ చేయడం
if os.path.exists("static/css/style.css"):
    with open("static/css/style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.header("🔱 ఆధ్యాత్మిక వాయిస్ సిస్టమ్")
st.caption("వాయిస్ కన్వర్షన్ (TTS), ఆడియో టు టెక్స్ట్ (STT), Web Audio DSP & డాక్యుమెంట్ ఎక్స్‌పోర్ట్")

# సెషన్ స్టేట్స్
if "main_text" not in st.session_state:
    st.session_state.main_text = ""
if "audio_bytes_data" not in st.session_state:
    st.session_state.audio_bytes_data = None
if "last_mic_text" not in st.session_state:
    st.session_state.last_mic_text = ""

# API Token (Streamlit Secrets నుండి)
HF_TOKEN = st.secrets.get("HF_TOKEN", None)

# ==========================================
# 2. ఇన్‌పుట్ విభాగం (డాక్స్, ఆడియో STT, & లైవ్ మైక్)
# ==========================================
st.divider()
c_doc, c_audio_stt, c_mic = st.columns([0.34, 0.33, 0.33])

# 1. డాక్యుమెంట్ అప్‌లోడ్
with c_doc:
    st.markdown("**📁 టెక్స్ట్ ఫైల్ (.docx, .txt):**")
    uploaded_doc = st.file_uploader(
        "డాక్యుమెంట్ అప్‌లోడ్", 
        type=["docx", "txt"],
        key="doc_uploader",
        help="Microsoft Word లేదా Text ఫైల్స్"
    )
    if uploaded_doc is not None:
        if uploaded_doc.size <= 10 * 1024 * 1024:
            try:
                f_text = extract_text_from_file(uploaded_doc)
                if f_text and f_text != st.session_state.main_text:
                    st.session_state.main_text = f_text
                    st.success(f"✅ '{uploaded_doc.name}' లోడ్ అయింది!")
            except Exception as fe:
                st.error(f"ఫైల్ ఎర్రర్: {fe}")

# 2. ఆడియో ఫైల్ స్పీచ్ టు టెక్స్ట్ (STT + DSP)
with c_audio_stt:
    st.markdown("**🎵 ఆడియో ఫైల్ టు టెక్స్ట్ (STT):**")
    uploaded_audio = st.file_uploader(
        "ఆడియో అప్‌లోడ్ (.mp3, .wav, .m4a)", 
        type=["mp3", "wav", "m4a", "ogg"],
        key="audio_stt_uploader"
    )
    use_dsp = st.checkbox("✨ DSP వాయిస్ బూస్టర్ (మృదువైన స్వరాల కోసం)", value=True)
    
    if uploaded_audio is not None:
        if st.button("🚀 ఆడియోని టెక్స్ట్‌గా మార్చు", use_container_width=True):
            with st.spinner("DSP తో ఆడియోను ప్రాసెస్ చేసి టెక్స్ట్‌గా మారుస్తోంది..."):
                transcribed_txt = transcribe_audio_file(
                    uploaded_audio, 
                    lang_code="te-IN", 
                    hf_token=HF_TOKEN,
                    enable_dsp=use_dsp
                )
                if transcribed_txt and not transcribed_txt.startswith("⚠️"):
                    st.session_state.main_text = (st.session_state.main_text + " " + transcribed_txt).strip()
                    st.success("✅ ఆడియో విజయవంతంగా టెక్స్ట్‌గా మార్చబడింది!")
                    st.rerun()
                else:
                    st.error(transcribed_txt)

# 3. లైవ్ మైక్రోఫోన్
with c_mic:
    st.markdown("**🎙️ లైవ్ మైక్రోఫోన్ (Voice Typing):**")
    mic_lang = st.selectbox("భాష:", options=["తెలుగు (Telugu)", "హిందీ (Hindi)", "ఇంగ్లీష్ (English)"])
    mic_code_map = {"తెలుగు (Telugu)": "te-IN", "హిందీ (Hindi)": "hi-IN", "ఇంగ్లీష్ (English)": "en-IN"}
    
    spoken_result = speech_to_text(
        start_prompt="🎙️ మాట్లాడటం ప్రారంభించండి",
        stop_prompt="⏹️ ఆపండి",
        language=mic_code_map[mic_lang],
        use_container_width=True,
        key='perfect_mic_recorder'
    )
    if spoken_result and spoken_result != st.session_state.last_mic_text:
        st.session_state.main_text = (st.session_state.main_text + " " + spoken_result).strip()
        st.session_state.last_mic_text = spoken_result
        st.rerun()

# ప్రధాన టెక్స్ట్ ఏరియా
user_input_text = st.text_area(
    "ప్రధాన టెక్స్ట్ (ఆడియో చేయడానికి లేదా డౌన్‌లోడ్ చేయడానికి):", 
    value=st.session_state.main_text, 
    height=180,
    placeholder="టెక్స్ట్ ఇక్కడ కనిపిస్తుంది..."
)
if user_input_text != st.session_state.main_text:
    st.session_state.main_text = user_input_text

# ==========================================
# 3. ఆడియో ఎంపికలు & కస్టమైజేషన్
# ==========================================
st.divider()
col_lang, col_voice = st.columns([0.5, 0.5])

with col_lang:
    selected_lang = st.selectbox("🌐 అవుట్‌పుట్ ఆడియో భాష:", options=["తెలుగు (Telugu)", "హిందీ (Hindi)", "ఇంగ్లీష్ (English)"])

with col_voice:
    if "తెలుగు" in selected_lang:
        voice_option = st.radio("🎙️ స్వరాన్ని ఎంచుకోండి:", options=["👨 మోహన్ (పురుష)", "👩 శ్రుతి (స్త్రీ)"], horizontal=True)
    elif "హిందీ" in selected_lang:
        voice_option = st.radio("🎙️ స్వరాన్ని ఎంచుకోండి:", options=["👨 మధుర్ (పురుష)", "👩 స్వర్ణ (స్త్రీ)"], horizontal=True)
    else:
        voice_option = st.radio("🎙️ స్వరాన్ని ఎంచుకోండి:", options=["👨 ప్రభాత్ (పురుష)", "👩 నీరజ (స్త్రీ)"], horizontal=True)

with st.expander("⚙️ ఆప్షనల్ ఆడియో సెట్టింగ్స్ (స్పీడ్, పిచ్ & BGM)"):
    col_opt_speed, col_opt_pitch, col_opt_pause = st.columns(3)
    with col_opt_speed:
        audio_speed = st.select_slider("🔊 ప్లే స్పీడ్:", options=[0.75, 0.85, 1.0, 1.15, 1.25, 1.5], value=0.85)
    with col_opt_pitch:
        pitch_custom = st.select_slider("🎚️ వాయిస్ పిచ్:", options=["సాధారణ (Normal)", "గంభీరం (Deep Base)", "అత్యంత గంభీరం (Heavy Base)"], value="సాధారణ (Normal)")
    with col_opt_pause:
        pause_duration = st.slider("⏸️ వాక్యాల మధ్య విరామం (సెకన్లు):", min_value=0.3, max_value=2.0, value=0.6, step=0.1)
        
    col_bgm_1, col_bgm_2 = st.columns([0.4, 0.6])
    with col_bgm_1:
        enable_bgm = st.checkbox("🎶 BGM జోడించు", value=True)
    with col_bgm_2:
        bgm_volume = st.slider("🎵 BGM సౌండ్ (%):", min_value=2, max_value=20, value=6)

# ==========================================
# 4. యాక్షన్ కంట్రోల్స్ (Action Buttons)
# ==========================================
st.markdown("##### 🎯 యాక్షన్ కంట్రోల్స్")
active_text = st.session_state.main_text.strip()
c1, c2, c3, c4, c5, c6 = st.columns([0.18, 0.18, 0.16, 0.16, 0.16, 0.16])

with c1:
    convert_btn = st.button("🔊 ఆడియో చేయి", type="primary", use_container_width=True)

with c2:
    if active_text:
        html_trans_page = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body><p style='font-size:18px; line-height:1.6;'>{active_text.replace(chr(10), '<br>')}</p></body></html>"
        st.download_button("🌐 HTML", data=html_trans_page.encode('utf-8'), file_name="translate_page.html", mime="text/html", use_container_width=True)
    else:
        st.button("🌐 HTML", disabled=True, use_container_width=True)

with c3:
    if active_text:
        printable_pdf = create_printable_pdf_html(active_text)
        st.download_button("📄 PDF ఫైల్", data=printable_pdf.encode('utf-8'), file_name="spiritual_note.html", mime="text/html", use_container_width=True)
    else:
        st.button("📄 PDF ఫైల్", disabled=True, use_container_width=True)

with c4:
    if active_text:
        docx_data = create_docx_bytes(active_text)
        st.download_button("📝 Word ఫైల్", data=docx_data, file_name="spiritual_note.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    else:
        st.button("📝 Word ఫైల్", disabled=True, use_container_width=True)

with c5:
    if active_text:
        if st.button("📋 కాపీ", use_container_width=True):
            st.code(active_text, language=None)
            st.toast("✅ టెక్స్ట్‌ని కాపీ చేసుకోండి!", icon="📋")
    else:
        st.button("📋 కాపీ", disabled=True, use_container_width=True)

with c6:
    if st.button("🧹 క్లియర్", use_container_width=True):
        st.session_state.main_text = ""
        st.session_state.audio_bytes_data = None
        st.session_state.last_mic_text = ""
        gc.collect()
        st.rerun()

# ==========================================
# 5. టెక్స్ట్ టు స్పీచ్ (TTS) ప్రాసెసింగ్
# ==========================================
if convert_btn:
    if active_text:
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
                    gc.collect()
                    st.success("🎉 ఆడియో విజయవంతంగా సిద్ధమైంది!")
                else:
                    st.error("❌ ఆడియో డేటా ఏదీ జనరేట్ కాలేదు!")

            except Exception as e:
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
