"""
Lebenslauf-Editor für mehrere Benutzer
"""
import os
import json
from datetime import datetime
from fpdf import FPDF
from config import PERSOENLICHE_DATEN, QUALIFIKATIONEN

DATEN_PFAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "benutzer_daten"
)
os.makedirs(DATEN_PFAD, exist_ok=True)


def user_daten_pfad(benutzername):
    """Gibt Pfad für Benutzerdaten zurück."""
    pfad = os.path.join(DATEN_PFAD, benutzername)
    os.makedirs(pfad, exist_ok=True)
    return pfad


def benutzer_daten_speichern(benutzername, daten):
    """Speichert Benutzerdaten als JSON."""
    pfad = os.path.join(
        user_daten_pfad(benutzername),
        "profil.json"
    )
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    return pfad


def benutzer_daten_laden(benutzername):
    """Lädt Benutzerdaten aus JSON."""
    pfad = os.path.join(
        user_daten_pfad(benutzername),
        "profil.json"
    )
    if os.path.exists(pfad):
        with open(pfad, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def standard_profil():
    """Gibt Standard-Profil zurück."""
    return {
        "vorname":      PERSOENLICHE_DATEN.get("vorname", ""),
        "nachname":     PERSOENLICHE_DATEN.get("nachname", ""),
        "strasse":      PERSOENLICHE_DATEN.get("strasse", ""),
        "plz":          PERSOENLICHE_DATEN.get("plz", ""),
        "stadt":        PERSOENLICHE_DATEN.get("stadt", ""),
        "telefon":      PERSOENLICHE_DATEN.get("telefon", ""),
        "email":        PERSOENLICHE_DATEN.get("email", ""),
        "geburtsdatum": PERSOENLICHE_DATEN.get("geburtsdatum", ""),
        "ausbildung":   QUALIFIKATIONEN.get("ausbildung", ""),
        "kenntnisse":   QUALIFIKATIONEN.get("kenntnisse", []),
        "sprachen":     QUALIFIKATIONEN.get("sprachen", []),
        "berufserfahrung": QUALIFIKATIONEN.get("berufserfahrung", []),
        "zertifikate":  QUALIFIKATIONEN.get("zertifikate", []),
    }


def lebenslauf_aus_profil(profil):
    """Erstellt Lebenslauf-PDF aus Profil-Daten."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Header
    pdf.set_fill_color(0, 70, 127)
    pdf.rect(0, 0, 210, 42, "F")
    pdf.set_xy(15, 7)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    name = f"{profil.get('vorname', '')} {profil.get('nachname', '')}"
    pdf.cell(0, 10, name, ln=True)

    pdf.set_xy(15, 19)
    pdf.set_font("Helvetica", "I", 12)
    pdf.set_text_color(200, 225, 255)
    pdf.cell(0, 7, profil.get("ausbildung", "IT-Fachtechniker"), ln=True)

    pdf.set_xy(15, 29)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(255, 255, 255)
    kontakt = (
        f"{profil.get('strasse', '')}, "
        f"{profil.get('plz', '')} {profil.get('stadt', '')}  |  "
        f"{profil.get('telefon', '')}  |  "
        f"{profil.get('email', '')}"
    )
    pdf.cell(0, 6, kontakt)
    pdf.ln(20)

    # Persönliche Daten
    pdf.set_fill_color(0, 70, 127)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "  PERSOENLICHE DATEN", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    if profil.get("geburtsdatum"):
        pdf.set_x(15)
        pdf.cell(45, 6, "Geburtsdatum:")
        pdf.cell(0, 6, profil["geburtsdatum"], ln=True)

    # Kenntnisse
    if profil.get("kenntnisse"):
        pdf.ln(3)
        pdf.set_fill_color(0, 70, 127)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "  IT-KENNTNISSE", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 9)
        for k in profil["kenntnisse"]:
            pdf.set_x(15)
            pdf.cell(5, 5, "-")
            pdf.cell(0, 5, k, ln=True)

    # Sprachen
    if profil.get("sprachen"):
        pdf.ln(3)
        pdf.set_fill_color(0, 70, 127)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "  SPRACHEN", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 9)
        for s in profil["sprachen"]:
            pdf.set_x(15)
            pdf.cell(5, 5, "-")
            pdf.cell(0, 5, s, ln=True)

    # Berufserfahrung
    if profil.get("berufserfahrung"):
        pdf.ln(3)
        pdf.set_fill_color(0, 70, 127)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "  BERUFSERFAHRUNG", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 9)
        for b in profil["berufserfahrung"]:
            pdf.set_x(15)
            pdf.cell(5, 5, "-")
            pdf.cell(0, 5, b, ln=True)

    # Zertifikate
    if profil.get("zertifikate"):
        pdf.ln(3)
        pdf.set_fill_color(0, 70, 127)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "  ZERTIFIKATE", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 9)
        for z in profil["zertifikate"]:
            pdf.set_x(15)
            pdf.cell(5, 5, "-")
            pdf.cell(0, 5, z, ln=True)

    # Speichern
    pfad = os.path.join(
        user_daten_pfad(profil.get("vorname", "user").lower()),
        f"Lebenslauf_{profil.get('nachname', '')}.pdf"
    )
    pdf.output(pfad)
    return pfad


if __name__ == "__main__":
    profil = standard_profil()
    pfad = lebenslauf_aus_profil(profil)
    print(f"Lebenslauf erstellt: {pfad}")