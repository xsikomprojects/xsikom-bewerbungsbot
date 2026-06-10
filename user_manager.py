"""
Benutzerverwaltung für XsiKOM-BewerbungsBOT
"""
import sqlite3
import hashlib
import os
import json
from datetime import datetime

DB_NAME = "bewerbungen.db"


def hash_passwort(passwort):
    """Erstellt Hash von Passwort."""
    return hashlib.sha256(passwort.encode()).hexdigest()


def user_db_erstellen():
    """Erstellt Benutzer-Tabelle."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS benutzer (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzername TEXT UNIQUE NOT NULL,
            passwort    TEXT NOT NULL,
            email       TEXT,
            vorname     TEXT,
            nachname    TEXT,
            rolle       TEXT DEFAULT 'user',
            erstellt_am TEXT,
            letzter_login TEXT,
            aktiv       INTEGER DEFAULT 1,
            einstellungen TEXT DEFAULT '{}'
        )
    """)

    conn.commit()
    conn.close()


def admin_erstellen():
    """Erstellt Admin-Benutzer falls nicht vorhanden."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT id FROM benutzer WHERE benutzername='admin'")
    if not c.fetchone():
        datum = datetime.now().strftime("%d.%m.%Y %H:%M")
        c.execute("""
            INSERT INTO benutzer
            (benutzername, passwort, email, vorname, nachname,
             rolle, erstellt_am, aktiv)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "admin",
            hash_passwort("XsiKOM2026!"),
            "xsikom.projects@gmail.com",
            "Komi",
            "Tevi",
            "admin",
            datum,
            1
        ))
        conn.commit()
        print("  Admin erstellt: admin / XsiKOM2026!")

    conn.close()


def benutzer_anlegen(benutzername, passwort, email="",
                     vorname="", nachname="", rolle="user"):
    """Legt einen neuen Benutzer an."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    try:
        datum = datetime.now().strftime("%d.%m.%Y %H:%M")
        c.execute("""
            INSERT INTO benutzer
            (benutzername, passwort, email, vorname, nachname,
             rolle, erstellt_am, aktiv)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            benutzername,
            hash_passwort(passwort),
            email, vorname, nachname,
            rolle, datum
        ))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def benutzer_pruefen(benutzername, passwort):
    """Prüft Benutzername und Passwort."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "SELECT id, benutzername, vorname, nachname, "
        "rolle, aktiv FROM benutzer "
        "WHERE benutzername=? AND passwort=?",
        (benutzername, hash_passwort(passwort))
    )
    user = c.fetchone()

    if user and user[5]:
        c.execute(
            "UPDATE benutzer SET letzter_login=? WHERE id=?",
            (datetime.now().strftime("%d.%m.%Y %H:%M"), user[0])
        )
        conn.commit()
        conn.close()
        return {
            "id":           user[0],
            "benutzername": user[1],
            "vorname":      user[2],
            "nachname":     user[3],
            "rolle":        user[4],
        }

    conn.close()
    return None


def alle_benutzer_laden():
    """Lädt alle Benutzer."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT id, benutzername, email, vorname, nachname, "
        "rolle, erstellt_am, letzter_login, aktiv "
        "FROM benutzer ORDER BY id"
    )
    users = c.fetchall()
    conn.close()
    return users


def benutzer_loeschen(user_id):
    """Löscht einen Benutzer."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM benutzer WHERE id=? AND rolle!='admin'", (user_id,))
    conn.commit()
    conn.close()


def benutzer_aktualisieren(user_id, **kwargs):
    """Aktualisiert Benutzerdaten."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    updates = []
    values  = []

    for key, wert in kwargs.items():
        if key == "passwort":
            updates.append("passwort=?")
            values.append(hash_passwort(wert))
        elif key in ["email", "vorname", "nachname", "rolle", "aktiv"]:
            updates.append(f"{key}=?")
            values.append(wert)

    if updates:
        values.append(user_id)
        c.execute(
            f"UPDATE benutzer SET {', '.join(updates)} WHERE id=?",
            values
        )
        conn.commit()

    conn.close()


def passwort_aendern(user_id, neues_passwort):
    """Ändert das Passwort."""
    benutzer_aktualisieren(user_id, passwort=neues_passwort)


if __name__ == "__main__":
    user_db_erstellen()
    admin_erstellen()
    print("  Benutzer-DB bereit!")