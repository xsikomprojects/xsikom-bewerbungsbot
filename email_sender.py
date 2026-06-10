import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import (
    EMAIL_CONFIG, PERSOENLICHE_DATEN,
    UNTERLAGEN, PRAKTIKUM_CONFIG
)
from database import bewerbung_speichern
from telegram_sender import telegram_bewerbung_gesendet

# ============================================================
# BETREFF - Einheitlich für alle Bewerbungen
# ============================================================
BETREFF = (
    "Bewerbung: Pflichtpraktikum als "
    "IT-Fachtechniker / Netzwerktechniker"
)


def verbindung_testen():
    print("\n  E-Mail Verbindung wird getestet...")
    print(f"  Server : {EMAIL_CONFIG['smtp_server']}")
    print(f"  E-Mail : {EMAIL_CONFIG['email']}")
    try:
        s = smtplib.SMTP(
            EMAIL_CONFIG["smtp_server"],
            EMAIL_CONFIG["smtp_port"]
        )
        s.starttls()
        s.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["passwort"])
        s.quit()
        print("  Verbindung erfolgreich!")
        return True
    except smtplib.SMTPAuthenticationError:
        print("  Fehler: Authentifizierung fehlgeschlagen!")
        return False
    except Exception as e:
        print(f"  Fehler: {e}")
        return False


def bewerbung_senden(
    empfaenger,
    firma,
    position="IT-Fachtechniker / Netzwerktechniker",
    kontakt="",
    anschreiben_pfad=None,
    trockenlauf=False
):
    p = PERSOENLICHE_DATEN

    print(f"\n  {'='*55}")
    print(f"  Firma    : {firma}")
    print(f"  Position : {position}")
    print(f"  Betreff  : {BETREFF}")
    print(f"  An       : {empfaenger}")
    print(f"  {'='*55}")

    # E-Mail erstellen
    msg         = MIMEMultipart()
    msg["From"] = (
        f"{EMAIL_CONFIG['absender_name']} "
        f"<{EMAIL_CONFIG['email']}>"
    )
    msg["To"]      = empfaenger
    msg["Subject"] = BETREFF

    # Anrede
    if kontakt:
        anrede = f"Sehr geehrte/r {kontakt}"
    else:
        anrede = "Sehr geehrte Damen und Herren"

    # E-Mail Text HTML
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;
                 font-size: 14px;
                 color: #333;
                 line-height: 1.7;
                 max-width: 650px;">

    <p>{anrede},</p>

    <p>
    hiermit bewerbe ich mich um ein
    <strong>Pflichtpraktikum als
    IT-Fachtechniker / Netzwerktechniker</strong>
    bei <strong>{firma}</strong>.
    </p>

    <p>
    Als angehender IT-Fachtechniker in Ausbildung beim BFW
    bringe ich folgende Kenntnisse mit:
    </p>

    <ul>
        <li>Netzwerktechnik (TCP/IP, VLAN, Routing, Switching)</li>
        <li>Windows Server &amp; Active Directory</li>
        <li>Hardware-Wartung &amp; Fehlerdiagnose</li>
        <li>IT-Support &amp; Troubleshooting</li>
        <li>SAP &amp; MS-Office 365</li>
        <li>
            Praxiserfahrung als Computer-Techniker
            (seit 1999, Lome/Togo)
        </li>
    </ul>

    <p>
    Das <strong>Pflichtpraktikum</strong> soll
    <strong>{PRAKTIKUM_CONFIG['dauer']}</strong> umfassen.
    Mein fruehestmoeglicher Starttermin ist der
    <strong>{PRAKTIKUM_CONFIG['fruehester_start']}</strong>.
    </p>

    <p>
    Meine vollstaendigen Bewerbungsunterlagen
    (Anschreiben, Lebenslauf, Zeugnisse, Zertifikate)
    finden Sie im Anhang dieser E-Mail.
    </p>

    <p>
    Ueber eine Einladung zu einem Vorstellungsgespraech
    freue ich mich sehr.
    </p>

    <p>
    Mit freundlichen Gruessen<br><br>
    <strong>{p['vorname']} {p['nachname']}</strong><br>
    {p['strasse']}<br>
    {p['plz']} {p['stadt']}<br>
    Tel.: {p['telefon']}<br>
    E-Mail: {p['email']}
    </p>

    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html", "utf-8"))

    # ── ANHÄNGE ──────────────────────────────────────
    anhaenge = []

    # 1. Anschreiben
    if anschreiben_pfad and os.path.exists(anschreiben_pfad):
        anhaenge.append((
            "Anschreiben_Komi_Tevi.pdf",
            anschreiben_pfad
        ))

    # 2. Lebenslauf
    lauf_pfad = UNTERLAGEN.get("lebenslauf", "")
    if os.path.exists(lauf_pfad):
        anhaenge.append((
            "Lebenslauf_Komi_Tevi.pdf",
            lauf_pfad
        ))

    # 3. Zeugnisse
    zeug_pfad = UNTERLAGEN.get("zeugnisse", "")
    if os.path.exists(zeug_pfad):
        anhaenge.append((
            "Zeugnisse_Komi_Tevi.pdf",
            zeug_pfad
        ))

    # 4. Zertifikate
    zert_pfad = UNTERLAGEN.get("zertifikate", "")
    if os.path.exists(zert_pfad):
        anhaenge.append((
            "Zertifikate_Komi_Tevi.pdf",
            zert_pfad
        ))

    # Anhänge hinzufügen
    for dateiname, dateipfad in anhaenge:
        try:
            with open(dateipfad, "rb") as f:
                teil = MIMEBase("application", "octet-stream")
                teil.set_payload(f.read())
                encoders.encode_base64(teil)
                teil.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{dateiname}"'
                )
                msg.attach(teil)
                print(f"  Anhang: {dateiname}")
        except Exception as e:
            print(f"  Anhang Fehler: {e}")

    # ── TROCKENLAUF ──────────────────────────────────
    if trockenlauf:
        print("  TROCKENLAUF - E-Mail wird NICHT gesendet!")
        print(f"  Betreff waere: {BETREFF}")
        bewerbung_speichern(
            firma, position,
            empfaenger, "trockenlauf"
        )
        return True

    # ── SENDEN ───────────────────────────────────────
    try:
        s = smtplib.SMTP(
            EMAIL_CONFIG["smtp_server"],
            EMAIL_CONFIG["smtp_port"]
        )
        s.starttls()
        s.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["passwort"])
        s.send_message(msg)
        s.quit()

        bewerbung_speichern(
            firma, position,
            empfaenger, "gesendet"
        )
        telegram_bewerbung_gesendet(firma, position, empfaenger)

        print(f"  Bewerbung erfolgreich gesendet!")
        print(f"  Betreff: {BETREFF}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("  Fehler: App-Passwort pruefen!")
        bewerbung_speichern(firma, position, empfaenger, "fehler")
        return False

    except Exception as e:
        print(f"  Fehler: {e}")
        bewerbung_speichern(firma, position, empfaenger, "fehler")
        return False