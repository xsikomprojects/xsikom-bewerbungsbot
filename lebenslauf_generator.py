from fpdf import FPDF
import os

UNTERLAGEN_PFAD = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "unterlagen"
)
os.makedirs(UNTERLAGEN_PFAD, exist_ok=True)


class MeinPDF(FPDF):

    def kopf(self, titel):
        self.set_fill_color(0, 70, 127)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 7, f"  {titel}", ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def zeile(self, links, rechts):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 70, 127)
        self.set_x(15)
        self.cell(45, 6, links)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, rechts)

    def text(self, inhalt):
        self.set_font("Helvetica", "", 9)
        self.set_x(15)
        self.multi_cell(0, 5, inhalt)
        self.ln(1)

    def punkt(self, punkte):
        self.set_font("Helvetica", "", 9)
        for p in punkte:
            self.set_x(15)
            self.cell(5, 5, "-")
            self.cell(0, 5, p, ln=True)
        self.ln(1)


def lebenslauf_erstellen():
    pdf = MeinPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # TITEL BLOCK
    pdf.set_fill_color(0, 70, 127)
    pdf.rect(0, 0, 210, 42, "F")
    pdf.set_xy(15, 7)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "Komi Tevi", ln=True)
    pdf.set_xy(15, 19)
    pdf.set_font("Helvetica", "I", 12)
    pdf.set_text_color(200, 225, 255)
    pdf.cell(0, 7, "IT-Fachtechniker  |  Netzwerktechniker", ln=True)
    pdf.set_xy(15, 29)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(
        0, 6,
        "Am Koenigsfloss 12, 55252 Mainz-Kastel  |  "
        "+49 178 8977320  |  xsikom.projects@gmail.com"
    )
    pdf.ln(20)

    # PERSÖNLICHE DATEN
    pdf.kopf("PERSOENLICHE DATEN")
    pdf.zeile("Geburtsdatum :", "29.11.1980")
    pdf.zeile("Geburtsort :", "Sika-Kondji, Togo")
    pdf.zeile("Familienstand :", "verheiratet")
    pdf.zeile("Staatsangeh. :", "deutsch")
    pdf.zeile("Fuehrerschein :", "Klasse B (PKW vorhanden)")
    pdf.ln(2)

    # PROFIL
    pdf.kopf("BERUFLICHES PROFIL")
    pdf.text(
        "Engagierter IT-Fachtechniker in Ausbildung mit fundierter "
        "Erfahrung als Computer-Techniker seit 1999. "
        "Umfangreiche Praxiserfahrung in Hardware-Wartung, "
        "Netzwerktechnik und Softwareinstallation. "
        "Zuverlaessig, lernbereit und hochmotiviert."
    )

    # AUSBILDUNG
    pdf.kopf("SCHULISCHE UND BERUFLICHE BILDUNG")
    pdf.zeile("seit 01.2026 :", "Ausbildung zum IT-Fachtechniker - BFW")
    pdf.zeile("07.2025-01.2026 :", "Reha-Vorbereitung - BFW")
    pdf.zeile("04.2006-12.2006 :", "Deutschkurs - Volkshochschule Greifswald")
    pdf.zeile("10.1999-10.2000 :", "Ausbildung Computertechniker - AC-INFORMATIQUE Lome/Togo")
    pdf.zeile("09.1986-06.1998 :", "Gymnasium LE GRAND-PLATEAU, Lome/Togo - Abitur")
    pdf.ln(2)

    # BERUFSERFAHRUNG
    pdf.kopf("BERUFLICHE ERFAHRUNG")
    pdf.zeile("12.2011-07.2025 :", "Logistiker & Admin Vertreter")
    pdf.text(
        "PROCTER & GAMBLE GmbH, Gross-Gerau\n"
        "- SAP & RTCIS Systeme\n"
        "- Administrative Aufgaben & Datenverwaltung"
    )
    pdf.zeile("07.2001-11.2003 :", "Computer-Techniker")
    pdf.text(
        "WANG-DATATECHNIQUE, Lome/Togo\n"
        "- Betreuung Computer & Netzsysteme\n"
        "- Softwareinstallation"
    )
    pdf.zeile("11.2003-12.2003 :", "Computer-Techniker - ONG-A.L.S.D, Lome/Togo")
    pdf.zeile("01.2001-06.2001 :", "Praktikum - NEAL-INFORMATIQUE, Lome/Togo")
    pdf.ln(2)

    # IT KENNTNISSE
    pdf.kopf("IT-KENNTNISSE")
    pdf.zeile("Betriebssysteme :", "Windows 10/11, Windows Server, Linux")
    pdf.zeile("Netzwerk :", "TCP/IP, VLAN, Routing, Switching")
    pdf.zeile("Software :", "MS-Office 365, SAP, RTCIS")
    pdf.zeile("Hardware :", "Wartung, Fehlerdiagnose, Reparatur")
    pdf.ln(2)

    # SPRACHEN
    pdf.kopf("SPRACHEN")
    pdf.zeile("Deutsch :", "B2 - Gute Kenntnisse")
    pdf.zeile("Franzoesisch :", "Fliessend (Muttersprache)")
    pdf.zeile("Englisch :", "A1 - Grundkenntnisse")
    pdf.ln(2)

    # SOFT SKILLS
    pdf.kopf("SOFT SKILLS")
    pdf.punkt([
        "Teamfaehigkeit & Kommunikationsstaerke",
        "Hohe Lernbereitschaft & Motivation",
        "Zuverlaessigkeit (13 Jahre bei PROCTER & GAMBLE)",
        "Interkulturelle Kompetenz",
        "Organisationstalent",
    ])

    # NUR generieren wenn keine echte Datei vorhanden
    pfad = os.path.join(UNTERLAGEN_PFAD, "lebenslauf_auto.pdf")
    pdf.output(pfad)
    print(f"  Auto-Lebenslauf erstellt: {pfad}")
    return pfad


