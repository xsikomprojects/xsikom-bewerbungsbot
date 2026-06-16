"""
XsiKOM-BewerbungsBOT
Web App mit PWA Mobile Support
Komi Tevi - 2026
"""
import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import (
    Flask, render_template_string, request,
    redirect, session, send_from_directory, make_response
)


# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(hours=2)

DB_NAME = "bewerbungen.db"


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


def benutzer_anlegen(user, pw, email, vn, nn):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            INSERT INTO benutzer
            (benutzername, passwort, email, vorname, nachname, erstellt)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user, hash_pw(pw), email, vn, nn, datetime.now().isoformat()))
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
# AALIYAH KI
# ============================================================
import random

AALIYAH_TIPPS = [
    "Passe dein Anschreiben immer an die konkrete Stelle an!",
    "Erwaehne im Anschreiben konkrete Projekte der Firma.",
    "Nutze Keywords aus der Stellenanzeige.",
    "Halte dein Anschreiben auf maximal eine Seite.",
    "Zeige Motivation - warum genau diese Firma?",
    "Sende Bewerbungen am Dienstag oder Mittwoch morgens.",
    "Pruefe deine E-Mail auf Rechtschreibung vor dem Senden.",
]

AALIYAH_ANTWORTEN = {
    "hallo": "Hallo! Ich bin Aaliyah. Wie kann ich dir helfen?",
    "hilfe": "Frag mich nach: tipps, lebenslauf, anschreiben, gehalt, gespraech, netzwerk!",
    "tipps": "Hier ist ein Tipp: Passe dein Anschreiben individuell an die Stelle an!",
    "lebenslauf": "Lebenslauf-Tipps:\n1. Chronologisch (neueste zuerst)\n2. Max 2 Seiten\n3. IT-Skills hervorheben\n4. Konkrete Projekte\n5. Professionelles Layout",
    "anschreiben": "Anschreiben-Tipps:\n1. Individueller Bezug zur Stelle\n2. Konkrete Motivation\n3. Max 1 Seite\n4. Fehlerfrei!",
    "gehalt": "Gehalt-Tipps:\n- Marktwert recherchieren (Glassdoor)\n- Spanne nennen\n- Begruenden mit Qualifikation\n- Praktikum: 800-1200 EUR ueblich",
    "gespraech": "Gespraech-Tipps:\n- Selbstpraesentation ueben (2 Min)\n- Fragen vorbereiten\n- STAR-Methode\n- Koerperhaltung beachten\n- Nachfassen nach Gespraech",
    "netzwerk": "Netzwerk-Interview:\n- OSI-Modell\n- TCP vs UDP\n- VLAN\n- Routing Protokolle\n- Firewall\n- DNS/DHCP",
    "danke": "Gerne! Viel Erfolg!",
}


def aaliyah_antwort(frage):
    f = frage.lower().strip()
    for key, antwort in AALIYAH_ANTWORTEN.items():
        if key in f:
            return antwort
    return "Interessante Frage! Frag mich nach: tipps, lebenslauf, anschreiben, gehalt, gespraech, netzwerk!"


