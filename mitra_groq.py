import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import os
import time
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

supabase, client, SECURE_EMAIL, SECURE_PASSWORD = initialize_connections()

if not supabase:
    st.stop()

# --- 3. వ్యక్తిగత లాగిన్ వ్యవస్థ (Security & Auth) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>🔐 మిత్ర ఏఐ ప్రైవేట్ యాక్సెస్</h1>", unsafe_allow_html=True)
    st.info("హర్ష గారు, ఇది మీ వ్యక్తిగత ఏఐ. దయచేసి లాగిన్ అవ్వండి.")
    
    with st.container():
        l_col1, l_col2 = st.columns(2)
        with l_col1:
            u_mail = st.text_input("మీ ఇమెయిల్ ఐడి (Email):")
        with l_col2:
            u_pass = st.text_input("మీ పాస్‌వర్డ్ (Password):", type="password")
        
        if st.button("ప్రవేశించు (Login Now)", use_container_width=True):
            if u_mail == SECURE_EMAIL and str(u_pass) == str(SECURE_PASSWORD):
                st.session_state.authenticated = True
                st.success("స్వాగతం హర్ష గారు! మిత్ర ఇప్పుడు మీ సేవలో ఉన్నాడు.")
                time.sleep(1.2)
                st.rerun()
            else:
                st.error("క్షమించండి, వివరాలు తప్పు! ఇది కేవలం హర్ష గారికి మాత్రమే.")
    st.stop()

# --- 4. కోర్ మేనేజ్‌మెంట్ ఫంక్షన్లు (Logic) ---
def get_clean_audio_text(text_to_speak):
    """వాయిస్ జవాబు కోసం టెక్స్ట్ లో ఉన్న అనవసర గుర్తులను క్లీన్ చేస్తుంది"""
    bad_symbols = ['*', '#', '_', '`', ':', '(', ')', '[', ']', '-', '\n']
    for s in bad_symbols:
        text_to_speak = text_to_speak.replace(s, ' ')
    return text_to_speak

def load_system_intelligence():
    """క్లౌడ్ (Supabase) నుండి మిత్ర జ్ఞాపకశక్తిని లోడ్ చేస్తుంది"""
    try:
        res = supabase.table("mitra_settings").select("*").eq("id", "current").execute()
        if res.data:
            return res.data[0]["intelligence"]
    except:
        pass
    return "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి ఒక ఆప్తమిత్రుడిలా సలహాలు ఇవ్వాలి."

def sync_chat_to_cloud(c_id, c_msgs, c_title):
    """మొత్తం చాట్ హిస్టరీని క్లౌడ్ లో భద్రపరుస్తుంది"""
    data_map = {"id": c_id, "title": c_title, "messages": c_msgs, "updated_at": "now()"}
    supabase.table("mitra_chats").upsert(data_map).execute()

def remove_chat_record(c_id):
    """అవసరం లేని చాట్ హిస్టరీని శాశ్వతంగా తొలగిస్తుంది"""
    supabase.table("mitra_chats").delete().eq("id", c_id).execute()
    st.rerun()

