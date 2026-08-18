import json
import urllib.request
import streamlit as st

def polish_and_translate_script(
    text, 
    target_lang="హిందీ (सरल व आध्यात्मिक शैली)", 
    style_mode="📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)", 
    pause_level="మధ్యస్థం (Normal Pauses)"
):
    if not text or not text.strip():
        return ""
        
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        return text

    # భాషా నిబంధనలు (Strict Language Rules)
    if "హిందీ" in target_lang:
        lang_rule = "CRITICAL MANDATE: TRANSLATE THE ENTIRE INPUT INTO PURE, RESPECTFUL HINDI (देवनागरी लिपि). Do NOT keep it in Telugu or English. Use Brahma Kumaris style respectful Hindi (e.g., 'आत्मिक भाई-बहनों को सादर ॐ शांति', 'रक्तदान महादान', 'आप सभी सादर आमंत्रित हैं')."
    elif "English" in target_lang or "ఇంగ్లీష్" in target_lang:
        lang_rule = "CRITICAL MANDATE: TRANSLATE THE ENTIRE INPUT INTO DIGNIFIED, INSPIRING ENGLISH. Do NOT keep it in Indian vernacular script."
    elif "తెలుగు" in target_lang:
        lang_rule = "CRITICAL MANDATE: TRANSLATE/POLISH THE INPUT INTO HIGHLY RESPECTFUL, DIGNIFIED TELUGU (Brahma Kumaris & Krishna District dialect - e.g., 'ఆత్మ బంధువులందరికీ హృదయపూర్వక నమస్కారం / ఓంశాంతి', 'ఈ మహోన్నత సేవలో పాల్గొనగలరు')."
    else:
        lang_rule = "Keep the original language and only format with breathing pauses and fix spelling errors."

    system_prompt = f"""You are a master multilingual translator and speech director.

{lang_rule}

VOICEOVER & PACING RULES:
1. Insert breathing pauses (...) and commas (,) naturally where a speaker takes a breath or emphasizes key points.
2. Break speech into crisp, readable clauses on separate lines for dates, times, venues, and concluding slogans.
3. Output ONLY the translated/polished final spoken script. No explanations, no notes, no markdown codeblocks."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transform this text into the target format:\n\n{text}"}
        ],
        "temperature": 0.2
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            polished = res_data['choices'][0]['message']['content'].strip()
            return polished
    except Exception:
        return text
