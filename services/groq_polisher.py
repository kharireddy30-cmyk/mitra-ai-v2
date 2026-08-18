import json
import urllib.request
import streamlit as st

def polish_and_translate_script(
    text, 
    target_lang="అసలు భాష (Original)", 
    style_mode="📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)", 
    pause_level="మధ్యస్థం (Normal Pauses)", 
    user_instruction=""
):
    """
    Groq AI ద్వారా స్పీచ్ స్క్రిప్ట్‌ను భావయుక్తంగా అనువదించి (Expressive Translation),
    సహజమైన విరామాలు (... మరియు కామాలు) అమర్చే ఇంజిన్.
    """
    if not text or not text.strip():
        return ""
        
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        return text

    style_guidelines = {
        "🧘 ఆధ్యాత్మికం (Spiritual & Calm)": "Use deeply peaceful, reverent pacing, longer thoughtful breathing pauses (...) after every phrase.",
        "📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)": "Crisp, authoritative, clear pauses. Highlight dates, venues, and calls to action.",
        "📰 న్యూస్ రీడర్ (News Bulletin)": "Fast, formal, structured delivery with minimal ellipsis and concise punctuation.",
        "🗣️ సంభాషణ / కబుర్లు (Conversational)": "Warm, engaging, natural conversational tone with soft pauses."
    }

    pause_guidelines = {
        "స్వల్పం (Fast / Light Pauses)": "Use minimal commas, tight phrasing, fast flow.",
        "మధ్యస్థం (Normal Pauses)": "Standard rhythm (3-5 words per clause), using commas and short ellipses (...) at phrase breaks.",
        "ఎక్కువ (Deep Breathing / Heavy Pauses)": "Frequent ellipsis (...) after every concept, 2-3 words per phrase, slow cadence."
    }

    translation_instructions = {
        "అసలు భాష (Original)": "Keep the output in the original language of the text without translating.",
        "తెలుగు (Telugu)": "Accurately and expressively TRANSLATE the text into natural, grammatically rich Telugu (భావయుక్తమైన సహజ తెలుగు). Preserve nuances.",
        "హిందీ (Hindi)": "Accurately and expressively TRANSLATE the text into fluent, natural Hindi (सरल और प्रभावी हिंदी).",
        "ఇంగ్లీష్ (English)": "Accurately and expressively TRANSLATE the text into polished, fluent English with natural flow."
    }

    selected_style_rule = style_guidelines.get(style_mode, style_guidelines["📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)"])
    selected_pause_rule = pause_guidelines.get(pause_level, pause_guidelines["మధ్యస్థం (Normal Pauses)"])
    selected_trans_rule = translation_instructions.get(target_lang, translation_instructions["అసలు భాష (Original)"])

    system_prompt = f"""You are a master multilingual translator and speech director specializing in Telugu, Hindi, and English spiritual discourses and public announcements.

YOUR DUAL MISSION:
1. TRANSLATION (Contextual & Expressive):
   {selected_trans_rule}
   - Do NOT do word-by-word literal robotic translation. Translate the TRUE MEANING, emotion, and tone (భావార్థం).
   - Fix misheard words and grammatical errors.

2. VOICE & SPEECH PACING:
   - Target Style: {selected_style_rule}
   - Target Pause Density: {selected_pause_rule}
   - Insert breathing pauses (...) and commas (,) naturally where a professional speaker pauses to breathe or emphasize key points.
   - Break speech into short readable clauses on separate lines for key facts (greetings, dates, times, venues, conclusions).

3. USER INSTRUCTION:
   {user_instruction if user_instruction.strip() else "Translate and format with natural flow."}

4. STRICT OUTPUT:
   - Output ONLY the translated, formatted final spoken script.
   - No explanations, notes, or meta text."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Translate and polish this content into target format:\n\n{text}"}
        ],
        "temperature": 0.2
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=14) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            polished = res_data['choices'][0]['message']['content'].strip()
            return polished
    except Exception:
        return text
