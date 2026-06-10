"""
Lizenz-Manager fuer Freemium/Premium
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_NAME = "bewerbungen.db"


# ============================================================
# LIMITS FÜR FREEMIUM/PREMIUM
# ============================================================
LIMITS = {
    "free": {
        "bewerbungen_pro_monat":  5,
        "lebenslauf_vorlagen":    1,
        "jobportale":             3,
        "staedte":                10,
        "auto_bewerbung":         False,
        "whatsapp":               False,
        "excel_export":           False,
        "charts":                 False,
        "nachfass_auto":          False,
        "aaliyah_premium":        False,
        "werbung":                True,
        "preis":                  0,
    },
    "premium": {
        "bewerbungen_pro_monat":  999999,
        "lebenslauf_vorlagen":    10,
        "jobportale":             8,
        "staedte":                30,
        "auto_bewerbung":         True,
        "whatsapp":               True,
        "excel_export":           True,
        "charts":                 True,
        "nachfass_auto":          True,
        "aaliyah_premium":        True,
        "werbung":                False,
        "preis":                  1.99,
    },
    "premium_jahr": {
        "bewerbungen_pro_monat":  999999,
        "lebenslauf_vorlagen":    10,
        "jobportale":             8,
        "staedte":                30,
        "auto_bewerbung":         True,
        "whatsapp":               True,
        "excel_export":           True,
        "charts":                 True,
        "nachfass_auto":          True,
        "aaliyah_premium":        True,
        "werbung":                False,
        "preis":                  19.99,
    },
}


def lizenz_tabelle_erstellen():
    """Erstellt Lizenz-Tabelle."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS lizenzen (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzer_id   INTEGER,
            typ           TEXT DEFAULT 'free',
            start_datum   TEXT,
            end_datum     TEXT,
            zahlung_id    TEXT,
            aktiv         INTEGER DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS nutzung (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            benutzer_id   INTEGER,
            aktion        TEXT,
            datum         TEXT
        )
    """)
    conn.commit()
    conn.close()


def lizenz_pruefen(benutzer_id):
    """Prueft welche Lizenz ein Benutzer hat."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT typ, end_datum
        FROM lizenzen
        WHERE benutzer_id=? AND aktiv=1
        ORDER BY id DESC LIMIT 1
    """, (benutzer_id,))
    r = c.fetchone()
    conn.close()

    if not r:
        return "free"

    typ, end = r
    if end:
        try:
            end_dt = datetime.fromisoformat(end)
            if end_dt < datetime.now():
                return "free"  # Abgelaufen
        except Exception:
            pass

    return typ


def lizenz_aktivieren(benutzer_id, typ="premium", monate=1):
    """Aktiviert eine Premium-Lizenz."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Alte Lizenzen deaktivieren
    c.execute("UPDATE lizenzen SET aktiv=0 WHERE benutzer_id=?", (benutzer_id,))

    start = datetime.now()
    if typ == "premium_jahr":
        end = start + timedelta(days=365)
    else:
        end = start + timedelta(days=30 * monate)

    c.execute("""
        INSERT INTO lizenzen
        (benutzer_id, typ, start_datum, end_datum, aktiv)
        VALUES (?, ?, ?, ?, 1)
    """, (
        benutzer_id, typ,
        start.isoformat(),
        end.isoformat()
    ))

    conn.commit()
    conn.close()
    return True


def feature_pruefen(benutzer_id, feature):
    """Prueft ob ein Feature verfuegbar ist."""
    typ = lizenz_pruefen(benutzer_id)
    limits = LIMITS.get(typ, LIMITS["free"])
    return limits.get(feature, False)


def limit_pruefen(benutzer_id, feature):
    """Prueft Limit fuer Feature (z.B. Bewerbungen pro Monat)."""
    typ = lizenz_pruefen(benutzer_id)
    limits = LIMITS.get(typ, LIMITS["free"])
    return limits.get(feature, 0)


def nutzung_zaehlen(benutzer_id, aktion):
    """Zaehlt Nutzung einer Aktion."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO nutzung (benutzer_id, aktion, datum) VALUES (?, ?, ?)",
        (benutzer_id, aktion, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def nutzung_monat(benutzer_id, aktion):
    """Zaehlt Nutzung im aktuellen Monat."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    monat_start = datetime.now().replace(day=1).isoformat()
    c.execute("""
        SELECT COUNT(*) FROM nutzung
        WHERE benutzer_id=? AND aktion=? AND datum >= ?
    """, (benutzer_id, aktion, monat_start))
    r = c.fetchone()[0]
    conn.close()
    return r


def kann_bewerbung_senden(benutzer_id):
    """Prueft ob Benutzer noch Bewerbungen senden kann."""
    aktuell = nutzung_monat(benutzer_id, "bewerbung")
    limit = limit_pruefen(benutzer_id, "bewerbungen_pro_monat")
    return aktuell < limit, aktuell, limit


def lizenz_info(benutzer_id):
    """Gibt Lizenz-Info zurueck."""
    typ = lizenz_pruefen(benutzer_id)
    limits = LIMITS.get(typ, LIMITS["free"])
    bew_aktuell = nutzung_monat(benutzer_id, "bewerbung")

    return {
        "typ":              typ,
        "name":             {
            "free":          "Kostenlos",
            "premium":       "Premium",
            "premium_jahr":  "Premium Jahr"
        }.get(typ, "Kostenlos"),
        "preis":            limits["preis"],
        "bewerbungen":      f"{bew_aktuell}/{limits['bewerbungen_pro_monat']}",
        "limits":           limits,
    }


# Beim Import erstellen
lizenz_tabelle_erstellen()


if __name__ == "__main__":
    print("Lizenz-Manager Tests")
    print(f"Free: {LIMITS['free']}")
    print(f"Premium: {LIMITS['premium']}")