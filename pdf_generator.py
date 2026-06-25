"""
XsiKOM PDF-Lebenslauf Generator
5 professionelle Vorlagen
"""
import os
import sqlite3
from datetime import datetime
from fpdf import FPDF

DB_NAME = "bewerbungen.db"
PDF_FOLDER = "generated_pdfs"
os.makedirs(PDF_FOLDER, exist_ok=True)


class LebenslaufPDF(FPDF):

    def __init__(self, vorlage="modern"):
        super().__init__()
        self.vorlage = vorlage
        self.set_auto_page_break(auto=True, margin=20)

    def kopf(self, titel, farbe=(0, 70, 127)):
        self.set_fill_color(*farbe)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, f"  {titel}", ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def zeile(self, links, rechts):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 70, 127)
        self.set_x(15)
        self.cell(45, 6, links)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, rechts)

    def punkt(self, punkte):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        for p in punkte:
            if p.strip():
                self.set_x(15)
                self.cell(5, 5, "-")
                self.cell(0, 5, p.strip(), ln=True)
        self.ln(1)


def vorlage_modern(profil):
    """Moderne Vorlage mit blauem Header."""
    pdf = LebenslaufPDF("modern")
    pdf.add_page()

    # Header
    pdf.set_fill_color(0, 100, 180)
    pdf.rect(0, 0, 210, 40, "F")
    pdf.set_xy(15, 8)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    name = f"{profil.get('vorname', '')} {profil.get('nachname', '')}"
    pdf.cell(0, 10, name, ln=True)
    pdf.set_xy(15, 20)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(200, 220, 255)
    kontakt = f"{profil.get('email', '')}  |  {profil.get('telefon', '')}  |  {profil.get('stadt', '')}"
    pdf.cell(0, 6, kontakt)
    if profil.get("strasse"):
        pdf.set_xy(15, 28)
        pdf.cell(0, 6, f"{profil.get('strasse', '')}, {profil.get('plz', '')} {profil.get('stadt', '')}")
    pdf.ln(20)

    # Persoenliche Daten
    pdf.kopf("PERSOENLICHE DATEN")
    if profil.get("geburtsdatum"):
        pdf.zeile("Geburtsdatum:", profil["geburtsdatum"])

    # Kenntnisse
    if profil.get("kenntnisse"):
        pdf.kopf("KENNTNISSE & FAEHIGKEITEN")
        pdf.punkt(profil["kenntnisse"].split("\n"))

    # Sprachen
    if profil.get("sprachen"):
        pdf.kopf("SPRACHEN")
        pdf.punkt(profil["sprachen"].split("\n"))

    return pdf


def vorlage_klassisch(profil):
    """Klassische schwarz-weiss Vorlage."""
    pdf = LebenslaufPDF("klassisch")
    pdf.add_page()

    # Name
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(0, 0, 0)
    name = f"{profil.get('vorname', '')} {profil.get('nachname', '')}"
    pdf.cell(0, 12, name, ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    kontakt = f"{profil.get('email', '')} | {profil.get('telefon', '')} | {profil.get('stadt', '')}"
    pdf.cell(0, 6, kontakt, ln=True, align="C")
    pdf.ln(5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    pdf.kopf("PERSOENLICHE DATEN", (50, 50, 50))
    if profil.get("geburtsdatum"):
        pdf.zeile("Geburtsdatum:", profil["geburtsdatum"])
    if profil.get("strasse"):
        pdf.zeile("Adresse:", f"{profil['strasse']}, {profil.get('plz','')} {profil.get('stadt','')}")

    if profil.get("kenntnisse"):
        pdf.kopf("KENNTNISSE", (50, 50, 50))
        pdf.punkt(profil["kenntnisse"].split("\n"))

    if profil.get("sprachen"):
        pdf.kopf("SPRACHEN", (50, 50, 50))
        pdf.punkt(profil["sprachen"].split("\n"))

    return pdf


def vorlage_kreativ(profil):
    """Kreative Vorlage mit Farben."""
    pdf = LebenslaufPDF("kreativ")
    pdf.add_page()

    # Sidebar simulieren
    pdf.set_fill_color(0, 180, 216)
    pdf.rect(0, 0, 70, 297, "F")

    # Name in Sidebar
    pdf.set_xy(5, 15)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(60, 8, profil.get("vorname", ""), ln=True, align="C")
    pdf.set_x(5)
    pdf.cell(60, 8, profil.get("nachname", ""), ln=True, align="C")

    # Kontakt in Sidebar
    pdf.set_xy(5, 40)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(60, 5, profil.get("email", ""), ln=True, align="C")
    pdf.set_x(5)
    pdf.cell(60, 5, profil.get("telefon", ""), ln=True, align="C")
    pdf.set_x(5)
    pdf.cell(60, 5, profil.get("stadt", ""), ln=True, align="C")

    # Sprachen in Sidebar
    if profil.get("sprachen"):
        pdf.set_xy(5, 70)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(60, 6, "SPRACHEN", ln=True, align="C")
        pdf.set_font("Helvetica", "", 8)
        for s in profil["sprachen"].split("\n"):
            if s.strip():
                pdf.set_x(5)
                pdf.cell(60, 5, s.strip(), ln=True, align="C")

    # Hauptbereich
    pdf.set_xy(75, 15)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "PROFIL", ln=True)
    pdf.set_x(75)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(120, 5, f"Motivierter Fachmann mit Kenntnissen in {profil.get('kenntnisse', '')[:100]}...")

    if profil.get("kenntnisse"):
        pdf.set_x(75)
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "KENNTNISSE", ln=True)
        pdf.set_font("Helvetica", "", 9)
        for k in profil["kenntnisse"].split("\n"):
            if k.strip():
                pdf.set_x(75)
                pdf.cell(5, 5, "-")
                pdf.cell(0, 5, k.strip(), ln=True)

    return pdf


