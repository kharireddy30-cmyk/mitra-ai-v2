import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from supabase import create_client

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI - Spiritual", layout="wide", page_icon="🧘")

# --- 2. కనెక్షన్లు ---
def initialize_all():
    try:
        supabase_client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        # మీ Secrets లో ఉన్న GEMINI_KEYS ని తీసుకుంటుంది
        gemini_keys = st.secrets.get("GEMINI_KEYS", [])
        return supabase_client, gemini_keys
    except Exception as e:
        st.error(f"Settings Error: {e}")
        return None, None

supabase, all_keys = initialize_all()

# --- 3. ఆధ్యాత్మిక ఏఐ లాజిక్ ---
def ask_mitra(prompt):
    if not all_keys:
        return "క్షమించండి, సీక్రెట్స్ లో ఏపీఐ కీలు సరిగ్గా అమర్చబడలేదు."
    
    for key in all_keys:
        try:
            genai.configure(api_key=key)
            # బహుభాషా సామర్థ్యం మరియు సెర్చ్ టూల్
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                tools=[{"google_search_retrieval": {}}]
            )
            
            instruction = """
            నీ పేరు మిత్ర. నువ్వు బ్రహ్మకుమారిస్ (ఓం శాంతి) ఆధ్యాత్మిక మార్గదర్శివి. 
            యూజర్ అడిగే ప్రశ్నలకు తెలుగు, హిందీ లేదా ఇంగ్లీష్ లో సమాధానం ఇవ్వు. 
            ముఖ్యంగా బ్రహ్మకుమారిస్ అఫీషియల్ సైట్ల నుండి మురళి జ్ఞానాన్ని సేకరించి వివరించు.
            """
            
            response = model.generate_content(f"{instruction}\n\nUser: {prompt}")
            return response.text
        except Exception:
            continue # ఒక కీ పని చేయకపోతే ఇంకో దానికి వెళ్తుంది
            
    return "ప్రస్తుతానికి అన్ని ఏపీఐ కీలు బిజీగా ఉన్నాయి. దయచేసి కాసేపటి తర్వాత ప్రయత్నించండి."

# --- 4. మెయిన్ యూజర్ ఇంటర్‌ఫేస్ ---
st.header("🔱 మిత్ర - ఆధ్యాత్మిక జ్ఞాన వేదిక")

if "messages" not in st.session_state:
    st.session_state.messages = []

# చాట్ ప్రదర్శన
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ఇన్పుట్ బాక్స్
prompt = st.chat_input("మీ ఆధ్యాత్మిక సందేహాన్ని అడగండి...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("మిత్ర జ్ఞానాన్ని వెతుకుతున్నాడు..."):
            ans = ask_mitra(prompt)
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # ఆడియో వినిపించడం
            try:
                tts = gTTS(text=ans[:200], lang='te') # మొదటి 200 అక్షరాలు
                f = io.BytesIO(); tts.write_to_fp(f)
                st.audio(f, format="audio/mp3")
            except: pass
