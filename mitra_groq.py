import streamlit as st
from gtts import gTTS
import io
import uuid

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(
    page_title="Brahma Kumaris - Spiritual TTS Voice Engine", 
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

# --- 3. సైడ్ బార్ (చాట్ & నోట్స్ మేనేజ్మెంట్) ---
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
        # రీనేమ్ ఫీచర్
        if st.session_state.rename_id == chat_id:
            new_title = st.text_input(
                "కొత్త టైటిల్ ఇవ్వండి:", 
                value=st.session_state.chat_history[chat_id]["title"], 
                key=f"input_ren_{chat_id}"
            )
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
st.header("🔱 బ్రహ్మకుమారీస్ - తెలుగు ఆధ్యాత్మిక వాయిస్ కన్వర్టర్ (TTS)")
st.caption("మీ ఆధ్యాత్మిక వచనాలు లేదా బాబా మురళీ టెక్స్ట్‌ని ఇక్కడ ఇస్తే అది స్వచ్ఛమైన తెలుగు స్వరంలో ప్లే అవుతుంది మరియు డోన్లోడ్ చేసుకోవచ్చు.")

current_chat = st.session_state.chat_history[st.session_state.current_chat_id]

# మెసేజ్ హిస్టరీ డిస్‌ప్లే
msg_to_delete = None

for idx, m in enumerate(current_chat["messages"]):
    with st.chat_message("assistant", avatar="🕉️"):
        st.markdown(m["text"])
        
        # ఆడియో ప్లేయర్
        if "audio" in m and m["audio"] is not None:
            st.audio(m["audio"], format="audio/mp3")

        c1, c2, _ = st.columns([0.08, 0.15, 0.77])
        with c1:
            if st.button("🗑️", key=f"msg_del_{idx}"):
                msg_to_delete = idx
        with c2:
            if "audio" in m and m["audio"] is not None:
                st.download_button(
                    label="📥 MP3 డీలొడ్", 
                    data=m["audio"], 
                    file_name=f"spiritual_audio_{idx+1}.mp3", 
                    mime="audio/mp3",
                    key=f"audio_dl_{idx}"
                )

# మెసేజ్ తొలగింపు ప్రాసెస్
if msg_to_delete is not None:
    current_chat["messages"].pop(msg_to_delete)
    st.rerun()

# --- 5. టెక్స్ట్ ఇన్‌పుట్ అండ్ వాయిస్ కన్వర్షన్ ---
st.divider()
user_text = st.text_area("ఆడియోగా మార్చాలనుకుంటున్న తెలుగు టెక్స్ట్‌ని ఇక్కడ పేస్ట్ చేయండి:", height=120, placeholder="ఉదాహరణకు: బాబా చెప్పారు... ఓం శాంతి.")

if st.button("🔊 వాయిస్ క్రియేట్ చేయి (Convert to Speech)", type="primary", use_container_width=True):
    if user_text.strip():
        with st.spinner("ఆధ్యాత్మిక వాయిస్ తయారవుతోంది... ప్రశాంతంగా ఉండండి..."):
            try:
                # టెక్స్ట్ క్లీనింగ్
                clean_txt = user_text.replace("*", "").replace("#", "")
                
                # gTTS తో తెలుగు స్పీచ్ జనరేట్ చేయడం
                tts = gTTS(text=clean_txt, lang='te')
                f = io.BytesIO()
                tts.write_to_fp(f)
                f.seek(0)
                audio_bytes = f.getvalue()

                # సెషన్ స్టేట్‌లో సేవ్ చేయడం
                current_chat["messages"].append({
                    "text": user_text,
                    "audio": audio_bytes
                })

                # టైటిల్ సెట్ చేయడం
                if len(current_chat["messages"]) == 1 or current_chat["title"] == "కొత్త ఆడియో నోట్":
                    current_chat["title"] = user_text[:20] + ("..." if len(user_text) > 20 else "")

                st.success("వాయిస్ విజయవంతంగా తయారైంది! పైన ప్లే చేసి లేదా MP3 గా డోన్లోడ్ చేసుకోండి.")
                st.rerun()

            except Exception as e:
                st.error(f"వాయిస్ తయారు చేయడంలో లోపం వచ్చింది: {e}")
    else:
        st.warning("దయచేసి ఏదైనా టెక్స్ట్‌ని ఎంటర్ చేయండి.")
