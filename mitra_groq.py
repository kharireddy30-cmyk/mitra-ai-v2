import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import os
import time
import base64
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from supabase import create_client, Client

# --- 1. వెబ్‌సైట్ ప్రాథమిక సెట్టింగ్స్ (Page Config) ---
st.set_page_config(
    page_title="Mitra AI Pro - Harsha's Personal Assistant",
    layout="wide",
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

# --- 2. రహస్య కీలు మరియు క్లౌడ్ కనెక్షన్లు (Security & Connections) ---
def initialize_connections():
    """అన్ని ఏపీఐ కనెక్షన్లను మరియు సెక్యూరిటీ వివరాలను లోడ్ చేస్తుంది"""
    try:
        # సుపబేస్ కనెక్షన్ సెటప్ (డేటాబేస్ కోసం)
        sb_url: str = st.secrets["SUPABASE_URL"]
        sb_key: str = st.secrets["SUPABASE_KEY"]
        supabase_client: Client = create_client(sb_url, sb_key)
        
        # ఏఐ మోడల్ కనెక్షన్ (Groq Cloud)
        ai_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # హర్ష గారి వ్యక్తిగత లాగిన్ వివరాలు
        admin_mail = st.secrets["MY_EMAIL"]
        admin_pass = st.secrets["MY_PASSWORD"]
        
        return supabase_client, ai_client, admin_mail, admin_pass
    except Exception as e:
        st.error(f"సెట్టింగ్స్ లోడ్ చేయడంలో విఫలం: {e}")
        return None, None, None, None

# కనెక్షన్లను సిద్ధం చేయడం
supabase, client, SECURE_EMAIL, SECURE_PASSWORD = initialize_connections()

if not supabase or not client:
    st.warning("కనెక్షన్ సమస్యలు ఉన్నాయి. దయచేసి Secrets చెక్ చేయండి.")
    st.stop()

# --- 3. వ్యక్తిగత లాగిన్ వ్యవస్థ (Authentication System) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>🔐 మిత్ర ఏఐ ప్రైవేట్ యాక్సెస్</h1>", unsafe_allow_html=True)
    st.info("హర్ష గారు, దయచేసి మీ గుర్తింపును ధృవీకరించండి.")
    
    with st.container():
        l_col1, l_col2 = st.columns(2)
        with l_col1:
            u_mail = st.text_input("మీ ఇమెయిల్ ఐడి (Email):")
        with l_col2:
            u_pass = st.text_input("మీ పాస్‌వర్డ్ (Password):", type="password")
        
        if st.button("ప్రవేశించు (Login)", use_container_width=True):
            if u_mail == SECURE_EMAIL and str(u_pass) == str(SECURE_PASSWORD):
                st.session_state.authenticated = True
                st.success("ధృవీకరణ పూర్తయింది! స్వాగతం హర్ష గారు.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("తప్పుడు వివరాలు! ఇది కేవలం హర్ష గారి వ్యక్తిగత సహాయకుడి కోసం మాత్రమే.")
    st.stop()

# --- 4. కోర్ మేనేజ్‌మెంట్ లాజిక్ (Helper Functions) ---
def get_clean_audio_text(text_to_speak):
    """వాయిస్ జవాబు కోసం టెక్స్ట్ లో ఉన్న అనవసర గుర్తులను తొలగిస్తుంది"""
    bad_chars = ['*', '#', '_', '`', ':', '(', ')', '[', ']', '-', '\n', '\r']
    for char in bad_chars:
        text_to_speak = text_to_speak.replace(char, ' ')
    return text_to_speak.strip()

def load_mitra_memory():
    """క్లౌడ్ (Supabase) నుండి మిత్ర జ్ఞాపకశక్తిని లోడ్ చేస్తుంది"""
    try:
        res = supabase.table("mitra_settings").select("*").eq("id", "current").execute()
        if res.data:
            return res.data[0]["intelligence"]
    except Exception:
        pass
    return "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి ఒక స్నేహితుడిలా సహాయం చేయాలి."

def sync_chat_to_cloud(c_id, c_msgs, c_title):
    """సంభాషణలను క్లౌడ్ లో భద్రపరుస్తుంది"""
    data = {"id": c_id, "title": c_title, "messages": c_msgs, "updated_at": "now()"}
    supabase.table("mitra_chats").upsert(data).execute()

def delete_chat_record(c_id):
    """చాట్ హిస్టరీని శాశ్వతంగా తొలగిస్తుంది"""
    try:
        supabase.table("mitra_chats").delete().eq("id", c_id).execute()
        st.success("చాట్ తొలగించబడింది!")
        time.sleep(0.5)
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# --- 5. సైడ్‌బార్ మేనేజర్ (Sidebar & History) ---
with st.sidebar:
    st.title("⚙️ మిత్ర కంట్రోల్ ప్యానెల్")
    st.divider()
    
    st.subheader("🧠 మిత్ర జ్ఞాపకశక్తి")
    current_intel = load_mitra_memory()
    new_intel = st.text_area("ఏఐ వ్యక్తిత్వాన్ని మార్చండి:", value=current_intel, height=220)
    
    if st.button("💾 మెమరీ సేవ్ చేయి", use_container_width=True):
        supabase.table("mitra_settings").upsert({"id": "current", "intelligence": new_intel}).execute()
        st.success("జ్ఞాపకశక్తి అప్‌డేట్ అయ్యింది!")
    
    st.divider()
    
    if st.button("➕ కొత్త చాట్ ప్రారంభించు", use_container_width=True):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.session_state.chat_title = "కొత్త చాట్"
        st.rerun()

    st.subheader("☁️ క్లౌడ్ హిస్టరీ")
    try:
        history = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).execute().data
        for chat in history:
            cid, ctitle = chat['id'], chat.get('title', 'Chat')
            c_col1, c_col2, c_col3 = st.columns([0.6, 0.2, 0.2])
            with c_col1:
                if st.button(f"💬 {ctitle[:12]}", key=f"btn_{cid}"):
                    st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title = cid, chat['messages'], ctitle
                    st.rerun()
            with c_col2:
                if st.button("✏️", key=f"ren_{cid}"): st.session_state.rename_id = cid
            with c_col3:
                if st.button("🗑️", key=f"del_{cid}"): delete_chat_record(cid)
            
            if "rename_id" in st.session_state and st.session_state.rename_id == cid:
                new_name = st.text_input("కొత్త పేరు ఇవ్వండి:", value=ctitle, key=f"in_{cid}")
                if st.button("Update", key=f"sav_{cid}"):
                    sync_chat_to_cloud(cid, chat['messages'], new_name)
                    del st.session_state.rename_id
                    st.rerun()
    except: pass

# --- 6. మెయిన్ చాట్ స్క్రీన్ (Main Interface) ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages, st.session_state.chat_title = [], "కొత్త సంభాషణ"

st.header(f"🚀 {st.session_state.chat_title}")

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            col_a1, col_a2 = st.columns([0.85, 0.15])
            with col_a2:
                st.download_button("📥 సేవ్", msg["content"], file_name=f"Mitra_{i}.txt", key=f"dl_{i}")
            try:
                clean_text = get_clean_audio_text(msg["content"])
                tts_file = gTTS(text=clean_text, lang='te')
                fp = io.BytesIO()
                tts_file.write_to_fp(fp)
                st.audio(fp, format="audio/mp3", key=f"aud_{i}_{st.session_state.chat_id}")
            except Exception:
                pass

# --- 7. ఇన్‌పుట్ మేనేజ్‌మెంట్ (Voice & Generation) ---
st.divider()
v_input = mic_recorder(start_prompt="🎙️ వాయిస్ టైపింగ్", stop_prompt="🛑 ఆపండి", key='mic')
t_input = st.chat_input("మిత్రను ఏదైనా అడగండి...")

prompt = None
if t_input: prompt = t_input
elif v_input:
    with st.spinner("వింటున్నాను..."):
        try:
            audio_bio = io.BytesIO(v_input['bytes'])
            audio_bio.name = "audio.wav"
            trans = client.audio.transcriptions.create(file=audio_bio, model="whisper-large-v3", language="te")
            prompt = trans.text
        except Exception as e: st.error(f"Voice Error: {e}")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("ఆలోచిస్తున్నాను..."):
            res = client.chat.completions.create(
                model="llama3-8b-8192", 
                messages=[{"role": "system", "content": current_intel}] + st.session_state.messages
            )
            ans = res.choices[0].message.content
            st.markdown(ans)
            
            try:
                ans_clean = get_clean_audio_text(ans)
                tts_ans = gTTS(text=ans_clean, lang='te')
                ans_fp = io.BytesIO()
                tts_ans.write_to_fp(ans_fp)
                st.audio(ans_fp, format="audio/mp3")
            except Exception: pass
            
            st.session_state.messages.append({"role": "assistant", "content": ans})
            sync_chat_to_cloud(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
            st.rerun()
