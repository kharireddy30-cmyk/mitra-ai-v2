import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import json
import os
from datetime import datetime
from streamlit_mic_recorder import mic_recorder

# 1. పేజీ కాన్ఫిగరేషన్
st.set_page_config(page_title="Mitra AI Pro - Harsha", layout="wide", page_icon="🤖")

# 2. ఫోల్డర్ల సెటప్
CHATS_DIR = "chats"
SETTINGS_FILE = "mitra_settings.json"
if not os.path.exists(CHATS_DIR): os.makedirs(CHATS_DIR)

# 3. వాయిస్ అవుట్‌పుట్ కోసం గుర్తులను క్లీన్ చేసే ఫంక్షన్
def clean_for_speech(text):
    # ఆస్టరిస్క్ (*), హాష్ (#), అండర్ స్కోర్ (_) వంటి గుర్తులను తొలగిస్తుంది
    unwanted_chars = ['*', '#', '_', '`', ':', '-']
    clean_text = text
    for char in unwanted_chars:
        clean_text = clean_text.replace(char, ' ')
    return clean_text

# 4. సెట్టింగ్స్ లోడ్ చేయడం
if not os.path.exists(SETTINGS_FILE):
    default_settings = {"intelligence": "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి సహాయం చేయాలి. సమాధానం ఇచ్చేటప్పుడు ఎక్కువ గుర్తులు వాడకు."}
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(default_settings, f)

with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
    current_settings = json.load(f)

# 5. లాగిన్ సిస్టమ్
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Mitra AI Login")
    email = st.text_input("Email ID")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email == "harsha@email.com" and password == "mitra123":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("తప్పుడు వివరాలు! మరొకసారి ప్రయత్నించండి.")
    st.stop()

# 6. API Key (Secrets లో ఉండాలి)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- సహాయక ఫంక్షన్లు (Data Management) ---
def save_chat(chat_id, messages, title):
    data = {"title": title, "messages": messages}
    with open(f"{CHATS_DIR}/{chat_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_chat(chat_id):
    path = f"{CHATS_DIR}/{chat_id}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list): return {"title": chat_id, "messages": data}
            return data
    return {"title": "New Conversation", "messages": []}

# --- సైడ్‌బార్ (సెట్టింగ్స్ మరియు హిస్టరీ) ---
with st.sidebar:
    st.title("⚙️ Workspace Settings")
    
    # మేధస్సు (Intelligence) సెట్టింగ్
    new_intel = st.text_area("మిత్ర మేధస్సు (System Prompt):", 
                             value=current_settings["intelligence"], height=150)
    if st.button("Save Intelligence"):
        current_settings["intelligence"] = new_intel
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current_settings, f)
        st.success("మేధస్సు అప్‌డేట్ అయ్యింది!")

    st.divider()
    if st.button("➕ Start New Chat"):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.session_state.chat_title = "కొత్త సంభాషణ"
        st.rerun()

    st.subheader("Recent Chats")
    files = sorted([f for f in os.listdir(CHATS_DIR) if f.endswith(".json")], reverse=True)
    for f in files:
        cid = f.replace(".json", "")
        chat_data = load_chat(cid)
        title = chat_data.get("title", cid)

        col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
        with col1:
            if st.button(f"💬 {title[:10]}", key=f"btn_{cid}"):
                st.session_state.chat_id = cid
                st.session_state.messages = chat_data["messages"]
                st.session_state.chat_title = title
                st.rerun()
        with col2:
            if st.button("✏️", key=f"edit_{cid}"):
                st.session_state.edit_target = cid
        with col3:
            if st.button("🗑️", key=f"del_full_{cid}"):
                os.remove(f"{CHATS_DIR}/{cid}.json")
                st.rerun()

    if "edit_target" in st.session_state:
        new_name = st.text_input("కొత్త పేరు:")
        if st.button("Rename OK"):
            c_data = load_chat(st.session_state.edit_target)
            save_chat(st.session_state.edit_target, c_data["messages"], new_name)
            del st.session_state.edit_target
            st.rerun()

# --- మెయిన్ చాట్ ఏరియా ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages = []
    st.session_state.chat_title = "కొత్త సంభాషణ"

st.header(f"🚀 {st.session_state.chat_title}")

# మెసేజ్‌లను ప్రదర్శించడం
for i, msg in enumerate(st.session_state.messages):
    col_msg, col_del = st.columns([0.9, 0.1])
    with col_msg:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                # వాయిస్ అవుట్‌పుట్ (క్లీన్ చేసిన టెక్స్ట్‌తో)
                try:
                    speech_text = clean_for_speech(msg["content"])
                    tts = gTTS(text=speech_text, lang='te')
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    st.audio(fp)
                except: pass
                st.download_button("📥 Save Text", msg["content"], file_name=f"Mitra_{i}.txt", key=f"dl_{i}")
    with col_del:
        if st.button("🗑️", key=f"del_msg_{i}"):
            st.session_state.messages.pop(i)
            save_chat(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
            st.rerun()

# ఇన్‌పుట్ సెక్షన్
audio = mic_recorder(start_prompt="🎙️ Voice", stop_prompt="🛑 Stop", key='recorder')
prompt = st.chat_input("Ask Mitra something...")

user_text = prompt if prompt else None
if audio and not prompt:
    with st.spinner("వింటున్నాను..."):
        trans = client.audio.transcriptions.create(file=("audio.wav", audio['bytes']), model="whisper-large-v3", language="te")
        user_text = trans.text

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"): st.markdown(user_text)

    with st.chat_message("assistant"):
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": current_settings["intelligence"]}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        
        # వాయిస్ అవుట్‌పుట్ (క్లీన్ చేసిన టెక్స్ట్‌తో)
        speech_text = clean_for_speech(ans)
        tts = gTTS(text=speech_text, lang='te')
        fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp)
        
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_chat(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
        st.rerun()