# --- 5. సైడ్‌బార్ మేనేజర్ (Sidebar Controls) ---
with st.sidebar:
    st.title("⚙️ మిత్ర కంట్రోల్ ప్యానెల్")
    st.divider()
    
    st.subheader("🧠 మిత్ర జ్ఞాపకశక్తి")
    system_prompt = load_system_intelligence()
    new_prompt = st.text_area("మిత్ర వ్యక్తిత్వాన్ని మార్చండి:", value=system_prompt, height=200)
    
    if st.button("💾 మెమరీ సేవ్ చేయి", use_container_width=True):
        supabase.table("mitra_settings").upsert({"id": "current", "intelligence": new_prompt}).execute()
        st.success("మిత్ర జ్ఞాపకశక్తి అప్‌డేట్ అయ్యింది!")
    
    st.divider()
    
    if st.button("➕ కొత్త చాట్ ప్రారంభించు", use_container_width=True):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.session_state.chat_title = "కొత్త చాట్"
        st.rerun()

    st.subheader("☁️ గత సంభాషణలు")
    try:
        chats_history = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).execute().data
        for chat_node in chats_history:
            node_id = chat_node['id']
            node_title = chat_node.get('title', 'Chat')
            
            sc1, sc2, sc3 = st.columns([0.6, 0.2, 0.2])
            with sc1:
                if st.button(f"💬 {node_title[:12]}", key=f"nav_{node_id}"):
                    st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title = node_id, chat_node['messages'], node_title
                    st.rerun()
            with sc2:
                if st.button("✏️", key=f"edit_btn_{node_id}"): st.session_state.renaming_node = node_id
            with sc3:
                if st.button("🗑️", key=f"del_btn_{node_id}"): remove_chat_record(node_id)
            
            if "renaming_node" in st.session_state and st.session_state.renaming_node == node_id:
                up_title = st.text_input("కొత్త పేరు:", value=node_title, key=f"ren_in_{node_id}")
                if st.button("Update", key=f"ren_save_{node_id}"):
                    sync_chat_to_cloud(node_id, chat_node['messages'], up_title)
                    del st.session_state.renaming_node
                    st.rerun()
    except: pass

# --- 6. ప్రధాన సంభాషణ స్క్రీన్ (Main Interface) ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages, st.session_state.chat_title = [], "కొత్త సంభాషణ"

st.header(f"🚀 {st.session_state.chat_title}")

for pos, msg_obj in enumerate(st.session_state.messages):
    with st.chat_message(msg_obj["role"]):
        st.markdown(msg_obj["content"])
        if msg_obj["role"] == "assistant":
            d_col1, d_col2 = st.columns([0.8, 0.2])
            with d_col2:
                st.download_button("📥 సేవ్", msg_obj["content"], file_name=f"Mitra_{pos}.txt", key=f"dl_{pos}")
            try:
                clean_txt = get_clean_audio_text(msg_obj["content"])
                tts = gTTS(text=clean_txt, lang='te')
                aud_buf = io.BytesIO()
                tts.write_to_fp(aud_buf)
                st.audio(aud_buf, format="audio/mp3", key=f"audio_{pos}")
            except: pass

# --- 7. ఇన్‌పుట్ మేనేజ్‌మెంట్ (Voice & AI Generation) ---
st.divider()
voice_input = mic_recorder(start_prompt="🎙️ వాయిస్ టైపింగ్", stop_prompt="🛑 ఆపండి", key='mic_input')
text_input = st.chat_input("మిత్రను ఏదైనా అడగండి...")

final_prompt = None
if text_input:
    final_prompt = text_input
elif voice_input:
    with st.spinner("మిత్ర వింటున్నాడు..."):
        try:
            audio_data = io.BytesIO(voice_input['bytes'])
            audio_data.name = "rec.wav"
            v_res = client.audio.transcriptions.create(file=audio_data, model="whisper-large-v3", language="te")
            final_prompt = v_res.text
        except Exception as v_err: st.error(f"వాయిస్ సమస్య: {v_err}")

if final_prompt:
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user"):
        st.markdown(final_prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("ఆలోచిస్తున్నాను..."):
            chat_res = client.chat.completions.create(
                model="llama-3-8b-8192", 
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
            )
            ai_ans = chat_res.choices[0].message.content
            st.markdown(ai_ans)
            
            try:
                clean_ans = get_clean_audio_text(ai_ans)
                tts_ans = gTTS(text=clean_ans, lang='te')
                ans_buf = io.BytesIO()
                tts_ans.write_to_fp(ans_buf)
                st.audio(ans_buf, format="audio/mp3")
            except: pass
            
            st.session_state.messages.append({"role": "assistant", "content": ai_ans})
            sync_chat_to_cloud(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
            st.rerun()
