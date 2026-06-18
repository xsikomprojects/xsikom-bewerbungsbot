"""
XsiKOM-BewerbungsBOT v6.0
Mit Aaliyah KI, AVINU Global Jobs, XSI Auto-Bewerber
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
    create_password_reset_token, verify_reset_token, use_reset_token,
    request_account_deletion, cancel_deletion,
    get_deletion_status, export_user_data, audit_log
)

from avinu_ki import (
    avinu_antwort, alle_jobs_suchen, get_alle_berufe,
    jobs_speichern, jobs_laden, vorlagen_laden,
    anschreiben_generieren, auto_bewerbung_erstellen,
    job_favorit_toggle, job_loeschen, BRANCHEN
)

from xsi_bot import (
    xsi_anschreiben_komplett, xsi_betreff_erstellen,
    xsi_email_senden, xsi_bewerbung_speichern,
    xsi_bewerbung_status_update, xsi_bewerbungen_laden,
    xsi_templates_laden, xsi_statistiken,
    xsi_unterlagen_pruefen
)

import stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE = os.environ.get("STRIPE_PRICE_MONAT", "")


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(hours=2)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

DB_NAME = "bewerbungen.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "bmp", "webp"}
CONTACT_EMAIL = "xsikom_digital@xsikom.de"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_ki_antwort(frage):
    if not GROQ_API_KEY:
        return "KI offline."
    try:
        r = requests.post(GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "system", "content": "Du bist Aaliyah, KI-Karriereberaterin. Deutsch."},
                               {"role": "user", "content": frage}],
                  "temperature": 0.7, "max_tokens": 500}, timeout=15)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return "Fehler."
    except Exception:
        return "Verbindung fehlgeschlagen."


def aaliyah_tipp():
    return random.choice(["Passe Anschreiben individuell an!", "Erwaehne konkrete Projekte.",
        "Max. 1 Seite Anschreiben.", "Zeige Motivation!", "Pruefe Rechtschreibung."])


def db_init():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS benutzer (id INTEGER PRIMARY KEY AUTOINCREMENT,
        benutzername TEXT UNIQUE NOT NULL, passwort TEXT NOT NULL, email TEXT, vorname TEXT,
        nachname TEXT, rolle TEXT DEFAULT 'user', premium INTEGER DEFAULT 0,
        kunde_typ TEXT DEFAULT 'privat', erstellt TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS bewerbungen (id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, firma TEXT, email TEXT, status TEXT DEFAULT 'gesendet', datum TEXT,
        typ TEXT DEFAULT 'job')""")
    try:
        c.execute("ALTER TABLE bewerbungen ADD COLUMN typ TEXT DEFAULT 'job'")
    except Exception:
        pass
    c.execute("""CREATE TABLE IF NOT EXISTS profile (user_id INTEGER PRIMARY KEY,
        vorname TEXT, nachname TEXT, strasse TEXT, plz TEXT, stadt TEXT,
        telefon TEXT, email TEXT, geburtsdatum TEXT, kenntnisse TEXT, sprachen TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS uploads (id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, dateiname TEXT, typ TEXT, kategorie TEXT, pfad TEXT, upload_datum TEXT)""")
    conn.commit()
    conn.close()


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def admin_anlegen():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM benutzer WHERE benutzername='admin'")
    if not c.fetchone():
        c.execute("""INSERT INTO benutzer (benutzername, passwort, email, vorname, nachname, rolle, premium, erstellt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("admin", hash_pw("XsiKOM2026!"), CONTACT_EMAIL, "Komi", "Tevi", "admin", 1, datetime.now().isoformat()))
        conn.commit()
    conn.close()


def benutzer_pruefen(user, pw):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, benutzername, vorname, nachname, rolle, premium FROM benutzer WHERE benutzername=? AND passwort=?", (user, hash_pw(pw)))
    r = c.fetchone()
    conn.close()
    return {"id": r[0], "benutzername": r[1], "vorname": r[2], "nachname": r[3], "rolle": r[4], "premium": r[5]} if r else None


def benutzer_anlegen(user, pw, email, vn, nn, kunde_typ="privat"):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO benutzer (benutzername, passwort, email, vorname, nachname, kunde_typ, erstellt) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user, hash_pw(pw), email, vn, nn, kunde_typ, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def premium_aktivieren(uid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE benutzer SET premium=1 WHERE id=?", (uid,))
    conn.commit()
    conn.close()


def bewerbungen_zaehlen(uid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM bewerbungen WHERE user_id=? AND datum >= ?", (uid, datetime.now().replace(day=1).isoformat()))
    n = c.fetchone()[0]
    conn.close()
    return n


def profil_laden(uid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM profile WHERE user_id=?", (uid,))
    r = c.fetchone()
    conn.close()
    if not r: return {}
    return {"vorname": r[1] or "", "nachname": r[2] or "", "strasse": r[3] or "", "plz": r[4] or "",
            "stadt": r[5] or "", "telefon": r[6] or "", "email": r[7] or "", "geburtsdatum": r[8] or "",
            "kenntnisse": r[9] or "", "sprachen": r[10] or ""}


def profil_speichern(uid, d):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM profile WHERE user_id=?", (uid,))
    c.execute("INSERT INTO profile (user_id, vorname, nachname, strasse, plz, stadt, telefon, email, geburtsdatum, kenntnisse, sprachen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (uid, d.get("vorname",""), d.get("nachname",""), d.get("strasse",""), d.get("plz",""), d.get("stadt",""),
         d.get("telefon",""), d.get("email",""), d.get("geburtsdatum",""), d.get("kenntnisse",""), d.get("sprachen","")))
    conn.commit()
    conn.close()


def allowed_file(f):
    return "." in f and f.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def datei_speichern(file, uid, kat):
    if not file or not allowed_file(file.filename): return None
    uf = os.path.join(UPLOAD_FOLDER, str(uid))
    os.makedirs(uf, exist_ok=True)
    fn = secure_filename(file.filename)
    _, ext = os.path.splitext(fn)
    ext = ext.lower()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nn = f"{kat}_{ts}{ext}"
    pfad = os.path.join(uf, nn)
    if ext in [".png", ".gif", ".bmp", ".webp"] and kat == "bild":
        try:
            img = Image.open(file.stream)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            nn = f"{kat}_{ts}.jpg"
            pfad = os.path.join(uf, nn)
            img.save(pfad, "JPEG", quality=90)
        except Exception:
            file.seek(0)
            file.save(pfad)
    else:
        file.save(pfad)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO uploads (user_id, dateiname, typ, kategorie, pfad, upload_datum) VALUES (?, ?, ?, ?, ?, ?)",
        (uid, nn, ext, kat, pfad, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return nn


def uploads_laden(uid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, dateiname, typ, kategorie, pfad, upload_datum FROM uploads WHERE user_id=? ORDER BY id DESC", (uid,))
    rows = c.fetchall()
    conn.close()
    return rows


def upload_loeschen(uid2, uid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT pfad FROM uploads WHERE id=? AND user_id=?", (uid2, uid))
    r = c.fetchone()
    if r and os.path.exists(r[0]):
        try: os.remove(r[0])
        except: pass
    c.execute("DELETE FROM uploads WHERE id=? AND user_id=?", (uid2, uid))
    conn.commit()
    conn.close()


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
if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js')});}
function cookieAccept(){localStorage.setItem('cookie_ok','yes');document.getElementById('cookie-banner').style.display='none';}
window.addEventListener('load',function(){if(localStorage.getItem('cookie_ok')!=='yes'){var b=document.getElementById('cookie-banner');if(b)b.style.display='block';}});
</script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0A0E1A;--card:rgba(20,28,48,0.6);--border:rgba(255,255,255,0.08);--cyan:#00D9FF;--purple:#8B5CF6;--green:#10F4B1;--yellow:#FFD93D;--red:#FF4757;--txt:#FFFFFF;--txt2:#A0AEC0;--txt3:#6B7280}
body{font-family:'Poppins',sans-serif;background:var(--bg);color:var(--txt);min-height:100vh}
body::before{content:'';position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(circle at 20% 20%,rgba(0,217,255,0.15) 0%,transparent 50%),radial-gradient(circle at 80% 80%,rgba(139,92,246,0.15) 0%,transparent 50%);z-index:-1}
.container{max-width:1200px;margin:0 auto;padding:20px}
.header{background:rgba(10,14,26,0.8);backdrop-filter:blur(20px);padding:20px 0;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}
.header-inner{display:flex;justify-content:space-between;align-items:center}
.logo{font-family:'Space Grotesk',sans-serif;font-size:32px;font-weight:700;background:linear-gradient(135deg,var(--cyan),var(--purple));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.subtitle{color:var(--txt2);font-size:13px}
.nav{background:rgba(19,24,41,0.5);padding:12px 0;border-bottom:1px solid var(--border);overflow-x:auto;white-space:nowrap}
.nav-inner{max-width:1200px;margin:0 auto;padding:0 20px;display:flex;gap:5px}
.nav a{color:var(--txt2);text-decoration:none;padding:10px 18px;border-radius:12px;font-size:14px;transition:all 0.3s}
.nav a:hover{color:var(--txt);background:rgba(0,217,255,0.1)}
.card{background:var(--card);backdrop-filter:blur(20px);border-radius:20px;padding:30px;margin:20px 0;border:1px solid var(--border);transition:all 0.4s}
.card:hover{transform:translateY(-5px);border-color:rgba(0,217,255,0.3)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:14px 28px;border:none;border-radius:12px;cursor:pointer;font-weight:600;font-size:14px;text-decoration:none;transition:all 0.3s;font-family:'Poppins',sans-serif}
.btn:hover{transform:translateY(-2px)}
.btn-primary{background:linear-gradient(135deg,var(--cyan),#0099CC);color:white}
.btn-success{background:linear-gradient(135deg,var(--green),#059669);color:white}
.btn-warning{background:linear-gradient(135deg,var(--yellow),#F59E0B);color:#0A0E1A}
.btn-danger{background:linear-gradient(135deg,var(--red),#DC2626);color:white}
.btn-purple{background:linear-gradient(135deg,var(--purple),#6D28D9);color:white}
input,textarea,select{background:rgba(10,14,26,0.6);border:1px solid var(--border);color:var(--txt);padding:14px 18px;border-radius:12px;width:100%;margin-bottom:12px;font-size:14px;font-family:'Poppins',sans-serif}
input:focus,textarea:focus,select:focus{outline:none;border-color:var(--cyan);box-shadow:0 0 0 4px rgba(0,217,255,0.1)}
h1{font-family:'Space Grotesk',sans-serif;font-size:36px;font-weight:700;background:linear-gradient(135deg,var(--cyan),var(--purple));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:20px}
h2{font-size:26px;font-weight:600;margin-bottom:16px}
h3{font-size:18px;font-weight:600;color:var(--cyan);margin-bottom:12px}
p{line-height:1.7;color:var(--txt2);margin-bottom:8px}
a{color:var(--cyan);text-decoration:none}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}
.stat-card{background:linear-gradient(135deg,rgba(20,28,48,0.8),rgba(30,38,58,0.6));border:1px solid var(--border);border-radius:20px;padding:30px;text-align:center;transition:all 0.4s;cursor:pointer}
.stat-card:hover{transform:translateY(-8px);border-color:var(--cyan)}
.stat-icon{font-size:48px;margin-bottom:12px}
.stat-value{font-family:'Space Grotesk',sans-serif;font-size:32px;font-weight:700;background:linear-gradient(135deg,var(--cyan),var(--purple));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.stat-label{color:var(--txt2);font-size:13px;margin-top:4px}
.badge{background:linear-gradient(135deg,var(--yellow),#EC4899);color:var(--bg);padding:6px 14px;border-radius:20px;font-size:11px;font-weight:700;display:inline-block}
.alert{padding:16px 20px;border-radius:12px;margin:16px 0;border:1px solid;display:flex;align-items:center;gap:12px}
.alert-ok{background:rgba(16,244,177,0.1);border-color:rgba(16,244,177,0.3);color:var(--green)}
.alert-err{background:rgba(255,71,87,0.1);border-color:rgba(255,71,87,0.3);color:var(--red)}
.alert-warn{background:rgba(255,217,61,0.1);border-color:rgba(255,217,61,0.3);color:var(--yellow)}
.alert-info{background:rgba(0,217,255,0.1);border-color:rgba(0,217,255,0.3);color:var(--cyan)}
.upload-item{background:rgba(10,14,26,0.6);padding:16px;border-radius:12px;margin:10px 0;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--border)}
.footer{background:rgba(10,14,26,0.9);padding:40px 20px 30px;text-align:center;color:var(--txt3);margin-top:60px;border-top:1px solid var(--border)}
.footer a{color:var(--txt2);margin:0 12px}
.footer-brand{margin-top:16px;font-family:'Space Grotesk',sans-serif;font-weight:600;color:var(--cyan)}
#cookie-banner{display:none;position:fixed;bottom:20px;left:20px;right:20px;max-width:1160px;margin:0 auto;background:rgba(20,28,48,0.95);color:white;padding:20px 25px;z-index:9999;border-radius:16px;border:1px solid var(--cyan)}
.legal-text{background:var(--card);padding:30px;border-radius:20px;margin:20px 0;line-height:1.8;border:1px solid var(--border)}
.legal-text h3{color:var(--cyan);margin-top:24px}
@media(max-width:768px){h1{font-size:28px}.logo{font-size:24px}}
</style>
</head>
<body>
<div id="cookie-banner">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px">
<div>🍪 Cookies. <a href="/datenschutz" style="color:var(--cyan)">Mehr</a></div>
<button onclick="cookieAccept()" class="btn btn-success">✓</button>
</div></div>
<div class="header"><div class="container header-inner"><div>
<div class="logo">XsiKOM</div>
<div class="subtitle">{{ user.vorname if user else 'KI Bewerbungs-Assistent' }}</div>
</div></div></div>
{% if user %}
<div class="nav"><div class="nav-inner">
<a href="/dashboard">🏠 Dashboard</a>
<a href="/aaliyah">🤖 Aaliyah</a>
<a href="/avinu">⚡ AVINU</a>
<a href="/xsi">🤖 XSI Bot</a>
<a href="/lebenslauf">📝 Lebenslauf</a>
<a href="/uploads">📂 Dateien</a>
<a href="/bewerbungen">📧 Bewerbungen</a>
<a href="/premium">💎 Premium</a>
<a href="/profil">⚙️ Profil</a>
<a href="/logout">🚪 Logout</a>
</div></div>
{% endif %}
<div class="container">{{ content|safe }}</div>
<div class="footer">
<div><a href="/impressum">Impressum</a>•<a href="/datenschutz">Datenschutz</a>•<a href="/agb">AGB</a>•<a href="/widerruf">Widerruf</a>•<a href="/haftung">Haftung</a></div>
<div class="footer-brand">XsiKOM-BewerbungsBOT</div>
<div style="margin-top:8px;font-size:11px;color:var(--txt3)">© 2026 XsiKOM DIGITAL Projects • Komi Tevi<br>
<a href="mailto:xsikom_digital@xsikom.de" style="color:var(--txt3)">xsikom_digital@xsikom.de</a></div>
</div></body></html>"""


@app.route("/")
def index():
    return redirect("/dashboard") if "user_id" in session else redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        result = benutzer_pruefen(request.form.get("username","").strip(), request.form.get("password","").strip())
        if result:
            for k in ["user_id", "username", "vorname", "nachname", "rolle", "premium"]:
                session[k] = result.get({"user_id": "id"}.get(k, k), "")
            session["user_id"] = result["id"]
            return redirect("/dashboard")
        msg = '<div class="alert alert-err">❌ Login falsch!</div>'
    content = f"""
    <div style="max-width:450px;margin:60px auto"><div class="card">
    <h1 style="text-align:center">🔐 Anmelden</h1>{msg}
    <form method="POST">
    <input type="text" name="username" value="admin" placeholder="Benutzername" required>
    <input type="password" name="password" placeholder="Passwort" required>
    <button type="submit" class="btn btn-primary" style="width:100%">🚀 Anmelden</button>
    </form>
    <p style="text-align:center;margin-top:25px"><a href="/register">✨ Neuen Account</a></p>
    </div></div>"""
    return render_template_string(BASE_HTML, content=content, user=None)


@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","").strip()
        e = request.form.get("email","").strip()
        if not all([u, p, e, request.form.get("datenschutz"), request.form.get("agb"), request.form.get("widerruf")]):
            msg = '<div class="alert alert-err">❌ Alle Felder!</div>'
        elif len(p) < 6:
            msg = '<div class="alert alert-err">❌ Min. 6 Zeichen!</div>'
        elif benutzer_anlegen(u, p, e, request.form.get("vorname",""), request.form.get("nachname",""), request.form.get("kunde_typ","privat")):
            return redirect("/login")
        else:
            msg = '<div class="alert alert-err">❌ Name vergeben!</div>'
    content = f"""
    <div style="max-width:600px;margin:30px auto"><div class="card"><h1>✨ Registrieren</h1>{msg}
    <form method="POST">
    <select name="kunde_typ" required><option value="privat">👤 Privat</option><option value="firma">🏢 Firma</option></select>
    <input type="text" name="username" placeholder="Benutzername" required>
    <input type="password" name="password" placeholder="Passwort" required>
    <input type="email" name="email" placeholder="E-Mail" required>
    <input type="text" name="vorname" placeholder="Vorname">
    <input type="text" name="nachname" placeholder="Nachname">
    <div style="margin-top:20px;padding:20px;background:rgba(10,14,26,0.5);border-radius:12px">
    <p><input type="checkbox" name="datenschutz" required style="width:auto"> <a href="/datenschutz" target="_blank">Datenschutz</a></p>
    <p><input type="checkbox" name="agb" required style="width:auto"> <a href="/agb" target="_blank">AGB</a></p>
    <p><input type="checkbox" name="widerruf" required style="width:auto"> <a href="/widerruf" target="_blank">Widerruf</a></p>
    </div>
    <button type="submit" class="btn btn-success" style="width:100%">🚀 Account erstellen</button>
    </form></div></div>"""
    return render_template_string(BASE_HTML, content=content, user=None)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect("/login")
    bw = bewerbungen_zaehlen(session["user_id"])
    limit = "∞" if session.get("premium") else "5"
    badge = '<span class="badge">⭐ PREMIUM</span>' if session.get("premium") else ""
    upgrade = '<a href="/premium" class="btn btn-warning">💎 Upgrade</a>' if not session.get("premium") else ""
    content = f"""
    <h1>👋 Hallo, {session.get('vorname','')}!</h1>
    <div class="card"><h3>📊 Plan: {"Premium" if session.get("premium") else "Free"} {badge}</h3>
    <p>Bewerbungen: <strong>{bw} / {limit}</strong></p>{upgrade}</div>
    <h2 style="margin-top:40px">⚡ Schnellaktionen</h2>
    <div class="grid">
    <a href="/aaliyah" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">🤖</div><div class="stat-value">Aaliyah</div><div class="stat-label">KI Chat</div></div></a>
    <a href="/avinu" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">⚡</div><div class="stat-value">AVINU</div><div class="stat-label">Global Jobs</div></div></a>
    <a href="/xsi" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">🤖</div><div class="stat-value">XSI</div><div class="stat-label">Auto-Bewerber</div></div></a>
    <a href="/lebenslauf" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">📝</div><div class="stat-value">Lebenslauf</div><div class="stat-label">Bearbeiten</div></div></a>
    <a href="/profil" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">⚙️</div><div class="stat-value">Profil</div><div class="stat-label">Sicherheit</div></div></a>
    </div>
    <div class="card" style="margin-top:30px"><h3>💡 Tipp</h3><p>{aaliyah_tipp()}</p></div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/aaliyah", methods=["GET", "POST"])
def aaliyah_route():
    if "user_id" not in session: return redirect("/login")
    antwort = ""
    if request.method == "POST":
        frage = request.form.get("frage","")
        if frage:
            a = get_ki_antwort(frage).replace("\n", "<br>")
            antwort = f'<div class="alert alert-info" style="flex-direction:column;align-items:start"><strong>🤖 Aaliyah:</strong><div style="margin-top:10px">{a}</div></div>'
    content = f"""<h1>🤖 Aaliyah KI</h1><div class="card"><form method="POST">
    <input type="text" name="frage" placeholder="Frag Aaliyah..." required>
    <button type="submit" class="btn btn-purple" style="width:100%">📤 Senden</button></form>{antwort}</div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/avinu", methods=["GET", "POST"])
def avinu_dashboard():
    if "user_id" not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        branche = request.form.get("branche","")
        suchbegriff = request.form.get("suchbegriff","")
        standort = request.form.get("standort","")
        radius = int(request.form.get("radius", 25))
        international = request.form.get("international") == "yes"
        if not suchbegriff and branche:
            suchbegriff = BRANCHEN.get(branche, ["Job"])[0]
        if suchbegriff and standort:
            try:
                alle = alle_jobs_suchen(suchbegriff, standort, radius, international)
                if alle:
                    n = jobs_speichern(session["user_id"], alle, branche, radius)
                    msg = f'<div class="alert alert-ok">✅ {n} neue Jobs!</div>'
                else:
                    msg = '<div class="alert alert-warn">⚠️ Keine Jobs!</div>'
            except Exception as e:
                msg = f'<div class="alert alert-err">❌ {str(e)[:100]}</div>'

    ft = request.args.get("filter", "offen")
    jobs = jobs_laden(session["user_id"], ft)
    berufe_options = "".join([f'<option value="{b}">' for b in get_alle_berufe()])
    branchen_html = "".join([f'<option value="{k}">{v}</option>' for k,v in
        {"it":"💻 IT","handwerk":"🔧 Handwerk","gesundheit":"🏥 Gesundheit","verwaltung":"📋 Verwaltung",
         "verkauf":"🛒 Verkauf","logistik":"📦 Logistik","gastronomie":"🍽️ Gastronomie","bildung":"📚 Bildung",
         "marketing":"📱 Marketing","finanzen":"💰 Finanzen","transport":"🚚 Transport",
         "produktion":"🏭 Produktion","reinigung":"🧹 Reinigung","sicherheit":"🛡️ Sicherheit"}.items()])

    jobs_html = ""
    for j in jobs[:30]:
        bew_badge = '<span style="background:var(--green);color:white;padding:4px 10px;border-radius:12px;font-size:11px">✅</span>' if j[11] else ''
        fav = j[13] if len(j)>13 else 0
        land = j[15] if len(j)>15 else "DE"
        flag = {"DE":"🇩🇪","US":"🇺🇸","UK":"🇬🇧","FR":"🇫🇷","EU":"🇪🇺","WORLD":"🌍","INT":"🌍"}.get(land,"🌍")
        url_link = f'<a href="{j[6]}" target="_blank">🔗</a>' if j[6] else ""
        beschr = j[5][:200]+"..." if j[5] and len(j[5])>200 else (j[5] or "")
        jobs_html += f"""<div class="card"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:15px">
        <div style="flex:1;min-width:280px"><h3>{flag} {j[3]} {bew_badge}</h3>
        <p style="color:var(--cyan);font-size:16px">🏢 <strong>{j[2]}</strong></p>
        <p style="color:var(--txt2);font-size:13px">📍 {j[4]} · 🔗 {j[9]} · 🏷️ {j[8]}</p>
        {f'<p style="color:var(--txt3);font-size:13px">{beschr}</p>' if beschr else ''}<p>{url_link}</p></div>
        <div style="display:flex;flex-direction:column;gap:8px">
        <a href="/xsi/schnell/{j[0]}" class="btn btn-success">🤖 XSI</a>
        <a href="/avinu/favorit/{j[0]}" class="btn btn-warning" style="padding:8px 14px">{"⭐" if fav else "☆"}</a>
        <a href="/avinu/loeschen/{j[0]}" class="btn btn-danger" style="padding:8px 14px" onclick="return confirm('?')">🗑️</a>
        </div></div></div>"""
    if not jobs_html:
        jobs_html = '<p style="text-align:center;color:var(--txt3);padding:40px">Keine Jobs!</p>'

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM jobs WHERE user_id=?", (session["user_id"],))
    total = c.fetchone()[0]
    try:
        c.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND beworben=1", (session["user_id"],))
        bew_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND favorit=1", (session["user_id"],))
        fav_count = c.fetchone()[0]
    except:
        bew_count = fav_count = 0
    conn.close()

    content = f"""<h1>⚡ AVINU - Global Job Bot</h1><p>10+ Portale · 300+ Berufe · 🌍 Weltweit</p>{msg}
    <div class="card"><h3>🔍 Job-Suche</h3><form method="POST">
    <p>📂 Branche:</p><select name="branche"><option value="">-- Branche --</option>{branchen_html}</select>
    <p>💼 Beruf:</p><input type="text" name="suchbegriff" placeholder="IT-Fachtechniker, IT-Netzwerktechniker, Praktikum..." list="bl" required><datalist id="bl">{berufe_options}</datalist>
    <p>📍 Standort:</p><input type="text" name="standort" placeholder="Berlin, Mainz, London..." required>
    <p>📏 Umkreis: <span id="rv">25</span> km</p>
    <input type="range" name="radius" min="5" max="200" value="25" step="5" oninput="document.getElementById('rv').textContent=this.value" style="width:100%;margin-bottom:15px">
    <div style="margin:20px 0;padding:15px;background:rgba(0,217,255,0.1);border-radius:12px">
    <label style="display:flex;align-items:center;gap:10px;cursor:pointer">
    <input type="checkbox" name="international" value="yes" style="width:auto">
    <span>🌍 <strong>International</strong></span></label></div>
    <button type="submit" class="btn btn-primary" style="width:100%">🚀 Jobs suchen</button></form></div>
    <div class="grid" style="margin:30px 0">
    <a href="/avinu?filter=alle" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">💼</div><div class="stat-value">{total}</div><div class="stat-label">Alle</div></div></a>
    <a href="/avinu?filter=offen" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">📋</div><div class="stat-value">{total-bew_count}</div><div class="stat-label">Offen</div></div></a>
    <a href="/avinu?filter=beworben" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">✅</div><div class="stat-value">{bew_count}</div><div class="stat-label">Beworben</div></div></a>
    <a href="/avinu?filter=favoriten" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">⭐</div><div class="stat-value">{fav_count}</div><div class="stat-label">Favoriten</div></div></a>
    </div><h2>🎯 Jobs ({len(jobs)})</h2>{jobs_html}"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/avinu/favorit/<int:jid>")
def avinu_favorit(jid):
    if "user_id" not in session: return redirect("/login")
    job_favorit_toggle(jid, session["user_id"])
    return redirect("/avinu")


@app.route("/avinu/loeschen/<int:jid>")
def avinu_loeschen(jid):
    if "user_id" not in session: return redirect("/login")
    job_loeschen(jid, session["user_id"])
    return redirect("/avinu")


# ============================================================
# XSI BOT
# ============================================================
@app.route("/xsi")
def xsi_dashboard():
    if "user_id" not in session: return redirect("/login")
    stats = xsi_statistiken(session["user_id"])
    check = xsi_unterlagen_pruefen(session["user_id"])

    unt_status = ""
    if not check["komplett"]:
        missing = []
        if not check["lebenslauf"]: missing.append("📄 Lebenslauf")
        if not check["zeugnis"]: missing.append("📜 Zeugnis")
        if not check["zertifikat"]: missing.append("🏆 Zertifikat")
        if not check["bild"]: missing.append("🖼️ Foto")
        unt_status = f'<div class="alert alert-warn">⚠️ Fehlend: {", ".join(missing)} <a href="/uploads">📂 Hochladen</a></div>'
    else:
        unt_status = '<div class="alert alert-ok">✅ Alle Unterlagen da!</div>'

    bews = xsi_bewerbungen_laden(session["user_id"])
    bew_html = ""
    for b in bews[:10]:
        si = {"erstellt":"📝","gesendet":"✅","antwort":"💬","absage":"❌"}.get(b[9],"📋")
        bew_html += f"""<div class="upload-item"><div>{si} <strong>{b[4]}</strong> bei {b[3]}<br>
        <small style="color:var(--txt3)">An: {b[5] or 'N/A'} · {b[9]} · {b[12][:16] if b[12] else 'N/A'}</small></div>
        <a href="/xsi/detail/{b[0]}" class="btn btn-primary" style="padding:8px 14px">👁️</a></div>"""
    if not bew_html:
        bew_html = '<p style="text-align:center;color:var(--txt3)">Noch keine</p>'

    content = f"""<h1>🤖 XSI Bot - Auto-Bewerber</h1><p>Automatisch Bewerbungen erstellen & senden!</p>
    {unt_status}
    <div class="grid" style="margin:30px 0">
    <a href="/xsi/neu" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">✨</div><div class="stat-value">Neu</div><div class="stat-label">Bewerbung</div></div></a>
    <div class="stat-card"><div class="stat-icon">📧</div><div class="stat-value">{stats['gesendet']}</div><div class="stat-label">Gesendet</div></div>
    <div class="stat-card"><div class="stat-icon">📝</div><div class="stat-value">{stats['erstellt']}</div><div class="stat-label">Entwuerfe</div></div>
    <div class="stat-card"><div class="stat-icon">📂</div><div class="stat-value">{stats['unterlagen']}</div><div class="stat-label">Unterlagen</div></div>
    </div>
    <h2>📧 Bewerbungen</h2><div class="card">{bew_html}</div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/xsi/neu", methods=["GET", "POST"])
def xsi_neu():
    if "user_id" not in session: return redirect("/login")
    profil = profil_laden(session["user_id"])
    msg = ""

    if request.method == "POST":
        firma = request.form.get("firma","").strip()
        position = request.form.get("position","").strip()
        empfaenger = request.form.get("empfaenger","").strip()
        template_id = request.form.get("template_id","")
        sprache = request.form.get("sprache","de")
        typ = request.form.get("typ","job")
        aktion = request.form.get("aktion","erstellen")

        if firma and position and template_id:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM xsi_templates WHERE id=?", (int(template_id),))
            template = c.fetchone()
            conn.close()

            if template:
                betreff = xsi_betreff_erstellen(template[2], firma, position, profil)
                anschreiben = xsi_anschreiben_komplett(template[3], firma, position, profil, sprache)
                bid = xsi_bewerbung_speichern(session["user_id"], 0, firma, position, empfaenger, betreff, anschreiben, "erstellt", sprache)

                if aktion == "senden" and empfaenger:
                    ok, info = xsi_email_senden(empfaenger, betreff, anschreiben, session["user_id"], profil)
                    if ok:
                        xsi_bewerbung_status_update(bid, "gesendet")
                        msg = f'<div class="alert alert-ok">✅ An {firma} gesendet! {info}</div>'
                    else:
                        msg = f'<div class="alert alert-err">❌ {info}</div>'
                else:
                    msg = '<div class="alert alert-ok">✅ Entwurf gespeichert!</div>'

    templates = xsi_templates_laden(premium=session.get("premium", False))
    tpl_html = ""
    for t in templates:
        pb = '<span class="badge">💎</span>' if t[5] else ''
        tpl_html += f"""<label style="display:block;margin:10px 0;padding:16px;background:rgba(10,14,26,0.5);border-radius:12px;cursor:pointer">
        <input type="radio" name="template_id" value="{t[0]}" required>
        <strong>{t[1]}</strong> {pb}<br><small style="color:var(--txt3)">Betreff: {t[2][:50]}... | {t[4].upper()}</small></label>"""

    check = xsi_unterlagen_pruefen(session["user_id"])
    unt_html = ""
    for kat, ok in [("📄 Lebenslauf", check["lebenslauf"]), ("📜 Zeugnis", check["zeugnis"]),
                     ("🏆 Zertifikat", check["zertifikat"]), ("🖼️ Foto", check["bild"])]:
        unt_html += f'<span style="margin-right:15px">{"✅" if ok else "❌"} {kat}</span>'

    content = f"""<h1>✨ Neue Bewerbung mit XSI</h1>{msg}
    <div class="card"><h3>📋 Unterlagen</h3><div style="margin:10px 0">{unt_html}</div>
    {'<a href="/uploads" class="btn btn-warning">📂 Hochladen</a>' if not check["komplett"] else ''}</div>

    <div class="card"><h3>📧 Bewerbung</h3><form method="POST">
    <p>📋 Art der Bewerbung:</p>
    <select name="typ">
    <option value="job">💼 Stellenbewerbung</option>
    <option value="praktikum">🎓 Praktikum</option>
    <option value="ausbildung">📚 Ausbildung</option>
    <option value="initiativ">💡 Initiativbewerbung</option>
    <option value="werkstudent">🧑‍💻 Werkstudent</option>
    <option value="minijob">💶 Minijob</option>
    </select>

    <p>🏢 Firma:</p>
    <input type="text" name="firma" placeholder="SAP, Telekom, Siemens, Google..." required>
    <p>💼 Position:</p>
    <input type="text" name="position" placeholder="IT-Fachtechniker, Netzwerktechniker, Praktikant..." required>
    <p>📧 E-Mail der Firma:</p>
    <input type="email" name="empfaenger" placeholder="bewerbung@firma.de">

    <p>🌍 Sprache:</p>
    <select name="sprache">
    <option value="de">🇩🇪 Deutsch</option>
    <option value="en">🇬🇧 English</option>
    <option value="fr">🇫🇷 Francais</option>
    </select>

    <p>📝 Vorlage:</p>{tpl_html}

    <div style="display:flex;gap:10px;margin-top:20px">
    <button type="submit" name="aktion" value="erstellen" class="btn btn-primary" style="flex:1">📝 Entwurf</button>
    <button type="submit" name="aktion" value="senden" class="btn btn-success" style="flex:1">🚀 Erstellen & Senden!</button>
    </div></form></div>

    <div class="alert alert-info">💡 XSI generiert KI-Anschreiben + haengt ALLE Unterlagen an!</div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/xsi/schnell/<int:job_id>")
def xsi_schnell(job_id):
    """Schnell-Bewerbung direkt aus AVINU Job-Liste."""
    if "user_id" not in session: return redirect("/login")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT firma, position FROM jobs WHERE id=? AND user_id=?", (job_id, session["user_id"]))
    j = c.fetchone()
    conn.close()
    if not j: return redirect("/avinu")
    return redirect(f"/xsi/neu?firma={j[0]}&position={j[1]}")


@app.route("/xsi/detail/<int:bid>")
def xsi_detail(bid):
    if "user_id" not in session: return redirect("/login")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM xsi_bewerbungen WHERE id=? AND user_id=?", (bid, session["user_id"]))
    b = c.fetchone()
    conn.close()
    if not b: return redirect("/xsi")
    si = {"erstellt":"📝 Entwurf","gesendet":"✅ Gesendet","antwort":"💬 Antwort","absage":"❌ Absage"}.get(b[9], b[9])
    content = f"""<h1>📧 Bewerbung</h1>
    <div class="card"><h3>{si}</h3>
    <p><strong>🏢</strong> {b[3]}</p><p><strong>💼</strong> {b[4]}</p>
    <p><strong>📧</strong> {b[5] or 'N/A'}</p><p><strong>📝</strong> {b[6]}</p>
    <p><strong>📅</strong> {b[12][:16] if b[12] else 'N/A'}</p>
    <p><strong>📎</strong> {b[8] or 'Keine'}</p></div>
    <div class="card"><h3>✉️ Anschreiben</h3><textarea rows="20">{b[7]}</textarea></div>
    <a href="/xsi" class="btn btn-primary">← Zurueck</a>"""
    return render_template_string(BASE_HTML, content=content, user=session)


# Uploads + Lebenslauf + Bewerbungen + Premium + Profil + Legal
@app.route("/uploads", methods=["GET", "POST"])
def uploads():
    if "user_id" not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        kat = request.form.get("kategorie","dokument")
        if "datei" in request.files:
            f = request.files["datei"]
            if f and f.filename and allowed_file(f.filename):
                r = datei_speichern(f, session["user_id"], kat)
                if r: msg = f'<div class="alert alert-ok">✅ {r}!</div>'
    uu = uploads_laden(session["user_id"])
    uh = ""
    for u in uu:
        ic = "📄" if u[2]==".pdf" else "🖼️"
        uh += f'<div class="upload-item"><div>{ic} <strong>{u[1]}</strong><br><small>{u[3]}-{u[5][:16]}</small></div><div><a href="/download/{u[0]}" class="btn btn-primary" style="padding:8px 14px">⬇️</a> <a href="/delete/{u[0]}" class="btn btn-danger" style="padding:8px 14px" onclick="return confirm(\'?\')">🗑️</a></div></div>'
    if not uh: uh = '<p>Keine Dateien</p>'
    content = f"""<h1>📂 Dateien</h1>{msg}
    <div class="card"><form method="POST" enctype="multipart/form-data">
    <select name="kategorie" required><option value="lebenslauf">📄 Lebenslauf</option><option value="zeugnis">📜 Zeugnis</option><option value="zertifikat">🏆 Zertifikat</option><option value="bild">🖼️ Bewerbungsbild</option></select>
    <input type="file" name="datei" required accept=".pdf,.png,.jpg,.jpeg">
    <button type="submit" class="btn btn-success" style="width:100%">🚀 Upload</button></form></div>
    <div class="card">{uh}</div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/download/<int:uid>")
def download_datei(uid):
    if "user_id" not in session: return redirect("/login")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT pfad, dateiname FROM uploads WHERE id=? AND user_id=?", (uid, session["user_id"]))
    r = c.fetchone()
    conn.close()
    if r and os.path.exists(r[0]): return send_file(r[0], as_attachment=True, download_name=r[1])
    return "Nicht gefunden", 404


@app.route("/delete/<int:uid>")
def delete_datei(uid):
    if "user_id" not in session: return redirect("/login")
    upload_loeschen(uid, session["user_id"])
    return redirect("/uploads")


@app.route("/lebenslauf", methods=["GET", "POST"])
def lebenslauf():
    if "user_id" not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        d = {k: request.form.get(k,"") for k in ["vorname","nachname","strasse","plz","stadt","telefon","email","geburtsdatum","kenntnisse","sprachen"]}
        profil_speichern(session["user_id"], d)
        msg = '<div class="alert alert-ok">✅</div>'
    p = profil_laden(session["user_id"])
    content = f"""<h1>📝 Lebenslauf</h1>{msg}
    <form method="POST"><div class="card"><h3>👤 Daten</h3>
    <input type="text" name="vorname" placeholder="Vorname" value="{p.get('vorname','')}">
    <input type="text" name="nachname" placeholder="Nachname" value="{p.get('nachname','')}">
    <input type="text" name="strasse" placeholder="Strasse" value="{p.get('strasse','')}">
    <input type="text" name="plz" placeholder="PLZ" value="{p.get('plz','')}">
    <input type="text" name="stadt" placeholder="Stadt" value="{p.get('stadt','')}">
    <input type="text" name="telefon" placeholder="Telefon" value="{p.get('telefon','')}">
    <input type="email" name="email" placeholder="E-Mail" value="{p.get('email','')}">
    <input type="text" name="geburtsdatum" placeholder="Geburtsdatum" value="{p.get('geburtsdatum','')}">
    </div><div class="card"><h3>💼 Kenntnisse</h3><textarea name="kenntnisse" rows="6">{p.get('kenntnisse','')}</textarea></div>
    <div class="card"><h3>🌍 Sprachen</h3><textarea name="sprachen" rows="4">{p.get('sprachen','')}</textarea></div>
    <button type="submit" class="btn btn-success">💾</button></form>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/bewerbungen", methods=["GET", "POST"])
def bewerbungen():
    if "user_id" not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        f = request.form.get("firma","").strip()
        e = request.form.get("email","").strip()
        t = request.form.get("typ","job")
        bw = bewerbungen_zaehlen(session["user_id"])
        if not session.get("premium") and bw >= 5:
            msg = '<div class="alert alert-warn">⚠️ Limit!</div>'
        elif f and e:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            try:
                c.execute("INSERT INTO bewerbungen (user_id, firma, email, datum, typ) VALUES (?, ?, ?, ?, ?)",
                      (session["user_id"], f, e, datetime.now().isoformat(), t))
            except Exception:
                c.execute("INSERT INTO bewerbungen (user_id, firma, email, datum) VALUES (?, ?, ?, ?)",
                      (session["user_id"], f, e, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            msg = f'<div class="alert alert-ok">✅ {f}!</div>'
    bw = bewerbungen_zaehlen(session["user_id"])
    limit = "∞" if session.get("premium") else 5
    content = f"""<h1>📧 Bewerbungen</h1><div class="card"><h3>📊 {bw} / {limit}</h3></div>{msg}
    <div class="card"><form method="POST">
    <select name="typ"><option value="job">💼 Job</option><option value="praktikum">🎓 Praktikum</option>
    <option value="ausbildung">📚 Ausbildung</option><option value="werkstudent">🧑‍💻 Werkstudent</option></select>
    <input type="text" name="firma" placeholder="Firma" required>
    <input type="email" name="email" placeholder="E-Mail" required>
    <button type="submit" class="btn btn-success">💾</button></form></div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/premium")
def premium():
    content = """<h1>💎 Premium</h1><div class="grid">
    <div class="card"><h2>🆓 Free</h2><h3>0 €</h3><ul style="list-style:none"><li>✓ 5 Bewerbungen</li></ul>
    <button class="btn btn-primary" style="width:100%">Aktuell</button></div>
    <div class="card" style="border:2px solid var(--yellow)"><span class="badge">BELIEBT</span>
    <h2>💎 Premium</h2><h3>1.99 €/Monat</h3><ul style="list-style:none"><li>✓ Unbegrenzt</li><li>✓ Premium Vorlagen</li><li>✓ XSI Auto-Sender</li></ul>
    <a href="/aktivieren" class="btn btn-warning" style="width:100%">🚀 Upgrade</a></div></div>"""
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/aktivieren", methods=["GET", "POST"])
def aktivieren():
    if "user_id" not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        code = request.form.get("code","").strip()
        if code == "XSIKOM-ADMIN-2026-PREMIUM":
            premium_aktivieren(session["user_id"])
            session["premium"] = 1
            return render_template_string(BASE_HTML, content='<h1>🎉</h1><div class="alert alert-ok">✅ Premium!</div><a href="/dashboard" class="btn btn-primary">Dashboard</a>', user=session)
        msg = '<div class="alert alert-err">❌</div>'
    stripe_btn = ""
    if stripe.api_key and STRIPE_PRICE:
        stripe_btn = '<a href="/stripe-checkout" class="btn btn-warning" style="width:100%;margin-top:15px">💳 Mit Kreditkarte (1.99€)</a>'
    content = f"""<h1>🔐 Premium</h1>{msg}
    <div class="card"><h3>🔑 Code</h3><form method="POST">
    <input type="text" name="code" placeholder="Premium-Code" required>
    <button type="submit" class="btn btn-success" style="width:100%">🚀</button></form></div>
    <div class="card"><h3>💳 Zahlung</h3>{stripe_btn if stripe_btn else '<p style="color:var(--txt3)">Stripe wird konfiguriert...</p>'}</div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/stripe-checkout")
def stripe_checkout():
    if "user_id" not in session: return redirect("/login")
    if not stripe.api_key or not STRIPE_PRICE: return redirect("/aktivieren")
    try:
        domain = request.host_url.rstrip("/")
        cs = stripe.checkout.Session.create(
            payment_method_types=["card"], line_items=[{"price": STRIPE_PRICE, "quantity": 1}],
            mode="subscription", success_url=f"{domain}/stripe-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{domain}/premium", metadata={"user_id": str(session["user_id"])})
        return redirect(cs.url, code=303)
    except Exception as e:
        return render_template_string(BASE_HTML, content=f'<h1>❌</h1><div class="alert alert-err">{str(e)[:200]}</div>', user=session)


@app.route("/stripe-success")
def stripe_success():
    if "user_id" not in session: return redirect("/login")
    sid = request.args.get("session_id")
    if sid and stripe.api_key:
        try:
            cs = stripe.checkout.Session.retrieve(sid)
            if cs.payment_status == "paid":
                premium_aktivieren(session["user_id"])
                session["premium"] = 1
        except: pass
    return render_template_string(BASE_HTML, content='<h1>🎉 Premium!</h1><div class="alert alert-ok">✅</div><a href="/dashboard" class="btn btn-primary">Dashboard</a>', user=session)


@app.route("/profil")
def profil():
    if "user_id" not in session: return redirect("/login")
    two_fa, _ = get_2fa_status(session["user_id"])
    content = f"""<h1>⚙️ Profil</h1><div class="grid">
    <a href="/profil/edit" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">👤</div><div class="stat-value">Daten</div></div></a>
    <a href="/profil/password" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">🔑</div><div class="stat-value">Passwort</div></div></a>
    <a href="/profil/2fa" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">{'✅' if two_fa else '🔐'}</div><div class="stat-value">2FA</div></div></a>
    <a href="/profil/export" style="text-decoration:none"><div class="stat-card"><div class="stat-icon">📥</div><div class="stat-value">Export</div></div></a>
    <a href="/profil/delete" style="text-decoration:none"><div class="stat-card" style="border-color:var(--red)"><div class="stat-icon">🗑️</div><div class="stat-value" style="color:var(--red)">Loeschen</div></div></a>
    </div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/edit", methods=["GET", "POST"])
def profil_edit():
    if "user_id" not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE benutzer SET vorname=?, nachname=?, email=? WHERE id=?",
            (request.form.get("vorname",""), request.form.get("nachname",""), request.form.get("email",""), session["user_id"]))
        conn.commit()
        conn.close()
        session["vorname"] = request.form.get("vorname","")
        msg = '<div class="alert alert-ok">✅</div>'
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT vorname, nachname, email FROM benutzer WHERE id=?", (session["user_id"],))
    u = c.fetchone()
    conn.close()
    content = f"""<h1>👤 Profil</h1>{msg}<div class="card"><form method="POST">
    <input type="text" name="vorname" value="{u[0] or ''}" required>
    <input type="text" name="nachname" value="{u[1] or ''}" required>
    <input type="email" name="email" value="{u[2] or ''}" required>
    <button type="submit" class="btn btn-success">💾</button></form></div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/password", methods=["GET", "POST"])
def profil_password():
    if "user_id" not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT passwort FROM benutzer WHERE id=?", (session["user_id"],))
        if hash_pw(request.form.get("old_password","")) == c.fetchone()[0]:
            new = request.form.get("new_password","")
            if len(new)>=8 and new==request.form.get("confirm_password",""):
                c.execute("UPDATE benutzer SET passwort=? WHERE id=?", (hash_pw(new), session["user_id"]))
                conn.commit()
                msg = '<div class="alert alert-ok">✅</div>'
        conn.close()
    content = f"""<h1>🔑 Passwort</h1>{msg}<div class="card"><form method="POST">
    <input type="password" name="old_password" placeholder="Altes Passwort" required>
    <input type="password" name="new_password" placeholder="Neues Passwort" required>
    <input type="password" name="confirm_password" placeholder="Bestaetigen" required>
    <button type="submit" class="btn btn-success">🔒</button></form></div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/2fa", methods=["GET", "POST"])
