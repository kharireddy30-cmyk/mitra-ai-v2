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

# --- 2. రహస్య కీలు మరియు క్లౌడ్ కనెక్షన్లు (Secrets & Cloud) ---
def initialize_connections():
    try:
        # సుపబేస్ కనెక్షన్ సెటప్
        sb_url: str = st.secrets["SUPABASE_URL"]
        sb_key: str = st.secrets["SUPABASE_KEY"]
        supabase_client: Client = create_client(sb_url, sb_key)
        
        # ఏఐ మోడల్ కనెక్షన్ (Groq)
        ai_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # సెక్యూరిటీ వివరాలు
        admin_mail = st.secrets["MY_EMAIL"]
        admin_pass = st.secrets["MY_PASSWORD"]
        
        return supabase_client, ai_client, admin_mail, admin_pass
    except Exception as e:
        st.error(f"సెట్టింగ్స్ లోడ్ చేయడంలో విఫలం: {e}")
        return None, None, None, None

supabase, client, SECURE_EMAIL, SECURE_PASSWORD = initialize_connections()

if not supabase:
    st.stop()

# --- 3. వ్యక్తిగత లాగిన్ వ్యవస్థ (Authentication) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>🔐 మిత్ర ఏఐ ప్రైవేట్ యాక్సెస్</h1>", unsafe_allow_html=True)
    st.info("హర్ష గారు, దయచేసి మీ వ్యక్తిగత వివరాలతో లాగిన్ అవ్వండి.")
    
    with st.container():
        l_col1, l_col2 = st.columns(2)
        with l_col1:
            u_mail = st.text_input("మీ రిజిస్టర్డ్ మెయిల్ ఐడి:")
        with l_col2:
            u_pass = st.text_input("మీ సెక్యూర్ పాస్‌వర్డ్:", type="password")
        
        if st.button("ప్రవేశించు (Login)", use_container_width=True):
            if u_mail == SECURE_EMAIL and str(u_pass) == str(SECURE_PASSWORD):
                st.session_state.authenticated = True
                st.success("ధృవీకరణ పూర్తయింది! మిత్ర సిద్ధంగా ఉన్నాడు.")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error("తప్పుడు వివరాలు! దయచేసి మళ్ళీ ప్రయత్నించండి.")
    st.stop()

# --- 4. కోర్ మేనేజ్‌మెంట్ ఫంక్షన్లు (Logic Functions) ---
def get_clean_audio_text(text_to_speak):
    """వాయిస్ కోసం టెక్స్ట్ లో ఉన్న గుర్తులను క్లీన్ చేస్తుంది"""
    symbols = ['*', '#', '_', '`', ':', '(', ')']
    for s in symbols:
        text_to_speak = text_to_speak.replace(s, ' ')
    return text_to_speak

def load_system_intelligence():
    """క్లౌడ్ నుండి ఏఐ వ్యక్తిత్వాన్ని లోడ్ చేస్తుంది"""
    try:
        res = supabase.table("mitra_settings").select("*").eq("id", "current").execute()
        if res.data:
            return res.data[0]["intelligence"]
    except:
        pass
    return "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి ఒక ఆప్తమిత్రుడిలా సలహాలు ఇవ్వాలి."

def sync_chat_to_cloud(c_id, c_msgs, c_title):
    """సంభాషణలను భద్రపరుస్తుంది"""
    data_map = {"id": c_id, "title": c_title, "messages": c_msgs, "updated_at": "now()"}
    supabase.table("mitra_chats").upsert(data_map).execute()

def remove_chat_record(c_id):
    """చాట్ రికార్డ్ తొలగిస్తుంది"""
    supabase.table("mitra_chats").delete().eq("id", c_id).execute()
    st.rerun()

