"""
Kalender-Integration fuer Bewerbungstermine
Erstellt .ics Dateien fuer Outlook/Google Kalender
"""
import sqlite3
import os
from datetime import datetime, timedelta
from database import DB_NAME


def ics_erstellen(
    titel, datum, uhrzeit="10:00",
    beschreibung="", ort=""
):
    """Erstellt eine .ics Kalender-Datei."""

    try:
        start_str = f"{datum} {uhrzeit}"
        start     = datetime.strptime(start_str, "%d.%m.%Y %H:%M")
        ende      = start + timedelta(hours=1)

        uid = f"bewerbung_{datetime.now().strftime('%Y%m%d%H%M%S')}@bot"

        ics_inhalt = (
            "BEGIN:VCALENDAR\n"
            "VERSION:2.0\n"
            "PRODID:-//BewerbungsBot//Komi Tevi//DE\n"
            "BEGIN:VEVENT\n"
            f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}\n"
            f"DTEND:{ende.strftime('%Y%m%dT%H%M%S')}\n"
            f"SUMMARY:{titel}\n"
            f"DESCRIPTION:{beschreibung}\n"
            f"LOCATION:{ort}\n"
            f"UID:{uid}\n"
            "STATUS:CONFIRMED\n"
            "BEGIN:VALARM\n"
            "TRIGGER:-PT30M\n"
            "ACTION:DISPLAY\n"
            "DESCRIPTION:Erinnerung: 30 Min\n"
            "END:VALARM\n"
            "END:VEVENT\n"
            "END:VCALENDAR\n"
        )

        # Ordner erstellen
        kalender_pfad = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "kalender"
        )
        os.makedirs(kalender_pfad, exist_ok=True)

        # Dateiname
        titel_clean = titel.replace(" ", "_").replace("/", "-")
        dateiname   = f"Termin_{titel_clean}_{datum.replace('.','')}.ics"
        pfad        = os.path.join(kalender_pfad, dateiname)

        with open(pfad, "w", encoding="utf-8") as f:
            f.write(ics_inhalt)

        print(f"  Kalender-Datei erstellt: {dateiname}")
        print(f"  Pfad: {pfad}")

        # Automatisch in Outlook oeffnen
        try:
            os.startfile(pfad)
            print("  Wird in Outlook geoeffnet...")
        except Exception:
            pass

        return pfad

    except Exception as e:
        print(f"  Kalender Fehler: {e}")
        return None


def vorstellungsgespraech_eintragen():
    """Traegt ein Vorstellungsgespraech in den Kalender ein."""
    print("\n  VORSTELLUNGSGESPRAECH EINTRAGEN")
    print("  " + "="*45)

    firma   = input("  Firma    : ").strip()
    datum   = input("  Datum    : (TT.MM.JJJJ): ").strip()
    uhrzeit = input("  Uhrzeit  : (HH:MM): ").strip() or "10:00"
    ort     = input("  Ort/Adresse : ").strip()
    kontakt = input("  Kontaktperson : ").strip()

    if not firma or not datum:
        print("  Firma und Datum erforderlich!")
        return None

    titel = (
        f"Vorstellungsgespraech - {firma} - "
        f"IT-Fachtechniker Praktikum"
    )
    beschreibung = (
        f"Vorstellungsgespraech bei {firma}\n"
        f"Position: IT-Fachtechniker / Netzwerktechniker\n"
        f"Kontakt: {kontakt}\n"
        f"Bewerber: Komi Tevi\n"
        f"Tel: +49 178 8977320"
    )

    pfad = ics_erstellen(
        titel=titel,
        datum=datum,
        uhrzeit=uhrzeit,
        beschreibung=beschreibung,
        ort=ort
    )

    # In Datenbank speichern
    if pfad:
        conn = sqlite3.connect(DB_NAME)
        c    = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS termine (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                firma    TEXT,
                datum    TEXT,
                uhrzeit  TEXT,
                ort      TEXT,
                typ      TEXT,
                notizen  TEXT,
                ics_pfad TEXT
            )
        """)

        c.execute("""
            INSERT INTO termine
            (firma, datum, uhrzeit, ort, typ, ics_pfad)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (firma, datum, uhrzeit, ort, "Vorstellungsgespraech", pfad))

        conn.commit()
        conn.close()

        print(f"\n  Termin gespeichert!")
        print(f"  {firma} am {datum} um {uhrzeit} Uhr")

    return pfad