def aaliyah_tipp():
    return random.choice(AALIYAH_TIPPS)


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
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="XsiKOM Bot">
    <link rel="apple-touch-icon" href="/static/icon-192.png">
    <link rel="icon" type="image/png" href="/static/icon-192.png">

    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/sw.js');
            });
        }
        let prompt = null;
        window.addEventListener('beforeinstallprompt', function(e) {
            e.preventDefault();
            prompt = e;
            var b = document.getElementById('install-btn');
            if (b) {
                b.style.display = 'block';
                b.onclick = function() {
                    if (prompt) {
                        prompt.prompt();
                        prompt = null;
                    }
                };
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
        .logo { color: #00B4D8; font-size: 32px; font-weight: bold; }
        .subtitle { color: #2DD4A8; font-size: 14px; }
        .nav { background: #162635; padding: 10px; overflow-x: auto; white-space: nowrap; }
        .nav a { color: #E8EDF2; text-decoration: none;
                 padding: 10px 16px; margin: 0 3px;
                 border-radius: 8px; display: inline-block;
                 font-size: 14px; }
        .nav a:hover { background: #1E3A4F; }
        .card { background: #1A2F42; border-radius: 12px;
                padding: 20px; margin: 15px 0;
                border: 1px solid #2A4A65; }
        .btn { padding: 12px 24px; border: none;
               border-radius: 8px; cursor: pointer;
               font-weight: bold; text-decoration: none;
               display: inline-block; font-size: 14px; }
        .btn-primary { background: #00B4D8; color: white; }
        .btn-success { background: #2DD4A8; color: white; }
        .btn-warning { background: #FFD93D; color: black; }
        .btn-danger { background: #FF5252; color: white; }
        input, textarea { background: #0A1520;
                           border: 1px solid #2A4A65;
                           color: #E8EDF2; padding: 12px;
                           border-radius: 6px; width: 100%;
                           margin-bottom: 10px; font-size: 14px; }
        h1, h2, h3 { color: #00B4D8; margin-bottom: 15px; }
        .grid { display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px; }
        .stat { background: #1A2F42; padding: 20px;
                border-radius: 12px; text-align: center;
                border-top: 4px solid #00B4D8; }
        .footer { background: #162635; padding: 20px;
                  text-align: center; color: #5C6B7A;
                  margin-top: 40px; font-size: 13px; }
        .footer a { color: #00B4D8; margin: 0 10px; }
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
        @media (max-width: 768px) {
            .logo { font-size: 24px; }
            .nav a { padding: 8px 10px; font-size: 12px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <div class="logo">XsiKOM</div>
            <div class="subtitle">BewerbungsBOT - {{ user.vorname if user else 'Login' }}</div>
        </div>
    </div>

    {% if user %}
    <div class="nav">
        <div class="container">
            <a href="/dashboard">Dashboard</a>
            <a href="/aaliyah">Aaliyah KI</a>
            <a href="/lebenslauf">Lebenslauf</a>
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
        <a href="/impressum">Impressum</a> |
        <a href="/datenschutz">Datenschutz</a> |
        <a href="/agb">AGB</a> |
        <a href="/install">App installieren</a>
        <div style="margin-top: 10px;">
            XsiKOM-BewerbungsBOT &copy; 2026 Komi Tevi
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

    content = """
    <div style="max-width: 400px; margin: 50px auto;">
        <div class="card">
            <h1>Anmelden</h1>
            """ + msg + """
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
        dsg = request.form.get("datenschutz", "")
        agb = request.form.get("agb", "")

        if not all([user, pw, email, dsg, agb]):
            msg = '<div class="alert-err">Alle Felder + DSGVO erforderlich!</div>'
        elif len(pw) < 6:
            msg = '<div class="alert-err">Passwort min. 6 Zeichen!</div>'
        elif benutzer_anlegen(user, pw, email, vn, nn):
            return redirect("/login")
        else:
            msg = '<div class="alert-err">Benutzername vergeben!</div>'

    content = """
    <div style="max-width: 500px; margin: 30px auto;">
        <div class="card">
            <h1>Registrieren</h1>
            """ + msg + """
            <form method="POST">
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
                <p style="margin-top: 15px;">
                    <input type="checkbox" name="datenschutz" required style="width: auto;">
                    Ich akzeptiere die <a href="/datenschutz" style="color: #00B4D8;">Datenschutzerklaerung</a>
                </p>
                <p>
                    <input type="checkbox" name="agb" required style="width: auto;">
                    Ich akzeptiere die <a href="/agb" style="color: #00B4D8;">AGB</a>
                </p>
                <br>
                <button type="submit" class="btn btn-success" style="width: 100%;">Registrieren</button>
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

    content = """
    <h1>Dashboard</h1>
    <p>Willkommen, """ + session['vorname'] + """!</p>

    <div class="card">
        <h3>Dein Plan: """ + ("Premium" if session.get("premium") else "Free") + " " + badge + """</h3>
        <p>Bewerbungen diesen Monat: <strong>""" + str(bw) + " / " + str(limit) + """</strong></p>
        """ + upgrade + """
    </div>

    <h2>Schnellaktionen</h2>
    <div class="grid">
        <div class="stat">
            <h2>Aaliyah</h2>
            <p>KI Assistentin</p>
            <a href="/aaliyah" class="btn btn-primary">Chat starten</a>
        </div>
        <div class="stat">
            <h2>Lebenslauf</h2>
            <p>Profil bearbeiten</p>
            <a href="/lebenslauf" class="btn btn-primary">Bearbeiten</a>
        </div>
        <div class="stat">
            <h2>Bewerbung</h2>
            <p>Senden</p>
            <a href="/bewerbungen" class="btn btn-primary">Senden</a>
        </div>
    </div>

    <div class="card">
        <h3>Aaliyahs Tipp des Tages</h3>
        <p>""" + aaliyah_tipp() + """</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/aaliyah", methods=["GET", "POST"])
def aaliyah():
    if "user_id" not in session:
        return redirect("/login")

    antwort = ""
    if request.method == "POST":
        frage = request.form.get("frage", "")
        if frage:
            a = aaliyah_antwort(frage)
            antwort = """
            <div style="margin-top: 20px; padding: 15px;
                        background: #0A1520; border-radius: 8px;
                        border-left: 4px solid #FF69B4;">
                <strong>Aaliyah:</strong><br>""" + a.replace("\n", "<br>") + """
            </div>
            """

    content = """
    <h1>Aaliyah KI</h1>
    <div class="card">
        <h3>Chat mit deiner Bewerbungsberaterin</h3>
        <form method="POST">
            <input type="text" name="frage" placeholder="Frag Aaliyah..." required>
            <button type="submit" class="btn btn-primary">Senden</button>
        </form>
        """ + antwort + """
    </div>
    <div class="card">
        <h3>Schnellfragen</h3>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="tipps">
            <button class="btn btn-primary">Tipps</button>
        </form>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="lebenslauf">
            <button class="btn btn-primary">Lebenslauf</button>
        </form>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="anschreiben">
            <button class="btn btn-primary">Anschreiben</button>
        </form>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="gehalt">
            <button class="btn btn-primary">Gehalt</button>
        </form>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="gespraech">
            <button class="btn btn-primary">Gespraech</button>
        </form>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="netzwerk">
            <button class="btn btn-primary">Netzwerk</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


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

    content = """
    <h1>Lebenslauf</h1>
    """ + msg + """
    <form method="POST">
        <div class="card">
            <h3>Persoenliche Daten</h3>
            <p>Vorname:</p><input type="text" name="vorname" value=" """ + p.get('vorname','') + """ ">
            <p>Nachname:</p><input type="text" name="nachname" value=" """ + p.get('nachname','') + """ ">
            <p>Strasse:</p><input type="text" name="strasse" value=" """ + p.get('strasse','') + """ ">
            <p>PLZ:</p><input type="text" name="plz" value=" """ + p.get('plz','') + """ ">
            <p>Stadt:</p><input type="text" name="stadt" value=" """ + p.get('stadt','') + """ ">
            <p>Telefon:</p><input type="text" name="telefon" value=" """ + p.get('telefon','') + """ ">
            <p>E-Mail:</p><input type="email" name="email" value=" """ + p.get('email','') + """ ">
            <p>Geburtsdatum:</p><input type="text" name="geburtsdatum" value=" """ + p.get('geburtsdatum','') + """ ">
        </div>
        <div class="card">
            <h3>IT-Kenntnisse (eine pro Zeile)</h3>
            <textarea name="kenntnisse" rows="6">""" + p.get('kenntnisse','') + """</textarea>
        </div>
        <div class="card">
            <h3>Sprachen (eine pro Zeile)</h3>
            <textarea name="sprachen" rows="4">""" + p.get('sprachen','') + """</textarea>
        </div>
        <div class="card">
            <button type="submit" class="btn btn-success">Speichern</button>
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
            msg = '<div class="alert-warn">Limit erreicht! <a href="/premium" style="color: black;">Upgrade auf Premium!</a></div>'
        elif firma and email:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                "INSERT INTO bewerbungen (user_id, firma, email, datum) VALUES (?, ?, ?, ?)",
                (session["user_id"], firma, email, datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            msg = '<div class="alert-ok">Bewerbung an ' + firma + ' gespeichert!</div>'

    bw = bewerbungen_zaehlen(session["user_id"])
    limit = "unbegrenzt" if session.get("premium") else 5
    upgrade_btn = ""
    if not session.get("premium") and bw >= 5:
        upgrade_btn = '<a href="/premium" class="btn btn-warning">Upgrade fuer unbegrenzte Bewerbungen!</a>'

    content = """
    <h1>Bewerbungen</h1>
    <div class="card">
        <h3>Dein Limit</h3>
        <p>Bewerbungen: <strong>""" + str(bw) + " / " + str(limit) + """</strong> diesen Monat</p>
        """ + upgrade_btn + """
    </div>
    """ + msg + """
    <div class="card">
        <h3>Neue Bewerbung</h3>
        <form method="POST">
            <p>Firma:</p>
            <input type="text" name="firma" required>
            <p>E-Mail des Unternehmens:</p>
            <input type="email" name="email" required>
            <br>
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
                <li>Alle 8 Jobportale</li>
                <li>Premium Aaliyah KI</li>
                <li>Werbefrei</li>
            </ul>
            <a href="/checkout" class="btn btn-warning" style="width: 100%; text-align: center;">Upgrade jetzt</a>
        </div>
        <div class="card">
            <h2>Premium Jahr</h2>
            <h3>19.99 EUR / Jahr</h3>
            <p style="color: #2DD4A8;">Spare 16%!</p>
            <ul style="list-style: none; padding: 0;">
                <li>Alles aus Premium</li>
                <li>Spare 4 EUR/Jahr</li>
                <li>Prioritaets-Support</li>
            </ul>
            <a href="/checkout?plan=jahr" class="btn btn-success" style="width: 100%; text-align: center;">Jahresplan</a>
        </div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/checkout")
def checkout():
    if "user_id" not in session:
        return redirect("/login")
    plan = request.args.get("plan", "monat")
    preis = "19.99 EUR / Jahr" if plan == "jahr" else "1.99 EUR / Monat"
    content = """
    <h1>Checkout</h1>
    <div class="card">
        <h2>Premium """ + plan.title() + """</h2>
        <h3>""" + preis + """</h3>
        <div class="alert-warn">
            Demo-Modus: Echte Zahlungen kommen bald (Stripe)!
        </div>
        <br>
        <a href="/aktivieren" class="btn btn-success">Demo Premium aktivieren</a>
        <a href="/dashboard" class="btn btn-primary">Zurueck</a>
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
    <div class="alert-ok">
        <h2>Erfolgreich!</h2>
        <p>Premium ist jetzt aktiv!</p>
    </div>
    <br>
    <a href="/dashboard" class="btn btn-primary">Zum Dashboard</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/install")
def install():
    content = """
    <h1>App auf Handy installieren</h1>
    <div class="card">
        <h2>Android (Chrome)</h2>
        <ol style="padding-left: 20px;">
            <li>Oeffne diese Seite in Chrome</li>
            <li>Tippe auf Menue (3 Punkte)</li>
            <li>Waehle "App installieren"</li>
            <li>Bestaetige mit "Installieren"</li>
            <li>Fertig!</li>
        </ol>
        <br>
        <button id="install-btn" class="btn btn-success" style="display: none; width: 100%;">
            Jetzt installieren
        </button>
    </div>
    <div class="card">
        <h2>iPhone (Safari)</h2>
        <ol style="padding-left: 20px;">
            <li>Oeffne in Safari</li>
            <li>Tippe auf Teilen-Symbol</li>
            <li>"Zum Home-Bildschirm"</li>
            <li>"Hinzufuegen"</li>
        </ol>
    </div>
    <div class="card" style="background: linear-gradient(135deg, #00B4D8, #2DD4A8);">
        <h2 style="color: white;">Vorteile:</h2>
        <ul style="color: white;">
            <li>App-Icon auf Handy</li>
            <li>Offline-Modus</li>
            <li>Schneller Zugriff</li>
            <li>Wie native App</li>
        </ul>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/datenschutz")
def datenschutz():
    content = """
    <h1>Datenschutzerklaerung</h1>
    <div class="card">
        <h3>Verantwortlicher</h3>
        <p>Komi Tevi<br>Am Koenigsfloss 12<br>55252 Mainz-Kastel<br>
        E-Mail: xsikom.projects@gmail.com<br>Tel: +49 178 8977320</p>
        <h3>Datenverarbeitung</h3>
        <p>Wir speichern: Name, E-Mail, Passwort (verschluesselt), Bewerbungsdaten.</p>
        <h3>Ihre Rechte (DSGVO)</h3>
        <ul style="padding-left: 20px;">
            <li>Auskunft (Art. 15)</li>
            <li>Berichtigung (Art. 16)</li>
            <li>Loeschung (Art. 17)</li>
            <li>Datenuebertragbarkeit (Art. 20)</li>
        </ul>
        <p>Anfragen: xsikom.projects@gmail.com</p>
        <h3>Datensicherheit</h3>
        <p>SSL/TLS, SHA-256 Hashing, Session Management.</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/impressum")
def impressum():
    content = """
    <h1>Impressum</h1>
    <div class="card">
        <h3>Angaben gemaess Paragraph 5 TMG:</h3>
        <p><strong>Komi Tevi</strong><br>
        Am Koenigsfloss 12<br>
        55252 Mainz-Kastel<br>
        Deutschland</p>
        <h3>Kontakt:</h3>
        <p>Telefon: +49 178 8977320<br>
        E-Mail: xsikom.projects@gmail.com</p>
        <h3>Verantwortlich fuer den Inhalt:</h3>
        <p>Komi Tevi (Anschrift wie oben)</p>
        <h3>Haftungsausschluss:</h3>
        <p>Die Inhalte wurden mit Sorgfalt erstellt. Fuer Richtigkeit
        und Vollstaendigkeit uebernehmen wir keine Gewaehr.</p>
        <p><small>XsiKOM-BewerbungsBOT (c) 2026 - Alle Rechte vorbehalten</small></p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/agb")
def agb():
    content = """
    <h1>AGB</h1>
    <div class="card">
        <h3>Paragraph 1 Geltungsbereich</h3>
        <p>Diese AGB gelten fuer alle Nutzer des XsiKOM-BewerbungsBOT.</p>
        <h3>Paragraph 2 Leistungen</h3>
        <p><strong>Free:</strong> 5 Bewerbungen/Monat, 1 Lebenslauf, 3 Jobportale</p>
        <p><strong>Premium (1.99 EUR/Monat):</strong> Unbegrenzt, alle Features</p>
        <p><strong>Premium Jahr (19.99 EUR):</strong> Spare 16%</p>
        <h3>Paragraph 3 Widerrufsrecht</h3>
        <p>14 Tage Widerrufsrecht ab Vertragsschluss.</p>
        <h3>Paragraph 4 Kuendigung</h3>
        <p>Jederzeit kuendbar. Daten werden nach 30 Tagen geloescht.</p>
        <h3>Paragraph 5 Haftung</h3>
        <p>Keine Garantie fuer Erfolg von Bewerbungen!</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ============================================================
# PWA ROUTEN
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


# ============================================================
# INIT
# ============================================================
db_init()
admin_anlegen()


if __name__ == "__main__":
    print("")
    print("=" * 60)
    print("  XsiKOM-BewerbungsBOT Web App + PWA")
    print("=" * 60)
    print("  URL:    http://localhost:5000")
    print("  Login:  admin / XsiKOM2026!")
    print("=" * 60)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)