from fpdf import FPDF
from datetime import datetime
import os

ANSCHREIBEN_PFAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "anschreiben"
)
os.makedirs(ANSCHREIBEN_PFAD, exist_ok=True)

# ============================================================
# EINHEITLICHER BETREFF
# ============================================================
BETREFF = (
    "Bewerbung: Pflichtpraktikum als "
    "IT-Fachtechniker / Netzwerktechniker"
)

# ============================================================
# TEXTE JE NACH BEREICH
# ============================================================
TEXTE = {
    "netzwerk": {
        "intro": (
            "mit grossem Interesse bewerbe ich mich um ein "
            "Pflichtpraktikum als IT-Fachtechniker / "
            "Netzwerktechniker in Ihrem Unternehmen. "
            "Als angehender IT-Fachtechniker bringe ich "
            "fundierte Kenntnisse in TCP/IP, Routing und "
            "Netzwerkinfrastruktur mit."
        ),
        "haupt": (
            "In meiner Ausbildung zum IT-Fachtechniker beim BFW "
            "erwerbe ich Kenntnisse in der Konfiguration von "
            "Switches, Routern und Firewalls. "
            "Bereits als Computer-Techniker in Lome/Togo habe "
            "ich Netzwerksysteme betreut und konfiguriert."
        ),
    },
    "systemadmin": {
        "intro": (
            "mit grosser Begeisterung bewerbe ich mich um ein "
            "Pflichtpraktikum als IT-Fachtechniker / "
            "Netzwerktechniker in Ihrem Unternehmen. "
            "Als IT-Fachtechniker in Ausbildung bringe ich "
            "Kenntnisse in Windows Server, Active Directory "
            "und Linux mit."
        ),
        "haupt": (
            "Meine Ausbildung beim BFW umfasst Windows Server "
            "Administration, Active Directory und Virtualisierung. "
            "Meine 13-jaehrige Erfahrung bei PROCTER & GAMBLE "
            "hat mir tiefgreifende SAP-Kenntnisse vermittelt."
        ),
    },
    "support": {
        "intro": (
            "mit grossem Interesse bewerbe ich mich um ein "
            "Pflichtpraktikum als IT-Fachtechniker / "
            "Netzwerktechniker in Ihrem Unternehmen. "
            "Als kommunikativer IT-Fachtechniker in Ausbildung "
            "bringe ich die richtigen Eigenschaften fuer "
            "einen erfolgreichen IT-Support mit."
        ),
        "haupt": (
            "Bereits als Computer-Techniker in Lome/Togo habe "
            "ich Nutzer betreut, Systeme gewartet und technische "
            "Probleme geloest. Meine Erfahrung umfasst "
            "Hardware-Diagnose, Softwareinstallation und "
            "Anwender-Unterstuetzung."
        ),
    },
    "allgemein": {
        "intro": (
            "mit grossem Interesse bewerbe ich mich um ein "
            "Pflichtpraktikum als IT-Fachtechniker / "
            "Netzwerktechniker in Ihrem Unternehmen. "
            "Als engagierter IT-Fachtechniker in Ausbildung "
            "moechte ich meine Kenntnisse in einem "
            "professionellen Umfeld einsetzen."
        ),
        "haupt": (
            "In meiner Ausbildung beim BFW erwerbe ich "
            "Kenntnisse in Netzwerktechnik, Systemadministration "
            "und IT-Support. Ergaenzend bringe ich praktische "
            "Erfahrung als Computer-Techniker sowie 13 Jahre "
            "Berufserfahrung bei PROCTER & GAMBLE mit."
        ),
    },
}