def erinnerung_eintragen():
    """Erstellt eine Erinnerung."""
    print("\n  ERINNERUNG ERSTELLEN")
    print("  " + "="*45)

    titel   = input("  Titel    : ").strip()
    datum   = input("  Datum    : (TT.MM.JJJJ): ").strip()
    uhrzeit = input("  Uhrzeit  : (HH:MM): ").strip() or "09:00"
    beschreibung = input("  Beschreibung : ").strip()

    if not titel or not datum:
        print("  Titel und Datum erforderlich!")
        return None

    return ics_erstellen(
        titel=titel,
        datum=datum,
        uhrzeit=uhrzeit,
        beschreibung=beschreibung
    )


def termine_anzeigen():
    """Zeigt alle Termine an."""
    conn = sqlite3.connect(DB_NAME)
    c    = conn.cursor()

    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS termine (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                firma    TEXT,
                datum    TEXT,
                uhrzeit  TEXT,
                ort      TEXT,
                typ      TEXT,
                notizen  TEXT,
                ics_pfad TEXT
            )
        """)

        c.execute(
            "SELECT * FROM termine ORDER BY datum DESC"
        )
        termine = c.fetchall()

    except Exception:
        termine = []

    conn.close()

    if not termine:
        print("\n  Keine Termine gespeichert.")
        return

    print(f"\n  {'='*65}")
    print(f"  TERMINE ({len(termine)})")
    print(f"  {'='*65}")
    print(
        f"  {'ID':<4} {'Firma':<20} {'Datum':<12} "
        f"{'Uhrzeit':<8} {'Typ':<20}"
    )
    print(f"  {'-'*65}")

    for t in termine:
        tid     = str(t[0])
        firma   = str(t[1])[:18] if t[1] else "N/A"
        datum   = str(t[2])[:10] if t[2] else "N/A"
        uhrzeit = str(t[3])[:6]  if t[3] else "N/A"
        typ     = str(t[5])[:18] if t[5] else "N/A"
        print(
            f"  {tid:<4} {firma:<20} {datum:<12} "
            f"{uhrzeit:<8} {typ:<20}"
        )

    print(f"  {'='*65}")


def naechste_schritte_kalender():
    """Erstellt automatisch Kalendereintraege fuer Bewerbungen."""
    print("\n  Erstelle Bewerbungs-Kalender...")

    heute = datetime.now()

    eintraege = [
        {
            "titel": "Bewerbungsbot - Taeglich Stellen suchen",
            "datum": heute.strftime("%d.%m.%Y"),
            "uhrzeit": "08:00",
            "beschreibung": "IT-Praktikum Bot starten und neue Stellen suchen",
        },
        {
            "titel": "Bewerbungen pruefen und nachfassen",
            "datum": (heute + timedelta(days=7)).strftime("%d.%m.%Y"),
            "uhrzeit": "09:00",
            "beschreibung": "Nach 1 Woche: Bewerbungen pruefen, ggf. nachfassen",
        },
        {
            "titel": "Nachfass-E-Mails senden",
            "datum": (heute + timedelta(days=14)).strftime("%d.%m.%Y"),
            "uhrzeit": "09:00",
            "beschreibung": "Nach 2 Wochen: Automatische Nachfass-E-Mails",
        },
    ]

    for e in eintraege:
        ics_erstellen(
            titel=e["titel"],
            datum=e["datum"],
            uhrzeit=e["uhrzeit"],
            beschreibung=e["beschreibung"]
        )

    print(f"\n  {len(eintraege)} Kalendereintraege erstellt!")
    print("  Ordner: kalender/")


if __name__ == "__main__":
    print("\n  KALENDER TOOLS")
    print("  1. Vorstellungsgespraech eintragen")
    print("  2. Erinnerung erstellen")
    print("  3. Termine anzeigen")
    print("  4. Standard Kalender erstellen")
    wahl = input("  Auswahl: ").strip()

    if wahl == "1":
        vorstellungsgespraech_eintragen()
    elif wahl == "2":
        erinnerung_eintragen()
    elif wahl == "3":
        termine_anzeigen()
    elif wahl == "4":
        naechste_schritte_kalender()