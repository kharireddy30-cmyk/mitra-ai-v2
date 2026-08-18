import os
import json
import base64
import urllib.request
import streamlit as st

def get_sticker_symbol(sticker_choice, text=""):
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
        if any(k in clean_t for k in ["రక్తం", "రక్తదాన", "సేవ", "ఆసుపత్రి", "బ్లడ్", "శిబిరం", "रक्तदान"]):
            return "🩸"
        elif any(k in clean_t for k in ["ఓం", "శాంతి", "ధ్యానం", "భగవాన్", "ఆత్మ", "ఆధ్యాత్మిక", "ॐ"]):
            return "🕉️"
        elif any(k in clean_t for k in ["శాంతి", "ప్రశాంతత", "ప్రేమ", "peace"]):
            return "🕊️"
        elif any(k in clean_t for k in ["విజయం", "శుభాకాంక్షలు", "అభినందనలు"]):
            return "🌟"
        else:
            return "🪷"
            
    return stickers_map.get(sticker_choice, "🕉️")

def generate_ai_poster_html(
    text, 
    theme="ఆధ్యాత్మికం (Golden Divine)", 
    sticker_choice="🪄 AI మ్యాజిక్ (Auto Select)", 
    content_mode="📜 పూర్తి మ్యాటర్ (Full Exact Text)",
    text_align="ఎడమ వైపు (Left)",
    font_size_choice="మధ్యస్థం (Medium - 18px)",
    custom_sticker_file=None
):
    if not text or not text.strip():
        return ""

    groq_key = st.secrets.get("GROQ_API_KEY", "")
    
    theme_styles = {
        "ఆధ్యాత్మికం (Golden Divine)": "linear-gradient(135deg, #180928 0%, #31134e 50%, #150624 100%)",
        "రక్తదానం / సేవా కార్యక్రమం (Red & White)": "linear-gradient(135deg, #660e0e 0%, #8c1616 50%, #3e0505 100%)",
        "ప్రకృతి / పచ్చదనం (Nature Green)": "linear-gradient(135deg, #04382a 0%, #065f46 50%, #02231b 100%)",
        "రాయల్ బ్లూ (Corporate & Formal)": "linear-gradient(135deg, #091326 0%, #172d5c 50%, #060e1d 100%)"
    }
    bg_gradient = theme_styles.get(theme, theme_styles["ఆధ్యాత్మికం (Golden Divine)"])

    font_size_map = {
        "చిన్నది (Small - 15px)": "15px",
        "మధ్యస్థం (Medium - 18px)": "18px",
        "పెద్దది (Large - 22px)": "22px",
        "చాలా పెద్దది (X-Large - 26px)": "26px"
    }
    f_size = font_size_map.get(font_size_choice, "18px")

    align_map = {
        "ఎడమ వైపు (Left)": "left",
        "మధ్యలో (Center)": "center",
        "సమానంగా (Justify)": "justify"
    }
    t_align = align_map.get(text_align, "left")

    custom_img_html = ""
    watermark_html = ""
    if custom_sticker_file is not None:
        try:
            custom_sticker_file.seek(0)
            b64_data = base64.b64encode(custom_sticker_file.read()).decode()
            mime_type = custom_sticker_file.type or "image/png"
            custom_img_html = f"<img src='data:{mime_type};base64,{b64_data}' style='width: 65px; height: 65px; object-fit: contain; border-radius: 50%; border: 2px solid #facc15; box-shadow: 0 0 15px rgba(250,204,21,0.6);' />"
            watermark_html = f"<img src='data:{mime_type};base64,{b64_data}' style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 320px; opacity: 0.08; pointer-events: none;' />"
        except Exception:
            custom_img_html = ""

    selected_symbol = get_sticker_symbol(sticker_choice, text)
    if not custom_img_html:
        top_sticker_display = f"<div class='sticker-badge'>{selected_symbol}</div>"
        watermark_html = f"<div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 260px; opacity: 0.06; pointer-events: none;'>{selected_symbol}</div>"
    else:
        top_sticker_display = custom_img_html

    # పూర్తి మ్యాటర్ vs AI సారాంశం
    if "పూర్తి మ్యాటర్" in content_mode:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        body_content_html = "".join([f"<p style='margin-bottom: 12px; line-height: 1.7;'>{p}</p>" for p in paragraphs])
        title_text = "సందేశం / ముఖ్యాంశాలు"
        footer_quote = "సర్వేజనా సుఖినోభవంతు"
    else:
        system_prompt = """Extract poster layout:
1. "title": Short title (3-6 words).
2. "highlights": 3 to 6 key bullet points.
3. "footer_quote": Ending blessing.
STRICT JSON ONLY: {"title": "...", "highlights": ["...", "..."], "footer_quote": "..."}"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key.strip()}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": text}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                parsed = json.loads(res_data['choices'][0]['message']['content'])
                title_text = parsed.get("title", "ముఖ్యాంశాలు")
                footer_quote = parsed.get("footer_quote", "సర్వేజనా సుఖినోభవంతు")
                body_content_html = "".join([f"<li style='margin-bottom: 10px; line-height: 1.6;'>✨ {hl}</li>" for hl in parsed.get("highlights", [])])
                body_content_html = f"<ul>{body_content_html}</ul>"
        except Exception:
            body_content_html = f"<p>{text}</p>"
            title_text = "ముఖ్యాంశాలు"
            footer_quote = "సర్వేజనా సుఖినోభవంతు"

    poster_html = f"""<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="utf-8">
