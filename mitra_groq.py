import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import uuid
from streamlit_mic_recorder import mic_recorder

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI - Professional", layout="wide", page_icon="🧘")

# --- 2. ఇనిషియలైజేషన్ ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "ai_memory" not in st.session_state:
    st.session_state.ai_memory = "నీ పేరు మిత్ర. నువ్వు బ్రహ్మకుమారిస్ ఆధ్యాత్మిక మార్గదర్శివి."

def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

client = get_groq_client()

# --- 3. సైడ్ బార్ (చాట్ మేనేజ్మెంట్) ---
with st.sidebar:
    st.title("🕉️ మిత్ర కంట్రోల్స్")
    
    if st.button("➕ కొత్త చాట్", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chat_history[new_id] = {"title": "కొత్త సంభాషణ", "messages": []}
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.divider()
    st.subheader("మీ సంభాషణలు")
    
    for chat_id in list(st.session_state.chat_history.keys()):
        col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
        with col1:
            if st.button(st.session_state.chat_history[chat_id]["title"], key=f"btn_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        
        # 1. పేరు మార్చుకునే ఆప్షన్ (Rename)
        with col2:
            if st.button("✏️", key=f"ren_{chat_id}"):
                st.session_state.rename_id = chat_id
        
        with col3:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.chat_history[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = None
                st.rerun()
        
        # పేరు మార్చుకోవడానికి టెక్స్ట్ బాక్స్
        if "rename_id" in st.session_state and st.session_state.rename_id == chat_id:
            new_title = st.text_input("కొత్త పేరు:", value=st.session_state.chat_history[chat_id]["title"], key=f"input_{chat_id}")
            if st.button("Save", key=f"save_title_{chat_id}"):
                st.session_state.chat_history[chat_id]["title"] = new_title
                del st.session_state.rename_id
                st.rerun()

    st.divider()
    with st.expander("⚙️ ఏఐ మెమరీ సెట్టింగ్స్"):
        st.session_state.ai_memory = st.text_area("జ్ఞాపకాలు:", value=st.session_state.ai_memory)

# --- 4. వాయిస్-టు-టెక్స్ట్ ఫంక్షన్ (Whisper API) ---
def speech_to_text(audio_data):
    try:
        # వాయిస్ డేటాను ఫైల్ లాగా మార్చడం
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"
        
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3", # Groq లో అత్యంత వేగవంతమైన వాయిస్ మోడల్
            language="te" # తెలుగు భాష కోసం
        )
        return transcription.text
    except Exception as e:
        return f"వాయిస్ లోపం: {e}"

# --- 5. ప్రధాన ఇంటర్‌ఫేస్ ---
st.header("🔱 మిత్ర - ఆధ్యాత్మిక జ్ఞాన వేదిక")

if not st.session_state.current_chat_id:
    st.info("చాట్ ప్రారంభించండి.")
    st.stop()

current_chat = st.session_state.chat_history[st.session_state.current_chat_id]

# మెసేజ్ హిస్టరీ చూపడం
for idx, m in enumerate(current_chat["messages"]):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            tts = gTTS(text=m["content"].replace("*",""), lang='te')
            f = io.BytesIO(); tts.write_to_fp(f)
            st.audio(f)

# --- 6. ఇన్‌పుట్ సెక్షన్ (వాయిస్ & టెక్స్ట్) ---
st.divider()
voice_text = ""
col_mic, col_txt = st.columns([0.1, 0.9])

with col_mic:
    # 2. వాయిస్ రికార్డింగ్ ఫీచర్ ఫిక్స్
    audio = mic_recorder(start_prompt="🎤", stop_prompt="🔴", key='recorder')
    if audio:
        with st.spinner("వాయిస్ నుంచి టెక్స్ట్ మారుస్తున్నాను..."):
            voice_text = speech_to_text(audio['bytes'])

# టెక్స్ట్ బాక్స్ (వాయిస్ ద్వారా వచ్చిన టెక్స్ట్ ఇక్కడ కనిపిస్తుంది)
user_input = st.chat_input("మీ సందేహాన్ని అడగండి...", key="main_input")

# ఒకవేళ వాయిస్ టెక్స్ట్ ఉంటే దాన్ని వాడుకుంటాం
final_prompt = user_input if user_input else (voice_text if voice_text else None)

if final_prompt:
    if voice_text: st.info(f"మీరు చెప్పింది: {voice_text}")
    
    current_chat["messages"].append({"role": "user", "content": final_prompt})
    with st.chat_message("user"): st.markdown(final_prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("మిత్ర ఆలోచిస్తున్నాడు..."):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": st.session_state.ai_memory}] + current_chat["messages"]
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            current_chat["messages"].append({"role": "assistant", "content": answer})
            
            tts = gTTS(text=answer.replace("*",""), lang='te')
            f = io.BytesIO(); tts.write_to_fp(f)
            st.audio(f)
    st.rerun()
