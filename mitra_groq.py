import streamlit as st
import edge_tts
from pydub import AudioSegment
import asyncio
import io
import uuid
import re

# --- 1. పేజీ సెట్టింగ్స్ ---
st.set_page_config(
    page_title="Brahma Kumaris - Spiritual Auto-Chunking Voice Generator", 
    layout="wide", 
    page_icon="🧘"
)

# --- 2. ఇనిషియలైజేషన్ ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}  
if "current_chat_id" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.chat_history[initial_id] = {"title": "కొత్త ఆడియో నోట్", "messages": []}
    st.session_state.current_chat_id = initial_id

if "rename_id" not in st.session_state:
    st.session_state.rename_id = None

# Single Chunk Edge-TTS Async
async def generate_voice_chunk(text, voice, pitch_val, rate_val):
    communicate = edge_tts.Communicate(text, voice, pitch=pitch_val, rate=rate_val)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# టెక్స్ట్‌ని చిన్న ముక్కలుగా విడదీసే ఫంక్షన్ (Auto-Chunking Logic)
def split_text_into_chunks(text, max_chars=400):
    sentences = re.split(r'(?<=[.!?\n])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks

# --- 3. సైడ్ బార్ ---
with st.sidebar:
    st.title("🕉️ ఆడియో నోట్స్ కంట్రోల్స్")
    if st.button("➕ కొత్త ఆడియో నోట్", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chat_history[new_id] = {"title": "కొత్త ఆడియో నోట్", "messages": []}
        st.session_state.current_chat_id = new_id
        st.session_state.rename_id = None
        st.rerun()

    st.divider()
    st.subheader("సేవ్ చేసిన ఆడియో జాబితా")
    
    for chat_id in list(st.session_state.chat_history.keys()):
        if st.session_state.rename_id == chat_id:
            new_title = st.text_input("కొత్త టైటిల్ ఇవ్వండి:", value=st.session_state.chat_history[chat_id]["title"], key=f"input_ren_{chat_id}")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("Save", key=f"save_title_{chat_id}"):
                    st.session_state.chat_history[chat_id]["title"] = new_title
                    st.session_state.rename_id = None
                    st.rerun()
            with col_s2:
                if st.button("Cancel", key=f"cancel_title_{chat_id}"):
                    st.session_state.rename_id = None
                    st.rerun()
        else:
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            with col1:
                btn_label = st.session_state.chat_history[chat_id]["title"]
                if st.button(btn_label, key=f"btn_{chat_id}", use_container_width=True):
                    st.session_state.current_chat_id = chat_id
                    st.rerun()
            with col2:
                if st.button("✏️", key=f"ren_{chat_id}"):
                    st.session_state.rename_id = chat_id
                    st.rerun()
            with col3:
                if st.button("🗑️", key=f"del_{chat_id}"):
                    del st.session_state.chat_history[chat_id]
                    if not st.session_state.chat_history:
                        new_id = str(uuid.uuid4())
                        st.session_state.chat_history[new_id] = {"title": "కొత్త ఆడియో నోట్", "messages": []}
                        st.session_state.current_chat_id = new_id
                    elif st.session_state.current_chat_id == chat_id:
                        st.session_state.current_chat_id = list(st.session_state.chat_history.keys())[0]
                    st.rerun()

# --- 4. ప్రధాన స్క్రీన్ ---
st.header("🔱 బ్రహ్మకుమారీస్ - ఆధ్యాత్మిక లాంగ్ మురళీ వాయిస్ కన్వర్టర్")
st.caption("ఎంత పెద్ద మురళీ టెక్స్ట్‌నైనా క్షణాల్లో కట్ అవ్వకుండా పూర్తిస్థాయి MP3 ఆడియోగా మార్చుకోండి.")

current_chat = st.session_state.chat_history[st.session_state.current_chat_id]
msg_to_delete = None

for idx, m in enumerate(current_chat["messages"]):
    with st.chat_message("assistant", avatar="🕉️"):
        st.markdown(m["text"])
        st.caption(f"🎙️ వాయిస్: {m.get('voice_name', 'తెలుగు')} | 🔊 వేగం: {m.get('speed', 1.0)}x")
        
        if "audio" in m and m["audio"] is not None:
            st.audio(m["audio"], format="audio/mp3")

        c1, c2, _ = st.columns([0.08, 0.18, 0.74])
        with c1:
            if st.button("🗑️", key=f"msg_del_{idx}"):
                msg_to_delete = idx
        with c2:
            if "audio" in m and m["audio"] is not None:
                st.download_button(
                    label="📥 MP3 డౌన్‌లోడ్", 
                    data=m["audio"], 
                    file_name=f"spiritual_murli_audio_{idx+1}.mp3", 
                    mime="audio/mp3",
                    key=f"audio_dl_{idx}"
                )

if msg_to_delete is not None:
    current_chat["messages"].pop(msg_to_delete)
    st.rerun()

# --- 5. ఇన్‌పుట్ & సెట్టింగ్స్ ---
st.divider()
user_text = st.text_area("ఆడియోగా మార్చాలనుకుంటున్న మురళీ / ఆధ్యాత్మిక టెక్స్ట్‌ని ఇక్కడ పేస్ట్ చేయండి:", height=150, placeholder="బాబా చెప్పారు... ఓం శాంతి.")

col_1, col_2 = st.columns([0.5, 0.5])

with col_1:
    voice_option = st.radio(
        "🎙️ స్వరాన్ని ఎంచుకోండి:",
        options=["👨 మోహన్ (గంభీరమైన పురుష గొంతు)", "👩 శ్రుతి (స్పష్టమైన స్త్రీ గొంతు)"],
        horizontal=True
    )

with col_2:
    audio_speed = st.select_slider(
        "🔊 ఆడియో వేగం (Speed):",
        options=[0.75, 0.85, 1.0, 1.15, 1.25, 1.5],
        value=0.85,
        help="0.85x వేగం ఆధ్యాత్మిక వాయిస్‌కి చాలా ప్రశాంతంగా ఉంటుంది."
    )

convert_btn = st.button("🔊 ఆధ్యాత్మిక మురళీ వాయిస్ క్రియేట్ చేయి", type="primary", use_container_width=True)

if convert_btn:
    if user_text.strip():
        with st.spinner("పెద్ద టెక్స్ట్‌ని ప్రాసెస్ చేసి, గంభీరమైన మురళీ ఆడియోగా మారుస్తోంది... దయచేసి వేచి ఉండండి..."):
            try:
                clean_txt = user_text.replace("*", "").replace("#", "")
                
                selected_voice = "te-IN-MohanNeural" if "మోహన్" in voice_option else "te-IN-ShrutiNeural"
                voice_label = "మోహన్ (పురుష)" if "మోహన్" in voice_option else "శ్రుతి (స్త్రీ)"

                # స్పీడ్ & పిచ్ సెట్టింగ్స్
                rate_str = f"{int((audio_speed - 1.0) * 100):+d}%"
                pitch_str = "-10Hz" if "మోహన్" in voice_option else "-5Hz"

                # 1. టెక్స్ట్‌ని చిన్న భాగముగా విడదీయడం (Auto-Chunking)
                text_chunks = split_text_into_chunks(clean_txt, max_chars=350)
                
                combined_sound = AudioSegment.empty()
                silence_pause = AudioSegment.silent(duration=500) # వాక్యాల మధ్య అర సెకను గ్యాప్

                # 2. ప్రతీ చంక్ నూ విడివిడిగా ప్రాసెస్ చేసి కలపడం (Stitching)
                for chunk in text_chunks:
                    raw_audio = asyncio.run(generate_voice_chunk(chunk, selected_voice, pitch_str, rate_str))
                    chunk_sound = AudioSegment.from_file(io.BytesIO(raw_audio), format="mp3")
                    combined_sound += chunk_sound + silence_pause

                final_fp = io.BytesIO()
                combined_sound.export(final_fp, format="mp3")
                final_fp.seek(0)
                audio_bytes = final_fp.getvalue()

                # 3. సేవ్ చేయడం
                current_chat["messages"].append({
                    "text": user_text,
                    "audio": audio_bytes,
                    "speed": audio_speed,
                    "voice_name": voice_label
                })

                if len(current_chat["messages"]) == 1 or current_chat["title"] == "కొత్త ఆడియో నోట్":
                    current_chat["title"] = user_text[:20] + ("..." if len(user_text) > 20 else "")

                st.success("విజయవంతంగా పూర్తి స్థాయి మురళీ ఆడియో సిద్ధమైంది!")
                st.rerun()

            except Exception as e:
                st.error(f"ఆడియో తయారీలో లోపం: {e}")
    else:
        st.warning("దయచేసి టెక్స్ట్ ఎంటర్ చేయండి.")
