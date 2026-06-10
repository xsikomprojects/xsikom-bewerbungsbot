"""
XsiKOM-BewerbungsBOT - Web App mit PWA
Komi Tevi - Version 2.0
"""
from flask import (
    Flask, render_template_string, request,
    redirect, session, send_file,
    send_from_directory, make_response
)
import os
from datetime import timedelta

from user_manager import (
    user_db_erstellen, admin_erstellen,
    benutzer_pruefen, benutzer_anlegen
)
from aaliyah_ki import Aaliyah
from sicherheit import (
    passwort_staerke, RateLimiter, audit_log
)
from datenschutz import (
    datenschutz_text, impressum_text,
    agb_text, einwilligung_speichern
)
from lizenz_manager import (
    lizenz_info, kann_bewerbung_senden,
    nutzung_zaehlen, lizenz_aktivieren
)


app = Flask(__name__)
app.secret_key = os.urandom(32)
app.permanent_session_lifetime = timedelta(hours=2)

aaliyah = Aaliyah()
rl = RateLimiter()


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
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="XsiKOM Bot">
    <link rel="apple-touch-icon" href="/static/icon-192.png">
    <link rel="icon" type="image/png" sizes="192x192" href="/static/icon-192.png">
    <link rel="icon" type="image/png" sizes="512x512" href="/static/icon-512.png">

    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/sw.js')
                    .then(function(reg) { console.log('SW OK'); })
                    .catch(function(err) { console.log('SW fail'); });
            });
        }

        let installPrompt = null;
        window.addEventListener('beforeinstallprompt', function(e) {
            e.preventDefault();
            installPrompt = e;
            var btn = document.getElementById('install-btn');
            if (btn) {
                btn.style.display = 'block';
                btn.onclick = function() {
                    if (installPrompt) {
                        installPrompt.prompt();
                        installPrompt.userChoice.then(function(result) {
                            if (result.outcome === 'accepted') {
                                btn.style.display = 'none';
                            }
                            installPrompt = null;
                        });
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
        .nav { background: #162635; padding: 10px; }
        .nav a { color: #E8EDF2; text-decoration: none;
                 padding: 10px 20px; margin: 0 5px;
                 border-radius: 8px; display: inline-block; }
        .nav a:hover { background: #1E3A4F; }
        .card { background: #1A2F42; border-radius: 12px;
                padding: 20px; margin: 15px 0;
                border: 1px solid #2A4A65; }
        .btn { padding: 12px 24px; border: none;
               border-radius: 8px; cursor: pointer;
               font-weight: bold; text-decoration: none;
               display: inline-block; }
        .btn-primary { background: #00B4D8; color: white; }
        .btn-success { background: #2DD4A8; color: white; }
        .btn-warning { background: #FFD93D; color: black; }
        .btn-danger { background: #FF5252; color: white; }
        input, textarea { background: #0A1520;
                           border: 1px solid #2A4A65;
                           color: #E8EDF2; padding: 10px;
                           border-radius: 6px; width: 100%;
                           margin-bottom: 10px; }
        h1, h2, h3 { color: #00B4D8; margin-bottom: 15px; }
        .stat-grid { display: grid;
                     grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                     gap: 15px; }
        .stat-card { background: #1A2F42; padding: 20px;
                     border-radius: 12px; text-align: center;
                     border-top: 4px solid #00B4D8; }
        .footer { background: #162635; padding: 20px;
                  text-align: center; color: #5C6B7A;
                  margin-top: 40px; }
        .footer a { color: #00B4D8; margin: 0 10px; }
        .premium-badge { background: linear-gradient(135deg, #FFD93D, #FF8C42);
                         color: black; padding: 5px 10px;
                         border-radius: 20px; font-size: 12px;
                         font-weight: bold; }
        .alert-success { background: #2DD4A8; color: black; padding: 15px;
                         border-radius: 8px; margin: 10px 0; }
        .alert-error { background: #FF5252; color: white; padding: 15px;
                       border-radius: 8px; margin: 10px 0; }
        .alert-warning { background: #FFD93D; color: black; padding: 15px;
                         border-radius: 8px; margin: 10px 0; }
        @media (max-width: 768px) {
            .nav a { padding: 8px 12px; font-size: 12px; }
            .logo { font-size: 24px; }
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
        <div>
            <a href="/impressum">Impressum</a> |
            <a href="/datenschutz">Datenschutz</a> |
            <a href="/agb">AGB</a> |
            <a href="/install">App installieren</a>
        </div>
        <div style="margin-top: 10px;">
            XsiKOM-BewerbungsBOT &copy; 2026 Komi Tevi
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pw   = request.form.get("password", "").strip()
        ok, msg = rl.versuch_pruefen(user)
        if not ok:
            return render_login(msg, error=True)
        result = benutzer_pruefen(user, pw)
        if result:
            rl.reset(user)
            session["user_id"]  = result["id"]
            session["username"] = result["benutzername"]
            session["vorname"]  = result["vorname"]
            session["nachname"] = result["nachname"]
            session["rolle"]    = result["rolle"]
            audit_log("login_erfolg", user)
            return redirect("/dashboard")
        else:
            audit_log("login_fehler", user)
            return render_login("Login falsch!", error=True)
    return render_login()


def render_login(msg="", error=False):
    alert = ""
    if error and msg:
        alert = '<div class="alert-error">' + msg + '</div>'
    elif msg:
        alert = '<div class="alert-success">' + msg + '</div>'

    content = """
    <div style="max-width: 400px; margin: 50px auto;">
        <div class="card">
            <h1>Anmelden</h1>
            """ + alert + """
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
    if request.method == "POST":
        user  = request.form.get("username", "").strip()
        pw    = request.form.get("password", "").strip()
        email = request.form.get("email", "").strip()
        vn    = request.form.get("vorname", "").strip()
        nn    = request.form.get("nachname", "").strip()
        dsg   = request.form.get("datenschutz", "")
        agb_ok = request.form.get("agb", "")

        if not all([user, pw, email, dsg, agb_ok]):
            return render_register("Alle Felder + DSGVO/AGB erforderlich!")

        staerke = passwort_staerke(pw)
        if staerke["score"] < 3:
            return render_register("Passwort zu schwach: " + ", ".join(staerke["feedback"]))

        if benutzer_anlegen(user, pw, email, vn, nn):
            einwilligung_speichern(user, agb=True, datenschutz=True)
            audit_log("registrierung", user)
            return redirect("/login")
        else:
            return render_register("Benutzername bereits vergeben!")
    return render_register()


def render_register(msg=""):
    alert = ""
    if msg:
        alert = '<div class="alert-error">' + msg + '</div>'

    content = """
    <div style="max-width: 500px; margin: 30px auto;">
        <div class="card">
            <h1>Registrieren</h1>
            """ + alert + """
            <form method="POST">
                <p>Benutzername:</p>
                <input type="text" name="username" required>
                <p>Passwort (min. 8 Zeichen):</p>
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
    lizenz = lizenz_info(session["user_id"])
    badge = '<span class="premium-badge">PREMIUM</span>' if lizenz["typ"] != "free" else ""
    upgrade = ""
    if lizenz["typ"] == "free":
        upgrade = '<a href="/premium" class="btn btn-warning">Upgrade auf Premium - 1.99 EUR/Monat</a>'

    content = """
    <h1>Dashboard</h1>
    <p>Willkommen, """ + session['vorname'] + """!</p>

    <div class="card">
        <h3>Dein Plan: """ + lizenz['name'] + " " + badge + """</h3>
        <p>Bewerbungen diesen Monat: <strong>""" + lizenz['bewerbungen'] + """</strong></p>
        """ + upgrade + """
    </div>

    <h2>Schnellaktionen</h2>
    <div class="stat-grid">
        <div class="stat-card">
            <h2>Aaliyah</h2>
            <p>KI Assistentin</p>
            <a href="/aaliyah" class="btn btn-primary">Chat starten</a>
        </div>
        <div class="stat-card">
            <h2>Lebenslauf</h2>
            <p>Profil bearbeiten</p>
            <a href="/lebenslauf" class="btn btn-primary">Bearbeiten</a>
        </div>
        <div class="stat-card">
            <h2>Bewerbung</h2>
            <p>Senden</p>
            <a href="/bewerbungen" class="btn btn-primary">Senden</a>
        </div>
    </div>

    <div class="card">
        <h3>Aaliyahs Tipp des Tages</h3>
        <p>""" + aaliyah.zufalls_tipp() + """</p>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/aaliyah", methods=["GET", "POST"])
def aaliyah_chat():
    if "user_id" not in session:
        return redirect("/login")
    antwort_html = ""
    if request.method == "POST":
        frage = request.form.get("frage", "")
        if frage:
            antwort = aaliyah.antwort(frage)
            antwort_text = antwort.replace("\n", "<br>")
            antwort_html = """
            <div style="margin-top: 20px; padding: 15px;
                        background: #0A1520; border-radius: 8px;
                        border-left: 4px solid #FF69B4;">
                <strong>Aaliyah:</strong><br>""" + antwort_text + """
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
        """ + antwort_html + """
    </div>
    <div class="card">
        <h3>Schnellfragen</h3>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="tipps bewerbung">
            <button type="submit" class="btn btn-primary">tipps bewerbung</button>
        </form>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="lebenslauf">
            <button type="submit" class="btn btn-primary">lebenslauf</button>
        </form>
        <form method="POST" style="display: inline;">
            <input type="hidden" name="frage" value="gehalt">
            <button type="submit" class="btn btn-primary">gehalt</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/lebenslauf", methods=["GET", "POST"])
def lebenslauf():
    if "user_id" not in session:
        return redirect("/login")
    from lebenslauf_editor import (
        standard_profil, benutzer_daten_laden,
        benutzer_daten_speichern, lebenslauf_aus_profil
    )
    profil = benutzer_daten_laden(session["username"]) or standard_profil()
    msg = ""
    if request.method == "POST":
        aktion = request.form.get("aktion", "")
        if aktion == "speichern":
            for key in ["vorname","nachname","strasse","plz","stadt","telefon","email","geburtsdatum"]:
                profil[key] = request.form.get(key, "").strip()
            profil["kenntnisse"] = [z.strip() for z in request.form.get("kenntnisse","").split("\n") if z.strip()]
            profil["sprachen"]   = [z.strip() for z in request.form.get("sprachen","").split("\n") if z.strip()]
            profil["berufserfahrung"] = []
            profil["zertifikate"]     = []
            benutzer_daten_speichern(session["username"], profil)
            msg = "Profil gespeichert!"
        elif aktion == "pdf":
            benutzer_daten_speichern(session["username"], profil)
            pfad = lebenslauf_aus_profil(profil)
            return send_file(pfad, as_attachment=True)
    alert = '<div class="alert-success">' + msg + '</div>' if msg else ''
    kenntnisse_text = "\n".join(profil.get("kenntnisse", []))
    sprachen_text   = "\n".join(profil.get("sprachen", []))
    content = """
    <h1>Lebenslauf</h1>
    """ + alert + """
    <form method="POST">
        <div class="card">
            <h3>Persoenliche Daten</h3>
            <p>Vorname:</p><input type="text" name="vorname" value=" """ + profil.get('vorname','') + """ ">
            <p>Nachname:</p><input type="text" name="nachname" value=" """ + profil.get('nachname','') + """ ">
            <p>Strasse:</p><input type="text" name="strasse" value=" """ + profil.get('strasse','') + """ ">
            <p>PLZ:</p><input type="text" name="plz" value=" """ + profil.get('plz','') + """ ">
            <p>Stadt:</p><input type="text" name="stadt" value=" """ + profil.get('stadt','') + """ ">
            <p>Telefon:</p><input type="text" name="telefon" value=" """ + profil.get('telefon','') + """ ">
            <p>E-Mail:</p><input type="email" name="email" value=" """ + profil.get('email','') + """ ">
            <p>Geburtsdatum:</p><input type="text" name="geburtsdatum" value=" """ + profil.get('geburtsdatum','') + """ ">
        </div>
        <div class="card">
            <h3>IT-Kenntnisse (eine pro Zeile)</h3>
            <textarea name="kenntnisse" rows="6">""" + kenntnisse_text + """</textarea>
        </div>
        <div class="card">
            <h3>Sprachen (eine pro Zeile)</h3>
            <textarea name="sprachen" rows="4">""" + sprachen_text + """</textarea>
        </div>
        <div class="card">
            <button type="submit" name="aktion" value="speichern" class="btn btn-success">Speichern</button>
            <button type="submit" name="aktion" value="pdf" class="btn btn-primary">PDF herunterladen</button>
        </div>
    </form>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/bewerbungen", methods=["GET", "POST"])
def bewerbungen():
    if "user_id" not in session:
        return redirect("/login")
    msg = ""
    alert_class = "alert-success"
    if request.method == "POST":
        firma = request.form.get("firma","").strip()
        email = request.form.get("email","").strip()
        ok, aktuell, limit = kann_bewerbung_senden(session["user_id"])
        if not ok:
            msg = "Limit erreicht: " + str(aktuell) + "/" + str(limit) + ". Upgrade auf Premium!"
            alert_class = "alert-warning"
        else:
            try:
                from anschreiben_generator import anschreiben_erstellen
                from email_sender import bewerbung_senden as send_app
                pfad = anschreiben_erstellen(firma=firma, bereich="allgemein")
                result = send_app(empfaenger=email, firma=firma,
                                   position="IT-Fachtechniker / Netzwerktechniker",
                                   anschreiben_pfad=pfad, trockenlauf=True)
                if result:
                    nutzung_zaehlen(session["user_id"], "bewerbung")
                    msg = "Bewerbung an " + firma + " vorbereitet!"
                else:
                    msg = "Fehler!"
                    alert_class = "alert-error"
            except Exception as e:
                msg = "Fehler: " + str(e)
                alert_class = "alert-error"
    ok, aktuell, limit = kann_bewerbung_senden(session["user_id"])
    alert = '<div class="' + alert_class + '">' + msg + '</div>' if msg else ''
    upgrade_btn = '<a href="/premium" class="btn btn-warning">Upgrade fuer unbegrenzte Bewerbungen!</a>' if aktuell >= limit else ''
    content = """
    <h1>Bewerbungen senden</h1>
    <div class="card">
        <h3>Dein Limit</h3>
        <p>Bewerbungen: <strong>""" + str(aktuell) + " / " + str(limit) + """</strong> diesen Monat</p>
        """ + upgrade_btn + """
    </div>
    """ + alert + """
    <div class="card">
        <h3>Einzelne Bewerbung (Trockenlauf)</h3>
        <form method="POST">
            <p>Firma:</p><input type="text" name="firma" required>
            <p>E-Mail des Unternehmens:</p><input type="email" name="email" required>
            <br>
            <button type="submit" class="btn btn-success">Bewerbung vorbereiten</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/premium")
def premium():
    content = """
    <h1>Premium Upgrade</h1>
    <div class="stat-grid">
        <div class="card">
            <h2>Free</h2><h3>0.00 EUR / Monat</h3>
            <ul style="list-style: none; padding: 0;">
                <li>5 Bewerbungen/Monat</li>
                <li>1 Lebenslauf-Vorlage</li>
                <li>3 Jobportale</li>
                <li>10 Staedte</li>
            </ul>
            <button class="btn btn-primary" style="width: 100%;">Aktuell</button>
        </div>
        <div class="card" style="border: 3px solid #FFD93D;">
            <span class="premium-badge">BELIEBT</span>
            <h2 style="margin-top: 10px;">Premium</h2><h3>1.99 EUR / Monat</h3>
            <ul style="list-style: none; padding: 0;">
                <li>UNBEGRENZTE Bewerbungen</li>
                <li>10 Lebenslauf-Vorlagen</li>
                <li>ALLE 8 Jobportale</li>
                <li>30 Staedte</li>
                <li>Premium Aaliyah KI</li>
                <li>Werbefrei</li>
            </ul>
            <a href="/checkout" class="btn btn-warning" style="width: 100%; text-align: center;">Upgrade jetzt</a>
        </div>
        <div class="card">
            <h2>Premium Jahr</h2><h3>19.99 EUR / Jahr</h3>
            <p style="color: #2DD4A8;">(spare 16%)</p>
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
        <h3>Preis: """ + preis + """</h3>
        <div class="alert-warning">
            <strong>Demo-Modus:</strong> Echte Zahlungen kommen bald!
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
    lizenz_aktivieren(session["user_id"], "premium", monate=1)
    content = """
    <h1>Premium aktiviert!</h1>
    <div class="alert-success">
        <h2>Erfolgreich!</h2>
        <p>Dein Premium ist 30 Tage aktiv!</p>
    </div>
    <br><a href="/dashboard" class="btn btn-primary">Zum Dashboard</a>
    """
    return render_template_string(BASE_HTML, content=content, user=session)


@app.route("/install")
def install_seite():
    content = """
    <h1>App auf Handy installieren</h1>

    <div class="card">
        <h2>Android (Chrome)</h2>
        <ol style="text-align: left; padding-left: 20px; color: #E8EDF2;">
            <li>Oeffne diese Seite in Chrome</li>
            <li>Tippe auf das Menue (3 Punkte) oben rechts</li>
            <li>Waehle "Zum Startbildschirm hinzufuegen"</li>
            <li>Bestaetige mit "Hinzufuegen"</li>
            <li>Fertig! XsiKOM Icon ist auf deinem Handy!</li>
        </ol>
        <br>
        <button id="install-btn" class="btn btn-success" style="display: none; width: 100%;">
            Jetzt installieren
        </button>
    </div>

    <div class="card">
        <h2>iPhone (Safari)</h2>
        <ol style="text-align: left; padding-left: 20px; color: #E8EDF2;">
            <li>Oeffne diese Seite in Safari</li>
            <li>Tippe auf das Teilen-Symbol</li>
            <li>Scrolle und tippe "Zum Home-Bildschirm"</li>
            <li>Bestaetige mit "Hinzufuegen"</li>
            <li>Fertig!</li>
        </ol>
    </div>

    <div class="card" style="background: linear-gradient(135deg, #00B4D8, #2DD4A8);">
        <h2 style="color: white;">Vorteile:</h2>
        <ul style="color: white; text-align: left;">
            <li>App-Icon auf deinem Geraet</li>
            <li>Offline-Modus</li>
            <li>Schneller Zugriff</li>
            <li>Wie native App</li>
        </ul>
    </div>
    """
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/datenschutz")
def datenschutz():
    content = "<h1>Datenschutz</h1><div class='card'><pre style='white-space: pre-wrap;'>" + datenschutz_text() + "</pre></div>"
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/impressum")
def impressum():
    content = "<h1>Impressum</h1><div class='card'><pre style='white-space: pre-wrap;'>" + impressum_text() + "</pre></div>"
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/agb")
def agb_seite():
    content = "<h1>AGB</h1><div class='card'><pre style='white-space: pre-wrap;'>" + agb_text() + "</pre></div>"
    return render_template_string(BASE_HTML, content=content, user=session if "user_id" in session else None)


@app.route("/logout")
def logout():
    audit_log("logout", session.get("username", "?"))
    session.clear()
    return redirect("/login")


@app.route("/manifest.json")
def manifest():
    return send_from_directory(".", "manifest.json", mimetype="application/json")


@app.route("/sw.js")
def service_worker():
    response = make_response(send_from_directory(".", "sw.js", mimetype="application/javascript"))
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


user_db_erstellen()
admin_erstellen()


if __name__ == "__main__":
    print("")
    print("=" * 60)
    print("  XsiKOM-BewerbungsBOT Web App + PWA")
    print("=" * 60)
    print("  URL:    http://localhost:5000")
    print("  Install: http://localhost:5000/install")
    print("  Login:  admin / XsiKOM2026!")
    print("=" * 60)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)