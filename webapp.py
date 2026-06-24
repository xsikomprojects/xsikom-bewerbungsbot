"""
XsiKOM-BewerbungsBOT v7.0 FINAL
Aaliyah + AVINU + XSI Bot
"""
import os, sqlite3, hashlib, secrets, random, requests
import json as json_module
import stripe
from datetime import datetime, timedelta
from flask import (Flask, render_template_string, request, redirect,
    session, send_from_directory, send_file, make_response, Response)
from werkzeug.utils import secure_filename
from PIL import Image
from security import (generate_2fa_secret, generate_qr_code, verify_2fa_token,
    get_2fa_status, enable_2fa, disable_2fa, create_password_reset_token,
    verify_reset_token, use_reset_token, request_account_deletion,
    cancel_deletion, get_deletion_status, export_user_data, audit_log)
from avinu_ki import (avinu_antwort, alle_jobs_suchen, get_alle_berufe,
    jobs_speichern, jobs_laden, vorlagen_laden, anschreiben_generieren,
    auto_bewerbung_erstellen, job_favorit_toggle, job_loeschen, BRANCHEN)
from xsi_bot import (xsi_anschreiben_komplett, xsi_betreff_erstellen,
    xsi_email_senden, xsi_bewerbung_speichern, xsi_bewerbung_status_update,
    xsi_bewerbungen_laden, xsi_templates_laden, xsi_statistiken,
    xsi_unterlagen_pruefen)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(hours=2)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE = os.environ.get("STRIPE_PRICE_MONAT", "")

DB = "bewerbungen.db"
UF = "uploads"
AE = {"pdf","png","jpg","jpeg","gif","bmp","webp"}
CE = "xsikom_digital@xsikom.de"
GK = os.environ.get("GROQ_API_KEY", "")
GU = "https://api.groq.com/openai/v1/chat/completions"
os.makedirs(UF, exist_ok=True)


def ki(frage):
    if not GK: return "KI offline."
    try:
        r = requests.post(GU, headers={"Authorization": f"Bearer {GK}",
            "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                "messages": [{"role":"system","content":"Du bist Aaliyah, KI-Karriereberaterin. Deutsch."},
                    {"role":"user","content":frage}],
                "temperature":0.7,"max_tokens":500}, timeout=15)
        return r.json()["choices"][0]["message"]["content"] if r.status_code==200 else "Fehler."
    except: return "Verbindung fehlgeschlagen."


def tipp():
    return random.choice(["Anschreiben individuell anpassen!","Konkrete Projekte erwaehnen.",
        "Max. 1 Seite.","Motivation zeigen!","Rechtschreibung pruefen."])


def dbi():
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS benutzer (id INTEGER PRIMARY KEY AUTOINCREMENT,benutzername TEXT UNIQUE NOT NULL,passwort TEXT NOT NULL,email TEXT,vorname TEXT,nachname TEXT,rolle TEXT DEFAULT 'user',premium INTEGER DEFAULT 0,kunde_typ TEXT DEFAULT 'privat',erstellt TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS bewerbungen (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,firma TEXT,email TEXT,status TEXT DEFAULT 'gesendet',datum TEXT,typ TEXT DEFAULT 'job')")
    c.execute("CREATE TABLE IF NOT EXISTS profile (user_id INTEGER PRIMARY KEY,vorname TEXT,nachname TEXT,strasse TEXT,plz TEXT,stadt TEXT,telefon TEXT,email TEXT,geburtsdatum TEXT,kenntnisse TEXT,sprachen TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS uploads (id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,dateiname TEXT,typ TEXT,kategorie TEXT,pfad TEXT,upload_datum TEXT)")
    for m in ["ALTER TABLE bewerbungen ADD COLUMN typ TEXT DEFAULT 'job'",
              "ALTER TABLE jobs ADD COLUMN favorit INTEGER DEFAULT 0",
              "ALTER TABLE jobs ADD COLUMN entfernung INTEGER DEFAULT 0",
              "ALTER TABLE jobs ADD COLUMN bewerbung_datum TEXT",
              "ALTER TABLE jobs ADD COLUMN land TEXT DEFAULT 'DE'",
              "ALTER TABLE jobs ADD COLUMN gehalt TEXT"]:
        try: c.execute(m)
        except: pass
    cn.commit()
    cn.close()


def hp(pw): return hashlib.sha256(pw.encode()).hexdigest()


def aa():
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT id FROM benutzer WHERE benutzername='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO benutzer (benutzername,passwort,email,vorname,nachname,rolle,premium,erstellt) VALUES (?,?,?,?,?,?,?,?)",
            ("admin",hp("XsiKOM2026!"),CE,"Komi","Tevi","admin",1,datetime.now().isoformat()))
        cn.commit()
    cn.close()


def bp(u,p):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT id,benutzername,vorname,nachname,rolle,premium FROM benutzer WHERE benutzername=? AND passwort=?",(u,hp(p)))
    r = c.fetchone()
    cn.close()
    return {"id":r[0],"benutzername":r[1],"vorname":r[2],"nachname":r[3],"rolle":r[4],"premium":r[5]} if r else None


def ba(u,p,e,v,n,k="privat"):
    try:
        cn = sqlite3.connect(DB)
        c = cn.cursor()
        c.execute("INSERT INTO benutzer (benutzername,passwort,email,vorname,nachname,kunde_typ,erstellt) VALUES (?,?,?,?,?,?,?)",
            (u,hp(p),e,v,n,k,datetime.now().isoformat()))
        cn.commit()
        cn.close()
        return True
    except: return False


