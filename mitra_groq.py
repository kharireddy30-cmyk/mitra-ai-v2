import streamlit as st
from groq import Groq
import requests
from gtts import gTTS
import io
import time
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from supabase import create_client, Client

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI - Ultimate", layout="wide", page_icon="🙏")

# --- 2. కనెక్షన్లు ---
def initialize_all():
    try:
        supabase_client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        ai_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        return supabase_client, ai_client, st.secrets["MY_EMAIL"], st.secrets["MY_PASSWORD"]
    except Exception as e:
        st.error(f"Settings Error: {e}")
        return None, None, None, None

supabase, client, SECURE_EMAIL, SECURE_PASSWORD = initialize_all()
if not supabase: st.stop()

# --- 3. లాగిన్ సిస్టమ్ ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.title("🔐 మిత్ర ఏఐ - ప్రవేశం")
    u_mail = st.text_input("ఇమెయిల్:")
    u_pass = st.text_input("పాస్‌వర్డ్:", type="password")
    if st.button("ప్రవేశించు"):
        if u_mail == SECURE_EMAIL and str(u_pass) == str(SECURE_PASSWORD):
            st.session_state.authenticated = True
            st.rerun()
        else: st.error("తప్పుడు వివరాలు!")
    st.stop()

# --- 4. బ్యాకప్ ఏఐ లాజిక్స్ (Fallbacks) ---
def ask_openrouter(messages):
    try:
        res = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"},
            json={"model": "meta-llama/llama-3.1-8b-instruct:free", "messages": messages}
        )
        return res.json()['choices'][0]['message']['content']
    except: return None

def ask_huggingface(prompt):
    try:
        headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
        res = requests.post("https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct", 
                            headers=headers, json={"inputs": prompt})
        return res.json()[0]['generated_text'].split("assistant\n")[-1] if res.status_code == 200 else None
    except: return None

# --- 5. హెల్పర్ ఫంక్షన్లు ---
def get_clean_text(text):
    for char in ['*', '#', '_', '`', ':', '(', ')', '[', ']', '-']: text = text.replace(char, ' ')
    return text.strip()

def load_memory():
    try:
        res = supabase.table("mitra_settings").select("*").eq("id", "current").execute()
        return res.data[0]["intelligence"] if res.data else "నువ్వు ఒక ఆధ్యాత్మిక మిత్రుడివి."
    except: return "మిత్ర ఏఐ"

# --- 6. సైడ్‌బార్ (చరిత్ర & డౌన్‌లోడ్) ---
with st.sidebar:
    st.title("🕉️ మిత్ర కంట్రోల్స్")
    current_intel = load_memory()
    if st.button("➕ కొత్త చాట్", use_container_width=True):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.rerun()
    
    if st.session_state.get("messages"):
        chat_txt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("📥 చాట్ సేవ్ చేయండి (Text)", chat_txt, file_name=f"Mitra_Chat.txt")

    st.subheader("📜 గత చరిత్ర")
    try:
        history = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).limit(5).execute().data
        for chat in history:
            if st.button(f"💬 {chat.get('title', 'Chat')[:15]}", key=chat['id']):
                st.session_state.chat_id, st.session_state.messages = chat['id'], chat['messages']
                st.rerun()
    except: pass

# --- 7. మెయిన్ స్క్రీన్ ---
if "messages" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages = []

st.header("🔱 మిత్ర ఆధ్యాత్మిక సహాయకుడు")

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            try:
                clean_m = get_clean_text(m["content"])
                tts = gTTS(text=clean_m, lang='te')
                f = io.BytesIO(); tts.write_to_fp(f)
                st.audio(f, format="audio/mp3")
                st.download_button(label="📥 ఆడియో డౌన్లోడ్", data=f.getvalue(), file_name=f"voice_{i}.mp3", key=f"dl_{i}")
            except: pass

# --- 8. ఇన్‌పుట్ & స్మార్ట్ ఏఐ లాజిక్ ---
v = mic_recorder(start_prompt="🎙️ వాయిస్", stop_prompt="🛑 ఆపండి", key='mic')
t = st.chat_input("మిత్రను అడగండి...")
prompt = t
if v:
    try:
        b = io.BytesIO(v['bytes']); b.name = "a.wav"
        prompt = client.audio.transcriptions.create(file=b, model="whisper-large-v3", language="te").text
    except: st.error("వాయిస్ లోపం.")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("మిత్ర జవాబిస్తున్నాడు..."):
            ans = None
            try:
                # Groq ప్రయత్నం (llama-3.1-8b-instant మోడల్ తో)
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant", 
                    messages=[{"role": "system", "content": current_intel}] + st.session_state.messages
                )
                ans = res.choices[0].message.content
            except:
                # OpenRouter ప్రయత్నం
                ans = ask_openrouter([{"role": "system", "content": current_intel}] + st.session_state.messages)
                if not ans:
                    # Hugging Face ప్రయత్నం
                    ans = ask_huggingface(f"System: {current_intel}\nUser: {prompt}")

            if ans:
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                try:
                    supabase.table("mitra_chats").upsert({"id": st.session_state.chat_id, "title": "Spiritual Chat", "messages": st.session_state.messages, "updated_at": "now()"}).execute()
                except: pass
                st.rerun()
