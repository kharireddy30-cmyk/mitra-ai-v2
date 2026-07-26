import streamlit as st
import edge_tts
from pydub import AudioSegment
import asyncio
import io
import uuid

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(
    page_title="Brahma Kumaris - Spiritual Voice Generator", 
    layout="wide", 
    page_icon="🧘"
)

# --- 2. ఇనిషియలైజేషన్ ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  
if "current_chat_id" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.chat_history[initial_id] = {"title": "కొత్త ఆడియో నోట్", "messages": []}
    st.session_state.current_chat_id = initial_id

if "rename_id" not in st.session_state:
    st.session_state.rename_id = None

# edge-tts async ఫంక్షన్
async def generate_voice(text, voice):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# --- 3. సైడ్ బార్ ---
with st.sidebar:
    st.title("🕉️ ఆడియో నోట్స్ కంట్రోల్స్")
    if st.button("➕ కొత్త ఆడియో నోట్", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chat_history[new_id] = {"title": "కొత్త ఆడియో నోట్", "messages": []}
        st.session_state.current_chat_id = new_id
        st.session_state.rename_id = None
        st.rerun()

    st.divider()
    st.subheader("సేవ్ చేసిన ఆడియో జాబితా")
    
    for chat_id in list(st.session_state.chat_history.keys()):
        if st.session_state.rename_id == chat_id:
            new_title = st.text_input("కొత్త టైటిల్ ఇవ్వండి:", value=st.session_state.chat_history[chat_id]["title"], key=f"input_ren_{chat_id}")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("Save", key=f"save_title_{chat_id}"):
                    st.session_state.chat_history[chat_id]["title"] = new_title
                    st.session_state.rename_id = None
                    st.rerun()
            with col_s2:
                if st.button("Cancel", key=f"cancel_title_{chat_id}"):
                    st.session_state.rename_id = None
                    st.rerun()
        else:
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            with col1:
                btn_label = st.session_state.chat_history[chat_id]["title"]
                if st.button(btn_label, key=f"btn_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with col2:
                if st.button("✏️", key=f"ren_{chat_id}"):
                    st.session_state.rename_id = chat_id
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_{chat_id}"):
                    del st.session_state.chat_history[chat_id]
                    if not st.session_state.chat_history:
                        new_id = str(uuid.uuid4())
                        st.session_state.chat_history[new_id] = {"title": "కొత్త ఆడియో నోట్", "messages": []}
                        st.session_state.current_chat_id = new_id
                    elif st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = list(st.session_state.chat_history.keys())[0]
                    st.rerun()

# --- 4. ప్రధాన స్క్రీన్ ---
st.header("🔱 బ్రహ్మకుమారీస్ - ఆధ్యాత్మిక వాయిస్ కన్వర్టర్")
st.caption("గంభీరమైన తెలుగు స్త్రీ మరియు పురుషుల స్వరాన్ని ఎంచుకుని మీ ఆధ్యాత్మిక టెక్స్ట్‌ని MP3 గా మార్చుకోండి.")

current_chat = st.session_state.chat_history[st.session_state.current_chat_id]
msg_to_delete = None

for idx, m in enumerate(current_chat["messages"]):
    with st.chat_message("assistant", avatar="🕉️"):
        st.markdown(m["text"])
        st.caption(f"🎙️ గొంతు: {m.get('voice_name', 'తెలుగు')} | 🔊 వేగం: {m.get('speed', 1.0)}x")
        
        if "audio" in m and m["audio"] is not None:
            st.audio(m["audio"], format="audio/mp3")

        c1, c2, _ = st.columns([0.08, 0.18, 0.74])
        with c1:
            if st.button("🗑️", key=f"msg_del_{idx}"):
                msg_to_delete = idx
        with c2:
            if "audio" in m and m["audio"] is not None:
                st.download_button(
                    label="📥 MP3 డౌన్‌లోడ్", 
                    data=m["audio"], 
                    file_name=f"spiritual_audio_{idx+1}.mp3", 
                    mime="audio/mp3",
                    key=f"audio_dl_{idx}"
                )

if msg_to_delete is not None:
    current_chat["messages"].pop(msg_to_delete)
    st.rerun()

# --- 5. ఇన్‌పుట్ & వాయిస్ సెట్టింగ్స్ ---
st.divider()
user_text = st.text_area("ఆడియోగా మార్చాలనుకుంటున్న తెలుగు టెక్స్ట్‌ని ఇక్కడ పేస్ట్ చేయండి:", height=130, placeholder="బాబా చెప్పారు... ఓం శాంతి.")

col_1, col_2 = st.columns([0.5, 0.5])

with col_1:
    voice_option = st.radio(
        "🎙️ వాయిస్ స్వరాన్ని ఎంచుకోండి (Select Voice):",
        options=["👨 మోహన్ (గంభీరమైన పురుష గొంతు)", "👩 శ్రుతి (స్పష్టమైన స్త్రీ గొంతు)"],
        horizontal=True
    )

with col_2:
    audio_speed = st.select_slider(
        "🔊 ఆడియో వేగాన్ని ఎంచుకోండి (Audio Speed):",
        options=[0.75, 1.0, 1.25, 1.5, 1.75, 2.0],
        value=1.0
    )

convert_btn = st.button("🔊 ఆధ్యాత్మిక వాయిస్ క్రియేట్ చేయి", type="primary", use_container_width=True)

if convert_btn:
    if user_text.strip():
        with st.spinner("సాఫ్ట్ & గంభీరమైన వాయిస్ తయారవుతోంది..."):
            try:
                clean_txt = user_text.replace("*", "").replace("#", "")
                
                # వాయిస్ సెలక్షన్
                selected_voice = "te-IN-MohanNeural" if "మోహన్" in voice_option else "te-IN-ShrutiNeural"
                voice_label = "మోహన్ (పురుష)" if "మోహన్" in voice_option else "శ్రుతి (స్త్రీ)"

                # 1. edge-tts తో హై-క్వాలిటీ ఆడియో జనరేట్ చేయడం
                raw_audio = asyncio.run(generate_voice(clean_txt, selected_voice))
                raw_fp = io.BytesIO(raw_audio)

                # 2. pydub తో స్పీడ్ అడ్జస్ట్‌మెంట్
                sound = AudioSegment.from_file(raw_fp, format="mp3")
                if audio_speed != 1.0:
                    sound = sound._spawn(sound.raw_data, overrides={
                        "frame_rate": int(sound.frame_rate * audio_speed)
                    }).set_frame_rate(sound.frame_rate)

                final_fp = io.BytesIO()
                sound.export(final_fp, format="mp3")
                final_fp.seek(0)
                audio_bytes = final_fp.getvalue()

                # 3. సెషన్ స్టేట్‌లో సేవ్
                current_chat["messages"].append({
                    "text": user_text,
                    "audio": audio_bytes,
                    "speed": audio_speed,
                    "voice_name": voice_label
                })

                if len(current_chat["messages"]) == 1 or current_chat["title"] == "కొత్త ఆడియో నోట్":
                    current_chat["title"] = user_text[:20] + ("..." if len(user_text) > 20 else "")

                st.success("గంభీరమైన ఆధ్యాత్మిక వాయిస్ సిద్ధమైంది!")
                st.rerun()

            except Exception as e:
                st.error(f"వాయిస్ తయారీలో లోపం వచ్చింది: {e}")
    else:
        st.warning("దయచేసి టెక్స్ట్ ఎంటర్ చేయండి.")
