"""
AVINU - KI Job-Such und Bewerbungs-Bot
Spezialist fuer ALLE Branchen!
"""
import os
import requests
import json
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
import re

DB_NAME = "bewerbungen.db"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ============================================================
# AVINU SYSTEM PROMPT
# ============================================================
AVINU_PROMPT = """Du bist AVINU, ein KI-Job-Such-Experte.

Deine Aufgabe:
- Hilf bei Jobsuche in ALLEN Branchen
- Analysiere Stellenanzeigen
- Erstelle individuelle Anschreiben
- Optimiere Bewerbungen

Branchen-Expertise:
- IT & Technik
- Handwerk & Bau
- Gesundheit & Pflege
- Verwaltung & Buero
- Verkauf & Handel
- Logistik & Transport
- Gastronomie & Hotel
- Bildung & Soziales
- Marketing & Medien
- Finanzen & Banken

Stil: Professionell, motivierend, konkret.
Antworte auf Deutsch in 3-5 Saetzen."""


# ============================================================
# DATENBANK SETUP
# ============================================================
def avinu_db_init():
    """Erstellt AVINU Tabellen."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            firma TEXT,
            position TEXT,
            standort TEXT,
            beschreibung TEXT,
            url TEXT,
            email TEXT,
            branche TEXT,
            quelle TEXT,
            gefunden TEXT,
            beworben INTEGER DEFAULT 0,
            bewerbung_datum TEXT
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS anschreiben_vorlagen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            beschreibung TEXT,
            template TEXT,
            premium INTEGER DEFAULT 0,
            branche TEXT
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS auto_bewerbungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_id INTEGER,
            anschreiben TEXT,
            status TEXT DEFAULT 'erstellt',
            gesendet TEXT,
            empfaenger TEXT,
            erstellt_am TEXT
        )
    """)
    
    conn.commit()
    
    # Standard Vorlagen einfügen
    standard_vorlagen_einfuegen()
    conn.close()


def standard_vorlagen_einfuegen():
    """Fuegt 10 Premium Vorlagen ein."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM anschreiben_vorlagen")
    if c.fetchone()[0] > 0:
        conn.close()
        return
    
    vorlagen = [
        {
            "name": "Klassisch Professionell",
            "beschreibung": "Klassische, formelle Bewerbung",
            "branche": "Alle",
            "premium": 0,
            "template": """Sehr geehrte Damen und Herren,

mit grossem Interesse habe ich Ihre Stellenausschreibung als {position} bei {firma} gelesen. 
Hiermit moechte ich mich um diese Position bewerben.

{einleitung}

{hauptteil}

{schluss}

Ueber eine Einladung zu einem persoenlichen Gespraech freue ich mich sehr.

Mit freundlichen Gruessen
{name}"""
        },
        {
            "name": "Modern & Dynamisch",
            "beschreibung": "Moderner Stil fuer junge Unternehmen",
            "branche": "IT, Marketing",
            "premium": 1,
            "template": """Hallo {ansprechpartner},

als ich Ihre Stellenanzeige fuer {position} entdeckt habe, wusste ich sofort: Das ist meine Chance!

{einleitung}

{hauptteil}

Was ich bei {firma} besonders schaetze: {firma_referenz}

{schluss}

Lassen Sie uns gerne sprechen - ich freue mich auf Ihre Antwort!

Beste Gruesse
{name}"""
        },
        {
            "name": "Karrierewechsel",
            "beschreibung": "Fuer Branchenwechsler",
            "branche": "Alle",
            "premium": 1,
            "template": """Sehr geehrte Damen und Herren,

mein bisheriger beruflicher Weg hat mich gelehrt, dass neue Herausforderungen den groessten Mehrwert schaffen. Die Position {position} bei {firma} ist genau diese Herausforderung.

{einleitung}

Meine bisherigen Erfahrungen sind ein wertvolles Plus:
{hauptteil}

{schluss}

Ich bringe Mut, Lernbereitschaft und frische Perspektiven mit. Ueber ein Gespraech freue ich mich.

Mit freundlichen Gruessen
{name}"""
        },
        {
            "name": "Berufseinstieg",
            "beschreibung": "Fuer Berufseinsteiger und Praktikanten",
            "branche": "Alle",
            "premium": 0,
            "template": """Sehr geehrte Damen und Herren,

