import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import uuid

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI - Updated", layout="wide", page_icon="🧘")

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
        st.error("API Key లోపం ఉంది.")
        return None

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
        
        # చాట్ రీనేమ్ ఆప్షన్ (✏️)
        with col2:
            if st.button("✏️", key=f"ren_{chat_id}"):
                st.session_state.rename_id = chat_id
        
        with col3:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.chat_history[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = None
                st.rerun()
        
        # పేరు మార్చుకోవడానికి ఇన్‌పుట్ బాక్స్
        if "rename_id" in st.session_state and st.session_state.rename_id == chat_id:
            new_title = st.text_input("కొత్త పేరు రాయండి:", value=st.session_state.chat_history[chat_id]["title"], key=f"input_{chat_id}")
            if st.button("Save Name", key=f"save_title_{chat_id}"):
                st.session_state.chat_history[chat_id]["title"] = new_title
                del st.session_state.rename_id
                st.rerun()

    st.divider()
    with st.expander("⚙️ ఏఐ మెమరీ సెట్టింగ్స్"):
        st.session_state.ai_memory = st.text_area("జ్ఞాపకాలు:", value=st.session_state.ai_memory, height=150)

# --- 4. ప్రధాన స్క్రీన్ ---
st.header("🔱 మిత్ర - ఆధ్యాత్మిక జ్ఞాన వేదిక")

if not st.session_state.current_chat_id:
    st.info("చాట్ ప్రారంభించడానికి 'కొత్త చాట్' బటన్ నొక్కండి.")
    st.stop()

current_chat = st.session_state.chat_history[st.session_state.current_chat_id]

# మెసేజ్ హిస్టరీ మరియు ఆడియో అవుట్‌పుట్
for idx, m in enumerate(current_chat["messages"]):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        
        # కేవలం ఏఐ సమాధానాలకు మాత్రమే ఆడియో వినిపిస్తుంది
        if m["role"] == "assistant":
            try:
                clean_text = m["content"].replace("*", "").replace("#", "")
                tts = gTTS(text=clean_text, lang='te')
                f = io.BytesIO()
                tts.write_to_fp(f)
                st.audio(f, format="audio/mp3")
            except:
                pass

# --- 5. యూజర్ ఇన్‌పుట్ ---
st.divider()
user_input = st.chat_input("మీ ఆధ్యాత్మిక సందేహాన్ని ఇక్కడ అడగండి...")

if user_input:
    # యూజర్ మెసేజ్ ని హిస్టరీలో చేర్చడం
    current_chat["messages"].append({"role": "user", "content": user_input})
    
    # మొదటిసారి మెసేజ్ పంపినప్పుడు ఆటోమేటిక్ టైటిల్
    if len(current_chat["messages"]) <= 2:
        current_chat["title"] = user_input[:20] + "..."

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("మిత్ర ఆలోచిస్తున్నాడు..."):
            try:
                # ఏఐ కి మెమరీ మరియు గత హిస్టరీని పంపడం
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": st.session_state.ai_memory}] + current_chat["messages"]
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                current_chat["messages"].append({"role": "assistant", "content": answer})
                
                # సమాధానాన్ని ఆడియోగా మార్చడం
                clean_ans = answer.replace("*", "").replace("#", "")
                tts = gTTS(text=clean_ans, lang='te')
                f = io.BytesIO()
                tts.write_to_fp(f)
                st.audio(f, format="audio/mp3")
            except Exception as e:
                st.error(f"క్షమించండి, లోపం వచ్చింది: {e}")
    
    st.rerun()
