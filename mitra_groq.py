import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import json
import os
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from supabase import create_client, Client

# 1. పేజీ కాన్ఫిగరేషన్ (మీ పాత టైటిల్ మరియు ఐకాన్ అలాగే ఉన్నాయి)
st.set_page_config(page_title="Mitra AI Pro - Harsha", layout="wide", page_icon="🤖")

# 2. క్లౌడ్ కనెక్షన్లు (Secrets నుండి సురక్షితంగా తీసుకుంటుంది)
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    # మీరు కోరిన సురక్షిత లాగిన్ వివరాలు
    SECURE_EMAIL = st.secrets["MY_EMAIL"]
    SECURE_PASSWORD = st.secrets["MY_PASSWORD"]
except Exception as e:
    st.error("సెక్యూరిటీ వివరాలు (Secrets) సరిగ్గా లేవు. దయచేసి వెబ్ సెట్టింగ్స్ చెక్ చేయండి.")

# --- 3. అత్యంత సురక్షితమైన లాగిన్ సిస్టమ్ (మీరు కోరిన వ్యక్తిగత లాగిన్) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Mitra AI Private Access")
    email_input = st.text_input("మీ పర్సనల్ మెయిల్ ఐడి (Email)")
    pass_input = st.text_input("మీ రహస్య పాస్‌వర్డ్ (Password)", type="password")
    
    if st.button("Access Mitra"):
        if email_input == SECURE_EMAIL and pass_input == SECURE_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("తప్పుడు వివరాలు! ఇది హర్ష గారి వ్యక్తిగత ఏఐ.")
    st.stop()

# 4. మీ పాత వాయిస్ క్లీనింగ్ ఫంక్షన్ (అలాగే ఉంది)
def clean_for_speech(text):
    unwanted_chars = ['*', '#', '_', '`', ':', '-']
    clean_text = text
    for char in unwanted_chars:
        clean_text = clean_text.replace(char, ' ')
    return clean_text

# --- 5. మిత్ర మేధస్సు/మెమరీ (Cloud Settings) ---
def load_settings_from_cloud():
    try:
        res = supabase.table("mitra_settings").select("*").eq("id", "current").execute()
        if res.data:
            return res.data[0]["intelligence"]
        return "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి సహాయం చేయాలి. సమాధానం ఇచ్చేటప్పుడు ఎక్కువ గుర్తులు వాడకు."
    except:
        return "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి సహాయం చేయాలి."

def save_settings_to_cloud(intel_text):
    try:
        supabase.table("mitra_settings").upsert({"id": "current", "intelligence": intel_text}).execute()
    except Exception as e:
        st.error(f"Settings Error: {e}")

# --- 6. క్లౌడ్ డేటా మేనేజ్మెంట్ (మునుపటిలాగే) ---
def save_chat_to_cloud(chat_id, messages, title):
    data = {"id": chat_id, "title": title, "messages": messages, "updated_at": "now()"}
    supabase.table("mitra_chats").upsert(data).execute()

def load_chats_from_cloud():
    try:
        response = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).execute()
        return response.data
    except:
        return []

def delete_chat_from_cloud(chat_id):
    supabase.table("mitra_chats").delete().eq("id", chat_id).execute()

# --- 7. సైడ్‌బార్ (సెట్టింగ్స్ మరియు క్లౌడ్ హిస్టరీ) ---
with st.sidebar:
    st.title("⚙️ Workspace Settings")
    
    # మిత్ర మేధస్సు జ్ఞాపకశక్తి ఆప్షన్
    current_intel = load_settings_from_cloud()
    new_intel = st.text_area("మిత్ర మేధస్సు (System Prompt):", value=current_intel, height=150)
    if st.button("Save Intelligence"):
        save_settings_to_cloud(new_intel)
        st.success("మేధస్సు క్లౌడ్ లో సేవ్ అయ్యింది!")

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

        col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
        with col1:
            if st.button(f"💬 {title[:10]}", key=f"btn_{cid}"):
                st.session_state.chat_id = cid
                st.session_state.messages = chat['messages']
                st.session_state.chat_title = title
                st.rerun()
        with col2:
            if st.button("✏️", key=f"edit_{cid}"):
                st.session_state.edit_target = cid
        with col3:
            if st.button("🗑️", key=f"del_full_{cid}"):
                delete_chat_from_cloud(cid)
                st.rerun()

    if "edit_target" in st.session_state:
        new_name = st.text_input("కొత్త పేరు:")
        if st.button("Rename OK"):
            t_chat = next((c for c in cloud_chats if c['id'] == st.session_state.edit_target), None)
            if t_chat:
                save_chat_to_cloud(st.session_state.edit_target, t_chat['messages'], new_name)
                del st.session_state.edit_target
                st.rerun()

# --- 8. మెయిన్ చాట్ ఏరియా (మీ అసలు డిజైన్ అలాగే ఉంది) ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages = []
    st.session_state.chat_title = "కొత్త సంభాషణ"

st.header(f"🚀 {st.session_state.chat_title}")

for i, msg in enumerate(st.session_state.messages):
    col_msg, col_del = st.columns([0.9, 0.1])
    with col_msg:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
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
            save_chat_to_cloud(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
            st.rerun()

# 9. ఇన్‌పుట్ సెక్షన్ (మీ ఒరిజినల్ Whisper Voice ఇన్‌పుట్)
audio = mic_recorder(start_prompt="🎙️ Voice", stop_prompt="🛑 Stop", key='recorder')
prompt = st.chat_input("Ask Mitra something...")

user_text = prompt if prompt else None
if audio and not prompt:
    with st.spinner("వింటున్నాను..."):
        try:
            trans = client.audio.transcriptions.create(file=("audio.wav", audio['bytes']), model="whisper-large-v3", language="te")
            user_text = trans.text
        except: pass

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"): st.markdown(user_text)

    with st.chat_message("assistant"):
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": current_intel}] + st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        
        speech_text = clean_for_speech(ans)
        tts = gTTS(text=speech_text, lang='te')
        fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp)
        
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_chat_to_cloud(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
        st.rerun()
