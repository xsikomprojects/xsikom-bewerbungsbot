import os
from config import (
    config_anzeigen, config_pruefen,
    PERSOENLICHE_DATEN, IT_FIRMEN
)
from database import (
    create_database, stelle_speichern, stellen_laden
)
from lebenslauf_generator import (
    lebenslauf_erstellen, zeugnisse_erstellen,
    zertifikate_erstellen, unterlagen_pruefen
)
from anschreiben_generator import anschreiben_erstellen
from email_sender import bewerbung_senden, verbindung_testen
from job_suche import (
    vollsuche_starten, stellen_anzeigen,
    it_firmen_hinzufuegen
)
from statistiken import statistiken_komplett
from telegram_sender import telegram_testen, telegram_senden
from excel_export import excel_export
from bewerbungs_tracker import (
    tracker_anzeigen, antwort_interaktiv,
    erinnerungen_pruefen, bewerbung_tracken,
    tracker_tabellen_erstellen
)
from windows_aufgabe import (
    aufgabe_erstellen, aufgaben_anzeigen,
    aufgabe_entfernen
)
from nachfass_email import (
    automatische_nachfass_pruefen, nachfass_manuell
)
from whatsapp_sender import whatsapp_testen
from kalender import (
    vorstellungsgespraech_eintragen,
    erinnerung_eintragen, termine_anzeigen,
    naechste_schritte_kalender
)
from charts import charts_erstellen
from firmen_suche import (
    alle_firmen_durchsuchen, eigene_url_durchsuchen
)


def banner():
    os.system("cls" if os.name == "nt" else "clear")
    print("\n" + "="*65)
    print("  IT-PRAKTIKUM BEWERBUNGSBOT  -  Komi Tevi")
    print("  Version 6.0 - ULTIMATE COMPLETE")
    print("="*65)
    print(
        f"  Bewerber  : "
        f"{PERSOENLICHE_DATEN['vorname']} "
        f"{PERSOENLICHE_DATEN['nachname']}"
    )
    print(f"  Gmail     : xsikom.projects@gmail.com")
    print(f"  Standort  : {PERSOENLICHE_DATEN['stadt']}")
    print(f"  IT-Firmen : {len(IT_FIRMEN)} bekannte Firmen")
    print("="*65)


def menue():
    print("\n  HAUPTMENUE - Version 6.0")
    print("  " + "="*52)
    print("  STELLENSUCHE")
    print("  1.  Automatische Suche (8 Portale)")
    print("  2.  Firmen-Webseiten durchsuchen")
    print("  3.  Eigene Firmen-URL durchsuchen")
    print("  4.  Gefundene Stellen anzeigen")
    print("  5.  IT-Firmenliste hinzufuegen (20 Firmen)")
    print("  6.  Stelle manuell hinzufuegen")
    print("  " + "-"*52)
    print("  BEWERBUNGEN")
    print("  7.  Anschreiben erstellen (PDF)")
    print("  8.  Einzelne Bewerbung senden")
    print("  9.  Massenbewerbung Trockenlauf")
    print("  10. Massenbewerbung LIVE senden")
    print("  11. Nachfass-E-Mail senden (2 Wochen)")
    print("  12. Automatische Nachfass pruefen")
    print("  " + "-"*52)
    print("  TRACKER & KALENDER")
    print("  13. Bewerbungs-Tracker anzeigen")
    print("  14. Antwort/Einladung eintragen")
    print("  15. Erinnerungen pruefen (14 Tage)")
    print("  16. Vorstellungsgespraech eintragen")
    print("  17. Erinnerung erstellen")
    print("  18. Termine anzeigen")
    print("  " + "-"*52)
    print("  AUSWERTUNG & EXPORT")
    print("  19. Statistiken detailliert")
    print("  20. Charts & Grafiken erstellen")
    print("  21. Excel Export")
    print("  " + "-"*52)
    print("  TOOLS & AUTOMATISIERUNG")
    print("  22. E-Mail Verbindung testen")
    print("  23. Telegram testen")
    print("  24. WhatsApp testen")
    print("  25. PDFs neu erstellen")
    print("  26. Unterlagen pruefen")
    print("  27. Windows Aufgabenplanung")
    print("  28. Kalender Grundeintraege erstellen")
    print("  29. AUTO-START starten")
    print("  30. Konfiguration anzeigen")
    print("  " + "-"*52)
    print("  0.  Beenden")
    print("  " + "="*52)


