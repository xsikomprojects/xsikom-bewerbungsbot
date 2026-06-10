"""
Eigene Firmen-Webseiten nach E-Mail und Jobs durchsuchen
"""
import requests
from bs4 import BeautifulSoup
import re
import time
from database import stelle_speichern
from telegram_sender import telegram_neue_stelle

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9",
}

# ============================================================
# IT-FIRMEN WEBSEITEN - Regional
# ============================================================
FIRMEN_WEBSEITEN = [
    # ── MAINZ & UMGEBUNG ──────────────────────────────
    {
        "firma":    "Fraunhofer IGD Darmstadt",
        "url":      "https://www.igd.fraunhofer.de/karriere",
        "standort": "Darmstadt",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "Software AG",
        "url":      "https://www.softwareag.com/de/career",
        "standort": "Darmstadt",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "IHK Rheinhessen",
        "url":      "https://www.rheinhessen.ihk24.de",
        "standort": "Mainz",
        "bereich":  "allgemein",
    },
    {
        "firma":    "Merck KGaA IT",
        "url":      "https://www.merckgroup.com/de/karriere",
        "standort": "Darmstadt",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "Mainzer Stadtwerke AG",
        "url":      "https://www.mainzer-stadtwerke.de/karriere",
        "standort": "Mainz",
        "bereich":  "support",
    },
    # ── FRANKFURT ─────────────────────────────────────
    {
        "firma":    "Deutsche Bank IT",
        "url":      "https://www.db.com/careers",
        "standort": "Frankfurt am Main",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "DZ BANK IT",
        "url":      "https://karriere.dzbank.de",
        "standort": "Frankfurt am Main",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "Telenet GmbH",
        "url":      "https://www.telenet.de/karriere",
        "standort": "Frankfurt am Main",
        "bereich":  "netzwerk",
    },
    # ── KÖLN ──────────────────────────────────────────
    {
        "firma":    "REWE Digital GmbH",
        "url":      "https://rewe-digital.com/karriere",
        "standort": "Koeln",
        "bereich":  "systemadmin",
    },
    {
        "firma":    "Plusnet GmbH",
        "url":      "https://www.plusnet.de/karriere",
        "standort": "Koeln",
        "bereich":  "netzwerk",
    },
    # ── HEIDELBERG & MANNHEIM ─────────────────────────
    {
        "firma":    "Heidelberg iT Management",
        "url":      "https://www.heidelberg-it.de/karriere",
        "standort": "Heidelberg",
        "bereich":  "support",
    },
    {
        "firma":    "MVV Energie IT",
        "url":      "https://www.mvv.de/karriere",
        "standort": "Mannheim",
        "bereich":  "systemadmin",
    },
    # ── WIESBADEN ─────────────────────────────────────
    {
        "firma":    "Helaba IT",
        "url":      "https://karriere.helaba.de",
        "standort": "Wiesbaden",
        "bereich":  "netzwerk",
    },
    {
        "firma":    "BKK IT GmbH",
        "url":      "https://www.bkk-it.de/karriere",
        "standort": "Wiesbaden",
        "bereich":  "support",
    },
    # ── DÜSSELDORF ────────────────────────────────────
    {
        "firma":    "trivago N.V. IT",
        "url":      "https://careers.trivago.com",
        "standort": "Duesseldorf",
        "bereich":  "systemadmin",
    },
]


def email_von_seite_finden(html_text, url):
    """Findet E-Mail-Adressen auf einer Webseite."""
    emails = set(re.findall(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        html_text
    ))

    # Irrelevante E-Mails entfernen
    irrelevant = [
        "example", "test", "noreply", "no-reply",
        "unsubscribe", "spam", "abuse", "privacy",
        "datenschutz", "info@example"
    ]

    relevante = [
        e for e in emails
        if not any(x in e.lower() for x in irrelevant)
    ]

    # Priorisierung
    prioritaet = [
        "bewerbung", "hr", "personal", "jobs",
        "karriere", "career", "ausbildung",
        "praktikum", "recruiting", "info"
    ]

    relevante.sort(
        key=lambda e: next(
            (i for i, p in enumerate(prioritaet)
             if p in e.lower()),
            999
        )
    )

    return relevante[:3]


