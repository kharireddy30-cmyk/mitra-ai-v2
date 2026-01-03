import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import os
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from supabase import create_client, Client

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI Pro - Harsha", layout="wide", page_icon="🤖")

# --- 2. క్లౌడ్ కనెక్షన్లు & సెక్యూరిటీ ---
try:
    # సుపబేస్ మరియు గ్రోక్ కీలు
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    # లాగిన్ క్రెడెన్షియల్స్
    SECURE_EMAIL = st.secrets["MY_EMAIL"]
    SECURE_PASSWORD = st.secrets["MY_PASSWORD"]
except Exception as e:
    st.error(f"Secrets లో సమస్య ఉంది: {e}")
    st.stop()

# --- 3. వ్యక్తిగత లాగిన్ సిస్టమ్ ---
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
    
    if st.button("Access Mitra", use_container_width=True):
        if email_input == SECURE_EMAIL and str(pass_input) == str(SECURE_PASSWORD):
            st.session_state.authenticated = True
            st.success("లాగిన్ విజయవంతం!")
            st.rerun()
        else:
            st.error("తప్పుడు వివరాలు! ఇది హర్ష గారి వ్యక్తిగత ఏఐ.")
    st.stop()

# --- 4. సహాయక ఫంక్షన్లు (Logic) ---
def clean_for_speech(text):
    unwanted = ['*', '#', '_', '`', ':', '-']
    for char in unwanted:
        text = text.replace(char, ' ')
    return text

def load_settings():
    try:
        res = supabase.table("mitra_settings").select("*").eq("id", "current").execute()
        if res.data:
            return res.data[0]["intelligence"]
    except:
        pass
    return "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి సహాయం చేయాలి."

def save_chat(chat_id, messages, title):
    data = {"id": chat_id, "title": title, "messages": messages, "updated_at": "now()"}
    supabase.table("mitra_chats").upsert(data).execute()

def delete_chat(chat_id):
    supabase.table("mitra_chats").delete().eq("id", chat_id).execute()
    st.rerun()

# --- 5. సైడ్‌బార్ (Manage Chats & Memory) ---
with st.sidebar:
    st.title("⚙️ Workspace Settings")
    
    # జ్ఞాపకశక్తి భాగం
    st.subheader("🧠 మిత్ర జ్ఞాపకశక్తి")
    current_intel = load_settings()
    new_intel = st.text_area("Intelligence Settings:", value=current_intel, height=150)
    if st.button("💾 Save Intelligence"):
        supabase.table("mitra_settings").upsert({"id": "current", "intelligence": new_intel}).execute()
        st.success("జ్ఞాపకశక్తి అప్‌డేట్ అయ్యింది!")

    st.divider()
    if st.button("➕ Start New Chat", use_container_width=True):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.session_state.chat_title = "కొత్త సంభాషణ"
        st.rerun()

    # పాత చాట్‌ల నిర్వహణ
    st.subheader("☁️ Recent Cloud Chats")
    try:
        cloud_chats = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).execute().data
        for chat in cloud_chats:
            cid = chat['id']
            title = chat.get('title', cid)
            
            col_t, col_e, col_d = st.columns([0.6, 0.2, 0.2])
            with col_t:
                if st.button(f"💬 {title[:15]}", key=f"btn_{cid}"):
                    st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title = cid, chat['messages'], title
                    st.rerun()
            with col_e:
                if st.button("✏️", key=f"edit_{cid}"):
                    st.session_state.rename_id = cid
            with col_d:
                if st.button("🗑️", key=f"del_{cid}"):
                    delete_chat(cid)
            
            # రీనేమ్ చేయడానికి ఇన్‌పుట్ బాక్స్
            if "rename_id" in st.session_state and st.session_state.rename_id == cid:
                new_name = st.text_input("కొత్త పేరు:", value=title, key=f"input_{cid}")
                if st.button("Update", key=f"upd_{cid}"):
                    save_chat(cid, chat['messages'], new_name)
                    del st.session_state.rename_id
                    st.rerun()
    except:
        st.write("చాట్‌లు లోడ్ కాలేదు.")

# --- 6. మెయిన్ చాట్ ఇంటర్‌ఫేస్ ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages, st.session_state.chat_title = [], "కొత్త సంభాషణ"

st.header(f"🚀 {st.session_state.chat_title}")

# చాట్ హిస్టరీ డిస్‌ప్లే
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            # డౌన్‌లోడ్ మరియు వాయిస్ ఆప్షన్లు
            col_a, col_b = st.columns([0.8, 0.2])
            with col_b:
                st.download_button("📥 Save", msg["content"], file_name=f"Mitra_Chat_{i}.txt", key=f"dl_{i}")
            try:
                clean_text = clean_for_speech(msg["content"])
                tts = gTTS(text=clean_text, lang='te')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                st.audio(fp)
            except:
                pass

# ఇన్‌పుట్ సెక్షన్ (Voice & Text)
st.divider()
audio = mic_recorder(start_prompt="🎙️ వాయిస్ టైపింగ్", stop_prompt="🛑 ఆపండి", key='recorder')
prompt = st.chat_input("మిత్రను ఏదైనా అడగండి...")

user_text = prompt
if audio:
    with st.spinner("వింటున్నాను..."):
        try:
            # Whisper మోడల్ తో వాయిస్ రికార్డింగ్ ఫిక్స్
            audio_bio = io.BytesIO(audio['bytes'])
            audio_bio.name = "audio.wav"
            trans = client.audio.transcriptions.create(file=audio_bio, model="whisper-large-v3", language="te")
            user_text = trans.text
        except Exception as e:
            st.error(f"వాయిస్ సమస్య: {e}")

# జవాబు ఇచ్చే ప్రక్రియ
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
    
    with st.chat_message("assistant"):
        with st.spinner("ఆలోచిస్తున్నాను..."):
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": current_intel}] + st.session_state.messages
            )
            ans = res.choices[0].message.content
            st.markdown(ans)
            
            # వాయిస్ జవాబు
            clean_ans = clean_for_speech(ans)
            tts_ans = gTTS(text=clean_ans, lang='te')
            fp_ans = io.BytesIO()
            tts_ans.write_to_fp(fp_ans)
            st.audio(fp_ans)
            
            # మెసేజ్ సేవ్ చేయడం
            st.session_state.messages.append({"role": "assistant", "content": ans})
            save_chat(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