def zeugnisse_erstellen():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(0, 70, 127)
    pdf.rect(0, 0, 210, 30, "F")
    pdf.set_xy(15, 10)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "ZEUGNISSE - Komi Tevi")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    for z in [
        "Abitur - Gymnasium LE GRAND-PLATEAU, Lome/Togo (1998)",
        "Abschluss Computertechniker - AC-INFORMATIQUE (2000)",
        "Arbeitszeugnis PROCTER & GAMBLE GmbH (2025)",
        "Deutschkurs B2 - Volkshochschule Greifswald",
        "Reha-Vorbereitung BFW (2025-2026)",
    ]:
        pdf.set_x(15)
        pdf.cell(5, 8, "-")
        pdf.cell(0, 8, z, ln=True)

    pfad = os.path.join(UNTERLAGEN_PFAD, "zeugnisse_auto.pdf")
    pdf.output(pfad)
    print(f"  Auto-Zeugnisse erstellt: {pfad}")
    return pfad


def zertifikate_erstellen():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(0, 70, 127)
    pdf.rect(0, 0, 210, 30, "F")
    pdf.set_xy(15, 10)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "ZERTIFIKATE - Komi Tevi")
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    for z in [
        "Abgeschlossene Ausbildung Computertechniker (2000)",
        "IT-Fachtechniker in Ausbildung - BFW (seit 2026)",
        "SAP Systemkenntnisse",
        "RTCIS Kenntnisse",
        "MS-Office 365",
        "Fuehrerschein Klasse B",
    ]:
        pdf.set_x(15)
        pdf.cell(5, 8, "-")
        pdf.cell(0, 8, z, ln=True)

    pfad = os.path.join(UNTERLAGEN_PFAD, "zertifikate.pdf")
    pdf.output(pfad)
    print(f"  Zertifikate erstellt: {pfad}")
    return pfad


def unterlagen_pruefen():
    """Prüft welche echten Unterlagen vorhanden sind."""
    print("\n  UNTERLAGEN UEBERSICHT")
    print("  " + "="*45)

    dateien = {
        "lebenslauf.pdf":  "Lebenslauf (deine echte Datei)",
        "zeugnisse.pdf":   "Zeugnisse (deine echte Datei)",
        "zertifikate.pdf": "Zertifikate",
    }

    alle_ok = True
    for datei, beschreibung in dateien.items():
        pfad = os.path.join(UNTERLAGEN_PFAD, datei)
        if os.path.exists(pfad):
            groesse = os.path.getsize(pfad)
            print(f"  OK  : {datei} ({groesse} Bytes)")
        else:
            print(f"  FEHLT: {datei} - {beschreibung}")
            alle_ok = False

    print("  " + "="*45)
    return alle_ok


if __name__ == "__main__":
    print("\n  UNTERLAGEN GENERATOR\n")
    unterlagen_pruefen()
    print("\n  Erstelle fehlende Dateien...")
    lebenslauf_erstellen()
    zeugnisse_erstellen()
    zertifikate_erstellen()
    print("\n  Fertig!")