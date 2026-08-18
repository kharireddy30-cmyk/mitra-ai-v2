import base64
import json
import urllib.request
import streamlit as st

def get_sticker_symbol(sticker_choice, text=""):
    """
    ఎంచుకున్న స్టిక్కర్ లేదా AI మ్యాజిక్ ఆధారంగా సరైన బ్యాడ్జ్ గుర్తును ఎంపిక చేస్తుంది.
    """
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
        elif any(k in clean_t for k in ["ఓం", "శాంతి", "ధ్యానం", "భగవాన్", "ఆత్మ", "ఆధ్యాత్మిక", "శివ"]):
            return "🕉️"
        elif any(k in clean_t for k in ["శాంతి", "ప్రశాంతత", "ప్రేమ"]):
            return "🕊️"
        elif any(k in clean_t for k in ["విజయం", "శుభాకాంక్షలు", "అభినందనలు", "స్టార్"]):
            return "🌟"
        else:
            return "🪷"
            
    return stickers_map.get(sticker_choice, "🕉️")


def get_groq_ai_design_suggestions(text, user_prompt=""):
    """
    గ్రోక్ AI ద్వారా కంటెంట్‌ను విశ్లేషించి సరైన రంగులు, హైలైట్ లైన్ మరియు శీర్షికను సిఫార్సు చేస్తుంది.
    """
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    
    default_config = {
        "title": "సందేశం / ముఖ్యాంశాలు",
        "highlight": "",
        "textColor": "#5c0606",
        "bgShade": "transparent",
        "fontSize": 18,
        "lineHeight": 1.65,
        "topOffset": 135,
        "auraEnabled": "block"
    }
    
    if not groq_key or not text or not text.strip():
        return default_config

    system_prompt = """You are an expert Indian graphic designer and typography stylist.
Analyze the user's Telugu/English script and optional styling instructions.
Return a STRICTLY VALID JSON object with these keys:
{
  "title": "Short meaningful Telugu heading (2-4 words)",
  "highlight": "The single most impactful sentence or slogan from the text to highlight (max 8 words)",
  "textColor": "One hex code: #5c0606 (Maroon), #0f172a (Black), #ffffff (White), #facc15 (Gold), #1e3a8a (Navy Blue)",
  "bgShade": "One CSS value: transparent, rgba(255,255,255,0.45), rgba(0,0,0,0.45)",
  "fontSize": 18,
  "lineHeight": 1.65,
  "topOffset": 135,
  "auraEnabled": "block or none"
}
STRICT JSON ONLY. No markdown wrapper, no conversational explanation."""

    user_content = f"CONTENT:\n{text}\n\nUSER WISH/STYLE:\n{user_prompt if user_prompt else 'Divine, respectful, highly legible and aesthetically balanced.'}"

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
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            parsed = json.loads(res_data['choices'][0]['message']['content'])
            default_config.update(parsed)
            return default_config
    except Exception:
        return default_config


