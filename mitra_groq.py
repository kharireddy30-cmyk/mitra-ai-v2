import streamlit as st
from groq import Groq  # Groq లైబ్రరీ
from gtts import gTTS
import io
from supabase import create_client

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI - Groq Powered", layout="wide", page_icon="🧘")

# --- 2. కనెక్షన్లు ---
def initialize_all():
    try:
        supabase_client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        # మీ Streamlit Secrets లో GROQ_API_KEY ఉండాలి
        api_key = st.secrets["GROQ_API_KEY"]
        return supabase_client, api_key
    except Exception as e:
        st.error(f"సెట్టింగ్స్ లో లోపం ఉంది: {e}")
        return None, None

supabase, groq_api_key = initialize_all()
if not groq_api_key: 
    st.warning("దయచేసి Groq API Key ని సెటప్ చేయండి.")
    st.stop()

# --- 3. Groq క్లయింట్ కాన్ఫిగరేషన్ ---
client = Groq(api_key=groq_api_key)

# --- 4. సహాయక ఫంక్షన్లు ---
def get_clean_text(text):
    for char in ['*', '#', '_', '`', ':', '(', ')', '[', ']', '-']: 
        text = text.replace(char, ' ')
    return text.strip()

def ask_mitra(user_prompt):
    system_instruction = """
    నీ పేరు మిత్ర. నువ్వు బ్రహ్మకుమారిస్ (ఓం శాంతి) ఆధ్యాత్మిక మార్గదర్శివి. 
    1. తెలుగులో మాత్రమే స్పష్టంగా సమాధానం ఇవ్వు. 
    2. ఆధ్యాత్మికత, మురళి జ్ఞానం, ధ్యానం గురించి వివరించు.
    """
    try:
        # Groq లో 'llama-3.3-70b-versatile' చాలా వేగంగా మరియు కచ్చితంగా పనిచేస్తుంది
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"క్షమించండి మిత్రమా, లోపం: {e}"

# --- 5. సైడ్‌బార్ & మెయిన్ ఇంటర్‌ఫేస్ ---
with st.sidebar:
    st.title("🕉️ మిత్ర కంట్రోల్స్")
    if st.button("➕ కొత్త చాట్"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.header("🔱 మిత్ర - ఆధ్యాత్మిక జ్ఞాన వేదిక (Groq Speed)")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 6. యూజర్ ఇన్‌పుట్ ---
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
