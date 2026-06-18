"""
AVINU - KI Job-Such und Bewerbungs-Bot v4.0
- 6 Jobportale
- Umkreissuche 5-200 km
- 200+ Berufe in 14 Branchen
- Auto-Migration der DB
"""
import os
import requests
import json
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
import re
import urllib.parse

DB_NAME = "bewerbungen.db"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ============================================================
# 200+ BERUFE IN 14 BRANCHEN
# ============================================================
BRANCHEN = {
    "it": [
        "IT-Praktikum", "Fachinformatiker Systemintegration",
        "Fachinformatiker Anwendungsentwicklung",
        "IT-Systemadministrator", "Netzwerkadministrator",
        "Softwareentwickler", "Webentwickler",
        "Frontend Developer", "Backend Developer",
        "Full Stack Developer", "DevOps Engineer",
        "Cloud Engineer", "Data Scientist",
        "KI-Engineer", "Cybersecurity Spezialist",
        "IT-Support", "Helpdesk Mitarbeiter",
        "Systemtechniker", "Datenbank Administrator",
        "IT-Projektmanager", "Scrum Master",
        "Python Entwickler", "Java Entwickler",
        "C# Entwickler", "Mobile App Entwickler",
    ],
    "handwerk": [
        "Elektroniker", "Elektriker", "Anlagenmechaniker",
        "Sanitär Heizung Klima", "Klempner",
        "Schreiner", "Tischler", "Zimmerer",
        "Maurer", "Maler und Lackierer",
        "Fliesenleger", "Dachdecker",
        "KFZ-Mechatroniker", "Karosseriebauer",
        "Industriemechaniker", "Werkzeugmechaniker",
        "Metallbauer", "Schweißer",
        "Bäcker", "Konditor", "Fleischer",
        "Friseur", "Kosmetiker",
        "Goldschmied", "Uhrmacher",
    ],
    "gesundheit": [
        "Pflegefachmann", "Pflegefachfrau",
        "Altenpfleger", "Krankenpfleger",
        "Gesundheits- und Krankenpfleger",
        "Medizinischer Fachangestellter",
        "Zahnmedizinischer Fachangestellter",
        "Pharmazeutisch-technischer Assistent",
        "Physiotherapeut", "Ergotherapeut", "Logopäde",
        "Hebamme", "Notfallsanitäter", "Rettungssanitäter",
        "Operationstechnischer Assistent",
        "Anästhesietechnischer Assistent",
        "Heilerziehungspfleger", "Sozialassistent",
        "Diätassistent", "Optiker", "Augenoptiker",
    ],
    "verwaltung": [
        "Kaufmann für Büromanagement",
        "Verwaltungsfachangestellter",
        "Industriekaufmann", "Bürokaufmann",
        "Personalsachbearbeiter", "Personalreferent",
        "HR Manager", "Sachbearbeiter",
        "Sekretär", "Assistent der Geschäftsleitung",
        "Office Manager", "Empfangsmitarbeiter",
        "Datenerfasser", "Buchhalter",
        "Steuerfachangestellter", "Rechtsanwaltsfachangestellter",
        "Notarfachangestellter", "Justizfachangestellter",
        "Sozialversicherungsfachangestellter",
    ],
    "verkauf": [
        "Verkäufer", "Kaufmann im Einzelhandel",
        "Kaufmann im Großhandel",
        "Filialleiter", "Verkaufsleiter",
        "Vertriebsmitarbeiter", "Außendienstmitarbeiter",
        "Account Manager", "Key Account Manager",
        "Sales Manager", "Kundenberater",
        "Kassierer", "Warenverräumer",
        "Drogist", "Buchhändler", "Apotheker",
        "Immobilienmakler", "Versicherungsvertreter",
        "Bankberater", "Finanzberater",
    ],
    "logistik": [
        "Fachlagerist", "Fachkraft für Lagerlogistik",
        "Lagermitarbeiter", "Kommissionierer",
        "Berufskraftfahrer", "LKW-Fahrer", "Auslieferungsfahrer",
        "Speditionskaufmann", "Disponent",
        "Logistikleiter", "Supply Chain Manager",
        "Versandmitarbeiter", "Staplerfahrer",
        "Postbote", "Paketzusteller", "Kurier",
        "Bahnmitarbeiter", "Flugbegleiter",
        "Pilot", "Schiffsführer",
    ],
    "gastronomie": [
        "Koch", "Beikoch", "Küchenhilfe",
        "Restaurantfachmann", "Kellner", "Servicekraft",
        "Barkeeper", "Sommelier",
        "Hotelfachmann", "Hotelmanager",
        "Empfangsmitarbeiter Hotel", "Concierge",
        "Housekeeping", "Zimmermädchen",
        "Eventmanager", "Catering Mitarbeiter",
        "Pizzabäcker", "Patissier", "Restaurantleiter",
    ],
    "bildung": [
        "Erzieher", "Kinderpfleger", "Sozialpädagoge",
        "Sozialarbeiter", "Heilpädagoge",
        "Grundschullehrer", "Gymnasiallehrer",
        "Berufsschullehrer", "Förderschullehrer",
        "Dozent", "Trainer", "Coach",
        "Bibliothekar", "Museumspädagoge",
        "Tagesmutter", "Au-pair",
        "Sportlehrer", "Musiklehrer",
        "Sprachlehrer", "Nachhilfelehrer",
    ],
    "marketing": [
        "Marketing Manager", "Online Marketing Manager",
        "Social Media Manager", "Content Manager",
        "SEO Spezialist", "SEA Spezialist",
        "Performance Marketing Manager",
        "Brand Manager", "Product Manager",
        "Copywriter", "Texter", "Redakteur",
        "Grafikdesigner", "UI/UX Designer",
        "Webdesigner", "Mediengestalter",
        "Fotograf", "Videograf", "Cutter",
        "PR Manager", "Eventmanager",
    ],
    "finanzen": [
        "Bankkaufmann", "Sparkassenkaufmann",
        "Investmentbanker", "Finanzberater",
        "Anlageberater", "Vermögensberater",
        "Versicherungskaufmann", "Versicherungsmakler",
        "Steuerberater", "Wirtschaftsprüfer",
        "Buchhalter", "Bilanzbuchhalter",
        "Controller", "Finanzanalyst",
        "Risikomanager", "Treasury Manager",
        "Kreditberater", "Immobilienfinanzierer",
        "Rentenberater", "Versicherungsmathematiker",
    ],
    "transport": [
        "LKW-Fahrer", "Busfahrer", "Taxifahrer",
        "Berufskraftfahrer", "Auslieferungsfahrer",
        "Spediteur", "Disponent",
        "Logistiker", "Versandmitarbeiter",
        "Hafenarbeiter", "Bahnmitarbeiter",
    ],
    "produktion": [
        "Produktionsmitarbeiter", "Maschinenbediener",
        "Industriemechaniker", "Verfahrensmechaniker",
        "Fertigungstechniker", "Qualitätskontrolleur",
        "Werker", "Helfer Produktion",
        "Schichtleiter", "Produktionsleiter",
        "CNC-Fräser", "Zerspanungsmechaniker",
    ],
    "reinigung": [
        "Reinigungskraft", "Gebäudereiniger",
        "Hausmeister", "Facility Manager",
        "Glasreiniger", "Industriereiniger",
        "Hotelreinigung", "Krankenhausreiniger",
    ],
    "sicherheit": [
        "Sicherheitsmitarbeiter", "Wachmann",
        "Pförtner", "Werkschutz",
        "Personenschützer", "Geldtransporter",
        "Detektiv", "Polizist",
    ],
}