def render_live_studio_poster(
    text, 
    theme="ఆధ్యాత్మికం (Golden Divine)", 
    sticker_choice="🪄 AI మ్యాజిక్ (Auto Select)", 
    content_mode="📜 పూర్తి మ్యాటర్ (Full Exact Text)",
    text_align="ఎడమ వైపు (Left)",
    font_size_choice="మధ్యస్థం (Medium - 18px)",
    custom_sticker_file=None,
    custom_bg_file=None,
    user_prompt=""
):
    """
    పూర్తి స్థాయి పోస్టర్ కాన్వాస్ మరియు దాని క్రింద లైవ్ ట్యూనింగ్ కంట్రోలర్ టూల్స్ రెండరింగ్.
    """
    if not text or not text.strip():
        return ""

    # గ్రోక్ AI రికమండేషన్స్
    ai_cfg = get_groq_ai_design_suggestions(text, user_prompt)

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

    font_size_map = {
        "చిన్నది (Small - 15px)": 15,
        "మధ్యస్థం (Medium - 18px)": 18,
        "పెద్దది (Large - 22px)": 22,
        "చాలా పెద్దది (X-Large - 26px)": 26
    }
    selected_font_size = font_size_map.get(font_size_choice, ai_cfg.get("fontSize", 18))

    align_map = {
        "ఎడమ వైపు (Left)": "left",
        "మధ్యలో (Center)": "center",
        "సమానంగా (Justify)": "justify"
    }
    selected_align = align_map.get(text_align, "left")

    custom_img_html = ""
    if custom_sticker_file is not None:
        try:
            custom_sticker_file.seek(0)
            b64_data = base64.b64encode(custom_sticker_file.read()).decode()
            mime_type = custom_sticker_file.type or "image/png"
            custom_img_html = f"<img src='data:{mime_type};base64,{b64_data}' style='width: 58px; height: 58px; object-fit: contain; border-radius: 50%; border: 2px solid #facc15; box-shadow: 0 0 14px rgba(250,204,21,0.6);' />"
        except Exception:
            pass

    selected_symbol = get_sticker_symbol(sticker_choice, text)
    top_sticker_display = custom_img_html if custom_img_html else f"<div class='sticker-badge'>{selected_symbol}</div>"

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    body_content_html = "".join([f"<p class='content-p'>{p}</p>" for p in paragraphs])

    init_top = 135 if has_custom_bg else 10
    init_color = "#5c0606" if has_custom_bg else "#ffffff"
    init_bg = ai_cfg.get("bgShade", "transparent")
    init_line_h = ai_cfg.get("lineHeight", 1.65)
    init_hl = ai_cfg.get("highlight", "")
    init_title = ai_cfg.get("title", "సందేశం / ముఖ్యాంశాలు")
    init_aura = "block"

    html_code = f"""<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="utf-8">
<title>BRAHMA AI Studio Pro</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Mandali&family=Suranna&family=Ramabhadra&display=swap');
  * {{ box-sizing: border-box; font-family: 'Mandali', sans-serif; }}
  body {{ margin: 0; padding: 14px; display: flex; flex-direction: column; align-items: center; background: #070a13; color: #fff; }}
  
  /* ========================================= */
  /* 1. పోస్టర్ కాన్వాస్ కార్డ్ (పైన స్పష్టంగా) */
  /* ========================================= */
  .poster-card {{
      width: 100%; max-width: 580px; min-height: 770px; background: {bg_style};
      border: 3.5px solid #facc15; border-radius: 20px; padding: 22px; color: #ffffff;
      box-shadow: 0 18px 45px rgba(0,0,0,0.95); position: relative; overflow: hidden;
      display: flex; flex-direction: column; justify-content: space-between;
      margin-bottom: 22px;
  }}

  /* యానిమేషన్లు (Divine Rays, Shimmer, Sparkles) */
  @keyframes pulseRays {{
      0% {{ transform: translate(-50%, 0) scale(0.85); opacity: 0.35; filter: drop-shadow(0 0 10px #f59e0b); }}
      50% {{ transform: translate(-50%, 0) scale(1.25); opacity: 0.90; filter: drop-shadow(0 0 35px #fbbf24); }}
      100% {{ transform: translate(-50%, 0) scale(0.85); opacity: 0.35; filter: drop-shadow(0 0 10px #f59e0b); }}
  }}
  @keyframes shimmerText {{
      0% {{ text-shadow: 0 0 4px rgba(250,204,21,0.3); }}
      50% {{ text-shadow: 0 0 18px rgba(250,204,21,0.95), 0 0 32px #f59e0b; }}
      100% {{ text-shadow: 0 0 4px rgba(250,204,21,0.3); }}
  }}
  @keyframes floatSparkles {{
      0% {{ opacity: 0.2; transform: translateY(0px) rotate(0deg); }}
      50% {{ opacity: 1; transform: translateY(-7px) rotate(180deg); }}
      100% {{ opacity: 0.2; transform: translateY(0px) rotate(360deg); }}
  }}

  .divine-aura-bottom {{
      position: absolute; bottom: 32px; left: 50%; width: 145px; height: 145px;
      border-radius: 50%; background: radial-gradient(circle, rgba(251,191,36,0.85) 0%, rgba(245,158,11,0.45) 45%, transparent 70%);
      pointer-events: none; z-index: 1; animation: pulseRays 2.2s infinite ease-in-out;
  }}
  .sparkle-decor {{ position: absolute; font-size: 22px; color: #fde047; pointer-events: none; animation: floatSparkles 2.8s infinite ease-in-out; }}

  .header-box {{ text-align: center; margin-bottom: 8px; z-index: 2; {'display: none;' if has_custom_bg else ''} }}
  .header-title {{ font-size: 25px; font-weight: bold; color: #facc15; animation: shimmerText 2.5s infinite; }}
  .sticker-badge {{ font-size: 40px; display: inline-block; filter: drop-shadow(0 0 10px #facc15); }}
  
  .content-canvas {{
      width: 88%; margin: 0 auto; padding: 14px;
      transition: all 0.1s ease-in-out; position: relative; z-index: 2;
      font-size: {selected_font_size}px; line-height: {init_line_h}; color: {init_color};
      text-align: {selected_align};
      margin-top: {init_top}px;
      text-shadow: 0 1px 2px rgba(255,255,255,0.7);
  }}
  .content-p {{ margin-bottom: 11px; }}

  .special-highlight-card {{
      display: {'block' if init_hl else 'none'}; margin-top: 12px; padding: 9px 14px; text-align: center;
      background: linear-gradient(90deg, rgba(250,204,21,0.2), rgba(250,204,21,0.65), rgba(250,204,21,0.2));
      border: 1.5px solid #facc15; border-radius: 9px; font-weight: bold; font-size: 20px; color: #7f1d1d;
      animation: shimmerText 2s infinite;
  }}
  
  .footer-box {{ text-align: center; padding: 6px; z-index: 2; {'display: none;' if has_custom_bg else ''} }}
  .footer-quote {{ font-size: 17px; font-weight: bold; color: #fde047; margin: 0; }}

  /* ========================================= */
  /* 2. పోస్టర్ కింద ఉండే ప్రొఫెషనల్ కంట్రోలర్ */
  /* ========================================= */
  .control-panel {{
      width: 100%; max-width: 660px; background: #111827; border: 1px solid #374151;
      border-radius: 16px; padding: 18px 22px; box-shadow: 0 10px 30px rgba(0,0,0,0.75);
  }}
  .panel-title {{ font-size: 15px; font-weight: bold; color: #facc15; text-align: center; margin-bottom: 15px; letter-spacing: 0.5px; }}
  
  .ctrl-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
  .ctrl-item {{ display: flex; flex-direction: column; font-size: 11px; font-weight: 600; color: #9ca3af; }}
  .ctrl-item input, .ctrl-item select {{ margin-top: 4px; padding: 6px; border-radius: 6px; border: 1px solid #4b5563; background: #1f2937; color: #facc15; font-size: 12px; }}
  
  .highlight-section {{
      margin-top: 14px; padding: 12px; background: #1f2937; border-radius: 10px; border: 1px dashed #f59e0b;
      display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 10px;
  }}

  .btn-row {{ display: flex; gap: 14px; justify-content: center; margin-top: 18px; }}
  .btn-png {{ background: #facc15; color: #000; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 14px; box-shadow: 0 4px 14px rgba(250,204,21,0.3); }}
  .btn-gif {{ background: #ec4899; color: #fff; border: none; padding: 10px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 14px; box-shadow: 0 4px 14px rgba(236,72,153,0.4); }}

  #gifStatus {{ color: #ec4899; font-size: 13px; font-weight: bold; margin-top: 10px; display: none; text-align: center; }}
</style>
</head>
<body>

<!-- 1. పోస్టర్ కార్డ్ (పైన ప్రత్యక్షమవుతుంది) -->
<div class="poster-card" id="posterCard">
  <div class="sparkle-decor" style="top: 25px; left: 30px;">✨</div>
  <div class="sparkle-decor" style="top: 35px; right: 35px; animation-delay: 1.4s;">🌟</div>
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

<!-- 2. లైవ్ కంట్రోలర్ ప్యానెల్ (పోస్టర్ క్రింద) -->
<div class="control-panel">
  <div class="panel-title">🎛️ పోస్టర్ లైవ్ ట్యూనింగ్ సెట్టింగ్స్ & ప్రొఫెషనల్ టూల్స్</div>
  
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
      <input type="range" id="rngFontSize" min="14" max="28" value="{selected_font_size}" oninput="updateLayout()">
    </div>
    <div class="ctrl-item">
      <label>📏 వాక్యాల దూరం (Line Gap):</label>
      <input type="range" id="rngLineHeight" min="1.2" max="2.4" step="0.1" value="{init_line_h}" oninput="updateLayout()">
    </div>
    <div class="ctrl-item">
      <label>🎨 టెక్స్ట్ రంగు:</label>
      <select id="selColor" onchange="updateLayout()">
        <option value="{init_color}">{'డార్క్ మెరూన్ (Maroon)' if has_custom_bg else 'ప్యూర్ వైట్ (White)'}</option>
        <option value="#5c0606">డార్క్ మెరూన్ (Maroon)</option>
        <option value="#0f172a">రాయల్ బ్లాక్ (Black)</option>
        <option value="#ffffff">ప్యూర్ వైట్ (White)</option>
        <option value="#facc15">గోల్డెన్ ఎల్లో (Gold)</option>
        <option value="#1e3a8a">రాయల్ బ్లూ (Blue)</option>
      </select>
    </div>
    <div class="ctrl-item">
      <label>🌫️ బ్యాక్‌గ్రౌండ్ షేడ్:</label>
      <select id="selBgShade" onchange="updateLayout()">
        <option value="transparent">పూర్తి పారదర్శకం (Clear)</option>
        <option value="rgba(255, 255, 255, 0.45)">లైట్ వైట్ గ్లాస్ (White Glass)</option>
        <option value="rgba(0, 0, 0, 0.45)">సాఫ్ట్ డార్క్ గ్లాస్ (Dark Glass)</option>
      </select>
    </div>
    <div class="ctrl-item">
      <label>🌟 దివ్య కిరణాల ఆరా (Rays):</label>
      <select id="selAura" onchange="toggleAura()">
        <option value="block">✨ ఆన్ (Shining Aura)</option>
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
      <label>🚩 స్పెషల్ వాక్యం / కొటేషన్ హైలైట్ చేయి:</label>
      <input type="text" id="txtHighlight" value="{init_hl}" placeholder="ఉదా: రక్తదానం మహోన్నత సేవ..." oninput="updateHighlight()">
    </div>
    <div class="ctrl-item">
      <label>🎨 హైలైట్ కలర్ స్టైల్:</label>
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
  <div id="gifStatus">⏳ GIF ఫ్రేమ్స్ & ఆరా ఎఫెక్ట్స్ తయారవుతున్నాయి... 3 సెకన్లు వేచి ఉండండి...</div>
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
    contentBox.style.borderRadius = "10px";
    
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

updateLayout();

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
