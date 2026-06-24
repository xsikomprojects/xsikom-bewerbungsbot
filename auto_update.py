"""
XsiKOM Auto-Update System
Monatliche KI-Updates
"""
import os
import sqlite3
import requests
import json
from datetime import datetime, timedelta

DB_NAME = "bewerbungen.db"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
VERSION = "8.0"


def update_db_init():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT, typ TEXT, beschreibung TEXT,
        details TEXT, datum TEXT, status TEXT DEFAULT 'geplant')""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, typ TEXT, nachricht TEXT,
        bewertung INTEGER, datum TEXT, bearbeitet INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS ki_vorschlaege (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kategorie TEXT, vorschlag TEXT, prioritaet TEXT,
        umgesetzt INTEGER DEFAULT 0, datum TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS changelog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT, datum TEXT, aenderungen TEXT, typ TEXT)""")
    conn.commit()
    conn.close()


def ki_anfrage(prompt):
    if not GROQ_API_KEY:
        return "KI offline."
    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "Du bist Software-Update-Experte. Deutsch, konkret."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7, "max_tokens": 800
            },
            timeout=15
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return "KI-Fehler."
    except Exception as e:
        return f"Verbindung fehlgeschlagen: {str(e)[:100]}"


def monatliches_update():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    ergebnisse = []

    neue_berufe = ki_anfrage("Nenne 10 neue gefragte Berufe 2026 mit Branche.")
    ergebnisse.append(("Neue Berufe", neue_berufe))
    c.execute("INSERT INTO ki_vorschlaege (kategorie, vorschlag, prioritaet, datum) VALUES (?,?,?,?)",
        ("berufe", neue_berufe, "mittel", datetime.now().isoformat()))

    trends = ki_anfrage("5 aktuelle Trends bei Bewerbungen 2026.")
    ergebnisse.append(("Bewerbungs-Trends", trends))
    c.execute("INSERT INTO ki_vorschlaege (kategorie, vorschlag, prioritaet, datum) VALUES (?,?,?,?)",
        ("trends", trends, "hoch", datetime.now().isoformat()))

    sicherheit = ki_anfrage("5 Sicherheits-Best-Practices fuer Web-Apps 2026.")
    ergebnisse.append(("Sicherheit", sicherheit))
    c.execute("INSERT INTO ki_vorschlaege (kategorie, vorschlag, prioritaet, datum) VALUES (?,?,?,?)",
        ("sicherheit", sicherheit, "hoch", datetime.now().isoformat()))

    ux = ki_anfrage("5 UX-Verbesserungen fuer Bewerbungs-Apps 2026.")
    ergebnisse.append(("UX", ux))
    c.execute("INSERT INTO ki_vorschlaege (kategorie, vorschlag, prioritaet, datum) VALUES (?,?,?,?)",
        ("ux", ux, "mittel", datetime.now().isoformat()))

    markt = ki_anfrage("Analyse des deutschen Arbeitsmarkts 2026: Top-Branchen und Staedte.")
    ergebnisse.append(("Markt-Analyse", markt))
    c.execute("INSERT INTO ki_vorschlaege (kategorie, vorschlag, prioritaet, datum) VALUES (?,?,?,?)",
        ("markt", markt, "niedrig", datetime.now().isoformat()))

    changelog_text = "Monatliches KI-Update:\n"
    for titel, inhalt in ergebnisse:
        changelog_text += f"\n{titel}:\n{inhalt[:200]}...\n"

    c.execute("INSERT INTO changelog (version, datum, aenderungen, typ) VALUES (?,?,?,?)",
        (VERSION, datetime.now().isoformat(), changelog_text, "ki_update"))

    c.execute("INSERT INTO updates (version, typ, beschreibung, details, datum, status) VALUES (?,?,?,?,?,?)",
        (VERSION, "monatlich", "Monatliches KI-Update",
         json.dumps([{"titel": t, "inhalt": i[:500]} for t, i in ergebnisse]),
         datetime.now().isoformat(), "abgeschlossen"))

    conn.commit()
    conn.close()
    return ergebnisse


def feedback_speichern(user_id, typ, nachricht, bewertung=5):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO feedback (user_id, typ, nachricht, bewertung, datum) VALUES (?,?,?,?,?)",
        (user_id, typ, nachricht, bewertung, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def changelog_laden(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM changelog ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def vorschlaege_laden(limit=20):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM ki_vorschlaege ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def update_status():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT datum FROM updates ORDER BY id DESC LIMIT 1")
    letztes = c.fetchone()

    c.execute("SELECT COUNT(*) FROM ki_vorschlaege WHERE umgesetzt=0")
    offen = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM feedback WHERE bearbeitet=0")
    fb_offen = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM changelog")
    gesamt = c.fetchone()[0]

    conn.close()

    naechstes = "Bald"
    if letztes:
        try:
            ldt = datetime.fromisoformat(letztes[0])
            naechstes = (ldt + timedelta(days=30)).strftime("%d.%m.%Y")
        except Exception:
            pass

    return {
        "version": VERSION,
        "letztes_update": letztes[0][:16] if letztes else "Noch keins",
        "naechstes_update": naechstes,
        "offene_vorschlaege": offen,
        "offenes_feedback": fb_offen,
        "updates_gesamt": gesamt,
    }


def ist_update_faellig():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT datum FROM updates ORDER BY id DESC LIMIT 1")
    letztes = c.fetchone()
    conn.close()

    if not letztes:
        return True

    try:
        ldt = datetime.fromisoformat(letztes[0])
        return (datetime.now() - ldt).days >= 30
    except Exception:
        return True


def auto_update_pruefen():
    if ist_update_faellig():
        print("KI-Update faellig! Starte...")
        ergebnisse = monatliches_update()
        print(f"Update fertig! {len(ergebnisse)} Bereiche.")
        return True
    return False


update_db_init()