def pa(uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("UPDATE benutzer SET premium=1 WHERE id=?",(uid,))
    cn.commit()
    cn.close()


def bz(uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT COUNT(*) FROM bewerbungen WHERE user_id=? AND datum>=?",(uid,datetime.now().replace(day=1).isoformat()))
    n = c.fetchone()[0]
    cn.close()
    return n


def pl(uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT * FROM profile WHERE user_id=?",(uid,))
    r = c.fetchone()
    cn.close()
    if not r: return {}
    return {"vorname":r[1] or "","nachname":r[2] or "","strasse":r[3] or "","plz":r[4] or "",
        "stadt":r[5] or "","telefon":r[6] or "","email":r[7] or "","geburtsdatum":r[8] or "",
        "kenntnisse":r[9] or "","sprachen":r[10] or ""}


def ps(uid,d):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("DELETE FROM profile WHERE user_id=?",(uid,))
    c.execute("INSERT INTO profile (user_id,vorname,nachname,strasse,plz,stadt,telefon,email,geburtsdatum,kenntnisse,sprachen) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (uid,d.get("vorname",""),d.get("nachname",""),d.get("strasse",""),d.get("plz",""),
         d.get("stadt",""),d.get("telefon",""),d.get("email",""),d.get("geburtsdatum",""),
         d.get("kenntnisse",""),d.get("sprachen","")))
    cn.commit()
    cn.close()


def af(f): return "." in f and f.rsplit(".",1)[1].lower() in AE


def ds(file,uid,kat):
    if not file or not af(file.filename): return None
    uf = os.path.join(UF,str(uid))
    os.makedirs(uf, exist_ok=True)
    fn = secure_filename(file.filename)
    _,ext = os.path.splitext(fn)
    ext = ext.lower()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nn = f"{kat}_{ts}{ext}"
    pfad = os.path.join(uf,nn)
    if ext in [".png",".gif",".bmp",".webp"] and kat=="bild":
        try:
            img = Image.open(file.stream)
            if img.mode in ("RGBA","P"): img = img.convert("RGB")
            nn = f"{kat}_{ts}.jpg"
            pfad = os.path.join(uf,nn)
            img.save(pfad,"JPEG",quality=90)
        except:
            file.seek(0)
            file.save(pfad)
    else:
        file.save(pfad)
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("INSERT INTO uploads (user_id,dateiname,typ,kategorie,pfad,upload_datum) VALUES (?,?,?,?,?,?)",
        (uid,nn,ext,kat,pfad,datetime.now().isoformat()))
    cn.commit()
    cn.close()
    return nn


def ul(uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT id,dateiname,typ,kategorie,pfad,upload_datum FROM uploads WHERE user_id=? ORDER BY id DESC",(uid,))
    rows = c.fetchall()
    cn.close()
    return rows


def udel(uid2,uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT pfad FROM uploads WHERE id=? AND user_id=?",(uid2,uid))
    r = c.fetchone()
    if r and os.path.exists(r[0]):
        try: os.remove(r[0])
        except: pass
    c.execute("DELETE FROM uploads WHERE id=? AND user_id=?",(uid2,uid))
    cn.commit()
    cn.close()


H = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>XsiKOM</title>
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#00D9FF">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<script>
if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js')});}
function cookieAccept(){localStorage.setItem('c','1');document.getElementById('cb').style.display='none';}
window.addEventListener('load',function(){if(localStorage.getItem('c')!=='1'){var b=document.getElementById('cb');if(b)b.style.display='block';}});
</script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0A0E1A;--cd:rgba(20,28,48,0.6);--bd:rgba(255,255,255,0.08);--cy:#00D9FF;--pu:#8B5CF6;--gn:#10F4B1;--yl:#FFD93D;--rd:#FF4757;--t1:#FFF;--t2:#A0AEC0;--t3:#6B7280}
body{font-family:'Poppins',sans-serif;background:var(--bg);color:var(--t1);min-height:100vh}
body::before{content:'';position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(circle at 20% 20%,rgba(0,217,255,0.15) 0%,transparent 50%),radial-gradient(circle at 80% 80%,rgba(139,92,246,0.15) 0%,transparent 50%);z-index:-1}
.ct{max-width:1200px;margin:0 auto;padding:20px}
.hd{background:rgba(10,14,26,0.8);backdrop-filter:blur(20px);padding:20px 0;border-bottom:1px solid var(--bd);position:sticky;top:0;z-index:100}
.hi{display:flex;justify-content:space-between;align-items:center}
.lg{font-family:'Space Grotesk',sans-serif;font-size:32px;font-weight:700;background:linear-gradient(135deg,var(--cy),var(--pu));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.st{color:var(--t2);font-size:13px}
.nv{background:rgba(19,24,41,0.5);padding:12px 0;border-bottom:1px solid var(--bd);overflow-x:auto;white-space:nowrap}
.ni{max-width:1200px;margin:0 auto;padding:0 20px;display:flex;gap:5px}
.nv a{color:var(--t2);text-decoration:none;padding:10px 18px;border-radius:12px;font-size:13px;transition:all 0.3s;text-shadow:0 1px 2px rgba(0,0,0,0.3);letter-spacing:0.3px;font-weight:500;position:relative}
.nv a:hover{color:var(--t1);background:rgba(0,217,255,0.15);transform:translateY(-2px);box-shadow:0 4px 15px rgba(0,217,255,0.2);text-shadow:0 0 10px rgba(0,217,255,0.5)}
.nv a:active{transform:translateY(1px);box-shadow:0 1px 5px rgba(0,0,0,0.3)}
.cd{background:var(--cd);backdrop-filter:blur(20px);border-radius:20px;padding:30px;margin:20px 0;border:1px solid var(--bd);transition:all 0.4s}
.cd:hover{transform:translateY(-5px);border-color:rgba(0,217,255,0.3)}
.bt{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:14px 28px;border:none;border-radius:12px;cursor:pointer;font-weight:600;font-size:14px;text-decoration:none;transition:all 0.3s;font-family:'Poppins',sans-serif}
.bt:hover{transform:translateY(-2px)}
.b1{background:linear-gradient(135deg,var(--cy),#0099CC);color:white}
.b2{background:linear-gradient(135deg,var(--gn),#059669);color:white}
.b3{background:linear-gradient(135deg,var(--yl),#F59E0B);color:#0A0E1A}
.b4{background:linear-gradient(135deg,var(--rd),#DC2626);color:white}
.b5{background:linear-gradient(135deg,var(--pu),#6D28D9);color:white}
input,textarea,select{background:rgba(10,14,26,0.6);border:1px solid var(--bd);color:var(--t1);padding:14px 18px;border-radius:12px;width:100%;margin-bottom:12px;font-size:14px;font-family:'Poppins',sans-serif}
input:focus,textarea:focus,select:focus{outline:none;border-color:var(--cy);box-shadow:0 0 0 4px rgba(0,217,255,0.1)}
h1{font-family:'Space Grotesk',sans-serif;font-size:36px;font-weight:700;background:linear-gradient(135deg,var(--cy),var(--pu));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:20px}
h2{font-size:26px;font-weight:600;margin-bottom:16px}
h3{font-size:18px;font-weight:600;color:var(--cy);margin-bottom:12px}
p{line-height:1.7;color:var(--t2);margin-bottom:8px}
a{color:var(--cy);text-decoration:none}
.gr{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}
.sc{background:linear-gradient(135deg,rgba(20,28,48,0.8),rgba(30,38,58,0.6));border:1px solid var(--bd);border-radius:20px;padding:30px;text-align:center;transition:all 0.4s;cursor:pointer}
.sc:hover{transform:translateY(-8px);border-color:var(--cy)}
.si{font-size:48px;margin-bottom:12px}
.sv{font-family:'Space Grotesk',sans-serif;font-size:32px;font-weight:700;background:linear-gradient(135deg,var(--cy),var(--pu));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.sl{color:var(--t2);font-size:13px;margin-top:4px}
.bg{background:linear-gradient(135deg,var(--yl),#EC4899);color:var(--bg);padding:6px 14px;border-radius:20px;font-size:11px;font-weight:700;display:inline-block}
.al{padding:16px 20px;border-radius:12px;margin:16px 0;border:1px solid}
.ao{background:rgba(16,244,177,0.1);border-color:rgba(16,244,177,0.3);color:var(--gn)}
.ae{background:rgba(255,71,87,0.1);border-color:rgba(255,71,87,0.3);color:var(--rd)}
.aw{background:rgba(255,217,61,0.1);border-color:rgba(255,217,61,0.3);color:var(--yl)}
.ai{background:rgba(0,217,255,0.1);border-color:rgba(0,217,255,0.3);color:var(--cy)}
.ui{background:rgba(10,14,26,0.6);padding:16px;border-radius:12px;margin:10px 0;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--bd)}
.ft{background:rgba(10,14,26,0.9);padding:40px 20px 30px;text-align:center;color:var(--t3);margin-top:60px;border-top:1px solid var(--bd)}
.ft a{color:var(--t2);margin:0 12px}
.fb{margin-top:16px;font-family:'Space Grotesk',sans-serif;font-weight:600;color:var(--cy)}
#cb{display:none;position:fixed;bottom:20px;left:20px;right:20px;max-width:1160px;margin:0 auto;background:rgba(20,28,48,0.95);color:white;padding:20px 25px;z-index:9999;border-radius:16px;border:1px solid var(--cy)}
.lt{background:var(--cd);padding:30px;border-radius:20px;margin:20px 0;line-height:1.8;border:1px solid var(--bd)}
.lt h3{color:var(--cy);margin-top:24px}
@media(max-width:768px){h1{font-size:28px}.lg{font-size:24px}}
</style>
</head>
<body>
<div id="cb"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px">
<div>🍪 Cookies. <a href="/datenschutz" style="color:var(--cy)">Mehr</a></div>
<button onclick="cookieAccept()" class="bt b2">✓</button></div></div>
<div class="hd"><div class="ct hi"><div><div class="lg">XsiKOM</div>
<div class="st">{{ user.vorname if user else 'KI Bewerbungs-Assistent' }}</div></div></div></div>
{% if user %}
<div class="nv"><div class="ni">
<a href="/dashboard">🏠 Dashboard</a>
<a href="/aaliyah">🤖 Aaliyah</a>
<a href="/avinu">⚡ AVINU</a>
<a href="/xsi">🤖 XSI Bot</a>
<a href="/lebenslauf">📝 Lebenslauf</a>
<a href="/uploads">📂 Dateien</a>
<a href="/bewerbungen">📧 Bewerbungen</a>
<a href="/premium">💎 Premium</a>
<a href="/tutorial">📚 Tutorial</a>
<a href="/updates">🔄 Updates</a>
<a href="/profil">⚙️ Profil</a>
<a href="/logout">🚪 Logout</a>
</div></div>
{% endif %}
<div class="ct">{{ content|safe }}</div>
<div class="ft">
<div><a href="/impressum">Impressum</a>•<a href="/datenschutz">Datenschutz</a>•<a href="/agb">AGB</a>•<a href="/widerruf">Widerruf</a>•<a href="/haftung">Haftung</a></div>
<div class="fb">XsiKOM-BewerbungsBOT</div>
<div style="margin-top:8px;font-size:11px;color:var(--t3)">© 2026 XsiKOM DIGITAL Projects<br>
<a href="mailto:xsikom_digital@xsikom.de" style="color:var(--t3)">xsikom_digital@xsikom.de</a></div>
</div></body></html>"""


@app.route("/")
def index():
    return redirect("/dashboard") if "user_id" in session else redirect("/login")


@app.route("/login", methods=["GET","POST"])
def login():
    msg = ""
    if request.method == "POST":
        r = bp(request.form.get("username","").strip(), request.form.get("password","").strip())
        if r:
            session["user_id"]=r["id"]; session["username"]=r["benutzername"]
            session["vorname"]=r["vorname"]; session["nachname"]=r["nachname"]
            session["rolle"]=r["rolle"]; session["premium"]=r["premium"]
            return redirect("/dashboard")
        msg = '<div class="al ae">❌ Login falsch!</div>'
    c = f'<div style="max-width:450px;margin:60px auto"><div class="cd"><h1 style="text-align:center">🔐 Anmelden</h1>{msg}<form method="POST"><input type="text" name="username" value="admin" placeholder="Benutzername" required><input type="password" name="password" placeholder="Passwort" required><button type="submit" class="bt b1" style="width:100%">🚀 Anmelden</button></form><p style="text-align:center;margin-top:25px"><a href="/register">✨ Neuen Account</a></p></div></div>'
    return render_template_string(H, content=c, user=None)


@app.route("/register", methods=["GET","POST"])
def register():
    msg = ""
    if request.method == "POST":
        u=request.form.get("username","").strip(); p=request.form.get("password","").strip()
        e=request.form.get("email","").strip()
        if not all([u,p,e,request.form.get("datenschutz"),request.form.get("agb"),request.form.get("widerruf")]):
            msg='<div class="al ae">❌ Alle Felder!</div>'
        elif len(p)<6: msg='<div class="al ae">❌ Min. 6 Zeichen!</div>'
        elif ba(u,p,e,request.form.get("vorname",""),request.form.get("nachname",""),request.form.get("kunde_typ","privat")):
            return redirect("/login")
        else: msg='<div class="al ae">❌ Name vergeben!</div>'
    c = f'<div style="max-width:600px;margin:30px auto"><div class="cd"><h1>✨ Registrieren</h1>{msg}<form method="POST"><select name="kunde_typ" required><option value="privat">👤 Privat</option><option value="firma">🏢 Firma</option></select><input type="text" name="username" placeholder="Benutzername" required><input type="password" name="password" placeholder="Passwort" required><input type="email" name="email" placeholder="E-Mail" required><input type="text" name="vorname" placeholder="Vorname"><input type="text" name="nachname" placeholder="Nachname"><div style="margin-top:20px;padding:20px;background:rgba(10,14,26,0.5);border-radius:12px"><p><input type="checkbox" name="datenschutz" required style="width:auto"> <a href="/datenschutz" target="_blank">Datenschutz</a></p><p><input type="checkbox" name="agb" required style="width:auto"> <a href="/agb" target="_blank">AGB</a></p><p><input type="checkbox" name="widerruf" required style="width:auto"> <a href="/widerruf" target="_blank">Widerruf</a></p></div><button type="submit" class="bt b2" style="width:100%">🚀 Account erstellen</button></form><p style="text-align:center;margin-top:20px"><a href="/login">← Login</a></p></div></div>'
    return render_template_string(H, content=c, user=None)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect("/login")
    bw=bz(session["user_id"]); lm="∞" if session.get("premium") else "5"
    bd='<span class="bg">⭐ PREMIUM</span>' if session.get("premium") else ""
    up='<a href="/premium" class="bt b3">💎 Upgrade</a>' if not session.get("premium") else ""
    c = f'<h1>👋 Hallo, {session.get("vorname","")}!</h1><div class="cd"><h3>📊 Plan: {"Premium" if session.get("premium") else "Free"} {bd}</h3><p>Bewerbungen: <strong>{bw} / {lm}</strong></p>{up}</div><h2 style="margin-top:40px">⚡ Schnellaktionen</h2><div class="gr"><a href="/aaliyah" style="text-decoration:none"><div class="sc"><div class="si">🤖</div><div class="sv">Aaliyah</div><div class="sl">KI Chat</div></div></a><a href="/avinu" style="text-decoration:none"><div class="sc"><div class="si">⚡</div><div class="sv">AVINU</div><div class="sl">Global Jobs</div></div></a><a href="/xsi" style="text-decoration:none"><div class="sc"><div class="si">🤖</div><div class="sv">XSI</div><div class="sl">Auto-Bewerber</div></div></a><a href="/lebenslauf" style="text-decoration:none"><div class="sc"><div class="si">📝</div><div class="sv">Lebenslauf</div><div class="sl">Bearbeiten</div></div></a></div><div class="cd" style="margin-top:30px"><h3>💡 Tipp</h3><p>{tipp()}</p></div>'
    return render_template_string(H, content=c, user=session)


@app.route("/aaliyah", methods=["GET","POST"])
def aaliyah_route():
    if "user_id" not in session: return redirect("/login")
    an = ""
    if request.method == "POST":
        f = request.form.get("frage","")
        if f:
            a = ki(f).replace("\n","<br>")
            an = f'<div class="al ai" style="flex-direction:column;align-items:start"><strong>🤖 Aaliyah:</strong><div style="margin-top:10px">{a}</div></div>'
    c = f'<h1>🤖 Aaliyah KI</h1><div class="cd"><form method="POST"><input type="text" name="frage" placeholder="Frag Aaliyah..." required><button type="submit" class="bt b5" style="width:100%">📤 Senden</button></form>{an}</div>'
    return render_template_string(H, content=c, user=session)


@app.route("/avinu", methods=["GET","POST"])
def avinu_dashboard():
    if "user_id" not in session: return redirect("/login")
    msg = ""
    if request.method == "POST":
        br=request.form.get("branche",""); sb=request.form.get("suchbegriff","")
        so=request.form.get("standort",""); rd=int(request.form.get("radius",25))
        intl=request.form.get("international")=="yes"
        if not sb and br: sb=BRANCHEN.get(br,["Job"])[0]
        if sb and so:
            try:
                aj=alle_jobs_suchen(sb,so,rd,intl)
                if aj:
                    n=jobs_speichern(session["user_id"],aj,br,rd)
                    msg=f'<div class="al ao">✅ {n} neue Jobs!</div>'
                else: msg='<div class="al aw">⚠️ Keine Jobs!</div>'
            except Exception as e: msg=f'<div class="al ae">❌ {str(e)[:100]}</div>'

    ft=request.args.get("filter","offen"); jobs=jobs_laden(session["user_id"],ft)
    bo="".join([f'<option value="{b}">' for b in get_alle_berufe()])
    bh="".join([f'<option value="{k}">{v}</option>' for k,v in {"it":"💻 IT","handwerk":"🔧 Handwerk","gesundheit":"🏥 Gesundheit","verwaltung":"📋 Verwaltung","verkauf":"🛒 Verkauf","logistik":"📦 Logistik","gastronomie":"🍽️ Gastronomie","bildung":"📚 Bildung","marketing":"📱 Marketing","finanzen":"💰 Finanzen","transport":"🚚 Transport","produktion":"🏭 Produktion","reinigung":"🧹 Reinigung","sicherheit":"🛡️ Sicherheit"}.items()])

    jh=""
    for j in jobs[:30]:
        bb='<span style="background:var(--gn);color:white;padding:4px 10px;border-radius:12px;font-size:11px">✅</span>' if j[11] else ''
        fv=j[13] if len(j)>13 else 0
        ld=j[15] if len(j)>15 else "DE"
        fg={"DE":"🇩🇪","US":"🇺🇸","UK":"🇬🇧","FR":"🇫🇷","EU":"🇪🇺","WORLD":"🌍","INT":"🌍"}.get(ld,"🌍")
        ul2=f'<a href="{j[6]}" target="_blank">🔗</a>' if j[6] else ""
        ds2=j[5][:200]+"..." if j[5] and len(j[5])>200 else (j[5] or "")
        jh+=f'<div class="cd"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:15px"><div style="flex:1;min-width:280px"><h3>{fg} {j[3]} {bb}</h3><p style="color:var(--cy);font-size:16px">🏢 <strong>{j[2]}</strong></p><p style="color:var(--t2);font-size:13px">📍 {j[4]} · 🔗 {j[9]} · 🏷️ {j[8]}</p>{f"<p style=color:var(--t3);font-size:13px>{ds2}</p>" if ds2 else ""}<p>{ul2}</p></div><div style="display:flex;flex-direction:column;gap:8px"><a href="/xsi/schnell/{j[0]}" class="bt b2">🤖 XSI</a><a href="/avinu/favorit/{j[0]}" class="bt b3" style="padding:8px 14px">{"⭐" if fv else "☆"}</a><a href="/avinu/loeschen/{j[0]}" class="bt b4" style="padding:8px 14px" onclick="return confirm(\'?\')">🗑️</a></div></div></div>'
    if not jh: jh='<p style="text-align:center;color:var(--t3);padding:40px">Keine Jobs!</p>'

    cn=sqlite3.connect(DB); cc=cn.cursor()
    cc.execute("SELECT COUNT(*) FROM jobs WHERE user_id=?",(session["user_id"],)); tt=cc.fetchone()[0]
    try:
        cc.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND beworben=1",(session["user_id"],)); bc=cc.fetchone()[0]
        cc.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND favorit=1",(session["user_id"],)); fc=cc.fetchone()[0]
    except: bc=fc=0
    cn.close()

    c=f'<h1>⚡ AVINU - Global Jobs</h1><p>10+ Portale · 300+ Berufe · 🌍</p>{msg}<div class="cd"><h3>🔍 Job-Suche</h3><form method="POST"><p>📂 Branche:</p><select name="branche"><option value="">--</option>{bh}</select><p>💼 Beruf:</p><input type="text" name="suchbegriff" placeholder="IT-Fachtechniker, Praktikum..." list="bl" required><datalist id="bl">{bo}</datalist><p>📍 Standort:</p><input type="text" name="standort" placeholder="Berlin, Mainz..." required><p>📏 Umkreis: <span id="rv">25</span> km</p><input type="range" name="radius" min="5" max="200" value="25" step="5" oninput="document.getElementById(\'rv\').textContent=this.value" style="width:100%;margin-bottom:15px"><div style="margin:20px 0;padding:15px;background:rgba(0,217,255,0.1);border-radius:12px"><label style="display:flex;align-items:center;gap:10px;cursor:pointer"><input type="checkbox" name="international" value="yes" style="width:auto"><span>🌍 <strong>International</strong></span></label></div><button type="submit" class="bt b1" style="width:100%">🚀 Jobs suchen</button></form></div><div class="gr" style="margin:30px 0"><a href="/avinu?filter=alle" style="text-decoration:none"><div class="sc"><div class="si">💼</div><div class="sv">{tt}</div><div class="sl">Alle</div></div></a><a href="/avinu?filter=offen" style="text-decoration:none"><div class="sc"><div class="si">📋</div><div class="sv">{tt-bc}</div><div class="sl">Offen</div></div></a><a href="/avinu?filter=beworben" style="text-decoration:none"><div class="sc"><div class="si">✅</div><div class="sv">{bc}</div><div class="sl">Beworben</div></div></a><a href="/avinu?filter=favoriten" style="text-decoration:none"><div class="sc"><div class="si">⭐</div><div class="sv">{fc}</div><div class="sl">Favoriten</div></div></a></div><h2>🎯 Jobs ({len(jobs)})</h2>{jh}'
    return render_template_string(H, content=c, user=session)


@app.route("/avinu/favorit/<int:jid>")
def avinu_favorit(jid):
    if "user_id" not in session: return redirect("/login")
    job_favorit_toggle(jid, session["user_id"]); return redirect("/avinu")


@app.route("/avinu/loeschen/<int:jid>")
def avinu_loeschen(jid):
    if "user_id" not in session: return redirect("/login")
    job_loeschen(jid, session["user_id"]); return redirect("/avinu")


@app.route("/xsi")
def xsi_dashboard():
    if "user_id" not in session: return redirect("/login")
    st = xsi_statistiken(session["user_id"])
    ch = xsi_unterlagen_pruefen(session["user_id"])
    us = ""
    if not ch["komplett"]:
        ms = []
        if not ch["lebenslauf"]: ms.append("Lebenslauf")
        if not ch["zeugnis"]: ms.append("Zeugnis")
        if not ch["zertifikat"]: ms.append("Zertifikat")
        if not ch["bild"]: ms.append("Foto")
        us = '<div class="al aw">⚠️ Fehlend: ' + ", ".join(ms) + ' <a href="/uploads">Hochladen</a></div>'
    else:
        us = '<div class="al ao">✅ Alle Unterlagen da!</div>'
    bw = xsi_bewerbungen_laden(session["user_id"])
    bh = ""
    for b in bw[:10]:
        ic = {"erstellt":"📝","gesendet":"✅","antwort":"💬","absage":"❌"}.get(b[9],"📋")
        bh += f'<div class="ui"><div>{ic} <strong>{b[4]}</strong> bei {b[3]}<br><small style="color:var(--t3)">An: {b[5] or "N/A"} · {b[9]}</small></div><a href="/xsi/detail/{b[0]}" class="bt b1" style="padding:8px 14px">👁️</a></div>'
    if not bh: bh = '<p style="text-align:center;color:var(--t3)">Noch keine</p>'
    c = f'<h1>🤖 XSI Bot - Auto-Bewerber</h1><p>Automatisch Bewerbungen erstellen & senden!</p>{us}<div class="gr" style="margin:30px 0"><a href="/xsi/neu" style="text-decoration:none"><div class="sc"><div class="si">✨</div><div class="sv">Neu</div><div class="sl">Bewerbung</div></div></a><div class="sc"><div class="si">📧</div><div class="sv">{st["gesendet"]}</div><div class="sl">Gesendet</div></div><div class="sc"><div class="si">📝</div><div class="sv">{st["erstellt"]}</div><div class="sl">Entwuerfe</div></div><div class="sc"><div class="si">📂</div><div class="sv">{st["unterlagen"]}</div><div class="sl">Unterlagen</div></div></div><h2>📧 Bewerbungen</h2><div class="cd">{bh}</div>'
    return render_template_string(H, content=c, user=session)


@app.route("/xsi/neu", methods=["GET","POST"])
def xsi_neu():
    if "user_id" not in session: return redirect("/login")
    pr = pl(session["user_id"]); msg = ""
    if request.method == "POST":
        fi=request.form.get("firma","").strip(); po=request.form.get("position","").strip()
        em=request.form.get("empfaenger","").strip(); ti=request.form.get("template_id","")
        sp=request.form.get("sprache","de"); ak=request.form.get("aktion","erstellen")
        if fi and po and ti:
            cn=sqlite3.connect(DB); cc=cn.cursor()
            cc.execute("SELECT * FROM xsi_templates WHERE id=?",(int(ti),))
            t=cc.fetchone(); cn.close()
            if t:
                bt2=xsi_betreff_erstellen(t[2],fi,po,pr)
                an=xsi_anschreiben_komplett(t[3],fi,po,pr,sp)
                bi=xsi_bewerbung_speichern(session["user_id"],0,fi,po,em,bt2,an,"erstellt",sp)
                if ak=="senden" and em:
                    ok,info=xsi_email_senden(em,bt2,an,session["user_id"],pr)
                    if ok:
                        xsi_bewerbung_status_update(bi,"gesendet")
                        msg=f'<div class="al ao">✅ An {fi} gesendet! {info}</div>'
                    else: msg=f'<div class="al ae">❌ {info}</div>'
                else: msg='<div class="al ao">✅ Entwurf gespeichert!</div>'

    tp=xsi_templates_laden(premium=session.get("premium",False))
    th=""
    for t in tp:
        pb='<span class="bg">💎</span>' if t[5] else ''
        th+=f'<label style="display:block;margin:10px 0;padding:16px;background:rgba(10,14,26,0.5);border-radius:12px;cursor:pointer"><input type="radio" name="template_id" value="{t[0]}" required><strong>{t[1]}</strong> {pb}<br><small style="color:var(--t3)">Betreff: {t[2][:50]}... | {t[4].upper()}</small></label>'

    ch=xsi_unterlagen_pruefen(session["user_id"])
    uh=""
    for k,v in [("📄 Lebenslauf",ch["lebenslauf"]),("📜 Zeugnis",ch["zeugnis"]),("🏆 Zertifikat",ch["zertifikat"]),("🖼️ Foto",ch["bild"])]:
        uh+=f'<span style="margin-right:15px">{"✅" if v else "❌"} {k}</span>'

    c=f'<h1>✨ Neue Bewerbung mit XSI</h1>{msg}<div class="cd"><h3>📋 Unterlagen</h3><div style="margin:10px 0">{uh}</div>{"<a href=/uploads class=bt b3>📂 Hochladen</a>" if not ch["komplett"] else ""}</div><div class="cd"><h3>📧 Bewerbung</h3><form method="POST"><p>📋 Art:</p><select name="typ"><option value="job">💼 Job</option><option value="praktikum">🎓 Praktikum</option><option value="ausbildung">📚 Ausbildung</option><option value="initiativ">💡 Initiativ</option><option value="werkstudent">🧑‍💻 Werkstudent</option><option value="minijob">💶 Minijob</option></select><p>🏢 Firma:</p><input type="text" name="firma" placeholder="SAP, Telekom, Siemens..." required><p>💼 Position:</p><input type="text" name="position" placeholder="IT-Fachtechniker, Praktikant..." required><p>📧 E-Mail der Firma:</p><input type="email" name="empfaenger" placeholder="bewerbung@firma.de"><p>🌍 Sprache:</p><select name="sprache"><option value="de">🇩🇪 Deutsch</option><option value="en">🇬🇧 English</option><option value="fr">🇫🇷 Francais</option></select><p>📝 Vorlage:</p>{th}<div style="display:flex;gap:10px;margin-top:20px"><button type="submit" name="aktion" value="erstellen" class="bt b1" style="flex:1">📝 Entwurf</button><button type="submit" name="aktion" value="senden" class="bt b2" style="flex:1">🚀 Senden!</button></div></form></div><div class="al ai">💡 XSI generiert KI-Anschreiben + haengt ALLE Unterlagen an!</div>'
    return render_template_string(H, content=c, user=session)


@app.route("/xsi/schnell/<int:jid>")
def xsi_schnell(jid):
    if "user_id" not in session: return redirect("/login")
    cn=sqlite3.connect(DB); cc=cn.cursor()
    cc.execute("SELECT firma,position FROM jobs WHERE id=? AND user_id=?",(jid,session["user_id"]))
    j=cc.fetchone(); cn.close()
    if not j: return redirect("/avinu")
    return redirect(f"/xsi/neu?firma={j[0]}&position={j[1]}")


@app.route("/xsi/detail/<int:bid>")
def xsi_detail(bid):
    if "user_id" not in session: return redirect("/login")
    cn=sqlite3.connect(DB); cc=cn.cursor()
    cc.execute("SELECT * FROM xsi_bewerbungen WHERE id=? AND user_id=?",(bid,session["user_id"]))
    b=cc.fetchone(); cn.close()
    if not b: return redirect("/xsi")
    si={"erstellt":"📝 Entwurf","gesendet":"✅ Gesendet","antwort":"💬 Antwort","absage":"❌ Absage"}.get(b[9],b[9])
    c=f'<h1>📧 Bewerbung</h1><div class="cd"><h3>{si}</h3><p><strong>🏢</strong> {b[3]}</p><p><strong>💼</strong> {b[4]}</p><p><strong>📧</strong> {b[5] or "N/A"}</p><p><strong>📝</strong> {b[6]}</p><p><strong>📎</strong> {b[8] or "Keine"}</p></div><div class="cd"><h3>✉️ Anschreiben</h3><textarea rows="20">{b[7]}</textarea></div><a href="/xsi" class="bt b1">← Zurueck</a>'
    return render_template_string(H, content=c, user=session)


@app.route("/uploads", methods=["GET","POST"])
def uploads():
    if "user_id" not in session: return redirect("/login")
    msg=""
    if request.method == "POST":
        k=request.form.get("kategorie","dokument")
        if "datei" in request.files:
            f=request.files["datei"]
            if f and f.filename and af(f.filename):
                r=ds(f,session["user_id"],k)
                if r: msg=f'<div class="al ao">✅ {r}!</div>'
    uu=ul(session["user_id"])
    uh=""
    for u in uu:
        ic="📄" if u[2]==".pdf" else "🖼️"
        uh+=f'<div class="ui"><div>{ic} <strong>{u[1]}</strong><br><small>{u[3]}-{u[5][:16]}</small></div><div><a href="/download/{u[0]}" class="bt b1" style="padding:8px 14px">⬇️</a> <a href="/delete/{u[0]}" class="bt b4" style="padding:8px 14px" onclick="return confirm(\'?\')">🗑️</a></div></div>'
    if not uh: uh='<p>Keine Dateien</p>'
    c=f'<h1>📂 Dateien</h1>{msg}<div class="cd"><form method="POST" enctype="multipart/form-data"><select name="kategorie" required><option value="lebenslauf">📄 Lebenslauf</option><option value="zeugnis">📜 Zeugnis</option><option value="zertifikat">🏆 Zertifikat</option><option value="bild">🖼️ Bewerbungsbild</option></select><input type="file" name="datei" required accept=".pdf,.png,.jpg,.jpeg"><button type="submit" class="bt b2" style="width:100%">🚀 Upload</button></form></div><div class="cd">{uh}</div>'
    return render_template_string(H, content=c, user=session)


@app.route("/download/<int:uid>")
def download_datei(uid):
    if "user_id" not in session: return redirect("/login")
    cn=sqlite3.connect(DB); cc=cn.cursor()
    cc.execute("SELECT pfad,dateiname FROM uploads WHERE id=? AND user_id=?",(uid,session["user_id"]))
    r=cc.fetchone(); cn.close()
    if r and os.path.exists(r[0]): return send_file(r[0],as_attachment=True,download_name=r[1])
    return "Nicht gefunden",404


@app.route("/delete/<int:uid>")
def delete_datei(uid):
    if "user_id" not in session: return redirect("/login")
    udel(uid,session["user_id"]); return redirect("/uploads")


@app.route("/lebenslauf", methods=["GET","POST"])
def lebenslauf():
    if "user_id" not in session: return redirect("/login")
    msg=""
    if request.method=="POST":
        d={k:request.form.get(k,"") for k in ["vorname","nachname","strasse","plz","stadt","telefon","email","geburtsdatum","kenntnisse","sprachen"]}
        ps(session["user_id"],d); msg='<div class="al ao">✅</div>'
    p=pl(session["user_id"])
    c=f'<h1>📝 Lebenslauf</h1>{msg}<form method="POST"><div class="cd"><h3>👤 Daten</h3><input type="text" name="vorname" placeholder="Vorname" value="{p.get("vorname","")}"><input type="text" name="nachname" placeholder="Nachname" value="{p.get("nachname","")}"><input type="text" name="strasse" placeholder="Strasse" value="{p.get("strasse","")}"><input type="text" name="plz" placeholder="PLZ" value="{p.get("plz","")}"><input type="text" name="stadt" placeholder="Stadt" value="{p.get("stadt","")}"><input type="text" name="telefon" placeholder="Telefon" value="{p.get("telefon","")}"><input type="email" name="email" placeholder="E-Mail" value="{p.get("email","")}"><input type="text" name="geburtsdatum" placeholder="Geburtsdatum" value="{p.get("geburtsdatum","")}"></div><div class="cd"><h3>💼 Kenntnisse</h3><textarea name="kenntnisse" rows="6">{p.get("kenntnisse","")}</textarea></div><div class="cd"><h3>🌍 Sprachen</h3><textarea name="sprachen" rows="4">{p.get("sprachen","")}</textarea></div><button type="submit" class="bt b2">💾</button></form>'
    return render_template_string(H, content=c, user=session)


@app.route("/bewerbungen", methods=["GET","POST"])
def bewerbungen():
    if "user_id" not in session: return redirect("/login")
    msg=""
    if request.method=="POST":
        f=request.form.get("firma","").strip(); e=request.form.get("email","").strip()
        bw2=bz(session["user_id"])
        if not session.get("premium") and bw2>=5: msg='<div class="al aw">⚠️ Limit!</div>'
        elif f and e:
            cn=sqlite3.connect(DB); cc=cn.cursor()
            try: cc.execute("INSERT INTO bewerbungen (user_id,firma,email,datum,typ) VALUES (?,?,?,?,?)",(session["user_id"],f,e,datetime.now().isoformat(),request.form.get("typ","job")))
            except: cc.execute("INSERT INTO bewerbungen (user_id,firma,email,datum) VALUES (?,?,?,?)",(session["user_id"],f,e,datetime.now().isoformat()))
            cn.commit(); cn.close(); msg=f'<div class="al ao">✅ {f}!</div>'
    bw2=bz(session["user_id"]); lm="∞" if session.get("premium") else 5
    c=f'<h1>📧 Bewerbungen</h1><div class="cd"><h3>📊 {bw2} / {lm}</h3></div>{msg}<div class="cd"><form method="POST"><select name="typ"><option value="job">💼 Job</option><option value="praktikum">🎓 Praktikum</option><option value="ausbildung">📚 Ausbildung</option><option value="werkstudent">🧑‍💻 Werkstudent</option></select><input type="text" name="firma" placeholder="Firma" required><input type="email" name="email" placeholder="E-Mail" required><button type="submit" class="bt b2">💾</button></form></div>'
    return render_template_string(H, content=c, user=session)


@app.route("/premium")
def premium():
    c='<h1>💎 Premium</h1><div class="gr"><div class="cd"><h2>🆓 Free</h2><h3>0 €</h3><ul style="list-style:none"><li>✓ 5 Bewerbungen</li></ul><button class="bt b1" style="width:100%">Aktuell</button></div><div class="cd" style="border:2px solid var(--yl)"><span class="bg">BELIEBT</span><h2>💎 Premium</h2><h3>1.99 €/Monat</h3><ul style="list-style:none"><li>✓ Unbegrenzt</li><li>✓ XSI Auto-Sender</li><li>✓ Premium Vorlagen</li></ul><a href="/aktivieren" class="bt b3" style="width:100%">🚀 Upgrade</a></div></div>'
    return render_template_string(H, content=c, user=session if "user_id" in session else None)


@app.route("/aktivieren", methods=["GET","POST"])
def aktivieren():
    if "user_id" not in session: return redirect("/login")
    msg=""
    if request.method=="POST":
        if request.form.get("code","").strip()=="XSIKOM-ADMIN-2026-PREMIUM":
            pa(session["user_id"]); session["premium"]=1
            return render_template_string(H, content='<h1>🎉</h1><div class="al ao">✅ Premium!</div><a href="/dashboard" class="bt b1">Dashboard</a>', user=session)
        msg='<div class="al ae">❌</div>'
    sb=""
    if stripe.api_key and STRIPE_PRICE:
        sb='<a href="/stripe-checkout" class="bt b3" style="width:100%;margin-top:15px">💳 Kreditkarte (1.99€)</a>'
    c=f'<h1>🔐 Premium</h1>{msg}<div class="cd"><h3>🔑 Code</h3><form method="POST"><input type="text" name="code" placeholder="Premium-Code" required><button type="submit" class="bt b2" style="width:100%">🚀</button></form></div><div class="cd"><h3>💳 Zahlung</h3>{sb if sb else "<p style=color:var(--t3)>Stripe kommt...</p>"}</div>'
    return render_template_string(H, content=c, user=session)


@app.route("/stripe-checkout")
def stripe_checkout():
    if "user_id" not in session: return redirect("/login")
    if not stripe.api_key or not STRIPE_PRICE: return redirect("/aktivieren")
    try:
        d=request.host_url.rstrip("/")
        cs=stripe.checkout.Session.create(payment_method_types=["card"],line_items=[{"price":STRIPE_PRICE,"quantity":1}],mode="subscription",success_url=f"{d}/stripe-success?session_id={{CHECKOUT_SESSION_ID}}",cancel_url=f"{d}/premium",metadata={"user_id":str(session["user_id"])})
        return redirect(cs.url,code=303)
    except Exception as e:
        return render_template_string(H, content=f'<h1>❌</h1><div class="al ae">{str(e)[:200]}</div>', user=session)


@app.route("/stripe-success")
def stripe_success():
    if "user_id" not in session: return redirect("/login")
    sid=request.args.get("session_id")
    if sid and stripe.api_key:
        try:
            cs=stripe.checkout.Session.retrieve(sid)
            if cs.payment_status=="paid": pa(session["user_id"]); session["premium"]=1
        except: pass
    return render_template_string(H, content='<h1>🎉</h1><div class="al ao">✅ Premium!</div><a href="/dashboard" class="bt b1">Dashboard</a>', user=session)


@app.route("/profil")
@app.route("/tutorial")
def tutorial():
    if "user_id" not in session: return redirect("/login")
    c = '<h1>📚 Tutorial</h1><p>Lerne alle Features!</p><div class="gr"><a href="/tutorial/start" style="text-decoration:none"><div class="sc"><div class="si">🚀</div><div class="sv">Start</div><div class="sl">Erste Schritte</div></div></a><a href="/tutorial/aaliyah" style="text-decoration:none"><div class="sc"><div class="si">🤖</div><div class="sv">Aaliyah</div><div class="sl">KI-Beraterin</div></div></a><a href="/tutorial/avinu" style="text-decoration:none"><div class="sc"><div class="si">⚡</div><div class="sv">AVINU</div><div class="sl">Job-Suche</div></div></a><a href="/tutorial/xsi" style="text-decoration:none"><div class="sc"><div class="si">🤖</div><div class="sv">XSI</div><div class="sl">Auto-Bewerber</div></div></a><a href="/tutorial/faq" style="text-decoration:none"><div class="sc"><div class="si">❓</div><div class="sv">FAQ</div><div class="sl">Fragen</div></div></a><a href="/tutorial/tipps" style="text-decoration:none"><div class="sc"><div class="si">💡</div><div class="sv">Tipps</div><div class="sl">Profi-Tipps</div></div></a></div>'
    return render_template_string(H, content=c, user=session)


@app.route("/tutorial/start")
def tutorial_start():
    if "user_id" not in session: return redirect("/login")
    c = '<h1>🚀 Erste Schritte</h1><div class="cd"><h3>Schritt 1: Profil</h3><p>Gehe zu <a href="/lebenslauf">📝 Lebenslauf</a> und fuelle deine Daten aus.</p></div><div class="cd"><h3>Schritt 2: Unterlagen</h3><p>Gehe zu <a href="/uploads">📂 Dateien</a> und lade hoch: Lebenslauf (PDF), Zeugnisse, Zertifikate, Bewerbungsfoto.</p></div><div class="cd"><h3>Schritt 3: Jobs suchen</h3><p>Gehe zu <a href="/avinu">⚡ AVINU</a>, waehle Branche + Standort und klick "Jobs suchen".</p></div><div class="cd"><h3>Schritt 4: Bewerben</h3><p>Gehe zu <a href="/xsi/neu">🤖 XSI</a>, gib Firma + Position ein, waehle Vorlage und klick "Senden!"</p></div><a href="/tutorial" class="bt b1">← Tutorial</a>'
    return render_template_string(H, content=c, user=session)


@app.route("/tutorial/aaliyah")
def tutorial_aaliyah():
    if "user_id" not in session: return redirect("/login")
    c = '<h1>🤖 Aaliyah Tutorial</h1><div class="cd"><h3>Was kann Aaliyah?</h3><ul style="padding-left:25px;line-height:2"><li>Bewerbungstipps</li><li>Anschreiben verbessern</li><li>Lebenslauf-Tipps</li><li>Interview-Vorbereitung</li><li>Gehaltsverhandlung</li><li>IT-Fachwissen</li></ul></div><div class="cd"><h3>Beispiel-Fragen</h3><p>"Wie schreibe ich ein Anschreiben fuer IT-Praktikum?"</p><p>"Welche Fragen kommen im Vorstellungsgespraech?"</p><p>"Wie verhandle ich Gehalt?"</p><p>"Erklaere mir TCP/IP"</p></div><a href="/aaliyah" class="bt b5">🤖 Aaliyah fragen</a> <a href="/tutorial" class="bt b1">← Tutorial</a>'
    return render_template_string(H, content=c, user=session)


@app.route("/tutorial/avinu")
def tutorial_avinu():
    if "user_id" not in session: return redirect("/login")
    c = '<h1>⚡ AVINU Tutorial</h1><div class="cd"><h3>So gehts</h3><ol style="padding-left:25px;line-height:2"><li>Branche waehlen (14 verfuegbar)</li><li>Beruf eingeben (300+ Berufe)</li><li>Standort eingeben</li><li>Umkreis waehlen (5-200 km)</li><li>Optional: International anklicken</li><li>"Jobs suchen" klicken!</li></ol></div><div class="cd"><h3>Nach der Suche</h3><ul style="padding-left:25px;line-height:2"><li>⭐ Favorit markieren</li><li>🤖 XSI: Auto-Bewerbung</li><li>🔗 Original-Stellenanzeige</li><li>Filter: Alle/Offen/Beworben/Favoriten</li></ul></div><a href="/avinu" class="bt b1">⚡ AVINU starten</a> <a href="/tutorial" class="bt b1">← Tutorial</a>'
    return render_template_string(H, content=c, user=session)


@app.route("/tutorial/xsi")
def tutorial_xsi():
    if "user_id" not in session: return redirect("/login")
    c = '<h1>🤖 XSI Tutorial</h1><div class="cd"><h3>Vorbereitung</h3><p>Bevor du XSI nutzt:</p><ul style="padding-left:25px;line-height:2"><li>📄 Lebenslauf hochladen</li><li>📜 Zeugnisse hochladen</li><li>🏆 Zertifikate hochladen</li><li>🖼️ Bewerbungsfoto hochladen</li><li>📝 Profil ausfuellen</li></ul></div><div class="cd"><h3>Bewerbung erstellen</h3><ol style="padding-left:25px;line-height:2"><li>Art waehlen (Job/Praktikum/Ausbildung)</li><li>Firma eingeben</li><li>Position eingeben</li><li>E-Mail der Firma eingeben</li><li>Sprache waehlen (DE/EN/FR)</li><li>Vorlage waehlen</li><li>"Senden!" klicken</li></ol></div><div class="al ao">✅ XSI erstellt KI-Anschreiben + haengt ALLE Unterlagen an!</div><a href="/xsi/neu" class="bt b2">🤖 XSI starten</a> <a href="/tutorial" class="bt b1">← Tutorial</a>'
    return render_template_string(H, content=c, user=session)


@app.route("/tutorial/faq")
def tutorial_faq():
    if "user_id" not in session: return redirect("/login")
    c = '<h1>❓ FAQ</h1>'
    faqs = [("Ist XsiKOM kostenlos?","Ja! Free: 5 Bewerbungen/Monat. Premium: 1.99€ unbegrenzt."),("Wie funktioniert die KI?","Llama 3.3 70B via Groq API. Generiert individuelle Anschreiben."),("Sind meine Daten sicher?","Ja! AES-256, 2FA, DSGVO konform."),("Kann ich Daten loeschen?","Ja! Profil → Loeschen. 30 Tage Frist."),("Welche Jobportale?","Arbeitsagentur, Indeed, StepStone, RemoteOK, Jobicy und mehr."),("Welche Sprachen?","Deutsch, Englisch, Franzoesisch."),("Welche Dateiformate?","PDF, PNG, JPG, JPEG, GIF, BMP, WEBP."),("Wie aktiviere ich Premium?","Admin-Code: XSIKOM-ADMIN-2026-PREMIUM oder Stripe.")]
    for f,a in faqs:
        c += f'<div class="cd"><h3>❓ {f}</h3><p>{a}</p></div>'
    c += '<a href="/tutorial" class="bt b1">← Tutorial</a>'
    return render_template_string(H, content=c, user=session)


@app.route("/tutorial/tipps")
def tutorial_tipps():
    if "user_id" not in session: return redirect("/login")
    tipps = [("🎯 Profil komplett ausfuellen","Je vollstaendiger, desto bessere KI-Anschreiben!"),("📄 Professionelle PDFs","Gut formatierter Lebenslauf als PDF macht den besten Eindruck."),("🖼️ Gutes Bewerbungsfoto","Professionelles Foto erhoeht die Chancen."),("🔍 Suchbegriffe variieren","Verschiedene Begriffe finden verschiedene Jobs."),("⭐ Favoriten nutzen","Interessante Jobs markieren."),("🌍 International suchen","Remote-Jobs weltweit mit 'International' Checkbox."),("📝 Erst Entwurf dann Senden","Pruefe das KI-Anschreiben vor dem Versand."),("🤖 Aaliyah fuer Vorbereitung","Frag Aaliyah vor dem Interview nach der Firma!")]
    c = '<h1>💡 Profi-Tipps</h1>'
    for t,b in tipps:
        c += f'<div class="cd"><h3>{t}</h3><p>{b}</p></div>'
    c += '<a href="/tutorial" class="bt b1">← Tutorial</a>'
    return render_template_string(H, content=c, user=session)
def profil():
    if "user_id" not in session: return redirect("/login")
    tf,_=get_2fa_status(session["user_id"])
    c=f'<h1>⚙️ Profil</h1><div class="gr"><a href="/profil/edit" style="text-decoration:none"><div class="sc"><div class="si">👤</div><div class="sv">Daten</div></div></a><a href="/profil/password" style="text-decoration:none"><div class="sc"><div class="si">🔑</div><div class="sv">Passwort</div></div></a><a href="/profil/2fa" style="text-decoration:none"><div class="sc"><div class="si">{"✅" if tf else "🔐"}</div><div class="sv">2FA</div></div></a><a href="/profil/export" style="text-decoration:none"><div class="sc"><div class="si">📥</div><div class="sv">Export</div></div></a><a href="/profil/delete" style="text-decoration:none"><div class="sc" style="border-color:var(--rd)"><div class="si">🗑️</div><div class="sv" style="color:var(--rd)">Loeschen</div></div></a></div>'
    return render_template_string(H, content=c, user=session)


@app.route("/profil/edit", methods=["GET","POST"])
def profil_edit():
    if "user_id" not in session: return redirect("/login")
    msg=""
    if request.method=="POST":
        cn=sqlite3.connect(DB); cc=cn.cursor()
        cc.execute("UPDATE benutzer SET vorname=?,nachname=?,email=? WHERE id=?",(request.form.get("vorname",""),request.form.get("nachname",""),request.form.get("email",""),session["user_id"]))
        cn.commit(); cn.close(); session["vorname"]=request.form.get("vorname",""); msg='<div class="al ao">✅</div>'
    cn=sqlite3.connect(DB); cc=cn.cursor()
    cc.execute("SELECT vorname,nachname,email FROM benutzer WHERE id=?",(session["user_id"],)); u=cc.fetchone(); cn.close()
    c=f'<h1>👤 Profil</h1>{msg}<div class="cd"><form method="POST"><input type="text" name="vorname" value="{u[0] or ""}" required><input type="text" name="nachname" value="{u[1] or ""}" required><input type="email" name="email" value="{u[2] or ""}" required><button type="submit" class="bt b2">💾</button></form></div>'
    return render_template_string(H, content=c, user=session)


@app.route("/profil/password", methods=["GET","POST"])
def profil_password():
    if "user_id" not in session: return redirect("/login")
    msg=""
    if request.method=="POST":
        cn=sqlite3.connect(DB); cc=cn.cursor()
        cc.execute("SELECT passwort FROM benutzer WHERE id=?",(session["user_id"],))
        if hp(request.form.get("old_password",""))==cc.fetchone()[0]:
            n=request.form.get("new_password","")
            if len(n)>=8 and n==request.form.get("confirm_password",""):
                cc.execute("UPDATE benutzer SET passwort=? WHERE id=?",(hp(n),session["user_id"])); cn.commit(); msg='<div class="al ao">✅</div>'
        cn.close()
    c=f'<h1>🔑 Passwort</h1>{msg}<div class="cd"><form method="POST"><input type="password" name="old_password" placeholder="Altes" required><input type="password" name="new_password" placeholder="Neues" required><input type="password" name="confirm_password" placeholder="Bestaetigen" required><button type="submit" class="bt b2">🔒</button></form></div>'
    return render_template_string(H, content=c, user=session)


@app.route("/profil/2fa", methods=["GET","POST"])
def profil_2fa():
    if "user_id" not in session: return redirect("/login")
    uid=session["user_id"]; tf,cu=get_2fa_status(uid); msg=""
    if request.method=="POST":
        ac=request.form.get("action",""); tk=request.form.get("token","")
        if ac=="enable":
            sc=request.form.get("secret","")
            if verify_2fa_token(sc,tk): enable_2fa(uid,sc); tf=True; msg='<div class="al ao">✅ 2FA aktiv!</div>'
        elif ac=="disable":
            if verify_2fa_token(cu,tk): disable_2fa(uid); tf=False
    if tf:
        c=f'<h1>🔐 2FA Aktiv</h1>{msg}<div class="cd"><form method="POST"><input type="hidden" name="action" value="disable"><input type="text" name="token" placeholder="Code" required><button type="submit" class="bt b4">⚠️ Deaktivieren</button></form></div>'
    else:
        sc=generate_2fa_secret(); qr=generate_qr_code(session.get("username",""),sc)
        c=f'<h1>🔐 2FA</h1>{msg}<div class="cd"><div style="text-align:center;background:white;padding:20px;border-radius:12px"><img src="{qr}" style="max-width:300px"></div><p style="margin-top:15px;font-family:monospace">{sc}</p><form method="POST"><input type="hidden" name="action" value="enable"><input type="hidden" name="secret" value="{sc}"><input type="text" name="token" placeholder="Code" required><button type="submit" class="bt b2">🔐 Aktivieren</button></form></div>'
    return render_template_string(H, content=c, user=session)


@app.route("/profil/export")
def profil_export():
    if "user_id" not in session: return redirect("/login")
    d=export_user_data(session["user_id"])
    return Response(json_module.dumps(d,indent=2),mimetype="application/json",headers={"Content-Disposition":"attachment; filename=export.json"})


@app.route("/profil/delete", methods=["GET","POST"])
def profil_delete():
    if "user_id" not in session: return redirect("/login")
    msg=""
    if request.method=="POST":
        if request.form.get("confirmation")=="LOESCHEN":
            request_account_deletion(session["user_id"]); msg='<div class="al ao">✅ Antrag!</div>'
    c=f'<h1 style="color:var(--rd)">🗑️ Loeschen</h1><div class="al aw">⚠️ 30 Tage!</div>{msg}<div class="cd"><form method="POST"><input type="password" name="password" placeholder="Passwort" required><input type="text" name="confirmation" placeholder="LOESCHEN" required><button type="submit" class="bt b4">🗑️</button></form></div>'
    return render_template_string(H, content=c, user=session)


@app.route("/impressum")
def impressum():
    return render_template_string(H, content=f'<h1>📜 Impressum</h1><div class="lt"><h3>§ 5 TMG</h3><p><strong>XsiKOM DIGITAL Projects</strong><br>Komi Tevi<br>Am Koenigsfloss 12<br>55252 Mainz-Kastel</p><p>E-Mail: <a href="mailto:{CE}">{CE}</a></p></div>', user=session if "user_id" in session else None)


@app.route("/datenschutz")
def datenschutz():
    return render_template_string(H, content=f'<h1>🔒 Datenschutz</h1><div class="lt"><p>XsiKOM DIGITAL Projects<br>{CE}</p></div>', user=session if "user_id" in session else None)


@app.route("/widerruf")
def widerruf():
    return render_template_string(H, content='<h1>↩️ Widerruf</h1><div class="lt"><p>14 Tage Widerrufsrecht.</p></div>', user=session if "user_id" in session else None)


@app.route("/haftung")
def haftung():
    return render_template_string(H, content='<h1>⚖️ Haftung</h1><div class="lt"><div class="al aw">⚠️ KI kann Fehler enthalten!</div></div>', user=session if "user_id" in session else None)


@app.route("/agb")
def agb():
    return render_template_string(H, content='<h1>📋 AGB</h1><div class="lt"><p>Free: 5 Bewerbungen | Premium: 1.99€</p></div>', user=session if "user_id" in session else None)


@app.route("/password-reset", methods=["GET","POST"])
def password_reset_request():
    msg=""
    if request.method=="POST":
        e=request.form.get("email","").strip()
        cn=sqlite3.connect(DB); cc=cn.cursor()
        cc.execute("SELECT id FROM benutzer WHERE email=?",(e,)); u=cc.fetchone(); cn.close()
        if u:
            t=create_password_reset_token(u[0]); l=f"{request.host_url}password-reset/{t}"
            msg=f'<div class="al ao">Link: {l}</div>'
    c=f'<div style="max-width:450px;margin:60px auto"><div class="cd"><h1>🔑 Reset</h1>{msg}<form method="POST"><input type="email" name="email" placeholder="E-Mail" required><button type="submit" class="bt b1">📧</button></form></div></div>'
    return render_template_string(H, content=c, user=None)


@app.route("/password-reset/<token>", methods=["GET","POST"])
def password_reset_new(token):
    uid=verify_reset_token(token)
    if not uid: return render_template_string(H, content="<h1>❌</h1>", user=None)
    if request.method=="POST":
        n=request.form.get("new_password","")
        if len(n)>=8:
            cn=sqlite3.connect(DB); cc=cn.cursor()
            cc.execute("UPDATE benutzer SET passwort=? WHERE id=?",(hp(n),uid)); cn.commit(); cn.close()
            use_reset_token(token); return redirect("/login")
    c='<div style="max-width:450px;margin:60px auto"><div class="cd"><h1>Neues Passwort</h1><form method="POST"><input type="password" name="new_password" required><button type="submit" class="bt b2">✅</button></form></div></div>'
    return render_template_string(H, content=c, user=None)


@app.route("/logout")
def logout():
    if "user_id" in session: audit_log(session["user_id"],"LOGOUT","")
    session.clear(); return redirect("/login")


@app.route("/manifest.json")
def manifest():
    return send_from_directory(".","manifest.json",mimetype="application/json")


@app.route("/sw.js")
def service_worker():
    r=make_response(send_from_directory(".","sw.js",mimetype="application/javascript"))
    r.headers["Service-Worker-Allowed"]="/"; return r


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static",filename)


@app.route("/.well-known/assetlinks.json")
def assetlinks():
    return send_from_directory(".well-known","assetlinks.json",mimetype="application/json")


dbi(); aa()


if __name__ == "__main__":
    print("=" * 60)
    print("  XsiKOM v7.0 FINAL")
    print(f"  KI: {'ONLINE' if GK else 'OFFLINE'}")
    print(f"  URL: http://localhost:5000")
    print("=" * 60)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)