def anschreiben_erstellen(
    firma,
    position="IT-Fachtechniker / Netzwerktechniker",
    kontakt="",
    bereich="allgemein"
):
    """Erstellt ein individuelles Anschreiben als PDF."""

    vorlage = TEXTE.get(bereich, TEXTE["allgemein"])
    datum   = datetime.now().strftime("%d.%m.%Y")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # ── ABSENDER ─────────────────────────────────────
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 70, 127)
    pdf.cell(0, 6, "Komi Tevi", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, "Am Koenigsfloss 12", ln=True)
    pdf.cell(0, 5, "55252 Mainz-Kastel", ln=True)
    pdf.cell(0, 5, "Tel.: +49 178 8977320", ln=True)
    pdf.cell(0, 5, "E-Mail: xsikom.projects@gmail.com", ln=True)
    pdf.ln(8)

    # ── EMPFÄNGER ────────────────────────────────────
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 5, firma, ln=True)
    if kontakt:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 5, f"z.Hd. {kontakt}", ln=True)
    pdf.ln(6)

    # ── DATUM ────────────────────────────────────────
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0, 5,
        f"Mainz-Kastel, {datum}",
        ln=True, align="R"
    )
    pdf.ln(6)

    # ── BETREFF ──────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 70, 127)
    pdf.cell(0, 6, BETREFF, ln=True)
    pdf.ln(5)

    # ── ANREDE ───────────────────────────────────────
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    if kontakt:
        pdf.cell(0, 6, f"Sehr geehrte/r {kontakt},", ln=True)
    else:
        pdf.cell(0, 6, "Sehr geehrte Damen und Herren,", ln=True)
    pdf.ln(4)

    # ── EINLEITUNG ───────────────────────────────────
    pdf.multi_cell(0, 6, vorlage["intro"])
    pdf.ln(3)

    # ── HAUPTTEIL ────────────────────────────────────
    pdf.multi_cell(0, 6, vorlage["haupt"])
    pdf.ln(3)

    # ── KENNTNISSE ───────────────────────────────────
    pdf.multi_cell(
        0, 6,
        "Meine fachlichen Kenntnisse umfassen:"
    )
    pdf.ln(2)

    for k in [
        "Netzwerktechnik (TCP/IP, VLAN, Routing, Switching)",
        "Windows Server & Active Directory",
        "Hardware-Wartung & Fehlerdiagnose",
        "IT-Support & Troubleshooting",
        "SAP & MS-Office 365",
        "Softwareinstallation & Systembetreuung",
    ]:
        pdf.set_x(15)
        pdf.cell(5, 5, "-")
        pdf.cell(0, 5, k, ln=True)
    pdf.ln(3)

    # ── MOTIVATION ───────────────────────────────────
    pdf.multi_cell(
        0, 6,
        f"Ein Praktikum bei {firma} bietet mir die ideale "
        "Moeglichkeit, meine Kenntnisse in der Praxis "
        "anzuwenden und weiterzuentwickeln. "
        "Ich bin ueberzeugt, dass ich durch meine Motivation "
        "und Lernbereitschaft einen wertvollen Beitrag "
        "zu Ihrem Team leisten kann."
    )
    pdf.ln(3)

    # ── ABSCHLUSS ────────────────────────────────────
    pdf.multi_cell(
        0, 6,
        "Das Pflichtpraktikum soll 3 Monate umfassen. "
        "Mein fruehestmoeglicher Starttermin ist "
        "der 01.03.2026. "
        "Ueber eine Einladung zu einem "
        "Vorstellungsgespraech freue ich mich sehr."
    )
    pdf.ln(5)

    # ── GRUSS ────────────────────────────────────────
    pdf.cell(0, 6, "Mit freundlichen Gruessen", ln=True)
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Komi Tevi", ln=True)
    pdf.ln(4)

    # ── ANLAGEN ──────────────────────────────────────
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, "Anlagen:", ln=True)
    pdf.cell(0, 4, "  - Lebenslauf", ln=True)
    pdf.cell(0, 4, "  - Zeugnisse", ln=True)
    pdf.cell(0, 4, "  - Zertifikate", ln=True)

    # ── SPEICHERN ────────────────────────────────────
    firma_clean = (
        firma
        .replace(" ", "_")
        .replace("/", "-")
        .replace(".", "")
        .replace(",", "")
    )
    dateiname = (
        f"Anschreiben_{firma_clean}_"
        f"{datum.replace('.','')}.pdf"
    )
    pfad = os.path.join(ANSCHREIBEN_PFAD, dateiname)
    pdf.output(pfad)

    print(f"  Anschreiben erstellt: {dateiname}")
    return pfad


if __name__ == "__main__":
    print("\n  Teste Anschreiben Generator...")
    pfad = anschreiben_erstellen(
        firma="IT Solutions GmbH",
        position="IT-Fachtechniker / Netzwerktechniker",
        bereich="allgemein"
    )
    print(f"\n  Betreff: {BETREFF}")
    print(f"  Gespeichert: {pfad}")
    print("\n  Test erfolgreich!")