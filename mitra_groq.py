import streamlit as st
from groq import Groq
import requests
from gtts import gTTS
import io
import os
import time
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from supabase import create_client, Client

# --- 1. పేజీ సెట్టింగ్స్ & స్టైలింగ్ ---
st.set_page_config(
    page_title="Mitra AI - The Ultimate Dharma Sarathi",
    layout="wide",
    page_icon="🙏"
)

# --- 2. కనెక్షన్లు (Error Handling తో) ---
def initialize_all():
    try:
        # సుపబేస్ కనెక్షన్
        sb_url = st.secrets["SUPABASE_URL"]
        sb_key = st.secrets["SUPABASE_KEY"]
        supabase_client = create_client(sb_url, sb_key)
        
        # Groq ఏఐ కనెక్షన్
        ai_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # అడ్మిన్ వివరాలు
        admin_mail = st.secrets["MY_EMAIL"]
        admin_pass = st.secrets["MY_PASSWORD"]
        
        return supabase_client, ai_client, admin_mail, admin_pass
    except Exception as e:
        st.error(f"సెట్టింగ్స్ లోపం: {e}")
        return None, None, None, None

supabase, client, SECURE_EMAIL, SECURE_PASSWORD = initialize_all()

if not supabase:
    st.stop()

# --- 3. లాగిన్ సిస్టమ్ ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 మిత్ర ఏఐ - ప్రవేశం")
    st.info("హర్ష గారు, మీ వివరాలతో లాగిన్ అవ్వండి.")
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        u_mail = st.text_input("ఇమెయిల్:")
    with l_col2:
        u_pass = st.text_input("పాస్‌వర్డ్:", type="password")
    
    if st.button("ప్రవేశించు (Login)", use_container_width=True):
        if u_mail == SECURE_EMAIL and str(u_pass) == str(SECURE_PASSWORD):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("తప్పుడు వివరాలు! మళ్ళీ ప్రయత్నించండి.")
    st.stop()

# --- 4. బ్యాకప్ ఏఐ లాజిక్స్ (Failover Layers) ---
def ask_openrouter(messages):
    """రెండవ రక్షణ వలయం: OpenRouter"""
    try:
        res = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}"},
            json={
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": messages
            }
        )
        return res.json()['choices'][0]['message']['content']
    except: return None

def ask_huggingface(prompt):
    """మూడవ రక్షణ వలయం: Hugging Face"""
    try:
        API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
        headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
        res = requests.post(API_URL, headers=headers, json={"inputs": prompt})
        if res.status_code == 200:
            return res.json()[0]['generated_text'].split("assistant\n")[-1]
    except: return None

# --- 5. కోర్ ఫంక్షన్లు (Memory & Cleaning) ---
def get_clean_text(text):
    for char in ['*', '#', '_', '`', ':', '(', ')', '[', ']', '-']:
        text = text.replace(char, ' ')
    return text.strip()

def load_memory():
    try:
        res = supabase.table("mitra_settings").select("*").eq("id", "current").execute()
        return res.data[0]["intelligence"] if res.data else "నువ్వు మిత్ర అనే ఏఐవి."
    except: return "నువ్వు ఒక ఆధ్యాత్మిక మిత్రుడివి."

def save_chat(cid, msgs, title):
    try:
        data = {"id": cid, "title": title, "messages": msgs, "updated_at": "now()"}
        supabase.table("mitra_chats").upsert(data).execute()
    except: pass

# --- 6. సైడ్‌బార్ (History & Controls) ---
with st.sidebar:
    st.title("🕉️ మిత్ర కంట్రోల్స్")
    current_intel = load_memory()
    new_intel = st.text_area("ఏఐ జ్ఞాపకశక్తి:", value=current_intel, height=180)
    if st.button("💾 మెమరీ సేవ్"):
        supabase.table("mitra_settings").upsert({"id": "current", "intelligence": new_intel}).execute()
        st.success("మెమరీ అప్‌డేట్ అయ్యింది!")
    
    st.divider()
    if st.button("➕ కొత్త సంభాషణ"):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages, st.session_state.chat_title = [], "కొత్త చాట్"
        st.rerun()

    st.subheader("📜 గత చరిత్ర")
    try:
        history = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).execute().data
        for chat in history:
            cid, ctitle = chat['id'], chat.get('title', 'Chat')
            c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
            with c1:
                if st.button(f"💬 {ctitle[:10]}", key=f"b_{cid}"):
                    st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title = cid, chat['messages'], ctitle
                    st.rerun()
            with c2:
                if st.button("✏️", key=f"r_{cid}"): st.session_state.rename_id = cid
            with c3:
                if st.button("🗑️", key=f"d_{cid}"):
                    supabase.table("mitra_chats").delete().eq("id", cid).execute()
                    st.rerun()
    except: pass

# --- 7. మెయిన్ ఇంటర్‌ఫేస్ & చాట్ ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages, st.session_state.chat_title = [], "కొత్త సంభాషణ"

st.header(f"🔱 {st.session_state.chat_title}")

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            try:
                clean_m = get_clean_text(m["content"])
                tts = gTTS(text=clean_m, lang='te')
                f = io.BytesIO(); tts.write_to_fp(f)
                st.audio(f, format="audio/mp3", key=f"au_{i}_{st.session_state.chat_id}")
            except: pass

# --- 8. ఇన్‌పుట్ & స్మార్ట్ స్విచ్చింగ్ ఏఐ ---
st.divider()
v = mic_recorder(start_prompt="🎙️ వాయిస్", stop_prompt="🛑 ఆపు", key='mic')
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
            # ప్రయత్నం 1: Groq
            try:
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant", 
                    messages=[{"role": "system", "content": current_intel}] + st.session_state.messages
                )
                ans = res.choices[0].message.content
            except:
                # ప్రయత్నం 2: OpenRouter (Fallback)
                st.warning("ప్రధాన సర్వర్ బిజీ.. OpenRouter ని వాడుతున్నాను..")
                ans = ask_openrouter([{"role": "system", "content": current_intel}] + st.session_state.messages)
                
                if not ans:
                    # ప్రయత్నం 3: Hugging Face (Final Fallback)
                    st.warning("చివరి ప్రయత్నంగా Hugging Face ని వాడుతున్నాను..")
                    ans = ask_huggingface(f"System: {current_intel}\nUser: {prompt}")

            if ans:
                st.markdown(ans)
                try:
                    c_ans = get_clean_text(ans)
                    tts_ans = gTTS(text=c_ans, lang='te')
                    af = io.BytesIO(); tts_ans.write_to_fp(af)
                    st.audio(af, format="audio/mp3")
                except: pass
                
                st.session_state.messages.append({"role": "assistant", "content": ans})
                save_chat(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
                st.rerun()
            else:
                st.error("అన్ని సర్వర్లు బిజీగా ఉన్నాయి. దయచేసి కాసేపటి తర్వాత ప్రయత్నించండి.")
