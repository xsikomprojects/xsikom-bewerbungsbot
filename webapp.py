"""
XsiKOM-BewerbungsBOT
Modern 3D Smart Design
"""
import os
import sqlite3
import hashlib
import secrets
import random
import requests
from datetime import datetime, timedelta
from flask import (
    Flask, render_template_string, request,
    redirect, session, send_from_directory,
    send_file, make_response
)
from werkzeug.utils import secure_filename
from PIL import Image


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(hours=2)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

DB_NAME = "bewerbungen.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "bmp", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CONTACT_EMAIL = "xsikom_digital@xsikom.de"

# ============================================================
# KI
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """Du bist Aaliyah, professionelle KI-Karriereberaterin fuer IT-Bewerber.
Spezialgebiete: IT-Praktika, Netzwerktechnik, Systemadmin, Fachinformatiker.
Antworte auf Deutsch, freundlich, 3-5 Saetze."""


def get_ki_antwort(frage):
    if not GROQ_API_KEY:
        return "Hallo! KI gerade offline. Bitte spaeter probieren."
    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": frage}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=20
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return "Entschuldigung, etwas ist schiefgelaufen."
    except Exception:
        return "KI-Verbindung fehlgeschlagen."


AALIYAH_TIPPS = [
    "Passe dein Anschreiben immer an die konkrete Stelle an!",
    "Erwaehne im Anschreiben konkrete Projekte der Firma.",
    "Halte dein Anschreiben auf maximal eine Seite.",
    "Zeige Motivation - warum genau diese Firma?",
    "Pruefe deine E-Mail auf Rechtschreibung vor dem Senden.",
]


def aaliyah_tipp():
    return random.choice(AALIYAH_TIPPS)


# ============================================================
# DATENBANK
# ============================================================
def db_init():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS benutzer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzername TEXT UNIQUE NOT NULL,
            passwort TEXT NOT NULL,
            email TEXT, vorname TEXT, nachname TEXT,
            rolle TEXT DEFAULT 'user',
            premium INTEGER DEFAULT 0,
            kunde_typ TEXT DEFAULT 'privat',
            erstellt TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bewerbungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, firma TEXT, email TEXT,
            status TEXT DEFAULT 'gesendet', datum TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            user_id INTEGER PRIMARY KEY,
            vorname TEXT, nachname TEXT, strasse TEXT,
            plz TEXT, stadt TEXT, telefon TEXT,
            email TEXT, geburtsdatum TEXT,
            kenntnisse TEXT, sprachen TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, dateiname TEXT, typ TEXT,
            kategorie TEXT, pfad TEXT, upload_datum TEXT
        )
    """)
    conn.commit()
    conn.close()


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def admin_anlegen():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM benutzer WHERE benutzername='admin'")
    if not c.fetchone():
        c.execute("""
            INSERT INTO benutzer
            (benutzername, passwort, email, vorname, nachname, rolle, premium, erstellt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "admin", hash_pw("XsiKOM2026!"),
            CONTACT_EMAIL, "Komi", "Tevi",
            "admin", 1, datetime.now().isoformat()
        ))
        conn.commit()
    conn.close()


def benutzer_pruefen(user, pw):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id, benutzername, vorname, nachname, rolle, premium "
        "FROM benutzer WHERE benutzername=? AND passwort=?",
        (user, hash_pw(pw))
    )
    r = c.fetchone()
    conn.close()
    if r:
        return {
            "id": r[0], "benutzername": r[1],
            "vorname": r[2], "nachname": r[3],
            "rolle": r[4], "premium": r[5]
        }
    return None


