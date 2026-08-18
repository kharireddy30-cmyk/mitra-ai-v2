import json
import urllib.request
import base64
import streamlit as st

def get_ai_design_styles(text, user_prompt=""):
    """గ్రోక్ API ద్వారా టెక్స్ట్ ఆధారిత ఆటోమేటిక్ డిజైన్ సెట్టింగ్స్"""
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    
    default_styles = {
        "title": "సందేశం / ముఖ్యాంశాలు",
        "highlight": "",
        "textColor": "#5c0606",
        "bgShade": "transparent",
        "fontSize": 18,
        "lineHeight": 1.6,
        "topOffset": 135,
        "auraEnabled": "block"
    }
    
    if not groq_key or not text.strip():
        return default_styles

    system_prompt = """You are a master graphic designer and typography stylist.
Analyze the user's Telugu/Hindi/English content and styling instructions. Return a strictly valid JSON object:
{
  "title": "Short meaningful Telugu title (2-4 words)",
  "highlight": "One most impactful slogan/quote from text to highlight (max 8 words)",
  "textColor": "Choose one hex code: #5c0606 (Maroon), #0f172a (Black), #ffffff (White), #facc15 (Gold), #1e3a8a (Royal Blue)",
  "bgShade": "Choose one: transparent, rgba(255,255,255,0.45), rgba(0,0,0,0.45)",
  "fontSize": 18,
  "lineHeight": 1.6,
  "topOffset": 135,
  "auraEnabled": "block or none"
}
STRICT JSON ONLY. No markdown, no conversational text."""

    user_content = f"CONTENT:\n{text}\n\nUSER COMMAND/WISH:\n{user_prompt if user_prompt else 'Make it divine, elegant, readable, and respectful.'}"

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key.strip()}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Mozilla/5.0"
        }
        req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=12) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            parsed = json.loads(res_data['choices'][0]['message']['content'])
            default_styles.update(parsed)
            return default_styles
    except Exception:
        return default_styles

