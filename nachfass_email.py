"""
Automatische Nachfass-E-Mails nach 14 Tagen
"""
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_CONFIG, PERSOENLICHE_DATEN
from database import DB_NAME
from telegram_sender import telegram_senden
from whatsapp_sender import whatsapp_senden


def nachfass_email_erstellen(firma, kontakt=""):
    """Erstellt eine Nachfass-E-Mail."""
    p      = PERSOENLICHE_DATEN
    datum  = datetime.now().strftime("%d.%m.%Y")

    msg            = MIMEMultipart()
    msg["From"]    = (
        f"{EMAIL_CONFIG['absender_name']} "
        f"<{EMAIL_CONFIG['email']}>"
    )
    msg["Subject"] = (
        "Nachfrage: Bewerbung Pflichtpraktikum als "
        "IT-Fachtechniker / Netzwerktechniker"
    )

    if kontakt:
        anrede = f"Sehr geehrte/r {kontakt}"
    else:
        anrede = "Sehr geehrte Damen und Herren"

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;
                 font-size: 14px;
                 color: #333;
                 line-height: 1.7;
                 max-width: 650px;">

    <p>{anrede},</p>

    <p>
    vor etwa zwei Wochen habe ich mich bei Ihnen um ein
    <strong>Pflichtpraktikum als
    IT-Fachtechniker / Netzwerktechniker</strong>
    beworben. Ich moechte hiermit hoeflich nachfragen,
    ob meine Bewerbung eingegangen ist und wie der
    aktuelle Stand ist.
    </p>

    <p>
    Ich bin weiterhin sehr interessiert an einem
    Praktikumsplatz in Ihrem Unternehmen und stehe
    jederzeit fuer ein Vorstellungsgespraech zur Verfuegung.
    </p>

    <p>
    Mein fruehestmoeglicher Starttermin ist der
    <strong>01.03.2026</strong>.
    Das Praktikum soll <strong>3 Monate</strong> umfassen.
    </p>

    <p>
    Bei Rueckfragen stehe ich Ihnen gerne zur Verfuegung.
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
    return msg


def nachfass_email_senden(empfaenger, firma, kontakt=""):
    """Sendet eine Nachfass-E-Mail."""
    print(f"\n  Nachfass-E-Mail an {firma}...")

    msg         = nachfass_email_erstellen(firma, kontakt)
    msg["To"]   = empfaenger

    try:
        s = smtplib.SMTP(
            EMAIL_CONFIG["smtp_server"],
            EMAIL_CONFIG["smtp_port"]
        )
        s.starttls()
        s.login(EMAIL_CONFIG["email"], EMAIL_CONFIG["passwort"])
        s.send_message(msg)
        s.quit()

        print(f"  Nachfass-E-Mail gesendet: {firma}")

        # Datenbank aktualisieren
        conn = sqlite3.connect(DB_NAME)
        c    = conn.cursor()
        c.execute("""
            UPDATE tracker SET
                notizen = notizen || ' | Nachfass: ' || ?
            WHERE firma = ? AND email = ?
        """, (
            datetime.now().strftime("%d.%m.%Y"),
            firma, empfaenger
        ))
        conn.commit()
        conn.close()

        # Benachrichtigungen
        telegram_senden(
            f"<b>Nachfass-E-Mail gesendet!</b>\n\n"
            f"Firma : {firma}\n"
            f"An    : {empfaenger}\n"
            f"Zeit  : {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        whatsapp_senden(
            f"Nachfass-E-Mail gesendet!\n"
            f"Firma: {firma}"
        )

        return True

    except Exception as e:
        print(f"  Fehler: {e}")
        return False


def automatische_nachfass_pruefen():
    """
    Prueft alle Bewerbungen die aelter als 14 Tage sind
    und noch keine Antwort haben.
    Sendet automatisch Nachfass-E-Mails.
    """
    print("\n  Pruefe automatische Nachfass-E-Mails...")

    conn  = sqlite3.connect(DB_NAME)
    c     = conn.cursor()
    heute = datetime.now()

    # Tracker Tabelle pruefen
    try:
        c.execute("""
            SELECT id, firma, email, gesendet_am
            FROM tracker
            WHERE antwort_status = 'ausstehend'
            AND absage = 0
            AND erinnerung_2 = 1
        """)
        faellig = c.fetchall()
    except Exception:
        faellig = []

    conn.close()

    if not faellig:
        print("  Keine Nachfass-E-Mails faellig.")
        return 0

    gesendet = 0

    print(f"\n  {len(faellig)} Nachfass-E-Mails faellig:")
    print("  " + "="*45)

    for eintrag in faellig:
        tid          = eintrag[0]
        firma        = eintrag[1]
        email        = eintrag[2]
        gesendet_str = eintrag[3]

        try:
            gesendet_am = datetime.strptime(
                gesendet_str[:16], "%d.%m.%Y %H:%M"
            )
            tage = (heute - gesendet_am).days
        except Exception:
            tage = 0

        print(f"\n  Firma    : {firma}")
        print(f"  E-Mail   : {email}")
        print(f"  Gesendet : vor {tage} Tagen")

        best = input("  Nachfass senden? (ja/nein): ").strip().lower()

        if best in ["ja", "j"]:
            result = nachfass_email_senden(email, firma)
            if result:
                gesendet += 1

                # Tracker Update
                conn = sqlite3.connect(DB_NAME)
                c    = conn.cursor()
                c.execute(
                    "UPDATE tracker SET erinnerung_2=2 WHERE id=?",
                    (tid,)
                )
                conn.commit()
                conn.close()

    print(f"\n  {gesendet} Nachfass-E-Mails gesendet!")
    return gesendet


def nachfass_manuell():
    """Manuelle Nachfass-E-Mail senden."""
    print("\n  MANUELLE NACHFASS-E-MAIL")
    print("  " + "="*40)

    firma  = input("  Firma    : ").strip()
    email  = input("  E-Mail   : ").strip()
    kontakt = input("  Kontakt  : ").strip()

    if not firma or not email:
        print("  Firma und E-Mail erforderlich!")
        return

    best = input(f"\n  Nachfass an {firma} senden? (ja/nein): ").strip().lower()

    if best in ["ja", "j"]:
        nachfass_email_senden(email, firma, kontakt)
    else:
        print("  Abgebrochen.")


if __name__ == "__main__":
    automatische_nachfass_pruefen()