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

    # ఖచ్చితమైన భాషా మార్పిడి రూల్స్
    if "హిందీ" in target_lang:
        instruction = "MANDATORY: You MUST translate the ENTIRE text into pure Hindi written in DEVANAGARI SCRIPT (हिन्दी लिपि). Do NOT output a single Telugu word. Use Brahma Kumaris respectful tone like 'आत्मिक भाई-बहनों को सादर ॐ शांति', 'रक्तदान महादान', 'सादर आमंत्रित हैं'."
    elif "ఇంగ్లీష్" in target_lang or "English" in target_lang:
        instruction = "MANDATORY: You MUST translate the ENTIRE text into dignified, fluent English. Do NOT output Telugu words."
    elif "తెలుగు" in target_lang:
        instruction = "MANDATORY: Convert the text into highly respectful Brahma Kumaris & Krishna district refined Telugu with honorific words like 'ఆత్మ బంధువులందరికీ హృదయపూర్వక నమస్కారం / ఓంశాంతి', 'ఈ మహోన్నత సేవలో పాల్గొనగలరు'."
    else:
        instruction = "Keep the original language and only add natural breathing pauses (...)."

    system_prompt = f"""You are a professional multilingual translator.

{instruction}

RULES:
1. Translate fully into the requested language script.
2. Add breathing pauses (...) and commas (,) where a voiceover speaker takes breath.
3. Put dates, times, and key action lines on separate lines.
4. Output ONLY the translated script. No intros, no notes, no English explanations."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Translate this text now:\n\n{text}"}
        ],
        "temperature": 0.1
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=18) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            polished = res_data['choices'][0]['message']['content'].strip()
            return polished
    except Exception:
        return text
