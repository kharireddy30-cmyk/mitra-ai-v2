import os
import re
import json
import urllib.request
import streamlit as st

def polish_speech_script(text):
    """
    తెలుగు, హిందీ, ఇంగ్లీష్ భాషల్లో సహజమైన శ్వాస విరామాలు (Natural Speech Pauses),
    చిన్న చిన్న వాక్య విభాగాలు (... మరియు కామాలు), స్పెల్లింగ్ కరెక్షన్స్ చేసే AI మాడ్యూల్.
    భవిష్యత్తులో ప్రాంప్ట్ మార్చాలంటే కేవలం ఈ ఫైల్‌ను మారిస్తే సరిపోతుంది.
    """
    if not text or not text.strip():
        return ""
        
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        return fallback_rule_based_polish(text)

    system_prompt = """You are an elite speech scriptwriter and voiceover director for Telugu, Hindi, and English announcements and spiritual discourses.

YOUR GOAL:
Transform raw/STT transcribed text into an emotionally resonant, beautifully paced spoken speech script with natural breathing pauses for Text-to-Speech (TTS).

RULES FOR FORMATTING & SPEECH PACING:
1. BREATHING PAUSES (... and commas):
   - Add ellipsis (...) and commas (,) where a human speaker would pause to take a breath or emphasize a point (e.g., "ఆత్మ బంధువులందరికీ... నమస్కారం!").
   - Break long run-on sentences into short, crisp lines (2 to 5 words per clause).
2. INTENTIONAL LINE BREAKS:
   - Separate distinct ideas, greetings, dates, times, venues, and concluding thoughts into separate lines and short paragraphs.
3. FIX STT ERRORS:
   - Fix speech recognition mistakes and misheard words (e.g., 'రక్తదాక్త న' -> 'రక్తదాన', 'రెండు చేద్దాం' -> 'రండి! రక్తదానం చేద్దాం', 'సర్వేజనా' -> 'సర్వేజనాః/సర్వేజనా').
4. MULTI-LANGUAGE SUPPORT:
   - If the input is Telugu, Hindi, English, or Code-mixed, preserve the exact language/context and apply speech pacing in that language.
5. STRICT OUTPUT RULE:
   - Output ONLY the polished, formatted final spoken script.
   - Do NOT include any explanations, greetings, quotes, or conversational notes."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transform this raw text into a natural speech script with rhythmic pauses and short lines:\n\n{text}"}
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
        return fallback_rule_based_polish(text)

def fallback_rule_based_polish(text):
    """ఆఫ్‌లైన్ బ్యాకప్ పద్ధతి"""
    clean_txt = re.sub(r'\s+', ' ', text).strip()
    connectors = ["అయితే", "మరియు", "కానీ", "కాబట్టి", "అందువల్ల", "ఎందుకంటే", "అలాగే", "మరోవైపు", "తో పాటు", "తర్వాత", "నమస్కారం"]
    for c in connectors:
        clean_txt = clean_txt.replace(f" {c} ", f"... {c}, ")
        
    hi_connectors = ["और", "लेकिन", "इसलिए", "क्योंकि", "तो", "परंतु", "तथा", "नमस्ते", "नमस्कार"]
    for hc in hi_connectors:
        clean_txt = clean_txt.replace(f" {hc} ", f"... {hc}, ")

    words = clean_txt.split(" ")
    formatted_chunks = []
    curr = []
    for w in words:
        curr.append(w)
        if len(curr) >= 8 or w.endswith((".", "।", "!", "?", "...", ":")):
            formatted_chunks.append(" ".join(curr))
            curr = []
    if curr:
        formatted_chunks.append(" ".join(curr))
        
    return "...\n\n".join(formatted_chunks)
