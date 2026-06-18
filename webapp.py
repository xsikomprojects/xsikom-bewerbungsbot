"""
XsiKOM-BewerbungsBOT v4.0
Mit AVINU Bot, 6 Portale, Umkreissuche, 200+ Berufe
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
    avinu_antwort, alle_jobs_suchen, get_alle_berufe,
    jobs_speichern, jobs_laden, vorlagen_laden,
    anschreiben_generieren, auto_bewerbung_erstellen,
    job_favorit_toggle, job_loeschen, BRANCHEN
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


# KI
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_ki_antwort(frage):
    if not GROQ_API_KEY:
        return "KI offline."
    try:
        response = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "Du bist Aaliyah, KI-Karriereberaterin. Antworte auf Deutsch."},
                    {"role": "user", "content": frage}
                ],
                "temperature": 0.7, "max_tokens": 500
            },
            timeout=20
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return "Fehler."
    except Exception:
        return "Verbindung fehlgeschlagen."


def aaliyah_tipp():
    return random.choice([
        "Passe dein Anschreiben individuell an!",
        "Erwaehne konkrete Projekte der Firma.",
        "Halte das Anschreiben max. 1 Seite.",
        "Zeige Motivation!",
        "Pruefe auf Rechtschreibung.",
    ])


# DB
def db_init():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS benutzer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        benutzername TEXT UNIQUE NOT NULL, passwort TEXT NOT NULL,
        email TEXT, vorname TEXT, nachname TEXT,
        rolle TEXT DEFAULT 'user', premium INTEGER DEFAULT 0,
        kunde_typ TEXT DEFAULT 'privat', erstellt TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS bewerbungen (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        firma TEXT, email TEXT, status TEXT DEFAULT 'gesendet', datum TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS profile (
        user_id INTEGER PRIMARY KEY,
        vorname TEXT, nachname TEXT, strasse TEXT, plz TEXT, stadt TEXT,
        telefon TEXT, email TEXT, geburtsdatum TEXT,
        kenntnisse TEXT, sprachen TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        dateiname TEXT, typ TEXT, kategorie TEXT, pfad TEXT, upload_datum TEXT)""")
    conn.commit()
    conn.close()


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def admin_anlegen():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM benutzer WHERE benutzername='admin'")
    if not c.fetchone():
        c.execute("""INSERT INTO benutzer
            (benutzername, passwort, email, vorname, nachname, rolle, premium, erstellt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("admin", hash_pw("XsiKOM2026!"), CONTACT_EMAIL, "Komi", "Tevi",
             "admin", 1, datetime.now().isoformat()))
        conn.commit()
    conn.close()


def benutzer_pruefen(user, pw):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, benutzername, vorname, nachname, rolle, premium FROM benutzer WHERE benutzername=? AND passwort=?",
              (user, hash_pw(pw)))
    r = c.fetchone()
    conn.close()
    if r:
        return {"id": r[0], "benutzername": r[1], "vorname": r[2],
                "nachname": r[3], "rolle": r[4], "premium": r[5]}
    return None


def benutzer_anlegen(user, pw, email, vn, nn, kunde_typ="privat"):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""INSERT INTO benutzer
            (benutzername, passwort, email, vorname, nachname, kunde_typ, erstellt)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user, hash_pw(pw), email, vn, nn, kunde_typ, datetime.now().isoformat()))
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
    c.execute("SELECT COUNT(*) FROM bewerbungen WHERE user_id=? AND datum >= ?",
              (user_id, monat_start))
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
    return {"vorname": r[1] or "", "nachname": r[2] or "", "strasse": r[3] or "",
            "plz": r[4] or "", "stadt": r[5] or "", "telefon": r[6] or "",
            "email": r[7] or "", "geburtsdatum": r[8] or "",
            "kenntnisse": r[9] or "", "sprachen": r[10] or ""}


def profil_speichern(user_id, daten):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM profile WHERE user_id=?", (user_id,))
    c.execute("""INSERT INTO profile
        (user_id, vorname, nachname, strasse, plz, stadt,
         telefon, email, geburtsdatum, kenntnisse, sprachen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, daten.get("vorname",""), daten.get("nachname",""),
         daten.get("strasse",""), daten.get("plz",""), daten.get("stadt",""),
         daten.get("telefon",""), daten.get("email",""), daten.get("geburtsdatum",""),
         daten.get("kenntnisse",""), daten.get("sprachen","")))
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
    c.execute("""INSERT INTO uploads (user_id, dateiname, typ, kategorie, pfad, upload_datum)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, neuer_name, ext_lower, kategorie, pfad, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return neuer_name


def uploads_laden(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, dateiname, typ, kategorie, pfad, upload_datum FROM uploads WHERE user_id=? ORDER BY id DESC",
              (user_id,))
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


# HTML
BASE_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>XsiKOM</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#00D9FF">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
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
    --bg-card: rgba(20, 28, 48, 0.6);
    --border: rgba(255, 255, 255, 0.08);
    --accent-cyan: #00D9FF;
    --accent-purple: #8B5CF6;
    --accent-green: #10F4B1;
    --accent-yellow: #FFD93D;
    --accent-red: #FF4757;
    --text-primary: #FFFFFF;
    --text-secondary: #A0AEC0;
    --text-muted: #6B7280;
}
body { font-family: 'Poppins', sans-serif; background: var(--bg-primary); color: var(--text-primary); min-height: 100vh; }
body::before { content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(circle at 20% 20%, rgba(0,217,255,0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(139,92,246,0.15) 0%, transparent 50%);
    z-index: -1; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.header { background: rgba(10,14,26,0.8); backdrop-filter: blur(20px);
    padding: 20px 0; border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100; }
.header-inner { display: flex; justify-content: space-between; align-items: center; }
.logo { font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 700;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; }
.subtitle { color: var(--text-secondary); font-size: 13px; }
.nav { background: rgba(19,24,41,0.5); padding: 12px 0; border-bottom: 1px solid var(--border);
    overflow-x: auto; white-space: nowrap; }
.nav-inner { max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; gap: 5px; }
.nav a { color: var(--text-secondary); text-decoration: none; padding: 10px 18px;
    border-radius: 12px; font-size: 14px; transition: all 0.3s; }
.nav a:hover { color: var(--text-primary); background: rgba(0,217,255,0.1); }
.card { background: var(--bg-card); backdrop-filter: blur(20px);
    border-radius: 20px; padding: 30px; margin: 20px 0;
    border: 1px solid var(--border); transition: all 0.4s; }
.card:hover { transform: translateY(-5px); border-color: rgba(0,217,255,0.3); }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    padding: 14px 28px; border: none; border-radius: 12px; cursor: pointer;
    font-weight: 600; font-size: 14px; text-decoration: none; transition: all 0.3s;
    font-family: 'Poppins', sans-serif; }
.btn:hover { transform: translateY(-2px); }
.btn-primary { background: linear-gradient(135deg, var(--accent-cyan), #0099CC); color: white; }
.btn-success { background: linear-gradient(135deg, var(--accent-green), #059669); color: white; }
.btn-warning { background: linear-gradient(135deg, var(--accent-yellow), #F59E0B); color: #0A0E1A; }
.btn-danger { background: linear-gradient(135deg, var(--accent-red), #DC2626); color: white; }
.btn-purple { background: linear-gradient(135deg, var(--accent-purple), #6D28D9); color: white; }
input, textarea, select { background: rgba(10,14,26,0.6); border: 1px solid var(--border);
    color: var(--text-primary); padding: 14px 18px; border-radius: 12px;
    width: 100%; margin-bottom: 12px; font-size: 14px;
    font-family: 'Poppins', sans-serif; }
input:focus, textarea:focus, select:focus { outline: none; border-color: var(--accent-cyan);
    box-shadow: 0 0 0 4px rgba(0,217,255,0.1); }
h1 { font-family: 'Space Grotesk', sans-serif; font-size: 36px; font-weight: 700;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; margin-bottom: 20px; }
h2 { font-size: 26px; font-weight: 600; margin-bottom: 16px; }
h3 { font-size: 18px; font-weight: 600; color: var(--accent-cyan); margin-bottom: 12px; }
p { line-height: 1.7; color: var(--text-secondary); margin-bottom: 8px; }
a { color: var(--accent-cyan); text-decoration: none; }
a:hover { color: var(--accent-purple); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; }
.stat-card { background: linear-gradient(135deg, rgba(20,28,48,0.8), rgba(30,38,58,0.6));
    border: 1px solid var(--border); border-radius: 20px; padding: 30px;
    text-align: center; transition: all 0.4s; cursor: pointer; }
.stat-card:hover { transform: translateY(-8px); border-color: var(--accent-cyan); }
.stat-icon { font-size: 48px; margin-bottom: 12px; }
.stat-value { font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 700;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; }
.stat-label { color: var(--text-secondary); font-size: 13px; margin-top: 4px; }
.badge { background: linear-gradient(135deg, var(--accent-yellow), #EC4899);
    color: var(--bg-primary); padding: 6px 14px; border-radius: 20px;
    font-size: 11px; font-weight: 700; display: inline-block; }
.alert { padding: 16px 20px; border-radius: 12px; margin: 16px 0;
    border: 1px solid; display: flex; align-items: center; gap: 12px; }
.alert-ok { background: rgba(16,244,177,0.1); border-color: rgba(16,244,177,0.3); color: var(--accent-green); }
.alert-err { background: rgba(255,71,87,0.1); border-color: rgba(255,71,87,0.3); color: var(--accent-red); }
.alert-warn { background: rgba(255,217,61,0.1); border-color: rgba(255,217,61,0.3); color: var(--accent-yellow); }
.alert-info { background: rgba(0,217,255,0.1); border-color: rgba(0,217,255,0.3); color: var(--accent-cyan); }
.upload-item { background: rgba(10,14,26,0.6); padding: 16px; border-radius: 12px;
    margin: 10px 0; display: flex; justify-content: space-between;
    align-items: center; border: 1px solid var(--border); }
.footer { background: rgba(10,14,26,0.9); padding: 40px 20px 30px;
    text-align: center; color: var(--text-muted); margin-top: 60px;
    border-top: 1px solid var(--border); }
.footer a { color: var(--text-secondary); margin: 0 12px; }
.footer-brand { margin-top: 16px; font-family: 'Space Grotesk', sans-serif;
    font-weight: 600; color: var(--accent-cyan); }
#cookie-banner { display: none; position: fixed; bottom: 20px; left: 20px; right: 20px;
    max-width: 1160px; margin: 0 auto; background: rgba(20,28,48,0.95);
    color: white; padding: 20px 25px; z-index: 9999;
    border-radius: 16px; border: 1px solid var(--accent-cyan); }
.legal-text { background: var(--bg-card); padding: 30px; border-radius: 20px;
    margin: 20px 0; line-height: 1.8; border: 1px solid var(--border); }
.legal-text h3 { color: var(--accent-cyan); margin-top: 24px; }
@media (max-width: 768px) { h1 { font-size: 28px; } .logo { font-size: 24px; } }
</style>
</head>
<body>
<div id="cookie-banner">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>🍪 Wir verwenden technisch notwendige Cookies. <a href="/datenschutz" style="color: var(--accent-cyan);">Mehr</a></div>
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
<div class="container">{{ content|safe }}</div>
<div class="footer">
    <div>
        <a href="/impressum">Impressum</a>•
        <a href="/datenschutz">Datenschutz</a>•
        <a href="/agb">AGB</a>•
        <a href="/widerruf">Widerruf</a>•
        <a href="/haftung">Haftung</a>
    </div>
    <div class="footer-brand">XsiKOM-BewerbungsBOT</div>
    <div style="margin-top: 8px; font-size: 11px; color: var(--text-muted);">
        © 2026 XsiKOM DIGITAL Projects • Komi Tevi<br>
        <a href="mailto:xsikom_digital@xsikom.de" style="color: var(--text-muted);">xsikom_digital@xsikom.de</a>
    </div>
</div>
</body>
</html>"""


# ROUTEN
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
            audit_log(result["id"], "LOGIN", "Login")
            return redirect("/dashboard")
        msg = '<div class="alert alert-err">❌ Login falsch!</div>'

    content = f"""
    <div style="max-width: 450px; margin: 60px auto;">
        <div class="card">
            <h1 style="text-align: center;">🔐 Anmelden</h1>
            {msg}
            <form method="POST">
                <input type="text" name="username" value="admin" placeholder="Benutzername" required>
                <input type="password" name="password" placeholder="Passwort" required>
                <button type="submit" class="btn btn-primary" style="width: 100%;">🚀 Anmelden</button>
            </form>
            <p style="text-align: center; margin-top: 25px;">
                <a href="/register">✨ Neuen Account erstellen</a>
            </p>
            <p style="text-align: center; margin-top: 10px;">
                <a href="/password-reset" style="color: var(--text-muted); font-size: 13px;">🔑 Passwort vergessen?</a>
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
        if not all([user, pw, email, request.form.get("datenschutz"),
                    request.form.get("agb"), request.form.get("widerruf")]):
            msg = '<div class="alert alert-err">❌ Alle Felder + Zustimmungen!</div>'
        elif len(pw) < 6:
            msg = '<div class="alert alert-err">❌ Min. 6 Zeichen!</div>'
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
                <div style="margin-top: 20px; padding: 20px; background: rgba(10,14,26,0.5); border-radius: 12px;">
                    <p><input type="checkbox" name="datenschutz" required style="width: auto;"> 
                        <a href="/datenschutz" target="_blank">Datenschutz</a></p>
                    <p><input type="checkbox" name="agb" required style="width: auto;"> 
                        <a href="/agb" target="_blank">AGB</a> + <a href="/haftung" target="_blank">Haftung</a></p>
                    <p><input type="checkbox" name="widerruf" required style="width: auto;"> 
                        <a href="/widerruf" target="_blank">Widerrufsrecht</a></p>
                </div>
                <button type="submit" class="btn btn-success" style="width: 100%;">🚀 Account erstellen</button>
            </form>
            <p style="text-align: center; margin-top: 20px;"><a href="/login">← Login</a></p>
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
    upgrade = '<a href="/premium" class="btn btn-warning">💎 Upgrade Premium</a>' if not session.get("premium") else ""

    content = f"""
    <h1>👋 Hallo, {session['vorname']}!</h1>
    <div class="card">
        <h3>📊 Plan: {"Premium" if session.get("premium") else "Free"} {badge}</h3>
        <p>Bewerbungen: <strong>{bw} / {limit}</strong></p>
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
        <h3>💡 Tipp</h3>
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
            antwort = f'<div class="alert alert-info" style="flex-direction: column; align-items: start;"><strong>🤖 Aaliyah:</strong><div style="margin-top: 10px;">{a_html}</div></div>'

    content = f"""
    <h1>🤖 Aaliyah KI</h1>
    <div class="card">
        <form method="POST">
            <input type="text" name="frage" placeholder="Frag Aaliyah..." required>
            <button type="submit" class="btn btn-purple" style="width: 100%;">📤 Senden</button>
        </form>
        {antwort}
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


# AVINU
@app.route("/avinu", methods=["GET", "POST"])
def avinu_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    
    msg = ""
    if request.method == "POST":
        branche = request.form.get("branche", "")
        suchbegriff = request.form.get("suchbegriff", "")
        standort = request.form.get("standort", "")
        radius = int(request.form.get("radius", 25))
        
        if not suchbegriff and branche:
            suchbegriff = BRANCHEN.get(branche, ["Job"])[0]
        
        if suchbegriff and standort:
            try:
                alle_jobs = alle_jobs_suchen(suchbegriff, standort, radius)
                if alle_jobs:
                    anzahl = jobs_speichern(session["user_id"], alle_jobs, branche, radius)
                    msg = f'<div class="alert alert-ok">✅ {anzahl} neue Jobs gefunden!</div>'
                else:
                    msg = '<div class="alert alert-warn">⚠️ Keine Jobs gefunden. Anderen Suchbegriff probieren!</div>'
            except Exception as e:
                msg = f'<div class="alert alert-err">❌ Fehler: {str(e)[:100]}</div>'
    
    filter_typ = request.args.get("filter", "offen")
    jobs = jobs_laden(session["user_id"], filter_typ)
    
    berufe_options = ""
    for beruf in get_alle_berufe():
        berufe_options += f'<option value="{beruf}">'
    
    branchen_html = ""
    namen = {"it": "💻 IT", "handwerk": "🔧 Handwerk", "gesundheit": "🏥 Gesundheit",
             "verwaltung": "📋 Verwaltung", "verkauf": "🛒 Verkauf",
             "logistik": "📦 Logistik", "gastronomie": "🍽️ Gastronomie",
             "bildung": "📚 Bildung", "marketing": "📱 Marketing",
             "finanzen": "💰 Finanzen", "transport": "🚚 Transport",
             "produktion": "🏭 Produktion", "reinigung": "🧹 Reinigung",
             "sicherheit": "🛡️ Sicherheit"}
    for key, name in namen.items():
        branchen_html += f'<option value="{key}">{name}</option>'
    
    jobs_html = ""
    for j in jobs[:30]:
        beworben_badge = '<span style="background: var(--accent-green); color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px;">✅ Beworben</span>' if j[11] else ''
        favorit = j[13] if len(j) > 13 else 0
        fav_icon = "⭐" if favorit else "☆"
        url_link = f'<a href="{j[6]}" target="_blank">🔗 Original</a>' if j[6] else ""
        beschr = j[5][:200] + "..." if j[5] and len(j[5]) > 200 else (j[5] or "")
        
        jobs_html += f"""
        <div class="card">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                <div style="flex: 1; min-width: 280px;">
                    <h3>💼 {j[3]} {beworben_badge}</h3>
                    <p style="color: var(--accent-cyan); font-size: 16px;">🏢 <strong>{j[2]}</strong></p>
                    <p style="color: var(--text-secondary); font-size: 13px;">
                        📍 {j[4]} · 🔗 {j[9]} · 🏷️ {j[8]}
                    </p>
                    {f'<p style="color: var(--text-muted); font-size: 13px; margin: 8px 0;">{beschr}</p>' if beschr else ''}
                    <p>{url_link}</p>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <a href="/avinu/bewerben/{j[0]}" class="btn btn-success">⚡ Bewerben</a>
                    <a href="/avinu/favorit/{j[0]}" class="btn btn-warning" style="padding: 8px 14px;">{fav_icon}</a>
                    <a href="/avinu/loeschen/{j[0]}" class="btn btn-danger" style="padding: 8px 14px;"
                       onclick="return confirm('Loeschen?')">🗑️</a>
                </div>
            </div>
        </div>
        """
    
    if not jobs_html:
        jobs_html = '<p style="text-align: center; color: var(--text-muted); padding: 40px;">Noch keine Jobs! Suche starten ⬆️</p>'
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM jobs WHERE user_id=?", (session["user_id"],))
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND beworben=1", (session["user_id"],))
    beworben_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND favorit=1", (session["user_id"],))
    favoriten_count = c.fetchone()[0]
    conn.close()
    
    content = f"""
    <h1>⚡ AVINU Bot</h1>
    <p>6 Jobportale · 14 Branchen · 200+ Berufe</p>
    {msg}
    <div class="card">
        <h3>🔍 Job-Suche</h3>
        <form method="POST">
            <p>📂 Branche (optional):</p>
            <select name="branche">
                <option value="">-- Branche waehlen --</option>
                {branchen_html}
            </select>
            <p>💼 Beruf / Suchbegriff:</p>
            <input type="text" name="suchbegriff" 
                   placeholder="z.B. Fachinformatiker, Elektriker, Pflegekraft..."
                   list="berufe-list" required>
            <datalist id="berufe-list">{berufe_options}</datalist>
            <p>📍 Standort:</p>
            <input type="text" name="standort" placeholder="z.B. Berlin, Mainz..." required>
            <p>📏 Umkreis: <span id="rv">25</span> km</p>
            <input type="range" name="radius" min="5" max="200" value="25" step="5"
                   oninput="document.getElementById('rv').textContent = this.value"
                   style="width: 100%; margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted);">
                <span>5km</span><span>50km</span><span>100km</span><span>200km</span>
            </div>
            <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 15px;">
                🚀 Jobs suchen
            </button>
        </form>
    </div>
    <div class="grid" style="margin: 30px 0;">
        <a href="/avinu?filter=alle" style="text-decoration: none;">
            <div class="stat-card"><div class="stat-icon">💼</div>
                <div class="stat-value">{total}</div><div class="stat-label">Alle</div></div>
        </a>
        <a href="/avinu?filter=offen" style="text-decoration: none;">
            <div class="stat-card"><div class="stat-icon">📋</div>
                <div class="stat-value">{total - beworben_count}</div><div class="stat-label">Offen</div></div>
        </a>
        <a href="/avinu?filter=beworben" style="text-decoration: none;">
            <div class="stat-card"><div class="stat-icon">✅</div>
                <div class="stat-value">{beworben_count}</div><div class="stat-label">Beworben</div></div>
        </a>
        <a href="/avinu?filter=favoriten" style="text-decoration: none;">
            <div class="stat-card"><div class="stat-icon">⭐</div>
                <div class="stat-value">{favoriten_count}</div><div class="stat-label">Favoriten</div></div>
        </a>
    </div>
    <h2>🎯 Jobs ({len(jobs)}) - Filter: {filter_typ.title()}</h2>
    {jobs_html}
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/avinu/favorit/<int:job_id>")
def avinu_favorit(job_id):
    if "user_id" not in session:
        return redirect("/login")
    job_favorit_toggle(job_id, session["user_id"])
    return redirect("/avinu")


@app.route("/avinu/loeschen/<int:job_id>")
def avinu_loeschen(job_id):
    if "user_id" not in session:
        return redirect("/login")
    job_loeschen(job_id, session["user_id"])
    return redirect("/avinu")


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
            anschreiben_text = anschreiben_generieren(job_id, session["user_id"], int(vorlage_id), profil)
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
            <small>{v[2]}</small>
        </label>
        """
    
    anschreiben_html = ""
    if anschreiben_text:
        anschreiben_html = f"""
        <div class="card">
            <h3>📝 Dein Anschreiben</h3>
            <textarea rows="15">{anschreiben_text}</textarea>
            <a href="/avinu" class="btn btn-primary">← Zurueck</a>
        </div>
        """

    content = f"""
    <h1>⚡ Auto-Bewerbung</h1>
    {msg}
    <div class="card">
        <h3>📝 Vorlage waehlen</h3>
        <form method="POST">
            {vorlagen_html}
            <button type="submit" class="btn btn-purple" style="width: 100%;">✨ KI generieren</button>
        </form>
    </div>
    {anschreiben_html}
    """
    return render_template_string(BASE_HTML, content=content, user=session)


# Uploads
@app.route("/uploads", methods=["GET", "POST"])
def uploads():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        kategorie = request.form.get("kategorie", "dokument")
        if "datei" in request.files:
            file = request.files["datei"]
            if file and file.filename and allowed_file(file.filename):
                result = datei_speichern(file, session["user_id"], kategorie)
                if result:
                    msg = f'<div class="alert alert-ok">✅ {result}!</div>'

    user_uploads = uploads_laden(session["user_id"])
    uploads_html = ""
    for u in user_uploads:
        icon = "📄" if u[2] == ".pdf" else "🖼️"
        uploads_html += f"""
        <div class="upload-item">
            <div>{icon} <strong>{u[1]}</strong><br><small>{u[3]} - {u[5][:16]}</small></div>
            <div>
                <a href="/download/{u[0]}" class="btn btn-primary" style="padding: 8px 14px;">⬇️</a>
                <a href="/delete/{u[0]}" class="btn btn-danger" style="padding: 8px 14px;" onclick="return confirm('Loeschen?')">🗑️</a>
            </div>
        </div>
        """
    if not uploads_html:
        uploads_html = '<p style="text-align: center;">Keine Dateien</p>'

    content = f"""
    <h1>📂 Dateien</h1>
    {msg}
    <div class="card">
        <form method="POST" enctype="multipart/form-data">
            <select name="kategorie" required>
                <option value="lebenslauf">📄 Lebenslauf</option>
                <option value="zeugnis">📜 Zeugnis</option>
                <option value="zertifikat">🏆 Zertifikat</option>
                <option value="bild">🖼️ Bewerbungsbild</option>
            </select>
            <input type="file" name="datei" required accept=".pdf,.png,.jpg,.jpeg">
            <button type="submit" class="btn btn-success" style="width: 100%;">🚀 Upload</button>
        </form>
    </div>
    <div class="card">{uploads_html}</div>
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
    return "Nicht gefunden", 404


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
        daten = {k: request.form.get(k, "") for k in 
                 ["vorname","nachname","strasse","plz","stadt","telefon","email","geburtsdatum","kenntnisse","sprachen"]}
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
            msg = '<div class="alert alert-warn">⚠️ Limit!</div>'
        elif firma and email:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO bewerbungen (user_id, firma, email, datum) VALUES (?, ?, ?, ?)",
                      (session["user_id"], firma, email, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            msg = f'<div class="alert alert-ok">✅ {firma}!</div>'
    bw = bewerbungen_zaehlen(session["user_id"])
    limit = "∞" if session.get("premium") else 5
    content = f"""
    <h1>📧 Bewerbungen</h1>
    <div class="card"><h3>📊 {bw} / {limit}</h3></div>
    {msg}
    <div class="card">
        <form method="POST">
            <input type="text" name="firma" placeholder="Firma" required>
            <input type="email" name="email" placeholder="E-Mail" required>
            <button type="submit" class="btn btn-success">💾 Speichern</button>
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
            <ul style="list-style: none;"><li>✓ 5 Bewerbungen</li></ul>
            <button class="btn btn-primary" style="width: 100%;">Aktuell</button>
        </div>
        <div class="card" style="border: 2px solid var(--accent-yellow);">
            <span class="badge">BELIEBT</span>
            <h2>💎 Premium</h2><h3>1.99 €/Monat</h3>
            <ul style="list-style: none;"><li>✓ Unbegrenzt</li></ul>
            <a href="/aktivieren" class="btn btn-warning" style="width: 100%;">🚀 Upgrade</a>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/aktivieren", methods=["GET", "POST"])
def aktivieren():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if code == "XSIKOM-ADMIN-2026-PREMIUM":
            premium_aktivieren(session["user_id"])
            session["premium"] = 1
            content = """
            <h1>🎉 Premium aktiviert!</h1>
            <div class="alert alert-ok">✅ Lebenslang Premium!</div>
            <a href="/dashboard" class="btn btn-primary">Dashboard</a>
            """
            return render_template_string(BASE_HTML, content=content, user=session)
        else:
            msg = '<div class="alert alert-err">❌ Falscher Code!</div>'

    content = f"""
    <h1>🔐 Premium aktivieren</h1>
    {msg}
    <div class="card">
        <form method="POST">
            <input type="text" name="code" placeholder="Premium-Code" required>
            <button type="submit" class="btn btn-success" style="width: 100%;">🚀 Aktivieren</button>
        </form>
        <div class="alert alert-info" style="margin-top: 20px;">
            💡 Admin-Code: <strong>XSIKOM-ADMIN-2026-PREMIUM</strong>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


# Profil
@app.route("/profil")
def profil():
    if "user_id" not in session:
        return redirect("/login")
    two_fa, _ = get_2fa_status(session["user_id"])
    content = f"""
    <h1>⚙️ Profil</h1>
    <div class="grid">
        <a href="/profil/edit" style="text-decoration: none;">
            <div class="stat-card"><div class="stat-icon">👤</div>
                <div class="stat-value">Daten</div></div>
        </a>
        <a href="/profil/password" style="text-decoration: none;">
            <div class="stat-card"><div class="stat-icon">🔑</div>
                <div class="stat-value">Passwort</div></div>
        </a>
        <a href="/profil/2fa" style="text-decoration: none;">
            <div class="stat-card"><div class="stat-icon">{'✅' if two_fa else '🔐'}</div>
                <div class="stat-value">2FA</div></div>
        </a>
        <a href="/profil/export" style="text-decoration: none;">
            <div class="stat-card"><div class="stat-icon">📥</div>
                <div class="stat-value">Export</div></div>
        </a>
        <a href="/profil/delete" style="text-decoration: none;">
            <div class="stat-card" style="border-color: var(--accent-red);">
                <div class="stat-icon">🗑️</div>
                <div class="stat-value" style="color: var(--accent-red);">Loeschen</div></div>
        </a>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/edit", methods=["GET", "POST"])
def profil_edit():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE benutzer SET vorname=?, nachname=?, email=? WHERE id=?",
                  (request.form.get("vorname",""), request.form.get("nachname",""),
                   request.form.get("email",""), session["user_id"]))
        conn.commit()
        conn.close()
        session["vorname"] = request.form.get("vorname","")
        msg = '<div class="alert alert-ok">✅</div>'
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
            <input type="text" name="vorname" value="{u[0] or ''}" required>
            <input type="text" name="nachname" value="{u[1] or ''}" required>
            <input type="email" name="email" value="{u[2] or ''}" required>
            <button type="submit" class="btn btn-success">💾</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/password", methods=["GET", "POST"])
def profil_password():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT passwort FROM benutzer WHERE id=?", (session["user_id"],))
        if hash_pw(request.form.get("old_password","")) == c.fetchone()[0]:
            new = request.form.get("new_password","")
            if len(new) >= 8 and new == request.form.get("confirm_password",""):
                c.execute("UPDATE benutzer SET passwort=? WHERE id=?", (hash_pw(new), session["user_id"]))
                conn.commit()
                msg = '<div class="alert alert-ok">✅</div>'
            else:
                msg = '<div class="alert alert-err">❌</div>'
        else:
            msg = '<div class="alert alert-err">❌ Falsch</div>'
        conn.close()
    content = f"""
    <h1>🔑 Passwort</h1>
    {msg}
    <div class="card">
        <form method="POST">
            <input type="password" name="old_password" placeholder="Altes Passwort" required>
            <input type="password" name="new_password" placeholder="Neues Passwort" required>
            <input type="password" name="confirm_password" placeholder="Bestaetigen" required>
            <button type="submit" class="btn btn-success">🔒</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/2fa", methods=["GET", "POST"])
def profil_2fa():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    two_fa, current = get_2fa_status(user_id)
    msg = ""
    if request.method == "POST":
        action = request.form.get("action","")
        token = request.form.get("token","")
        if action == "enable":
            secret = request.form.get("secret","")
            if verify_2fa_token(secret, token):
                enable_2fa(user_id, secret)
                two_fa = True
                msg = '<div class="alert alert-ok">✅ 2FA aktiv!</div>'
        elif action == "disable":
            if verify_2fa_token(current, token):
                disable_2fa(user_id)
                two_fa = False

    if two_fa:
        content = f"""
        <h1>🔐 2FA Aktiv</h1>
        {msg}
        <div class="card">
            <form method="POST">
                <input type="hidden" name="action" value="disable">
                <input type="text" name="token" placeholder="6-stelliger Code" required>
                <button type="submit" class="btn btn-danger">⚠️ Deaktivieren</button>
            </form>
        </div>
        """
    else:
        secret = generate_2fa_secret()
        qr = generate_qr_code(session.get("username","user"), secret)
        content = f"""
        <h1>🔐 2FA einrichten</h1>
        {msg}
        <div class="card">
            <div style="text-align: center; background: white; padding: 20px; border-radius: 12px;">
                <img src="{qr}" style="max-width: 300px;">
            </div>
            <p style="margin-top: 15px; font-family: monospace; word-break: break-all;">{secret}</p>
            <form method="POST">
                <input type="hidden" name="action" value="enable">
                <input type="hidden" name="secret" value="{secret}">
                <input type="text" name="token" placeholder="Code aus App" required>
                <button type="submit" class="btn btn-success">🔐 Aktivieren</button>
            </form>
        </div>
        """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/export")
def profil_export():
    if "user_id" not in session:
        return redirect("/login")
    data = export_user_data(session["user_id"])
    return Response(json_module.dumps(data, indent=2), mimetype="application/json",
                    headers={"Content-Disposition": f"attachment; filename=export.json"})


@app.route("/profil/delete", methods=["GET", "POST"])
def profil_delete():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    if request.method == "POST":
        if request.form.get("confirmation") == "LOESCHEN":
            request_account_deletion(session["user_id"])
            msg = '<div class="alert alert-ok">✅ Antrag eingegangen!</div>'
    content = f"""
    <h1 style="color: var(--accent-red);">🗑️ Account loeschen</h1>
    <div class="alert alert-warn">⚠️ 30 Tage Frist!</div>
    {msg}
    <div class="card">
        <form method="POST">
            <input type="password" name="password" placeholder="Passwort" required>
            <input type="text" name="confirmation" placeholder='Tippe "LOESCHEN"' required>
            <button type="submit" class="btn btn-danger">🗑️ Loeschen</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


# Rechtliche Seiten
@app.route("/impressum")
def impressum():
    content = f"""
    <h1>📜 Impressum</h1>
    <div class="legal-text">
        <h3>§ 5 TMG</h3>
        <p><strong>XsiKOM DIGITAL Projects</strong><br>
        Komi Tevi<br>Am Koenigsfloss 12<br>55252 Mainz-Kastel</p>
        <p>E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/datenschutz")
def datenschutz():
    content = f"""
    <h1>🔒 Datenschutz</h1>
    <div class="legal-text">
        <p>XsiKOM DIGITAL Projects, Komi Tevi<br>{CONTACT_EMAIL}</p>
        <h3>DSGVO Rechte</h3>
        <p>Auskunft, Berichtigung, Loeschung, Uebertragbarkeit</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/widerruf")
def widerruf():
    content = f"""
    <h1>↩️ Widerruf</h1>
    <div class="legal-text">
        <p>14 Tage Widerrufsrecht. Kontakt: {CONTACT_EMAIL}</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/haftung")
def haftung():
    content = f"""
    <h1>⚖️ Haftung</h1>
    <div class="legal-text">
        <div class="alert alert-warn">⚠️ KI-Inhalte koennen Fehler enthalten!</div>
        <p>Keine Haftung fuer Schaeden.</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/agb")
def agb():
    content = f"""
    <h1>📋 AGB</h1>
    <div class="legal-text">
        <p>Free: 5 Bewerbungen | Premium: 1.99€</p>
        <p>Gerichtsstand: Mainz</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/password-reset", methods=["GET", "POST"])
def password_reset_request():
    msg = ""
    if request.method == "POST":
        email = request.form.get("email","").strip()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM benutzer WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()
        if user:
            token = create_password_reset_token(user[0])
            link = f"{request.host_url}password-reset/{token}"
            msg = f'<div class="alert alert-ok">Link: {link}</div>'
        else:
            msg = '<div class="alert alert-info">Email gesendet (falls existiert)</div>'

    content = f"""
    <div style="max-width: 450px; margin: 60px auto;">
        <div class="card">
            <h1>🔑 Reset</h1>
            {msg}
            <form method="POST">
                <input type="email" name="email" placeholder="E-Mail" required>
                <button type="submit" class="btn btn-primary">📧</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=None)


@app.route("/password-reset/<token>", methods=["GET", "POST"])
def password_reset_new(token):
    user_id = verify_reset_token(token)
    if not user_id:
        content = '<h1>❌ Ungueltig</h1>'
        return render_template_string(BASE_HTML, content=content, user=None)
    if request.method == "POST":
        new = request.form.get("new_password","")
        if len(new) >= 8:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("UPDATE benutzer SET passwort=? WHERE id=?", (hash_pw(new), user_id))
            conn.commit()
            conn.close()
            use_reset_token(token)
            return redirect("/login")
    content = """
    <div style="max-width: 450px; margin: 60px auto;">
        <div class="card">
            <h1>Neues Passwort</h1>
            <form method="POST">
                <input type="password" name="new_password" required>
                <button type="submit" class="btn btn-success">✅</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=None)


@app.route("/logout")
def logout():
    if "user_id" in session:
        audit_log(session["user_id"], "LOGOUT", "")
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
    print("=" * 60)
    print("  XsiKOM v4.0")
    print(f"  KI: {'ONLINE' if GROQ_API_KEY else 'OFFLINE'}")
    print(f"  URL: http://localhost:5000")
    print("=" * 60)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)