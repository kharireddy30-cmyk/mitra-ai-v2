import streamlit as st
from openai import OpenAI  # OpenAI లైబ్రరీ
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
        # OpenAI API Key ని ఇక్కడ తీసుకుంటున్నాం
        api_key = st.secrets["OPENAI_API_KEY"]
        return supabase_client, api_key
    except Exception as e:
        st.error(f"సెట్టింగ్స్ లో లోపం ఉంది: {e}")
        return None, None

supabase, openai_api_key = initialize_all()
if not openai_api_key: 
    st.warning("దయచేసి OpenAI API Key ని సెటప్ చేయండి.")
    st.stop()

# --- 3. OpenAI క్లయింట్ కాన్ఫిగరేషన్ ---
client = OpenAI(api_key=openai_api_key)

# --- 4. సహాయక ఫంక్షన్లు ---
def get_clean_text(text):
    for char in ['*', '#', '_', '`', ':', '(', ')', '[', ']', '-']: 
        text = text.replace(char, ' ')
    return text.strip()

def ask_mitra(user_prompt):
    system_instruction = """
    నీ పేరు మిత్ర. నువ్వు బ్రహ్మకుమారిస్ (ఓం శాంతి) ఆధ్యాత్మిక మార్గదర్శివి. 
    1. తెలుగు, హిందీ, ఇంగ్లీష్ భాషల్లో సమాధానం ఇవ్వు. 
    2. ఆధ్యాత్మికత, మురళి జ్ఞానం, యోగం గురించి మాత్రమే వివరించు.
    """
    try:
        # GPT-4o లేదా gpt-3.5-turbo ఉపయోగించవచ్చు
        response = client.chat.completions.create(
            model="gpt-4o", # లేదా "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"క్షమించండి మిత్రమా, లోపం: {e}"

# --- 5. సైడ్‌బార్ ---
with st.sidebar:
    st.title("🕉️ మిత్ర కంట్రోల్స్")
    if st.button("➕ కొత్త చాట్", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 6. మెయిన్ ఇంటర్‌ఫేస్ ---
if "messages" not in st.session_state:
    st.session_state.messages = []

st.header("🔱 మిత్ర - ఆధ్యాత్మిక జ్ఞాన వేదిక (GPT Powered)")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 7. యూజర్ ఇన్‌పుట్ ---
prompt = st.chat_input("మీ ఆధ్యాత్మిక సందేహాన్ని అడగండి...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("మిత్ర ఆలోచిస్తున్నాడు..."):
            answer = ask_mitra(prompt)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # ఆడియో
            try:
                clean_ans = get_clean_text(answer)
                tts = gTTS(text=clean_ans[:250], lang='te')
                f = io.BytesIO()
                tts.write_to_fp(f)
                st.audio(f, format="audio/mp3")
            except:
                pass
