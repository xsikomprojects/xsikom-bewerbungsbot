import requests
from bs4 import BeautifulSoup
import time
from config import SUCH_CONFIG, IT_FIRMEN
from database import stelle_speichern, stellen_laden
from telegram_sender import telegram_neue_stelle

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9",
}


def stellen_anzeigen():
    stellen    = stellen_laden()
    if not stellen:
        print("\n  Keine Stellen gefunden.")
        print("  -> Option 1: Suche starten")
        print("  -> Option 3: IT-Firmen hinzufuegen")
        return

    mit_email  = sum(1 for s in stellen if s[4])
    ohne_email = len(stellen) - mit_email

    print(f"\n  {'='*78}")
    print(f"  GEFUNDENE STELLEN ({len(stellen)})")
    print(f"  Mit E-Mail: {mit_email} | Ohne E-Mail: {ohne_email}")
    print(f"  {'='*78}")
    print(
        f"  {'ID':<4} {'Titel':<24} {'Firma':<18} "
        f"{'Ort':<14} {'Quelle':<12} {'Email':<5}"
    )
    print(f"  {'-'*78}")

    for s in stellen:
        sid       = str(s[0])
        titel     = str(s[1])[:22] if s[1] else "N/A"
        firma     = str(s[2])[:16] if s[2] else "N/A"
        ort       = str(s[3])[:12] if s[3] else "N/A"
        quelle    = str(s[6])[:10] if s[6] else "N/A"
        hat_email = "Ja" if s[4] else "Nein"
        print(
            f"  {sid:<4} {titel:<24} {firma:<18} "
            f"{ort:<14} {quelle:<12} {hat_email:<5}"
        )

    print(f"  {'='*78}")


def _speichern(titel, firma, standort, url, quelle):
    """Hilfsfunktion: Stelle speichern + Telegram."""
    sid = stelle_speichern(
        titel, firma, standort, "", url, quelle
    )
    if sid:
        telegram_neue_stelle(firma, titel, standort, quelle)
        return True
    return False


def suche_indeed(suchbegriff, standort):
    gefunden = 0
    try:
        url  = (
            f"https://de.indeed.com/jobs?"
            f"q={suchbegriff.replace(' ','+')}"
            f"&l={standort.replace(' ','+')}"
        )
        r    = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return 0
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = (
            soup.find_all("div", class_="job_seen_beacon") or
            soup.find_all("li", class_="css-5lfssm") or
            soup.find_all("div", attrs={"data-testid": "slider_item"})
        )
        for card in cards[:8]:
            try:
                t     = card.find("h2")
                titel = t.get_text(strip=True) if t else "IT-Praktikum"
                f     = (
                    card.find("span", attrs={"data-testid": "company-name"}) or
                    card.find("span", class_="css-92r8pb")
                )
                firma = f.get_text(strip=True) if f else "Unbekannt"
                a     = card.find("a", href=True)
                link  = ""
                if a and a.get("href"):
                    href = a["href"]
                    link = "https://de.indeed.com" + href if href.startswith("/") else href
                if _speichern(titel, firma, standort, link, "Indeed"):
                    gefunden += 1
            except Exception:
                continue
    except Exception:
        pass
    return gefunden


def suche_stepstone(suchbegriff, standort):
    gefunden = 0
    try:
        url  = (
            f"https://www.stepstone.de/jobs/"
            f"{suchbegriff.replace(' ','-')}/"
            f"in-{standort.replace(' ','-')}"
        )
        r    = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return 0
        soup    = BeautifulSoup(r.text, "html.parser")
        artikel = soup.find_all("article")
        for art in artikel[:8]:
            try:
                t     = art.find(["h2", "h3"])
                titel = t.get_text(strip=True) if t else "IT-Praktikum"
                f     = (
                    art.find("span", attrs={"data-at": "job-item-company-name"}) or
                    art.find("span", class_="listing-item__label")
                )
                firma = f.get_text(strip=True) if f else "Unbekannt"
                a     = art.find("a", href=True)
                link  = ""
                if a and a.get("href"):
                    href = a["href"]
                    link = "https://www.stepstone.de" + href if not href.startswith("http") else href
                if _speichern(titel, firma, standort, link, "StepStone"):
                    gefunden += 1
            except Exception:
                continue
    except Exception:
        pass
    return gefunden


