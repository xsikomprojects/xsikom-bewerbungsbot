"""
XSI BOT - Automatischer Bewerbungs-Sender
- Findet Pratikum in allen Branchen
- Findet Jobs in allen Branchen
- Generiert KI-Anschreiben
- Sendet E-Mails mit allen Unterlagen
- Bulk-Bewerbungen
"""
import os
import sqlite3
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

DB_NAME = "bewerbungen.db"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# E-Mail Config
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_PASS = os.environ.get("GMAIL_PASS", "")
UPLOAD_FOLDER = "uploads"


# ============================================================
# XSI DATENBANK
# ============================================================
def xsi_db_init():
    """XSI Tabellen erstellen."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS xsi_bewerbungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pratikum_id INTEGER,
            firma TEXT,
            position TEXT,
            empfaenger_email TEXT,
            betreff TEXT,
            anschreiben TEXT,
            anhaenge TEXT,
            status TEXT DEFAULT 'erstellt',
            gesendet_am TEXT,
            antwort TEXT,
            erstellt_am TEXT,
            sprache TEXT DEFAULT 'de'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS xsi_bewerbungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_id INTEGER,
            firma TEXT,
            position TEXT,
            empfaenger_email TEXT,
            betreff TEXT,
            anschreiben TEXT,
            anhaenge TEXT,
            status TEXT DEFAULT 'erstellt',
            gesendet_am TEXT,
            antwort TEXT,
            erstellt_am TEXT,
            sprache TEXT DEFAULT 'de'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS xsi_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            betreff_template TEXT,
            anschreiben_template TEXT,
            sprache TEXT DEFAULT 'de',
            premium INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    xsi_templates_einfuegen()
    conn.close()


def xsi_templates_einfuegen():
    """Standard Betreff + Anschreiben Templates."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM xsi_templates")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    templates = [
        # DEUTSCH
        ("Klassisch DE", "Bewerbung als {position}", 
         "Sehr geehrte Damen und Herren,\n\nhiermit bewerbe ich mich um die ausgeschriebene Stelle als {position} bei {firma}.\n\n{ki_text}\n\nMeine Bewerbungsunterlagen finden Sie im Anhang.\n\nUeber eine Einladung zu einem persoenlichen Gespraech freue ich mich sehr.\n\nMit freundlichen Gruessen\n{name}\n\nAnlagen:\n- Lebenslauf\n- Zeugnisse\n- Zertifikate",
         "de", 0),

        ("Praktikum DE", "Bewerbung: Pflichtpraktikum als {position}",
         "Sehr geehrte Damen und Herren,\n\nmit grossem Interesse bewerbe ich mich um ein Praktikum als {position} bei {firma}.\n\n{ki_text}\n\nIm Anhang finden Sie meine vollstaendigen Bewerbungsunterlagen.\n\nMit freundlichen Gruessen\n{name}",
         "de", 0),

        ("IT Spezialist DE", "Bewerbung als {position} - IT-Fachtechniker",
         "Sehr geehrte Damen und Herren,\n\nals IT-Fachtechniker mit Erfahrung in Netzwerktechnik und Systemadministration bewerbe ich mich um die Position {position} bei {firma}.\n\n{ki_text}\n\nMeine Qualifikationen und Unterlagen entnehmen Sie dem Anhang.\n\nMit freundlichen Gruessen\n{name}",
         "de", 1),

        ("Initiativ DE", "Initiativbewerbung - {position}",
         "Sehr geehrte Damen und Herren,\n\nobwohl aktuell keine Stelle ausgeschrieben ist, moechte ich mich initiativ als {position} bei {firma} bewerben.\n\n{ki_text}\n\nMeine Unterlagen finden Sie im Anhang.\n\nMit freundlichen Gruessen\n{name}",
         "de", 1),

        ("Kurz & Knapp DE", "Bewerbung {position}",
         "Sehr geehrte Damen und Herren,\n\nhiermit bewerbe ich mich als {position}.\n\n{ki_text}\n\nMit freundlichen Gruessen\n{name}",
         "de", 0),

        # ENGLISH
        ("Classic EN", "Application for {position}",
         "Dear Sir or Madam,\n\nI am writing to apply for the position of {position} at {firma}.\n\n{ki_text}\n\nPlease find my application documents attached.\n\nI look forward to hearing from you.\n\nBest regards,\n{name}",
         "en", 0),

        ("IT Professional EN", "Application: {position} - IT Specialist",
         "Dear Hiring Manager,\n\nI am excited to apply for the {position} role at {firma}.\n\n{ki_text}\n\nMy resume and certificates are attached.\n\nBest regards,\n{name}",
         "en", 1),

        # FRANCAIS
        ("Classique FR", "Candidature: {position}",
         "Madame, Monsieur,\n\nJe me permets de vous adresser ma candidature pour le poste de {position} au sein de {firma}.\n\n{ki_text}\n\nVeuillez trouver ci-joint mon dossier de candidature.\n\nCordialement,\n{name}",
         "fr", 0),
    ]

    for t in templates:
        c.execute("""INSERT INTO xsi_templates 
            (name, betreff_template, anschreiben_template, sprache, premium)
            VALUES (?, ?, ?, ?, ?)""", t)

    conn.commit()
    conn.close()