def jobs_auf_seite_finden(soup, firma):
    """Findet Jobangebote auf einer Firmenwebseite."""
    jobs = []
    it_keywords = [
        "praktikum", "it", "netzwerk", "system",
        "admin", "techniker", "support", "helpdesk",
        "informatik", "software", "network", "server"
    ]

    for tag in soup.find_all(["h1", "h2", "h3", "a", "li"]):
        text = tag.get_text(strip=True).lower()
        if any(kw in text for kw in it_keywords):
            if len(text) > 10 and len(text) < 100:
                jobs.append(tag.get_text(strip=True))

    return list(set(jobs))[:5]


def firmen_webseite_durchsuchen(firma_data):
    """Durchsucht eine Firmen-Webseite."""
    firma    = firma_data["firma"]
    url      = firma_data["url"]
    standort = firma_data["standort"]
    bereich  = firma_data["bereich"]

    print(f"\n  Durchsuche: {firma}")
    print(f"  URL: {url}")

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"  Status: {r.status_code} - Uebersprungen")
            return None

        soup  = BeautifulSoup(r.text, "html.parser")
        text  = r.text

        # E-Mail finden
        emails = email_von_seite_finden(text, url)

        # Jobs finden
        jobs = jobs_auf_seite_finden(soup, firma)

        email = emails[0] if emails else ""

        print(f"  E-Mail   : {email if email else 'Nicht gefunden'}")
        print(f"  Jobs     : {len(jobs)} gefunden")

        if jobs:
            for job in jobs[:3]:
                print(f"    - {job[:60]}")

        # In Datenbank speichern
        titel = (
            jobs[0][:50] if jobs
            else "IT-Praktikum / Netzwerktechniker"
        )
        sid = stelle_speichern(
            titel=titel,
            firma=firma,
            standort=standort,
            email=email,
            url=url,
            quelle="Firmenseite"
        )

        if sid:
            telegram_neue_stelle(
                firma, titel, standort, "Firmenseite"
            )
            print(f"  Gespeichert! ID: {sid}")

        return {
            "firma":   firma,
            "email":   email,
            "jobs":    jobs,
            "sid":     sid,
        }

    except requests.exceptions.ConnectionError:
        print(f"  Keine Verbindung zu {url}")
        return None
    except requests.exceptions.Timeout:
        print(f"  Timeout: {url}")
        return None
    except Exception as e:
        print(f"  Fehler: {e}")
        return None


def alle_firmen_durchsuchen():
    """Durchsucht alle gespeicherten Firmen-Webseiten."""
    print(f"\n  {'='*60}")
    print(f"  FIRMEN-WEBSEITEN DURCHSUCHEN")
    print(f"  {'='*60}")
    print(f"  Firmen: {len(FIRMEN_WEBSEITEN)}")
    print(f"  {'='*60}")

    gefunden  = 0
    mit_email = 0

    for i, firma_data in enumerate(FIRMEN_WEBSEITEN, 1):
        print(f"\n  [{i}/{len(FIRMEN_WEBSEITEN)}]")
        result = firmen_webseite_durchsuchen(firma_data)

        if result:
            gefunden += 1
            if result.get("email"):
                mit_email += 1

        time.sleep(3)

    print(f"\n  {'='*60}")
    print(f"  SUCHE ABGESCHLOSSEN!")
    print(f"  Firmen durchsucht : {len(FIRMEN_WEBSEITEN)}")
    print(f"  Ergebnisse        : {gefunden}")
    print(f"  Mit E-Mail        : {mit_email}")
    print(f"  {'='*60}")

    return gefunden


def eigene_url_durchsuchen():
    """Durchsucht eine vom User eingegebene URL."""
    print("\n  EIGENE FIRMEN-URL DURCHSUCHEN")
    print("  " + "="*45)

    firma    = input("  Firmenname : ").strip()
    url      = input("  URL        : ").strip()
    standort = input("  Standort   : ").strip()

    if not firma or not url:
        print("  Firma und URL erforderlich!")
        return

    firma_data = {
        "firma":    firma,
        "url":      url,
        "standort": standort,
        "bereich":  "allgemein",
    }

    result = firmen_webseite_durchsuchen(firma_data)

    if result:
        print(f"\n  Ergebnis:")
        print(f"  Firma  : {result['firma']}")
        print(f"  E-Mail : {result['email']}")
        print(f"  Jobs   : {len(result['jobs'])}")


if __name__ == "__main__":
    print("\n  FIRMEN SUCHE")
    print("  1. Alle Firmen durchsuchen")
    print("  2. Eigene URL eingeben")
    wahl = input("  Auswahl: ").strip()

    if wahl == "1":
        alle_firmen_durchsuchen()
    elif wahl == "2":
        eigene_url_durchsuchen()