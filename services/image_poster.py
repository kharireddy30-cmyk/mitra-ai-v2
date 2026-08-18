import base64
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
        if any(k in clean_t for k in ["రక్తం", "రక్తదాన", "సేవ", "ఆసుపత్రి", "బ్లడ్", "శిబిరం"]):
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

def generate_ai_poster_html(
    text, 
    theme="ఆధ్యాత్మికం (Golden Divine)", 
    sticker_choice="🪄 AI మ్యాజిక్ (Auto Select)", 
    content_mode="📜 పూర్తి మ్యాటర్ (Full Exact Text)",
    text_align="ఎడమ వైపు (Left)",
    font_size_choice="మధ్యస్థం (Medium - 18px)",
    custom_sticker_file=None,
    custom_bg_file=None
):
    if not text or not text.strip():
        return ""

    theme_styles = {
        "ఆధ్యాత్మికం (Golden Divine)": "linear-gradient(135deg, #180928 0%, #31134e 50%, #150624 100%)",
        "రక్తదానం / సేవా కార్యక్రమం (Red & White)": "linear-gradient(135deg, #660e0e 0%, #8c1616 50%, #3e0505 100%)",
        "ప్రకృతి / పచ్చదనం (Nature Green)": "linear-gradient(135deg, #04382a 0%, #065f46 50%, #02231b 100%)",
        "రాయల్ బ్లూ (Corporate & Formal)": "linear-gradient(135deg, #091326 0%, #172d5c 50%, #060e1d 100%)"
    }
    bg_style = theme_styles.get(theme, theme_styles["ఆధ్యాత్మికం (Golden Divine)"])

    # యూజర్ ఎంప్టీ బ్యాక్‌గ్రౌండ్ ఇమేజ్ అప్‌లోడ్ చేస్తే:
    if custom_bg_file is not None:
        try:
            custom_bg_file.seek(0)
            bg_b64 = base64.b64encode(custom_bg_file.read()).decode()
            bg_mime = custom_bg_file.type or "image/png"
            bg_style = f"url('data:{bg_mime};base64,{bg_b64}') center/cover no-repeat"
        except Exception:
            pass

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
        top_sticker_display = f"<div class='sticker-badge spark-elem'>{selected_symbol}</div>"
        watermark_html = f"<div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 260px; opacity: 0.06; pointer-events: none;'>{selected_symbol}</div>"
    else:
        top_sticker_display = custom_img_html

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    body_content_html = "".join([f"<p style='margin-bottom: 12px; line-height: 1.7;'>{p}</p>" for p in paragraphs])
    title_text = "సందేశం / ముఖ్యాంశాలు"
    footer_quote = "సర్వేజనా సుఖినోభవంతు"

    poster_html = f"""<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="utf-8">
<title>BRAHMA AI - Poster & Animated GIF</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Mandali&display=swap');
  * {{ box-sizing: border-box; font-family: 'Mandali', sans-serif; }}
  body {{ margin: 0; padding: 15px; display: flex; flex-direction: column; align-items: center; background: #060911; }}
  
  .toolbar {{ width: 100%; max-width: 580px; display: flex; gap: 12px; justify-content: center; margin-bottom: 15px; }}
  .btn-png {{ background: #facc15; color: #000; border: none; padding: 10px 18px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 14px; box-shadow: 0 4px 12px rgba(250, 204, 21, 0.4); }}
  .btn-gif {{ background: #ec4899; color: #fff; border: none; padding: 10px 18px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 14px; box-shadow: 0 4px 12px rgba(236, 72, 153, 0.4); }}
  
  .poster-card {{
      width: 100%; max-width: 580px; min-height: 720px; background: {bg_style}; border: 4px solid #facc15;
      border-radius: 22px; padding: 28px 24px; color: #ffffff; box-shadow: 0 18px 40px rgba(0,0,0,0.7);
      position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between;
  }}
  .inner-border {{ position: absolute; top: 10px; left: 10px; right: 10px; bottom: 10px; border: 1px dashed rgba(250, 204, 21, 0.4); border-radius: 16px; pointer-events: none; }}
  
  @keyframes glowText {{
      0% {{ text-shadow: 0 0 6px rgba(250, 204, 21, 0.4); }}
      50% {{ text-shadow: 0 0 20px rgba(250, 204, 21, 0.9), 0 0 30px #f59e0b; }}
      100% {{ text-shadow: 0 0 6px rgba(250, 204, 21, 0.4); }}
  }}
  @keyframes sparkleBadge {{
      0% {{ transform: scale(1); filter: drop-shadow(0 0 5px #facc15); }}
      50% {{ transform: scale(1.08); filter: drop-shadow(0 0 20px #fbbf24); }}
      100% {{ transform: scale(1); filter: drop-shadow(0 0 5px #facc15); }}
  }}
  
  .spark-title {{ animation: glowText 2s infinite ease-in-out; color: #facc15; font-size: 26px; font-weight: bold; line-height: 1.3; margin-top: 6px; text-shadow: 0 2px 8px rgba(0,0,0,0.8); }}
  .spark-elem {{ animation: sparkleBadge 2s infinite ease-in-out; font-size: 45px; display: inline-block; }}

  .header {{ text-align: center; margin-bottom: 12px; position: relative; z-index: 2; }}
  .content-box {{
      background: rgba(0, 0, 0, 0.55); backdrop-filter: blur(4px); border-radius: 14px; padding: 18px; margin: 10px 0;
      border: 1px solid rgba(255, 255, 255, 0.15); position: relative; z-index: 2;
      font-size: {f_size}; text-align: {t_align}; color: #f8fafc; text-shadow: 0 1px 4px rgba(0,0,0,0.8);
  }}
  .footer {{ text-align: center; background: rgba(0, 0, 0, 0.6); border: 1px solid #facc15; border-radius: 10px; padding: 10px; margin-top: 10px; position: relative; z-index: 2; }}
  .footer-quote {{ font-size: 19px; font-weight: bold; color: #fde047; margin: 0; animation: glowText 2.5s infinite; }}
  
  #gifStatus {{ color: #ec4899; font-size: 14px; font-weight: bold; margin-bottom: 10px; display: none; }}
</style>
</head>
<body>
<div class="toolbar">
  <button class="btn-png" onclick="saveAsImage()">📸 ఇమేజ్ (.PNG)</button>
  <button class="btn-gif" onclick="generateAnimatedGIF()">✨ యానిమేటెడ్ GIF డౌన్‌లోడ్</button>
</div>
<div id="gifStatus">⏳ యానిమేటెడ్ GIF తయారవుతోంది... దయచేసి 3 సెకన్లు ఆగండి...</div>

<div class="poster-card" id="posterCard">
  <div class="inner-border"></div>
  {watermark_html}
  <div class="header">
    {top_sticker_display}
    <div class="spark-title">{title_text}</div>
  </div>
  <div class="content-box">
    {body_content_html}
  </div>
  <div class="footer">
    <p class="footer-quote">🌺 ✨ {footer_quote} ✨ 🌺</p>
  </div>
</div>

<script>
function saveAsImage() {{
    const target = document.getElementById("posterCard");
    html2canvas(target, {{ scale: 2.5, useCORS: true, backgroundColor: null }}).then(canvas => {{
        const link = document.createElement("a");
        link.download = "brahma_poster.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    }});
}}

function generateAnimatedGIF() {{
    const statusDiv = document.getElementById("gifStatus");
    statusDiv.style.display = "block";
    const target = document.getElementById("posterCard");

    let frames = [];
    let count = 0;
    
    function captureFrame() {{
        html2canvas(target, {{ scale: 1.4, useCORS: true }}).then(canvas => {{
            frames.push(canvas.toDataURL("image/png"));
            count++;
            if (count < 6) {{
                setTimeout(captureFrame, 250);
            }} else {{
                gifshot.createGIF({{
                    images: frames,
                    gifWidth: 460,
                    gifHeight: 600,
                    interval: 0.25,
                    numFrames: 6
                }}, function(obj) {{
                    if (!obj.error) {{
                        const animatedImage = obj.image;
                        const a = document.createElement("a");
                        a.href = animatedImage;
                        a.download = "brahma_animated_poster.gif";
                        a.click();
                        statusDiv.style.display = "none";
                    }}
                }});
            }}
        }});
    }}
    captureFrame();
}}
</script>
</body>
</html>"""
    return poster_html