# ============================================================
# XSI KI - ANSCHREIBEN GENERATOR
# ============================================================
def xsi_anschreiben_generieren(firma, position, profil, sprache="de"):
    """Generiert individuelles Anschreiben mit KI."""
    if not GROQ_API_KEY:
        return f"Hiermit bewerbe ich mich als {position} bei {firma}."

    sprache_text = {"de": "Deutsch", "en": "English", "fr": "Francais"}.get(sprache, "Deutsch")

    prompt = f"""Erstelle den HAUPTTEIL eines Bewerbungsanschreibens in {sprache_text}:

Firma: {firma}
Position: {position}

Bewerber:
Name: {profil.get('vorname', '')} {profil.get('nachname', '')}
Adresse: {profil.get('strasse', '')}, {profil.get('plz', '')} {profil.get('stadt', '')}
Kenntnisse: {profil.get('kenntnisse', '')}
Sprachen: {profil.get('sprachen', '')}

Schreibe NUR den Hauptteil (2-3 Absaetze):
- Warum diese Firma
- Welche Qualifikationen passen
- Was der Bewerber beitragen kann

Max 150 Woerter. In {sprache_text}. Kein Gruss, keine Anrede."""

    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}",
                     "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"Du bist ein Bewerbungs-Experte. Schreibe in {sprache_text}."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7, "max_tokens": 500
            },
            timeout=15
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return f"Bewerbung als {position} bei {firma}."
    except Exception:
        return f"Bewerbung als {position} bei {firma}."


def xsi_betreff_erstellen(template, firma, position, profil):
    """Erstellt individualisierten Betreff."""
    name = f"{profil.get('vorname', '')} {profil.get('nachname', '')}"
    return template.format(
        position=position,
        firma=firma,
        name=name
    )


def xsi_anschreiben_komplett(template, firma, position, profil, sprache="de"):
    """Erstellt komplettes Anschreiben mit KI-Text."""
    name = f"{profil.get('vorname', '')} {profil.get('nachname', '')}"
    ki_text = xsi_anschreiben_generieren(firma, position, profil, sprache)

    return template.format(
        position=position,
        firma=firma,
        name=name,
        ki_text=ki_text
    )


# ============================================================
# XSI E-MAIL SENDER
# ============================================================
def xsi_email_senden(empfaenger, betreff, anschreiben, user_id, profil):
    """Sendet Bewerbungs-E-Mail mit allen Unterlagen."""
    if not GMAIL_USER or not GMAIL_PASS:
        return False, "Gmail nicht konfiguriert. Setze GMAIL_USER und GMAIL_PASS."

    try:
        msg = MIMEMultipart()
        name = f"{profil.get('vorname', '')} {profil.get('nachname', '')}"
        msg["From"] = f"{name} <{GMAIL_USER}>"
        msg["To"] = empfaenger
        msg["Subject"] = betreff

        # HTML E-Mail Body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        {anschreiben.replace(chr(10), '<br>')}
        <hr style="margin-top: 30px; border: 1px solid #ddd;">
        <p style="font-size: 12px; color: #888;">
            Gesendet via XsiKOM-BewerbungsBOT<br>
            {profil.get('email', '')} | {profil.get('telefon', '')}
        </p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # ALLE Unterlagen des Users anhängen
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            "SELECT dateiname, pfad, kategorie FROM uploads WHERE user_id=? ORDER BY kategorie",
            (user_id,)
        )
        dateien = c.fetchall()
        conn.close()

        angehangen = []
        for dateiname, pfad, kategorie in dateien:
            if os.path.exists(pfad):
                try:
                    with open(pfad, "rb") as f:
                        teil = MIMEBase("application", "octet-stream")
                        teil.set_payload(f.read())
                    encoders.encode_base64(teil)

                    # Schöner Dateiname
                    kat_namen = {
                        "lebenslauf": f"Lebenslauf_{name.replace(' ', '_')}",
                        "zeugnis": f"Zeugnis_{name.replace(' ', '_')}",
                        "zertifikat": f"Zertifikat_{name.replace(' ', '_')}",
                        "bild": f"Bewerbungsfoto_{name.replace(' ', '_')}",
                        "anschreiben": f"Anschreiben_{name.replace(' ', '_')}",
                    }
                    ext = os.path.splitext(dateiname)[1]
                    anzeige_name = kat_namen.get(kategorie, dateiname) + ext

                    teil.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{anzeige_name}"'
                    )
                    msg.attach(teil)
                    angehangen.append(f"{kategorie}: {anzeige_name}")
                except Exception as e:
                    print(f"Anhang Fehler ({dateiname}): {e}")

        # Senden
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
        server.quit()

        return True, f"Gesendet! ({len(angehangen)} Anhaenge)"

    except smtplib.SMTPAuthenticationError:
        return False, "Gmail Authentifizierung fehlgeschlagen! App-Passwort pruefen."
    except Exception as e:
        return False, f"Fehler: {str(e)[:200]}"


