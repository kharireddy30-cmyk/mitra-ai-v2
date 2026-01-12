import streamlit as st
from groq import Groq
from gtts import gTTS
import io
import uuid

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(page_title="Brahma Kumaris - Spiritual AI", layout="wide", page_icon="🧘")

# --- 2. ఇనిషియలైజేషన్ ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  
if "current_chat_id" not in st.session_state:
    # మొదటిసారి ఓపెన్ చేసినప్పుడు ఆటోమేటిక్ గా ఒక చాట్ ఐడిని క్రియేట్ చేయడం (దీనివల్ల నేరుగా ప్రశ్న అడగవచ్చు)
    initial_id = str(uuid.uuid4())
    st.session_state.chat_history[initial_id] = {"title": "కొత్త సంభాషణ", "messages": []}
    st.session_state.current_chat_id = initial_id

if "ai_memory" not in st.session_state:
    st.session_state.ai_memory = "నీ పేరు మిత్ర. నువ్వు బ్రహ్మకుమారిస్ ఆధ్యాత్మిక మార్గదర్శివి. కేవలం ఆధ్యాత్మికత, మురళి జ్ఞానం, యోగం గురించి మాత్రమే వివరించు."

def get_groq_client():
    try:
        return Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("API Key సెట్టింగ్స్ లో లేదు.")
        return None

client = get_groq_client()

# --- 3. సైడ్ బార్ ---
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
            # ప్రస్తుత చాట్ ను హైలైట్ చేయడం కోసం చిన్న లాజిక్
            btn_label = st.session_state.chat_history[chat_id]["title"]
            if st.button(btn_label, key=f"btn_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()
        
        with col2:
            if st.button("✏️", key=f"ren_{chat_id}"):
                st.session_state.rename_id = chat_id
        
        with col3:
            if st.button("🗑️", key=f"del_{chat_id}"):
                del st.session_state.chat_history[chat_id]
                # ఒకవేళ ఉన్న చాట్ డిలీట్ అయితే కొత్తదాన్ని క్రియేట్ చేయడం
                if not st.session_state.chat_history:
                    new_id = str(uuid.uuid4())
                    st.session_state.chat_history[new_id] = {"title": "కొత్త సంభాషణ", "messages": []}
                    st.session_state.current_chat_id = new_id
                elif st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = list(st.session_state.chat_history.keys())[0]
                st.rerun()
        
        if "rename_id" in st.session_state and st.session_state.rename_id == chat_id:
            new_title = st.text_input("పేరు మార్చండి:", value=st.session_state.chat_history[chat_id]["title"], key=f"input_{chat_id}")
            if st.button("Save", key=f"save_title_{chat_id}"):
                st.session_state.chat_history[chat_id]["title"] = new_title
                del st.session_state.rename_id
                st.rerun()

    st.divider()
    with st.expander("⚙️ ఏఐ మెమరీ సెట్టింగ్స్"):
        st.session_state.ai_memory = st.text_area("జ్ఞాపకాలు:", value=st.session_state.ai_memory, height=150)

# --- 4. ప్రధాన స్క్రీన్ (మార్పు చేసిన హెడర్) ---
st.header("🔱 బ్రహ్మకుమారిస్ ఆధ్యాత్మిక జ్ఞాన వేదిక")

current_chat = st.session_state.chat_history[st.session_state.current_chat_id]

# మెసేజ్ హిస్టరీ
for idx, m in enumerate(current_chat["messages"]):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        
        if m["role"] == "assistant":
            try:
                clean_txt = m["content"].replace("*","").replace("#","")
                tts = gTTS(text=clean_txt, lang='te')
                f = io.BytesIO(); tts.write_to_fp(f)
                st.audio(f)
            except: pass

        c1, c2, _ = st.columns([0.07, 0.07, 0.86])
        with c1:
            if st.button("🗑️", key=f"msg_del_{idx}"):
                current_chat["messages"].pop(idx)
                st.rerun()
        with c2:
            st.download_button("💾", m["content"], file_name=f"mitra_msg_{idx}.txt", key=f"msg_save_{idx}")

# --- 5. యూజర్ ఇన్‌పుట్ ---
st.divider()
user_input = st.chat_input("మీ ఆధ్యాత్మిక సందేహాన్ని ఇక్కడ అడగండి...")

if user_input:
    current_chat["messages"].append({"role": "user", "content": user_input})
    
    if len(current_chat["messages"]) <= 2:
        current_chat["title"] = user_input[:20] + "..."

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("మిత్ర ఆలోచిస్తున్నాడు..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": st.session_state.ai_memory}] + current_chat["messages"]
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                current_chat["messages"].append({"role": "assistant", "content": answer})
                
                clean_ans = answer.replace("*","").replace("#","")
                tts = gTTS(text=clean_ans, lang='te')
                f = io.BytesIO(); tts.write_to_fp(f)
                st.audio(f)
            except Exception as e:
                st.error(f"Error: {e}")
    st.rerun()
