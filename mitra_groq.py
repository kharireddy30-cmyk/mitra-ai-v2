import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from supabase import create_client

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI - Om Shanti", layout="wide", page_icon="🧘")

# --- 2. కనెక్షన్లు ---
def initialize_all():
    try:
        supabase_client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        api_key = st.secrets["GEMINI_KEY"]
        return supabase_client, api_key
    except Exception as e:
        st.error(f"సెట్టింగ్స్ లో లోపం ఉంది: {e}")
        return None, None

supabase, google_api_key = initialize_all()
if not google_api_key: st.stop()

# --- 3. ఆధ్యాత్మిక ఏఐ కాన్ఫిగరేషన్ ---
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    tools=[{"google_search_retrieval": {}}] # మురళి జ్ఞానం వెతకడానికి సెర్చ్ టూల్
)

# --- 4. సహాయక ఫంక్షన్లు ---
def get_clean_text(text):
    for char in ['*', '#', '_', '`', ':', '(', ')', '[', ']', '-']: text = text.replace(char, ' ')
    return text.strip()

def ask_mitra(user_prompt):
    system_instruction = """
    నీ పేరు మిత్ర. నువ్వు బ్రహ్మకుమారిస్ (ఓం శాంతి) ఆధ్యాత్మిక మార్గదర్శివి. 
    1. తెలుగు, హిందీ, ఇంగ్లీష్ భాషల్లో సమాధానం ఇవ్వు. 
    2. బ్రహ్మకుమారిస్ అఫీషియల్ వెబ్‌సైట్ల నుండి ఖచ్చితమైన సమాచారం సేకరించు.
    3. ఆధ్యాత్మికత మినహా ఇతర విషయాల గురించి మాట్లాడకు.
    """
    try:
        response = model.generate_content(f"{system_instruction}\n\nప్రశ్న: {user_prompt}")
        return response.text
    except Exception as e:
        return f"క్షమించండి మిత్రమా, ఒక లోపం సంభవించింది: {e}"

# --- 5. సైడ్‌బార్ ---
with st.sidebar:
    st.title("🕉️ మిత్ర కంట్రోల్స్")
    st.info("భాషలు: తెలుగు | హిందీ | English")
    if st.button("➕ కొత్త చాట్", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 6. మెయిన్ ఇంటర్‌ఫేస్ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.header("🔱 మిత్ర - ఆధ్యాత్మిక జ్ఞాన వేదిక")

# పాత మెసేజ్‌లను చూపించడం
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            try:
                clean_m = get_clean_text(m["content"])
                tts = gTTS(text=clean_m[:250], lang='te')
                f = io.BytesIO(); tts.write_to_fp(f)
                st.audio(f, format="audio/mp3")
            except: pass

# --- 7. యూజర్ ఇన్‌పుట్ ---
prompt = st.chat_input("మీ ఆధ్యాత్మిక సందేహాన్ని అడగండి...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("మిత్ర జ్ఞానాన్ని అన్వేషిస్తున్నాడు..."):
            answer = ask_mitra(prompt)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # ఆటోమేటిక్ వాయిస్
            try:
                tts = gTTS(text=get_clean_text(answer)[:250], lang='te')
                f = io.BytesIO(); tts.write_to_fp(f)
                st.audio(f, format="audio/mp3")
            except: pass
            
            # డేటాబేస్ లో సేవ్ చేయడం
            try:
                chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                supabase.table("mitra_chats").upsert({
                    "id": chat_id, "title": "Om Shanti", "messages": st.session_state.messages
                }).execute()
            except: pass