def profil_2fa():
    if "user_id" not in session: return redirect("/login")
    uid = session["user_id"]
    two_fa, current = get_2fa_status(uid)
    msg = ""
    if request.method == "POST":
        action = request.form.get("action","")
        token = request.form.get("token","")
        if action=="enable":
            secret = request.form.get("secret","")
            if verify_2fa_token(secret, token):
                enable_2fa(uid, secret)
                two_fa = True
                msg = '<div class="alert alert-ok">✅ 2FA aktiv!</div>'
        elif action=="disable":
            if verify_2fa_token(current, token):
                disable_2fa(uid)
                two_fa = False
    if two_fa:
        content = f"""<h1>🔐 2FA Aktiv</h1>{msg}<div class="card"><form method="POST">
        <input type="hidden" name="action" value="disable">
        <input type="text" name="token" placeholder="6-stelliger Code" required>
        <button type="submit" class="btn btn-danger">⚠️ Deaktivieren</button></form></div>"""
    else:
        secret = generate_2fa_secret()
        qr = generate_qr_code(session.get("username","user"), secret)
        content = f"""<h1>🔐 2FA</h1>{msg}<div class="card">
        <div style="text-align:center;background:white;padding:20px;border-radius:12px"><img src="{qr}" style="max-width:300px"></div>
        <p style="margin-top:15px;font-family:monospace">{secret}</p>
        <form method="POST"><input type="hidden" name="action" value="enable"><input type="hidden" name="secret" value="{secret}">
        <input type="text" name="token" placeholder="Code" required>
        <button type="submit" class="btn btn-success">🔐 Aktivieren</button></form></div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/profil/export")
def profil_export():
    if "user_id" not in session: return redirect("/login")
    data = export_user_data(session["user_id"])
    return Response(json_module.dumps(data, indent=2), mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=export.json"})


@app.route("/profil/delete", methods=["GET", "POST"])
def profil_delete():
    if "user_id" not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        if request.form.get("confirmation") == "LOESCHEN":
            request_account_deletion(session["user_id"])
            msg = '<div class="alert alert-ok">✅ Antrag!</div>'
    content = f"""<h1 style="color:var(--red)">🗑️ Loeschen</h1><div class="alert alert-warn">⚠️ 30 Tage!</div>{msg}
    <div class="card"><form method="POST">
    <input type="password" name="password" placeholder="Passwort" required>
    <input type="text" name="confirmation" placeholder='Tippe "LOESCHEN"' required>
    <button type="submit" class="btn btn-danger">🗑️</button></form></div>"""
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/impressum")
def impressum():
    return render_template_string(BASE_HTML, content=f'<h1>📜 Impressum</h1><div class="legal-text"><h3>§ 5 TMG</h3><p><strong>XsiKOM DIGITAL Projects</strong><br>Komi Tevi<br>Am Koenigsfloss 12<br>55252 Mainz-Kastel</p><p>E-Mail: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p></div>', user=session if "user_id" in session else None)


@app.route("/datenschutz")
def datenschutz():
    return render_template_string(BASE_HTML, content=f'<h1>🔒 Datenschutz</h1><div class="legal-text"><p>XsiKOM DIGITAL Projects<br>{CONTACT_EMAIL}</p></div>', user=session if "user_id" in session else None)


@app.route("/widerruf")
def widerruf():
    return render_template_string(BASE_HTML, content='<h1>↩️ Widerruf</h1><div class="legal-text"><p>14 Tage Widerrufsrecht.</p></div>', user=session if "user_id" in session else None)


@app.route("/haftung")
def haftung():
    return render_template_string(BASE_HTML, content='<h1>⚖️ Haftung</h1><div class="legal-text"><div class="alert alert-warn">⚠️ KI-Inhalte koennen Fehler enthalten!</div></div>', user=session if "user_id" in session else None)


@app.route("/agb")
def agb():
    return render_template_string(BASE_HTML, content='<h1>📋 AGB</h1><div class="legal-text"><p>Free: 5 Bewerbungen | Premium: 1.99€</p></div>', user=session if "user_id" in session else None)


@app.route("/password-reset", methods=["GET", "POST"])
def password_reset_request():
    msg = ""
    if request.method == "POST":
        email = request.form.get("email","").strip()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM benutzer WHERE email=?", (email,))
        u = c.fetchone()
        conn.close()
        if u:
            token = create_password_reset_token(u[0])
            link = f"{request.host_url}password-reset/{token}"
            msg = f'<div class="alert alert-ok">Link: {link}</div>'
    content = f"""<div style="max-width:450px;margin:60px auto"><div class="card"><h1>🔑 Reset</h1>{msg}
    <form method="POST"><input type="email" name="email" placeholder="E-Mail" required>
    <button type="submit" class="btn btn-primary">📧</button></form></div></div>"""
    return render_template_string(BASE_HTML, content=content, user=None)


@app.route("/password-reset/<token>", methods=["GET", "POST"])
def password_reset_new(token):
    uid = verify_reset_token(token)
    if not uid: return render_template_string(BASE_HTML, content="<h1>❌</h1>", user=None)
    if request.method == "POST":
        new = request.form.get("new_password","")
        if len(new) >= 8:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("UPDATE benutzer SET passwort=? WHERE id=?", (hash_pw(new), uid))
            conn.commit()
            conn.close()
            use_reset_token(token)
            return redirect("/login")
    content = """<div style="max-width:450px;margin:60px auto"><div class="card"><h1>Neues Passwort</h1>
    <form method="POST"><input type="password" name="new_password" required>
    <button type="submit" class="btn btn-success">✅</button></form></div></div>"""
    return render_template_string(BASE_HTML, content=content, user=None)


@app.route("/logout")
def logout():
    if "user_id" in session: audit_log(session["user_id"], "LOGOUT", "")
    session.clear()
    return redirect("/login")


@app.route("/manifest.json")
def manifest():
    return send_from_directory(".", "manifest.json", mimetype="application/json")


@app.route("/sw.js")
def service_worker():
    r = make_response(send_from_directory(".", "sw.js", mimetype="application/javascript"))
    r.headers["Service-Worker-Allowed"] = "/"
    return r


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/.well-known/assetlinks.json")
def assetlinks():
    return send_from_directory(".well-known", "assetlinks.json", mimetype="application/json")


def force_migration():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for m in ["ALTER TABLE jobs ADD COLUMN favorit INTEGER DEFAULT 0",
              "ALTER TABLE jobs ADD COLUMN entfernung INTEGER DEFAULT 0",
              "ALTER TABLE jobs ADD COLUMN bewerbung_datum TEXT",
              "ALTER TABLE jobs ADD COLUMN land TEXT DEFAULT 'DE'",
              "ALTER TABLE jobs ADD COLUMN gehalt TEXT",
              "ALTER TABLE bewerbungen ADD COLUMN typ TEXT DEFAULT 'job'"]:
        try: c.execute(m)
        except: pass
    conn.commit()
    conn.close()


db_init()
admin_anlegen()
force_migration()


if __name__ == "__main__":
    print("=" * 60)
    print("  XsiKOM v6.0 + XSI Bot")
    print(f"  KI: {'ONLINE' if GROQ_API_KEY else 'OFFLINE'}")
    print(f"  URL: http://localhost:5000")
    print("=" * 60)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)