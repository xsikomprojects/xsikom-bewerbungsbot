import sqlite3
from datetime import datetime

DB_NAME = "bewerbungen.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS stellen (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            titel       TEXT,
            firma       TEXT,
            standort    TEXT,
            email       TEXT,
            url         TEXT,
            quelle      TEXT,
            datum       TEXT,
            status      TEXT DEFAULT 'neu'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS bewerbungen (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            firma       TEXT,
            position    TEXT,
            email       TEXT,
            status      TEXT DEFAULT 'vorbereitet',
            datum       TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Datenbank bereit.")


def stelle_speichern(titel, firma, standort="", email="", url="", quelle="Manuell"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Duplikat prüfen
    c.execute(
        "SELECT id FROM stellen WHERE titel=? AND firma=?",
        (titel, firma)
    )
    if c.fetchone():
        conn.close()
        return None

    datum = datetime.now().strftime("%d.%m.%Y %H:%M")
    c.execute(
        "INSERT INTO stellen (titel, firma, standort, email, url, quelle, datum) VALUES (?,?,?,?,?,?,?)",
        (titel, firma, standort, email, url, quelle, datum)
    )
    conn.commit()
    stelle_id = c.lastrowid
    conn.close()
    return stelle_id


def bewerbung_speichern(firma, position, email, status="gesendet"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    datum = datetime.now().strftime("%d.%m.%Y %H:%M")
    c.execute(
        "INSERT INTO bewerbungen (firma, position, email, status, datum) VALUES (?,?,?,?,?)",
        (firma, position, email, status, datum)
    )
    conn.commit()
    conn.close()


def stellen_laden():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, titel, firma, standort, email, url, quelle, datum, status FROM stellen ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def bewerbungen_laden():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, firma, position, email, status, datum FROM bewerbungen ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def statistiken_anzeigen():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM stellen")
    stellen = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bewerbungen")
    alle = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM bewerbungen WHERE status='gesendet'")
    gesendet = c.fetchone()[0]
    conn.close()

    print("\n" + "="*40)
    print("  STATISTIKEN")
    print("="*40)
    print(f"  Gefundene Stellen  : {stellen}")
    print(f"  Bewerbungen gesamt : {alle}")
    print(f"  Gesendet           : {gesendet}")
    print("="*40)


if __name__ == "__main__":
    create_database()
    print("Datenbank erfolgreich erstellt!")