def render_live_studio_poster(
    text, 
    user_prompt="",
    custom_sticker_file=None,
    custom_bg_file=None
):
    if not text or not text.strip():
        return ""

    # గ్రోక్ AI ద్వారా ఆటోమేటిక్ స్టైల్స్ నిర్ణయం
    ai_cfg = get_ai_design_styles(text, user_prompt)

    has_custom_bg = False
    bg_style = "linear-gradient(135deg, #180928 0%, #31134e 50%, #150624 100%)"
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

    top_sticker_display = custom_img_html if custom_img_html else "<div class='sticker-badge'>🕉️</div>"
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    body_content_html = "".join([f"<p class='content-p'>{p}</p>" for p in paragraphs])

    init_top = ai_cfg.get("topOffset", 135 if has_custom_bg else 10)
    init_color = ai_cfg.get("textColor", "#5c0606")
    init_bg = ai_cfg.get("bgShade", "transparent")
    init_font = ai_cfg.get("fontSize", 18)
    init_line_h = ai_cfg.get("lineHeight", 1.6)
    init_hl = ai_cfg.get("highlight", "")
    init_title = ai_cfg.get("title", "సందేశం / ముఖ్యాంశాలు")
    init_aura = ai_cfg.get("auraEnabled", "block")

    html_code = f"""<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="utf-8">
<title>Live Divine Studio & AI Command</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Mandali&display=swap');
  * {{ box-sizing: border-box; font-family: 'Mandali', sans-serif; }}
  body {{ margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; background: #070a13; color: #fff; }}
  
  .control-panel {{
      width: 100%; max-width: 650px; background: #111827; border: 1px solid #374151;
      border-radius: 14px; padding: 14px 18px; margin-bottom: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.7);
  }}
  .panel-title {{ font-size: 14px; font-weight: bold; color: #facc15; text-align: center; margin-bottom: 12px; }}
  
  .ctrl-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(135px, 1fr)); gap: 10px; }}
  .ctrl-item {{ display: flex; flex-direction: column; font-size: 11px; font-weight: 600; color: #9ca3af; }}
  .ctrl-item input, .ctrl-item select {{ margin-top: 3px; padding: 5px; border-radius: 6px; border: 1px solid #4b5563; background: #1f2937; color: #facc15; font-size: 12px; }}
  
  .highlight-section {{
      margin-top: 10px; padding: 10px; background: #1f2937; border-radius: 8px; border: 1px dashed #f59e0b;
      display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
  }}

  .btn-row {{ display: flex; gap: 12px; justify-content: center; margin-top: 14px; }}
  .btn-png {{ background: #facc15; color: #000; border: none; padding: 9px 20px; border-radius: 7px; font-weight: bold; cursor: pointer; font-size: 13px; }}
  .btn-gif {{ background: #ec4899; color: #fff; border: none; padding: 9px 20px; border-radius: 7px; font-weight: bold; cursor: pointer; font-size: 13px; }}

  .poster-card {{
      width: 100%; max-width: 580px; min-height: 760px; background: {bg_style};
      border: 3px solid #facc15; border-radius: 18px; padding: 20px; color: #ffffff;
      box-shadow: 0 15px 40px rgba(0,0,0,0.9); position: relative; overflow: hidden;
      display: flex; flex-direction: column; justify-content: space-between;
  }}

  @keyframes pulseRays {{
      0% {{ transform: translate(-50%, 0) scale(0.85); opacity: 0.35; filter: drop-shadow(0 0 10px #f59e0b); }}
      50% {{ transform: translate(-50%, 0) scale(1.25); opacity: 0.85; filter: drop-shadow(0 0 35px #fbbf24); }}
      100% {{ transform: translate(-50%, 0) scale(0.85); opacity: 0.35; filter: drop-shadow(0 0 10px #f59e0b); }}
  }}
  @keyframes shimmerText {{
      0% {{ text-shadow: 0 0 4px rgba(250,204,21,0.3); }}
      50% {{ text-shadow: 0 0 18px rgba(250,204,21,0.95), 0 0 30px #f59e0b; }}
      100% {{ text-shadow: 0 0 4px rgba(250,204,21,0.3); }}
  }}

  .divine-aura-bottom {{
      position: absolute; bottom: 35px; left: 50%; width: 140px; height: 140px;
      border-radius: 50%; background: radial-gradient(circle, rgba(251,191,36,0.8) 0%, rgba(245,158,11,0.4) 45%, transparent 70%);
      pointer-events: none; z-index: 1; animation: pulseRays 2.2s infinite ease-in-out;
  }}
  .sparkle-decor {{ position: absolute; font-size: 20px; color: #fde047; pointer-events: none; }}

  .header-box {{ text-align: center; margin-bottom: 8px; z-index: 2; {'display: none;' if has_custom_bg else ''} }}
  .header-title {{ font-size: 24px; font-weight: bold; color: #facc15; animation: shimmerText 2.5s infinite; }}
  .sticker-badge {{ font-size: 38px; display: inline-block; filter: drop-shadow(0 0 8px #facc15); }}
  
  .content-canvas {{
      width: 88%; margin: 0 auto; padding: 12px;
      transition: all 0.1s ease-in-out; position: relative; z-index: 2;
      font-size: {init_font}px; line-height: {init_line_h}; color: {init_color};
      background: {init_bg}; border-radius: 10px; margin-top: {init_top}px;
      text-shadow: 0 1px 2px rgba(255,255,255,0.7);
  }}
  .content-p {{ margin-bottom: 10px; }}

  .special-highlight-card {{
      display: {'block' if init_hl else 'none'}; margin-top: 10px; padding: 8px 12px; text-align: center;
      background: linear-gradient(90deg, rgba(250,204,21,0.2), rgba(250,204,21,0.6), rgba(250,204,21,0.2));
      border: 1px solid #facc15; border-radius: 8px; font-weight: bold; font-size: 19px; color: #7f1d1d;
      animation: shimmerText 2s infinite;
  }}
  
  .footer-box {{ text-align: center; padding: 6px; z-index: 2; {'display: none;' if has_custom_bg else ''} }}
  .footer-quote {{ font-size: 16px; font-weight: bold; color: #fde047; margin: 0; }}

  #gifStatus {{ color: #ec4899; font-size: 13px; font-weight: bold; margin-top: 8px; display: none; text-align: center; }}
</style>
</head>
<body>

<div class="control-panel">
  <div class="panel-title">🎛️ లైవ్ ట్యూనింగ్ ప్యానెల్ (AI Styles Applied)</div>
  
  <div class="ctrl-grid">
    <div class="ctrl-item">
      <label>↕️ ఎత్తు (Top Offset):</label>
      <input type="range" id="rngTop" min="0" max="350" value="{init_top}" oninput="updateLayout()">
    </div>
    <div class="ctrl-item">
      <label>↔️ బాక్స్ వెడల్పు (%):</label>
      <input type="range" id="rngWidth" min="60" max="100" value="88" oninput="updateLayout()">
    </div>
    <div class="ctrl-item">
      <label>🔤 అక్షరాల సైజు (px):</label>
      <input type="range" id="rngFontSize" min="14" max="28" value="{init_font}" oninput="updateLayout()">
    </div>
    <div class="ctrl-item">
      <label>📏 వాక్యాల దూరం:</label>
      <input type="range" id="rngLineHeight" min="1.2" max="2.4" step="0.1" value="{init_line_h}" oninput="updateLayout()">
    </div>
    <div class="ctrl-item">
      <label>🎨 టెక్స్ట్ రంగు:</label>
      <select id="selColor" onchange="updateLayout()">
        <option value="{init_color}">AI ఎంపిక ({init_color})</option>
        <option value="#5c0606">డార్క్ మెరూన్ (Maroon)</option>
        <option value="#0f172a">రాయల్ బ్లాక్ (Black)</option>
        <option value="#ffffff">ప్యూర్ వైట్ (White)</option>
        <option value="#facc15">గోల్డెన్ ఎల్లో (Gold)</option>
      </select>
    </div>
    <div class="ctrl-item">
      <label>🌫️ బ్యాక్‌గ్రౌండ్ షేడ్:</label>
      <select id="selBgShade" onchange="updateLayout()">
        <option value="{init_bg}">AI షేడ్</option>
        <option value="transparent">పూర్తి పారదర్శకం (Clear)</option>
        <option value="rgba(255, 255, 255, 0.45)">లైట్ వైట్ గ్లాస్ (White Glass)</option>
        <option value="rgba(0, 0, 0, 0.45)">సాఫ్ట్ డార్క్ గ్లాస్ (Dark Glass)</option>
      </select>
    </div>
    <div class="ctrl-item">
      <label>🌟 దివ్య కిరణాల ఆరా:</label>
      <select id="selAura" onchange="toggleAura()">
        <option value="{init_aura}">{'✨ ఆన్ (Shining Aura)' if init_aura == 'block' else 'ఆఫ్ (Off)'}</option>
        <option value="block">ఆన్ (On)</option>
        <option value="none">ఆఫ్ (Off)</option>
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

  <div class="highlight-section">
    <div class="ctrl-item">
      <label>🚩 AI స్పెషల్ కొటేషన్ హైలైట్:</label>
      <input type="text" id="txtHighlight" value="{init_hl}" placeholder="AI స్వయంగా లైన్ ఎంచుకుంటుంది..." oninput="updateHighlight()">
    </div>
    <div class="ctrl-item">
      <label>🎨 హైలైట్ రంగు:</label>
      <select id="selHlColor" onchange="updateHighlight()">
        <option value="#7f1d1d">డీప్ రెడ్ (Deep Red)</option>
        <option value="#1e3a8a">రాయల్ బ్లూ (Royal Blue)</option>
        <option value="#065f46">ఎమరాల్డ్ గ్రీన్ (Green)</option>
        <option value="#facc15">గోల్డ్ (Gold)</option>
      </select>
    </div>
  </div>

  <div class="btn-row">
    <button class="btn-png" onclick="saveAsImage()">📸 ఇమేజ్ (.PNG)</button>
    <button class="btn-gif" onclick="generateAnimatedGIF()">✨ యానిమేటెడ్ GIF డౌన్‌లోడ్</button>
  </div>
  <div id="gifStatus">⏳ GIF ఫ్రేమ్స్ & ఆరా ఎఫెక్ట్స్ సిద్ధమవుతున్నాయి... 3 సెకన్లు వేచి ఉండండి...</div>
</div>

<div class="poster-card" id="posterCard">
  <div class="sparkle-decor" style="top: 25px; left: 30px;">✨</div>
  <div class="sparkle-decor" style="top: 35px; right: 35px;">🌟</div>
  <div class="divine-aura-bottom" id="divineAura" style="display: {init_aura};"></div>

  <div class="header-box" id="headerBox">
    {top_sticker_display}
    <div class="header-title">{init_title}</div>
  </div>

  <div class="content-canvas" id="contentBox">
    {body_content_html}
    <div class="special-highlight-card" id="specialHighlight">{'✨ ' + init_hl + ' ✨' if init_hl else ''}</div>
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
    const lineHVal = document.getElementById("rngLineHeight").value;
    const colorVal = document.getElementById("selColor").value;
    const bgShadeVal = document.getElementById("selBgShade").value;
    
    const contentBox = document.getElementById("contentBox");
    contentBox.style.marginTop = topVal + "px";
    contentBox.style.width = widthVal + "%";
    contentBox.style.fontSize = fontVal + "px";
    contentBox.style.lineHeight = lineHVal;
    contentBox.style.color = colorVal;
    contentBox.style.background = bgShadeVal;
    
    if (colorVal === "#ffffff" || colorVal === "#facc15") {{
        contentBox.style.textShadow = "0 2px 6px rgba(0,0,0,0.95)";
    }} else {{
        contentBox.style.textShadow = "0 1px 2px rgba(255,255,255,0.7)";
    }}
}}

function updateHighlight() {{
    const hlText = document.getElementById("txtHighlight").value.trim();
    const hlCard = document.getElementById("specialHighlight");
    const hlColor = document.getElementById("selHlColor").value;

    if (hlText.length > 0) {{
        hlCard.innerText = "✨ " + hlText + " ✨";
        hlCard.style.color = hlColor;
        hlCard.style.display = "block";
    }} else {{
        hlCard.style.display = "none";
    }}
}}

function toggleHeader() {{
    const val = document.getElementById("selHeader").value;
    document.getElementById("headerBox").style.display = val;
    document.getElementById("footerBox").style.display = val;
}}

function toggleAura() {{
    const val = document.getElementById("selAura").value;
    document.getElementById("divineAura").style.display = val;
}}

function saveAsImage() {{
    const target = document.getElementById("posterCard");
    html2canvas(target, {{ scale: 2.5, useCORS: true, backgroundColor: null }}).then(canvas => {{
        const link = document.createElement("a");
        link.download = "brahma_divine_poster.png";
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
                        a.download = "brahma_divine_aura.gif";
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
