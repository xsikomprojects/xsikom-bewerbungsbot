"""Erstellt ein App-Icon."""
from PIL import Image, ImageDraw, ImageFont
import os


def icon_erstellen():
    """Erstellt ein professionelles App-Icon."""
    # Icon Groesse
    groesse = 256
    img     = Image.new("RGBA", (groesse, groesse), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(img)

    # Hintergrund (Blauer Kreis)
    draw.ellipse(
        [10, 10, groesse-10, groesse-10],
        fill=(0, 70, 127)
    )

    # Innerer Kreis
    draw.ellipse(
        [20, 20, groesse-20, groesse-20],
        fill=(0, 90, 160)
    )

    # Text "KT"
    draw.text(
        (groesse//2, groesse//2),
        "KT",
        fill=(255, 255, 255),
        anchor="mm"
    )

    # IT Text
    draw.text(
        (groesse//2, groesse//2 + 50),
        "BOT",
        fill=(200, 220, 255),
        anchor="mm"
    )

    # Speichern
    pfad_png = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "icon.png"
    )
    pfad_ico = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "icon.ico"
    )

    img.save(pfad_png)

    # ICO erstellen
    img_ico = img.resize((64, 64))
    img_ico.save(pfad_ico, format="ICO")

    print(f"Icon erstellt: {pfad_png}")
    print(f"Icon erstellt: {pfad_ico}")
    return pfad_ico


if __name__ == "__main__":
    icon_erstellen()