# ============================================================
# DATENBANK MIT AUTO-MIGRATION
# ============================================================
def avinu_db_init():
    """Erstellt Tabellen und migriert alte DBs."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # JOBS Tabelle
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
            bewerbung_datum TEXT,
            favorit INTEGER DEFAULT 0,
            entfernung INTEGER DEFAULT 0
        )
    """)
    
    # MIGRATION: Spalten hinzufügen falls fehlen
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN favorit INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Spalte existiert bereits
    
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN entfernung INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    
    try:
        c.execute("ALTER TABLE jobs ADD COLUMN bewerbung_datum TEXT")
    except sqlite3.OperationalError:
        pass
    
    # VORLAGEN Tabelle
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
    
    # AUTO-BEWERBUNGEN
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
    standard_vorlagen_einfuegen()
    conn.close()


def standard_vorlagen_einfuegen():
    """10 Premium Vorlagen."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM anschreiben_vorlagen")
    if c.fetchone()[0] > 0:
        conn.close()
        return
    
    vorlagen = [
        ("Klassisch Professionell", "Klassische Bewerbung", 0, "Alle",
         "Sehr geehrte Damen und Herren,\n\nmit Interesse habe ich Ihre Stellenanzeige als {position} bei {firma} gelesen.\n\nMit freundlichen Gruessen\n{name}"),
        ("Modern & Dynamisch", "Moderner Stil", 1, "IT, Marketing",
         "Hallo {ansprechpartner},\n\nIhre Stellenanzeige fuer {position} hat mich begeistert!\n\nBeste Gruesse\n{name}"),
        ("Berufseinstieg", "Fuer Anfaenger", 0, "Alle",
         "Sehr geehrte Damen und Herren,\n\nmit Begeisterung bewerbe ich mich als {position}.\n\nMit freundlichen Gruessen\n{name}"),
        ("IT Spezialist", "Fuer IT-Jobs", 1, "IT",
         "Sehr geehrte Damen und Herren,\n\nals {position} bewerbe ich mich bei {firma}.\n\nMit freundlichen Gruessen\n{name}"),
        ("Karrierewechsel", "Fuer Branchenwechsler", 1, "Alle",
         "Sehr geehrte Damen und Herren,\n\nNeue Herausforderungen schaffen Mehrwert.\n\nMit freundlichen Gruessen\n{name}"),
        ("Handwerk Praktisch", "Fuer Handwerker", 0, "Handwerk",
         "Sehr geehrte Damen und Herren,\n\nmit Interesse bewerbe ich mich als {position}.\n\nMit freundlichen Gruessen\n{name}"),
        ("Gesundheit & Pflege", "Fuer Pflegeberufe", 1, "Gesundheit",
         "Sehr geehrte Damen und Herren,\n\nMenschen helfen ist meine Berufung.\n\nMit freundlichen Gruessen\n{name}"),
        ("Fuehrungskraft", "Fuer Manager", 1, "Management",
         "Sehr geehrte Damen und Herren,\n\nmit Fuehrungserfahrung bewerbe ich mich.\n\nMit besten Gruessen\n{name}"),
        ("Kreativ & Originell", "Kreativbranche", 1, "Marketing",
         "Hallo {firma}-Team!\n\nIhre Stellenanzeige hat mich begeistert!\n\nKreative Gruesse\n{name}"),
        ("Premium Executive", "Top-Positionen", 1, "Executive",
         "Sehr geehrte Damen und Herren,\n\nmit groesstem Interesse habe ich Ihre Ausschreibung gelesen.\n\nMit besten Gruessen\n{name}"),
    ]
    
    for v in vorlagen:
        c.execute("""
            INSERT INTO anschreiben_vorlagen 
            (name, beschreibung, premium, branche, template)
            VALUES (?, ?, ?, ?, ?)
        """, v)
    
    conn.commit()
    conn.close()


# ============================================================
# AVINU KI
# ============================================================
AVINU_PROMPT = """Du bist AVINU, KI-Job-Experte.
Hilf bei Jobsuche in ALLEN Branchen.
Antworte auf Deutsch in 3-5 Saetzen."""


def avinu_antwort(frage):
    if not GROQ_API_KEY:
        return "AVINU offline."
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
                    {"role": "user", "content": frage}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return "Fehler bei AVINU."
    except Exception:
        return "Verbindung fehlgeschlagen."


# ============================================================
# JOB-SUCHE - 6 PORTALE
# ============================================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def jobs_suchen_indeed(suchbegriff, standort, radius=25, anzahl=15):
    """Indeed mit Umkreissuche."""
    jobs = []
    try:
        q = urllib.parse.quote(suchbegriff)
        l = urllib.parse.quote(standort)
        url = f"https://de.indeed.com/jobs?q={q}&l={l}&radius={radius}"
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        
        cards = (soup.find_all("div", class_=re.compile("job_seen_beacon")) or
                 soup.find_all("div", class_=re.compile("jobsearch-SerpJobCard")) or
                 soup.find_all("a", class_=re.compile("tapItem")))
        
        for card in cards[:anzahl]:
            try:
                titel = ""
                titel_elem = card.find("h2") or card.find("a", {"data-jk": True})
                if titel_elem:
                    titel = titel_elem.get_text(strip=True)
                
                firma = "Unbekannt"
                firma_elem = (card.find("span", class_=re.compile("companyName")) or
                              card.find("div", class_=re.compile("company")))
                if firma_elem:
                    firma = firma_elem.get_text(strip=True)
                
                ort = standort
                ort_elem = card.find("div", class_=re.compile("companyLocation"))
                if ort_elem:
                    ort = ort_elem.get_text(strip=True)
                
                beschreibung = ""
                desc_elem = card.find("div", class_=re.compile("job-snippet"))
                if desc_elem:
                    beschreibung = desc_elem.get_text(strip=True)[:300]
                
                link = ""
                link_elem = card.find("a", href=True)
                if link_elem:
                    href = link_elem.get("href", "")
                    if href.startswith("/"):
                        link = "https://de.indeed.com" + href
                    else:
                        link = href
                
                if titel:
                    jobs.append({
                        "titel": titel, "firma": firma,
                        "standort": ort, "beschreibung": beschreibung,
                        "url": link, "quelle": "Indeed"
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"Indeed Fehler: {e}")
    
    return jobs


def jobs_suchen_arbeitsagentur(suchbegriff, standort, radius=25, anzahl=15):
    """Arbeitsagentur offizielle API."""
    jobs = []
    try:
        url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
        params = {
            "was": suchbegriff,
            "wo": standort,
            "umkreis": radius,
            "size": anzahl
        }
        headers = {
            "X-API-Key": "jobboerse-jobsuche",
            "User-Agent": HEADERS["User-Agent"]
        }
        
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for stellen in data.get("stellenangebote", [])[:anzahl]:
                try:
                    arbeitsort = stellen.get("arbeitsort", {})
                    ort = arbeitsort.get("ort", standort) if isinstance(arbeitsort, dict) else standort
                    
                    jobs.append({
                        "titel": stellen.get("titel", ""),
                        "firma": stellen.get("arbeitgeber", "Unbekannt"),
                        "standort": ort,
                        "beschreibung": stellen.get("beruf", "")[:300],
                        "url": f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{stellen.get('refnr', '')}",
                        "quelle": "Arbeitsagentur"
                    })
                except Exception:
                    continue
    except Exception as e:
        print(f"Arbeitsagentur Fehler: {e}")
    
    return jobs


def jobs_suchen_stepstone(suchbegriff, standort, radius=25, anzahl=10):
    """StepStone."""
    jobs = []
    try:
        q = urllib.parse.quote(suchbegriff)
        l = urllib.parse.quote(standort)
        url = f"https://www.stepstone.de/jobs/{q}/in-{l}"
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        
        articles = soup.find_all("article")[:anzahl]
        
        for art in articles:
            try:
                titel = ""
                titel_elem = art.find(["h2", "h3"])
                if titel_elem:
                    titel = titel_elem.get_text(strip=True)
                
                firma = "Unbekannt"
                firma_elem = art.find("span", class_=re.compile("company"))
                if firma_elem:
                    firma = firma_elem.get_text(strip=True)
                
                link = ""
                link_elem = art.find("a", href=True)
                if link_elem:
                    link = "https://www.stepstone.de" + link_elem["href"]
                
                if titel:
                    jobs.append({
                        "titel": titel, "firma": firma,
                        "standort": standort, "beschreibung": "",
                        "url": link, "quelle": "StepStone"
                    })
            except Exception:
                continue
    except Exception:
        pass
    
    return jobs


def jobs_suchen_xing(suchbegriff, standort, anzahl=10):
    """XING."""
    jobs = []
    try:
        q = urllib.parse.quote(suchbegriff)
        l = urllib.parse.quote(standort)
        url = f"https://www.xing.com/jobs/search?keywords={q}&location={l}"
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        
        cards = soup.find_all("article")[:anzahl]
        
        for card in cards:
            try:
                titel = card.find(["h2", "h3", "a"])
                if titel:
                    jobs.append({
                        "titel": titel.get_text(strip=True),
                        "firma": "via XING",
                        "standort": standort,
                        "beschreibung": "",
                        "url": "https://www.xing.com/jobs",
                        "quelle": "XING"
                    })
            except Exception:
                continue
    except Exception:
        pass
    
    return jobs


def jobs_suchen_meinestadt(suchbegriff, standort, anzahl=10):
    """meinestadt.de."""
    jobs = []
    try:
        q = urllib.parse.quote(suchbegriff)
        l = urllib.parse.quote(standort.lower())
        url = f"https://jobs.meinestadt.de/{l}/suche?words={q}"
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        
        cards = soup.find_all("article")[:anzahl]
        
        for card in cards:
            try:
                titel_elem = card.find(["h2", "h3"])
                if titel_elem:
                    jobs.append({
                        "titel": titel_elem.get_text(strip=True),
                        "firma": "Lokal",
                        "standort": standort,
                        "beschreibung": "",
                        "url": "https://jobs.meinestadt.de",
                        "quelle": "meinestadt"
                    })
            except Exception:
                continue
    except Exception:
        pass
    
    return jobs


def jobs_suchen_kimeta(suchbegriff, standort, anzahl=10):
    """Kimeta."""
    jobs = []
    try:
        q = urllib.parse.quote(suchbegriff)
        l = urllib.parse.quote(standort)
        url = f"https://www.kimeta.de/stellenangebote/jobs?q={q}&loc={l}"
        
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        
        cards = soup.find_all("article")[:anzahl]
        
        for card in cards:
            try:
                titel_elem = card.find(["h2", "h3"])
                if titel_elem:
                    jobs.append({
                        "titel": titel_elem.get_text(strip=True),
                        "firma": "via Kimeta",
                        "standort": standort,
                        "beschreibung": "",
                        "url": "https://www.kimeta.de",
                        "quelle": "Kimeta"
                    })
            except Exception:
                continue
    except Exception:
        pass
    
    return jobs


def alle_jobs_suchen(suchbegriff, standort, radius=25):
    """Sucht in ALLEN Portalen."""
    alle_jobs = []
    
    # Alle Portale durchsuchen
    portale = [
        (jobs_suchen_indeed, [suchbegriff, standort, radius, 15]),
        (jobs_suchen_arbeitsagentur, [suchbegriff, standort, radius, 15]),
        (jobs_suchen_stepstone, [suchbegriff, standort, radius, 10]),
        (jobs_suchen_xing, [suchbegriff, standort, 10]),
        (jobs_suchen_meinestadt, [suchbegriff, standort, 10]),
        (jobs_suchen_kimeta, [suchbegriff, standort, 10]),
    ]
    
    for func, args in portale:
        try:
            jobs = func(*args)
            alle_jobs.extend(jobs)
        except Exception as e:
            print(f"Portal Fehler ({func.__name__}): {e}")
    
    return alle_jobs


def jobs_speichern(user_id, jobs, branche="", radius=25):
    """Speichert Jobs in DB."""
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
        
        try:
            c.execute("""
                INSERT INTO jobs (
                    user_id, firma, position, standort, beschreibung,
                    url, branche, quelle, gefunden, entfernung, favorit, beworben
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
            """, (
                user_id, job.get("firma", ""), job.get("titel", ""),
                job.get("standort", ""), job.get("beschreibung", ""),
                job.get("url", ""), branche, job.get("quelle", ""),
                datetime.now().isoformat(), radius
            ))
            gespeichert += 1
        except Exception as e:
            print(f"Insert Fehler: {e}")
            continue
    
    conn.commit()
    conn.close()
    return gespeichert


def jobs_laden(user_id, filter_typ="alle"):
    """Laedt Jobs mit Filter."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        if filter_typ == "offen":
            c.execute("SELECT * FROM jobs WHERE user_id=? AND beworben=0 ORDER BY id DESC", (user_id,))
        elif filter_typ == "beworben":
            c.execute("SELECT * FROM jobs WHERE user_id=? AND beworben=1 ORDER BY id DESC", (user_id,))
        elif filter_typ == "favoriten":
            c.execute("SELECT * FROM jobs WHERE user_id=? AND favorit=1 ORDER BY id DESC", (user_id,))
        else:
            c.execute("SELECT * FROM jobs WHERE user_id=? ORDER BY id DESC LIMIT 100", (user_id,))
        
        rows = c.fetchall()
    except Exception:
        rows = []
    
    conn.close()
    return rows


def job_favorit_toggle(job_id, user_id):
    """Toggle Favorit."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("SELECT favorit FROM jobs WHERE id=? AND user_id=?", (job_id, user_id))
        r = c.fetchone()
        if r:
            new_val = 0 if r[0] else 1
            c.execute("UPDATE jobs SET favorit=? WHERE id=?", (new_val, job_id))
            conn.commit()
    except Exception:
        pass
    conn.close()


def job_loeschen(job_id, user_id):
    """Loescht Job."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM jobs WHERE id=? AND user_id=?", (job_id, user_id))
    conn.commit()
    conn.close()


