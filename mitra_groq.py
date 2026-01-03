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

# --- 1. వెబ్‌సైట్ ప్రాథమిక సెట్టింగ్స్ (Page Configuration) ---
# ఇక్కడ యాప్ పేరు, లోగో మరియు లేఅవుట్ సెట్ చేస్తున్నాం
st.set_page_config(
    page_title="Mitra AI Pro - Harsha's Personal Assistant",
    layout="wide",
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

# --- 2. రహస్య కీలు మరియు క్లౌడ్ కనెక్షన్లు (Cloud Connection Setup) ---
def initialize_connections():
    """అన్ని ఏపీఐ కనెక్షన్లను మరియు సెక్యూరిటీ వివరాలను లోడ్ చేస్తుంది"""
    try:
        # సుపబేస్ కనెక్షన్ వివరాలు (డేటాబేస్)
        sb_url: str = st.secrets["SUPABASE_URL"]
        sb_key: str = st.secrets["SUPABASE_KEY"]
        supabase_client: Client = create_client(sb_url, sb_key)
        
        # ఏఐ మోడల్ కనెక్షన్ (Groq Cloud API)
        ai_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        # హర్ష గారి వ్యక్తిగత లాగిన్ వివరాలు (Secrets నుండి)
        admin_mail = st.secrets["MY_EMAIL"]
        admin_pass = st.secrets["MY_PASSWORD"]
        
        return supabase_client, ai_client, admin_mail, admin_pass
    except Exception as e:
        st.error(f"సెట్టింగ్స్ లోడ్ చేయడంలో విఫలం: {e}")
        return None, None, None, None

# కనెక్షన్లను గ్లోబల్ వేరియబుల్స్ గా మార్చడం
supabase, client, SECURE_EMAIL, SECURE_PASSWORD = initialize_connections()

# కనెక్షన్ లేకపోతే యాప్ ని నిలిపివేయడం
if not supabase or not client:
    st.error("కనెక్షన్ ఎర్రర్! దయచేసి Secrets సరిచూసుకోండి.")
    st.stop()

# --- 3. వ్యక్తిగత లాగిన్ వ్యవస్థ (Authentication System) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>🔐 మిత్ర ఏఐ ప్రైవేట్ యాక్సెస్</h1>", unsafe_allow_html=True)
    st.info("హర్ష గారు, ఇది మీ వ్యక్తిగత ఏఐ. దయచేసి మీ వివరాలతో లాగిన్ అవ్వండి.")
    
    with st.container():
        # లాగిన్ ఫామ్ డిజైన్
        login_col1, login_col2 = st.columns(2)
        with login_col1:
            u_mail = st.text_input("మీ రిజిస్టర్డ్ మెయిల్ ఐడి (Email):")
        with login_col2:
            u_pass = st.text_input("మీ సెక్యూర్ పాస్‌వర్డ్ (Password):", type="password")
        
        # లాగిన్ బటన్ లాజిక్
        if st.button("ప్రవేశించు (Login Now)", use_container_width=True):
            if u_mail == SECURE_EMAIL and str(u_pass) == str(SECURE_PASSWORD):
                st.session_state.authenticated = True
                st.success("ధృవీకరణ పూర్తయింది! మిత్ర ఇప్పుడు మీ సేవలో ఉన్నాడు.")
                time.sleep(1.2)
                st.rerun()
            else:
                st.error("తప్పుడు వివరాలు! ఇది కేవలం హర్ష గారి కోసం మాత్రమే రూపొందించబడింది.")
    st.stop()

# --- 4. కోర్ లాజిక్ ఫంక్షన్లు (Helper Logic Functions) ---
def get_clean_audio_text(text_to_speak):
    """వాయిస్ జవాబు కోసం టెక్స్ట్ లో ఉన్న అనవసర గుర్తులను తొలగిస్తుంది"""
    # స్పెషల్ క్యారెక్టర్ల జాబితా
    bad_symbols = ['*', '#', '_', '`', ':', '(', ')', '[', ']', '-', '\n', '\r']
    for s in bad_symbols:
        text_to_speak = text_to_speak.replace(s, ' ')
    return text_to_speak.strip()

def load_system_intelligence():
    """క్లౌడ్ (Supabase) నుండి మిత్ర జ్ఞాపకశక్తిని మరియు ఇన్స్ట్రక్షన్స్ లోడ్ చేస్తుంది"""
    try:
        res = supabase.table("mitra_settings").select("*").eq("id", "current").execute()
        if res.data:
            return res.data[0]["intelligence"]
    except Exception as log_err:
        st.sidebar.warning(f"జ్ఞాపకశక్తి లోడ్ కాలేదు: {log_err}")
    return "నువ్వు మిత్ర అనే ఏఐవి. హర్ష గారికి ఒక ఆప్తమిత్రుడిలా సలహాలు ఇవ్వాలి."

def sync_chat_to_cloud(c_id, c_msgs, c_title):
    """మొత్తం చాట్ హిస్టరీని మరియు మెసేజ్ లను క్లౌడ్ లో భద్రపరుస్తుంది"""
    data_map = {
        "id": c_id, 
        "title": c_title, 
        "messages": c_msgs, 
        "updated_at": "now()"
    }
    supabase.table("mitra_chats").upsert(data_map).execute()

def remove_chat_record(c_id):
    """అవసరం లేని పాత చాట్ హిస్టరీని శాశ్వతంగా తొలగిస్తుంది"""
    try:
        supabase.table("mitra_chats").delete().eq("id", c_id).execute()
        st.success("చాట్ తొలగించబడింది!")
        time.sleep(1)
        st.rerun()
    except Exception as d_err:
        st.error(f"తొలగించడంలో లోపం: {d_err}")

# --- 5. సైడ్‌బార్ మేనేజర్ (Sidebar & History Controls) ---
with st.sidebar:
    st.title("⚙️ మిత్ర కంట్రోల్ ప్యానెల్")
    st.divider()
    
    # మిత్ర జ్ఞాపకశక్తి అప్‌డేట్ చేసే విభాగం
    st.subheader("🧠 ఏఐ జ్ఞాపకశక్తి (Memory)")
    system_prompt = load_system_intelligence()
    new_prompt = st.text_area("మిత్ర వ్యక్తిత్వాన్ని ఇక్కడ మార్చండి:", value=system_prompt, height=220)
    
    if st.button("💾 మెమరీ సేవ్ చేయి", use_container_width=True):
        supabase.table("mitra_settings").upsert({"id": "current", "intelligence": new_prompt}).execute()
        st.success("మిత్ర జ్ఞాపకశక్తి అప్‌డేట్ అయ్యింది!")
    
    st.divider()
    
    # కొత్త సంభాషణను ప్రారంభించే బటన్
    if st.button("➕ కొత్త చాట్ ప్రారంభించు", use_container_width=True):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.session_state.chat_title = "కొత్త చాట్"
        st.rerun()

    # క్లౌడ్ లో భద్రపరిచిన పాత సంభాషణల జాబితా
    st.subheader("☁️ గత సంభాషణలు")
    try:
        chats_history = supabase.table("mitra_chats").select("*").order("updated_at", desc=True).execute().data
        for chat_node in chats_history:
            node_id = chat_node['id']
            node_title = chat_node.get('title', 'Chat')
            
            # మేనేజ్మెంట్ బటన్లు (View, Rename, Delete)
            sc1, sc2, sc3 = st.columns([0.6, 0.2, 0.2])
            with sc1:
                if st.button(f"💬 {node_title[:12]}", key=f"nav_{node_id}"):
                    st.session_state.chat_id = node_id
                    st.session_state.messages = chat_node['messages']
                    st.session_state.chat_title = node_title
                    st.rerun()
            with sc2:
                if st.button("✏️", key=f"edit_btn_{node_id}", help="పేరు మార్చు"):
                    st.session_state.renaming_node = node_id
            with sc3:
                if st.button("🗑️", key=f"del_btn_{node_id}", help="తొలగించు"):
                    remove_chat_record(node_id)
            
            # రీనేమ్ లాజిక్ ఇన్‌పుట్ బాక్స్
            if "renaming_node" in st.session_state and st.session_state.renaming_node == node_id:
                up_title = st.text_input("కొత్త పేరు ఇవ్వండి:", value=node_title, key=f"ren_in_{node_id}")
                if st.button("Save Name", key=f"ren_save_{node_id}"):
                    sync_chat_to_cloud(node_id, chat_node['messages'], up_title)
                    del st.session_state.renaming_node
                    st.rerun()
    except Exception as history_err:
        st.info("హిస్టరీ లోడ్ చేయడంలో సమస్య ఉంది.")

# --- 6. ప్రధాన చాట్ ఇంటర్‌ఫేస్ (Main Screen) ---
if "chat_id" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages, st.session_state.chat_title = [], "కొత్త సంభాషణ"

st.header(f"🚀 {st.session_state.chat_title}")

# మెసేజ్ హిస్టరీని లూప్ ద్వారా ప్రదర్శించడం
for pos, msg_obj in enumerate(st.session_state.messages):
    with st.chat_message(msg_obj["role"]):
        st.markdown(msg_obj["content"])
        if msg_obj["role"] == "assistant":
            # డౌన్‌లోడ్ మరియు ఆడియో ప్లేయర్ ఆప్షన్లు
            d_col1, d_col2 = st.columns([0.85, 0.15])
            with d_col2:
                st.download_button("📥 సేవ్", msg_obj["content"], file_name=f"Mitra_{pos}.txt", key=f"dl_{pos}")
            
            # ఆడియో లాజిక్
            try:
                clean_txt = get_clean_audio_text(msg_obj["content"])
                tts_output = gTTS(text=clean_txt, lang='te')
                aud_buf = io.BytesIO()
                tts_output.write_to_fp(aud_buf)
                st.audio(aud_buf, format="audio/mp3", key=f"audio_play_{pos}")
            except Exception as tts_err:
                st.write("ఆడియో లోడ్ చేయలేకపోయాను.")

# --- 7. యూజర్ ఇన్‌పుట్ మరియు ఏఐ రెస్పాన్స్ (Input Handling) ---
st.divider()
# వాయిస్ రికార్డర్ బటన్
voice_data = mic_recorder(start_prompt="🎙️ మాట్లాడండి (వాయిస్ టైపింగ్)", stop_prompt="🛑 ఆపండి", key='mic_input')
text_data = st.chat_input("మిత్రను ఏదైనా అడగండి...")

user_prompt = None
# టెక్స్ట్ లేదా వాయిస్ - ఏదో ఒకటి ఎంచుకోవడం
if text_data:
    user_prompt = text_data
elif voice_data:
    with st.spinner("మిత్ర వింటున్నాడు..."):
        try:
            audio_bytes = io.BytesIO(voice_data['bytes'])
            audio_bytes.name = "recording.wav"
            trans_res = client.audio.transcriptions.create(file=audio_bytes, model="whisper-large-v3", language="te")
            user_prompt = trans_res.text
        except Exception as v_err:
            st.error(f"వాయిస్ రికగ్నిషన్ సమస్య: {v_err}")

# ఏఐ జవాబు జనరేషన్ (Groq API ద్వారా)
if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("ఆలోచిస్తున్నాను..."):
            # ఇక్కడ మోడల్ పేరు అప్‌డేట్ చేయబడింది (Rate Limit నివారణకు)
            api_res = client.chat.completions.create(
                model="llama-3-8b-8192", 
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages
            )
            bot_ans = api_res.choices[0].message.content
            st.markdown(bot_ans)
            
            # ఆటోమేటిక్ వాయిస్ ప్లేయర్
            try:
                clean_ans = get_clean_audio_text(bot_ans)
                final_tts = gTTS(text=clean_ans, lang='te')
                final_aud = io.BytesIO()
                final_tts.write_to_fp(final_aud)
                st.audio(final_aud, format="audio/mp3")
            except:
                pass
            
            # చాట్ సేవ్ చేయడం మరియు పేజీని రీఫ్రెష్ చేయడం
            st.session_state.messages.append({"role": "assistant", "content": bot_ans})
            sync_chat_to_cloud(st.session_state.chat_id, st.session_state.messages, st.session_state.chat_title)
            st.rerun()
