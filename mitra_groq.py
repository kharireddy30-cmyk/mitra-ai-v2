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
st.set_page_config(page_title="Mitra AI Pro - Cloud Edition", layout="wide", page_icon="🤖")

# 2. Supabase క్లౌడ్ కనెక్షన్ సెటప్ (Secrets నుండి)
# ఈ వివరాలను మనం తర్వాత Streamlit Settings లో ఇస్తాం
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("క్లౌడ్ కనెక్షన్ వివరాలు ఇంకా సెట్ చేయలేదు. దయచేసి Secrets లో URL మరియు Key ఇవ్వండి.")

# 3. Groq ఏపీఐ కీ
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 4. వాయిస్ అవుట్‌పుట్ కోసం గుర్తులను క్లీన్ చేసే ఫంక్షన్
def clean_for_speech(text):
    unwanted_chars = ['*', '#', '_', '`', ':', '-']
    clean_text = text
    for char in unwanted_chars:
        clean_text = clean_text.replace(char, ' ')
    return clean_text

# --- సహాయక ఫంక్షన్లు (Cloud Data Management) ---

def save_chat_to_cloud(chat_id, messages, title):
    """చాట్ డేటాను క్లౌడ్ డేటాబేస్ లో భద్రపరుస్తుంది"""
    try:
        data = {
            "id": chat_id,
            "title": title,
            "messages": messages,
            "updated_at": "now()"
        }
        supabase.table("mitra_chats").upsert(data).execute()
    except Exception as e:
        st.error(f"Save Error: {e}")

def load_chats_from_cloud():
    """అన్ని పాత సంభాషణలను క్లౌడ్ నుండి తెస్తుంది"""
    try:
        response = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).execute()
        return response.data
    except:
        return []

def delete_chat_from_cloud(chat_id):
    """మొత్తం చాట్ ను క్లౌడ్ నుండి తొలగిస్తుంది"""
    try:
        supabase.table("mitra_chats").delete().eq("id", chat_id).execute()
    except Exception as e:
        st.error(f"Delete Error: {e}")

# --- సైడ్‌బార్ (సెట్టింగ్స్ మరియు క్లౌడ్ హిస్టరీ) ---
with st.sidebar:
    st.title("⚙️ Workspace Settings")
    
    # మిత్ర మేధస్సు (Intelligence) - ఇది ప్రస్తుతం ఫిక్స్‌డ్ గా ఉంటుంది లేదా క్లౌడ్ కి మార్చుకోవచ్చు
    intel_prompt = "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి సహాయం చేయాలి. సమాధానం ఇచ్చేటప్పుడు ఎక్కువ గుర్తులు వాడకు."

    if st.button("➕ Start New Chat"):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.session_state.chat_title = "కొత్త సంభాషణ"
        st.rerun()

    st.divider()
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
            # క్లౌడ్ లో పేరు మార్చడం
            target_chat = next((c for c in cloud_chats if c['id'] == st.session_state.edit_target), None)
            if target_chat:
                save_chat_to_cloud(st.session_state.edit_target, target_chat['messages'], new_name)
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

# ఇన్‌పుట్ సెక్షన్
audio = mic_recorder(start_prompt="🎙️ Voice Input", stop_prompt="🛑 Stop", key='recorder')
prompt = st.chat_input("Ask Mitra something...")

user_text = prompt if prompt else None
if audio and not prompt:
    with st.spinner("వింటున్నాను..."):
        try:
            trans = client.audio.transcriptions.create(file=("audio.wav", audio['bytes']), model="whisper-large-v3", language="te")
            user_text = trans.text
        except Exception as e:
            st.error(f"Voice Error: {e}")

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"): st.markdown(user_text)

    with st.chat_message("assistant"):
        try:
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": intel_prompt}] + st.session_state.messages
            )
            ans = res.choices[0].message.content
            st.markdown(ans)
            
            # వాయిస్ అవుట్‌పుట్
            speech_text = clean_for_speech(ans)
            tts = gTTS(text=speech_text, lang='te')
            fp = io.BytesIO(); tts.write_to_fp(fp); st.audio(fp)
            
            st.session_state.messages.append({"role": "assistant", "content": ans})
            # క్లౌడ్ లో సేవ్ చేయడం
            save_chat_to_cloud(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
            st.rerun()
        except Exception as e:
            st.error(f"AI Error: {e}")
