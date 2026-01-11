import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import uuid
from streamlit_mic_recorder import mic_recorder # వాయిస్ ఇన్‌పుట్ కోసం

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI - Complete Guide", layout="wide", page_icon="🧘")

# --- 2. ఇనిషియలైజేషన్ ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "ai_memory" not in st.session_state:
    st.session_state.ai_memory = "నీ పేరు మిత్ర. నువ్వు బ్రహ్మకుమారిస్ ఆధ్యాత్మిక మార్గదర్శివి."

def get_groq_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("దయచేసి Streamlit Secrets లో GROQ_API_KEY ని సెట్ చేయండి.")
        return None

client = get_groq_client()

# --- 3. సైడ్ బార్ (చాట్ హిస్టరీ & సెట్టింగ్స్) ---
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
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button(st.session_state.chat_history[chat_id]["title"], key=f"btn_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.chat_history[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = None
                st.rerun()

    st.divider()
    with st.expander("⚙️ ఏఐ మెమరీ సెట్టింగ్స్"):
        new_memory = st.text_area("ఏఐకి గుర్తుండవలసిన విషయాలు:", value=st.session_state.ai_memory, height=150)
        if st.button("జ్ఞాపకాలను సేవ్ చేయి"):
            st.session_state.ai_memory = new_memory
            st.success("సేవ్ చేయబడింది!")

# --- 4. ప్రధాన స్క్రీన్ ---
st.header("🔱 మిత్ర - ఆధ్యాత్మిక జ్ఞాన వేదిక")

if not st.session_state.current_chat_id:
    st.info("ఎడమవైపు 'కొత్త చాట్' క్లిక్ చేసి ప్రారంభించండి.")
    st.stop()

current_chat = st.session_state.chat_history[st.session_state.current_chat_id]

# మెసేజ్ క్లీనింగ్ ఫంక్షన్ (ఆడియో కోసం)
def clean_for_audio(text):
    return text.replace("*", "").replace("#", "").replace("`", "").strip()

# మెసేజ్‌లను ప్రదర్శించడం
for idx, m in enumerate(current_chat["messages"]):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        
        # ఆడియో అవుట్‌పుట్ (సహాయకుడు చెప్పిన సమాధానం కోసం)
        if m["role"] == "assistant":
            try:
                clean_text = clean_for_audio(m["content"])
                tts = gTTS(text=clean_text, lang='te')
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp, format="audio/mp3")
            except: pass

        # కంట్రోల్స్ (డిలీట్ & సేవ్)
        col1, col2, _ = st.columns([0.05, 0.05, 0.9])
        with col1:
            if st.button("🗑️", key=f"msg_del_{idx}"):
                current_chat["messages"].pop(idx)
                st.rerun()
        with col2:
            st.download_button("💾", m["content"], file_name="mitra_msg.txt", key=f"save_{idx}")

# --- 5. వాయిస్ ఇన్‌పుట్ & టెక్స్ట్ ఇన్‌పుట్ ---
st.divider()
col_mic, col_txt = st.columns([0.1, 0.9])

with col_mic:
    # వాయిస్ రికార్డర్
    audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🔴", key='recorder')

with col_txt:
    user_input = st.chat_input("మీ ఆధ్యాత్మిక సందేహాన్ని ఇక్కడ అడగండి...")

# వాయిస్ ఇన్‌పుట్ ప్రాసెసింగ్ (ఒకవేళ వాయిస్ ద్వారా ప్రశ్న వస్తే)
if audio_input:
    # గమనిక: Groq లో 'distil-whisper-large-v3-en' వాడి వాయిస్ టు టెక్స్ట్ చేయవచ్చు
    # ప్రస్తుతానికి యూజర్ టెక్స్ట్ బాక్స్ లేదా వాయిస్ రికార్డింగ్ పై దృష్టి పెట్టాం
    st.warning("వాయిస్ రికార్డింగ్ పూర్తయింది. (వాయిస్-టు-టెక్స్ట్ కోసం విస్పర్‌ని జోడించవచ్చు)")

# --- 6. ఏఐ రెస్పాన్స్ ఫంక్షన్ ---
def ask_mitra(prompt, history):
    system_prompt = f"{st.session_state.ai_memory}\n\nముఖ్యంగా తెలుగులో మాత్రమే సమాధానం ఇవ్వాలి."
    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-5:]: messages.append(h)
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"లోపం: {e}"

# మెసేజ్ ప్రాసెసింగ్
if user_input:
    current_chat["messages"].append({"role": "user", "content": user_input})
    if len(current_chat["messages"]) <= 2:
        current_chat["title"] = user_input[:15] + "..."
    
    with st.chat_message("user"): st.markdown(user_input)
    with st.chat_message("assistant"):
        with st.spinner("మిత్ర ఆలోచిస్తున్నాడు..."):
            answer = ask_mitra(user_input, current_chat["messages"][:-1])
            st.markdown(answer)
            current_chat["messages"].append({"role": "assistant", "content": answer})
            
            # వెంటనే ఆడియో ప్లే చేయడం
            clean_text = clean_for_audio(answer)
            tts = gTTS(text=clean_text, lang='te')
            f = io.BytesIO(); tts.write_to_fp(f)
            st.audio(f)
    st.rerun()
