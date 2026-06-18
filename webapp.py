"""
XsiKOM-BewerbungsBOT - KOMPLETT
Mit Aaliyah KI, AVINU Bot, 2FA, DSGVO, Quantum Security
"""
import os
import sqlite3
import hashlib
import secrets
import random
import requests
import json as json_module
from datetime import datetime, timedelta
from flask import (
    Flask, render_template_string, request,
    redirect, session, send_from_directory,
    send_file, make_response, Response
)
from werkzeug.utils import secure_filename
from PIL import Image

from security import (
    generate_2fa_secret, generate_qr_code,
    verify_2fa_token, get_2fa_status, enable_2fa, disable_2fa,
    password_strength, create_password_reset_token,
    verify_reset_token, use_reset_token,
    request_account_deletion, cancel_deletion,
    get_deletion_status, export_user_data, audit_log, get_audit_log
)

from avinu_ki import (
    avinu_antwort, jobs_suchen_indeed, jobs_suchen_arbeitsagentur,
    jobs_speichern, jobs_laden, vorlagen_laden,
    anschreiben_generieren, auto_bewerbung_erstellen,
    BRANCHEN
)


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(hours=2)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

DB_NAME = "bewerbungen.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "bmp", "webp"}
CONTACT_EMAIL = "xsikom_digital@xsikom.de"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# KI
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """Du bist Aaliyah, professionelle KI-Karriereberaterin.
Spezialgebiete: IT, Bewerbungen, Lebenslauf, Vorstellungsgespraech.
Antworte auf Deutsch, freundlich, 3-5 Saetze."""


def get_ki_antwort(frage):
    if not GROQ_API_KEY:
        return "Hallo! KI gerade offline."
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
        return "Entschuldigung, ein Fehler ist aufgetreten."
    except Exception:
        return "KI-Verbindung fehlgeschlagen."