def suche_monster(suchbegriff, standort):
    gefunden = 0
    try:
        url  = (
            f"https://www.monster.de/jobs/suche/?"
            f"q={suchbegriff.replace(' ','-')}"
            f"&where={standort.replace(' ','-')}"
        )
        r    = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return 0
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = (
            soup.find_all("div", class_="job-search-card") or
            soup.find_all("section", class_="card-content")
        )
        for card in cards[:8]:
            try:
                t     = card.find(["h2", "h3", "a"])
                titel = t.get_text(strip=True) if t else "IT-Praktikum"
                f     = (
                    card.find("div", class_="company") or
                    card.find("span", class_="name")
                )
                firma = f.get_text(strip=True) if f else "Unbekannt"
                if _speichern(titel, firma, standort, "", "Monster"):
                    gefunden += 1
            except Exception:
                continue
    except Exception:
        pass
    return gefunden


def suche_xing(suchbegriff, standort):
    gefunden = 0
    try:
        url  = (
            f"https://www.xing.com/jobs/search?"
            f"keywords={suchbegriff.replace(' ','+')}"
            f"&location={standort.replace(' ','+')}"
        )
        r    = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return 0
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = (
            soup.find_all("div", attrs={"data-xds": "JobCard"}) or
            soup.find_all("li", class_="jobs-search-result__list-item")
        )
        for card in cards[:8]:
            try:
                t     = card.find(["h2", "h3", "a"])
                titel = t.get_text(strip=True) if t else "IT-Praktikum"
                f     = card.find(
                    ["span", "div"],
                    class_=lambda x: x and "company" in x.lower()
                )
                firma = f.get_text(strip=True) if f else "Unbekannt"
                if _speichern(titel, firma, standort, "", "XING"):
                    gefunden += 1
            except Exception:
                continue
    except Exception:
        pass
    return gefunden


def suche_linkedin(suchbegriff, standort):
    gefunden = 0
    try:
        url  = (
            f"https://www.linkedin.com/jobs/search/?"
            f"keywords={suchbegriff.replace(' ','%20')}"
            f"&location={standort.replace(' ','%20')}"
        )
        r    = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return 0
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = (
            soup.find_all("div", class_="base-card") or
            soup.find_all("li", class_="jobs-search__results-list")
        )
        for card in cards[:8]:
            try:
                t     = card.find(["h3", "h4"])
                titel = t.get_text(strip=True) if t else "IT-Praktikum"
                f     = (
                    card.find("h4", class_="base-search-card__subtitle") or
                    card.find("a", class_="hidden-nested-link")
                )
                firma = f.get_text(strip=True) if f else "Unbekannt"
                a     = card.find("a", href=True)
                link  = a["href"] if a and a.get("href") else ""
                if _speichern(titel, firma, standort, link, "LinkedIn"):
                    gefunden += 1
            except Exception:
                continue
    except Exception:
        pass
    return gefunden


def suche_glassdoor(suchbegriff, standort):
    gefunden = 0
    try:
        url  = (
            f"https://www.glassdoor.de/Job/"
            f"{standort.lower().replace(' ','-')}-"
            f"{suchbegriff.lower().replace(' ','-')}"
            f"-jobs-SRCH_IL.0,1_IC1.htm"
        )
        r    = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return 0
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("li", class_=lambda x: x and "JobsList" in str(x))
        if not cards:
            cards = soup.find_all("div", attrs={"data-test": "jobListing"})
        for card in cards[:8]:
            try:
                t     = card.find(["a", "h3"])
                titel = t.get_text(strip=True) if t else "IT-Praktikum"
                f     = card.find("div", class_=lambda x: x and "employer" in str(x).lower())
                firma = f.get_text(strip=True) if f else "Unbekannt"
                if _speichern(titel, firma, standort, "", "Glassdoor"):
                    gefunden += 1
            except Exception:
                continue
    except Exception:
        pass
    return gefunden


