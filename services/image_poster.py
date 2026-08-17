import os
import json
import base64
import urllib.request
import streamlit as st

def get_sticker_symbol(sticker_choice, text=""):
    """యూజర్ ఎంపిక లేదా AI మ్యాజిక్ ద్వారా స్టిక్కర్ ఎంబవ్‌ను గుర్తిస్తుంది"""
    stickers_map = {
        "🕉️ ఓం (Divine Om)": "🕉️",
        "🪷 పద్మం (Sacred Lotus)": "🪷",
        "🩸 రక్తదానం (Blood Drop)": "🩸",
        "🕊️ శాంతి కపోతం (Peace Dove)": "🕊️",
        "🌟 గోల్డెన్ స్టార్ (Golden Star)": "🌟",
        "📜 రాయల్ సీల్ (Royal Seal)": "📜",
        "❤️ సేవా హస్తం (Loving Care)": "❤️"
    }
    
    if sticker_choice == "🪄 AI మ్యాజిక్ (Auto Select)":
        clean_t = text.lower()
        if any(k in clean_t for k in ["రక్తం", "రక్తదాన", "సేవ", "ఆసుపత్రి", "బ్లడ్"]):
            return "🩸"
        elif any(k in clean_t for k in ["ఓం", "శాంతి", "ధ్యానం", "భగవాన్", "ఆత్మ", "ఆధ్యాత్మిక"]):
            return "🕉️"
        elif any(k in clean_t for k in ["శాంతి", "ప్రశాంతత", "ప్రేమ"]):
            return "🕊️"
        elif any(k in clean_t for k in ["విజయం", "శుభాకాంక్షలు", "అభినందనలు"]):
            return "🌟"
        else:
            return "🪷"
            
    return stickers_map.get(sticker_choice, "🕉️")

def generate_ai_poster_html(text, theme="ఆధ్యాత్మికం (Golden Divine)", sticker_choice="🪄 AI మ్యాజిక్ (Auto Select)", custom_sticker_file=None):
    """
    Groq AI మరియు స్టిక్కర్ ఇంజిన్ ద్వారా అందమైన గ్రాఫిక్ పోస్టర్ కార్డ్ తయారుచేస్తుంది.
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

    # కస్టమ్ ఇమేజ్ స్టిక్కర్ ఉంటే Base64 లోకి మార్చడం
    custom_img_html = ""
    watermark_html = ""
    if custom_sticker_file is not None:
        try:
            custom_sticker_file.seek(0)
            b64_data = base64.b64encode(custom_sticker_file.read()).decode()
            mime_type = custom_sticker_file.type or "image/png"
            custom_img_html = f"<img src='data:{mime_type};base64,{b64_data}' style='width: 60px; height: 60px; object-fit: contain; border-radius: 50%; border: 2px solid #facc15; box-shadow: 0 0 15px rgba(250,204,21,0.6);' />"
            watermark_html = f"<img src='data:{mime_type};base64,{b64_data}' style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 320px; opacity: 0.08; pointer-events: none;' />"
        except Exception:
            custom_img_html = ""

    selected_symbol = get_sticker_symbol(sticker_choice, text)
    if not custom_img_html:
        top_sticker_display = f"<div class='sticker-badge'>{selected_symbol}</div>"
        watermark_html = f"<div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 260px; opacity: 0.06; pointer-events: none;'>{selected_symbol}</div>"
    else:
        top_sticker_display = custom_img_html

    system_prompt = """You are an expert graphic designer and layout artist for posters.
Extract key elements from the text:
1. "title": Short impactful title (3-6 words).
2. "subtitle": Brief context, organizer, date, or venue.
3. "highlights": 3 to 5 concise key points.
4. "footer_quote": Ending slogan or blessing.

STRICT JSON ONLY:
{
  "title": "...",
  "subtitle": "...",
  "highlights": ["...", "..."],
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
            {"role": "user", "content": f"Extract poster layout details:\n\n{text}"}
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

    bullets_html = "".join([f"<li style='margin-bottom: 12px; font-size: 19px; line-height: 1.6; color: #f1f5f9;'>✨ {hl}</li>" for hl in parsed.get("highlights", [])])

    poster_html = f"""<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="utf-8">
<title>AI Graphic Poster</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Mandali&display=swap');
  * {{ box-sizing: border-box; font-family: 'Mandali', sans-serif; }}
  body {{ margin: 0; padding: 20px; display: flex; justify-content: center; background: #0b0f19; }}
  .poster-card {{
      width: 600px;
      min-height: 750px;
      background: {bg_gradient};
      border: 4px solid #facc15;
      border-radius: 24px;
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
      border-radius: 18px;
      pointer-events: none;
  }}
  .sticker-badge {{
      font-size: 42px;
      display: inline-block;
      filter: drop-shadow(0 0 12px rgba(250, 204, 21, 0.8));
      animation: float 3s ease-in-out infinite;
  }}
  .header {{ text-align: center; margin-bottom: 15px; }}
  .title {{ font-size: 28px; font-weight: bold; color: #facc15; text-shadow: 0 2px 8px rgba(0,0,0,0.5); line-height: 1.3; margin-top: 8px; }}
  .subtitle {{ font-size: 16px; color: #cbd5e1; margin-top: 6px; border-bottom: 1px solid rgba(250,204,21,0.3); padding-bottom: 12px; }}
  .content-box {{
      background: rgba(0, 0, 0, 0.35);
      border-radius: 14px;
      padding: 20px;
      margin: 15px 0;
      border: 1px solid rgba(255, 255, 255, 0.1);
      position: relative;
      z-index: 2;
  }}
  ul {{ list-style-type: none; padding-left: 5px; margin: 0; }}
  .footer {{
      text-align: center;
      background: rgba(250, 204, 21, 0.15);
      border: 1px solid #facc15;
      border-radius: 12px;
      padding: 12px;
      margin-top: 15px;
      position: relative;
      z-index: 2;
  }}
  .footer-quote {{ font-size: 20px; font-weight: bold; color: #fde047; margin: 0; }}
</style>
</head>
<body>
<div class="poster-card">
  <div class="inner-border"></div>
  {watermark_html}
  <div class="header">
    {top_sticker_display}
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
