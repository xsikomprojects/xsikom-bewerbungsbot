"""
AVINU - Global Job Bot v6.0
- 15+ Jobportale weltweit
- Deutschland + Europa + USA + Afrika + Asien + Australien
- 300+ Berufe in 14 Branchen
- Multi-Language Support
- IT-Fachtechniker, Netzwerktechniker und mehr
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
# 300+ BERUFE IN 14 BRANCHEN
# ============================================================
BRANCHEN = {
    "it": [
        "IT-Praktikum",
        "IT-Fachtechniker",
        "IT-Netzwerktechniker",
        "IT-Techniker",
        "IT-Systemtechniker",
        "Fachinformatiker Systemintegration",
        "Fachinformatiker Anwendungsentwicklung",
        "Fachinformatiker Daten- und Prozessanalyse",
        "Fachinformatiker Digitale Vernetzung",
        "IT-Systemadministrator",
        "Netzwerkadministrator",
        "Netzwerkingenieur",
        "Systemingenieur",
        "Softwareentwickler",
        "Software Engineer",
        "Webentwickler",
        "Frontend Developer",
        "Backend Developer",
        "Full Stack Developer",
        "DevOps Engineer",
        "Cloud Engineer",
        "Cloud Architect",
        "Data Scientist",
        "Data Engineer",
        "Data Analyst",
        "KI Engineer",
        "Machine Learning Engineer",
        "Cybersecurity Spezialist",
        "Penetration Tester",
        "IT-Sicherheitsbeauftragter",
        "IT-Support",
        "Helpdesk Mitarbeiter",
        "1st Level Support",
        "2nd Level Support",
        "3rd Level Support",
        "Datenbank Administrator",
        "Database Administrator",
        "IT-Projektmanager",
        "IT-Consultant",
        "Scrum Master",
        "Product Owner",
        "Python Entwickler",
        "Java Entwickler",
        "C# Entwickler",
        "JavaScript Entwickler",
        "PHP Entwickler",
        "Ruby Developer",
        "Mobile App Entwickler",
        "iOS Developer",
        "Android Developer",
        "Game Developer",
        "Blockchain Developer",
        "AR/VR Developer",
        "QA Tester",
        "Test Engineer",
        "Technical Writer",
        "IT-Trainer",
        "SAP Berater",
        "Salesforce Consultant",
    ],
    "handwerk": [
        "Elektroniker", "Elektriker", "Elektrotechniker",
        "Anlagenmechaniker", "Sanitär Heizung Klima",
        "Klempner", "Schreiner", "Tischler", "Zimmerer",
        "Maurer", "Bauarbeiter", "Stuckateur",
        "Maler und Lackierer", "Fliesenleger", "Dachdecker",
        "KFZ-Mechatroniker", "KFZ-Mechaniker",
        "Karosseriebauer", "Lackierer",
        "Industriemechaniker", "Werkzeugmechaniker",
        "Metallbauer", "Schlosser", "Schweißer",
        "Bäcker", "Konditor", "Fleischer", "Metzger",
        "Friseur", "Barbier", "Kosmetiker", "Nageldesigner",
        "Goldschmied", "Uhrmacher", "Schuhmacher",
        "Schneider", "Polsterer", "Glaser",
        "Gärtner", "Landschaftsgärtner", "Florist",
    ],
    "gesundheit": [
        "Pflegefachmann", "Pflegefachfrau",
        "Altenpfleger", "Altenpflegerin",
        "Krankenpfleger", "Krankenpflegerin",
        "Gesundheits- und Krankenpfleger",
        "Medizinischer Fachangestellter MFA",
        "Zahnmedizinischer Fachangestellter ZFA",
        "Pharmazeutisch-technischer Assistent PTA",
        "Apotheker", "Apothekenhelfer",
        "Physiotherapeut", "Ergotherapeut", "Logopäde",
        "Hebamme", "Entbindungspfleger",
        "Notfallsanitäter", "Rettungssanitäter",
        "Rettungsassistent",
        "Operationstechnischer Assistent OTA",
        "Anästhesietechnischer Assistent ATA",
        "Heilerziehungspfleger", "Sozialassistent",
        "Diätassistent", "Ernährungsberater",
        "Optiker", "Augenoptiker", "Hörakustiker",
        "Masseur", "Heilpraktiker",
        "Psychotherapeut", "Psychologe",
        "Arzt", "Ärztin", "Zahnarzt",
        "Tierarzt", "Tiermedizinischer Fachangestellter",
    ],
    "verwaltung": [
        "Kaufmann für Büromanagement",
        "Kauffrau für Büromanagement",
        "Verwaltungsfachangestellter",
        "Industriekaufmann", "Bürokaufmann",
        "Personalsachbearbeiter", "Personalreferent",
        "HR Manager", "HR Business Partner",
        "Sachbearbeiter", "Sachbearbeiterin",
        "Sekretär", "Sekretärin",
        "Assistent der Geschäftsleitung",
        "Office Manager", "Empfangsmitarbeiter",
        "Datenerfasser", "Buchhalter", "Buchhalterin",
        "Steuerfachangestellter", "Steuerberater",
        "Rechtsanwaltsfachangestellter", "Anwalt",
        "Notarfachangestellter", "Notar",
        "Justizfachangestellter",
        "Sozialversicherungsfachangestellter",
        "Bankkaufmann", "Versicherungskaufmann",
    ],
    "verkauf": [
        "Verkäufer", "Verkäuferin",
        "Kaufmann im Einzelhandel",
        "Kaufmann im Großhandel",
        "Filialleiter", "Filialleiterin",
        "Verkaufsleiter", "Verkaufsleiterin",
        "Vertriebsmitarbeiter", "Außendienstmitarbeiter",
        "Account Manager", "Key Account Manager",
        "Sales Manager", "Sales Representative",
        "Business Development Manager",
        "Kundenberater", "Kundenbetreuer",
        "Kassierer", "Kassiererin",
        "Warenverräumer", "Lagerist",
        "Drogist", "Buchhändler", "Apotheker",
        "Immobilienmakler", "Immobilienberater",
        "Versicherungsvertreter", "Versicherungsmakler",
        "Bankberater", "Finanzberater",
        "Anlageberater", "Vermögensberater",
    ],
    "logistik": [
        "Fachlagerist", "Fachkraft für Lagerlogistik",
        "Lagermitarbeiter", "Lagerhelfer", "Kommissionierer",
        "Berufskraftfahrer", "LKW-Fahrer", "Truck Driver",
        "Auslieferungsfahrer", "Lieferfahrer",
        "Speditionskaufmann", "Disponent",
        "Logistikleiter", "Supply Chain Manager",
        "Logistik Manager", "Transport Manager",
        "Versandmitarbeiter", "Staplerfahrer",
        "Postbote", "Paketzusteller", "Kurier",
        "Bahnmitarbeiter", "Flugbegleiter",
        "Pilot", "Co-Pilot", "Schiffsführer",
        "Zollabfertiger", "Frachtagent",
    ],
    "gastronomie": [
        "Koch", "Köchin", "Chefkoch", "Sous Chef",
        "Beikoch", "Küchenhilfe", "Spüler",
        "Restaurantfachmann", "Kellner", "Servicekraft",
        "Barkeeper", "Bartender", "Sommelier",
        "Hotelfachmann", "Hotelfachfrau",
        "Hotelmanager", "Hoteldirektor",
        "Empfangsmitarbeiter Hotel", "Concierge",
        "Housekeeping", "Zimmermädchen",
        "Eventmanager", "Veranstaltungskaufmann",
        "Catering Mitarbeiter", "Pizzabäcker",
        "Patissier", "Restaurantleiter",
        "Restaurantmanager", "F&B Manager",
    ],
    "bildung": [
        "Erzieher", "Erzieherin", "Kinderpfleger",
        "Sozialpädagoge", "Sozialarbeiter",
        "Heilpädagoge", "Heilerziehungspfleger",
        "Grundschullehrer", "Gymnasiallehrer",
        "Realschullehrer", "Berufsschullehrer",
        "Förderschullehrer", "Sonderpädagoge",
        "Dozent", "Trainer", "Coach",
        "Bibliothekar", "Museumspädagoge",
        "Tagesmutter", "Tagesvater", "Au-pair",
        "Sportlehrer", "Musiklehrer",
        "Sprachlehrer", "Nachhilfelehrer",
        "Schulleiter", "Universitätsprofessor",
        "Wissenschaftlicher Mitarbeiter",
    ],
    "marketing": [
        "Marketing Manager", "Marketing Specialist",
        "Online Marketing Manager", "Digital Marketing Manager",
        "Social Media Manager", "Content Manager",
        "SEO Spezialist", "SEA Spezialist",
        "Performance Marketing Manager",
        "Brand Manager", "Product Manager",
        "Product Marketing Manager",
        "Copywriter", "Texter", "Redakteur",
        "Journalist", "Lektor",
        "Grafikdesigner", "UI/UX Designer",
        "Webdesigner", "Mediengestalter",
        "Art Director", "Creative Director",
        "Fotograf", "Videograf", "Cutter",
        "PR Manager", "PR Berater",
        "Eventmanager", "Influencer Marketing Manager",
        "Community Manager", "Affiliate Manager",
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
        "Aktuar", "Quantitative Analyst",
        "Hedgefonds Manager", "Portfolio Manager",
    ],
    "transport": [
        "LKW-Fahrer", "Busfahrer", "Taxifahrer",
        "Uber Driver", "Berufskraftfahrer",
        "Auslieferungsfahrer", "Lieferdienst Fahrer",
        "Spediteur", "Disponent",
        "Logistiker", "Versandmitarbeiter",
        "Hafenarbeiter", "Bahnmitarbeiter",
        "Lokführer", "Zugbegleiter",
        "Pilot", "Flugbegleiter", "Steward",
    ],
    "produktion": [
        "Produktionsmitarbeiter", "Maschinenbediener",
        "Industriemechaniker", "Verfahrensmechaniker",
        "Fertigungstechniker", "Qualitätskontrolleur",
        "Werker", "Helfer Produktion",
        "Schichtleiter", "Produktionsleiter",
        "CNC-Fräser", "Zerspanungsmechaniker",
        "Anlagenführer", "Maschinenführer",
    ],
    "reinigung": [
        "Reinigungskraft", "Gebäudereiniger",
        "Hausmeister", "Facility Manager",
        "Glasreiniger", "Industriereiniger",
        "Hotelreinigung", "Krankenhausreiniger",
        "Büroreinigung", "Tatortreiniger",
    ],
    "sicherheit": [
        "Sicherheitsmitarbeiter", "Wachmann",
        "Pförtner", "Werkschutz",
        "Personenschützer", "Bodyguard",
        "Geldtransporter", "Detektiv",
        "Polizist", "Feuerwehrmann",
        "Rettungsschwimmer", "Türsteher",
    ],
}


# ============================================================
# DATENBANK
# ============================================================
def avinu_db_init():
    """Tabellen mit Auto-Migration."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, firma TEXT, position TEXT,
            standort TEXT, beschreibung TEXT, url TEXT, email TEXT,
            branche TEXT, quelle TEXT, gefunden TEXT,
            beworben INTEGER DEFAULT 0, bewerbung_datum TEXT,
            favorit INTEGER DEFAULT 0, entfernung INTEGER DEFAULT 0,
            land TEXT DEFAULT 'DE', gehalt TEXT
        )
    """)
    
    # Migration
    for m in [
        "ALTER TABLE jobs ADD COLUMN favorit INTEGER DEFAULT 0",
        "ALTER TABLE jobs ADD COLUMN entfernung INTEGER DEFAULT 0",
        "ALTER TABLE jobs ADD COLUMN bewerbung_datum TEXT",
        "ALTER TABLE jobs ADD COLUMN land TEXT DEFAULT 'DE'",
        "ALTER TABLE jobs ADD COLUMN gehalt TEXT",
    ]:
        try:
            c.execute(m)
        except sqlite3.OperationalError:
            pass
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS anschreiben_vorlagen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, beschreibung TEXT, template TEXT,
            premium INTEGER DEFAULT 0, branche TEXT,
            sprache TEXT DEFAULT 'de'
        )
    """)
    
    try:
        c.execute("ALTER TABLE anschreiben_vorlagen ADD COLUMN sprache TEXT DEFAULT 'de'")
    except sqlite3.OperationalError:
        pass
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS auto_bewerbungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, job_id INTEGER, anschreiben TEXT,
            status TEXT DEFAULT 'erstellt', gesendet TEXT,
            empfaenger TEXT, erstellt_am TEXT, sprache TEXT DEFAULT 'de'
        )
    """)
    
    conn.commit()
    standard_vorlagen_einfuegen()
    conn.close()


def standard_vorlagen_einfuegen():
    """10 Vorlagen in DE + EN."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM anschreiben_vorlagen")
    if c.fetchone()[0] > 0:
        conn.close()
        return
    
    vorlagen = [
        # DEUTSCH
        ("Klassisch DE", "Klassische Bewerbung", 0, "Alle", "de",
         "Sehr geehrte Damen und Herren,\n\nmit Interesse bewerbe ich mich als {position}.\n\nMit freundlichen Gruessen\n{name}"),
        ("Modern DE", "Moderner Stil", 1, "IT", "de",
         "Hallo!\n\nIhre Stellenanzeige fuer {position} hat mich begeistert!\n\nBeste Gruesse\n{name}"),
        ("IT Spezialist DE", "IT-Jobs", 1, "IT", "de",
         "Sehr geehrte Damen und Herren,\n\nals {position} bewerbe ich mich.\n\nMit freundlichen Gruessen\n{name}"),
        ("Handwerk DE", "Handwerker", 0, "Handwerk", "de",
         "Sehr geehrte Damen und Herren,\n\nmit Interesse bewerbe ich mich als {position}.\n\nMit freundlichen Gruessen\n{name}"),
        ("Pflege DE", "Gesundheit", 1, "Gesundheit", "de",
         "Sehr geehrte Damen und Herren,\n\nMenschen helfen ist meine Berufung.\n\nMit freundlichen Gruessen\n{name}"),
        
        # ENGLISH
        ("Classic EN", "Classic application", 0, "All", "en",
         "Dear Sir or Madam,\n\nI am writing to apply for the position of {position}.\n\nBest regards,\n{name}"),
        ("Modern EN", "Modern style", 1, "IT", "en",
         "Hello!\n\nYour job posting for {position} caught my attention!\n\nBest regards,\n{name}"),
        ("Tech Specialist EN", "Tech jobs", 1, "IT", "en",
         "Dear Hiring Manager,\n\nI am excited to apply for the {position} position.\n\nSincerely,\n{name}"),
        
        # FRANCAIS
        ("Classique FR", "Candidature classique", 0, "Tous", "fr",
         "Madame, Monsieur,\n\nJe vous adresse ma candidature pour le poste de {position}.\n\nCordialement,\n{name}"),
        
        # ESPANOL
        ("Clasica ES", "Solicitud clasica", 0, "Todos", "es",
         "Estimados senores,\n\nMe dirijo a ustedes para solicitar el puesto de {position}.\n\nAtentamente,\n{name}"),
    ]
    
    for v in vorlagen:
        c.execute("""INSERT INTO anschreiben_vorlagen 
            (name, beschreibung, premium, branche, sprache, template)
            VALUES (?, ?, ?, ?, ?, ?)""", v)
    
    conn.commit()
    conn.close()


