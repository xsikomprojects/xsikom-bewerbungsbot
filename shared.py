"""
XsiKOM Shared Module
Alle Funktionen + HTML Template
"""
import os
import sqlite3
import hashlib
import random
import requests
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image

DB = "bewerbungen.db"
UF = "uploads"
AE = {"pdf", "png", "jpg", "jpeg", "gif", "bmp", "webp"}
CE = "xsikom_digital@xsikom.de"
GK = os.environ.get("GROQ_API_KEY", "")
GU = "https://api.groq.com/openai/v1/chat/completions"
os.makedirs(UF, exist_ok=True)


def ki(frage):
    """
    KI-Anfrage an Groq API.
    B4: Output wird NICHT hier bereinigt –
    das macht xss_clean() in der Route!
    """
    if not GK:
        return "KI offline."
    try:
        r = requests.post(
            GU,
            headers={
                "Authorization":  f"Bearer {GK}",
                "Content-Type":   "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role":    "system",
                        "content": (
                            "Du bist Aaliyah, KI-Karriereberaterin. "
                            "Antworte auf Deutsch. "
                            "Nutze keine HTML-Tags in deinen Antworten."
                        ),
                    },
                    {"role": "user", "content": frage},
                ],
                "temperature": 0.7,
                "max_tokens":  500,
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return "KI-Fehler. Bitte versuche es erneut."
    except Exception:
        return "Verbindung fehlgeschlagen."

def tipp():
    return random.choice(["Anschreiben individuell anpassen!", "Konkrete Projekte erwaehnen.",
        "Max. 1 Seite Anschreiben.", "Motivation zeigen!", "Rechtschreibung pruefen."])