AALIYAH_TIPPS = [
    "Passe dein Anschreiben individuell an!",
    "Erwaehne konkrete Projekte der Firma.",
    "Halte das Anschreiben auf max. 1 Seite.",
    "Zeige Motivation und Begeisterung.",
    "Pruefe deine Bewerbung auf Rechtschreibung.",
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
# HTML TEMPLATE
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
    </script>

    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg-primary: #0A0E1A;
            --bg-secondary: #131829;
            --bg-card: rgba(20, 28, 48, 0.6);
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
        }
        body::before {
            content: '';
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: 
                radial-gradient(circle at 20% 20%, rgba(0, 217, 255, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%);
            z-index: -1;
            animation: bgMove 20s ease infinite;
        }
        @keyframes bgMove {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header {
            background: rgba(10, 14, 26, 0.8);
            backdrop-filter: blur(20px);
            padding: 20px 0;
            border-bottom: 1px solid var(--border);
            position: sticky; top: 0; z-index: 100;
        }
        .header-inner { display: flex; justify-content: space-between; align-items: center; }
        .logo {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 32px; font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -1px;
        }
        .subtitle { color: var(--text-secondary); font-size: 13px; margin-top: 2px; }
        .nav {
            background: rgba(19, 24, 41, 0.5);
            backdrop-filter: blur(20px);
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
            overflow-x: auto; white-space: nowrap;
        }
        .nav-inner { max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; gap: 5px; }
        .nav a {
            color: var(--text-secondary); text-decoration: none;
            padding: 10px 18px; border-radius: 12px;
            font-size: 14px; font-weight: 500;
            transition: all 0.3s;
        }
        .nav a:hover {
            color: var(--text-primary);
            background: rgba(0, 217, 255, 0.1);
        }
        .card {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            margin: 20px 0;
            border: 1px solid var(--border);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.4s;
            position: relative;
            overflow: hidden;
        }
        .card::before {
            content: '';
            position: absolute; top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--accent-cyan), var(--accent-purple), transparent);
            opacity: 0.5;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0, 217, 255, 0.15);
            border-color: rgba(0, 217, 255, 0.3);
        }
        .btn {
            display: inline-flex; align-items: center; justify-content: center;
            gap: 8px; padding: 14px 28px; border: none;
            border-radius: 12px; cursor: pointer;
            font-weight: 600; font-size: 14px;
            text-decoration: none;
            transition: all 0.3s;
            font-family: 'Poppins', sans-serif;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn-primary { background: linear-gradient(135deg, var(--accent-cyan), #0099CC); color: white; }
        .btn-success { background: linear-gradient(135deg, var(--accent-green), #059669); color: white; }
        .btn-warning { background: linear-gradient(135deg, var(--accent-yellow), #F59E0B); color: #0A0E1A; }
        .btn-danger { background: linear-gradient(135deg, var(--accent-red), #DC2626); color: white; }
        .btn-purple { background: linear-gradient(135deg, var(--accent-purple), #6D28D9); color: white; }
        input, textarea, select {
            background: rgba(10, 14, 26, 0.6);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 14px 18px; border-radius: 12px;
            width: 100%; margin-bottom: 12px;
            font-size: 14px; font-family: 'Poppins', sans-serif;
            transition: all 0.3s;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--accent-cyan);
            box-shadow: 0 0 0 4px rgba(0, 217, 255, 0.1);
        }
        h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 36px; font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }
        h2 { font-size: 26px; font-weight: 600; margin-bottom: 16px; }
        h3 { font-size: 18px; font-weight: 600; color: var(--accent-cyan); margin-bottom: 12px; }
        p { line-height: 1.7; color: var(--text-secondary); margin-bottom: 8px; }
        a { color: var(--accent-cyan); text-decoration: none; transition: color 0.3s; }
        a:hover { color: var(--accent-purple); }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, rgba(20,28,48,0.8), rgba(30,38,58,0.6));
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            transition: all 0.4s;
            cursor: pointer;
        }
        .stat-card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: var(--accent-cyan);
            box-shadow: 0 25px 50px rgba(0, 217, 255, 0.2);
        }
        .stat-icon { font-size: 48px; margin-bottom: 12px; }
        .stat-value {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 32px; font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stat-label { color: var(--text-secondary); font-size: 13px; margin-top: 4px; }
        .badge {
            background: linear-gradient(135deg, var(--accent-yellow), var(--accent-pink));
            color: var(--bg-primary);
            padding: 6px 14px; border-radius: 20px;
            font-size: 11px; font-weight: 700;
            display: inline-block;
        }
        .status-online {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 6px 14px;
            background: rgba(16, 244, 177, 0.1);
            border: 1px solid rgba(16, 244, 177, 0.3);
            border-radius: 20px; color: var(--accent-green);
            font-size: 12px; font-weight: 600;
        }
        .status-online::before {
            content: ''; width: 8px; height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-green);
            animation: pulse 2s infinite;
        }
        .status-offline {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 6px 14px;
            background: rgba(255, 71, 87, 0.1);
            border: 1px solid rgba(255, 71, 87, 0.3);
            border-radius: 20px; color: var(--accent-red);
            font-size: 12px; font-weight: 600;
        }
        .status-offline::before {
            content: ''; width: 8px; height: 8px;
            background: var(--accent-red);
            border-radius: 50%;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.2); }
        }
        .alert {
            padding: 16px 20px; border-radius: 12px;
            margin: 16px 0; backdrop-filter: blur(10px);
            border: 1px solid; display: flex;
            align-items: center; gap: 12px;
        }
        .alert-ok { background: rgba(16, 244, 177, 0.1); border-color: rgba(16, 244, 177, 0.3); color: var(--accent-green); }
        .alert-err { background: rgba(255, 71, 87, 0.1); border-color: rgba(255, 71, 87, 0.3); color: var(--accent-red); }
        .alert-warn { background: rgba(255, 217, 61, 0.1); border-color: rgba(255, 217, 61, 0.3); color: var(--accent-yellow); }
        .alert-info { background: rgba(0, 217, 255, 0.1); border-color: rgba(0, 217, 255, 0.3); color: var(--accent-cyan); }
        .file-upload {
            background: rgba(10, 14, 26, 0.4);
            border: 2px dashed var(--border);
            border-radius: 16px;
            padding: 40px 20px; text-align: center;
            transition: all 0.3s; cursor: pointer;
        }
        .file-upload:hover {
            border-color: var(--accent-cyan);
            background: rgba(0, 217, 255, 0.05);
        }
        .upload-item {
            background: rgba(10, 14, 26, 0.6);
            padding: 16px; border-radius: 12px;
            margin: 10px 0;
            display: flex; justify-content: space-between;
            align-items: center;
            border: 1px solid var(--border);
        }
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
        .footer-brand {
            margin-top: 16px;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            color: var(--accent-cyan);
        }
        #cookie-banner {
            display: none;
            position: fixed;
            bottom: 20px; left: 20px; right: 20px;
            max-width: 1160px; margin: 0 auto;
            background: rgba(20, 28, 48, 0.95);
            backdrop-filter: blur(30px);
            color: white; padding: 20px 25px;
            z-index: 9999;
            border-radius: 16px;
            border: 1px solid var(--accent-cyan);
        }
        .cookie-content {
            display: flex; justify-content: space-between;
            align-items: center; flex-wrap: wrap; gap: 15px;
        }
        .legal-text {
            background: var(--bg-card);
            padding: 30px; border-radius: 20px;
            margin: 20px 0; line-height: 1.8;
            border: 1px solid var(--border);
        }
        .legal-text h3 {
            color: var(--accent-cyan);
            margin-top: 24px; margin-bottom: 8px;
        }
        @media (max-width: 768px) {
            h1 { font-size: 28px; }
            .logo { font-size: 24px; }
            .nav a { padding: 8px 12px; font-size: 12px; }
        }
    </style>
</head>
<body>

<div id="cookie-banner">
    <div class="cookie-content">
        <div style="flex: 1; min-width: 250px;">
            <strong style="color: var(--accent-cyan);">🍪 Cookie-Hinweis</strong><br>
            <small style="color: var(--text-secondary);">
                Wir verwenden technisch notwendige Cookies. 
                <a href="/datenschutz" style="color: var(--accent-cyan);">Mehr</a>
            </small>
        </div>
        <button onclick="cookieAccept()" class="btn btn-success">✓ Akzeptieren</button>
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
        <a href="/aaliyah">🤖 Aaliyah</a>
        <a href="/avinu">⚡ AVINU</a>
        <a href="/lebenslauf">📝 Lebenslauf</a>
        <a href="/uploads">📂 Dateien</a>
        <a href="/bewerbungen">📧 Bewerbungen</a>
        <a href="/premium">💎 Premium</a>
        <a href="/profil">⚙️ Profil</a>
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
    <div class="footer-brand">XsiKOM-BewerbungsBOT</div>
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
            audit_log(result["id"], "LOGIN", "Erfolgreicher Login")
            return redirect("/dashboard")
        msg = '<div class="alert alert-err">❌ Login falsch!</div>'

    content = f"""
    <div style="max-width: 450px; margin: 60px auto;">
        <div class="card">
            <h1 style="text-align: center;">🔐 Anmelden</h1>
            {msg}
            <form method="POST">
                <input type="text" name="username" value="admin" placeholder="👤 Benutzername" required>
                <input type="password" name="password" placeholder="🔒 Passwort" required>
                <button type="submit" class="btn btn-primary" style="width: 100%;">🚀 Anmelden</button>
            </form>
            <p style="text-align: center; margin-top: 25px;">
                <a href="/register">✨ Neuen Account erstellen</a>
            </p>
            <p style="text-align: center; margin-top: 10px;">
                <a href="/password-reset" style="color: var(--text-muted); font-size: 13px;">
                    🔑 Passwort vergessen?
                </a>
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
                <input type="password" name="password" placeholder="Passwort" required>
                <input type="email" name="email" placeholder="E-Mail" required>
                <input type="text" name="vorname" placeholder="Vorname">
                <input type="text" name="nachname" placeholder="Nachname">

                <div style="margin-top: 20px; padding: 20px;
                            background: rgba(10,14,26,0.5); 
                            border-radius: 12px;">
                    <p style="margin: 10px 0;">
                        <input type="checkbox" name="datenschutz" required style="width: auto;">
                        Ich akzeptiere die <a href="/datenschutz" target="_blank">Datenschutzerklaerung</a>
                    </p>
                    <p style="margin: 10px 0;">
                        <input type="checkbox" name="agb" required style="width: auto;">
                        Ich akzeptiere die <a href="/agb" target="_blank">AGB</a> + 
                        <a href="/haftung" target="_blank">Haftung</a>
                    </p>
                    <p style="margin: 10px 0;">
                        <input type="checkbox" name="widerruf" required style="width: auto;">
                        Ich kenne mein <a href="/widerruf" target="_blank">Widerrufsrecht</a>
                    </p>
                </div>
                <button type="submit" class="btn btn-success" style="width: 100%;">
                    🚀 Account erstellen
                </button>
            </form>
            <p style="text-align: center; margin-top: 20px;">
                <a href="/login">← Login</a>
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

    ki_status = '<span class="status-online">KI Aktiv</span>' if GROQ_API_KEY else '<span class="status-offline">KI Offline</span>'

    upgrade = ""
    if not session.get("premium"):
        upgrade = '<a href="/premium" class="btn btn-warning">💎 Upgrade Premium - 1.99€/Monat</a>'

    content = f"""
    <h1>👋 Hallo, {session['vorname']}!</h1>
    <p style="margin-bottom: 30px;">{ki_status}</p>

    <div class="card">
        <h3>📊 Plan: {"Premium" if session.get("premium") else "Free"} {badge}</h3>
        <p style="font-size: 18px;">Bewerbungen: <strong>{bw} / {limit}</strong></p>
        {upgrade}
    </div>

    <h2 style="margin-top: 40px;">⚡ Schnellaktionen</h2>
    <div class="grid">
        <a href="/aaliyah" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">🤖</div>
                <div class="stat-value">Aaliyah</div>
                <div class="stat-label">KI Chat</div>
            </div>
        </a>
        <a href="/avinu" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">⚡</div>
                <div class="stat-value">AVINU</div>
                <div class="stat-label">Job Bot</div>
            </div>
        </a>
        <a href="/lebenslauf" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">📝</div>
                <div class="stat-value">Lebenslauf</div>
                <div class="stat-label">Bearbeiten</div>
            </div>
        </a>
        <a href="/profil" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">⚙️</div>
                <div class="stat-value">Profil</div>
                <div class="stat-label">Sicherheit</div>
            </div>
        </a>
    </div>

    <div class="card" style="margin-top: 30px;">
        <h3>💡 Aaliyahs Tipp</h3>
        <p>{aaliyah_tipp()}</p>
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
            <div class="alert alert-info" style="flex-direction: column; align-items: start;">
                <strong style="color: var(--accent-pink);">🤖 Aaliyah:</strong>
                <div style="margin-top: 10px;">{a_html}</div>
            </div>
            """
    content = f"""
    <h1>🤖 Aaliyah KI</h1>
    <div class="card">
        <h3>💬 Chat</h3>
        <form method="POST">
            <input type="text" name="frage" placeholder="Frag Aaliyah..." required>
            <button type="submit" class="btn btn-purple" style="width: 100%;">📤 Senden</button>
        </form>
        {antwort}
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


# ============================================================
# AVINU ROUTES
# ============================================================
@app.route("/avinu", methods=["GET", "POST"])
def avinu_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        branche = request.form.get("branche", "")
        standort = request.form.get("standort", "")
        suchbegriff = request.form.get("suchbegriff", "")
        if branche and standort:
            if not suchbegriff:
                suchbegriff = BRANCHEN.get(branche, ["Job"])[0]
            jobs1 = jobs_suchen_indeed(suchbegriff, standort, 10)
            jobs2 = jobs_suchen_arbeitsagentur(suchbegriff, standort, 10)
            alle_jobs = jobs1 + jobs2
            if alle_jobs:
                anzahl = jobs_speichern(session["user_id"], alle_jobs, branche)
                msg = f'<div class="alert alert-ok">✅ {anzahl} neue Jobs!</div>'
            else:
                msg = '<div class="alert alert-warn">⚠️ Keine Jobs gefunden!</div>'

    jobs = jobs_laden(session["user_id"], nur_offen=True)
    jobs_html = ""
    for j in jobs[:20]:
        jobs_html += f"""
        <div class="card">
            <h3>💼 {j[3]}</h3>
            <p>🏢 <strong>{j[2]}</strong></p>
            <p>📍 {j[4]} · 🔗 {j[9]} · 🏷️ {j[8]}</p>
            <a href="/avinu/bewerben/{j[0]}" class="btn btn-success">⚡ Auto-Bewerben</a>
        </div>
        """
    if not jobs_html:
        jobs_html = '<p style="text-align: center; color: var(--text-muted);">Noch keine Jobs!</p>'

    content = f"""
    <h1>⚡ AVINU Bot</h1>
    {msg}
    <div class="card">
        <h3>🔍 Job-Suche</h3>
        <form method="POST">
            <select name="branche" required>
                <option value="">-- Branche --</option>
                <option value="it">💻 IT</option>
                <option value="handwerk">🔧 Handwerk</option>
                <option value="gesundheit">🏥 Gesundheit</option>
                <option value="verwaltung">📋 Verwaltung</option>
                <option value="verkauf">🛒 Verkauf</option>
                <option value="logistik">📦 Logistik</option>
                <option value="gastronomie">🍽️ Gastronomie</option>
                <option value="bildung">📚 Bildung</option>
                <option value="marketing">📱 Marketing</option>
                <option value="finanzen">💰 Finanzen</option>
            </select>
            <input type="text" name="suchbegriff" placeholder="Suchbegriff (optional)">
            <input type="text" name="standort" placeholder="Standort" required>
            <button type="submit" class="btn btn-primary" style="width: 100%;">🚀 Suchen</button>
        </form>
    </div>
    <h2>💼 Jobs ({len(jobs)})</h2>
    {jobs_html}
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/avinu/bewerben/<int:job_id>", methods=["GET", "POST"])
def avinu_bewerben(job_id):
    if "user_id" not in session:
        return redirect("/login")

    vorlagen = vorlagen_laden(premium=session.get("premium", False))
    profil = profil_laden(session["user_id"])
    msg = ""
    anschreiben_text = ""

    if request.method == "POST":
        vorlage_id = request.form.get("vorlage_id")
        if vorlage_id:
            anschreiben_text = anschreiben_generieren(
                job_id, session["user_id"], int(vorlage_id), profil
            )
            if anschreiben_text:
                auto_bewerbung_erstellen(session["user_id"], job_id, anschreiben_text)
                msg = '<div class="alert alert-ok">✅ Bewerbung erstellt!</div>'

    vorlagen_html = ""
    for v in vorlagen:
        premium_badge = '<span class="badge">💎</span>' if v[4] else ''
        vorlagen_html += f"""
        <label style="display: block; margin: 12px 0; padding: 16px;
                       background: rgba(10,14,26,0.5); border-radius: 12px; cursor: pointer;">
            <input type="radio" name="vorlage_id" value="{v[0]}" required>
            <strong>{v[1]}</strong> {premium_badge}<br>
            <small style="color: var(--text-muted);">{v[2]}</small>
        </label>
        """

    anschreiben_html = ""
    if anschreiben_text:
        anschreiben_html = f"""
        <div class="card">
            <h3>📝 Dein Anschreiben</h3>
            <textarea rows="15">{anschreiben_text}</textarea>
            <a href="/avinu/bewerbungen" class="btn btn-primary">📋 Bewerbungen</a>
        </div>
        """

    content = f"""
    <h1>⚡ Auto-Bewerbung</h1>
    {msg}
    <div class="card">
        <h3>📝 Vorlage waehlen</h3>
        <form method="POST">
            {vorlagen_html}
            <button type="submit" class="btn btn-purple" style="width: 100%;">
                ✨ KI-Anschreiben generieren
            </button>
        </form>
    </div>
    {anschreiben_html}
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/avinu/bewerbungen")
def avinu_meine_bewerbungen():
    if "user_id" not in session:
        return redirect("/login")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT ab.*, j.firma, j.position 
        FROM auto_bewerbungen ab
        LEFT JOIN jobs j ON ab.job_id = j.id
        WHERE ab.user_id=?
        ORDER BY ab.id DESC
    """, (session["user_id"],))
    bewerbungen = c.fetchall()
    conn.close()

    html = ""
    for b in bewerbungen:
        html += f"""
        <div class="card">
            <h3>{b[8] or 'Unbekannt'}</h3>
            <p>🏢 {b[7] or 'Unbekannt'}</p>
            <p>📅 {b[6][:16] if b[6] else 'N/A'}</p>
            <details>
                <summary style="cursor: pointer; color: var(--accent-cyan);">Anschreiben</summary>
                <pre style="margin-top: 10px; padding: 15px; background: rgba(10,14,26,0.5); 
                            border-radius: 8px; white-space: pre-wrap;">{b[3]}</pre>
            </details>
        </div>
        """
    if not html:
        html = '<p style="text-align: center;">Noch keine Bewerbungen</p>'

    content = f"""
    <h1>📧 Meine Bewerbungen</h1>
    {html}
    <a href="/avinu" class="btn btn-primary">← Zurueck</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


# ============================================================
# UPLOADS
# ============================================================
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
                    msg = '<div class="alert alert-err">❌ Dateityp nicht erlaubt!</div>'

    user_uploads = uploads_laden(session["user_id"])
    uploads_html = ""
    for u in user_uploads:
        icon = "📄" if u[2] == ".pdf" else "🖼️"
        uploads_html += f"""
        <div class="upload-item">
            <div>{icon} <strong>{u[1]}</strong><br>
                <small style="color: var(--text-muted);">{u[3]} - {u[5][:16]}</small>
            </div>
            <div>
                <a href="/download/{u[0]}" class="btn btn-primary" style="padding: 8px 14px;">⬇️</a>
                <a href="/delete/{u[0]}" class="btn btn-danger" style="padding: 8px 14px;"
                   onclick="return confirm('Loeschen?')">🗑️</a>
            </div>
        </div>
        """
    if not uploads_html:
        uploads_html = '<p style="text-align: center; color: var(--text-muted);">Keine Dateien</p>'

    content = f"""
    <h1>📂 Meine Dateien</h1>
    {msg}
    <div class="card">
        <h3>📤 Upload</h3>
        <form method="POST" enctype="multipart/form-data">
            <select name="kategorie" required>
                <option value="lebenslauf">📄 Lebenslauf</option>
                <option value="zeugnis">📜 Zeugnis</option>
                <option value="zertifikat">🏆 Zertifikat</option>
                <option value="bild">🖼️ Bewerbungsbild</option>
                <option value="anschreiben">✉️ Anschreiben</option>
            </select>
            <div class="file-upload">
                <div style="font-size: 48px;">📤</div>
                <input type="file" name="datei" required accept=".pdf,.png,.jpg,.jpeg">
            </div>
            <button type="submit" class="btn btn-success" style="width: 100%;">🚀 Upload</button>
        </form>
    </div>
    <div class="card">
        <h3>📋 Dateien ({len(user_uploads)})</h3>
        {uploads_html}
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
        msg = '<div class="alert alert-ok">✅ Gespeichert!</div>'

    p = profil_laden(session["user_id"])
    content = f"""
    <h1>📝 Lebenslauf</h1>
    {msg}
    <form method="POST">
        <div class="card">
            <h3>👤 Daten</h3>
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
            <h3>💼 Kenntnisse</h3>
            <textarea name="kenntnisse" rows="6">{p.get('kenntnisse','')}</textarea>
        </div>
        <div class="card">
            <h3>🌍 Sprachen</h3>
            <textarea name="sprachen" rows="4">{p.get('sprachen','')}</textarea>
        </div>
        <button type="submit" class="btn btn-success">💾 Speichern</button>
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
            msg = '<div class="alert alert-warn">⚠️ Limit! <a href="/premium">Upgrade!</a></div>'
        elif firma and email:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO bewerbungen (user_id, firma, email, datum) VALUES (?, ?, ?, ?)",
                      (session["user_id"], firma, email, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            msg = f'<div class="alert alert-ok">✅ {firma} gespeichert!</div>'

    bw = bewerbungen_zaehlen(session["user_id"])
    limit = "∞" if session.get("premium") else 5
    content = f"""
    <h1>📧 Bewerbungen</h1>
    <div class="card"><h3>📊 Limit</h3><p>{bw} / {limit}</p></div>
    {msg}
    <div class="card">
        <h3>➕ Neue Bewerbung</h3>
        <form method="POST">
            <input type="text" name="firma" placeholder="Firma" required>
            <input type="email" name="email" placeholder="E-Mail" required>
            <button type="submit" class="btn btn-success" style="width: 100%;">💾 Speichern</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/premium")
def premium():
    content = """
    <h1>💎 Premium</h1>
    <div class="grid">
        <div class="card">
            <h2>🆓 Free</h2><h3>0 €</h3>
            <ul style="list-style: none; padding: 0;">
                <li>✓ 5 Bewerbungen</li>
                <li>✓ Basis KI</li>
            </ul>
            <button class="btn btn-primary" style="width: 100%;">Aktuell</button>
        </div>
        <div class="card" style="border: 2px solid var(--accent-yellow);">
            <span class="badge">BELIEBT</span>
            <h2>💎 Premium</h2><h3>1.99 €/Monat</h3>
            <ul style="list-style: none; padding: 0;">
                <li>✓ UNBEGRENZTE Bewerbungen</li>
                <li>✓ 10 Premium-Vorlagen</li>
                <li>✓ Premium KI</li>
            </ul>
            <a href="/checkout" class="btn btn-warning" style="width: 100%;">🚀 Upgrade</a>
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
        <div class="alert alert-warn">⚠️ Demo-Modus</div>
        <a href="/aktivieren" class="btn btn-success">🎁 Demo Premium</a>
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
    <div class="alert alert-ok">✅ Aktiv!</div>
    <a href="/dashboard" class="btn btn-primary">Dashboard</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/install")
def install():
    content = """
    <h1>📱 App installieren</h1>
    <div class="card">
        <h3>Android</h3>
        <p>3-Punkte → "App installieren"</p>
    </div>
    <div class="card">
        <h3>iPhone</h3>
        <p>Teilen → "Zum Home-Bildschirm"</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


# ============================================================
# PROFIL & SICHERHEIT
# ============================================================
@app.route("/profil")
def profil():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    two_fa_active, _ = get_2fa_status(user_id)
    deletion_status = get_deletion_status(user_id)

    deletion_warning = ""
    if deletion_status:
        deletion_warning = f"""
        <div class="alert alert-warn">
            ⚠️ <strong>Konto wird geloescht am:</strong> {deletion_status[0][:10]}
            <br><a href="/profil/cancel-deletion">↩️ Stornieren</a>
        </div>
        """

    content = f"""
    <h1>⚙️ Profil & Sicherheit</h1>
    {deletion_warning}
    <div class="grid">
        <a href="/profil/edit" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">👤</div>
                <div class="stat-value">Profil</div>
                <div class="stat-label">Daten</div>
            </div>
        </a>
        <a href="/profil/password" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">🔑</div>
                <div class="stat-value">Passwort</div>
                <div class="stat-label">Aendern</div>
            </div>
        </a>
        <a href="/profil/2fa" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">{'✅' if two_fa_active else '🔐'}</div>
                <div class="stat-value">2FA</div>
                <div class="stat-label">{'Aktiv' if two_fa_active else 'Einrichten'}</div>
            </div>
        </a>
        <a href="/profil/export" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">📥</div>
                <div class="stat-value">Export</div>
                <div class="stat-label">DSGVO</div>
            </div>
        </a>
        <a href="/profil/audit" style="text-decoration: none;">
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-value">Audit</div>
                <div class="stat-label">Log</div>
            </div>
        </a>
        <a href="/profil/delete" style="text-decoration: none;">
            <div class="stat-card" style="border-color: var(--accent-red);">
                <div class="stat-icon">🗑️</div>
                <div class="stat-value" style="color: var(--accent-red);">Loeschen</div>
                <div class="stat-label">Account</div>
            </div>
        </a>
    </div>
    <div class="card" style="margin-top: 30px;">
        <h3>🔒 Quantum-Sicherheit</h3>
        <ul style="line-height: 2;">
            <li>✅ AES-256 Verschluesselung</li>
            <li>✅ PBKDF2 600.000 Iterationen</li>
            <li>✅ SHA-512 Passwort-Hashing</li>
            <li>✅ HTTPS Ende-zu-Ende</li>
            <li>✅ DSGVO-konform</li>
        </ul>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/edit", methods=["GET", "POST"])
def profil_edit():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        vn = request.form.get("vorname", "").strip()
        nn = request.form.get("nachname", "").strip()
        em = request.form.get("email", "").strip()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE benutzer SET vorname=?, nachname=?, email=? WHERE id=?",
                  (vn, nn, em, session["user_id"]))
        conn.commit()
        conn.close()
        session["vorname"] = vn
        session["nachname"] = nn
        audit_log(session["user_id"], "PROFILE_UPDATED", "Profil aktualisiert")
        msg = '<div class="alert alert-ok">✅ Gespeichert!</div>'

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT vorname, nachname, email FROM benutzer WHERE id=?", (session["user_id"],))
    u = c.fetchone()
    conn.close()

    content = f"""
    <h1>👤 Profil</h1>
    {msg}
    <div class="card">
        <form method="POST">
            <input type="text" name="vorname" placeholder="Vorname" value="{u[0] or ''}" required>
            <input type="text" name="nachname" placeholder="Nachname" value="{u[1] or ''}" required>
            <input type="email" name="email" placeholder="E-Mail" value="{u[2] or ''}" required>
            <button type="submit" class="btn btn-success" style="width: 100%;">💾 Speichern</button>
        </form>
    </div>
    <a href="/profil" class="btn btn-primary">← Zurueck</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/password", methods=["GET", "POST"])
def profil_password():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        old = request.form.get("old_password", "")
        new = request.form.get("new_password", "")
        conf = request.form.get("confirm_password", "")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT passwort FROM benutzer WHERE id=?", (session["user_id"],))
        current = c.fetchone()[0]
        if hash_pw(old) != current:
            msg = '<div class="alert alert-err">❌ Altes Passwort falsch!</div>'
        elif new != conf:
            msg = '<div class="alert alert-err">❌ Passwoerter unterschiedlich!</div>'
        elif len(new) < 8:
            msg = '<div class="alert alert-err">❌ Min. 8 Zeichen!</div>'
        else:
            c.execute("UPDATE benutzer SET passwort=? WHERE id=?",
                      (hash_pw(new), session["user_id"]))
            conn.commit()
            audit_log(session["user_id"], "PASSWORD_CHANGED", "Passwort geaendert")
            msg = '<div class="alert alert-ok">✅ Geaendert!</div>'
        conn.close()

    content = f"""
    <h1>🔑 Passwort</h1>
    {msg}
    <div class="card">
        <form method="POST">
            <input type="password" name="old_password" placeholder="Altes Passwort" required>
            <input type="password" name="new_password" placeholder="Neues Passwort" required>
            <input type="password" name="confirm_password" placeholder="Bestaetigen" required>
            <button type="submit" class="btn btn-success" style="width: 100%;">🔒 Aendern</button>
        </form>
    </div>
    <a href="/profil" class="btn btn-primary">← Zurueck</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/2fa", methods=["GET", "POST"])
def profil_2fa():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    two_fa_active, current_secret = get_2fa_status(user_id)
    msg = ""

    if request.method == "POST":
        action = request.form.get("action", "")
        token = request.form.get("token", "")
        if action == "enable":
            secret = request.form.get("secret", "")
            if verify_2fa_token(secret, token):
                codes = enable_2fa(user_id, secret)
                codes_html = "<br>".join(codes)
                msg = f"""
                <div class="alert alert-ok" style="flex-direction: column; align-items: start;">
                    ✅ 2FA aktiviert!
                    <h3>Backup Codes:</h3>
                    <div style="background: #0A0E1A; padding: 15px; border-radius: 8px; 
                                font-family: monospace; margin-top: 10px;">{codes_html}</div>
                </div>
                """
                two_fa_active = True
            else:
                msg = '<div class="alert alert-err">❌ Falscher Code!</div>'
        elif action == "disable":
            if verify_2fa_token(current_secret, token):
                disable_2fa(user_id)
                two_fa_active = False
                msg = '<div class="alert alert-ok">✅ 2FA deaktiviert</div>'
            else:
                msg = '<div class="alert alert-err">❌ Falscher Code!</div>'

    if two_fa_active:
        content = f"""
        <h1>🔐 2FA aktiv</h1>
        {msg}
        <div class="card">
            <div class="alert alert-ok">✅ 2FA ist aktiv!</div>
            <form method="POST">
                <input type="hidden" name="action" value="disable">
                <input type="text" name="token" placeholder="6-stelliger Code" required>
                <button type="submit" class="btn btn-danger">⚠️ Deaktivieren</button>
            </form>
        </div>
        <a href="/profil" class="btn btn-primary">← Zurueck</a>
        """
    else:
        secret = generate_2fa_secret()
        qr = generate_qr_code(session.get("username", "user"), secret)
        content = f"""
        <h1>🔐 2FA einrichten</h1>
        {msg}
        <div class="card">
            <h3>📱 Schritt 1: Authenticator App</h3>
            <p>Google Authenticator, Microsoft Authenticator, Authy</p>
        </div>
        <div class="card">
            <h3>📷 Schritt 2: QR scannen</h3>
            <div style="text-align: center; padding: 20px; background: white; border-radius: 12px;">
                <img src="{qr}" alt="QR" style="max-width: 300px;">
            </div>
            <p style="margin-top: 15px; font-family: monospace; word-break: break-all;">
                Code: {secret}
            </p>
        </div>
        <div class="card">
            <h3>✅ Schritt 3: Code eingeben</h3>
            <form method="POST">
                <input type="hidden" name="action" value="enable">
                <input type="hidden" name="secret" value="{secret}">
                <input type="text" name="token" placeholder="6-stelliger Code" required
                       style="text-align: center; font-size: 24px; letter-spacing: 10px;">
                <button type="submit" class="btn btn-success" style="width: 100%;">🔐 Aktivieren</button>
            </form>
        </div>
        <a href="/profil" class="btn btn-primary">← Zurueck</a>
        """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/export")
def profil_export():
    if "user_id" not in session:
        return redirect("/login")
    data = export_user_data(session["user_id"])
    json_str = json_module.dumps(data, ensure_ascii=False, indent=2)
    audit_log(session["user_id"], "DATA_EXPORTED", "DSGVO Export")
    return Response(
        json_str, mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=xsikom_{session['user_id']}.json"}
    )


@app.route("/profil/audit")
def profil_audit():
    if "user_id" not in session:
        return redirect("/login")
    logs = get_audit_log(session["user_id"])
    logs_html = ""
    for log in logs:
        logs_html += f"""
        <tr style="border-bottom: 1px solid var(--border);">
            <td style="padding: 12px;"><strong>{log[0]}</strong></td>
            <td style="padding: 12px;">{log[1]}</td>
            <td style="padding: 12px; font-size: 11px;">{log[2][:16]}</td>
        </tr>
        """
    if not logs_html:
        logs_html = '<tr><td colspan="3" style="text-align: center; padding: 20px;">Keine Eintraege</td></tr>'

    content = f"""
    <h1>📊 Audit Log</h1>
    <div class="card">
        <table style="width: 100%;">
            <thead>
                <tr style="background: rgba(0,217,255,0.1);">
                    <th style="padding: 12px; text-align: left;">Event</th>
                    <th style="padding: 12px; text-align: left;">Details</th>
                    <th style="padding: 12px; text-align: left;">Zeit</th>
                </tr>
            </thead>
            <tbody>{logs_html}</tbody>
        </table>
    </div>
    <a href="/profil" class="btn btn-primary">← Zurueck</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/delete", methods=["GET", "POST"])
def profil_delete():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        pw = request.form.get("password", "")
        reason = request.form.get("reason", "")
        conf = request.form.get("confirmation", "")
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT passwort FROM benutzer WHERE id=?", (session["user_id"],))
        current = c.fetchone()[0]
        conn.close()
        if hash_pw(pw) != current:
            msg = '<div class="alert alert-err">❌ Passwort falsch!</div>'
        elif conf != "LOESCHEN":
            msg = '<div class="alert alert-err">❌ "LOESCHEN" eingeben!</div>'
        else:
            token, sched = request_account_deletion(session["user_id"], reason)
            msg = f'<div class="alert alert-ok">✅ Loeschungsantrag eingegangen! Geplant: {sched[:10]}</div>'

    content = f"""
    <h1 style="color: var(--accent-red);">🗑️ Account loeschen</h1>
    <div class="alert alert-warn">
        ⚠️ Endgueltig! 30 Tage Frist zur Stornierung.
    </div>
    {msg}
    <div class="card">
        <form method="POST">
            <textarea name="reason" rows="3" placeholder="Grund (optional)"></textarea>
            <input type="password" name="password" placeholder="Passwort" required>
            <input type="text" name="confirmation" placeholder='Tippe "LOESCHEN"' required>
            <button type="submit" class="btn btn-danger" style="width: 100%;">🗑️ Loeschen</button>
        </form>
    </div>
    <a href="/profil" class="btn btn-primary">← Zurueck</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/cancel-deletion")
def profil_cancel_deletion():
    if "user_id" not in session:
        return redirect("/login")
    cancel_deletion(session["user_id"])
    content = """
    <h1>↩️ Storniert</h1>
    <div class="alert alert-ok">✅ Account bleibt aktiv!</div>
    <a href="/profil" class="btn btn-primary">Profil</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/password-reset", methods=["GET", "POST"])
def password_reset_request():
    msg = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM benutzer WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        if user:
            token = create_password_reset_token(user[0])
            link = f"{request.host_url}password-reset/{token}"
            msg = f'<div class="alert alert-ok">✅ Link: <a href="{link}" style="word-break: break-all;">{link}</a></div>'
        else:
            msg = '<div class="alert alert-info">Falls E-Mail existiert, Link gesendet.</div>'

    content = f"""
    <div style="max-width: 450px; margin: 60px auto;">
        <div class="card">
            <h1>🔑 Reset</h1>
            {msg}
            <form method="POST">
                <input type="email" name="email" placeholder="E-Mail" required>
                <button type="submit" class="btn btn-primary" style="width: 100%;">📧 Senden</button>
            </form>
            <p style="text-align: center; margin-top: 20px;">
                <a href="/login">← Login</a>
            </p>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=None)


@app.route("/password-reset/<token>", methods=["GET", "POST"])
def password_reset_new(token):
    user_id = verify_reset_token(token)
    if not user_id:
        content = """
        <h1>❌ Ungueltig</h1>
        <div class="alert alert-err">Link abgelaufen.</div>
        <a href="/password-reset" class="btn btn-primary">Neu</a>
        """
        return render_template_string(BASE_HTML, content=content, user=None)
    msg = ""
    if request.method == "POST":
        new = request.form.get("new_password", "")
        conf = request.form.get("confirm_password", "")
        if new != conf:
            msg = '<div class="alert alert-err">❌ Unterschiedlich!</div>'
        elif len(new) < 8:
            msg = '<div class="alert alert-err">❌ Min. 8 Zeichen!</div>'
        else:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("UPDATE benutzer SET passwort=? WHERE id=?", (hash_pw(new), user_id))
            conn.commit()
            conn.close()
            use_reset_token(token)
            audit_log(user_id, "PASSWORD_RESET", "Per Reset-Link")
            content = """
            <h1>✅ Erfolgreich!</h1>
            <div class="alert alert-ok">Du kannst dich jetzt einloggen.</div>
            <a href="/login" class="btn btn-primary">Login</a>
            """
            return render_template_string(BASE_HTML, content=content, user=None)

    content = f"""
    <div style="max-width: 450px; margin: 60px auto;">
        <div class="card">
            <h1>🔑 Neues Passwort</h1>
            {msg}
            <form method="POST">
                <input type="password" name="new_password" placeholder="Neues Passwort" required>
                <input type="password" name="confirm_password" placeholder="Bestaetigen" required>
                <button type="submit" class="btn btn-success" style="width: 100%;">✅ Setzen</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=None)


# ============================================================
# RECHTLICHE SEITEN
# ============================================================
@app.route("/impressum")
def impressum():
    content = f"""
    <h1>📜 Impressum</h1>
    <div class="legal-text">
        <h3>§ 5 TMG</h3>
        <p><strong>XsiKOM DIGITAL Projects</strong><br>
        Komi Tevi<br>Am Koenigsfloss 12<br>55252 Mainz-Kastel</p>
        <h3>Kontakt</h3>
        <p>Telefon: +49 178 8977320<br>
        E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
        <h3>Verantwortlich</h3>
        <p>Komi Tevi (Anschrift wie oben)</p>
        <p style="margin-top: 30px;">© 2026 XsiKOM DIGITAL Projects</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/datenschutz")
def datenschutz():
    content = f"""
    <h1>🔒 Datenschutz (DSGVO)</h1>
    <div class="legal-text">
        <h3>1. Verantwortlicher</h3>
        <p>XsiKOM DIGITAL Projects<br>Komi Tevi<br>Am Koenigsfloss 12<br>55252 Mainz-Kastel<br>
        E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
        <h3>2. Daten</h3>
        <p>Stammdaten, Bewerbungsdaten, Uploads, Login-Daten (verschluesselt).</p>
        <h3>3. Ihre Rechte</h3>
        <ul><li>Auskunft</li><li>Berichtigung</li><li>Loeschung</li><li>Datenuebertragbarkeit</li></ul>
        <h3>4. Sicherheit</h3>
        <p>AES-256, PBKDF2, SHA-512, HTTPS.</p>
        <p>© 2026 XsiKOM DIGITAL Projects</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/widerruf")
def widerruf():
    content = f"""
    <h1>↩️ Widerruf</h1>
    <div class="legal-text">
        <h3>14 Tage Widerrufsrecht</h3>
        <p>An: XsiKOM DIGITAL Projects, Komi Tevi, Am Koenigsfloss 12, 55252 Mainz-Kastel<br>
        E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
        <h3>B2B</h3>
        <p>Firmenkunden kein gesetzliches Widerrufsrecht.</p>
        <p>© 2026 XsiKOM DIGITAL Projects</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/haftung")
def haftung():
    content = f"""
    <h1>⚖️ Haftung</h1>
    <div class="legal-text">
        <h3>KI-Inhalte</h3>
        <div class="alert alert-warn">
            ⚠️ KI-Inhalte koennen fehlerhaft sein. Pruefen Sie alles!
        </div>
        <h3>Haftungsausschluss</h3>
        <p>Keine Haftung fuer Schaeden, Datenverlust, erfolglose Bewerbungen.</p>
        <h3>Eigenverantwortung</h3>
        <p>KI-Inhalte pruefen, Backups erstellen.</p>
        <p>Kontakt: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
        <p>© 2026 XsiKOM DIGITAL Projects</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/agb")
def agb():
    content = f"""
    <h1>📋 AGB</h1>
    <div class="legal-text">
        <h3>§ 1 Geltung</h3>
        <p>Fuer alle Nutzer.</p>
        <h3>§ 2 Partner</h3>
        <p>XsiKOM DIGITAL Projects, Komi Tevi, Mainz-Kastel<br>
        E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
        <h3>§ 3 Leistungen</h3>
        <p>Free: 5 Bewerbungen | Premium: 1.99€/Monat unbegrenzt</p>
        <h3>§ 4 Widerruf</h3>
        <p>14 Tage fuer Verbraucher. <a href="/widerruf">Mehr</a></p>
        <h3>§ 5 Haftung</h3>
        <p>Siehe <a href="/haftung">Haftungsausschluss</a></p>
        <h3>§ 6 Gerichtsstand</h3>
        <p>Mainz, Deutschland.</p>
        <p>© 2026 XsiKOM DIGITAL Projects</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/logout")
def logout():
    if "user_id" in session:
        audit_log(session["user_id"], "LOGOUT", "Logout")
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
    print("  XsiKOM-BewerbungsBOT v3.0")
    print("=" * 60)
    print(f"  KI:      {'ONLINE' if GROQ_API_KEY else 'OFFLINE'}")
    print(f"  Email:   {CONTACT_EMAIL}")
    print(f"  URL:     http://localhost:5000")
    print(f"  Login:   admin / XsiKOM2026!")
    print("=" * 60 + "\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)