# ============================================================
# AVINU KI
# ============================================================
def avinu_antwort(frage):
    if not GROQ_API_KEY:
        return "AVINU offline."
    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "Du bist AVINU, globaler Job-Experte fuer alle Laender. Antworte mehrsprachig."},
                    {"role": "user", "content": frage}
                ],
                "temperature": 0.7, "max_tokens": 1000
            },
            timeout=15
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return "Fehler."
    except Exception:
        return "Verbindung fehlgeschlagen."


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}


# ============================================================
# JOB-SUCHE - DEUTSCHLAND
# ============================================================
def jobs_arbeitsagentur(suchbegriff, standort, radius=25, anzahl=20):
    """Deutschland - Arbeitsagentur API (SCHNELLSTE!)."""
    jobs = []
    try:
        url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
        params = {"was": suchbegriff, "wo": standort, "umkreis": radius, "size": anzahl}
        headers = {"X-API-Key": "jobboerse-jobsuche", "User-Agent": HEADERS["User-Agent"]}
        
        r = requests.get(url, params=params, headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            for s in data.get("stellenangebote", [])[:anzahl]:
                try:
                    ao = s.get("arbeitsort", {})
                    ort = ao.get("ort", standort) if isinstance(ao, dict) else standort
                    jobs.append({
                        "titel": s.get("titel", ""),
                        "firma": s.get("arbeitgeber", "Unbekannt"),
                        "standort": ort,
                        "beschreibung": s.get("beruf", "")[:300],
                        "url": f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{s.get('refnr', '')}",
                        "quelle": "Arbeitsagentur",
                        "land": "DE"
                    })
                except Exception:
                    continue
    except Exception as e:
        print(f"Arbeitsagentur: {e}")
    return jobs


def jobs_indeed(suchbegriff, standort, radius=25, land="de", anzahl=15):
    """Indeed (Deutschland, USA, UK, etc.)."""
    jobs = []
    try:
        q = urllib.parse.quote(suchbegriff)
        l = urllib.parse.quote(standort)
        
        # Verschiedene Indeed-Domains
        domains = {
            "de": "de.indeed.com",
            "us": "www.indeed.com",
            "uk": "uk.indeed.com",
            "fr": "fr.indeed.com",
            "es": "es.indeed.com",
            "it": "it.indeed.com",
            "ca": "ca.indeed.com",
            "au": "au.indeed.com",
            "in": "in.indeed.com",
            "za": "za.indeed.com",
        }
        domain = domains.get(land.lower(), "de.indeed.com")
        url = f"https://{domain}/jobs?q={q}&l={l}&radius={radius}"
        
        r = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        
        cards = (soup.find_all("div", class_=re.compile("job_seen_beacon")) or
                 soup.find_all("a", class_=re.compile("tapItem")))
        
        for card in cards[:anzahl]:
            try:
                te = card.find("h2") or card.find("a", {"data-jk": True})
                titel = te.get_text(strip=True) if te else ""
                fe = card.find("span", class_=re.compile("companyName"))
                firma = fe.get_text(strip=True) if fe else "Unbekannt"
                oe = card.find("div", class_=re.compile("companyLocation"))
                ort = oe.get_text(strip=True) if oe else standort
                de = card.find("div", class_=re.compile("job-snippet"))
                beschr = de.get_text(strip=True)[:300] if de else ""
                
                link = ""
                le = card.find("a", href=True)
                if le:
                    h = le.get("href", "")
                    link = f"https://{domain}" + h if h.startswith("/") else h
                
                if titel:
                    jobs.append({
                        "titel": titel, "firma": firma, "standort": ort,
                        "beschreibung": beschr, "url": link,
                        "quelle": f"Indeed {land.upper()}", "land": land.upper()
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"Indeed {land}: {e}")
    return jobs


def jobs_stepstone(suchbegriff, standort, anzahl=10):
    """StepStone Deutschland."""
    jobs = []
    try:
        q = urllib.parse.quote(suchbegriff)
        l = urllib.parse.quote(standort)
        url = f"https://www.stepstone.de/jobs/{q}/in-{l}"
        
        r = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        articles = soup.find_all("article")[:anzahl]
        
        for art in articles:
            try:
                te = art.find(["h2", "h3"])
                titel = te.get_text(strip=True) if te else ""
                fe = art.find("span", class_=re.compile("company"))
                firma = fe.get_text(strip=True) if fe else "Unbekannt"
                le = art.find("a", href=True)
                link = "https://www.stepstone.de" + le["href"] if le else ""
                
                if titel:
                    jobs.append({
                        "titel": titel, "firma": firma, "standort": standort,
                        "beschreibung": "", "url": link,
                        "quelle": "StepStone", "land": "DE"
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"StepStone: {e}")
    return jobs


# ============================================================
# JOB-SUCHE - INTERNATIONAL
# ============================================================
def jobs_remoteok(suchbegriff, anzahl=10):
    """RemoteOK - Remote Jobs weltweit."""
    jobs = []
    try:
        url = "https://remoteok.com/api"
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            data = r.json()
            count = 0
            for item in data[1:]:  # Erste Zeile ist Metadata
                if count >= anzahl:
                    break
                try:
                    titel = item.get("position", "")
                    if suchbegriff.lower() in titel.lower():
                        jobs.append({
                            "titel": titel,
                            "firma": item.get("company", "Unbekannt"),
                            "standort": "Remote (Worldwide)",
                            "beschreibung": item.get("description", "")[:300],
                            "url": item.get("url", ""),
                            "quelle": "RemoteOK",
                            "land": "WORLD"
                        })
                        count += 1
                except Exception:
                    continue
    except Exception as e:
        print(f"RemoteOK: {e}")
    return jobs


def jobs_themuse(suchbegriff, standort, anzahl=10):
    """TheMuse - USA & International."""
    jobs = []
    try:
        url = "https://www.themuse.com/api/public/jobs"
        params = {"category": suchbegriff, "location": standort, "page": 0}
        r = requests.get(url, params=params, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("results", [])[:anzahl]:
                try:
                    locations = item.get("locations", [])
                    ort = locations[0]["name"] if locations else standort
                    jobs.append({
                        "titel": item.get("name", ""),
                        "firma": item.get("company", {}).get("name", "Unbekannt"),
                        "standort": ort,
                        "beschreibung": item.get("contents", "")[:300],
                        "url": item.get("refs", {}).get("landing_page", ""),
                        "quelle": "TheMuse",
                        "land": "INT"
                    })
                except Exception:
                    continue
    except Exception as e:
        print(f"TheMuse: {e}")
    return jobs


def jobs_jobicy(suchbegriff, anzahl=10):
    """Jobicy - Remote Jobs International."""
    jobs = []
    try:
        url = "https://jobicy.com/api/v2/remote-jobs"
        params = {"count": anzahl, "tag": suchbegriff}
        r = requests.get(url, params=params, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            data = r.json()
            for item in data.get("jobs", [])[:anzahl]:
                try:
                    jobs.append({
                        "titel": item.get("jobTitle", ""),
                        "firma": item.get("companyName", "Unbekannt"),
                        "standort": item.get("jobGeo", "Remote"),
                        "beschreibung": item.get("jobExcerpt", "")[:300],
                        "url": item.get("url", ""),
                        "quelle": "Jobicy",
                        "land": "WORLD"
                    })
                except Exception:
                    continue
    except Exception as e:
        print(f"Jobicy: {e}")
    return jobs


def jobs_arbeitnow(suchbegriff, anzahl=10):
    """Arbeitnow - Europa Jobs."""
    jobs = []
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            data = r.json()
            count = 0
            for item in data.get("data", []):
                if count >= anzahl:
                    break
                try:
                    titel = item.get("title", "")
                    if suchbegriff.lower() in titel.lower():
                        locations = item.get("location", "Europe")
                        jobs.append({
                            "titel": titel,
                            "firma": item.get("company_name", "Unbekannt"),
                            "standort": locations,
                            "beschreibung": item.get("description", "")[:300],
                            "url": item.get("url", ""),
                            "quelle": "Arbeitnow",
                            "land": "EU"
                        })
                        count += 1
                except Exception:
                    continue
    except Exception as e:
        print(f"Arbeitnow: {e}")
    return jobs


# ============================================================
# HAUPT-SUCHFUNKTION
# ============================================================
def alle_jobs_suchen(suchbegriff, standort, radius=25, international=False):
    """Sucht in vielen Portalen."""
    alle_jobs = []
    
    # DEUTSCHLAND (immer)
    try:
        jobs = jobs_arbeitsagentur(suchbegriff, standort, radius, 20)
        alle_jobs.extend(jobs)
        print(f"Arbeitsagentur DE: {len(jobs)}")
    except Exception as e:
        print(f"Arbeitsagentur Fehler: {e}")
    
    try:
        jobs = jobs_indeed(suchbegriff, standort, radius, "de", 15)
        alle_jobs.extend(jobs)
        print(f"Indeed DE: {len(jobs)}")
    except Exception as e:
        print(f"Indeed DE Fehler: {e}")
    
    try:
        jobs = jobs_stepstone(suchbegriff, standort, 10)
        alle_jobs.extend(jobs)
        print(f"StepStone: {len(jobs)}")
    except Exception as e:
        print(f"StepStone Fehler: {e}")
    
    # INTERNATIONAL (wenn aktiviert)
    if international:
        try:
            jobs = jobs_remoteok(suchbegriff, 10)
            alle_jobs.extend(jobs)
            print(f"RemoteOK: {len(jobs)}")
        except Exception as e:
            print(f"RemoteOK Fehler: {e}")
        
        try:
            jobs = jobs_jobicy(suchbegriff, 10)
            alle_jobs.extend(jobs)
            print(f"Jobicy: {len(jobs)}")
        except Exception as e:
            print(f"Jobicy Fehler: {e}")
        
        try:
            jobs = jobs_arbeitnow(suchbegriff, 10)
            alle_jobs.extend(jobs)
            print(f"Arbeitnow EU: {len(jobs)}")
        except Exception as e:
            print(f"Arbeitnow Fehler: {e}")
        
        try:
            jobs = jobs_themuse(suchbegriff, standort, 10)
            alle_jobs.extend(jobs)
            print(f"TheMuse: {len(jobs)}")
        except Exception as e:
            print(f"TheMuse Fehler: {e}")
        
        # USA Indeed
        try:
            jobs = jobs_indeed(suchbegriff, standort, radius, "us", 10)
            alle_jobs.extend(jobs)
            print(f"Indeed US: {len(jobs)}")
        except Exception as e:
            print(f"Indeed US Fehler: {e}")
        
        # UK Indeed
        try:
            jobs = jobs_indeed(suchbegriff, standort, radius, "uk", 10)
            alle_jobs.extend(jobs)
            print(f"Indeed UK: {len(jobs)}")
        except Exception as e:
            print(f"Indeed UK Fehler: {e}")
    
    print(f"GESAMT: {len(alle_jobs)} Jobs")
    return alle_jobs


def jobs_speichern(user_id, jobs, branche="", radius=25):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    gespeichert = 0
    
    for job in jobs:
        c.execute("SELECT id FROM jobs WHERE user_id=? AND firma=? AND position=?",
                  (user_id, job.get("firma", ""), job.get("titel", "")))
        if c.fetchone():
            continue
        
        try:
            c.execute("""INSERT INTO jobs 
                (user_id, firma, position, standort, beschreibung,
                 url, branche, quelle, gefunden, entfernung, favorit, beworben, land)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)""",
                (user_id, job.get("firma", ""), job.get("titel", ""),
                 job.get("standort", ""), job.get("beschreibung", ""),
                 job.get("url", ""), branche, job.get("quelle", ""),
                 datetime.now().isoformat(), radius, job.get("land", "DE")))
            gespeichert += 1
        except Exception:
            continue
    
    conn.commit()
    conn.close()
    return gespeichert


def jobs_laden(user_id, filter_typ="alle"):
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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM jobs WHERE id=? AND user_id=?", (job_id, user_id))
    conn.commit()
    conn.close()


def vorlagen_laden(premium=False, sprache="de"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        if premium:
            c.execute("SELECT * FROM anschreiben_vorlagen WHERE sprache=? ORDER BY premium, name", (sprache,))
        else:
            c.execute("SELECT * FROM anschreiben_vorlagen WHERE premium=0 AND sprache=? ORDER BY name", (sprache,))
        rows = c.fetchall()
        # Fallback ohne Sprache
        if not rows:
            if premium:
                c.execute("SELECT * FROM anschreiben_vorlagen ORDER BY premium, name")
            else:
                c.execute("SELECT * FROM anschreiben_vorlagen WHERE premium=0 ORDER BY name")
            rows = c.fetchall()
    except Exception:
        rows = []
    conn.close()
    return rows


def anschreiben_generieren(job_id, user_id, vorlage_id, user_profil, sprache="de"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE id=? AND user_id=?", (job_id, user_id))
    job = c.fetchone()
    c.execute("SELECT * FROM anschreiben_vorlagen WHERE id=?", (vorlage_id,))
    vorlage = c.fetchone()
    conn.close()
    
    if not job or not vorlage:
        return None
    
    sprache_text = {
        "de": "Deutsch",
        "en": "English",
        "fr": "Francais",
        "es": "Espanol"
    }.get(sprache, "Deutsch")
    
    prompt = f"""Erstelle Anschreiben in {sprache_text}:

Firma: {job[2]}
Position: {job[3]}
Standort: {job[4]}
Land: {job[15] if len(job) > 15 else 'DE'}

Bewerber: {user_profil.get('vorname', '')} {user_profil.get('nachname', '')}
Kenntnisse: {user_profil.get('kenntnisse', '')}

Style: {vorlage[2]}

Vollstaendiges Anschreiben, max 300 Woerter, in {sprache_text}."""
    
    return avinu_antwort(prompt)


def auto_bewerbung_erstellen(user_id, job_id, anschreiben, sprache="de"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO auto_bewerbungen 
            (user_id, job_id, anschreiben, erstellt_am, sprache) 
            VALUES (?, ?, ?, ?, ?)""",
            (user_id, job_id, anschreiben, datetime.now().isoformat(), sprache))
    except Exception:
        c.execute("""INSERT INTO auto_bewerbungen 
            (user_id, job_id, anschreiben, erstellt_am) 
            VALUES (?, ?, ?, ?)""",
            (user_id, job_id, anschreiben, datetime.now().isoformat()))
    
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
    alle = []
    for berufe in BRANCHEN.values():
        alle.extend(berufe)
    return sorted(set(alle))


# Init
avinu_db_init()