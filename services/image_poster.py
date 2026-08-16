import os
import json
import urllib.request
import streamlit as st

def generate_ai_poster_html(text, theme="ఆధ్యాత్మికం (Golden Divine)"):
    """
    Groq AI ద్వారా టెక్స్ట్‌ను విశ్లేషించి హై-క్వాలిటీ గ్రాఫిక్ పోస్టర్ (HTML Canvas Card) రూపొందించే ఇంజిన్.
    """
    if not text or not text.strip():
        return ""

    groq_key = st.secrets.get("GROQ_API_KEY", "")
    
    theme_styles = {
        "ఆధ్యాత్మికం (Golden Divine)": "linear-gradient(135deg, #1a0b2e 0%, #3b1d60 50%, #1a0b2e 100%)",
        "రక్తదానం / సేవా కార్యక్రమం (Red & White)": "linear-gradient(135deg, #7f1d1d 0%, #991b1b 50%, #450a0a 100%)",
        "ప్రకృతి / పచ్చదనం (Nature Green)": "linear-gradient(135deg, #064e3b 0%, #047857 50%, #022c22 100%)",
        "రాయల్ బ్లూ (Corporate & Formal)": "linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%)"
    }
    bg_gradient = theme_styles.get(theme, theme_styles["ఆధ్యాత్మికం (Golden Divine)"])

    system_prompt = """You are an expert graphic designer and layout artist for Telugu, Hindi, and English posters and social media banners.
Your goal: Analyze the given text and extract:
1. "title": A short, impactful, grand title (3-6 words).
2. "subtitle": A brief context or organizing body (e.g. date, venue, or organizers).
3. "highlights": An array of 3 to 5 key bullet points (concise phrases).
4. "footer_quote": A powerful ending slogan, blessing, or call to action (e.g. 'రక్తదానం - ప్రాణదానం' or 'సర్వేజనా సుఖినోభవంతు').

STRICT JSON OUTPUT ONLY:
{
  "title": "...",
  "subtitle": "...",
  "highlights": ["...", "...", "..."],
  "footer_quote": "..."
}"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract poster layout details from this text:\n\n{text}"}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            parsed = json.loads(res_data['choices'][0]['message']['content'])
    except Exception:
        parsed = {
            "title": "సందేశం / ప్రకటన",
            "subtitle": "",
            "highlights": [text[:150]],
            "footer_quote": "సర్వేజనా సుఖినోభవంతు"
        }

    # ఆకర్షణీయమైన పోస్టర్ HTML టెంప్లేట్ నిర్మాణం
    bullets_html = "".join([f"<li style='margin-bottom: 12px; font-size: 19px; line-height: 1.6; color: #f1f5f9;'>✨ {hl}</li>" for hl in parsed.get("highlights", [])])

    poster_html = f"""<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="utf-8">
<title>AI Graphic Poster</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Mandali&family=Cinzel:wght@700&display=swap');
  * {{ box-sizing: border-box; font-family: 'Mandali', sans-serif; }}
  body {{ margin: 0; padding: 20px; display: flex; justify-content: center; background: #0b0f19; }}
  .poster-card {{
      width: 600px;
      min-height: 750px;
      background: {bg_gradient};
      border: 4px solid #facc15;
      border-radius: 20px;
      padding: 35px 30px;
      color: #ffffff;
      box-shadow: 0 15px 35px rgba(0,0,0,0.6);
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
  }}
  .inner-border {{
      position: absolute;
      top: 10px; left: 10px; right: 10px; bottom: 10px;
      border: 1px dashed rgba(250, 204, 21, 0.4);
      border-radius: 14px;
      pointer-events: none;
  }}
  .header {{ text-align: center; margin-bottom: 20px; }}
  .symbol {{ font-size: 38px; color: #facc15; margin-bottom: 6px; }}
  .title {{ font-size: 28px; font-weight: bold; color: #facc15; text-shadow: 0 2px 8px rgba(0,0,0,0.5); line-height: 1.3; }}
  .subtitle {{ font-size: 16px; color: #cbd5e1; margin-top: 6px; border-bottom: 1px solid rgba(250,204,21,0.3); padding-bottom: 12px; }}
  .content-box {{
      background: rgba(0, 0, 0, 0.35);
      border-radius: 12px;
      padding: 20px;
      margin: 15px 0;
      border: 1px solid rgba(255, 255, 255, 0.1);
  }}
  ul {{ list-style-type: none; padding-left: 5px; margin: 0; }}
  .footer {{
      text-align: center;
      background: rgba(250, 204, 21, 0.15);
      border: 1px solid #facc15;
      border-radius: 10px;
      padding: 12px;
      margin-top: 15px;
  }}
  .footer-quote {{ font-size: 20px; font-weight: bold; color: #fde047; margin: 0; }}
</style>
</head>
<body>
<div class="poster-card">
  <div class="inner-border"></div>
  <div class="header">
    <div class="symbol">🕉️ 🔱 🕉️</div>
    <div class="title">{parsed.get("title", "")}</div>
    <div class="subtitle">{parsed.get("subtitle", "")}</div>
  </div>
  
  <div class="content-box">
    <ul>
      {bullets_html}
    </ul>
  </div>
  
  <div class="footer">
    <p class="footer-quote">🌺 {parsed.get("footer_quote", "")} 🌺</p>
  </div>
</div>
</body>
</html>"""
    return poster_html