def benutzer_anlegen(user, pw, email, vn, nn, kunde_typ="privat"):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            INSERT INTO benutzer
            (benutzername, passwort, email, vorname, nachname, kunde_typ, erstellt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user, hash_pw(pw), email, vn, nn, kunde_typ, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def premium_aktivieren(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE benutzer SET premium=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def bewerbungen_zaehlen(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    monat_start = datetime.now().replace(day=1).isoformat()
    c.execute(
        "SELECT COUNT(*) FROM bewerbungen WHERE user_id=? AND datum >= ?",
        (user_id, monat_start)
    )
    n = c.fetchone()[0]
    conn.close()
    return n


def profil_laden(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM profile WHERE user_id=?", (user_id,))
    r = c.fetchone()
    conn.close()
    if not r:
        return {}
    return {
        "vorname": r[1] or "", "nachname": r[2] or "",
        "strasse": r[3] or "", "plz": r[4] or "",
        "stadt": r[5] or "", "telefon": r[6] or "",
        "email": r[7] or "", "geburtsdatum": r[8] or "",
        "kenntnisse": r[9] or "", "sprachen": r[10] or ""
    }


def profil_speichern(user_id, daten):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM profile WHERE user_id=?", (user_id,))
    c.execute("""
        INSERT INTO profile
        (user_id, vorname, nachname, strasse, plz, stadt,
         telefon, email, geburtsdatum, kenntnisse, sprachen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, daten.get("vorname",""), daten.get("nachname",""),
        daten.get("strasse",""), daten.get("plz",""),
        daten.get("stadt",""), daten.get("telefon",""),
        daten.get("email",""), daten.get("geburtsdatum",""),
        daten.get("kenntnisse",""), daten.get("sprachen","")
    ))
    conn.commit()
    conn.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def datei_speichern(file, user_id, kategorie):
    if not file or not allowed_file(file.filename):
        return None
    user_folder = os.path.join(UPLOAD_FOLDER, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    ext_lower = ext.lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    neuer_name = f"{kategorie}_{timestamp}{ext_lower}"
    pfad = os.path.join(user_folder, neuer_name)

    if ext_lower in [".png", ".gif", ".bmp", ".webp"] and kategorie == "bild":
        try:
            img = Image.open(file.stream)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            neuer_name = f"{kategorie}_{timestamp}.jpg"
            pfad = os.path.join(user_folder, neuer_name)
            img.save(pfad, "JPEG", quality=90, optimize=True)
        except Exception:
            file.seek(0)
            file.save(pfad)
    else:
        file.save(pfad)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO uploads (user_id, dateiname, typ, kategorie, pfad, upload_datum)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, neuer_name, ext_lower, kategorie, pfad, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return neuer_name


def uploads_laden(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id, dateiname, typ, kategorie, pfad, upload_datum "
        "FROM uploads WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def upload_loeschen(upload_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT pfad FROM uploads WHERE id=? AND user_id=?", (upload_id, user_id))
    r = c.fetchone()
    if r and os.path.exists(r[0]):
        try:
            os.remove(r[0])
        except Exception:
            pass
    c.execute("DELETE FROM uploads WHERE id=? AND user_id=?", (upload_id, user_id))
    conn.commit()
    conn.close()


# ============================================================
# MODERN 3D DESIGN TEMPLATE
# ============================================================
BASE_HTML = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XsiKOM - KI Bewerbungs-Assistent</title>

    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#00D9FF">
    <link rel="icon" type="image/png" href="/static/icon-192.png">

    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">

    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/sw.js');
            });
        }

        function cookieAccept() {
            localStorage.setItem('cookie_ok', 'yes');
            document.getElementById('cookie-banner').style.display = 'none';
        }

        window.addEventListener('load', function() {
            if (localStorage.getItem('cookie_ok') !== 'yes') {
                var b = document.getElementById('cookie-banner');
                if (b) b.style.display = 'block';
            }
        });

        function toggleMenu() {
            var m = document.getElementById('mobile-menu');
            m.classList.toggle('open');
        }
    </script>

    <style>
        * { 
            margin: 0; padding: 0; box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        :root {
            --bg-primary: #0A0E1A;
            --bg-secondary: #131829;
            --bg-card: rgba(20, 28, 48, 0.6);
            --bg-glass: rgba(255, 255, 255, 0.03);
            --border: rgba(255, 255, 255, 0.08);
            --accent-cyan: #00D9FF;
            --accent-purple: #8B5CF6;
            --accent-pink: #EC4899;
            --accent-green: #10F4B1;
            --accent-yellow: #FFD93D;
            --accent-red: #FF4757;
            --text-primary: #FFFFFF;
            --text-secondary: #A0AEC0;
            --text-muted: #6B7280;
        }

        body {
            font-family: 'Poppins', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }

        /* Animierter Hintergrund */
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: 
                radial-gradient(circle at 20% 20%, rgba(0, 217, 255, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.08) 0%, transparent 50%);
            z-index: -1;
            animation: bgMove 20s ease infinite;
        }

        @keyframes bgMove {
            0%, 100% { transform: scale(1) rotate(0deg); }
            50% { transform: scale(1.1) rotate(2deg); }
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        .header {
            background: rgba(10, 14, 26, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 20px 0;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        }

        .header-inner {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 30px rgba(0, 217, 255, 0.3);
            cursor: pointer;
            letter-spacing: -1px;
        }

        .subtitle {
            color: var(--text-secondary);
            font-size: 13px;
            margin-top: 2px;
            font-weight: 400;
        }

        /* Navigation */
        .nav {
            background: rgba(19, 24, 41, 0.5);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
            overflow-x: auto;
            white-space: nowrap;
            scrollbar-width: none;
        }
        .nav::-webkit-scrollbar { display: none; }

        .nav-inner {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            gap: 5px;
        }

        .nav a {
            color: var(--text-secondary);
            text-decoration: none;
            padding: 10px 18px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .nav a:hover {
            color: var(--text-primary);
            background: rgba(0, 217, 255, 0.1);
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 217, 255, 0.2);
        }

        /* Cards - 3D Glass Effekt */
        .card {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            margin: 20px 0;
            border: 1px solid var(--border);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent, 
                var(--accent-cyan), 
                var(--accent-purple), 
                transparent);
            opacity: 0.5;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 
                0 20px 40px rgba(0, 217, 255, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
            border-color: rgba(0, 217, 255, 0.3);
        }

        /* Buttons - 3D Modern */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 14px 28px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            text-decoration: none;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            font-family: 'Poppins', sans-serif;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(255, 255, 255, 0.2), 
                transparent);
            transition: left 0.5s;
        }

        .btn:hover::before { left: 100%; }

        .btn:hover {
            transform: translateY(-2px);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-cyan), #0099CC);
            color: white;
            box-shadow: 0 4px 20px rgba(0, 217, 255, 0.3);
        }

        .btn-primary:hover {
            box-shadow: 0 6px 25px rgba(0, 217, 255, 0.5);
        }

        .btn-success {
            background: linear-gradient(135deg, var(--accent-green), #059669);
            color: white;
            box-shadow: 0 4px 20px rgba(16, 244, 177, 0.3);
        }

        .btn-success:hover {
            box-shadow: 0 6px 25px rgba(16, 244, 177, 0.5);
        }

        .btn-warning {
            background: linear-gradient(135deg, var(--accent-yellow), #F59E0B);
            color: #0A0E1A;
            box-shadow: 0 4px 20px rgba(255, 217, 61, 0.3);
        }

        .btn-warning:hover {
            box-shadow: 0 6px 25px rgba(255, 217, 61, 0.5);
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--accent-red), #DC2626);
            color: white;
            box-shadow: 0 4px 20px rgba(255, 71, 87, 0.3);
        }

        .btn-purple {
            background: linear-gradient(135deg, var(--accent-purple), #6D28D9);
            color: white;
            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.3);
        }

        /* Input Fields - Modern */
        input, textarea, select {
            background: rgba(10, 14, 26, 0.6);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 14px 18px;
            border-radius: 12px;
            width: 100%;
            margin-bottom: 12px;
            font-size: 14px;
            font-family: 'Poppins', sans-serif;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--accent-cyan);
            box-shadow: 
                0 0 0 4px rgba(0, 217, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }

        input::placeholder, textarea::placeholder {
            color: var(--text-muted);
        }

        /* Headings */
        h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 36px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
            letter-spacing: -1px;
        }

        h2 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 26px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
        }

        h3 {
            font-family: 'Poppins', sans-serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--accent-cyan);
            margin-bottom: 12px;
        }

        p {
            line-height: 1.7;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }

        a {
            color: var(--accent-cyan);
            text-decoration: none;
            transition: color 0.3s;
        }

        a:hover { color: var(--accent-purple); }

        /* Grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
        }

        /* Stat Cards - 3D mit Glow */
        .stat-card {
            background: linear-gradient(135deg, 
                rgba(20, 28, 48, 0.8), 
                rgba(30, 38, 58, 0.6));
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            position: relative;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            overflow: hidden;
        }

        .stat-card::after {
            content: '';
            position: absolute;
            top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle, 
                var(--accent-cyan) 0%, 
                transparent 70%);
            opacity: 0;
            transition: opacity 0.4s;
        }

        .stat-card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: var(--accent-cyan);
            box-shadow: 
                0 25px 50px rgba(0, 217, 255, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.15);
        }

        .stat-card:hover::after { opacity: 0.05; }

        .stat-icon {
            font-size: 48px;
            margin-bottom: 12px;
            display: inline-block;
            filter: drop-shadow(0 4px 20px rgba(0, 217, 255, 0.4));
        }

        .stat-value {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 13px;
            margin-top: 4px;
        }

        /* Badge */
        .badge {
            background: linear-gradient(135deg, var(--accent-yellow), var(--accent-pink));
            color: var(--bg-primary);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            display: inline-block;
            box-shadow: 0 4px 15px rgba(255, 217, 61, 0.3);
        }

        /* Status Indicator */
        .status-online {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            background: rgba(16, 244, 177, 0.1);
            border: 1px solid rgba(16, 244, 177, 0.3);
            border-radius: 20px;
            color: var(--accent-green);
            font-size: 12px;
            font-weight: 600;
        }

        .status-online::before {
            content: '';
            width: 8px; height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-green);
            animation: pulse 2s infinite;
        }

        .status-offline {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            background: rgba(255, 71, 87, 0.1);
            border: 1px solid rgba(255, 71, 87, 0.3);
            border-radius: 20px;
            color: var(--accent-red);
            font-size: 12px;
            font-weight: 600;
        }

        .status-offline::before {
            content: '';
            width: 8px; height: 8px;
            background: var(--accent-red);
            border-radius: 50%;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.2); }
        }

        /* Alerts */
        .alert {
            padding: 16px 20px;
            border-radius: 12px;
            margin: 16px 0;
            backdrop-filter: blur(10px);
            border: 1px solid;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .alert-ok {
            background: rgba(16, 244, 177, 0.1);
            border-color: rgba(16, 244, 177, 0.3);
            color: var(--accent-green);
        }

        .alert-err {
            background: rgba(255, 71, 87, 0.1);
            border-color: rgba(255, 71, 87, 0.3);
            color: var(--accent-red);
        }

        .alert-warn {
            background: rgba(255, 217, 61, 0.1);
            border-color: rgba(255, 217, 61, 0.3);
            color: var(--accent-yellow);
        }

        .alert-info {
            background: rgba(0, 217, 255, 0.1);
            border-color: rgba(0, 217, 255, 0.3);
            color: var(--accent-cyan);
        }

        /* File Upload */
        .file-upload {
            background: rgba(10, 14, 26, 0.4);
            border: 2px dashed var(--border);
            border-radius: 16px;
            padding: 40px 20px;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
        }

        .file-upload:hover {
            border-color: var(--accent-cyan);
            background: rgba(0, 217, 255, 0.05);
        }

        .upload-item {
            background: rgba(10, 14, 26, 0.6);
            padding: 16px;
            border-radius: 12px;
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid var(--border);
            transition: all 0.3s;
        }

        .upload-item:hover {
            transform: translateX(4px);
            border-color: var(--accent-cyan);
            box-shadow: 0 4px 20px rgba(0, 217, 255, 0.1);
        }

        /* Footer */
        .footer {
            background: rgba(10, 14, 26, 0.9);
            backdrop-filter: blur(20px);
            padding: 40px 20px 30px;
            text-align: center;
            color: var(--text-muted);
            margin-top: 60px;
            border-top: 1px solid var(--border);
        }

        .footer a {
            color: var(--text-secondary);
            margin: 0 12px;
            transition: color 0.3s;
        }

        .footer a:hover {
            color: var(--accent-cyan);
        }

        .footer-brand {
            margin-top: 16px;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            color: var(--accent-cyan);
        }

        /* Cookie Banner */
        #cookie-banner {
            display: none;
            position: fixed;
            bottom: 20px; left: 20px; right: 20px;
            max-width: 1160px;
            margin: 0 auto;
            background: rgba(20, 28, 48, 0.95);
            backdrop-filter: blur(30px);
            -webkit-backdrop-filter: blur(30px);
            color: white;
            padding: 20px 25px;
            z-index: 9999;
            border-radius: 16px;
            border: 1px solid var(--accent-cyan);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .cookie-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        /* Legal Text */
        .legal-text {
            background: var(--bg-card);
            padding: 30px;
            border-radius: 20px;
            margin: 20px 0;
            line-height: 1.8;
            border: 1px solid var(--border);
        }

        .legal-text h3 {
            color: var(--accent-cyan);
            margin-top: 24px;
            margin-bottom: 8px;
        }

        /* Mobile */
        @media (max-width: 768px) {
            h1 { font-size: 28px; }
            h2 { font-size: 22px; }
            .logo { font-size: 24px; }
            .card { padding: 20px; }
            .nav a { padding: 8px 12px; font-size: 12px; }
            .btn { padding: 12px 20px; font-size: 13px; }
        }
    </style>
</head>
<body>

<div id="cookie-banner">
    <div class="cookie-content">
        <div style="flex: 1; min-width: 250px;">
            <strong style="color: var(--accent-cyan); font-size: 14px;">🍪 Cookie-Hinweis</strong><br>
            <small style="color: var(--text-secondary); line-height: 1.5;">
                Wir verwenden technisch notwendige Cookies fuer Login. 
                <a href="/datenschutz" style="color: var(--accent-cyan);">Mehr erfahren</a>
            </small>
        </div>
        <button onclick="cookieAccept()" class="btn btn-success">
            ✓ Akzeptieren
        </button>
    </div>
</div>

<div class="header">
    <div class="container header-inner">
        <div>
            <div class="logo">XsiKOM</div>
            <div class="subtitle">{{ user.vorname if user else 'KI Bewerbungs-Assistent' }}</div>
        </div>
    </div>
</div>

{% if user %}
<div class="nav">
    <div class="nav-inner">
        <a href="/dashboard">🏠 Dashboard</a>
        <a href="/aaliyah">🤖 Aaliyah KI</a>
        <a href="/lebenslauf">📝 Lebenslauf</a>
        <a href="/uploads">📂 Dateien</a>
        <a href="/bewerbungen">📧 Bewerbungen</a>
        <a href="/premium">💎 Premium</a>
        <a href="/install">📱 App</a>
        <a href="/logout">🚪 Logout</a>
    </div>
</div>
{% endif %}

<div class="container">
    {{ content|safe }}
</div>

<div class="footer">
    <div>
        <a href="/impressum">Impressum</a>•
        <a href="/datenschutz">Datenschutz</a>•
        <a href="/agb">AGB</a>•
        <a href="/widerruf">Widerruf</a>•
        <a href="/haftung">Haftung</a>•
        <a href="/install">App</a>
    </div>
    <div class="footer-brand">
        XsiKOM-BewerbungsBOT
    </div>
    <div style="margin-top: 8px; font-size: 11px; color: var(--text-muted);">
        © 2026 XsiKOM DIGITAL Projects • Komi Tevi<br>
        <a href="mailto:xsikom_digital@xsikom.de" style="color: var(--text-muted);">
            xsikom_digital@xsikom.de
        </a>
    </div>
</div>

</body>
</html>
"""


# ============================================================
# ROUTEN
# ============================================================
@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pw = request.form.get("password", "").strip()
        result = benutzer_pruefen(user, pw)
        if result:
            session["user_id"] = result["id"]
            session["username"] = result["benutzername"]
            session["vorname"] = result["vorname"]
            session["nachname"] = result["nachname"]
            session["rolle"] = result["rolle"]
            session["premium"] = result["premium"]
            return redirect("/dashboard")
        msg = '<div class="alert alert-err">❌ Login falsch!</div>'

    content = f"""
    <div style="max-width: 450px; margin: 60px auto;">
        <div class="card">
            <h1 style="text-align: center;">🔐 Anmelden</h1>
            <p style="text-align: center; color: var(--text-secondary); margin-bottom: 30px;">
                Willkommen zurueck!
            </p>
            {msg}
            <form method="POST">
                <input type="text" name="username" value="admin" placeholder="👤 Benutzername" required>
                <input type="password" name="password" placeholder="🔒 Passwort" required>
                <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 10px;">
                    🚀 Anmelden
                </button>
            </form>
            <p style="text-align: center; margin-top: 25px;">
                <a href="/register">✨ Neuen Account erstellen</a>
            </p>
            <p style="text-align: center; margin-top: 15px; font-size: 11px; color: var(--text-muted);">
                Demo: admin / XsiKOM2026!
            </p>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=None)


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pw = request.form.get("password", "").strip()
        email = request.form.get("email", "").strip()
        vn = request.form.get("vorname", "").strip()
        nn = request.form.get("nachname", "").strip()
        kunde_typ = request.form.get("kunde_typ", "privat")
        dsg = request.form.get("datenschutz", "")
        agb = request.form.get("agb", "")
        widerruf = request.form.get("widerruf", "")

        if not all([user, pw, email, dsg, agb, widerruf]):
            msg = '<div class="alert alert-err">❌ Alle Felder + Zustimmungen!</div>'
        elif len(pw) < 6:
            msg = '<div class="alert alert-err">❌ Passwort min. 6 Zeichen!</div>'
        elif benutzer_anlegen(user, pw, email, vn, nn, kunde_typ):
            return redirect("/login")
        else:
            msg = '<div class="alert alert-err">❌ Benutzername vergeben!</div>'

    content = f"""
    <div style="max-width: 600px; margin: 30px auto;">
        <div class="card">
            <h1>✨ Registrieren</h1>
            {msg}
            <form method="POST">
                <select name="kunde_typ" required>
                    <option value="privat">👤 Privatkunde</option>
                    <option value="firma">🏢 Firmenkunde</option>
                </select>
                <input type="text" name="username" placeholder="Benutzername" required>
                <input type="password" name="password" placeholder="Passwort (min. 6 Zeichen)" required>
                <input type="email" name="email" placeholder="E-Mail" required>
                <input type="text" name="vorname" placeholder="Vorname">
                <input type="text" name="nachname" placeholder="Nachname">

                <div style="margin-top: 20px; padding: 20px;
                            background: rgba(10, 14, 26, 0.5); 
                            border-radius: 12px; border: 1px solid var(--border);">
                    <p style="margin: 10px 0; display: flex; align-items: start; gap: 10px;">
                        <input type="checkbox" name="datenschutz" required style="width: auto; margin-top: 4px;">
                        <span>Ich akzeptiere die 
                            <a href="/datenschutz" target="_blank">Datenschutzerklaerung (DSGVO)</a>
                        </span>
                    </p>
                    <p style="margin: 10px 0; display: flex; align-items: start; gap: 10px;">
                        <input type="checkbox" name="agb" required style="width: auto; margin-top: 4px;">
                        <span>Ich akzeptiere die <a href="/agb" target="_blank">AGB</a> + 
                            <a href="/haftung" target="_blank">Haftungsausschluss</a>
                        </span>
                    </p>
                    <p style="margin: 10px 0; display: flex; align-items: start; gap: 10px;">
                        <input type="checkbox" name="widerruf" required style="width: auto; margin-top: 4px;">
                        <span>Ich kenne mein <a href="/widerruf" target="_blank">Widerrufsrecht</a></span>
                    </p>
                </div>
                <br>
                <button type="submit" class="btn btn-success" style="width: 100%;">
                    🚀 Account erstellen
                </button>
            </form>
            <p style="text-align: center; margin-top: 20px;">
                <a href="/login">← Zurueck zum Login</a>
            </p>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=None)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    bw = bewerbungen_zaehlen(session["user_id"])
    limit = "∞" if session.get("premium") else "5"
    badge = '<span class="badge">⭐ PREMIUM</span>' if session.get("premium") else ""
    
    ki_status = ""
    if GROQ_API_KEY:
        ki_status = '<span class="status-online">KI Aktiv</span>'
    else:
        ki_status = '<span class="status-offline">KI Offline</span>'

    upgrade = ""
    if not session.get("premium"):
        upgrade = '<a href="/premium" class="btn btn-warning">💎 Upgrade auf Premium - 1.99€/Monat</a>'

    content = f"""
    <h1>👋 Hallo, {session['vorname']}!</h1>
    <p style="margin-bottom: 30px;">{ki_status}</p>

    <div class="card">
        <h3>📊 Dein Plan: {"Premium" if session.get("premium") else "Free"} {badge}</h3>
        <p style="font-size: 18px; margin: 16px 0;">
            Bewerbungen: <strong style="color: var(--accent-cyan);">{bw} / {limit}</strong>
        </p>
        {upgrade}
    </div>

    <h2 style="margin-top: 40px;">⚡ Schnellaktionen</h2>
    <div class="grid">
        <a href="/aaliyah" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">🤖</div>
                <div class="stat-value">Aaliyah</div>
                <div class="stat-label">KI Chat starten</div>
            </div>
        </a>
        <a href="/lebenslauf" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-value">Lebenslauf</div>
                <div class="stat-label">Profil bearbeiten</div>
            </div>
        </a>
        <a href="/uploads" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">📂</div>
                <div class="stat-value">Dateien</div>
                <div class="stat-label">PDFs & Bilder</div>
            </div>
        </a>
        <a href="/bewerbungen" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">📧</div>
                <div class="stat-value">{bw}</div>
                <div class="stat-label">Bewerbungen</div>
            </div>
        </a>
    </div>

    <div class="card" style="margin-top: 30px;">
        <h3>💡 Aaliyahs Tipp des Tages</h3>
        <p style="font-size: 15px; color: var(--text-primary);">{aaliyah_tipp()}</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/aaliyah", methods=["GET", "POST"])
def aaliyah_route():
    if "user_id" not in session:
        return redirect("/login")

    antwort = ""
    if request.method == "POST":
        frage = request.form.get("frage", "")
        if frage:
            a = get_ki_antwort(frage)
            a_html = a.replace("\n", "<br>")
            antwort = f"""
            <div class="alert alert-info" style="margin-top: 20px; flex-direction: column; align-items: start;">
                <strong style="color: var(--accent-pink); font-size: 16px;">🤖 Aaliyah:</strong>
                <div style="margin-top: 10px; line-height: 1.7;">{a_html}</div>
            </div>
            """

    ki_status = ""
    if not GROQ_API_KEY:
        ki_status = '<div class="alert alert-warn">⚠️ KI offline - begrenzte Antworten</div>'

    content = f"""
    <h1>🤖 Aaliyah KI</h1>
    <p>Deine intelligente Bewerbungsberaterin</p>
    {ki_status}
    
    <div class="card">
        <h3>💬 Chat</h3>
        <form method="POST">
            <input type="text" name="frage" placeholder="Frag Aaliyah alles..." required>
            <button type="submit" class="btn btn-purple" style="width: 100%;">
                📤 Senden
            </button>
        </form>
        {antwort}
    </div>

    <div class="card">
        <h3>⚡ Beispielfragen</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
            <form method="POST" style="display: inline;">
                <input type="hidden" name="frage" value="Wie schreibe ich ein gutes IT-Anschreiben?">
                <button class="btn btn-primary">💼 IT-Anschreiben</button>
            </form>
            <form method="POST" style="display: inline;">
                <input type="hidden" name="frage" value="Welche Fragen kommen im Vorstellungsgespraech?">
                <button class="btn btn-primary">🎤 Gespraech</button>
            </form>
            <form method="POST" style="display: inline;">
                <input type="hidden" name="frage" value="Wie verhandle ich Gehalt?">
                <button class="btn btn-primary">💰 Gehalt</button>
            </form>
            <form method="POST" style="display: inline;">
                <input type="hidden" name="frage" value="Erklaere TCP/IP fuer mein Interview">
                <button class="btn btn-primary">🌐 Netzwerk</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/uploads", methods=["GET", "POST"])
def uploads():
    if "user_id" not in session:
        return redirect("/login")

    msg = ""
    if request.method == "POST":
        kategorie = request.form.get("kategorie", "dokument")
        if "datei" in request.files:
            file = request.files["datei"]
            if file and file.filename:
                if allowed_file(file.filename):
                    result = datei_speichern(file, session["user_id"], kategorie)
                    if result:
                        msg = f'<div class="alert alert-ok">✅ {result} hochgeladen!</div>'
                    else:
                        msg = '<div class="alert alert-err">❌ Fehler beim Upload!</div>'
                else:
                    msg = '<div class="alert alert-err">❌ Dateityp nicht erlaubt!</div>'

    user_uploads = uploads_laden(session["user_id"])
    uploads_html = ""
    if user_uploads:
        for u in user_uploads:
            upload_id, name, typ, kat, pfad, datum = u
            icon = "📄" if typ == ".pdf" else "🖼️"
            uploads_html += f"""
            <div class="upload-item">
                <div>
                    {icon} <strong>{name}</strong><br>
                    <small style="color: var(--text-muted);">{kat} - {datum[:16]}</small>
                </div>
                <div style="display: flex; gap: 8px;">
                    <a href="/download/{upload_id}" class="btn btn-primary" style="padding: 8px 14px; font-size: 12px;">
                        ⬇️
                    </a>
                    <a href="/delete/{upload_id}" class="btn btn-danger" style="padding: 8px 14px; font-size: 12px;"
                       onclick="return confirm('Wirklich loeschen?')">
                        🗑️
                    </a>
                </div>
            </div>
            """
    else:
        uploads_html = '<p style="color: var(--text-muted); text-align: center; padding: 20px;">Noch keine Dateien</p>'

    content = f"""
    <h1>📂 Meine Dateien</h1>
    {msg}

    <div class="card">
        <h3>📤 Datei hochladen</h3>
        <form method="POST" enctype="multipart/form-data">
            <select name="kategorie" required>
                <option value="lebenslauf">📄 Lebenslauf</option>
                <option value="zeugnis">📜 Zeugnis</option>
                <option value="zertifikat">🏆 Zertifikat</option>
                <option value="bild">🖼️ Bewerbungsbild</option>
                <option value="anschreiben">✉️ Anschreiben</option>
                <option value="dokument">📋 Sonstiges</option>
            </select>

            <div class="file-upload">
                <div style="font-size: 48px; margin-bottom: 10px;">📤</div>
                <input type="file" name="datei" required
                       accept=".pdf,.png,.jpg,.jpeg,.gif,.bmp,.webp"
                       style="margin: 10px 0;">
                <p style="font-size: 13px; color: var(--text-muted); margin-top: 10px;">
                    PDF, PNG, JPG, JPEG, GIF, BMP, WEBP
                </p>
            </div>

            <button type="submit" class="btn btn-success" style="width: 100%; margin-top: 15px;">
                🚀 Hochladen
            </button>
        </form>
    </div>

    <div class="card">
        <h3>📋 Deine Dateien ({len(user_uploads)})</h3>
        {uploads_html}
    </div>

    <div class="alert alert-info">
        🔒 <strong>Datenschutz:</strong> Deine Dateien sind nur fuer dich sichtbar.
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/download/<int:upload_id>")
def download_datei(upload_id):
    if "user_id" not in session:
        return redirect("/login")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT pfad, dateiname FROM uploads WHERE id=? AND user_id=?",
              (upload_id, session["user_id"]))
    r = c.fetchone()
    conn.close()
    if r and os.path.exists(r[0]):
        return send_file(r[0], as_attachment=True, download_name=r[1])
    return "Datei nicht gefunden", 404


@app.route("/delete/<int:upload_id>")
def delete_datei(upload_id):
    if "user_id" not in session:
        return redirect("/login")
    upload_loeschen(upload_id, session["user_id"])
    return redirect("/uploads")


@app.route("/lebenslauf", methods=["GET", "POST"])
def lebenslauf():
    if "user_id" not in session:
        return redirect("/login")

    msg = ""
    if request.method == "POST":
        daten = {
            "vorname": request.form.get("vorname", ""),
            "nachname": request.form.get("nachname", ""),
            "strasse": request.form.get("strasse", ""),
            "plz": request.form.get("plz", ""),
            "stadt": request.form.get("stadt", ""),
            "telefon": request.form.get("telefon", ""),
            "email": request.form.get("email", ""),
            "geburtsdatum": request.form.get("geburtsdatum", ""),
            "kenntnisse": request.form.get("kenntnisse", ""),
            "sprachen": request.form.get("sprachen", "")
        }
        profil_speichern(session["user_id"], daten)
        msg = '<div class="alert alert-ok">✅ Profil gespeichert!</div>'

    p = profil_laden(session["user_id"])

    content = f"""
    <h1>📝 Lebenslauf</h1>
    {msg}
    <form method="POST">
        <div class="card">
            <h3>👤 Persoenliche Daten</h3>
            <input type="text" name="vorname" placeholder="Vorname" value="{p.get('vorname','')}">
            <input type="text" name="nachname" placeholder="Nachname" value="{p.get('nachname','')}">
            <input type="text" name="strasse" placeholder="Strasse" value="{p.get('strasse','')}">
            <input type="text" name="plz" placeholder="PLZ" value="{p.get('plz','')}">
            <input type="text" name="stadt" placeholder="Stadt" value="{p.get('stadt','')}">
            <input type="text" name="telefon" placeholder="Telefon" value="{p.get('telefon','')}">
            <input type="email" name="email" placeholder="E-Mail" value="{p.get('email','')}">
            <input type="text" name="geburtsdatum" placeholder="Geburtsdatum" value="{p.get('geburtsdatum','')}">
        </div>
        <div class="card">
            <h3>💼 IT-Kenntnisse</h3>
            <textarea name="kenntnisse" rows="6" placeholder="Eine Kenntnis pro Zeile">{p.get('kenntnisse','')}</textarea>
        </div>
        <div class="card">
            <h3>🌍 Sprachen</h3>
            <textarea name="sprachen" rows="4" placeholder="Eine Sprache pro Zeile">{p.get('sprachen','')}</textarea>
        </div>
        <div class="card">
            <button type="submit" class="btn btn-success">💾 Speichern</button>
            <a href="/uploads" class="btn btn-primary">📤 Lebenslauf-Datei hochladen</a>
        </div>
    </form>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/bewerbungen", methods=["GET", "POST"])
def bewerbungen():
    if "user_id" not in session:
        return redirect("/login")

    msg = ""
    if request.method == "POST":
        firma = request.form.get("firma", "").strip()
        email = request.form.get("email", "").strip()
        bw = bewerbungen_zaehlen(session["user_id"])

        if not session.get("premium") and bw >= 5:
            msg = '<div class="alert alert-warn">⚠️ Limit erreicht! <a href="/premium">Upgrade!</a></div>'
        elif firma and email:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                "INSERT INTO bewerbungen (user_id, firma, email, datum) VALUES (?, ?, ?, ?)",
                (session["user_id"], firma, email, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            msg = f'<div class="alert alert-ok">✅ Bewerbung bei {firma} gespeichert!</div>'

    bw = bewerbungen_zaehlen(session["user_id"])
    limit = "∞" if session.get("premium") else 5

    content = f"""
    <h1>📧 Bewerbungen</h1>
    <div class="card">
        <h3>📊 Dein Limit</h3>
        <p style="font-size: 20px;">
            <strong style="color: var(--accent-cyan);">{bw} / {limit}</strong> diesen Monat
        </p>
    </div>
    {msg}
    <div class="card">
        <h3>➕ Neue Bewerbung</h3>
        <form method="POST">
            <input type="text" name="firma" placeholder="Firmenname" required>
            <input type="email" name="email" placeholder="E-Mail des Unternehmens" required>
            <button type="submit" class="btn btn-success" style="width: 100%;">
                💾 Speichern
            </button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/premium")
def premium():
    content = """
    <h1>💎 Premium Upgrade</h1>
    <div class="grid">
        <div class="card">
            <h2>🆓 Free</h2>
            <h3 style="font-size: 32px; margin: 16px 0;">0 €</h3>
            <p style="color: var(--text-muted);">Pro Monat</p>
            <ul style="list-style: none; padding: 0; margin: 20px 0;">
                <li style="padding: 8px 0;">✓ 5 Bewerbungen/Monat</li>
                <li style="padding: 8px 0;">✓ 1 Lebenslauf</li>
                <li style="padding: 8px 0;">✓ Basis KI</li>
            </ul>
            <button class="btn btn-primary" style="width: 100%;">Aktuell</button>
        </div>
        <div class="card" style="border: 2px solid var(--accent-yellow); transform: scale(1.05);">
            <span class="badge">⭐ BELIEBT</span>
            <h2 style="margin-top: 12px;">💎 Premium</h2>
            <h3 style="font-size: 32px; margin: 16px 0; color: var(--accent-yellow);">1.99 €</h3>
            <p style="color: var(--text-muted);">Pro Monat</p>
            <ul style="list-style: none; padding: 0; margin: 20px 0;">
                <li style="padding: 8px 0;">✓ UNBEGRENZTE Bewerbungen</li>
                <li style="padding: 8px 0;">✓ 10 Lebenslauf-Vorlagen</li>
                <li style="padding: 8px 0;">✓ Premium KI</li>
                <li style="padding: 8px 0;">✓ Werbefrei</li>
            </ul>
            <a href="/checkout" class="btn btn-warning" style="width: 100%;">🚀 Upgrade jetzt</a>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect("/login")
    content = """
    <h1>💳 Checkout</h1>
    <div class="card">
        <div class="alert alert-warn">⚠️ Demo-Modus: Stripe Integration kommt bald!</div>
        <a href="/aktivieren" class="btn btn-success">🎁 Demo Premium aktivieren</a>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/aktivieren")
def aktivieren():
    if "user_id" not in session:
        return redirect("/login")
    premium_aktivieren(session["user_id"])
    session["premium"] = 1
    content = """
    <h1>🎉 Premium aktiviert!</h1>
    <div class="alert alert-ok">✅ Premium ist jetzt aktiv!</div>
    <a href="/dashboard" class="btn btn-primary">→ Zum Dashboard</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/install")
def install():
    content = """
    <h1>📱 App installieren</h1>
    <div class="card">
        <h3>🤖 Android (Chrome)</h3>
        <ol style="padding-left: 25px; line-height: 2;">
            <li>3-Punkte-Menue oben rechts</li>
            <li>"App installieren"</li>
            <li>Bestaetigen</li>
        </ol>
    </div>
    <div class="card">
        <h3>🍎 iPhone (Safari)</h3>
        <ol style="padding-left: 25px; line-height: 2;">
            <li>Teilen-Symbol</li>
            <li>"Zum Home-Bildschirm"</li>
            <li>"Hinzufuegen"</li>
        </ol>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


# ============================================================
# RECHTLICHE SEITEN
# ============================================================
@app.route("/impressum")
def impressum():
    content = f"""
    <h1>📜 Impressum</h1>
    <div class="legal-text">
        <h3>Angaben gemaess § 5 TMG</h3>
        <p><strong>XsiKOM DIGITAL Projects</strong><br>
        Komi Tevi<br>
        Am Koenigsfloss 12<br>
        55252 Mainz-Kastel<br>
        Deutschland</p>

        <h3>Kontakt</h3>
        <p>Telefon: +49 178 8977320<br>
        E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a><br>
        Web: https://xsikom.de</p>

        <h3>Verantwortlich nach § 55 Abs. 2 RStV</h3>
        <p>Komi Tevi (Anschrift wie oben)</p>

        <h3>Umsatzsteuer</h3>
        <p>Kleinunternehmer nach § 19 UStG.</p>

        <h3>EU-Streitschlichtung</h3>
        <p><a href="https://ec.europa.eu/consumers/odr/" target="_blank">
            https://ec.europa.eu/consumers/odr/
        </a></p>

        <h3>Verbraucherstreitbeilegung</h3>
        <p>Wir nehmen nicht an Streitbeilegungsverfahren teil.</p>

        <h3>Haftung</h3>
        <p>Trotz sorgfaeltiger Pruefung uebernehmen wir keine Haftung 
        fuer externe Links.</p>

        <p style="margin-top: 30px; padding: 16px; background: rgba(10,14,26,0.5); 
                  border-radius: 12px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026 • 
            <strong>© 2026 XsiKOM DIGITAL Projects</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/datenschutz")
def datenschutz():
    content = f"""
    <h1>🔒 Datenschutz (DSGVO)</h1>
    <div class="legal-text">
        <h3>1. Verantwortlicher</h3>
        <p><strong>XsiKOM DIGITAL Projects</strong><br>
        Komi Tevi<br>Am Koenigsfloss 12<br>55252 Mainz-Kastel<br>
        E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>

        <h3>2. Erhobene Daten</h3>
        <ul style="padding-left: 25px;">
            <li>Stammdaten (Name, E-Mail)</li>
            <li>Zugangsdaten (verschluesselt)</li>
            <li>Bewerbungsdaten, Uploads</li>
            <li>Nutzungsdaten (anonymisiert)</li>
        </ul>

        <h3>3. Zwecke</h3>
        <p>Bereitstellung Bewerbungs-Service (Art. 6 Abs. 1 lit. b DSGVO).</p>

        <h3>4. Ihre Rechte (DSGVO)</h3>
        <ul style="padding-left: 25px;">
            <li>Auskunft (Art. 15)</li>
            <li>Berichtigung (Art. 16)</li>
            <li>Loeschung (Art. 17)</li>
            <li>Datenuebertragbarkeit (Art. 20)</li>
            <li>Widerspruch (Art. 21)</li>
        </ul>
        <p>Anfragen: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>

        <h3>5. KI-Verarbeitung</h3>
        <p>Aaliyah nutzt Groq Inc. (USA). EU-US Data Privacy Framework.</p>

        <h3>6. Cookies</h3>
        <p>Nur technisch notwendige Cookies (Login, Session).</p>

        <h3>7. Hosting</h3>
        <p>Render Services Inc., USA. Standardvertragsklauseln EU.</p>

        <h3>8. Speicherdauer</h3>
        <ul style="padding-left: 25px;">
            <li>Aktive Accounts: Dauer der Nutzung</li>
            <li>Inaktive: 12 Monate</li>
            <li>Logs: 30 Tage</li>
        </ul>

        <h3>9. Aufsichtsbehoerde</h3>
        <p>Landesbeauftragter Datenschutz RLP<br>
        Hintere Bleiche 34, 55116 Mainz</p>

        <p style="margin-top: 30px; padding: 16px; background: rgba(10,14,26,0.5); 
                  border-radius: 12px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026 • 
            <strong>© 2026 XsiKOM DIGITAL Projects</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/widerruf")
def widerruf():
    content = f"""
    <h1>↩️ Widerrufsbelehrung</h1>
    <div class="legal-text">
        <h3>Widerrufsrecht (§ 312g BGB)</h3>
        <p><strong>14 Tage Widerrufsrecht ab Vertragsschluss.</strong></p>

        <h3>Widerruf an</h3>
        <p style="padding: 16px; background: rgba(10,14,26,0.5); border-radius: 12px;">
            <strong>XsiKOM DIGITAL Projects</strong><br>
            Komi Tevi<br>
            Am Koenigsfloss 12<br>
            55252 Mainz-Kastel<br>
            E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
        </p>

        <h3>Folgen des Widerrufs</h3>
        <p>Rueckzahlung binnen 14 Tagen.</p>

        <h3>Firmenkunden (B2B)</h3>
        <p>Kein gesetzliches Widerrufsrecht. Es gelten unsere AGB.</p>

        <h3>Ausschluss</h3>
        <p>Widerrufsrecht erlischt bei digitalen Inhalten nach ausdruecklicher 
        Zustimmung zur Ausfuehrung.</p>

        <p style="margin-top: 30px; padding: 16px; background: rgba(10,14,26,0.5); 
                  border-radius: 12px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026 • 
            <strong>© 2026 XsiKOM DIGITAL Projects</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/haftung")
def haftung():
    content = f"""
    <h1>⚖️ Haftungsausschluss</h1>
    <div class="legal-text">
        <h3>1. Haftung fuer Inhalte</h3>
        <p>Inhalte mit Sorgfalt erstellt, keine Gewaehr fuer Richtigkeit.</p>

        <h3>2. KI-Inhalte ⚠️</h3>
        <div class="alert alert-warn">
            <div>
                <strong>WICHTIG:</strong><br>
                • KI-Inhalte koennen fehlerhaft sein<br>
                • Pruefen Sie alle Inhalte<br>
                • Keine Garantie fuer Erfolg<br>
                • Nutzung auf eigenes Risiko
            </div>
        </div>

        <h3>3. Haftungsausschluss</h3>
        <p>XsiKOM DIGITAL Projects haftet nicht fuer:</p>
        <ul style="padding-left: 25px;">
            <li>Direkte oder indirekte Schaeden</li>
            <li>Datenverlust</li>
            <li>Erfolglose Bewerbungen</li>
            <li>Fehlerhafte KI-Empfehlungen</li>
            <li>Folgeschaeden</li>
        </ul>

        <h3>4. Haftungsbeschraenkung</h3>
        <p>Haftung nur bei Vorsatz und grober Fahrlaessigkeit.</p>

        <h3>5. Eigenverantwortung</h3>
        <ul style="padding-left: 25px;">
            <li>Korrekte Daten eingeben</li>
            <li>KI-Inhalte pruefen</li>
            <li>Bewerbungsfristen einhalten</li>
            <li>Backups erstellen</li>
        </ul>

        <h3>6. Anwendbares Recht</h3>
        <p>Deutsches Recht. Gerichtsstand: Mainz.</p>

        <h3>Kontakt</h3>
        <p>E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>

        <p style="margin-top: 30px; padding: 16px; background: rgba(10,14,26,0.5); 
                  border-radius: 12px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026 • 
            <strong>© 2026 XsiKOM DIGITAL Projects</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/agb")
def agb():
    content = f"""
    <h1>📋 AGB</h1>
    <div class="legal-text">
        <h3>§ 1 Geltungsbereich</h3>
        <p>Diese AGB gelten fuer alle Nutzer.</p>

        <h3>§ 2 Vertragspartner</h3>
        <p><strong>XsiKOM DIGITAL Projects</strong><br>
        Komi Tevi<br>Am Koenigsfloss 12<br>55252 Mainz-Kastel<br>
        E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>

        <h3>§ 3 Leistungen</h3>
        <p><strong>Free:</strong> 5 Bewerbungen, 1 Lebenslauf, Basis KI</p>
        <p><strong>Premium (1.99 €/Monat):</strong> Unbegrenzt, alle Features</p>

        <h3>§ 4 Preise</h3>
        <p>Kleinunternehmer nach § 19 UStG.</p>

        <h3>§ 5 Widerrufsrecht</h3>
        <p>14 Tage fuer Verbraucher. <a href="/widerruf">Mehr</a></p>

        <h3>§ 6 Kuendigung</h3>
        <p>Jederzeit zum Monatsende.</p>

        <h3>§ 7 Haftung</h3>
        <p>Siehe <a href="/haftung">Haftungsausschluss</a>.</p>

        <h3>§ 8 KI-Nutzung</h3>
        <p>KI-Inhalte sind nicht fehlerfrei. Eigenverantwortung!</p>

        <h3>§ 9 Datenschutz</h3>
        <p>Siehe <a href="/datenschutz">Datenschutzerklaerung</a>.</p>

        <h3>§ 10 Gerichtsstand</h3>
        <p>Mainz, Deutschland. Deutsches Recht.</p>

        <p style="margin-top: 30px; padding: 16px; background: rgba(10,14,26,0.5); 
                  border-radius: 12px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026 • 
            <strong>© 2026 XsiKOM DIGITAL Projects</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/manifest.json")
def manifest():
    return send_from_directory(".", "manifest.json", mimetype="application/json")


@app.route("/sw.js")
def service_worker():
    response = make_response(send_from_directory(".", "sw.js", mimetype="application/javascript"))
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/.well-known/assetlinks.json")
def assetlinks():
    return send_from_directory(".well-known", "assetlinks.json", mimetype="application/json")


db_init()
admin_anlegen()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  XsiKOM-BewerbungsBOT - Modern Design")
    print("=" * 60)
    print(f"  KI:    {'ONLINE' if GROQ_API_KEY else 'OFFLINE'}")
    print(f"  Email: {CONTACT_EMAIL}")
    print(f"  URL:   http://localhost:5000")
    print("=" * 60 + "\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)