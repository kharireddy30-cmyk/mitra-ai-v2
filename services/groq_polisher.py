import json
import urllib.request
import streamlit as st

def polish_speech_script(
    text, 
    style_mode="📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)", 
    pause_level="మధ్యస్థం (Normal Pauses)", 
    user_instruction=""
):
    """
    Groq AI ద్వారా స్పీచ్ స్క్రిప్ట్‌ను గౌరవప్రదమైన శైలితో పాలిష్ చేసి,
    సహజమైన శ్వాస విరామాలు (... మరియు కామాలు) అమర్చే కోర్ ఇంజిన్.
    """
    if not text or not text.strip():
        return ""
        
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        return text

    style_guidelines = {
        "🧘 ఆధ్యాత్మికం (Spiritual & Calm)": "Use deeply peaceful, reverent pacing, thoughtful breathing pauses (...) after every key phrase. Use dignified Telugu.",
        "📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)": "Crisp, authoritative, clear pauses. Highlight dates, venues, timings, and calls to action.",
        "📰 న్యూస్ రీడర్ (News Bulletin)": "Fast, formal, structured delivery with minimal ellipsis and concise punctuation.",
        "🗣️ సంభాషణ / కబుర్లు (Conversational)": "Warm, engaging, natural conversational tone with soft pauses."
    }

    pause_guidelines = {
        "స్వల్పం (Fast / Light Pauses)": "Use minimal commas, tight phrasing, fast flow.",
        "మధ్యస్థం (Normal Pauses)": "Standard rhythm (3-5 words per clause), using commas and short ellipses (...) at phrase breaks.",
        "ఎక్కువ (Deep Breathing / Heavy Pauses)": "Frequent ellipsis (...) after every concept, 2-3 words per phrase, slow cadence."
    }

    selected_style_rule = style_guidelines.get(style_mode, style_guidelines["📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)"])
    selected_pause_rule = pause_guidelines.get(pause_level, pause_guidelines["మధ్యస్థం (Normal Pauses)"])

    system_prompt = f"""You are a master speech director and voiceover scriptwriter specializing in Telugu, Hindi, and English public notices and spiritual discourses.

YOUR MISSION:
1. SCRIPT POLISHING & FIXES:
   - Correct misheard words, spelling mistakes, and grammar from voice STT.
   - Maintain a highly respectful, polite, and dignified tone.

2. VOICE & SPEECH PACING:
   - Target Style: {selected_style_rule}
   - Target Pause Density: {selected_pause_rule}
   - Insert breathing pauses (...) and commas (,) naturally where a professional speaker pauses to breathe or emphasize key points.
   - Break speech into short readable clauses on separate lines for key facts (greetings, dates, times, venues, conclusions).

3. USER INSTRUCTION:
   {user_instruction if user_instruction.strip() else "Format with natural pacing and clean rhythm."}

4. STRICT OUTPUT:
   - Output ONLY the polished final spoken script.
   - No explanations, notes, or meta text."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key.strip()}",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    for model_name in models:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Polish this text for speech:\n\n{text}"}
            ],
            "temperature": 0.2
        }

        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), 
                headers=headers, 
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=18) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                polished = res_data['choices'][0]['message']['content'].strip()
                return polished
        except Exception:
            continue

    return text
