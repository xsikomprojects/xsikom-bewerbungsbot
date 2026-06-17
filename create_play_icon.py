"""
Play Store Icons fuer XsiKOM-BewerbungsBOT
"""
import os
from PIL import Image, ImageDraw, ImageFont


def play_store_icon():
    """Erstellt 512x512 Play Store Icon."""
    groesse = 512
    img = Image.new("RGBA", (groesse, groesse), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gradient Hintergrund
    for i in range(groesse):
        r = int(30 + (i / groesse) * 50)
        g = int(61 + (i / groesse) * 100)
        b = int(92 + (i / groesse) * 60)
        draw.line(
            [(0, i), (groesse, i)],
            fill=(r, g, b, 255)
        )

    # Runde Ecken
    mask = Image.new("L", (groesse, groesse), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = groesse // 6
    mask_draw.rounded_rectangle(
        [(0, 0), (groesse, groesse)],
        radius=radius,
        fill=255
    )
    output = Image.new("RGBA", (groesse, groesse), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)

    draw = ImageDraw.Draw(output)

    # KI Chip oben
    chip_y = 130
    draw.rounded_rectangle(
        [(180, chip_y), (332, chip_y + 60)],
        radius=20,
        fill=(255, 217, 61, 255)
    )
    # Chip Dots
    for x in [220, 256, 292]:
        draw.ellipse(
            [(x-8, chip_y+22), (x+8, chip_y+38)],
            fill=(15, 25, 35, 255)
        )

    # XsiKOM Text
    try:
        font_xsikom = ImageFont.truetype("arial.ttf", 90)
        font_bot = ImageFont.truetype("arial.ttf", 50)
    except Exception:
        font_xsikom = ImageFont.load_default()
        font_bot = ImageFont.load_default()

    # XsiKOM
    text = "XsiKOM"
    bbox = draw.textbbox((0, 0), text, font=font_xsikom)
    text_breite = bbox[2] - bbox[0]
    x = (groesse - text_breite) // 2

    # Schatten
    draw.text((x + 3, 233), text, fill=(0, 0, 0, 150), font=font_xsikom)
    # Text
    draw.text((x, 230), text, fill=(0, 180, 216, 255), font=font_xsikom)

    # BOT
    text = "BOT"
    bbox = draw.textbbox((0, 0), text, font=font_bot)
    text_breite = bbox[2] - bbox[0]
    x = (groesse - text_breite) // 2

    draw.text((x + 2, 342), text, fill=(0, 0, 0, 150), font=font_bot)
    draw.text((x, 340), text, fill=(232, 237, 242, 255), font=font_bot)

    # Speichern
    static_pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "static"
    )
    os.makedirs(static_pfad, exist_ok=True)

    pfad = os.path.join(static_pfad, "play-store-icon-512.png")
    output.save(pfad, "PNG", optimize=True)
    print(f"Play Store Icon erstellt: {pfad}")


def feature_graphic():
    """Erstellt 1024x500 Feature Graphic."""
    breite = 1024
    hoehe = 500
    img = Image.new("RGBA", (breite, hoehe), (15, 25, 35, 255))
    draw = ImageDraw.Draw(img)

    # Gradient
    for i in range(breite):
        r = int(30 + (i / breite) * 50)
        g = int(61 + (i / breite) * 100)
        b = int(92 + (i / breite) * 60)
        draw.line(
            [(i, 0), (i, hoehe)],
            fill=(r, g, b, 255)
        )

    try:
        font_xl = ImageFont.truetype("arial.ttf", 80)
        font_l = ImageFont.truetype("arial.ttf", 40)
        font_m = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        font_xl = ImageFont.load_default()
        font_l = ImageFont.load_default()
        font_m = ImageFont.load_default()

    # Titel
    draw.text((50, 100), "XsiKOM", fill=(0, 180, 216, 255), font=font_xl)
    draw.text((50, 200), "BewerbungsBOT", fill=(45, 212, 168, 255), font=font_l)

    # Subtitle
    draw.text(
        (50, 280),
        "Dein KI-Assistent fuer IT-Bewerbungen",
        fill=(232, 237, 242, 255),
        font=font_m
    )

    # Features
    draw.text((50, 360), "+ Aaliyah KI Beraterin", fill=(255, 217, 61, 255), font=font_m)
    draw.text((50, 400), "+ Lebenslauf Editor", fill=(255, 217, 61, 255), font=font_m)
    draw.text((50, 440), "+ Bewerbungs-Tracking", fill=(255, 217, 61, 255), font=font_m)

    static_pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "static"
    )
    pfad = os.path.join(static_pfad, "play-store-feature.png")
    img.save(pfad, "PNG", optimize=True)
    print(f"Feature Graphic erstellt: {pfad}")


if __name__ == "__main__":
    print("Erstelle Play Store Assets...")
    play_store_icon()
    feature_graphic()
    print("\nFertig! Dateien:")
    print("- static/play-store-icon-512.png (512x512)")
    print("- static/play-store-feature.png (1024x500)")