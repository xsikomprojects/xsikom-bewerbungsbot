import sqlite3
from datetime import datetime
from database import DB_NAME


def statistiken_komplett():
    """Zeigt vollstaendige Bewerbungsstatistiken."""
    conn  = sqlite3.connect(DB_NAME)
    c     = conn.cursor()
    heute = datetime.now().strftime("%d.%m.%Y")

    # Stellen
    c.execute("SELECT COUNT(*) FROM stellen")
    stellen_gesamt = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM stellen WHERE status='neu'")
    stellen_neu = c.fetchone()[0]

    # Bewerbungen
    c.execute("SELECT COUNT(*) FROM bewerbungen")
    bew_gesamt = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM bewerbungen WHERE status='gesendet'")
    bew_gesendet = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM bewerbungen WHERE status='trockenlauf'")
    bew_test = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM bewerbungen WHERE status='fehler'")
    bew_fehler = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM bewerbungen WHERE datum LIKE ?",
        (f"%{heute}%",)
    )
    bew_heute = c.fetchone()[0]

    # Top Quellen
    c.execute("""
        SELECT quelle, COUNT(*) as anz
        FROM stellen
        GROUP BY quelle
        ORDER BY anz DESC
    """)
    top_quellen = c.fetchall()

    # Top Standorte
    c.execute("""
        SELECT standort, COUNT(*) as anz
        FROM stellen
        WHERE standort != ''
        GROUP BY standort
        ORDER BY anz DESC
        LIMIT 5
    """)
    top_standorte = c.fetchall()

    # Letzte Bewerbungen
    c.execute("""
        SELECT firma, position, status, datum
        FROM bewerbungen
        ORDER BY id DESC
        LIMIT 5
    """)
    letzte = c.fetchall()

    conn.close()

    # AUSGABE
    print("\n" + "="*55)
    print("  BEWERBUNGSSTATISTIKEN - Komi Tevi")
    print("="*55)

    print("\n  STELLEN")
    print("  " + "-"*40)
    print(f"  Gefunden gesamt  : {stellen_gesamt}")
    print(f"  Neu (unbeworben) : {stellen_neu}")

    print("\n  BEWERBUNGEN")
    print("  " + "-"*40)
    print(f"  Gesamt           : {bew_gesamt}")
    print(f"  Gesendet         : {bew_gesendet}")
    print(f"  Heute gesendet   : {bew_heute}")
    print(f"  Testlaeufe       : {bew_test}")
    print(f"  Fehler           : {bew_fehler}")

    if bew_gesamt > 0:
        quote = round((bew_gesendet / bew_gesamt) * 100, 1)
        print(f"  Erfolgsquote     : {quote}%")

    if top_quellen:
        print("\n  STELLEN NACH QUELLE")
        print("  " + "-"*40)
        for q in top_quellen:
            print(f"  {str(q[0]):<20} : {q[1]} Stellen")

    if top_standorte:
        print("\n  TOP STANDORTE")
        print("  " + "-"*40)
        for s in top_standorte:
            if s[0]:
                print(f"  {str(s[0]):<20} : {s[1]} Stellen")

    if letzte:
        print("\n  LETZTE BEWERBUNGEN")
        print("  " + "-"*40)
        for b in letzte:
            firma  = str(b[0])[:18] if b[0] else "N/A"
            pos    = str(b[1])[:18] if b[1] else "N/A"
            status = str(b[2])[:10] if b[2] else "N/A"
            datum  = str(b[3])[:16] if b[3] else "N/A"
            print(f"  {firma:<20} {pos:<20} {status:<12} {datum}")

    print("\n" + "="*55)

    return {
        "stellen":  stellen_gesamt,
        "gesamt":   bew_gesamt,
        "heute":    bew_heute,
        "antworten": 0,
        "einladungen": 0,
    }


if __name__ == "__main__":
    statistiken_komplett()