mit Begeisterung bewerbe ich mich auf die ausgeschriebene Stelle als {position}. Ihr Unternehmen ist fuer mich der ideale Einstieg in meinen Wunschberuf.

{einleitung}

Was ich mitbringe:
{hauptteil}

{schluss}

Auch wenn ich am Anfang meiner Karriere stehe, bringe ich viel Motivation und Lernwillen mit. Ich freue mich auf ein Gespraech!

Mit freundlichen Gruessen
{name}"""
        },
        {
            "name": "IT & Tech Spezialist",
            "beschreibung": "Fuer IT Positionen",
            "branche": "IT",
            "premium": 1,
            "template": """Sehr geehrte Damen und Herren,

als technologiebegeisterter {position} habe ich Ihre Stelle bei {firma} mit grossem Interesse gelesen.

{einleitung}

Meine technischen Skills:
{hauptteil}

Was mich besonders interessiert: Die innovativen Projekte bei {firma}, insbesondere {firma_referenz}.

{schluss}

Ich freue mich auf ein technisches Gespraech und die Moeglichkeit, gemeinsam etwas zu bewegen!

Mit freundlichen Gruessen
{name}"""
        },
        {
            "name": "Fuehrungskraft",
            "beschreibung": "Fuer Manager und Fuehrungsrollen",
            "branche": "Management",
            "premium": 1,
            "template": """Sehr geehrte Damen und Herren,

mit ueber {jahre} Jahren Fuehrungserfahrung bewerbe ich mich um die Position {position} in Ihrem Hause.

{einleitung}

Meine Fuehrungsstaerken:
{hauptteil}

In meinen bisherigen Stationen konnte ich erfolgreich {erfolg} erreichen.

{schluss}

Ein persoenliches Gespraech ueber Ihre strategischen Ziele wuerde mich sehr freuen.

Mit freundlichen Gruessen
{name}"""
        },
        {
            "name": "Kreativ & Originell",
            "beschreibung": "Fuer Kreativbranche",
            "branche": "Marketing, Design",
            "premium": 1,
            "template": """Hallo {firma}-Team!

Ihre Stellenanzeige hat mich auf Anhieb begeistert - und ich bin sicher: Wir passen zusammen!

{einleitung}

Warum ich der richtige bin:
{hauptteil}

Meine Vision fuer diese Position: {vision}

{schluss}

Ich brenne darauf, gemeinsam mit Ihrem Team kreative Loesungen zu entwickeln. Wann koennen wir reden?

Kreative Gruesse
{name}"""
        },
        {
            "name": "Handwerk & Praktisch",
            "beschreibung": "Fuer Handwerksberufe",
            "branche": "Handwerk",
            "premium": 0,
            "template": """Sehr geehrte Damen und Herren,

mit grossem Interesse bewerbe ich mich auf die ausgeschriebene Stelle als {position}.

{einleitung}

Meine Qualifikationen:
{hauptteil}

Bei Ihnen schaetze ich besonders: {firma_referenz}

{schluss}

Ueber eine Einladung zum Vorstellungsgespraech und eventuell einer Probearbeit freue ich mich sehr.

Mit freundlichen Gruessen
{name}"""
        },
        {
            "name": "Gesundheit & Pflege",
            "beschreibung": "Fuer Gesundheitsberufe",
            "branche": "Gesundheit",
            "premium": 1,
            "template": """Sehr geehrte Damen und Herren,

Menschen zu helfen ist meine Berufung - deshalb bewerbe ich mich mit grosser Freude um die Stelle als {position} bei {firma}.

{einleitung}

Meine fachlichen und menschlichen Qualifikationen:
{hauptteil}

Bei Ihnen schaetze ich besonders die patientenorientierte Arbeitsweise.

{schluss}

Ueber die Moeglichkeit eines persoenlichen Gespraechs freue ich mich sehr.

Mit freundlichen Gruessen
{name}"""
        },
        {
            "name": "Premium Executive",
            "beschreibung": "Hochwertig fuer Top-Positionen",
            "branche": "Executive",
            "premium": 1,
            "template": """Sehr geehrte Damen und Herren,

mit groesstem Interesse habe ich Ihre Ausschreibung fuer die Position {position} bei {firma} zur Kenntnis genommen.

{einleitung}

Was ich Ihrem Unternehmen biete:
{hauptteil}

