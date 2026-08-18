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
        return "⚠️ Groq API Key Not Found! Please check secrets.toml"

    # భాషా సూచనలు (Strict Language Rules)
    if "హిందీ" in target_lang:
        instruction = "MANDATORY: Translate the entire content into pure, respectful HINDI in Devanagari script (हिन्दी). Do NOT use Telugu words. Example tone: 'आत्मिक भाई-बहनों को सादर ॐ शांति', 'रक्तदान महादान', 'आप सभी सादर आमंत्रित हैं'."
    elif "ఇంగ్లీష్" in target_lang or "English" in target_lang:
        instruction = "MANDATORY: Translate the entire content into dignified, inspiring, and fluent ENGLISH. Do NOT output Telugu words."
    elif "తెలుగు" in target_lang:
        instruction = "MANDATORY: Refine and polish the content into highly respectful Brahma Kumaris & Krishna district dignified Telugu ('ఆత్మ బంధువులందరికీ హృదయపూర్వక నమస్కారం / ఓంశాంతి', 'ఈ మహోన్నత సేవలో పాల్గొనగలరు')."
    else:
        instruction = "Keep the original language and polish speech pacing."

    prompt_content = f"""You are a master translator and speech director.
TASK: {instruction}

RULES:
1. Output ONLY the translated speech text.
2. Insert breathing pauses (...) and commas (,) naturally.
3. Put dates, times, venues on separate lines.
4. No intro, no explanations, no markdown tags.

TEXT TO TRANSLATE:
{text}"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key.strip()}",
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    # స్థిరమైన మరియు ఖచ్చితమైన మోడల్స్
    models_to_try = ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt_content}
            ],
            "temperature": 0.2
        }

        try:
            json_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=20) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                translated_result = res_data['choices'][0]['message']['content'].strip()
                return translated_result
                
        except urllib.error.HTTPError as he:
            err_body = he.read().decode('utf-8')
            if "model_not_found" in err_body:
                continue  # తదుపరి మోడల్‌తో ప్రయత్నిస్తుంది
            return f"⚠️ API Error ({he.code}): {err_body}"
        except Exception as e:
            return f"⚠️ Connection Error: {str(e)}"

    return "⚠️ Error: Unable to connect with available Groq models."