def vorlage_minimal(profil):
    """Minimale saubere Vorlage."""
    pdf = LebenslaufPDF("minimal")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 30, 30)
    name = f"{profil.get('vorname', '')} {profil.get('nachname', '')}"
    pdf.cell(0, 14, name, ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"{profil.get('email','')} | {profil.get('telefon','')} | {profil.get('stadt','')}", ln=True)
    pdf.ln(8)

    if profil.get("kenntnisse"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, "Kenntnisse", ln=True)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        for k in profil["kenntnisse"].split("\n"):
            if k.strip():
                pdf.set_x(15)
                pdf.cell(0, 5, f"• {k.strip()}", ln=True)
        pdf.ln(5)

    if profil.get("sprachen"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, "Sprachen", ln=True)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        for s in profil["sprachen"].split("\n"):
            if s.strip():
                pdf.set_x(15)
                pdf.cell(0, 5, f"• {s.strip()}", ln=True)

    return pdf


def vorlage_executive(profil):
    """Executive/Premium Vorlage."""
    pdf = LebenslaufPDF("executive")
    pdf.add_page()

    # Dunkelblauer Header
    pdf.set_fill_color(20, 40, 80)
    pdf.rect(0, 0, 210, 50, "F")

    # Gold Linie
    pdf.set_fill_color(218, 165, 32)
    pdf.rect(0, 50, 210, 3, "F")

    pdf.set_xy(15, 10)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(255, 255, 255)
    name = f"{profil.get('vorname', '')} {profil.get('nachname', '')}"
    pdf.cell(0, 12, name, ln=True)

    pdf.set_xy(15, 26)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(218, 165, 32)
    pdf.cell(0, 6, profil.get("email", ""), ln=True)
    pdf.set_xy(15, 34)
    pdf.cell(0, 6, f"{profil.get('telefon','')} | {profil.get('stadt','')}")
    pdf.ln(25)

    pdf.set_text_color(20, 40, 80)
    pdf.kopf("QUALIFIKATIONEN", (20, 40, 80))
    if profil.get("kenntnisse"):
        pdf.punkt(profil["kenntnisse"].split("\n"))

    pdf.kopf("SPRACHEN", (20, 40, 80))
    if profil.get("sprachen"):
        pdf.punkt(profil["sprachen"].split("\n"))

    return pdf


VORLAGEN = {
    "modern": {"name": "Modern", "icon": "🎨", "func": vorlage_modern, "premium": False},
    "klassisch": {"name": "Klassisch", "icon": "📄", "func": vorlage_klassisch, "premium": False},
    "kreativ": {"name": "Kreativ", "icon": "🌈", "func": vorlage_kreativ, "premium": True},
    "minimal": {"name": "Minimal", "icon": "✨", "func": vorlage_minimal, "premium": True},
    "executive": {"name": "Executive", "icon": "👔", "func": vorlage_executive, "premium": True},
}


def lebenslauf_generieren(user_id, vorlage_key="modern"):
    """Generiert PDF-Lebenslauf aus Profil."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM profile WHERE user_id=?", (user_id,))
    r = c.fetchone()
    conn.close()

    if not r:
        return None

    profil = {
        "vorname": r[1] or "", "nachname": r[2] or "",
        "strasse": r[3] or "", "plz": r[4] or "",
        "stadt": r[5] or "", "telefon": r[6] or "",
        "email": r[7] or "", "geburtsdatum": r[8] or "",
        "kenntnisse": r[9] or "", "sprachen": r[10] or ""
    }

    vorlage = VORLAGEN.get(vorlage_key, VORLAGEN["modern"])
    pdf = vorlage["func"](profil)

    user_folder = os.path.join(PDF_FOLDER, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_clean = f"{profil['vorname']}_{profil['nachname']}".replace(" ", "_")
    dateiname = f"Lebenslauf_{name_clean}_{vorlage_key}_{ts}.pdf"
    pfad = os.path.join(user_folder, dateiname)

    pdf.output(pfad)
    return pfad, dateiname


def vorlagen_info():
    """Gibt Vorlagen-Info zurueck."""
    return VORLAGEN