Mein bisheriger Karriereweg dokumentiert nachhaltige Erfolge in {erfolg}. Diese Expertise moechte ich gewinnbringend bei {firma} einsetzen.

{schluss}

Ich bin ueberzeugt, dass meine Erfahrung und Vision optimal zu Ihren strategischen Zielen passen. Auf ein persoenliches Kennenlernen freue ich mich.

Mit besten Gruessen
{name}"""
        },
    ]
    
    for v in vorlagen:
        c.execute("""
            INSERT INTO anschreiben_vorlagen 
            (name, beschreibung, template, premium, branche)
            VALUES (?, ?, ?, ?, ?)
        """, (v["name"], v["beschreibung"], v["template"], v["premium"], v["branche"]))
    
    conn.commit()
    conn.close()


# ============================================================
# AVINU KI ANTWORTEN
# ============================================================
def avinu_antwort(frage, kontext=""):
    """Holt eine Antwort von AVINU."""
    if not GROQ_API_KEY:
        return "AVINU ist gerade offline. Bitte versuche es spaeter."
    
    full_frage = frage
    if kontext:
        full_frage = f"Kontext: {kontext}\n\nFrage: {frage}"
    
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
                    {"role": "system", "content": AVINU_PROMPT},
                    {"role": "user", "content": full_frage}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return "AVINU hat ein Problem. Bitte spaeter probieren."
    except Exception:
        return "Verbindung zu AVINU fehlgeschlagen."


# ============================================================
# JOB SUCHE
# ============================================================
BRANCHEN = {
    "it": ["IT", "Informatik", "Software", "Netzwerk", "Programmierer", "Fachinformatiker"],
    "handwerk": ["Handwerk", "Elektriker", "Klempner", "Maurer", "Schreiner", "Mechaniker"],
    "gesundheit": ["Pflege", "Arzt", "Krankenschwester", "Therapeut", "Gesundheit"],
    "verwaltung": ["Verwaltung", "Buero", "Sekretariat", "Sachbearbeiter", "Assistent"],
    "verkauf": ["Verkauf", "Einzelhandel", "Verkaeufer", "Kassierer", "Handel"],
    "logistik": ["Logistik", "Lager", "Lagerist", "Fahrer", "Disponent"],
    "gastronomie": ["Gastronomie", "Koch", "Kellner", "Hotelfach", "Bedienung"],
    "bildung": ["Lehrer", "Erzieher", "Sozialpaedagoge", "Bildung", "Trainer"],
    "marketing": ["Marketing", "Werbung", "Social Media", "PR", "Content"],
    "finanzen": ["Banker", "Buchhaltung", "Finanzen", "Steuerberater", "Controlling"],
}


def jobs_suchen_indeed(suchbegriff, standort, anzahl=10):
    """Sucht Jobs auf Indeed."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        url = f"https://de.indeed.com/jobs?q={suchbegriff}&l={standort}"
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        
        cards = soup.find_all("div", class_=re.compile("job_seen"))[:anzahl]
        
        for card in cards:
            try:
                titel_elem = card.find("h2")
                firma_elem = card.find("span", class_=re.compile("company"))
                ort_elem = card.find("div", class_=re.compile("location"))
                
                if titel_elem and firma_elem:
                    job = {
                        "titel": titel_elem.get_text(strip=True),
                        "firma": firma_elem.get_text(strip=True),
                        "standort": ort_elem.get_text(strip=True) if ort_elem else standort,
                        "quelle": "Indeed",
                        "url": "https://de.indeed.com" + (card.find("a")["href"] if card.find("a") else "")
                    }
                    jobs.append(job)
            except Exception:
                continue
                
    except Exception as e:
        print(f"Indeed Fehler: {e}")
    
    return jobs


def jobs_suchen_arbeitsagentur(suchbegriff, standort, anzahl=10):
    """Sucht Jobs bei Bundesagentur fuer Arbeit."""
    jobs = []
    try:
        url = f"https://www.arbeitsagentur.de/jobsuche/suche?was={suchbegriff}&wo={standort}"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        
        cards = soup.find_all("div", class_=re.compile("jobtile"))[:anzahl]
        
        for card in cards:
            try:
                titel = card.find("h2")
                firma = card.find("p", class_=re.compile("company"))
                
                if titel:
                    job = {
                        "titel": titel.get_text(strip=True),
                        "firma": firma.get_text(strip=True) if firma else "Unbekannt",
                        "standort": standort,
                        "quelle": "Arbeitsagentur",
                        "url": ""
                    }
                    jobs.append(job)
            except Exception:
                continue
                
    except Exception:
        pass
    
    return jobs


