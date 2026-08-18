import json
import re
import urllib.request
import streamlit as st

def fallback_auto_punctuate(text):
    """
    Groq API అందుబాటులో లేనప్పుడు లేదా ప్రాసెస్ కానప్పుడు,
    సుదీర్ఘ వచనాన్ని చిన్న వాక్యాలుగా మరియు విరామ చిహ్నాలుగా విభజించే ఫాల్‌బ్యాక్ ఫంక్షన్.
    """
    if not text:
        return ""
    
    # 8-12 పదాల తర్వాత స్వయంచాలకంగా కామాలు మరియు వాక్యాల విరామాలు అమర్చడం
    words = text.split()
    if len(words) < 5:
        return text
    
    result = []
    word_count = 0
    
    for word in words:
        result.append(word)
        word_count += 1
        
        # హిందీ / సంస్కృతం విరామం లేదా తెలుగు విరామం
        if word_count >= 10:
            if any(char in word for char in ["है", "హై", "ఉంది", "చారే", "था", "గాక", "కరో", "చేయండి", "होने"]):
                result.append("।\n")
            else:
                result.append(",")
            word_count = 0
            
    final_text = " ".join(result)
    # కామాలు మరియు పూర్ణవిరామాల దగ్గర క్లీనప్
    final_text = re.sub(r'\s+([,।\.\?])', r'\1', final_text)
    final_text = re.sub(r'([,।\.\?])\s*', r'\1 ', final_text)
    final_text = re.sub(r'\n\s*', r'\n', final_text)
    return final_text.strip()


def polish_speech_script(
    text, 
    style_mode="📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)", 
    pause_level="మధ్యస్థం (Normal Pauses)", 
    user_instruction=""
):
    """
    Groq AI ద్వారా స్పీచ్ స్క్రిప్ట్‌ను పాలిష్ చేసి,
    ఖచ్చితమైన కామాలు, పూర్ణవిరామాలు (।, .) మరియు శ్వాస విరామాలు (...) అమర్చే కోర్ ఇంజిన్.
    """
    if not text or not text.strip():
        return ""
        
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    
    style_guidelines = {
        "🧘 ఆధ్యాత్మికం (Spiritual & Calm)": "Use deeply peaceful pacing. Insert full stops (। or .), commas (,), and breathing pauses (...) after every short phrase (3-5 words). Separate sentences onto new lines.",
        "📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)": "Authoritative delivery. Use strict full stops, clear commas at every pause, and line breaks for every new thought/venue/date.",
        "📰 న్యూస్ రీడర్ (News Bulletin)": "Crisp and structured. Insert commas and full stops strictly at clause boundaries for clear reading.",
        "🗣️ సంభాషణ / కబుర్లు (Conversational)": "Warm tone with natural commas, question marks (?), and soft ellipses (...) for realistic speech flow."
    }

    pause_guidelines = {
        "స్వల్పం (Fast / Light Pauses)": "Add commas (,) every 6-8 words and full stops (। or .) at sentence endings.",
        "మధ్యస్థం (Normal Pauses)": "Add commas (,) every 4-6 words, full stops (। or .) after every sentence, and short breathing pauses (...) between key phrases.",
        "ఎక్కువ (Deep Breathing / Heavy Pauses)": "Frequent ellipses (...) after every 2-4 words, commas (,), and line breaks (\n) for a slow, meditative cadence."
    }

    selected_style_rule = style_guidelines.get(style_mode, style_guidelines["📢 పబ్లిక్ అనౌన్స్‌మెంట్ (Public Notice)"])
    selected_pause_rule = pause_guidelines.get(pause_level, pause_guidelines["మధ్యస్థం (Normal Pauses)"])

    system_prompt = f"""You are a master voiceover director and speech editor specializing in Hindi, Telugu, and English scripts.

CRITICAL MANDATORY REQUIREMENT:
The input text MAY TOTALLY LACK PUNCTUATION (no commas, no full stops, no question marks).
YOUR MOST IMPORTANT TASK IS TO INJECT ALL MISSING PUNCTUATION:
1. FULL STOPS: Use '।' for Hindi/Sanskrit/Devanagari, and '.' for Telugu/English at the end of every sentence.
2. COMMAS: Insert commas (,) frequently inside sentences wherever a speaker must pause or breathe.
3. QUESTION MARKS: Add '?' wherever a question is asked.
4. LINE BREAKS: Separate major sentences or ideas onto new lines (\\n).

PACING & STYLE:
- Target Style: {selected_style_rule}
- Target Pause Density: {selected_pause_rule}

CORRECTIONS & TONE:
- Correct voice STT misheard words, grammar, and typos.
- Keep the language respectful, polite, and dignified.

USER INSTRUCTION:
{user_instruction if user_instruction.strip() else "Mandatorily add commas, full stops (। or .), and line breaks to break continuous unpunctuated text into natural sentences."}

STRICT OUTPUT RULE:
Return ONLY the final polished script with all injected commas, full stops, ellipses, and line breaks.
No introductory text, no explanations, no markdown code blocks wrapper."""

    if not groq_key:
        return fallback_auto_punctuate(text)

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
                {"role": "user", "content": f"MANDATORY: Inject missing commas (,), full stops (। or .), and line breaks into this text for natural voiceover reading:\n\n{text}"}
            ],
            "temperature": 0.1
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
                # Markdown wrappers ఉన్నా తీసివేసి శుభ్రపరచడం
                polished = re.sub(r'^
```[a-z]*\n?', '', polished, flags=re.IGNORECASE)
                polished = re.sub(r'\n?
```$', '', polished)
                if polished and len(polished) > 5:
                    return polished.strip()
        except Exception:
            continue

    return fallback_auto_punctuate(text)
