"""
XsiKOM-BewerbungsBOT
Web App mit allen Features + Recht
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
    send_file, make_response, jsonify
)
from werkzeug.utils import secure_filename
from PIL import Image
import io


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(hours=2)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB max

DB_NAME = "bewerbungen.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "bmp", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# AALIYAH KI (Groq)
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """Du bist Aaliyah, eine professionelle KI-Karriereberaterin fuer IT-Bewerber.

Spezialgebiete:
- IT-Praktika (Fachinformatiker, Netzwerktechnik, Systemadministration)
- Bewerbungsschreiben und Anschreiben
- Lebenslauf-Optimierung
- Vorstellungsgespraechs-Coaching
- Gehaltsverhandlungen

Antworte auf Deutsch, freundlich, professionell, 3-5 Saetze."""


def get_ki_antwort(frage):
    if not GROQ_API_KEY:
        return ("Hallo! Ich bin Aaliyah. Meine KI-Verbindung ist gerade offline. "
                "Bitte versuche es spaeter nochmal oder kontaktiere den Support.")
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
        return "Entschuldigung, da ist etwas schiefgelaufen. Bitte spaeter nochmal."
    except Exception as e:
        return f"KI-Verbindung fehlgeschlagen. ({str(e)[:50]})"


AALIYAH_TIPPS = [
    "Passe dein Anschreiben immer an die konkrete Stelle an!",
    "Erwaehne im Anschreiben konkrete Projekte der Firma.",
    "Halte dein Anschreiben auf maximal eine Seite.",
    "Zeige Motivation - warum genau diese Firma?",
    "Pruefe deine E-Mail auf Rechtschreibung vor dem Senden.",
]


def aaliyah_antwort(frage):
    return get_ki_antwort(frage)


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
            email TEXT,
            vorname TEXT,
            nachname TEXT,
            rolle TEXT DEFAULT 'user',
            premium INTEGER DEFAULT 0,
            kunde_typ TEXT DEFAULT 'privat',
            erstellt TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bewerbungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            firma TEXT,
            email TEXT,
            status TEXT DEFAULT 'gesendet',
            datum TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            user_id INTEGER PRIMARY KEY,
            vorname TEXT, nachname TEXT,
            strasse TEXT, plz TEXT, stadt TEXT,
            telefon TEXT, email TEXT,
            geburtsdatum TEXT,
            kenntnisse TEXT, sprachen TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            dateiname TEXT,
            typ TEXT,
            kategorie TEXT,
            pfad TEXT,
            upload_datum TEXT
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
            "xsikom.projects@gmail.com", "Komi", "Tevi",
            "admin", 1,
            datetime.now().isoformat()
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


# ============================================================
# UPLOAD FUNKTIONEN
# ============================================================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def datei_speichern(file, user_id, kategorie):
    """Speichert Datei und konvertiert Bilder zu JPG falls nötig."""
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
        except Exception as e:
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


def uploads_laden(user_id, kategorie=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if kategorie:
        c.execute(
            "SELECT id, dateiname, typ, kategorie, pfad, upload_datum "
            "FROM uploads WHERE user_id=? AND kategorie=? ORDER BY id DESC",
            (user_id, kategorie)
        )
    else:
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
    c.execute(
        "SELECT pfad FROM uploads WHERE id=? AND user_id=?",
        (upload_id, user_id)
    )
    r = c.fetchone()
    if r and os.path.exists(r[0]):
        try:
            os.remove(r[0])
        except Exception:
            pass
    c.execute(
        "DELETE FROM uploads WHERE id=? AND user_id=?",
        (upload_id, user_id)
    )
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
    <title>XsiKOM-BewerbungsBOT</title>

    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#00B4D8">
    <link rel="icon" type="image/png" href="/static/icon-192.png">

    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/sw.js');
            });
        }

        function cookieAccept() {
            localStorage.setItem('cookie_accepted', 'yes');
            document.getElementById('cookie-banner').style.display = 'none';
        }

        window.addEventListener('load', function() {
            if (localStorage.getItem('cookie_accepted') !== 'yes') {
                var banner = document.getElementById('cookie-banner');
                if (banner) banner.style.display = 'block';
            }
        });
    </script>

    <style>
        * { margin: 0; padding: 0; box-sizing: border-box;
             font-family: 'Segoe UI', Arial, sans-serif; }
        body { background: #0F1923; color: #E8EDF2; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #1E3D5C, #162635);
                  padding: 20px; border-bottom: 3px solid #00B4D8; }
        .logo-text { color: #00B4D8; font-size: 28px; font-weight: bold;
                     background: linear-gradient(90deg, #00B4D8, #2DD4A8);
                     -webkit-background-clip: text;
                     background-clip: text;
                     -webkit-text-fill-color: transparent; }
        .subtitle { color: #2DD4A8; font-size: 14px; }
        .nav { background: #162635; padding: 10px;
               overflow-x: auto; white-space: nowrap; }
        .nav a { color: #E8EDF2; text-decoration: none;
                 padding: 10px 16px; margin: 0 3px;
                 border-radius: 8px; display: inline-block;
                 font-size: 14px; transition: all 0.3s ease; }
        .nav a:hover { background: #1E3A4F; }
        .card { background: linear-gradient(135deg, #1A2F42, #243D54);
                border-radius: 16px; padding: 24px; margin: 15px 0;
                border: 1px solid #2A4A65;
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3); }
        .btn { padding: 12px 24px; border: none;
               border-radius: 10px; cursor: pointer;
               font-weight: bold; text-decoration: none;
               display: inline-block; font-size: 14px;
               transition: all 0.3s ease; }
        .btn:hover { transform: translateY(-2px); }
        .btn-primary { background: linear-gradient(135deg, #00B4D8, #0077B6); color: white; }
        .btn-success { background: linear-gradient(135deg, #2DD4A8, #00B894); color: white; }
        .btn-warning { background: linear-gradient(135deg, #FFD93D, #FF8C42); color: #0F1923; }
        .btn-danger { background: linear-gradient(135deg, #FF5252, #E74C3C); color: white; }
        input, textarea, select { background: #0A1520;
                           border: 1px solid #2A4A65;
                           color: #E8EDF2; padding: 12px;
                           border-radius: 6px; width: 100%;
                           margin-bottom: 10px; font-size: 14px; }
        h1, h2, h3 { color: #00B4D8; margin-bottom: 15px; }
        .grid { display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 15px; }
        .footer { background: #162635; padding: 30px 20px;
                  text-align: center; color: #5C6B7A;
                  margin-top: 40px; font-size: 13px;
                  border-top: 2px solid #1E3D5C; }
        .footer a { color: #00B4D8; margin: 0 8px;
                    text-decoration: none; }
        .footer a:hover { color: #2DD4A8; }
        .badge { background: linear-gradient(135deg, #FFD93D, #FF8C42);
                 color: black; padding: 5px 12px;
                 border-radius: 20px; font-size: 12px;
                 font-weight: bold; display: inline-block; }
        .alert-ok { background: #2DD4A8; color: black; padding: 15px;
                    border-radius: 8px; margin: 10px 0; }
        .alert-err { background: #FF5252; color: white; padding: 15px;
                     border-radius: 8px; margin: 10px 0; }
        .alert-warn { background: #FFD93D; color: black; padding: 15px;
                      border-radius: 8px; margin: 10px 0; }
        .file-upload { background: #0A1520;
                        border: 2px dashed #2A4A65;
                        border-radius: 10px; padding: 20px;
                        text-align: center; margin: 10px 0; }
        .file-upload:hover { border-color: #00B4D8; }
        .upload-item { background: #0A1520; padding: 12px;
                       border-radius: 8px; margin: 8px 0;
                       display: flex; justify-content: space-between;
                       align-items: center; }
        #cookie-banner {
            display: none;
            position: fixed; bottom: 0; left: 0; right: 0;
            background: #1A2F42; color: white;
            padding: 20px; z-index: 9999;
            border-top: 3px solid #00B4D8;
            box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
        }
        .legal-text {
            background: #1A2F42; padding: 25px;
            border-radius: 10px; margin: 15px 0;
            line-height: 1.7;
        }
        .legal-text h3 { color: #00B4D8; margin-top: 20px; }
        .legal-text p { margin: 10px 0; }
        @media (max-width: 768px) {
            .logo-text { font-size: 24px; }
            .nav a { padding: 8px 10px; font-size: 12px; }
        }
    </style>
</head>
<body>

<div id="cookie-banner">
    <div style="max-width: 1200px; margin: 0 auto; display: flex;
                justify-content: space-between; align-items: center;
                flex-wrap: wrap; gap: 15px;">
        <div style="flex: 1; min-width: 250px;">
            <strong>🍪 Cookie-Hinweis</strong><br>
            <small>Wir verwenden technisch notwendige Cookies fuer Login und 
            Funktionalitaet. Mit Nutzung der Seite akzeptierst du unsere 
            <a href="/datenschutz" style="color: #00B4D8;">Datenschutzerklaerung</a>.</small>
        </div>
        <button onclick="cookieAccept()" class="btn btn-success">
            Akzeptieren
        </button>
    </div>
</div>

<div class="header">
    <div class="container">
        <div class="logo-text">XsiKOM</div>
        <div class="subtitle">BewerbungsBOT - {{ user.vorname if user else 'Login' }}</div>
    </div>
</div>

{% if user %}
<div class="nav">
    <div class="container">
        <a href="/dashboard">Dashboard</a>
        <a href="/aaliyah">Aaliyah KI</a>
        <a href="/lebenslauf">Lebenslauf</a>
        <a href="/uploads">Meine Dateien</a>
        <a href="/bewerbungen">Bewerbungen</a>
        <a href="/premium">Premium</a>
        <a href="/install">App installieren</a>
        <a href="/logout">Logout</a>
    </div>
</div>
{% endif %}

<div class="container">
    {{ content|safe }}
</div>

<div class="footer">
    <div style="margin-bottom: 15px;">
        <a href="/impressum">Impressum</a> |
        <a href="/datenschutz">Datenschutz</a> |
        <a href="/agb">AGB</a> |
        <a href="/widerruf">Widerrufsrecht</a> |
        <a href="/haftung">Haftungsausschluss</a> |
        <a href="/install">App installieren</a>
    </div>
    <div style="margin-top: 10px;">
        XsiKOM-BewerbungsBOT &copy; 2026 
        <strong style="color: #00B4D8;">XsiKOM DIGITAL Projects</strong>
    </div>
    <div style="margin-top: 5px; font-size: 11px; color: #5C6B7A;">
        Komi Tevi  |  
        <a href="mailto:xsikom.projects@gmail.com" style="color: #5C6B7A;">
            xsikom.projects@gmail.com
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
        msg = '<div class="alert-err">Login falsch!</div>'

    content = f"""
    <div style="max-width: 400px; margin: 50px auto;">
        <div class="card">
            <h1>Anmelden</h1>
            {msg}
            <form method="POST">
                <p>Benutzername:</p>
                <input type="text" name="username" value="admin" required>
                <p>Passwort:</p>
                <input type="password" name="password" required>
                <button type="submit" class="btn btn-primary" style="width: 100%;">Anmelden</button>
            </form>
            <p style="margin-top: 15px;">
                <a href="/register" style="color: #00B4D8;">Neuen Account erstellen</a>
            </p>
            <p style="margin-top: 10px; color: #5C6B7A; font-size: 12px;">
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
            msg = '<div class="alert-err">Alle Felder und Zustimmungen erforderlich!</div>'
        elif len(pw) < 6:
            msg = '<div class="alert-err">Passwort min. 6 Zeichen!</div>'
        elif benutzer_anlegen(user, pw, email, vn, nn, kunde_typ):
            return redirect("/login")
        else:
            msg = '<div class="alert-err">Benutzername vergeben!</div>'

    content = f"""
    <div style="max-width: 600px; margin: 30px auto;">
        <div class="card">
            <h1>Registrieren</h1>
            {msg}
            <form method="POST">
                <p>Kundentyp:</p>
                <select name="kunde_typ" required>
                    <option value="privat">Privatkunde</option>
                    <option value="firma">Firmenkunde</option>
                </select>
                <p>Benutzername:</p>
                <input type="text" name="username" required>
                <p>Passwort (min. 6 Zeichen):</p>
                <input type="password" name="password" required>
                <p>E-Mail:</p>
                <input type="email" name="email" required>
                <p>Vorname:</p>
                <input type="text" name="vorname">
                <p>Nachname:</p>
                <input type="text" name="nachname">

                <div style="margin-top: 20px; padding: 15px;
                            background: #0A1520; border-radius: 8px;">
                    <p style="margin: 8px 0;">
                        <input type="checkbox" name="datenschutz" required style="width: auto;">
                        Ich akzeptiere die 
                        <a href="/datenschutz" target="_blank" style="color: #00B4D8;">
                            Datenschutzerklaerung (DSGVO)
                        </a>
                    </p>
                    <p style="margin: 8px 0;">
                        <input type="checkbox" name="agb" required style="width: auto;">
                        Ich akzeptiere die 
                        <a href="/agb" target="_blank" style="color: #00B4D8;">AGB</a>
                        und den 
                        <a href="/haftung" target="_blank" style="color: #00B4D8;">
                            Haftungsausschluss
                        </a>
                    </p>
                    <p style="margin: 8px 0;">
                        <input type="checkbox" name="widerruf" required style="width: auto;">
                        Ich habe das 
                        <a href="/widerruf" target="_blank" style="color: #00B4D8;">
                            Widerrufsrecht
                        </a>
                        zur Kenntnis genommen
                    </p>
                </div>
                <br>
                <button type="submit" class="btn btn-success" style="width: 100%;">
                    Registrieren
                </button>
            </form>
            <p style="margin-top: 15px;">
                <a href="/login" style="color: #00B4D8;">Bereits Account? Login</a>
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
    limit = "unbegrenzt" if session.get("premium") else 5
    badge = '<span class="badge">PREMIUM</span>' if session.get("premium") else ""
    upgrade = ""
    if not session.get("premium"):
        upgrade = '<a href="/premium" class="btn btn-warning">Upgrade auf Premium - 1.99 EUR/Monat</a>'

    ki_status = '<span style="color: #2DD4A8;">● KI Online</span>' if GROQ_API_KEY else '<span style="color: #FF5252;">● KI Offline</span>'

    content = f"""
    <h1>Dashboard</h1>
    <p>Willkommen, {session['vorname']}! {ki_status}</p>

    <div class="card">
        <h3>Dein Plan: {"Premium" if session.get("premium") else "Free"} {badge}</h3>
        <p>Bewerbungen diesen Monat: <strong>{bw} / {limit}</strong></p>
        {upgrade}
    </div>

    <h2>Schnellaktionen</h2>
    <div class="grid">
        <div class="card" style="text-align: center;">
            <h3>🤖 Aaliyah KI</h3>
            <p>KI Beraterin</p>
            <a href="/aaliyah" class="btn btn-primary">Chat starten</a>
        </div>
        <div class="card" style="text-align: center;">
            <h3>📄 Lebenslauf</h3>
            <p>Profil bearbeiten</p>
            <a href="/lebenslauf" class="btn btn-primary">Bearbeiten</a>
        </div>
        <div class="card" style="text-align: center;">
            <h3>📂 Meine Dateien</h3>
            <p>PDFs & Bilder</p>
            <a href="/uploads" class="btn btn-primary">Verwalten</a>
        </div>
        <div class="card" style="text-align: center;">
            <h3>📧 Bewerbungen</h3>
            <p>Senden</p>
            <a href="/bewerbungen" class="btn btn-primary">Senden</a>
        </div>
    </div>

    <div class="card">
        <h3>Aaliyahs Tipp des Tages</h3>
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
            a = aaliyah_antwort(frage)
            a_html = a.replace("\n", "<br>")
            antwort = f"""
            <div style="margin-top: 20px; padding: 15px;
                        background: #0A1520; border-radius: 8px;
                        border-left: 4px solid #FF69B4;">
                <strong>Aaliyah:</strong><br>{a_html}
            </div>
            """

    ki_status = ""
    if not GROQ_API_KEY:
        ki_status = '<div class="alert-warn">KI ist gerade offline. Antworten begrenzt!</div>'

    content = f"""
    <h1>Aaliyah KI</h1>
    {ki_status}
    <div class="card">
        <h3>Chat mit deiner Bewerbungsberaterin</h3>
        <form method="POST">
            <input type="text" name="frage" placeholder="Frag Aaliyah..." required>
            <button type="submit" class="btn btn-primary">Senden</button>
        </form>
        {antwort}
    </div>
    <div class="card">
        <h3>Beispielfragen</h3>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="Wie schreibe ich ein gutes IT-Anschreiben?">
            <button class="btn btn-primary">IT-Anschreiben</button>
        </form>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="Welche Fragen kommen im Vorstellungsgespraech?">
            <button class="btn btn-primary">Gespraechsfragen</button>
        </form>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="Wie verhandle ich Gehalt?">
            <button class="btn btn-primary">Gehalt</button>
        </form>
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
                        msg = f'<div class="alert-ok">Datei {result} hochgeladen!</div>'
                    else:
                        msg = '<div class="alert-err">Fehler beim Hochladen!</div>'
                else:
                    msg = '<div class="alert-err">Dateityp nicht erlaubt!</div>'

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
                    <small style="color: #5C6B7A;">{kat} - {datum[:16]}</small>
                </div>
                <div>
                    <a href="/download/{upload_id}" class="btn btn-primary" 
                       style="padding: 8px 16px; font-size: 12px;">
                        Download
                    </a>
                    <a href="/delete/{upload_id}" class="btn btn-danger" 
                       style="padding: 8px 16px; font-size: 12px;"
                       onclick="return confirm('Wirklich loeschen?')">
                        Loeschen
                    </a>
                </div>
            </div>
            """
    else:
        uploads_html = '<p style="color: #5C6B7A;">Noch keine Dateien hochgeladen.</p>'

    content = f"""
    <h1>📂 Meine Dateien</h1>
    {msg}

    <div class="card">
        <h3>Datei hochladen</h3>
        <form method="POST" enctype="multipart/form-data">
            <p>Kategorie:</p>
            <select name="kategorie" required>
                <option value="lebenslauf">📄 Lebenslauf</option>
                <option value="zeugnis">📜 Zeugnis</option>
                <option value="zertifikat">🏆 Zertifikat</option>
                <option value="bild">🖼️ Bewerbungsbild</option>
                <option value="anschreiben">✉️ Anschreiben</option>
                <option value="dokument">📋 Sonstiges Dokument</option>
            </select>

            <div class="file-upload">
                <p>📤 Klicke hier um Datei auszuwaehlen</p>
                <input type="file" name="datei" required
                       accept=".pdf,.png,.jpg,.jpeg,.gif,.bmp,.webp">
                <p style="font-size: 12px; color: #5C6B7A; margin-top: 10px;">
                    Erlaubte Formate: PDF, PNG, JPG, JPEG, GIF, BMP, WEBP
                </p>
                <p style="font-size: 11px; color: #5C6B7A;">
                    Bilder werden automatisch zu JPG konvertiert.
                </p>
            </div>

            <button type="submit" class="btn btn-success" style="width: 100%;">
                📤 Hochladen
            </button>
        </form>
    </div>

    <div class="card">
        <h3>Deine Dateien ({len(user_uploads)})</h3>
        {uploads_html}
    </div>

    <div class="alert-warn">
        <strong>🔒 Datenschutz:</strong> Deine Dateien sind nur fuer dich sichtbar 
        und werden verschluesselt gespeichert. Nach DSGVO loeschen wir alle Daten 
        auf Anfrage.
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/download/<int:upload_id>")
def download_datei(upload_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT pfad, dateiname FROM uploads WHERE id=? AND user_id=?",
        (upload_id, session["user_id"])
    )
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
        msg = '<div class="alert-ok">Profil gespeichert!</div>'

    p = profil_laden(session["user_id"])
    kenntnisse_text = p.get('kenntnisse', '')
    sprachen_text = p.get('sprachen', '')

    content = f"""
    <h1>Lebenslauf</h1>
    {msg}
    <form method="POST">
        <div class="card">
            <h3>Persoenliche Daten</h3>
            <p>Vorname:</p>
            <input type="text" name="vorname" value="{p.get('vorname','')}">
            <p>Nachname:</p>
            <input type="text" name="nachname" value="{p.get('nachname','')}">
            <p>Strasse:</p>
            <input type="text" name="strasse" value="{p.get('strasse','')}">
            <p>PLZ:</p>
            <input type="text" name="plz" value="{p.get('plz','')}">
            <p>Stadt:</p>
            <input type="text" name="stadt" value="{p.get('stadt','')}">
            <p>Telefon:</p>
            <input type="text" name="telefon" value="{p.get('telefon','')}">
            <p>E-Mail:</p>
            <input type="email" name="email" value="{p.get('email','')}">
            <p>Geburtsdatum:</p>
            <input type="text" name="geburtsdatum" value="{p.get('geburtsdatum','')}">
        </div>
        <div class="card">
            <h3>IT-Kenntnisse (eine pro Zeile)</h3>
            <textarea name="kenntnisse" rows="6">{kenntnisse_text}</textarea>
        </div>
        <div class="card">
            <h3>Sprachen (eine pro Zeile)</h3>
            <textarea name="sprachen" rows="4">{sprachen_text}</textarea>
        </div>
        <div class="card">
            <button type="submit" class="btn btn-success">Speichern</button>
            <a href="/uploads" class="btn btn-primary">Lebenslauf-Datei hochladen</a>
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
            msg = '<div class="alert-warn">Limit erreicht! <a href="/premium">Upgrade auf Premium!</a></div>'
        elif firma and email:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                "INSERT INTO bewerbungen (user_id, firma, email, datum) VALUES (?, ?, ?, ?)",
                (session["user_id"], firma, email, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            msg = f'<div class="alert-ok">Bewerbung an {firma} gespeichert!</div>'

    bw = bewerbungen_zaehlen(session["user_id"])
    limit = "unbegrenzt" if session.get("premium") else 5

    content = f"""
    <h1>Bewerbungen</h1>
    <div class="card">
        <h3>Dein Limit</h3>
        <p>Bewerbungen: <strong>{bw} / {limit}</strong> diesen Monat</p>
    </div>
    {msg}
    <div class="card">
        <h3>Neue Bewerbung</h3>
        <form method="POST">
            <p>Firma:</p>
            <input type="text" name="firma" required>
            <p>E-Mail des Unternehmens:</p>
            <input type="email" name="email" required>
            <button type="submit" class="btn btn-success">Bewerbung speichern</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/premium")
def premium():
    content = """
    <h1>Premium Upgrade</h1>
    <div class="grid">
        <div class="card">
            <h2>Free</h2><h3>0.00 EUR / Monat</h3>
            <ul style="list-style: none; padding: 0;">
                <li>5 Bewerbungen/Monat</li>
                <li>1 Lebenslauf</li>
                <li>3 Jobportale</li>
                <li>Basis KI</li>
            </ul>
            <button class="btn btn-primary" style="width: 100%;">Aktuell</button>
        </div>
        <div class="card" style="border: 3px solid #FFD93D;">
            <span class="badge">BELIEBT</span>
            <h2 style="margin-top: 10px;">Premium</h2>
            <h3>1.99 EUR / Monat</h3>
            <ul style="list-style: none; padding: 0;">
                <li>UNBEGRENZTE Bewerbungen</li>
                <li>10 Lebenslauf-Vorlagen</li>
                <li>Premium KI</li>
                <li>Werbefrei</li>
            </ul>
            <a href="/checkout" class="btn btn-warning" style="width: 100%;">Upgrade</a>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect("/login")
    content = """
    <h1>Checkout</h1>
    <div class="card">
        <div class="alert-warn">Demo-Modus: Stripe Integration kommt bald!</div>
        <a href="/aktivieren" class="btn btn-success">Demo Premium aktivieren</a>
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
    <h1>Premium aktiviert!</h1>
    <div class="alert-ok">Premium ist jetzt aktiv!</div>
    <a href="/dashboard" class="btn btn-primary">Dashboard</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/install")
def install():
    content = """
    <h1>App installieren</h1>
    <div class="card">
        <h2>Android (Chrome)</h2>
        <ol style="padding-left: 20px;">
            <li>3-Punkte-Menue oben rechts</li>
            <li>"App installieren"</li>
            <li>Bestaetigen</li>
        </ol>
    </div>
    <div class="card">
        <h2>iPhone (Safari)</h2>
        <ol style="padding-left: 20px;">
            <li>Teilen-Symbol</li>
            <li>"Zum Home-Bildschirm"</li>
            <li>Hinzufuegen</li>
        </ol>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


# ============================================================
# RECHTLICHE SEITEN
# ============================================================
@app.route("/impressum")
def impressum():
    content = """
    <h1>📜 Impressum</h1>
    <div class="legal-text">
        <h3>Angaben gemaess § 5 TMG (Telemediengesetz)</h3>
        
        <p><strong>Betreiber:</strong><br>
        Komi Tevi<br>
        XsiKOM DIGITAL Projects<br>
        Am Koenigsfloss 12<br>
        55252 Mainz-Kastel<br>
        Deutschland</p>

        <h3>Kontakt</h3>
        <p>Telefon: +49 178 8977320<br>
        E-Mail: xsikom.projects@gmail.com<br>
        Web: https://xsikom-bewerbungsbot.onrender.com</p>

        <h3>Verantwortlich fuer den Inhalt nach § 55 Abs. 2 RStV</h3>
        <p>Komi Tevi<br>
        Am Koenigsfloss 12<br>
        55252 Mainz-Kastel</p>

        <h3>Umsatzsteuer-ID</h3>
        <p>Kleinunternehmer im Sinne von § 19 UStG - keine Umsatzsteuer ausgewiesen.</p>

        <h3>EU-Streitschlichtung</h3>
        <p>Die Europaeische Kommission stellt eine Plattform zur 
        Online-Streitbeilegung (OS) bereit:<br>
        <a href="https://ec.europa.eu/consumers/odr/" target="_blank" style="color: #00B4D8;">
            https://ec.europa.eu/consumers/odr/
        </a></p>
        <p>Unsere E-Mail-Adresse finden Sie oben im Impressum.</p>

        <h3>Verbraucherstreitbeilegung</h3>
        <p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungs-
        verfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>

        <h3>Haftung fuer Inhalte</h3>
        <p>Als Diensteanbieter sind wir gemaess § 7 Abs.1 TMG fuer 
        eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen 
        verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter 
        jedoch nicht verpflichtet, uebermittelte oder gespeicherte fremde 
        Informationen zu ueberwachen.</p>

        <h3>Haftung fuer Links</h3>
        <p>Unser Angebot enthaelt Links zu externen Webseiten Dritter, 
        auf deren Inhalte wir keinen Einfluss haben. Fuer die Inhalte 
        verlinkter Seiten ist stets der jeweilige Anbieter verantwortlich.</p>

        <h3>Urheberrecht</h3>
        <p>Die durch die Seitenbetreiber erstellten Inhalte und Werke 
        auf diesen Seiten unterliegen dem deutschen Urheberrecht.</p>

        <p style="margin-top: 30px; padding: 15px; background: #0A1520; 
                  border-radius: 8px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026<br>
            <strong>(c) 2026 XsiKOM DIGITAL Projects - Komi Tevi</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/datenschutz")
def datenschutz():
    content = """
    <h1>🔒 Datenschutzerklaerung nach DSGVO</h1>
    <div class="legal-text">
        <h3>1. Verantwortlicher</h3>
        <p>Verantwortlich fuer die Datenverarbeitung auf dieser Website ist:</p>
        <p><strong>Komi Tevi</strong><br>
        XsiKOM DIGITAL Projects<br>
        Am Koenigsfloss 12<br>
        55252 Mainz-Kastel<br>
        Deutschland<br>
        E-Mail: xsikom.projects@gmail.com</p>

        <h3>2. Erhebung und Speicherung personenbezogener Daten</h3>
        <p>Wir verarbeiten folgende Daten:</p>
        <ul style="padding-left: 25px;">
            <li>Stammdaten (Name, E-Mail, Adresse)</li>
            <li>Zugangsdaten (Benutzername, verschluesseltes Passwort)</li>
            <li>Inhaltsdaten (Lebenslauf, Bewerbungen, hochgeladene Dateien)</li>
            <li>Nutzungsdaten (Login-Zeiten, IP-Adresse anonymisiert)</li>
        </ul>

        <h3>3. Zwecke der Datenverarbeitung</h3>
        <p>Die Daten werden verarbeitet zu folgenden Zwecken:</p>
        <ul style="padding-left: 25px;">
            <li>Bereitstellung des Bewerbungs-Service (Art. 6 Abs. 1 lit. b DSGVO)</li>
            <li>Erfuellung vertraglicher Pflichten</li>
            <li>Optimierung der Anwendung</li>
            <li>Erfuellung gesetzlicher Aufbewahrungspflichten</li>
        </ul>

        <h3>4. Ihre Rechte nach DSGVO</h3>
        <p>Sie haben folgende Rechte:</p>
        <ul style="padding-left: 25px;">
            <li><strong>Auskunftsrecht</strong> (Art. 15 DSGVO)</li>
            <li><strong>Berichtigungsrecht</strong> (Art. 16 DSGVO)</li>
            <li><strong>Recht auf Loeschung</strong> (Art. 17 DSGVO)</li>
            <li><strong>Recht auf Einschraenkung</strong> (Art. 18 DSGVO)</li>
            <li><strong>Recht auf Datenuebertragbarkeit</strong> (Art. 20 DSGVO)</li>
            <li><strong>Widerspruchsrecht</strong> (Art. 21 DSGVO)</li>
            <li><strong>Beschwerderecht</strong> bei der Aufsichtsbehoerde</li>
        </ul>
        <p>Anfragen senden Sie bitte an: xsikom.projects@gmail.com</p>

        <h3>5. KI-Verarbeitung (Aaliyah)</h3>
        <p>Bei Nutzung der KI-Funktionen werden Ihre Eingaben an 
        Groq Inc. (USA) uebermittelt. Es gilt der EU-US Data Privacy 
        Framework. Keine personenbezogenen Daten werden dauerhaft 
        gespeichert.</p>

        <h3>6. Cookies</h3>
        <p>Wir verwenden ausschliesslich technisch notwendige Cookies:</p>
        <ul style="padding-left: 25px;">
            <li><strong>Session-Cookie:</strong> Fuer Ihren Login</li>
            <li><strong>CSRF-Token:</strong> Schutz vor Cross-Site-Forgery</li>
        </ul>
        <p>Keine Tracking-Cookies, keine Werbung.</p>

        <h3>7. Hosting</h3>
        <p>Unsere Webseite wird gehostet bei:</p>
        <p>Render Services Inc.<br>
        525 Brannan Street, San Francisco, CA 94107, USA</p>
        <p>Standardvertragsklauseln der EU sind vereinbart.</p>

        <h3>8. Speicherdauer</h3>
        <ul style="padding-left: 25px;">
            <li>Account-Daten: solange Account aktiv</li>
            <li>Inaktive Accounts: 12 Monate, dann Loeschung</li>
            <li>Logs: 30 Tage</li>
            <li>Backups: 90 Tage</li>
        </ul>

        <h3>9. Datensicherheit</h3>
        <ul style="padding-left: 25px;">
            <li>SSL/TLS Verschluesselung (HTTPS)</li>
            <li>SHA-256 Passwort-Hashing</li>
            <li>Sichere Sessions mit Timeout</li>
            <li>Regelmaessige Sicherheits-Updates</li>
        </ul>

        <h3>10. Aufsichtsbehoerde</h3>
        <p>Bei Beschwerden wenden Sie sich an:</p>
        <p>Landesbeauftragter fuer den Datenschutz<br>
        Rheinland-Pfalz<br>
        Hintere Bleiche 34, 55116 Mainz<br>
        Telefon: 06131 8920-0</p>

        <p style="margin-top: 30px; padding: 15px; background: #0A1520; 
                  border-radius: 8px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026<br>
            <strong>(c) 2026 XsiKOM DIGITAL Projects - Komi Tevi</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/widerruf")
def widerruf():
    content = """
    <h1>↩️ Widerrufsbelehrung</h1>
    <div class="legal-text">
        <h3>Widerrufsrecht fuer Verbraucher (§ 312g BGB)</h3>
        
        <p><strong>Sie haben das Recht, binnen 14 Tagen ohne Angabe von 
        Gruenden diesen Vertrag zu widerrufen.</strong></p>

        <p>Die Widerrufsfrist betraegt vierzehn Tage ab dem Tag des 
        Vertragsabschlusses (Registrierung bzw. Premium-Buchung).</p>

        <h3>Um Ihr Widerrufsrecht auszuueben</h3>
        <p>Sie muessen uns mittels einer eindeutigen Erklaerung 
        (z.B. ein mit der Post versandter Brief, Telefax oder E-Mail) 
        ueber Ihren Entschluss informieren:</p>

        <p style="padding: 15px; background: #0A1520; border-radius: 8px;">
            <strong>XsiKOM DIGITAL Projects</strong><br>
            Komi Tevi<br>
            Am Koenigsfloss 12<br>
            55252 Mainz-Kastel<br>
            Deutschland<br><br>
            E-Mail: xsikom.projects@gmail.com<br>
            Telefon: +49 178 8977320
        </p>

        <h3>Folgen des Widerrufs</h3>
        <p>Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle 
        Zahlungen, die wir von Ihnen erhalten haben, unverzueglich und 
        spaetestens binnen vierzehn Tagen ab dem Tag zurueckzuzahlen, 
        an dem die Mitteilung ueber Ihren Widerruf bei uns eingegangen ist.</p>

        <h3>Muster-Widerrufsformular</h3>
        <div style="padding: 15px; background: #0A1520; border-radius: 8px;
                    font-family: monospace; white-space: pre-line;">
An: XsiKOM DIGITAL Projects
    Komi Tevi
    Am Koenigsfloss 12
    55252 Mainz-Kastel
    E-Mail: xsikom.projects@gmail.com

Hiermit widerrufe(n) ich/wir den von mir/uns 
abgeschlossenen Vertrag ueber die Erbringung der 
folgenden Dienstleistung:

___________________________________________

Bestellt am: _______________
Name des/der Verbraucher(s): _______________
Anschrift des/der Verbraucher(s): _______________
Datum: _______________
Unterschrift: _______________
        </div>

        <h3>Besonderheiten fuer Firmenkunden (B2B)</h3>
        <p>Fuer Unternehmer (B2B) gilt das gesetzliche Widerrufsrecht 
        nach §§ 355 ff. BGB nicht. Es gelten die Bestimmungen unserer AGB.</p>

        <h3>Ausschluss des Widerrufsrechts</h3>
        <p>Das Widerrufsrecht erlischt bei digitalen Inhalten, wenn Sie 
        ausdruecklich zugestimmt haben, dass wir mit der Ausfuehrung des 
        Vertrages vor Ablauf der Widerrufsfrist beginnen und Sie 
        bestaetigt haben, dass Sie Ihr Widerrufsrecht damit verlieren.</p>

        <p style="margin-top: 30px; padding: 15px; background: #0A1520; 
                  border-radius: 8px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026<br>
            <strong>(c) 2026 XsiKOM DIGITAL Projects - Komi Tevi</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/haftung")
def haftung():
    content = """
    <h1>⚖️ Haftungsausschluss</h1>
    <div class="legal-text">
        <h3>1. Haftung fuer Inhalte</h3>
        <p>Die Inhalte unserer Anwendung wurden mit groesster Sorgfalt 
        erstellt. Fuer die Richtigkeit, Vollstaendigkeit und Aktualitaet 
        der Inhalte koennen wir jedoch keine Gewaehr uebernehmen.</p>

        <h3>2. KI-Generierte Inhalte (WICHTIG!)</h3>
        <p>Unsere App nutzt kuenstliche Intelligenz (KI) zur Generierung 
        von Bewerbungstexten, Tipps und Beratung. Bitte beachten Sie:</p>
        
        <div class="alert-warn" style="margin: 15px 0;">
            <strong>⚠️ Wichtiger Hinweis zur KI:</strong>
            <ul style="padding-left: 25px; margin-top: 10px;">
                <li>KI-generierte Inhalte koennen <strong>fehlerhaft</strong> sein</li>
                <li>Pruefen Sie alle Inhalte vor Verwendung</li>
                <li>Keine Garantie fuer Erfolg von Bewerbungen</li>
                <li>KI-Empfehlungen ersetzen keine professionelle Beratung</li>
                <li>Nutzung auf eigenes Risiko</li>
            </ul>
        </div>

        <h3>3. Haftungsausschluss</h3>
        <p>XsiKOM DIGITAL Projects und Komi Tevi schliessen jegliche 
        Haftung aus fuer:</p>
        <ul style="padding-left: 25px;">
            <li>Direkte oder indirekte Schaeden durch Nutzung der App</li>
            <li>Datenverlust durch technische Ausfaelle</li>
            <li>Erfolglose Bewerbungen</li>
            <li>Fehlerhafte KI-Empfehlungen</li>
            <li>Probleme bei externen Diensten (E-Mail-Versand, etc.)</li>
            <li>Folgeschaeden jeglicher Art</li>
        </ul>

        <h3>4. Haftungsbeschraenkung</h3>
        <p>Die Haftung des Betreibers ist beschraenkt auf Vorsatz und grobe 
        Fahrlaessigkeit. Die Haftung fuer leicht fahrlaessige Verletzungen 
        wesentlicher Vertragspflichten (Kardinalpflichten) ist auf den 
        vorhersehbaren, typischerweise eintretenden Schaden begrenzt.</p>

        <h3>5. Haftung fuer Links</h3>
        <p>Unsere App enthaelt Links zu externen Webseiten Dritter (z.B. 
        Jobportale). Auf deren Inhalte haben wir keinen Einfluss. Fuer 
        die Inhalte verlinkter Seiten ist stets der jeweilige Anbieter 
        verantwortlich.</p>

        <h3>6. Eigenverantwortung des Nutzers</h3>
        <p>Der Nutzer ist selbst verantwortlich fuer:</p>
        <ul style="padding-left: 25px;">
            <li>Korrektheit seiner eingegebenen Daten</li>
            <li>Pruefung von KI-generierten Inhalten</li>
            <li>Aktualitaet seiner Bewerbungsunterlagen</li>
            <li>Backup seiner Daten</li>
            <li>Einhaltung von Bewerbungsfristen</li>
        </ul>

        <h3>7. Datensicherheit</h3>
        <p>Trotz hoher Sicherheitsmassnahmen koennen wir keine 100%ige 
        Sicherheit garantieren. Bitte verwenden Sie:</p>
        <ul style="padding-left: 25px;">
            <li>Sichere Passwoerter (mindestens 8 Zeichen)</li>
            <li>Aktuellen Browser</li>
            <li>Vertrauliche Login-Daten</li>
        </ul>

        <h3>8. Aenderungsvorbehalt</h3>
        <p>Wir behalten uns vor, diese App jederzeit zu aendern, 
        einzustellen oder Funktionen anzupassen.</p>

        <h3>9. Anwendbares Recht</h3>
        <p>Es gilt deutsches Recht. Gerichtsstand ist Mainz, Deutschland.</p>

        <p style="margin-top: 30px; padding: 15px; background: #0A1520; 
                  border-radius: 8px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026<br>
            <strong>(c) 2026 XsiKOM DIGITAL Projects - Komi Tevi</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/agb")
def agb():
    content = """
    <h1>📋 Allgemeine Geschaeftsbedingungen (AGB)</h1>
    <div class="legal-text">
        <h3>§ 1 Geltungsbereich</h3>
        <p>Diese AGB gelten fuer alle Nutzer des 
        XsiKOM-BewerbungsBOT von XsiKOM DIGITAL Projects.</p>

        <h3>§ 2 Vertragspartner</h3>
        <p>Vertragspartner ist:<br>
        XsiKOM DIGITAL Projects<br>
        Komi Tevi<br>
        Am Koenigsfloss 12<br>
        55252 Mainz-Kastel</p>

        <h3>§ 3 Leistungen</h3>
        <p><strong>Free-Version (kostenlos):</strong></p>
        <ul style="padding-left: 25px;">
            <li>5 Bewerbungen pro Monat</li>
            <li>1 Lebenslauf-Vorlage</li>
            <li>3 Jobportale</li>
            <li>Basis Aaliyah KI</li>
            <li>Datei-Upload (PDFs, Bilder)</li>
        </ul>

        <p><strong>Premium (1.99 EUR/Monat):</strong></p>
        <ul style="padding-left: 25px;">
            <li>UNBEGRENZTE Bewerbungen</li>
            <li>10 Lebenslauf-Vorlagen</li>
            <li>Alle Premium-Features</li>
            <li>Werbefrei</li>
            <li>Premium Aaliyah KI</li>
        </ul>

        <p><strong>Premium Jahr (19.99 EUR/Jahr):</strong> 16% Rabatt</p>

        <h3>§ 4 Vertragsabschluss</h3>
        <p>Der Vertrag kommt durch Registrierung und Zustimmung zu AGB 
        und Datenschutz zustande.</p>

        <h3>§ 5 Preise und Zahlung</h3>
        <p>Premium wird monatlich abgerechnet. Zahlung via Kreditkarte, 
        PayPal oder SEPA. Alle Preise inkl. gesetzlicher MwSt. 
        (Kleinunternehmer nach § 19 UStG).</p>

        <h3>§ 6 Widerrufsrecht</h3>
        <p>Privatkunden haben ein 14-taegiges Widerrufsrecht (siehe 
        <a href="/widerruf" style="color: #00B4D8;">Widerrufsbelehrung</a>).</p>
        <p>Fuer Firmenkunden (B2B) gilt das Widerrufsrecht nicht.</p>

        <h3>§ 7 Kuendigung</h3>
        <p>Premium-Abos sind jederzeit zum Monatsende kuendbar. 
        Account-Loeschung jederzeit moeglich.</p>

        <h3>§ 8 Haftung</h3>
        <p>Es gelten die Bestimmungen unseres 
        <a href="/haftung" style="color: #00B4D8;">Haftungsausschlusses</a>.</p>

        <p><strong>Wichtig:</strong> Keine Garantie fuer Erfolg von 
        Bewerbungen. KI-generierte Inhalte koennen Fehler enthalten.</p>

        <h3>§ 9 KI-Nutzung</h3>
        <p>Nutzer erkennen an:</p>
        <ul style="padding-left: 25px;">
            <li>KI-Inhalte sind <strong>nicht fehlerfrei</strong></li>
            <li>Inhalte muessen geprueft werden</li>
            <li>Keine professionelle Beratung ersetzbar</li>
            <li>Nutzung auf eigene Verantwortung</li>
        </ul>

        <h3>§ 10 Pflichten des Nutzers</h3>
        <p>Der Nutzer verpflichtet sich:</p>
        <ul style="padding-left: 25px;">
            <li>Wahrheitsgemaesse Daten anzugeben</li>
            <li>Zugangsdaten geheim zu halten</li>
            <li>Keine rechtswidrigen Inhalte hochzuladen</li>
            <li>Keine Spam-Bewerbungen zu versenden</li>
            <li>Geltendes Recht zu beachten</li>
        </ul>

        <h3>§ 11 Datenschutz</h3>
        <p>Es gilt unsere 
        <a href="/datenschutz" style="color: #00B4D8;">Datenschutzerklaerung</a>.</p>

        <h3>§ 12 Aenderungen der AGB</h3>
        <p>Aenderungen werden 30 Tage vor Inkrafttreten per E-Mail 
        mitgeteilt. Bei Widerspruch endet der Vertrag.</p>

        <h3>§ 13 Salvatorische Klausel</h3>
        <p>Sollten einzelne Bestimmungen unwirksam sein, bleibt der 
        Rest der AGB wirksam.</p>

        <h3>§ 14 Gerichtsstand</h3>
        <p>Gerichtsstand: Mainz, Deutschland.<br>
        Es gilt deutsches Recht.</p>

        <p style="margin-top: 30px; padding: 15px; background: #0A1520; 
                  border-radius: 8px; font-size: 12px;">
            <strong>Stand:</strong> Juni 2026<br>
            <strong>(c) 2026 XsiKOM DIGITAL Projects - Komi Tevi</strong>
        </p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ============================================================
# PWA & TWA
# ============================================================
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
    return send_from_directory(
        ".well-known", "assetlinks.json",
        mimetype="application/json"
    )


# ============================================================
# INIT
# ============================================================
db_init()
admin_anlegen()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  XsiKOM-BewerbungsBOT")
    print("=" * 60)
    print(f"  KI: {'ONLINE' if GROQ_API_KEY else 'OFFLINE - setze GROQ_API_KEY!'}")
    print(f"  URL: http://localhost:5000")
    print(f"  Login: admin / XsiKOM2026!")
    print("=" * 60 + "\n")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)