# --- 5. సైడ్‌బార్ మేనేజర్ (Sidebar Controls) ---
with st.sidebar:
    st.title("🤖 మిత్ర ఏఐ సెట్టింగ్స్")
    st.divider()
    
    # జ్ఞాపకశక్తి విభాగం (Memory)
    st.subheader("🧠 మిత్ర జ్ఞాపకశక్తి")
    system_prompt = load_system_intelligence()
    new_prompt = st.text_area("ఏఐ జ్ఞాపకాలను ఇక్కడ మార్చండి:", value=system_prompt, height=220)
    
    if st.button("💾 మెమరీ అప్‌డేట్ చేయి", use_container_width=True):
        supabase.table("mitra_settings").upsert({"id": "current", "intelligence": new_prompt}).execute()
        st.success("మిత్ర జ్ఞాపకశక్తి అప్‌డేట్ అయ్యింది!")
    
    st.divider()
    
    # కొత్త చాట్ ప్రారంభం
    if st.button("➕ కొత్త సంభాషణ ప్రారంభించు", use_container_width=True):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.session_state.chat_title = "కొత్త చాట్"
        st.rerun()

    # క్లౌడ్ హిస్టరీ (Rename & Delete)
    st.subheader("☁️ క్లౌడ్ సంభాషణలు")
    try:
        chats_history = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).execute().data
        for chat_node in chats_history:
            node_id = chat_node['id']
            node_title = chat_node.get('title', 'Chat')
            
            sc1, sc2, sc3 = st.columns([0.6, 0.2, 0.2])
            with sc1:
                if st.button(f"💬 {node_title[:15]}", key=f"nav_{node_id}"):
                    st.session_state.chat_id = node_id
                    st.session_state.messages = chat_node['messages']
                    st.session_state.chat_title = node_title
                    st.rerun()
            with sc2:
                if st.button("✏️", key=f"edit_btn_{node_id}"):
                    st.session_state.renaming_node = node_id
            with sc3:
                if st.button("🗑️", key=f"del_btn_{node_id}"):
                    remove_chat_record(node_id)
            
            # రీనేమ్ చేయడానికి ఆప్షన్
            if "renaming_node" in st.session_state and st.session_state.renaming_node == node_id:
                up_title = st.text_input("కొత్త పేరు ఇవ్వండి:", value=node_title, key=f"ren_in_{node_id}")
                if st.button("Save Name", key=f"ren_save_{node_id}"):
                    sync_chat_to_cloud(node_id, chat_node['messages'], up_title)
                    del st.session_state.renaming_node
                    st.rerun()
    except Exception as e:
        st.info("చాట్ హిస్టరీ ఖాళీగా ఉంది.")

# --- 6. ప్రధాన సంభాషణ విభాగం (Main Chat) ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages, st.session_state.chat_title = [], "కొత్త సంభాషణ"

st.header(f"🚀 {st.session_state.chat_title}")

# మెసేజ్ హిస్టరీ మరియు ఆప్షన్స్
for pos, msg_obj in enumerate(st.session_state.messages):
    with st.chat_message(msg_obj["role"]):
        st.markdown(msg_obj["content"])
        if msg_obj["role"] == "assistant":
            # డౌన్‌లోడ్ బటన్
            d_col1, d_col2 = st.columns([0.8, 0.2])
            with d_col2:
                st.download_button("📥 Save", msg_obj["content"], file_name=f"Mitra_Record_{pos}.txt", key=f"dl_btn_{pos}")
            
            # వాయిస్ ఆడియో ప్లేయర్
            try:
                raw_txt = get_clean_audio_text(msg_obj["content"])
                tts_output = gTTS(text=raw_txt, lang='te')
                aud_buf = io.BytesIO()
                tts_output.write_to_fp(aud_buf)
                st.audio(aud_buf)
            except:
                pass

# --- 7. ఇన్‌పుట్ సెక్షన్ (Voice Typing & Groq AI) ---
st.divider()
voice_input = mic_recorder(start_prompt="🎙️ మాట్లాడండి (వాయిస్ టైపింగ్)", stop_prompt="🛑 ఆపండి", key='mic_input')
text_input = st.chat_input("మిత్రను ఏదైనా అడగండి...")

final_prompt = text_input

# వాయిస్ ప్రాసెసింగ్ (Whisper Large V3)
if voice_input:
    with st.spinner("మిత్ర వింటున్నాడు..."):
        try:
            audio_data = io.BytesIO(voice_input['bytes'])
            audio_data.name = "recording.wav"
            v_res = client.audio.transcriptions.create(file=audio_data, model="whisper-large-v3", language="te")
            final_prompt = v_res.text
        except Exception as v_err:
            st.error(f"వాయిస్ సమస్య: {v_err}")

# ఏఐ జవాబు జనరేషన్
if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user"):
        st.markdown(final_prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("ఆలోచిస్తున్నాను..."):
            chat_res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
            )
            ai_ans = chat_res.choices[0].message.content
            st.markdown(ai_ans)
            
            # వాయిస్ జవాబు ప్లే చేయడం
            try:
                clean_ans = get_clean_audio_text(ai_ans)
                tts_ans = gTTS(text=clean_ans, lang='te')
                ans_buf = io.BytesIO()
                tts_ans.write_to_fp(ans_buf)
                st.audio(ans_buf)
            except:
                pass
            
            # క్లౌడ్ సేవింగ్
            st.session_state.messages.append({"role": "assistant", "content": ai_ans})
            sync_chat_to_cloud(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
            st.rerun()