def hp(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def bp(u, p):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT id,benutzername,vorname,nachname,rolle,premium FROM benutzer WHERE benutzername=? AND passwort=?", (u, hp(p)))
    r = c.fetchone()
    cn.close()
    if r:
        return {"id": r[0], "benutzername": r[1], "vorname": r[2], "nachname": r[3], "rolle": r[4], "premium": r[5]}
    return None


def ba(u, p, e, v, n, k="privat"):
    try:
        cn = sqlite3.connect(DB)
        c = cn.cursor()
        c.execute("INSERT INTO benutzer (benutzername,passwort,email,vorname,nachname,kunde_typ,erstellt) VALUES (?,?,?,?,?,?,?)",
            (u, hp(p), e, v, n, k, datetime.now().isoformat()))
        cn.commit()
        cn.close()
        return True
    except Exception:
        return False


def pa(uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("UPDATE benutzer SET premium=1 WHERE id=?", (uid,))
    cn.commit()
    cn.close()


def bz(uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT COUNT(*) FROM bewerbungen WHERE user_id=? AND datum>=?",
              (uid, datetime.now().replace(day=1).isoformat()))
    n = c.fetchone()[0]
    cn.close()
    return n


def pl(uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT * FROM profile WHERE user_id=?", (uid,))
    r = c.fetchone()
    cn.close()
    if not r:
        return {}
    return {"vorname": r[1] or "", "nachname": r[2] or "", "strasse": r[3] or "",
            "plz": r[4] or "", "stadt": r[5] or "", "telefon": r[6] or "",
            "email": r[7] or "", "geburtsdatum": r[8] or "",
            "kenntnisse": r[9] or "", "sprachen": r[10] or ""}


def ps(uid, d):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("DELETE FROM profile WHERE user_id=?", (uid,))
    c.execute("INSERT INTO profile (user_id,vorname,nachname,strasse,plz,stadt,telefon,email,geburtsdatum,kenntnisse,sprachen) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (uid, d.get("vorname",""), d.get("nachname",""), d.get("strasse",""), d.get("plz",""),
         d.get("stadt",""), d.get("telefon",""), d.get("email",""), d.get("geburtsdatum",""),
         d.get("kenntnisse",""), d.get("sprachen","")))
    cn.commit()
    cn.close()


def af(f):
    return "." in f and f.rsplit(".", 1)[1].lower() in AE


def ds(file, uid, kat):
    if not file or not af(file.filename):
        return None
    uf = os.path.join(UF, str(uid))
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
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            nn = f"{kat}_{ts}.jpg"
            pfad = os.path.join(uf, nn)
            img.save(pfad, "JPEG", quality=90)
        except Exception:
            file.seek(0)
            file.save(pfad)
    else:
        file.save(pfad)
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("INSERT INTO uploads (user_id,dateiname,typ,kategorie,pfad,upload_datum) VALUES (?,?,?,?,?,?)",
        (uid, nn, ext, kat, pfad, datetime.now().isoformat()))
    cn.commit()
    cn.close()
    return nn


def ul(uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT id,dateiname,typ,kategorie,pfad,upload_datum FROM uploads WHERE user_id=? ORDER BY id DESC", (uid,))
    rows = c.fetchall()
    cn.close()
    return rows


def udel(uid2, uid):
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT pfad FROM uploads WHERE id=? AND user_id=?", (uid2, uid))
    r = c.fetchone()
    if r and os.path.exists(r[0]):
        try:
            os.remove(r[0])
        except Exception:
            pass
    c.execute("DELETE FROM uploads WHERE id=? AND user_id=?", (uid2, uid))
    cn.commit()
    cn.close()

def dbi():
    cn = sqlite3.connect(DB)
    c = cn.cursor()

    # ── Bestehende Tabellen ───────────────────────────────────────
    c.execute("CREATE TABLE IF NOT EXISTS benutzer ("
              "id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "benutzername TEXT UNIQUE NOT NULL,"
              "passwort TEXT NOT NULL,"
              "email TEXT,"
              "vorname TEXT,"
              "nachname TEXT,"
              "rolle TEXT DEFAULT 'user',"
              "premium INTEGER DEFAULT 0,"
              "kunde_typ TEXT DEFAULT 'privat',"
              "theme TEXT DEFAULT 'dark',"  # F3: Dark/Light Mode
              "erstellt TEXT)")

    c.execute("CREATE TABLE IF NOT EXISTS bewerbungen ("
              "id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "user_id INTEGER,"
              "firma TEXT,"
              "email TEXT,"
              "status TEXT DEFAULT 'gesendet',"
              "datum TEXT,"
              "typ TEXT DEFAULT 'job')")

    c.execute("CREATE TABLE IF NOT EXISTS profile ("
              "user_id INTEGER PRIMARY KEY,"
              "vorname TEXT,"
              "nachname TEXT,"
              "strasse TEXT,"
              "plz TEXT,"
              "stadt TEXT,"
              "telefon TEXT,"
              "email TEXT,"
              "geburtsdatum TEXT,"
              "kenntnisse TEXT,"
              "sprachen TEXT)")

    c.execute("CREATE TABLE IF NOT EXISTS uploads ("
              "id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "user_id INTEGER,"
              "dateiname TEXT,"
              "typ TEXT,"
              "kategorie TEXT,"
              "pfad TEXT,"
              "upload_datum TEXT)")

    # ── F6: Bewerbungs-Tags ───────────────────────────────────────
    c.execute("CREATE TABLE IF NOT EXISTS bewerbung_tags ("
              "id INTEGER PRIMARY KEY AUTOINCREMENT,"
              "user_id INTEGER,"
              "bewerbung_id INTEGER,"
              "tag TEXT,"
              "farbe TEXT DEFAULT 'cy',"
              "erstellt TEXT)")

    # ── F1: Chart-Daten Cache ─────────────────────────────────────
    c.execute("CREATE TABLE IF NOT EXISTS statistiken_cache ("
              "user_id INTEGER PRIMARY KEY,"
              "daten TEXT,"
              "aktualisiert TEXT)")

    # ── ALTER TABLE: Neue Spalten hinzufügen ──────────────────────
    for m in [
        "ALTER TABLE bewerbungen ADD COLUMN typ TEXT DEFAULT 'job'",
        "ALTER TABLE bewerbungen ADD COLUMN tags TEXT DEFAULT ''",
        "ALTER TABLE benutzer ADD COLUMN theme TEXT DEFAULT 'dark'",
        "ALTER TABLE jobs ADD COLUMN favorit INTEGER DEFAULT 0",
        "ALTER TABLE jobs ADD COLUMN entfernung INTEGER DEFAULT 0",
        "ALTER TABLE jobs ADD COLUMN bewerbung_datum TEXT",
        "ALTER TABLE jobs ADD COLUMN land TEXT DEFAULT 'DE'",
        "ALTER TABLE jobs ADD COLUMN gehalt TEXT",
    ]:
        try:
            c.execute(m)
        except Exception:
            pass

    cn.commit()
    cn.close()


def aa():
    cn = sqlite3.connect(DB)
    c = cn.cursor()
    c.execute("SELECT id FROM benutzer WHERE benutzername='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO benutzer (benutzername,passwort,email,vorname,nachname,rolle,premium,erstellt) VALUES (?,?,?,?,?,?,?,?)",
            ("admin", hp("XsiKOM2026!"), CE, "Komi", "Tevi", "admin", 1, datetime.now().isoformat()))
        cn.commit()
    cn.close()


# ============================================================
# HTML TEMPLATE
# ============================================================
# ─────────────────────────────────────────────────────────────────
# F3: DARK/LIGHT MODE
# ─────────────────────────────────────────────────────────────────

def get_theme(uid):
    """Gibt Theme des Users zurück ('dark' oder 'light')."""
    try:
        cn = sqlite3.connect(DB)
        c  = cn.cursor()
        c.execute("SELECT theme FROM benutzer WHERE id=?", (uid,))
        r = c.fetchone()
        cn.close()
        return r[0] if r and r[0] else "dark"
    except Exception:
        return "dark"


def set_theme(uid, theme):
    """Speichert Theme des Users in DB."""
    if theme not in ("dark", "light"):
        theme = "dark"
    cn = sqlite3.connect(DB)
    c  = cn.cursor()
    c.execute(
        "UPDATE benutzer SET theme=? WHERE id=?",
        (theme, uid)
    )
    cn.commit()
    cn.close()


# ─────────────────────────────────────────────────────────────────
# F6: BEWERBUNGS-TAGS
# ─────────────────────────────────────────────────────────────────

# Standard-Tags mit Farben
STANDARD_TAGS = [
    ("⭐ Wichtig",   "yl"),
    ("✅ Zusage",    "gn"),
    ("❌ Absage",    "rd"),
    ("💬 Interview", "cy"),
    ("⏳ Warten",    "t2"),
    ("🗄️ Archiv",   "t3"),
]


def tags_laden(uid, bewerbung_id):
    """Lädt alle Tags einer Bewerbung."""
    try:
        cn = sqlite3.connect(DB)
        c  = cn.cursor()
        c.execute(
            "SELECT id, tag, farbe FROM bewerbung_tags "
            "WHERE user_id=? AND bewerbung_id=? "
            "ORDER BY id DESC",
            (uid, bewerbung_id)
        )
        rows = c.fetchall()
        cn.close()
        return rows
    except Exception:
        return []


def tag_hinzufuegen(uid, bewerbung_id, tag, farbe="cy"):
    """Fügt einen Tag zu einer Bewerbung hinzu."""
    try:
        cn = sqlite3.connect(DB)
        c  = cn.cursor()
        c.execute(
            "INSERT INTO bewerbung_tags "
            "(user_id, bewerbung_id, tag, farbe, erstellt) "
            "VALUES (?,?,?,?,?)",
            (uid, bewerbung_id, tag[:30], farbe,
             datetime.now().isoformat())
        )
        cn.commit()
        cn.close()
        return True
    except Exception:
        return False


def tag_loeschen(tag_id, uid):
    """Löscht einen Tag."""
    try:
        cn = sqlite3.connect(DB)
        c  = cn.cursor()
        c.execute(
            "DELETE FROM bewerbung_tags WHERE id=? AND user_id=?",
            (tag_id, uid)
        )
        cn.commit()
        cn.close()
        return True
    except Exception:
        return False


def alle_tags_user(uid):
    """Gibt alle einzigartigen Tags eines Users zurück."""
    try:
        cn = sqlite3.connect(DB)
        c  = cn.cursor()
        c.execute(
            "SELECT DISTINCT tag, farbe FROM bewerbung_tags "
            "WHERE user_id=? ORDER BY tag",
            (uid,)
        )
        rows = c.fetchall()
        cn.close()
        return rows
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────
# F1: CHART-DATEN
# ─────────────────────────────────────────────────────────────────

def chart_daten_laden(uid):
    """
    Lädt Statistik-Daten für Charts:
    - Bewerbungen pro Woche (letzte 8 Wochen)
    - Bewerbungen pro Monat (letzte 6 Monate)
    - Status-Verteilung
    """
    try:
        cn = sqlite3.connect(DB)
        c  = cn.cursor()

        # ── Pro Woche ────────────────────────────────────────────
        c.execute(
            "SELECT datum FROM bewerbungen "
            "WHERE user_id=? ORDER BY datum DESC LIMIT 200",
            (uid,)
        )
        alle = [r[0] for r in c.fetchall() if r[0]]

        wochen = {}
        monate = {}
        for d in alle:
            try:
                dt = datetime.fromisoformat(d[:19])
                # Kalenderwoche
                kw  = f"KW{dt.isocalendar()[1]:02d}"
                wochen[kw] = wochen.get(kw, 0) + 1
                # Monat
                mo  = dt.strftime("%b %Y")
                monate[mo] = monate.get(mo, 0) + 1
            except Exception:
                pass

        # Letzte 8 Wochen / 6 Monate
        wochen_labels = list(wochen.keys())[-8:]
        wochen_daten  = [wochen[k] for k in wochen_labels]
        monate_labels = list(monate.keys())[-6:]
        monate_daten  = [monate[k] for k in monate_labels]

        # ── Status-Verteilung ────────────────────────────────────
        c.execute(
            "SELECT status, COUNT(*) FROM bewerbungen "
            "WHERE user_id=? GROUP BY status",
            (uid,)
        )
        status_rows = c.fetchall()
        status_labels = [r[0] or "offen" for r in status_rows]
        status_daten  = [r[1]            for r in status_rows]

        # ── Gesamt ───────────────────────────────────────────────
        c.execute(
            "SELECT COUNT(*) FROM bewerbungen WHERE user_id=?",
            (uid,)
        )
        gesamt = c.fetchone()[0]

        cn.close()

        return {
            "wochen":  {"labels": wochen_labels, "daten": wochen_daten},
            "monate":  {"labels": monate_labels, "daten": monate_daten},
            "status":  {"labels": status_labels, "daten": status_daten},
            "gesamt":  gesamt,
        }

    except Exception:
        return {
            "wochen":  {"labels": [], "daten": []},
            "monate":  {"labels": [], "daten": []},
            "status":  {"labels": [], "daten": []},
            "gesamt":  0,
        }

H = ('<!DOCTYPE html><html lang="de" id="html-root"><head>'
     '<meta charset="UTF-8">'
     '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
     '<title>XsiKOM</title>'
     '<link rel="manifest" href="/manifest.json">'
     '<meta name="theme-color" content="#00D9FF">'
     '<link rel="icon" type="image/png" href="/static/icon-192.png">'
     '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">'
     # Chart.js CDN
     '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>'
     '<script>'
     # Theme System
     'function applyTheme(t){'
     '  var r=document.getElementById("html-root");'
     '  if(t==="light"){'
     '    r.style.setProperty("--bg","#F0F4FF");'
     '    r.style.setProperty("--cd","rgba(255,255,255,0.8)");'
     '    r.style.setProperty("--bd","rgba(0,0,0,0.1)");'
     '    r.style.setProperty("--t1","#1A1A2E");'
     '    r.style.setProperty("--t2","#4A5568");'
     '    r.style.setProperty("--t3","#718096");'
     '    r.style.setProperty("--bg-body","linear-gradient(135deg,#E8F4FD,#F0E8FF)");'
     '  }else{'
     '    r.style.setProperty("--bg","#0A0E1A");'
     '    r.style.setProperty("--cd","rgba(20,28,48,0.6)");'
     '    r.style.setProperty("--bd","rgba(255,255,255,0.08)");'
     '    r.style.setProperty("--t1","#FFF");'
     '    r.style.setProperty("--t2","#A0AEC0");'
     '    r.style.setProperty("--t3","#6B7280");'
     '    r.style.setProperty("--bg-body","none");'
     '  }'
     '  localStorage.setItem("theme",t);'
     '}'
     'function toggleTheme(){'
     '  var cur=localStorage.getItem("theme")||"dark";'
     '  var neu=cur==="dark"?"light":"dark";'
     '  applyTheme(neu);'
     '  var btn=document.getElementById("theme-btn");'
     '  if(btn)btn.textContent=neu==="dark"?"☀️":"🌙";'
     '  fetch("/theme/"+neu);'  # Speichert in DB
     '}'
     # Init Theme
     'document.addEventListener("DOMContentLoaded",function(){'
     '  var t=localStorage.getItem("theme")||"dark";'
     '  applyTheme(t);'
     '  var btn=document.getElementById("theme-btn");'
     '  if(btn)btn.textContent=t==="dark"?"☀️":"🌙";'
     '});'
     # Service Worker
     "if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js')});}"
     # Cookie Banner
     "function cookieAccept(){localStorage.setItem('c','1');document.getElementById('cb').style.display='none';}"
     "window.addEventListener('load',function(){if(localStorage.getItem('c')!=='1'){var b=document.getElementById('cb');if(b)b.style.display='block';}});"
     '</script>'
     '<style>'
     '*{margin:0;padding:0;box-sizing:border-box}'
     ':root{--bg:#0A0E1A;--cd:rgba(20,28,48,0.6);--bd:rgba(255,255,255,0.08);--cy:#00D9FF;--pu:#8B5CF6;--gn:#10F4B1;--yl:#FFD93D;--rd:#FF4757;--t1:#FFF;--t2:#A0AEC0;--t3:#6B7280}'
     "body{font-family:'Poppins',sans-serif;background:var(--bg);color:var(--t1);min-height:100vh;transition:background 0.3s,color 0.3s}"
     "body::before{content:'';position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(circle at 20% 20%,rgba(0,217,255,0.15) 0%,transparent 50%),radial-gradient(circle at 80% 80%,rgba(139,92,246,0.15) 0%,transparent 50%);z-index:-1}"
     '.ct{max-width:1200px;margin:0 auto;padding:20px}'
     '.hd{background:rgba(10,14,26,0.8);backdrop-filter:blur(20px);padding:20px 0;border-bottom:1px solid var(--bd);position:sticky;top:0;z-index:100}'
     '.hi{display:flex;justify-content:space-between;align-items:center}'
     ".lg{font-family:'Space Grotesk',sans-serif;font-size:32px;font-weight:700;background:linear-gradient(135deg,var(--cy),var(--pu));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}"
     '.st{color:var(--t2);font-size:13px}'
     '.nv{background:rgba(19,24,41,0.5);padding:12px 0;border-bottom:1px solid var(--bd);overflow-x:auto;white-space:nowrap}'
     '.ni{max-width:1200px;margin:0 auto;padding:0 20px;display:flex;gap:5px;align-items:center}'
     '.nv a{color:var(--t2);text-decoration:none;padding:10px 18px;border-radius:12px;font-size:13px;transition:all 0.3s;font-weight:500}'
     '.nv a:hover{color:var(--t1);background:rgba(0,217,255,0.15);transform:translateY(-2px)}'
     # Theme Toggle Button
     '.tm{background:rgba(0,217,255,0.1);border:1px solid var(--cy);color:var(--t1);padding:8px 14px;border-radius:12px;cursor:pointer;font-size:18px;transition:all 0.3s;margin-left:auto}'
     '.tm:hover{background:rgba(0,217,255,0.2);transform:translateY(-2px)}'
     '.cd{background:var(--cd);backdrop-filter:blur(20px);border-radius:20px;padding:30px;margin:20px 0;border:1px solid var(--bd);transition:all 0.4s}'
     '.cd:hover{transform:translateY(-5px);border-color:rgba(0,217,255,0.3)}'
     '.bt{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:14px 28px;border:none;border-radius:12px;cursor:pointer;font-weight:600;font-size:14px;text-decoration:none;transition:all 0.3s}'
     '.bt:hover{transform:translateY(-2px)}'
     '.b1{background:linear-gradient(135deg,var(--cy),#0099CC);color:white}'
     '.b2{background:linear-gradient(135deg,var(--gn),#059669);color:white}'
     '.b3{background:linear-gradient(135deg,var(--yl),#F59E0B);color:#0A0E1A}'
     '.b4{background:linear-gradient(135deg,var(--rd),#DC2626);color:white}'
     '.b5{background:linear-gradient(135deg,var(--pu),#6D28D9);color:white}'
     'input,textarea,select{background:rgba(10,14,26,0.6);border:1px solid var(--bd);color:var(--t1);padding:14px 18px;border-radius:12px;width:100%;margin-bottom:12px;font-size:14px;transition:all 0.3s}'
     'input:focus,textarea:focus,select:focus{outline:none;border-color:var(--cy);box-shadow:0 0 0 4px rgba(0,217,255,0.1)}'
     "h1{font-family:'Space Grotesk',sans-serif;font-size:36px;font-weight:700;background:linear-gradient(135deg,var(--cy),var(--pu));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:20px}"
     'h2{font-size:26px;font-weight:600;margin-bottom:16px}'
     'h3{font-size:18px;font-weight:600;color:var(--cy);margin-bottom:12px}'
     'p{line-height:1.7;color:var(--t2);margin-bottom:8px}'
     'a{color:var(--cy);text-decoration:none}'
     '.gr{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px}'
     '.sc{background:linear-gradient(135deg,rgba(20,28,48,0.8),rgba(30,38,58,0.6));border:1px solid var(--bd);border-radius:20px;padding:30px;text-align:center;transition:all 0.4s;cursor:pointer}'
     '.sc:hover{transform:translateY(-8px);border-color:var(--cy)}'
     '.si{font-size:48px;margin-bottom:12px}'
     ".sv{font-family:'Space Grotesk',sans-serif;font-size:32px;font-weight:700;background:linear-gradient(135deg,var(--cy),var(--pu));-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}"
     '.sl{color:var(--t2);font-size:13px;margin-top:4px}'
     '.bg{background:linear-gradient(135deg,var(--yl),#EC4899);color:#0A0E1A;padding:6px 14px;border-radius:20px;font-size:11px;font-weight:700;display:inline-block}'
     '.al{padding:16px 20px;border-radius:12px;margin:16px 0;border:1px solid}'
     '.ao{background:rgba(16,244,177,0.1);border-color:rgba(16,244,177,0.3);color:var(--gn)}'
     '.ae{background:rgba(255,71,87,0.1);border-color:rgba(255,71,87,0.3);color:var(--rd)}'
     '.aw{background:rgba(255,217,61,0.1);border-color:rgba(255,217,61,0.3);color:var(--yl)}'
     '.ai{background:rgba(0,217,255,0.1);border-color:rgba(0,217,255,0.3);color:var(--cy)}'
     '.ui{background:rgba(10,14,26,0.6);padding:16px;border-radius:12px;margin:10px 0;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--bd)}'
     # F6: Tag Styles
     '.tg{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;margin:3px;border:1px solid rgba(255,255,255,0.2)}'
     '.tg-cy{background:rgba(0,217,255,0.15);color:var(--cy);border-color:var(--cy)}'
     '.tg-gn{background:rgba(16,244,177,0.15);color:var(--gn);border-color:var(--gn)}'
     '.tg-yl{background:rgba(255,217,61,0.15);color:var(--yl);border-color:var(--yl)}'
     '.tg-rd{background:rgba(255,71,87,0.15);color:var(--rd);border-color:var(--rd)}'
     '.tg-pu{background:rgba(139,92,246,0.15);color:var(--pu);border-color:var(--pu)}'
     '.tg-t2{background:rgba(160,174,192,0.15);color:var(--t2);border-color:var(--t2)}'
     '.tg-t3{background:rgba(107,114,128,0.15);color:var(--t3);border-color:var(--t3)}'
     # Chart Container
     '.ch{position:relative;height:300px;margin:20px 0}'
     '.ft{background:rgba(10,14,26,0.9);padding:40px 20px 30px;text-align:center;color:var(--t3);margin-top:60px;border-top:1px solid var(--bd)}'
     '.ft a{color:var(--t2);margin:0 12px}'
     ".fb{margin-top:16px;font-family:'Space Grotesk',sans-serif;font-weight:600;color:var(--cy)}"
     '#cb{display:none;position:fixed;bottom:20px;left:20px;right:20px;max-width:1160px;margin:0 auto;background:rgba(20,28,48,0.95);color:white;padding:20px 25px;z-index:9999;border-radius:16px;border:1px solid var(--cy)}'
     '.lt{background:var(--cd);padding:30px;border-radius:20px;margin:20px 0;line-height:1.8;border:1px solid var(--bd)}'
     '.lt h3{color:var(--cy);margin-top:24px}'
     '@media(max-width:768px){h1{font-size:28px}.lg{font-size:24px}.ch{height:200px}}'
     '</style></head><body>'
     '<div id="cb"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px">'
     '<div>🍪 Cookies. <a href="/datenschutz" style="color:var(--cy)">Mehr</a></div>'
     '<button onclick="cookieAccept()" class="bt b2">✓</button></div></div>'
     '<div class="hd"><div class="ct hi"><div>'
     '<div style="display:flex;align-items:center;gap:12px">'
     '<img src="/static/logo.png" alt="XsiKOM" style="height:45px" onerror="this.style.display=\'none\'">'
     '<div class="lg">XsiKOM</div></div>'
     '<div class="st">{{ user.vorname if user else "KI Bewerbungs-Assistent" }}</div>'
     '</div>'
     # Theme Toggle im Header
     '<button class="tm" id="theme-btn" onclick="toggleTheme()">☀️</button>'
     '</div></div>'
     '{% if user %}'
     '<div class="nv"><div class="ni">'
     '<a href="/dashboard">🏠 Dashboard</a>'
     '<a href="/aaliyah">🤖 Aaliyah</a>'
     '<a href="/avinu">⚡ AVINU</a>'
     '<a href="/xsi">🤖 XSI Bot</a>'
     '<a href="/lebenslauf">📝 Lebenslauf</a>'
     '<a href="/pdf-lebenslauf">📄 PDF</a>'
     '<a href="/uploads">📂 Dateien</a>'
     '<a href="/bewerbungen">📧 Bewerbungen</a>'
     '<a href="/premium">💎 Premium</a>'
     '<a href="/tutorial">📚 Tutorial</a>'
     '<a href="/updates">🔄 Updates</a>'
     '<a href="/profil">⚙️ Profil</a>'
     '<a href="/logout">🚪 Logout</a>'
     '</div></div>'
     '{% endif %}'
     '<div class="ct">{{ content|safe }}</div>'
     '<div class="ft">'
  '<div style="margin-bottom:15px">'
'<a href="/landing" class="bt b2" style="padding:10px 24px">'
'🚀 Kostenlos starten</a>'
'</div>'
'<div><a href="/impressum">Impressum</a>·<a href="/datenschutz">Datenschutz</a>·<a href="/agb">AGB</a>·<a href="/widerruf">Widerruf</a>·<a href="/haftung">Haftung</a></div>'
     '<div class="fb">XsiKOM-BewerbungsBOT v10.0</div>'
     '<div style="margin-top:8px;font-size:11px;color:var(--t3)">© 2026 XsiKOM DIGITAL Projects<br>'
     '<a href="mailto:xsikom_digital@xsikom.de" style="color:var(--t3)">xsikom_digital@xsikom.de</a></div>'
     '</div></body></html>')