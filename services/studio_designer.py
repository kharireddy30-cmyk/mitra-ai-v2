import base64
import json
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
        if any(k in clean_t for k in ["రక్తం", "రక్తదాన", "సేవ", "ఆసుపత్రి", "బ్లడ్", "శిబిరం"]):
            return "🩸"
        elif any(k in clean_t for k in ["ఓం", "శాంతి", "ధ్యానం", "భగవాన్", "ఆత్మ", "ఆధ్యాత్మిక", "శివ", "బాబా"]):
            return "🕉️"
        elif any(k in clean_t for k in ["శాంతి", "ప్రశాంతత", "ప్రేమ"]):
            return "🕊️"
        elif any(k in clean_t for k in ["విజయం", "శుభాకాంక్షలు", "అభినందనలు", "స్టార్"]):
            return "🌟"
        else:
            return "🪷"
            
    return stickers_map.get(sticker_choice, "🕉️")


def get_groq_ai_design_suggestions(text, user_prompt=""):
    groq_key = st.secrets.get("GROQ_API_KEY", "")
    
    default_config = {
        "title": "సందేశం / ముఖ్యాంశాలు",
        "highlight": "",
        "textColor": "#5c0606",
        "bgShade": "transparent",
        "fontSize": 18,
        "lineHeight": 1.6,
        "topOffset": 230,
        "leftOffset": 0,
        "auraPos": "top",
        "fontFamily": "'Mandali', sans-serif"
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
  "lineHeight": 1.6,
  "topOffset": 230,
  "leftOffset": 0,
  "auraPos": "top or center or bottom or none",
  "fontFamily": "'Mandali', sans-serif"
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
        req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers=headers, method='POST')
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
    if not text or not text.strip():
        return ""

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
        "పెద్దది (Large - 22px)": 21,
        "చాలా పెద్దది (X-Large - 26px)": 25
    }
    selected_font_size = font_size_map.get(font_size_choice, ai_cfg.get("fontSize", 18))

    align_map = {
        "ఎడమ వైపు (Left)": "left",
        "మధ్యలో (Center)": "center",
        "సమానంగా (Justify)": "justify"
    }
    selected_align = align_map.get(text_align, "center")

    custom_img_html = ""
    if custom_sticker_file is not None:
        try:
            custom_sticker_file.seek(0)
            b64_data = base64.b64encode(custom_sticker_file.read()).decode()
            mime_type = custom_sticker_file.type or "image/png"
            custom_img_html = f"<img src='data:{mime_type};base64,{b64_data}' style='width: 52px; height: 52px; object-fit: contain; border-radius: 50%; border: 2px solid #facc15;' />"
        except Exception:
            pass

    selected_symbol = get_sticker_symbol(sticker_choice, text)
    top_sticker_display = custom_img_html if custom_img_html else f"<div class='sticker-badge'>{selected_symbol}</div>"

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    body_content_html = "".join([f"<p class='content-p'>{p}</p>" for p in paragraphs])

    init_top = 230 if has_custom_bg else 10
    init_left = 0
    init_color = "#5c0606" if has_custom_bg else "#ffffff"
    init_bg = ai_cfg.get("bgShade", "transparent")
    init_line_h = ai_cfg.get("lineHeight", 1.6)
    init_hl = ai_cfg.get("highlight", "")
    init_title = ai_cfg.get("title", "సందేశం / ముఖ్యాంశాలు")

    html_code = f"""<!DOCTYPE html>
<html lang="te">
<head>
<meta charset="utf-8">
<title>BRAHMA AI Studio Pro - Ultimate Edition</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gifshot/0.3.2/gifshot.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Mandali&family=Suranna&family=Ramabhadra&display=swap');
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; padding: 10px; background: #070a13; color: #fff; font-family: 'Mandali', sans-serif; user-select: none; }}
  
  .studio-layout {{
      display: flex; flex-direction: row; justify-content: center; align-items: flex-start;
      gap: 15px; width: 100%; max-width: 1320px; margin: 0 auto;
  }}

  /* టూల్ ప్యానెల్స్ */
  .side-panel {{
      flex: 1; min-width: 260px; max-width: 320px; background: #111827;
      border: 1px solid #374151; border-radius: 14px; padding: 14px 16px;
      box-shadow: 0 8px 25px rgba(0,0,0,0.75);
  }}
  .panel-header {{
      font-size: 13px; font-weight: bold; color: #facc15; text-align: center;
      margin-bottom: 12px; border-bottom: 1px solid #374151; padding-bottom: 6px;
  }}
  .tool-item {{
      display: flex; flex-direction: column; margin-bottom: 10px;
      font-size: 11px; font-weight: 600; color: #cbd5e1;
  }}
  .tool-item input, .tool-item select {{
      margin-top: 3px; padding: 5px 8px; border-radius: 6px;
      border: 1px solid #4b5563; background: #1f2937; color: #facc15; font-size: 12px;
  }}
  
  /* మధ్యలో పోస్టర్ కాన్వాస్ కార్డ్ */
  .center-stage {{ flex: 1.4; display: flex; flex-direction: column; align-items: center; }}
  .poster-card {{
      width: 100%; max-width: 530px; min-height: 730px; background: {bg_style};
      border: 3.5px solid #facc15; border-radius: 18px; padding: 18px; color: #ffffff;
      box-shadow: 0 15px 40px rgba(0,0,0,0.95); position: relative; overflow: hidden;
      display: flex; flex-direction: column; justify-content: space-between;
  }}

  /* యానిమేషన్లు */
  @keyframes pulseRays {{
      0% {{ transform: translate(-50%, 0) scale(0.85); opacity: 0.35; filter: drop-shadow(0 0 10px #f59e0b); }}
      50% {{ transform: translate(-50%, 0) scale(1.30); opacity: 0.95; filter: drop-shadow(0 0 35px #fbbf24); }}
      100% {{ transform: translate(-50%, 0) scale(0.85); opacity: 0.35; filter: drop-shadow(0 0 10px #f59e0b); }}
  }}
  @keyframes shimmerText {{
      0% {{ text-shadow: 0 0 4px rgba(250,204,21,0.3); }}
      50% {{ text-shadow: 0 0 16px rgba(250,204,21,0.95), 0 0 28px #f59e0b; }}
      100% {{ text-shadow: 0 0 4px rgba(250,204,21,0.3); }}
  }}

  /* డైనమిక్ ఆరా (టాప్, సెంటర్, బాటమ్) */
  .divine-aura {{
      position: absolute; left: 50%; width: 130px; height: 130px;
      border-radius: 50%; background: radial-gradient(circle, rgba(251,191,36,0.9) 0%, rgba(245,158,11,0.5) 45%, transparent 70%);
      pointer-events: none; z-index: 1; animation: pulseRays 2.2s infinite ease-in-out;
  }}
  .aura-top {{ top: 38px; }}
  .aura-center {{ top: 50%; transform: translate(-50%, -50%); }}
  .aura-bottom {{ bottom: 30px; }}

  .sparkle-decor {{ position: absolute; font-size: 20px; color: #fde047; pointer-events: none; }}

  .header-box {{ text-align: center; margin-bottom: 6px; z-index: 2; cursor: move; {'display: none;' if has_custom_bg else ''} }}
  .header-title {{ font-size: 22px; font-weight: bold; color: #facc15; animation: shimmerText 2.5s infinite; }}
  .sticker-badge {{ font-size: 36px; display: inline-block; filter: drop-shadow(0 0 8px #facc15); }}
  
  /* డ్రాగబుల్ కంటెంట్ బాక్స్ */
  .content-canvas {{
      width: 88%; margin: 0 auto; padding: 10px;
      transition: width 0.1s, font-size 0.1s, line-height 0.1s, color 0.1s, background 0.1s;
      position: relative; z-index: 2; cursor: move;
      font-size: {selected_font_size}px; line-height: {init_line_h}; color: {init_color};
      text-align: {selected_align};
      margin-top: {init_top}px;
      transform: translateX({init_left}px);
      text-shadow: 0 1px 2px rgba(255,255,255,0.7);
      font-family: 'Mandali', sans-serif;
  }}
  .content-p {{ margin-bottom: 8px; }}

  .special-highlight-card {{
      display: {'block' if init_hl else 'none'}; margin-top: 10px; padding: 7px 12px; text-align: center;
      background: linear-gradient(90deg, rgba(250,204,21,0.2), rgba(250,204,21,0.65), rgba(250,204,21,0.2));
      border: 1.5px solid #facc15; border-radius: 8px; font-weight: bold; font-size: 18px; color: #7f1d1d;
      animation: shimmerText 2s infinite; cursor: move;
  }}
  
  .footer-box {{ text-align: center; padding: 5px; z-index: 2; cursor: move; {'display: none;' if has_custom_bg else ''} }}
  .footer-quote {{ font-size: 15px; font-weight: bold; color: #fde047; margin: 0; }}

  .btn-stack {{ display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }}
  .btn-png {{ background: #facc15; color: #000; border: none; padding: 9px; border-radius: 7px; font-weight: bold; cursor: pointer; font-size: 13px; }}
  .btn-gif {{ background: #ec4899; color: #fff; border: none; padding: 9px; border-radius: 7px; font-weight: bold; cursor: pointer; font-size: 13px; }}

  #gifStatus {{ color: #ec4899; font-size: 12px; font-weight: bold; margin-top: 8px; display: none; text-align: center; }}
</style>
</head>
<body>

<div class="studio-layout">
  
  <!-- ఎడమ వైపు ప్యానెల్ (Typography, Font & Align) -->
  <div class="side-panel">
    <div class="panel-header">📐 లేఅవుట్, స్థానం & ఫాంట్స్ (Left)</div>
    
    <div class="tool-item">
      <label>↕️ ఎత్తు (Top/Y Offset):</label>
      <input type="range" id="rngTop" min="0" max="450" value="{init_top}" oninput="updateLayout()">
    </div>

    <div class="tool-item">
      <label>↔️ అడ్డం (Left/X Offset):</label>
      <input type="range" id="rngLeft" min="-150" max="150" value="{init_left}" oninput="updateLayout()">
    </div>
    
    <div class="tool-item">
      <label>↔️ బాక్స్ వెడల్పు (%):</label>
      <input type="range" id="rngWidth" min="50" max="100" value="88" oninput="updateLayout()">
    </div>
    
    <div class="tool-item">
      <label>🔤 అక్షరాల సైజు (px):</label>
      <input type="range" id="rngFontSize" min="12" max="30" value="{selected_font_size}" oninput="updateLayout()">
    </div>
    
    <div class="tool-item">
      <label>📏 వాక్యాల దూరం (Line Gap):</label>
      <input type="range" id="rngLineHeight" min="1.1" max="2.4" step="0.1" value="{init_line_h}" oninput="updateLayout()">
    </div>

    <div class="tool-item">
      <label>🖋️ తెలుగు ఫాంట్ శైలి:</label>
      <select id="selFont" onchange="updateLayout()">
        <option value="'Mandali', sans-serif">మండలి (Mandali - Standard)</option>
        <option value="'Suranna', serif">సూరన్న (Suranna - Traditional)</option>
        <option value="'Ramabhadra', sans-serif">రామభద్ర (Ramabhadra - Bold)</option>
      </select>
    </div>

    <div class="tool-item">
      <label>📐 టెక్స్ట్ అమరిక (Alignment):</label>
      <select id="selAlign" onchange="updateLayout()">
        <option value="center">మధ్యలో (Center)</option>
        <option value="left">ఎడమ వైపు (Left)</option>
        <option value="justify">సమానంగా (Justify)</option>
      </select>
    </div>

    <div class="tool-item">
      <label>👁️ హెడర్ / టైటిల్:</label>
      <select id="selHeader" onchange="toggleHeader()">
        <option value="{'none' if has_custom_bg else 'block'}">{'దాచు (Hide)' if has_custom_bg else 'చూపించు (Show)'}</option>
        <option value="{'block' if has_custom_bg else 'none'}">{'చూపించు (Show)' if has_custom_bg else 'దాచు (Hide)'}</option>
      </select>
    </div>
  </div>

  <!-- మధ్యలో పోస్టర్ కార్డ్ (Center Full Poster with Drag Support) -->
  <div class="center-stage">
    <div class="poster-card" id="posterCard">
      <div class="sparkle-decor" style="top: 20px; left: 25px;">✨</div>
      <div class="sparkle-decor" style="top: 30px; right: 30px;">🌟</div>
      
      <!-- జ్యోతి ఆరా లైట్ -->
      <div class="divine-aura aura-top" id="divineAura"></div>

      <div class="header-box" id="headerBox">
        {top_sticker_display}
        <div class="header-title">{init_title}</div>
      </div>

      <div class="content-canvas" id="contentBox" title="మౌస్ లేదా టచ్ తో పట్టుకుని ఎక్కడికైనా జరపవచ్చు">
        {body_content_html}
        <div class="special-highlight-card" id="specialHighlight">{'✨ ' + init_hl + ' ✨' if init_hl else ''}</div>
      </div>

      <div class="footer-box" id="footerBox">
        <p class="footer-quote">🌺 ✨ సర్వేజనా సుఖినోభవంతు ✨ 🌺</p>
      </div>
    </div>
  </div>

  <!-- కుడి వైపు ప్యానెల్ (Colors, 3D Outline, Aura & Export) -->
  <div class="side-panel">
    <div class="panel-header">🎨 రంగులు, గ్లో & ఎగుమతి (Right)</div>
    
    <div class="tool-item">
      <label>🎨 టెక్స్ట్ రంగు:</label>
      <select id="selColor" onchange="updateLayout()">
        <option value="{init_color}">{'డార్క్ మెరూన్ (Maroon)' if has_custom_bg else 'ప్యూర్ వైట్ (White)'}</option>
        <option value="#5c0606">డార్క్ మెరూన్ (Maroon)</option>
        <option value="#0f172a">రాయల్ బ్లాక్ (Black)</option>
        <option value="#ffffff">ప్యూర్ వైట్ (White)</option>
        <option value="#facc15">గోల్డెన్ ఎల్లో (Gold)</option>
        <option value="#1e3a8a">రాయల్ బ్లూ (Blue)</option>
        <option value="#7f1d1d">డీప్ రెడ్ (Deep Red)</option>
      </select>
    </div>

    <div class="tool-item">
      <label>✨ టెక్స్ట్ స్ట్రోక్ & 3D గ్లో:</label>
      <select id="selStroke" onchange="updateLayout()">
        <option value="none">సాధారణ షాడో (Normal Shadow)</option>
        <option value="gold-glow">గోల్డెన్ గ్లో (Golden Glow)</option>
        <option value="dark-outline">డార్క్ ఔట్‌లైన్ (Dark Bold Outline)</option>
        <option value="white-glow">వైట్ డివైన్ గ్లో (Angelic White Glow)</option>
      </select>
    </div>

    <div class="tool-item">
      <label>🌫️ బ్యాక్‌గ్రౌండ్ గ్లాస్ షేడ్:</label>
      <select id="selBgShade" onchange="updateLayout()">
        <option value="transparent">పూర్తి పారదర్శకం (Clear)</option>
        <option value="rgba(255, 255, 255, 0.45)">లైట్ వైట్ గ్లాస్ (White Glass)</option>
        <option value="rgba(0, 0, 0, 0.45)">సాఫ్ట్ డార్క్ గ్లాస్ (Dark Glass)</option>
        <option value="rgba(250, 204, 21, 0.2)">గోల్డెన్ గ్లాస్ (Gold Tint)</option>
      </select>
    </div>

    <div class="tool-item">
      <label>🌟 దివ్య జ్యోతి ఆరా (Light Position):</label>
      <select id="selAuraPos" onchange="updateAura()">
        <option value="top">✨ పైన జ్యోతి బిందువు (Top Light)</option>
        <option value="center">🕊️ మధ్యలో అవ్యక్త ఆరా (Center Angelic)</option>
        <option value="bottom">🕉️ కింద శివలింగం (Bottom Light)</option>
        <option value="none">ఆఫ్ (Off)</option>
      </select>
    </div>

    <div class="tool-item">
      <label>🚩 కొటేషన్ / స్లోగన్ హైలైట్:</label>
      <input type="text" id="txtHighlight" value="{init_hl}" placeholder="ముఖ్యమైన వాక్యం..." oninput="updateHighlight()">
    </div>

    <div class="tool-item">
      <label>🎨 హైలైట్ కలర్:</label>
      <select id="selHlColor" onchange="updateHighlight()">
        <option value="#7f1d1d">డీప్ రెడ్ (Deep Red)</option>
        <option value="#1e3a8a">రాయల్ బ్లూ (Royal Blue)</option>
        <option value="#065f46">ఎమరాల్డ్ గ్రీన్ (Green)</option>
        <option value="#facc15">గోల్డ్ (Gold)</option>
      </select>
    </div>

    <div class="btn-stack">
      <button class="btn-png" onclick="saveAsImage()">📸 ఇమేజ్ (.PNG)</button>
      <button class="btn-gif" onclick="generateAnimatedGIF()">✨ యానిమేటెడ్ GIF డౌన్‌లోడ్</button>
    </div>
    <div id="gifStatus">⏳ GIF ఫ్రేమ్స్ రికార్డ్ అవుతున్నాయి... 3 సెకన్లు వేచి ఉండండి...</div>
  </div>

</div>

<script>
function updateLayout() {{
    const topVal = document.getElementById("rngTop").value;
    const leftVal = document.getElementById("rngLeft").value;
    const widthVal = document.getElementById("rngWidth").value;
    const fontVal = document.getElementById("rngFontSize").value;
    const lineHVal = document.getElementById("rngLineHeight").value;
    const colorVal = document.getElementById("selColor").value;
    const strokeVal = document.getElementById("selStroke").value;
    const bgShadeVal = document.getElementById("selBgShade").value;
    const alignVal = document.getElementById("selAlign").value;
    const fontFam = document.getElementById("selFont").value;
    
    const contentBox = document.getElementById("contentBox");
    contentBox.style.marginTop = topVal + "px";
    contentBox.style.transform = `translateX(${{leftVal}}px)`;
    contentBox.style.width = widthVal + "%";
    contentBox.style.fontSize = fontVal + "px";
    contentBox.style.lineHeight = lineHVal;
    contentBox.style.color = colorVal;
    contentBox.style.background = bgShadeVal;
    contentBox.style.textAlign = alignVal;
    contentBox.style.fontFamily = fontFam;
    contentBox.style.borderRadius = "10px";
    
    if (strokeVal === "gold-glow") {{
        contentBox.style.textShadow = "0 0 10px #facc15, 0 0 20px #f59e0b, 0 1px 2px #000";
    }} else if (strokeVal === "dark-outline") {{
        contentBox.style.textShadow = "-1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 2px 5px rgba(0,0,0,0.8)";
    }} else if (strokeVal === "white-glow") {{
        contentBox.style.textShadow = "0 0 8px rgba(255,255,255,0.9), 0 0 15px rgba(255,255,255,0.6)";
    }} else {{
        if (colorVal === "#ffffff" || colorVal === "#facc15") {{
            contentBox.style.textShadow = "0 2px 6px rgba(0,0,0,0.95)";
        }} else {{
            contentBox.style.textShadow = "0 1px 2px rgba(255,255,255,0.7)";
        }}
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

function updateAura() {{
    const pos = document.getElementById("selAuraPos").value;
    const aura = document.getElementById("divineAura");
    if (pos === "none") {{
        aura.style.display = "none";
    }} else if (pos === "top") {{
        aura.style.display = "block";
        aura.className = "divine-aura aura-top";
    }} else if (pos === "center") {{
        aura.style.display = "block";
        aura.className = "divine-aura aura-center";
    }} else {{
        aura.style.display = "block";
        aura.className = "divine-aura aura-bottom";
    }}
}}

// ===============================================
// లైవ్ మౌస్ & టచ్ డ్రాగ్ అండ్ డ్రాప్ ఇంజిన్
// ===============================================
let isDragging = false;
let startX, startY;
const contentBox = document.getElementById("contentBox");

function startDrag(e) {{
    isDragging = true;
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    startX = clientX;
    startY = clientY;
}}

function doDrag(e) {{
    if (!isDragging) return;
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    const dx = clientX - startX;
    const dy = clientY - startY;
    
    let currentTop = parseInt(document.getElementById("rngTop").value) || 0;
    let currentLeft = parseInt(document.getElementById("rngLeft").value) || 0;
    
    let newTop = Math.max(0, Math.min(450, currentTop + dy));
    let newLeft = Math.max(-150, Math.min(150, currentLeft + dx));
    
    document.getElementById("rngTop").value = newTop;
    document.getElementById("rngLeft").value = newLeft;
    
    startX = clientX;
    startY = clientY;
    
    updateLayout();
}}

function stopDrag() {{
    isDragging = false;
}}

contentBox.addEventListener("mousedown", startDrag);
window.addEventListener("mousemove", doDrag);
window.addEventListener("mouseup", stopDrag);

contentBox.addEventListener("touchstart", startDrag, {{ passive: true }});
window.addEventListener("touchmove", doDrag, {{ passive: true }});
window.addEventListener("touchend", stopDrag);

// ప్రారంభ అమరిక
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
