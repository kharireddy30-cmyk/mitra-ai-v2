import json
import urllib.request
import streamlit as st

def polish_and_translate_script(
    text, 
    target_lang="తెలుగు (గౌరవప్రదమైన కృష్ణా యాస / BK)", 
    style_mode="📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)", 
    pause_level="మధ్యస్థం (Normal Pauses)"
):
    """
    బ్రహ్మకుమారీస్ మరియు కృష్ణా జిల్లా గౌరవప్రదమైన భాషా శైలితో,
    సహజమైన శ్వాస విరామాలు (... మరియు కామాలు) అమర్చే AI అనువాద ఇంజిన్.
    """
    if not text or not text.strip():
        return ""
        
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    if not groq_key:
        return text

    system_prompt = """You are an elite multilingual translator and spiritual voiceover scriptwriter specializing in Brahma Kumaris (BK) respectful discourse and Krishna District refined, dignified Telugu (గౌరవప్రదమైన కృష్ణా యాస & సంస్కారవంతమైన ఆధ్యాత్మిక శైలి).

CORE TRANSLATION & DIALECT GUIDELINES:
1. RESPECTFUL & DIGNIFIED VOCABULARY (BK & Krishna District Telugu):
   - Use deeply respectful honorifics: 'ఆత్మ బంధువులందరికీ హృదయపూర్వక నమస్కారం / ఓంశాంతి', 'విశేషమైన సేవ', 'సద్వినియోగం చేసుకోగలరు', 'పాల్గొనవలసిందిగా కోరుతున్నాము', 'సర్వేజనా సుఖినోభవంతు'.
   - Avoid harsh, blunt, or overly casual words. Use polished, culturally rich words (e.g. 'రండి చేద్దాం' -> 'రండి! రక్తదానం చేద్దాం / ఈ మహోన్నత సేవలో భాగస్వామ్యులవుదాం').
2. HINDI (सरल, मधुर एवं आध्यात्मिक शैली):
   - Use respectful Hindi (e.g., 'आत्मिक भाई-बहनों को सादर नमस्कार / ॐ शांति', 'विशेष सेवा', 'आप सभी सादर आमंत्रित हैं').
3. ENGLISH (Dignified, Warm & Inspiring):
   - Expressive, inspiring, professional, and spiritual tone.
4. SPEECH PACING & BREATHING PAUSES:
   - Insert breathing pauses (...) and commas (,) naturally where a speaker takes a breath or emphasizes key points.
   - Break speech into crisp, readable clauses on separate lines for dates, times, venues, and concluding slogans.
5. STRICT OUTPUT RULE:
   - Output ONLY the polished/translated speech script. No explanations or conversational introductions."""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Target Language/Style: {target_lang}\nDelivery Style: {style_mode}\nPause Density: {pause_level}\n\nInput Text:\n{text}"}
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
