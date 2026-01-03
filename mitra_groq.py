import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import json
import os
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from supabase import create_client, Client

# 1. పేజీ కాన్ఫిగరేషన్
st.set_page_config(page_title="Mitra AI Pro - Harsha", layout="wide", page_icon="🤖")

# --- 2. సెక్యూరిటీ మరియు క్లౌడ్ కనెక్షన్లు ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    SECURE_EMAIL = st.secrets["MY_EMAIL"]
    SECURE_PASSWORD = st.secrets["MY_PASSWORD"]
except Exception as e:
    st.error(f"Secrets లో సమస్య ఉంది: {e}")
    st.stop()

# --- 3. అత్యంత సురక్షితమైన లాగిన్ సిస్టమ్ ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Mitra AI Private Access")
    st.info("హర్ష గారు, దయచేసి మీ వివరాలతో లాగిన్ అవ్వండి.")
    
    col1, col2 = st.columns(2)
    with col1:
        email_input = st.text_input("Email ID")
    with col2:
        pass_input = st.text_input("Password", type="password")
    
    if st.button("Access Mitra"):
        # str() వాడటం వల్ల నంబర్ పాస్‌వర్డ్స్ కూడా పనిచేస్తాయి
        if email_input == SECURE_EMAIL and str(pass_input) == str(SECURE_PASSWORD):
            st.session_state.authenticated = True
            st.success("లాగిన్ విజయవంతం!")
            st.rerun()
        else:
            st.error("తప్పుడు వివరాలు! ఇది హర్ష గారి వ్యక్తిగత ఏఐ.")
    st.stop() 

# --- 4. సహాయక ఫంక్షన్లు ---
def clean_for_speech(text):
    unwanted_chars = ['*', '#', '_', '`', ':', '-']
    for char in unwanted_chars:
        text = text.replace(char, ' ')
    return text

def load_settings_from_cloud():
    try:
        res = supabase.table("mitra_settings").select("*").eq("id", "current").execute()
        if res.data:
            return res.data[0]["intelligence"]
    except:
        pass
    return "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి సహాయం చేయాలి."

def save_settings_to_cloud(intel_text):
    try:
        supabase.table("mitra_settings").upsert({"id": "current", "intelligence": intel_text}).execute()
        return True
    except:
        return False

def save_chat_to_cloud(chat_id, messages, title):
    data = {"id": chat_id, "title": title, "messages": messages, "updated_at": "now()"}
    supabase.table("mitra_chats").upsert(data).execute()

def load_chats_from_cloud():
    try:
        response = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).execute()
        return response.data
    except:
        return []

# --- 5. సైడ్‌బార్ (సెట్టింగ్స్) ---
with st.sidebar:
    st.title("⚙️ Workspace Settings")
    st.subheader("🧠 మిత్ర జ్ఞాపకశక్తి")
    current_intel = load_settings_from_cloud()
    new_intel = st.text_area("Intelligence Settings:", value=current_intel, height=150)
    if st.button("Save Intelligence"):
        if save_settings_to_cloud(new_intel):
            st.success("జ్ఞాపకశక్తి సేవ్ అయ్యింది!")
            st.rerun()

    st.divider()
    if st.button("➕ Start New Chat"):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.session_state.chat_title = "కొత్త సంభాషణ"
        st.rerun()

    st.subheader("☁️ Recent Cloud Chats")
    cloud_chats = load_chats_from_cloud()
    for chat in cloud_chats:
        cid = chat['id']
        title = chat.get('title', cid)
        if st.button(f"💬 {title[:15]}", key=f"btn_{cid}"):
            st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title = cid, chat['messages'], title
            st.rerun()

# --- 6. మెయిన్ చాట్ ఏరియా ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages, st.session_state.chat_title = [], "కొత్త సంభాషణ"

st.header(f"🚀 {st.session_state.chat_title}")

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

audio = mic_recorder(start_prompt="🎙️ Voice", stop_prompt="🛑 Stop", key='recorder')
prompt = st.chat_input("Ask Mitra something...")

user_text = prompt
if audio and not prompt:
    trans = client.audio.transcriptions.create(file=("audio.wav", audio['bytes']), model="whisper-large-v3", language="te")
    user_text = trans.text

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"): st.markdown(user_text)
    
    with st.chat_message("assistant"):
        # లూపింగ్ సమస్యను ఆపడానికి ఇక్కడ జాగ్రత్తగా కోడ్ రాశాను
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": current_intel}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        
        try:
            tts = gTTS(text=clean_for_speech(ans), lang='te')
            fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp)
        except: pass
        
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_chat_to_cloud(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
        # ఇక్కడ rerun తీసేయడం వల్ల జవాబు ఆగిపోకుండా వెళ్లే సమస్య తీరిపోతుంది