def massenbewerbung(trockenlauf=True):
    stellen    = stellen_laden()
    mit_email  = [s for s in stellen if s[4]]
    ohne_email = len(stellen) - len(mit_email)

    print(f"\n  {'='*50}")
    print(f"  MASSENBEWERBUNG")
    print(f"  {'='*50}")
    print(f"  Stellen gesamt : {len(stellen)}")
    print(f"  Mit E-Mail     : {len(mit_email)}")
    print(f"  Ohne E-Mail    : {ohne_email}")
    print(
        f"  Betreff        : Bewerbung: Pflichtpraktikum\n"
        f"                   als IT-Fachtechniker / "
        f"Netzwerktechniker"
    )

    if not mit_email:
        print("\n  Keine Stellen mit E-Mail!")
        print("  -> Option 5 : IT-Firmenliste")
        print("  -> Option 6 : Manuell hinzufuegen")
        print("  -> Option 2 : Firmen-Webseiten")
        return

    modus = "TROCKENLAUF" if trockenlauf else "LIVE"
    print(f"\n  Modus: {modus}")

    if not trockenlauf:
        print("  ACHTUNG: Echte E-Mails werden gesendet!")

    best = input("\n  Fortfahren? (ja/nein): ").strip().lower()
    if best not in ["ja", "j"]:
        print("  Abgebrochen.")
        return

    ok  = 0
    err = 0

    for i, s in enumerate(mit_email, 1):
        firma    = s[2] if s[2] else "Unbekannt"
        position = "IT-Fachtechniker / Netzwerktechniker"
        email    = s[4]

        print(f"\n  [{i}/{len(mit_email)}] {firma}")

        try:
            pfad = anschreiben_erstellen(
                firma=firma,
                position=position,
                bereich="allgemein"
            )
        except Exception as e:
            print(f"  Anschreiben Fehler: {e}")
            pfad = None

        result = bewerbung_senden(
            empfaenger=email,
            firma=firma,
            position=position,
            anschreiben_pfad=pfad,
            trockenlauf=trockenlauf
        )

        if result:
            ok += 1
            if not trockenlauf:
                bewerbung_tracken(firma, position, email)
        else:
            err += 1

        if not trockenlauf:
            import time
            print("  Warte 30 Sekunden...")
            time.sleep(30)

    print(f"\n  {'='*50}")
    print(f"  ERGEBNIS")
    print(f"  Erfolgreich : {ok}")
    print(f"  Fehler      : {err}")
    print(f"  {'='*50}")

    if not trockenlauf:
        telegram_senden(
            f"<b>Massenbewerbung fertig!</b>\n\n"
            f"Erfolgreich : {ok}\n"
            f"Fehler      : {err}\n\n"
            f"Weiter so, Komi!"
        )


