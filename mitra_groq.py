import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
from datetime import datetime
from streamlit_mic_recorder import mic_recorder
from supabase import create_client

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI - Om Shanti", layout="wide", page_icon="🧘")

# --- 2. కనెక్షన్లు & ఏపీఐ కీ రొటేషన్ ---
def initialize_all():
    try:
        supabase_client = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
        gemini_keys = st.secrets["GEMINI_KEYS"]
        return supabase_client, gemini_keys
    except Exception as e:
        st.error(f"Settings Error: {e}")
        return None, None

supabase, all_keys = initialize_all()
if not supabase: st.stop()

# --- 3. బహుభాషా & వెబ్ సెర్చ్ లాజిక్ ---
def ask_mitra_spiritual(prompt):
    for key in all_keys:
        try:
            genai.configure(api_key=key)
            # గూగుల్ సెర్చ్ టూల్‌ను యాక్టివేట్ చేయడం (బ్రహ్మకుమారిస్ వెబ్సైట్ల కోసం)
            model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                tools=[{"google_search_retrieval": {}}]
            )
            
            system_instruction = """
            నీ పేరు మిత్ర. నువ్వు బ్రహ్మకుమారిస్ (ఓం శాంతి) ఆధ్యాత్మిక మార్గదర్శివి. 
            ముఖ్య గమనికలు:
            1. తెలుగు, హిందీ, ఇంగ్లీష్ భాషల్లో యూజర్ ఏ భాషలో అడిగితే ఆ భాషలో స్పష్టంగా సమాధానం ఇవ్వు.
            2. సమాధానం కోసం అవసరమైతే బ్రహ్మకుమారిస్ అఫీషియల్ వెబ్‌సైట్లు (brahmakumaris.org, madhubanmurli.org) వెతికి నిఖార్సైన మురళి జ్ఞానాన్ని అందించు.
            3. ఆధ్యాత్మికత, యోగం, బ్రహ్మజ్ఞానం మినహా ఇతర అనవసర విషయాల జోలికి వెళ్లకు.
            4. ఎల్లప్పుడూ శాంతంగా, మర్యాదగా 'మిత్రమా' అని సంబోధిస్తూ మాట్లాడు.
            """
            
            response = model.generate_content(f"{system_instruction}\n\nUser Question: {prompt}")
            return response.text
        except Exception:
            continue
    return "క్షమించండి మిత్రమా, ప్రస్తుతం ఏపీఐ కీలు అందుబాటులో లేవు."

# --- 4. హెల్పర్ ఫంక్షన్లు ---
def get_clean_text(text):
    for char in ['*', '#', '_', '`', ':', '(', ')', '[', ']', '-']: text = text.replace(char, ' ')
    return text.strip()

# --- 5. సైడ్‌బార్ ---
with st.sidebar:
    st.title("🕉️ మిత్ర కంట్రోల్స్")
    st.info("భాష: తెలుగు | హిందీ | English")
    if st.button("➕ కొత్త చాట్", use_container_width=True):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []
        st.rerun()

# --- 6. మెయిన్ స్క్రీన్ ---
if "messages" not in st.session_state:
    st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages = []

st.header("🔱 మిత్ర - ఆధ్యాత్మిక జ్ఞాన వేదిక")

# చాట్ చరిత్ర ప్రదర్శన
for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            try:
                clean_m = get_clean_text(m["content"])
                # భాషను బట్టి TTS సెట్ చేయవచ్చు (ప్రస్తుతానికి తెలుగు)
                tts = gTTS(text=clean_m, lang='te')
                f = io.BytesIO(); tts.write_to_fp(f)
                st.audio(f, format="audio/mp3")
            except: pass

# --- 7. ఇన్పుట్ ---
t = st.chat_input("మీ ఆధ్యాత్మిక సందేహాన్ని ఇక్కడ అడగండి...")
v = mic_recorder(start_prompt="🎙️ వాయిస్", stop_prompt="🛑 ఆపండి", key='mic')

prompt = t # ప్రస్తుతానికి టెక్స్ట్ ఇన్పుట్ ప్రధానం

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("మిత్ర జ్ఞానాన్ని వెతుకుతున్నాడు..."):
            ans = ask_mitra_spiritual(prompt)
            if ans:
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                try:
                    supabase.table("mitra_chats").upsert({
                        "id": st.session_state.chat_id, 
                        "title": "Spiritual Insight", 
                        "messages": st.session_state.messages, 
                        "updated_at": "now()"
                    }).execute()
                except: pass
