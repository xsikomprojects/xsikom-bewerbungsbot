import sqlite3
from datetime import datetime, timedelta
from database import DB_NAME
from telegram_sender import telegram_senden


def tracker_tabellen_erstellen():
    """Erstellt Tracker-Tabellen in der Datenbank."""
    conn = sqlite3.connect(DB_NAME)
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS tracker (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            bewerbung_id    INTEGER,
            firma           TEXT,
            position        TEXT,
            email           TEXT,
            gesendet_am     TEXT,
            antwort_status  TEXT DEFAULT 'ausstehend',
            antwort_datum   TEXT,
            antwort_text    TEXT,
            einladung       INTEGER DEFAULT 0,
            einladung_datum TEXT,
            absage          INTEGER DEFAULT 0,
            erinnerung_1    INTEGER DEFAULT 0,
            erinnerung_2    INTEGER DEFAULT 0,
            notizen         TEXT
        )
    """)

    conn.commit()
    conn.close()


def bewerbung_tracken(firma, position, email, bewerbung_id=None):
    """Fügt eine Bewerbung zum Tracker hinzu."""
    tracker_tabellen_erstellen()

    conn = sqlite3.connect(DB_NAME)
    c    = conn.cursor()

    # Duplikat prüfen
    c.execute(
        "SELECT id FROM tracker WHERE firma=? AND email=?",
        (firma, email)
    )
    if c.fetchone():
        conn.close()
        return None

    datum = datetime.now().strftime("%d.%m.%Y %H:%M")
    c.execute("""
        INSERT INTO tracker
        (bewerbung_id, firma, position, email, gesendet_am)
        VALUES (?, ?, ?, ?, ?)
    """, (bewerbung_id, firma, position, email, datum))

    tracker_id = c.lastrowid
    conn.commit()
    conn.close()
    return tracker_id


def antwort_eintragen(tracker_id, status, text="", einladung=False):
    """Trägt eine Antwort in den Tracker ein."""
    conn  = sqlite3.connect(DB_NAME)
    c     = conn.cursor()
    datum = datetime.now().strftime("%d.%m.%Y %H:%M")

    c.execute("""
        UPDATE tracker SET
            antwort_status = ?,
            antwort_datum  = ?,
            antwort_text   = ?,
            einladung      = ?,
            einladung_datum = ?
        WHERE id = ?
    """, (
        status, datum, text,
        1 if einladung else 0,
        datum if einladung else None,
        tracker_id
    ))

    conn.commit()
    conn.close()

    # Telegram Benachrichtigung
    if einladung:
        telegram_senden(
            f"<b>EINLADUNG ERHALTEN!</b>\n\n"
            f"Firma  : {_firma_von_id(tracker_id)}\n"
            f"Status : {status}\n"
            f"Datum  : {datum}\n\n"
            f"Glueckwunsch, Komi!"
        )
    elif status == "absage":
        telegram_senden(
            f"<b>Absage erhalten</b>\n\n"
            f"Firma  : {_firma_von_id(tracker_id)}\n"
            f"Datum  : {datum}"
        )


def _firma_von_id(tracker_id):
    """Hilfsfunktion: Firma anhand ID laden."""
    conn = sqlite3.connect(DB_NAME)
    c    = conn.cursor()
    c.execute("SELECT firma FROM tracker WHERE id=?", (tracker_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "Unbekannt"


def erinnerungen_pruefen():
    """Prüft welche Bewerbungen noch keine Antwort haben."""
    tracker_tabellen_erstellen()

    conn  = sqlite3.connect(DB_NAME)
    c     = conn.cursor()
    heute = datetime.now()

    c.execute("""
        SELECT id, firma, position, email, gesendet_am
        FROM tracker
        WHERE antwort_status = 'ausstehend'
        AND absage = 0
    """)
    ausstehend = c.fetchall()

    erinnerungen = []

    for t in ausstehend:
        tid          = t[0]
        firma        = t[1]
        position     = t[2]
        email        = t[3]
        gesendet_str = t[4]

        try:
            gesendet = datetime.strptime(
                gesendet_str[:16], "%d.%m.%Y %H:%M"
            )
        except Exception:
            continue

        tage_vergangen = (heute - gesendet).days

        # Nach 7 Tagen: Erste Erinnerung
        c.execute(
            "SELECT erinnerung_1 FROM tracker WHERE id=?",
            (tid,)
        )
        row = c.fetchone()
        er1 = row[0] if row else 0

        if tage_vergangen >= 7 and not er1:
            erinnerungen.append({
                "id":     tid,
                "firma":  firma,
                "tage":   tage_vergangen,
                "typ":    "erste",
            })
            c.execute(
                "UPDATE tracker SET erinnerung_1=1 WHERE id=?",
                (tid,)
            )

        # Nach 14 Tagen: Zweite Erinnerung
        c.execute(
            "SELECT erinnerung_2 FROM tracker WHERE id=?",
            (tid,)
        )
        row = c.fetchone()
        er2 = row[0] if row else 0

        if tage_vergangen >= 14 and not er2:
            erinnerungen.append({
                "id":    tid,
                "firma": firma,
                "tage":  tage_vergangen,
                "typ":   "zweite",
            })
            c.execute(
                "UPDATE tracker SET erinnerung_2=1 WHERE id=?",
                (tid,)
            )

    conn.commit()
    conn.close()

    # Erinnerungen ausgeben und Telegram senden
    if erinnerungen:
        print(f"\n  ERINNERUNGEN ({len(erinnerungen)})")
        print("  " + "="*45)

        for e in erinnerungen:
            print(
                f"  {e['typ'].upper()} Erinnerung: "
                f"{e['firma']} ({e['tage']} Tage)"
            )

            telegram_senden(
                f"<b>Erinnerung - Keine Antwort!</b>\n\n"
                f"Firma    : {e['firma']}\n"
                f"Gesendet : vor {e['tage']} Tagen\n"
                f"Typ      : {e['typ']} Erinnerung\n\n"
                f"Vielleicht nochmal nachfragen, Komi?"
            )
    else:
        print("\n  Keine offenen Erinnerungen.")

    return erinnerungen


def tracker_anzeigen():
    """Zeigt alle getrackten Bewerbungen an."""
    tracker_tabellen_erstellen()

    conn = sqlite3.connect(DB_NAME)
    c    = conn.cursor()
    c.execute("""
        SELECT id, firma, position, email,
               gesendet_am, antwort_status,
               einladung, absage
        FROM tracker
        ORDER BY id DESC
    """)
    eintraege = c.fetchall()
    conn.close()

    if not eintraege:
        print("\n  Keine Bewerbungen im Tracker.")
        return

    print(f"\n  {'='*75}")
    print(f"  BEWERBUNGS-TRACKER ({len(eintraege)})")
    print(f"  {'='*75}")
    print(
        f"  {'ID':<4} {'Firma':<20} {'Status':<12} "
        f"{'Einladung':<10} {'Gesendet':<16}"
    )
    print(f"  {'-'*75}")

    for e in eintraege:
        tid      = str(e[0])
        firma    = str(e[1])[:18] if e[1] else "N/A"
        status   = str(e[5])[:10] if e[5] else "N/A"
        einlad   = "JA!" if e[6] else "Nein"
        gesendet = str(e[4])[:14] if e[4] else "N/A"

        # Status Farbe
        if e[6]:
            status_anzeige = f"EINLADUNG"
        elif e[7]:
            status_anzeige = "Absage"
        elif status == "ausstehend":
            status_anzeige = "Ausstehend"
        else:
            status_anzeige = status

        print(
            f"  {tid:<4} {firma:<20} "
            f"{status_anzeige:<12} {einlad:<10} {gesendet:<16}"
        )

    print(f"  {'='*75}")

    # Zusammenfassung
    einladungen = sum(1 for e in eintraege if e[6])
    absagen     = sum(1 for e in eintraege if e[7])
    ausstehend  = sum(
        1 for e in eintraege
        if not e[6] and not e[7]
    )

    print(f"\n  Einladungen : {einladungen}")
    print(f"  Absagen     : {absagen}")
    print(f"  Ausstehend  : {ausstehend}")


def antwort_interaktiv():
    """Interaktives Menü zum Eintragen von Antworten."""
    tracker_anzeigen()

    print("\n  Antwort eintragen:")
    tid = input("  Tracker-ID eingeben: ").strip()

    if not tid.isdigit():
        print("  Ungueltige ID!")
        return

    print("\n  Status waehlen:")
    print("  1. Einladung zum Gespraech erhalten!")
    print("  2. Absage erhalten")
    print("  3. Antwort erhalten (positiv)")
    print("  4. Antwort erhalten (neutral)")
    print("  5. Notiz hinzufuegen")
    print("  0. Abbrechen")

    wahl = input("  Auswahl: ").strip()

    if wahl == "1":
        text = input("  Gespraechangebot Text: ").strip()
        antwort_eintragen(int(tid), "einladung", text, einladung=True)
        print("  EINLADUNG eingetragen!")
        print("  Glueckwunsch, Komi!")

    elif wahl == "2":
        text = input("  Absage Text (optional): ").strip()
        conn = sqlite3.connect(DB_NAME)
        c    = conn.cursor()
        c.execute(
            "UPDATE tracker SET absage=1, "
            "antwort_status='absage', "
            "antwort_text=? WHERE id=?",
            (text, int(tid))
        )
        conn.commit()
        conn.close()
        print("  Absage eingetragen.")

    elif wahl == "3":
        text = input("  Antwort Text: ").strip()
        antwort_eintragen(int(tid), "positiv", text)
        print("  Antwort eingetragen!")

    elif wahl == "4":
        text = input("  Antwort Text: ").strip()
        antwort_eintragen(int(tid), "neutral", text)
        print("  Antwort eingetragen!")

    elif wahl == "5":
        notiz = input("  Notiz: ").strip()
        conn  = sqlite3.connect(DB_NAME)
        c     = conn.cursor()
        c.execute(
            "UPDATE tracker SET notizen=? WHERE id=?",
            (notiz, int(tid))
        )
        conn.commit()
        conn.close()
        print("  Notiz gespeichert!")

    elif wahl == "0":
        print("  Abgebrochen.")


if __name__ == "__main__":
    tracker_tabellen_erstellen()
    print("  Tracker Tabellen erstellt!")
    erinnerungen_pruefen()