def main():
    banner()
    tracker_tabellen_erstellen()

    fehler, warnungen = config_pruefen()
    if fehler:
        for f in fehler:
            print(f"  FEHLER: {f}")
        input("  Enter zum Beenden...")
        return

    create_database()

    while True:
        menue()
        wahl = input("\n  Auswahl: ").strip()

        # ── STELLENSUCHE ──────────────────────────────
        if wahl == "1":
            vollsuche_starten()

        elif wahl == "2":
            alle_firmen_durchsuchen()

        elif wahl == "3":
            eigene_url_durchsuchen()

        elif wahl == "4":
            stellen_anzeigen()

        elif wahl == "5":
            it_firmen_hinzufuegen()

        elif wahl == "6":
            print("\n  Stelle manuell hinzufuegen:")
            titel    = input("  Titel    : ").strip()
            firma    = input("  Firma    : ").strip()
            standort = input("  Standort : ").strip()
            email    = input("  E-Mail   : ").strip()
            url      = input("  URL      : ").strip()
            sid = stelle_speichern(
                titel, firma, standort,
                email, url, "Manuell"
            )
            if sid:
                print(f"  Stelle gespeichert! ID: {sid}")
            else:
                print("  Stelle bereits vorhanden!")

        # ── BEWERBUNGEN ───────────────────────────────
        elif wahl == "7":
            firma = input("\n  Firma    : ").strip()
            print("  Bereich: 1=Netzwerk 2=Admin 3=Support 4=Allgemein")
            b       = input("  Auswahl [4]: ").strip()
            bmap    = {
                "1": "netzwerk", "2": "systemadmin",
                "3": "support",  "4": "allgemein"
            }
            bereich = bmap.get(b, "allgemein")
            pfad    = anschreiben_erstellen(
                firma=firma,
                position="IT-Fachtechniker / Netzwerktechniker",
                bereich=bereich
            )
            print(f"\n  Gespeichert: {pfad}")

        elif wahl == "8":
            firma  = input("\n  Firma    : ").strip()
            email  = input("  E-Mail   : ").strip()
            print("  Bereich: 1=Netzwerk 2=Admin 3=Support 4=Allgemein")
            b      = input("  Auswahl [4]: ").strip()
            bmap   = {
                "1": "netzwerk", "2": "systemadmin",
                "3": "support",  "4": "allgemein"
            }
            bereich = bmap.get(b, "allgemein")
            pfad    = anschreiben_erstellen(
                firma=firma,
                position="IT-Fachtechniker / Netzwerktechniker",
                bereich=bereich
            )
            result  = bewerbung_senden(
                empfaenger=email, firma=firma,
                position="IT-Fachtechniker / Netzwerktechniker",
                anschreiben_pfad=pfad,
                trockenlauf=False
            )
            if result:
                bewerbung_tracken(
                    firma,
                    "IT-Fachtechniker / Netzwerktechniker",
                    email
                )

        elif wahl == "9":
            massenbewerbung(trockenlauf=True)

        elif wahl == "10":
            print("\n  ACHTUNG: Echte E-Mails!")
            sicher = input("  Bist du sicher? (JA): ").strip()
            if sicher == "JA":
                massenbewerbung(trockenlauf=False)
            else:
                print("  Abgebrochen.")

        elif wahl == "11":
            nachfass_manuell()

        elif wahl == "12":
            automatische_nachfass_pruefen()

        # ── TRACKER & KALENDER ────────────────────────
        elif wahl == "13":
            tracker_anzeigen()

        elif wahl == "14":
            antwort_interaktiv()

        elif wahl == "15":
            erinnerungen_pruefen()

        elif wahl == "16":
            vorstellungsgespraech_eintragen()

        elif wahl == "17":
            erinnerung_eintragen()

        elif wahl == "18":
            termine_anzeigen()

        # ── AUSWERTUNG ────────────────────────────────
        elif wahl == "19":
            statistiken_komplett()

        elif wahl == "20":
            print("\n  Charts werden erstellt...")
            charts_erstellen()

        elif wahl == "21":
            excel_export()

        # ── TOOLS ────────────────────────────────────
        elif wahl == "22":
            verbindung_testen()

        elif wahl == "23":
            telegram_testen()

        elif wahl == "24":
            whatsapp_testen()

        elif wahl == "25":
            print("\n  PDFs werden erstellt...")
            lebenslauf_erstellen()
            zeugnisse_erstellen()
            zertifikate_erstellen()
            print("\n  Alle PDFs erstellt!")

        elif wahl == "26":
            unterlagen_pruefen()

        elif wahl == "27":
            print("\n  Windows Aufgabenplanung:")
            print("  1. Aufgaben erstellen")
            print("  2. Aufgaben anzeigen")
            print("  3. Aufgaben entfernen")
            w2 = input("  Auswahl: ").strip()
            if w2 == "1":
                aufgabe_erstellen()
            elif w2 == "2":
                aufgaben_anzeigen()
            elif w2 == "3":
                aufgabe_entfernen()

        elif wahl == "28":
            naechste_schritte_kalender()

        elif wahl == "29":
            print("\n  AUTO-START wird gestartet...")
            best = input("  Fortfahren? (ja/nein): ").strip().lower()
            if best in ["ja", "j"]:
                import subprocess
                subprocess.Popen(
                    ["python", "auto_start.py"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                print("  Auto-Start laeuft!")

        elif wahl == "30":
            config_anzeigen()

        elif wahl == "0":
            print(
                f"\n  Auf Wiedersehen, "
                f"{PERSOENLICHE_DATEN['vorname']}!"
            )
            print("  Viel Erfolg bei deinen Bewerbungen!")
            break

        else:
            print("\n  Ungueltige Eingabe! (0-30)")

        input("\n  Enter zum Fortfahren...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Bot beendet.")