def jobs_speichern(user_id, jobs, branche=""):
    """Speichert gefundene Jobs in DB."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    gespeichert = 0
    
    for job in jobs:
        # Duplikat-Check
        c.execute(
            "SELECT id FROM jobs WHERE user_id=? AND firma=? AND position=?",
            (user_id, job.get("firma", ""), job.get("titel", ""))
        )
        if c.fetchone():
            continue
        
        c.execute("""
            INSERT INTO jobs (
                user_id, firma, position, standort, 
                beschreibung, url, branche, quelle, gefunden
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            job.get("firma", ""),
            job.get("titel", ""),
            job.get("standort", ""),
            job.get("beschreibung", ""),
            job.get("url", ""),
            branche,
            job.get("quelle", ""),
            datetime.now().isoformat()
        ))
        gespeichert += 1
    
    conn.commit()
    conn.close()
    return gespeichert


def jobs_laden(user_id, nur_offen=False):
    """Laedt gespeicherte Jobs."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if nur_offen:
        c.execute(
            "SELECT * FROM jobs WHERE user_id=? AND beworben=0 ORDER BY id DESC",
            (user_id,)
        )
    else:
        c.execute(
            "SELECT * FROM jobs WHERE user_id=? ORDER BY id DESC LIMIT 50",
            (user_id,)
        )
    
    rows = c.fetchall()
    conn.close()
    return rows


def vorlagen_laden(premium=False):
    """Laedt Anschreiben-Vorlagen."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if premium:
        c.execute("SELECT * FROM anschreiben_vorlagen ORDER BY premium, name")
    else:
        c.execute("SELECT * FROM anschreiben_vorlagen WHERE premium=0 ORDER BY name")
    
    rows = c.fetchall()
    conn.close()
    return rows


def anschreiben_generieren(job_id, user_id, vorlage_id, user_profil):
    """Generiert ein individuelles Anschreiben mit KI."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Job laden
    c.execute("SELECT * FROM jobs WHERE id=? AND user_id=?", (job_id, user_id))
    job = c.fetchone()
    
    # Vorlage laden
    c.execute("SELECT * FROM anschreiben_vorlagen WHERE id=?", (vorlage_id,))
    vorlage = c.fetchone()
    
    conn.close()
    
    if not job or not vorlage:
        return None
    
    # KI-Prompt erstellen
    prompt = f"""Erstelle ein professionelles Anschreiben fuer:

Firma: {job[2]}
Position: {job[3]}
Standort: {job[4]}
Branche: {job[8]}

Bewerber-Profil:
Name: {user_profil.get('vorname', '')} {user_profil.get('nachname', '')}
Kenntnisse: {user_profil.get('kenntnisse', '')}
Sprachen: {user_profil.get('sprachen', '')}

Vorlage Style: {vorlage[1]}

Erstelle ein vollstaendiges, ueberzeugendes Anschreiben.
Verwende konkrete Bezuege zum Unternehmen.
Maximal 250 Woerter.
Auf Deutsch."""
    
    return avinu_antwort(prompt)


def auto_bewerbung_erstellen(user_id, job_id, anschreiben):
    """Speichert eine Auto-Bewerbung."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("""
        INSERT INTO auto_bewerbungen 
        (user_id, job_id, anschreiben, erstellt_am)
        VALUES (?, ?, ?, ?)
    """, (user_id, job_id, anschreiben, datetime.now().isoformat()))
    
    bewerbung_id = c.lastrowid
    
    # Job als beworben markieren
    c.execute(
        "UPDATE jobs SET beworben=1, bewerbung_datum=? WHERE id=?",
        (datetime.now().isoformat(), job_id)
    )
    
    conn.commit()
    conn.close()
    return bewerbung_id


# Init
avinu_db_init()


if __name__ == "__main__":
    print("AVINU KI Bot - Test")
    print(f"KI: {'ONLINE' if GROQ_API_KEY else 'OFFLINE'}")
    print(f"Branchen: {len(BRANCHEN)}")