def suche_arbeitsagentur(suchbegriff, standort):
    gefunden = 0
    try:
        url  = (
            f"https://www.arbeitsagentur.de/jobsuche/suche?"
            f"was={suchbegriff.replace(' ','+')}"
            f"&wo={standort.replace(' ','+')}"
            f"&angebotsart=34"
        )
        r    = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return 0
        soup  = BeautifulSoup(r.text, "html.parser")
        items = (
            soup.find_all("div", class_="jobtile") or
            soup.find_all("div", attrs={"data-jobid": True})
        )
        for item in items[:8]:
            try:
                t     = item.find(["h2", "h3", "a"])
                titel = t.get_text(strip=True) if t else "IT-Praktikum"
                f     = item.find("span", class_="company")
                firma = f.get_text(strip=True) if f else "Unbekannt"
                if _speichern(titel, firma, standort, url, "Arbeitsagentur"):
                    gefunden += 1
            except Exception:
                continue
    except Exception:
        pass
    return gefunden


def suche_kimeta(suchbegriff, standort):
    """Kimeta - deutsche Jobbörse."""
    gefunden = 0
    try:
        url  = (
            f"https://www.kimeta.de/jobs?"
            f"q={suchbegriff.replace(' ','+')}"
            f"&l={standort.replace(' ','+')}"
        )
        r    = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return 0
        soup  = BeautifulSoup(r.text, "html.parser")
        cards = soup.find_all("div", class_=lambda x: x and "job" in str(x).lower())
        for card in cards[:8]:
            try:
                t     = card.find(["h2", "h3", "a"])
                titel = t.get_text(strip=True) if t else "IT-Praktikum"
                f     = card.find(["span", "div"], class_=lambda x: x and "company" in str(x).lower())
                firma = f.get_text(strip=True) if f else "Unbekannt"
                if _speichern(titel, firma, standort, "", "Kimeta"):
                    gefunden += 1
            except Exception:
                continue
    except Exception:
        pass
    return gefunden


def it_firmen_hinzufuegen():
    """Fügt bekannte IT-Firmen direkt in die Datenbank ein."""
    print("\n  Bekannte IT-Firmen werden hinzugefuegt...")
    neu = 0
    for firma_data in IT_FIRMEN:
        sid = stelle_speichern(
            titel="IT-Praktikum / Netzwerktechnik",
            firma=firma_data["firma"],
            standort=firma_data["standort"],
            email=firma_data["email"],
            url="",
            quelle="IT-Firmenliste"
        )
        if sid:
            neu += 1
            print(
                f"  + {firma_data['firma']} "
                f"({firma_data['standort']})"
            )
    print(f"\n  {neu} neue IT-Firmen hinzugefuegt!")
    return neu


def vollsuche_starten():
    suchbegriffe = SUCH_CONFIG["suchbegriffe"]
    standorte    = SUCH_CONFIG["standorte"]

    print(f"\n  {'='*60}")
    print(f"  AUTOMATISCHE STELLENSUCHE - MAXIMAL")
    print(f"  {'='*60}")
    print(f"  Suchbegriffe : {len(suchbegriffe)}")
    print(f"  Standorte    : {len(standorte)}")
    print(
        f"  Portale      : Indeed, StepStone, Monster, "
        f"XING, LinkedIn, Glassdoor, "
        f"Arbeitsagentur, Kimeta"
    )
    print(f"  {'='*60}\n")

    gesamt = 0

    portale = [
        ("Indeed",        suche_indeed),
        ("StepStone",     suche_stepstone),
        ("Monster",       suche_monster),
        ("XING",          suche_xing),
        ("LinkedIn",      suche_linkedin),
        ("Glassdoor",     suche_glassdoor),
        ("Arbeitsagentur",suche_arbeitsagentur),
        ("Kimeta",        suche_kimeta),
    ]

    for begriff in suchbegriffe[:3]:
        for ort in standorte[:5]:
            print(f"\n  Suche: '{begriff}' in {ort}")
            for name, funktion in portale:
                try:
                    n = funktion(begriff, ort)
                    print(f"    {name:<16}: {n} neue")
                    gesamt += n
                except Exception as e:
                    print(f"    {name:<16}: Fehler - {e}")
                time.sleep(2)

    print(f"\n  {'='*60}")
    print(f"  SUCHE ABGESCHLOSSEN!")
    print(f"  Neue Stellen gesamt: {gesamt}")
    print(f"  {'='*60}")

    stellen_anzeigen()
    return gesamt


if __name__ == "__main__":
    vollsuche_starten()