<title>BRAHMA AI - Smart Poster</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Mandali&display=swap');
  * {{ box-sizing: border-box; font-family: 'Mandali', sans-serif; }}
  body {{ margin: 0; padding: 15px; display: flex; flex-direction: column; align-items: center; background: #060911; }}
  .toolbar {{ width: 100%; max-width: 580px; display: flex; justify-content: center; margin-bottom: 15px; }}
  .btn {{ background: #facc15; color: #000; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px; box-shadow: 0 4px 12px rgba(250, 204, 21, 0.4); }}
  .poster-card {{
      width: 100%; max-width: 580px; min-height: 720px; background: {bg_gradient}; border: 4px solid #facc15;
      border-radius: 22px; padding: 28px 24px; color: #ffffff; box-shadow: 0 18px 40px rgba(0,0,0,0.7);
      position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between;
  }}
  .inner-border {{ position: absolute; top: 10px; left: 10px; right: 10px; bottom: 10px; border: 1px dashed rgba(250, 204, 21, 0.4); border-radius: 16px; pointer-events: none; }}
  .sticker-badge {{ font-size: 45px; display: inline-block; filter: drop-shadow(0 0 12px rgba(250, 204, 21, 0.8)); }}
  .header {{ text-align: center; margin-bottom: 12px; position: relative; z-index: 2; }}
  .title {{ font-size: 26px; font-weight: bold; color: #facc15; text-shadow: 0 2px 8px rgba(0,0,0,0.6); line-height: 1.3; margin-top: 6px; }}
  .content-box {{
      background: rgba(0, 0, 0, 0.4); border-radius: 14px; padding: 18px; margin: 10px 0;
      border: 1px solid rgba(255, 255, 255, 0.12); position: relative; z-index: 2;
      font-size: {f_size}; text-align: {t_align}; color: #f8fafc;
  }}
  ul {{ list-style-type: none; padding-left: 2px; margin: 0; }}
  .footer {{ text-align: center; background: rgba(250, 204, 21, 0.15); border: 1px solid #facc15; border-radius: 10px; padding: 10px; margin-top: 10px; position: relative; z-index: 2; }}
  .footer-quote {{ font-size: 19px; font-weight: bold; color: #fde047; margin: 0; }}
</style>
</head>
<body>
<div class="toolbar">
  <button class="btn" onclick="saveAsImage()">📸 ఇమేజ్ డౌన్‌లోడ్ (.PNG)</button>
</div>
<div class="poster-card" id="posterCard">
  <div class="inner-border"></div>
  {watermark_html}
  <div class="header">
    {top_sticker_display}
    <div class="title">{title_text}</div>
  </div>
  <div class="content-box">
    {body_content_html}
  </div>
  <div class="footer">
    <p class="footer-quote">🌺 {footer_quote} 🌺</p>
  </div>
</div>
<script>
function saveAsImage() {{
    const target = document.getElementById("posterCard");
    html2canvas(target, {{ scale: 2.5, useCORS: true, backgroundColor: null }}).then(canvas => {{
        const link = document.createElement("a");
        link.download = "brahma_ai_poster.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    }});
}}
</script>
</body>
</html>"""
    return poster_html
