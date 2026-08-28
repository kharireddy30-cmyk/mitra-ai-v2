from PIL import Image, ImageDraw, ImageFont
import os

def generate_golden_om_icon():
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # బ్యాక్‌గ్రౌండ్ గోల్డెన్ & రాయల్ పర్పుల్ సర్కిల్ గ్లో
    for r in range(120, 0, -2):
        alpha = int(255 * (1 - (r / 120)))
        draw.ellipse([128 - r, 128 - r, 128 + r, 128 + r], fill=(245, 158, 11, alpha))

    # బార్డర్ సర్కిల్
    draw.ellipse([8, 8, 248, 248], outline=(250, 204, 21, 255), width=8)

    # 🕉️ చిహ్నం డ్రాయింగ్
    try:
        font = ImageFont.truetype("arial.ttf", 130)
    except Exception:
        font = ImageFont.load_default()

    draw.text((128, 128), "🕉", fill=(255, 255, 255, 255), font=font, anchor="mm")

    icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save("app_icon.ico", format="ICO", sizes=icon_sizes)
    print("✅ app_icon.ico generated successfully!")

if __name__ == "__main__":
    generate_golden_om_icon()