def vorlagen_laden(premium=False):
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
    """KI-Anschreiben generieren."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE id=? AND user_id=?", (job_id, user_id))
    job = c.fetchone()
    c.execute("SELECT * FROM anschreiben_vorlagen WHERE id=?", (vorlage_id,))
    vorlage = c.fetchone()
    conn.close()
    
    if not job or not vorlage:
        return None
    
    prompt = f"""Erstelle professionelles Anschreiben fuer:

Firma: {job[2]}
Position: {job[3]}
Standort: {job[4]}
Branche: {job[8]}

Bewerber:
Name: {user_profil.get('vorname', '')} {user_profil.get('nachname', '')}
Adresse: {user_profil.get('strasse', '')}, {user_profil.get('plz', '')} {user_profil.get('stadt', '')}
E-Mail: {user_profil.get('email', '')}
Telefon: {user_profil.get('telefon', '')}
Kenntnisse: {user_profil.get('kenntnisse', '')}
Sprachen: {user_profil.get('sprachen', '')}

Style: {vorlage[2]}

Erstelle vollstaendiges Anschreiben mit:
- Anrede
- Einleitung mit Bezug zur Firma
- Hauptteil mit Qualifikationen
- Abschluss mit Gespraechswunsch
- Mit freundlichen Gruessen + Name

Max 300 Woerter. Deutsch."""
    
    return avinu_antwort(prompt)


def auto_bewerbung_erstellen(user_id, job_id, anschreiben):
    """Speichert Auto-Bewerbung."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO auto_bewerbungen (user_id, job_id, anschreiben, erstellt_am)
        VALUES (?, ?, ?, ?)
    """, (user_id, job_id, anschreiben, datetime.now().isoformat()))
    bewerbung_id = c.lastrowid
    
    try:
        c.execute("UPDATE jobs SET beworben=1, bewerbung_datum=? WHERE id=?",
                  (datetime.now().isoformat(), job_id))
    except Exception:
        c.execute("UPDATE jobs SET beworben=1 WHERE id=?", (job_id,))
    
    conn.commit()
    conn.close()
    return bewerbung_id


def get_alle_berufe():
    """Alle Berufe alphabetisch."""
    alle = []
    for berufe in BRANCHEN.values():
        alle.extend(berufe)
    return sorted(set(alle))


# Init beim Import
avinu_db_init()