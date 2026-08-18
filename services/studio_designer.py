import base64

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
        else:
            return "🪷"
    return stickers_map.get(sticker_choice, "🕉️")

def render_live_studio_poster(
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

    has_custom_bg = False
    if custom_bg_file is not None:
        try:
            custom_bg_file.seek(0)
            bg_b64 = base64.b64encode(custom_bg_file.read()).decode()
            bg_mime = custom_bg_file.type or "image/png"
            bg_style = f"url('data:{bg_mime};base64,{bg_b64}') center/contain no-repeat #000000"
            has_custom_bg = True
        except Exception:
            pass

    custom_img_html = ""
    if custom_sticker_file is not None:
        try:
            custom_sticker_file.seek(0)
            b64_data = base64.b64encode(custom_sticker_file.read()).decode()
            mime_type = custom_sticker_file.type or "image/png"
            custom_img_html = f"<img src='data:{mime_type};base64,{b64_data}' style='width: 55px; height: 55px; object-fit: contain; border-radius: 50%; border: 2px solid #facc15;' />"
        except Exception:
            pass

    selected_symbol = get_sticker_symbol(sticker_choice, text)
    top_sticker_display = custom_img_html if custom_img_html else f"<div class='sticker-badge'>{selected_symbol}</div>"

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    body_content_html = "".join([f"<p class='content-p'>{p}</p>" for p in paragraphs])

    html_code = f"""<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="utf-8">
<title>Live Poster & GIF Studio</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Mandali&display=swap');
  * {{ box-sizing: border-box; font-family: 'Mandali', sans-serif; }}
  body {{ margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; background: #0b0f19; color: #fff; }}
  
  /* లైవ్ కంట్రోల్స్ టూల్‌బార్ */
  .control-panel {{
      width: 100%; max-width: 620px; background: #1e293b; border: 1px solid #334155;
      border-radius: 12px; padding: 12px 16px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
  }}
  .ctrl-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; align-items: center; }}
  .ctrl-item {{ display: flex; flex-direction: column; font-size: 12px; font-weight: 600; color: #cbd5e1; }}
  .ctrl-item input, .ctrl-item select {{ margin-top: 4px; padding: 4px 6px; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #facc15; }}
  
  .btn-row {{ display: flex; gap: 10px; justify-content: center; margin-top: 12px; }}
  .btn-png {{ background: #facc15; color: #000; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px; }}
  .btn-gif {{ background: #ec4899; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px; }}

  /* పోస్టర్ కాన్వాస్ */
  .poster-card {{
      width: 100%; max-width: 580px; min-height: 750px; background: {bg_style};
      border: 3px solid #facc15; border-radius: 18px; padding: 20px; color: #ffffff;
      box-shadow: 0 15px 35px rgba(0,0,0,0.8); position: relative; overflow: hidden;
      display: flex; flex-direction: column; justify-content: space-between;
  }}
  
  .header-box {{ text-align: center; margin-bottom: 8px; {'display: none;' if has_custom_bg else ''} }}
  .header-title {{ font-size: 24px; font-weight: bold; color: #facc15; text-shadow: 0 2px 6px rgba(0,0,0,0.8); }}
  .sticker-badge {{ font-size: 40px; display: inline-block; filter: drop-shadow(0 0 8px #facc15); }}
  
  /* పారదర్శక టెక్స్ట్ ఏరియా - డార్క్ బాక్స్ లేకుండా */
  .content-canvas {{
      width: 90%; margin: 0 auto; padding: 12px;
      transition: all 0.1s ease-in-out;
      font-size: 19px; line-height: 1.65;
      color: #111827; /* డార్క్ షేడ్ లేదా యూజర్ ఎంచుకున్న కలర్ */
      text-shadow: 0 1px 2px rgba(255,255,255,0.6);
  }}
  .content-p {{ margin-bottom: 10px; }}
  
  .footer-box {{ text-align: center; padding: 8px; {'display: none;' if has_custom_bg else ''} }}
  .footer-quote {{ font-size: 17px; font-weight: bold; color: #fde047; margin: 0; }}

  #gifStatus {{ color: #ec4899; font-size: 13px; font-weight: bold; margin-top: 6px; display: none; text-align: center; }}
</style>
</head>
<body>

<div class="control-panel">
  <div style="font-size:13px; font-weight:bold; color:#38bdf8; margin-bottom:8px; text-align:center;">🎛️ లైవ్ ట్యూనింగ్ కంట్రోలర్ (Live Canvas Controller)</div>
  <div class="ctrl-grid">
    <div class="ctrl-item">
      <label>↕️ ఎత్తు (Top Margin):</label>
      <input type="range" id="rngTop" min="0" max="350" value="{'140' if has_custom_bg else '10'}" oninput="updateLayout()">
    </div>
    <div class="ctrl-item">
      <label>↔️ బాక్స్ వెడల్పు (%):</label>
      <input type="range" id="rngWidth" min="60" max="100" value="88" oninput="updateLayout()">
    </div>
    <div class="ctrl-item">
      <label>🔤 అక్షరాల సైజు (px):</label>
      <input type="range" id="rngFontSize" min="14" max="28" value="18" oninput="updateLayout()">
    </div>
    <div class="ctrl-item">
      <label>🎨 టెక్స్ట్ రంగు:</label>
      <select id="selColor" onchange="updateLayout()">
        <option value="#5c0606">డార్క్ మెరూన్ (Maroon)</option>
        <option value="#0f172a">రాయల్ బ్లాక్ (Black)</option>
        <option value="#ffffff">ప్యూర్ వైట్ (White)</option>
        <option value="#facc15">గోల్డెన్ ఎల్లో (Gold)</option>
      </select>
    </div>
    <div class="ctrl-item">
      <label>🌫️ బ్యాక్‌గ్రౌండ్ షేడ్:</label>
      <select id="selBgShade" onchange="updateLayout()">
        <option value="transparent">పూర్తి పారదర్శకం (Clear)</option>
        <option value="rgba(255, 255, 255, 0.4)">లైట్ వైట్ గ్లాస్ (White Glass)</option>
        <option value="rgba(0, 0, 0, 0.4)">సాఫ్ట్ డార్క్ గ్లాస్ (Dark Glass)</option>
      </select>
    </div>
    <div class="ctrl-item">
      <label>👁️ హెడర్ / టైటిల్:</label>
      <select id="selHeader" onchange="toggleHeader()">
        <option value="{'none' if has_custom_bg else 'block'}">{'దాచు (Hide)' if has_custom_bg else 'చూపించు (Show)'}</option>
        <option value="{'block' if has_custom_bg else 'none'}">{'చూపించు (Show)' if has_custom_bg else 'దాచు (Hide)'}</option>
      </select>
    </div>
  </div>

  <div class="btn-row">
    <button class="btn-png" onclick="saveAsImage()">📸 ఇమేజ్ (.PNG)</button>
    <button class="btn-gif" onclick="generateAnimatedGIF()">✨ యానిమేటెడ్ GIF డౌన్‌లోడ్</button>
  </div>
  <div id="gifStatus">⏳ GIF ఫ్రేమ్స్ రికార్డ్ అవుతున్నాయి... 3 సెకన్లు ఆగండి...</div>
</div>

<div class="poster-card" id="posterCard">
  <div class="header-box" id="headerBox">
    {top_sticker_display}
    <div class="header-title">సందేశం / ముఖ్యాంశాలు</div>
  </div>

  <div class="content-canvas" id="contentBox">
    {body_content_html}
  </div>

  <div class="footer-box" id="footerBox">
    <p class="footer-quote">🌺 ✨ సర్వేజనా సుఖినోభవంతు ✨ 🌺</p>
  </div>
</div>

<script>
function updateLayout() {{
    const topVal = document.getElementById("rngTop").value;
    const widthVal = document.getElementById("rngWidth").value;
    const fontVal = document.getElementById("rngFontSize").value;
    const colorVal = document.getElementById("selColor").value;
    const bgShadeVal = document.getElementById("selBgShade").value;
    
    const contentBox = document.getElementById("contentBox");
    contentBox.style.marginTop = topVal + "px";
    contentBox.style.width = widthVal + "%";
    contentBox.style.fontSize = fontVal + "px";
    contentBox.style.color = colorVal;
    contentBox.style.background = bgShadeVal;
    contentBox.style.borderRadius = "10px";
    
    if (colorVal === "#ffffff" || colorVal === "#facc15") {{
        contentBox.style.textShadow = "0 2px 5px rgba(0,0,0,0.9)";
    }} else {{
        contentBox.style.textShadow = "0 1px 2px rgba(255,255,255,0.7)";
    }}
}}

function toggleHeader() {{
    const val = document.getElementById("selHeader").value;
    document.getElementById("headerBox").style.display = val;
    document.getElementById("footerBox").style.display = val;
}}

// ప్రారంభ లోడ్
updateLayout();

function saveAsImage() {{
    const target = document.getElementById("posterCard");
    html2canvas(target, {{ scale: 2.5, useCORS: true, backgroundColor: null }}).then(canvas => {{
        const link = document.createElement("a");
        link.download = "brahma_custom_poster.png";
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
                        const a = document.createElement("a");
                        a.href = obj.image;
                        a.download = "brahma_studio_animated.gif";
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
    return html_code
