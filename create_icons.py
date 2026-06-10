"""
PWA Icons fuer XsiKOM-BewerbungsBOT erstellen
"""
import os
from PIL import Image, ImageDraw, ImageFont


def icon_erstellen(groesse, dateiname):
    """Erstellt ein PWA Icon."""
    img = Image.new("RGBA", (groesse, groesse), (15, 25, 35, 255))
    draw = ImageDraw.Draw(img)

    # Hintergrund Gradient (simuliert)
    for i in range(groesse):
        farbe_r = int(0 + (i / groesse) * 30)
        farbe_g = int(180 + (i / groesse) * 20)
        farbe_b = int(216 - (i / groesse) * 50)
        draw.line(
            [(0, i), (groesse, i)],
            fill=(farbe_r, farbe_g, farbe_b, 255)
        )

    # Runde Ecken simulieren (mit Maske)
    mask = Image.new("L", (groesse, groesse), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = groesse // 6
    mask_draw.rounded_rectangle(
        [(0, 0), (groesse, groesse)],
        radius=radius,
        fill=255
    )

    # Anwenden
    output = Image.new("RGBA", (groesse, groesse), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask)

    # Text XK
    draw = ImageDraw.Draw(output)
    schrift_groesse = groesse // 3
    try:
        font = ImageFont.truetype("arial.ttf", schrift_groesse)
    except Exception:
        font = ImageFont.load_default()

    text = "XK"

    # Text zentrieren
    bbox = draw.textbbox((0, 0), text, font=font)
    text_breite = bbox[2] - bbox[0]
    text_hoehe = bbox[3] - bbox[1]
    x = (groesse - text_breite) // 2
    y = (groesse - text_hoehe) // 2 - bbox[1]

    # Text mit Schatten
    draw.text(
        (x + 2, y + 2),
        text,
        fill=(0, 0, 0, 100),
        font=font
    )
    draw.text(
        (x, y),
        text,
        fill=(255, 255, 255, 255),
        font=font
    )

    # Speichern
    output.save(dateiname, "PNG")
    print(f"  Icon erstellt: {dateiname} ({groesse}x{groesse})")


def alle_icons_erstellen():
    """Erstellt alle benoetigten PWA Icons."""
    # Ordner erstellen
    static_pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "static"
    )
    os.makedirs(static_pfad, exist_ok=True)

    # Alle Groessen
    groessen = [72, 96, 128, 144, 152, 192, 384, 512]

    print("\nErstelle PWA Icons...")
    print("-" * 50)

    for groesse in groessen:
        dateiname = os.path.join(static_pfad, f"icon-{groesse}.png")
        icon_erstellen(groesse, dateiname)

    print("-" * 50)
    print(f"Alle Icons erstellt in: {static_pfad}")
    print(f"Anzahl: {len(groessen)} Icons")


if __name__ == "__main__":
    alle_icons_erstellen()