# ============================================================
# XSI BEWERBUNG SPEICHERN
# ============================================================
def xsi_bewerbung_speichern(user_id, job_id, firma, position, 
                              empfaenger, betreff, anschreiben, 
                              status="erstellt", sprache="de"):
    """Speichert XSI Bewerbung in DB."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Anhaenge zusammenfassen
    c.execute(
        "SELECT dateiname, kategorie FROM uploads WHERE user_id=?",
        (user_id,)
    )
    dateien = c.fetchall()
    anhaenge_str = ", ".join([f"{d[1]}:{d[0]}" for d in dateien])

    c.execute("""
        INSERT INTO xsi_bewerbungen 
        (user_id, job_id, firma, position, empfaenger_email,
         betreff, anschreiben, anhaenge, status, erstellt_am, sprache)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, job_id, firma, position, empfaenger,
          betreff, anschreiben, anhaenge_str, status,
          datetime.now().isoformat(), sprache))

    bewerbung_id = c.lastrowid
    conn.commit()
    conn.close()
    return bewerbung_id


def xsi_bewerbung_status_update(bewerbung_id, status, details=""):
    """Aktualisiert Bewerbungs-Status."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if status == "gesendet":
        c.execute(
            "UPDATE xsi_bewerbungen SET status=?, gesendet_am=? WHERE id=?",
            (status, datetime.now().isoformat(), bewerbung_id)
        )
    else:
        c.execute(
            "UPDATE xsi_bewerbungen SET status=?, antwort=? WHERE id=?",
            (status, details, bewerbung_id)
        )
    conn.commit()
    conn.close()


def xsi_bewerbungen_laden(user_id, status=None):
    """Laedt XSI Bewerbungen."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if status:
        c.execute(
            "SELECT * FROM xsi_bewerbungen WHERE user_id=? AND status=? ORDER BY id DESC",
            (user_id, status)
        )
    else:
        c.execute(
            "SELECT * FROM xsi_bewerbungen WHERE user_id=? ORDER BY id DESC LIMIT 50",
            (user_id,)
        )
    rows = c.fetchall()
    conn.close()
    return rows


def xsi_templates_laden(sprache="de", premium=False):
    """Laedt E-Mail Templates."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        if premium:
            c.execute(
                "SELECT * FROM xsi_templates WHERE sprache=? ORDER BY premium, name",
                (sprache,)
            )
        else:
            c.execute(
                "SELECT * FROM xsi_templates WHERE sprache=? AND premium=0 ORDER BY name",
                (sprache,)
            )
        rows = c.fetchall()
        if not rows:
            c.execute("SELECT * FROM xsi_templates ORDER BY premium, name")
            rows = c.fetchall()
    except Exception:
        rows = []
    conn.close()
    return rows


def xsi_statistiken(user_id):
    """XSI Statistiken."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    stats = {}

    try:
        c.execute("SELECT COUNT(*) FROM xsi_bewerbungen WHERE user_id=?", (user_id,))
        stats["gesamt"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM xsi_bewerbungen WHERE user_id=? AND status='gesendet'", (user_id,))
        stats["gesendet"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM xsi_bewerbungen WHERE user_id=? AND status='erstellt'", (user_id,))
        stats["erstellt"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM xsi_bewerbungen WHERE user_id=? AND status='antwort'", (user_id,))
        stats["antworten"] = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM uploads WHERE user_id=?", (user_id,))
        stats["unterlagen"] = c.fetchone()[0]
    except Exception:
        stats = {"gesamt": 0, "gesendet": 0, "erstellt": 0, "antworten": 0, "unterlagen": 0}

    conn.close()
    return stats


def xsi_unterlagen_pruefen(user_id):
    """Prueft ob alle wichtigen Unterlagen vorhanden sind."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT kategorie FROM uploads WHERE user_id=?",
        (user_id,)
    )
    kategorien = [r[0] for r in c.fetchall()]
    conn.close()

    check = {
        "lebenslauf": "lebenslauf" in kategorien,
        "zeugnis": "zeugnis" in kategorien,
        "zertifikat": "zertifikat" in kategorien,
        "bild": "bild" in kategorien,
    }
    check["komplett"] = all(check.values())
    return check


# Init
xsi_db_init()