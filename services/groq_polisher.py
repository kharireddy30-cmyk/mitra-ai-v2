import os
import re
import json
import urllib.request
import streamlit as st

def polish_speech_script(text, style_mode="🧘 ఆధ్యాత్మికం (Spiritual & Calm)", pause_level="మధ్యస్థం (Normal Pauses)", user_instruction=""):
    """
    యూజర్ ఎంచుకున్న స్పీచ్ స్టైల్ (Style), పాజ్ లెవెల్ (Pause Level) మరియు 
    కస్టమ్ ఇన్‌స్ట్రక్షన్స్ ఆధారంగా స్క్రిప్ట్‌ను రూపొందించే AI ఇంజిన్.
    """
    if not text or not text.strip():
        return ""
        
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        return fallback_rule_based_polish(text, pause_level)

    style_guidelines = {
        "🧘 ఆధ్యాత్మికం (Spiritual & Calm)": "Use deeply peaceful, reverent pacing, longer thoughtful breathing pauses (...) after every phrase, making it sound meditative and spiritual.",
        "📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)": "Crisp, authoritative, clear pauses. Highlight dates, venues, times and core messages on separate lines so listeners absorb critical facts.",
        "📰 న్యూస్ రీడర్ (News Bulletin)": "Fast, formal, structured delivery with minimal ellipsis but clear punctuation and concise sentence units.",
        "🗣️ సంభాషణ / కబుర్లు (Conversational)": "Warm, engaging, natural conversational tone with soft pauses and friendly cadence."
    }

    pause_guidelines = {
        "స్వల్పం (Fast / Light Pauses)": "Use minimal commas, tight phrasing (5-8 words per chunk), fast flow.",
        "మధ్యస్థం (Normal Pauses)": "Standard rhythm (3-5 words per clause), using commas and short ellipses (...) at key phrase breaks.",
        "ఎక్కువ (Deep Breathing / Heavy Pauses)": "Frequent ellipsis (...) after almost every concept, 2-3 words per phrase, slow majestic cadence."
    }

    selected_style_rule = style_guidelines.get(style_mode, style_guidelines["🧘 ఆధ్యాత్మికం (Spiritual & Calm)"])
    selected_pause_rule = pause_guidelines.get(pause_level, pause_guidelines["మధ్యస్థం (Normal Pauses)"])

    system_prompt = f"""You are an elite multilingual voiceover director and speech scriptwriter.

TARGET STYLE:
- Delivery Style: {style_mode} -> {selected_style_rule}
- Pause Density: {pause_level} -> {selected_pause_rule}

CORE RULES:
1. FORMATTING FOR TTS SPEECH:
   - Insert ellipsis (...) and commas (,) strictly based on the chosen pause density and style.
   - Break speech onto separate lines for distinct thoughts, greetings, key actions, dates, and conclusions.
2. STT ERROR CORRECTION:
   - Fix misheard speech-to-text words while preserving Telugu, Hindi, or English vocabulary.
3. CUSTOM USER INSTRUCTION:
   {user_instruction if user_instruction.strip() else "Apply the selected style naturally without changing original meaning."}
4. STRICT OUTPUT FORMAT:
   - Output ONLY the formatted spoken script. No introduction, no markdown backticks, no explanations."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transform this text into the target voiceover script:\n\n{text}"}
        ],
        "temperature": 0.2
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            polished = res_data['choices'][0]['message']['content'].strip()
            return polished
    except Exception:
        return fallback_rule_based_polish(text, pause_level)

def fallback_rule_based_polish(text, pause_level):
    clean_txt = re.sub(r'\s+', ' ', text).strip()
    pause_mark = "..." if "ఎక్కువ" in pause_level else ","
    connectors = ["అయితే", "మరియు", "కానీ", "కాబట్టి", "అందువల్ల", "ఎందుకంటే", "అలాగే", "నమస్కారం", "और", "लेकिन", "इसलिए"]
    for c in connectors:
        clean_txt = clean_txt.replace(f" {c} ", f" {pause_mark} {c} ")

    words = clean_txt.split(" ")
    chunk_size = 4 if "ఎక్కువ" in pause_level else (7 if "మధ్యస్థం" in pause_level else 10)
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return f" {pause_mark}\n\n".join(chunks)
