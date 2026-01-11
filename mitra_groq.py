import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import uuid

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Mitra AI - Personal Guide", layout="wide", page_icon="🧘")

# --- 2. ఇనిషియలైజేషన్ ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  # {chat_id: {"title": str, "messages": list}}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "ai_memory" not in st.session_state:
    st.session_state.ai_memory = "నీ పేరు మిత్ర. నువ్వు ఒక ఆధ్యాత్మిక మార్గదర్శివి."

# API కీ తనిఖీ
def get_groq_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("దయచేసి Streamlit Secrets లో GROQ_API_KEY ని సెట్ చేయండి.")
        return None

client = get_groq_client()

# --- 3. సైడ్ బార్ (చాట్ హిస్టరీ & మేనేజ్మెంట్) ---
with st.sidebar:
    st.title("🕉️ మిత్ర కంట్రోల్స్")
    
    # కొత్త చాట్ బటన్
    if st.button("➕ కొత్త చాట్", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chat_history[new_id] = {"title": f"Chat {len(st.session_state.chat_history)+1}", "messages": []}
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.divider()
    st.subheader("మీ సంభాషణలు")
    
    # చాట్ లిస్ట్ మరియు డిలీట్ ఆప్షన్
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
    # సెట్టింగ్స్ బాక్స్ (AI జ్ఞాపకాల కోసం)
    with st.expander("⚙️ ఏఐ మెమరీ సెట్టింగ్స్"):
        st.info("ఇక్కడ మీరు ఇచ్చే సమాచారాన్ని బట్టి ఏఐ ప్రవర్తిస్తుంది.")
        new_memory = st.text_area("ఏఐకి గుర్తుండవలసిన విషయాలు:", value=st.session_state.ai_memory, height=150)
        if st.button("జ్ఞాపకాలను సేవ్ చేయి"):
            st.session_state.ai_memory = new_memory
            st.success("ఏఐ జ్ఞాపకాలు అప్‌డేట్ అయ్యాయి!")

# --- 4. ప్రధాన స్క్రీన్ ---
st.header("🔱 మిత్ర - ఆధ్యాత్మిక జ్ఞాన వేదిక")

if not st.session_state.current_chat_id:
    st.info("ఎడమవైపు ఉన్న 'కొత్త చాట్' బటన్ నొక్కి సంభాషణను ప్రారంభించండి.")
    st.stop()

current_chat = st.session_state.chat_history[st.session_state.current_chat_id]

# మెసేజ్‌లను ప్రదర్శించడం
for idx, m in enumerate(current_chat["messages"]):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        
        # ప్రతి మెసేజ్ కింద డిలీట్ మరియు సేవ్ ఆప్షన్లు
        col1, col2, col3 = st.columns([0.1, 0.1, 0.8])
        with col1:
            if st.button("🗑️", key=f"msg_del_{idx}"):
                current_chat["messages"].pop(idx)
                st.rerun()
        with col2:
            # టెక్స్ట్ ని కాపీ చేసుకోవడానికి వీలుగా చూపిస్తుంది
            st.download_button("💾", m["content"], file_name=f"mitra_msg_{idx}.txt", key=f"msg_save_{idx}")

# --- 5. చాట్ ఫంక్షన్ ---
def ask_mitra(prompt, history):
    system_prompt = f"{st.session_state.ai_memory}\n\nదయచేసి తెలుగులో సమాధానం ఇవ్వు."
    messages = [{"role": "system", "content": system_prompt}]
    
    # గత సంభాషణను ఏఐకి అందించడం (Context)
    for h in history[-5:]: # చివరి 5 మెసేజ్‌లు
        messages.append(h)
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

# --- 6. యూజర్ ఇన్‌పుట్ ---
user_input = st.chat_input("మీ సందేహాన్ని ఇక్కడ అడగండి...")

if user_input:
    # యూజర్ మెసేజ్ ని చేర్చడం
    current_chat["messages"].append({"role": "user", "content": user_input})
    
    # చాట్ టైటిల్ ని మొదటి ప్రశ్నతో అప్‌డేట్ చేయడం
    if len(current_chat["messages"]) == 1:
        current_chat["title"] = user_input[:20] + "..."

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("మిత్ర ఆలోచిస్తున్నాడు..."):
            answer = ask_mitra(user_input, current_chat["messages"][:-1])
            st.markdown(answer)
            current_chat["messages"].append({"role": "assistant", "content": answer})
            
            # ఆడియో ప్లేయర్
            try:
                clean_text = answer.replace("*", "").replace("#", "")
                tts = gTTS(text=clean_text[:250], lang='te')
                f = io.BytesIO()
                tts.write_to_fp(f)
                st.audio(f, format="audio/mp3")
            except:
                pass
    st.rerun()
