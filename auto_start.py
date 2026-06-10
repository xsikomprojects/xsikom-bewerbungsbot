import schedule
import time
import os
from datetime import datetime
from job_suche import vollsuche_starten, it_firmen_hinzufuegen
from email_sender import bewerbung_senden
from anschreiben_generator import anschreiben_erstellen
from database import stellen_laden
from statistiken import statistiken_komplett
from telegram_sender import telegram_senden
from excel_export import excel_export


def morgen_routine():
    """Wird jeden Morgen um 08:00 Uhr ausgeführt."""
    print(f"\n{'='*60}")
    print(f"  MORGEN-ROUTINE - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    telegram_senden(
        f"<b>Guten Morgen, Komi!</b>\n\n"
        f"Bewerbungsbot startet jetzt...\n"
        f"Zeit: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # 1. Neue Stellen suchen
    print("\n  Suche neue Stellen...")
    gesamt = vollsuche_starten()

    # 2. IT-Firmen aktualisieren
    print("\n  IT-Firmen aktualisieren...")
    it_firmen_hinzufuegen()

    # 3. Statistiken
    stats = statistiken_komplett()

    # 4. Excel Export
    print("\n  Excel Export...")
    excel_export()

    # 5. Zusammenfassung via Telegram
    telegram_senden(
        f"<b>Morgen-Routine abgeschlossen!</b>\n\n"
        f"Neue Stellen : {gesamt}\n"
        f"Stellen ges. : {stats['stellen']}\n"
        f"Bewerbungen  : {stats['gesamt']}\n\n"
        f"Uhr: {datetime.now().strftime('%H:%M')}"
    )

    print(f"\n  Morgen-Routine abgeschlossen!")


def abend_routine():
    """Wird jeden Abend um 18:00 Uhr ausgeführt."""
    print(f"\n{'='*60}")
    print(f"  ABEND-ROUTINE - {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    # Statistiken
    stats = statistiken_komplett()

    # Excel Export
    excel_export()

    telegram_senden(
        f"<b>Tagesabschluss - Komi Tevi</b>\n\n"
        f"Stellen heute : {stats['stellen']}\n"
        f"Heute gesendet: {stats['heute']}\n"
        f"Gesamt gesendet: {stats['gesamt']}\n\n"
        f"Gute Nacht!"
    )


def bewerbungen_automatisch_senden():
    """Sendet Bewerbungen an alle Stellen mit E-Mail."""
    print("\n  Auto-Bewerbung startet...")

    stellen    = stellen_laden()
    mit_email  = [s for s in stellen if s[4] and s[8] == "neu"]

    if not mit_email:
        print("  Keine neuen Stellen mit E-Mail.")
        return

    ok  = 0
    err = 0

    for s in mit_email[:10]:  # Max 10 pro Durchgang
        firma    = s[2] if s[2] else "Unbekannt"
        position = s[1] if s[1] else "IT-Praktikant"
        email    = s[4]

        try:
            pfad = anschreiben_erstellen(
                firma=firma,
                position=position,
                bereich="allgemein"
            )
        except Exception:
            pfad = None

        result = bewerbung_senden(
            empfaenger=email,
            firma=firma,
            position=position,
            anschreiben_pfad=pfad,
            trockenlauf=False
        )

        if result:
            ok += 1
        else:
            err += 1

        time.sleep(30)

    telegram_senden(
        f"<b>Auto-Bewerbung abgeschlossen!</b>\n\n"
        f"Gesendet : {ok}\n"
        f"Fehler   : {err}"
    )


def auto_start():
    """Startet den automatischen täglichen Betrieb."""

    print("\n" + "="*60)
    print("  AUTO-START - IT-PRAKTIKUM BEWERBUNGSBOT")
    print("  Komi Tevi - Version 3.0")
    print("="*60)
    print("\n  Zeitplan:")
    print("  08:00 Uhr → Morgen-Routine (Suche + Stellen)")
    print("  10:00 Uhr → Bewerbungen automatisch senden")
    print("  18:00 Uhr → Abend-Routine (Statistiken)")
    print("\n  Bot laeuft... (Strg+C zum Beenden)")
    print("="*60)

    telegram_senden(
        "<b>Auto-Start aktiviert!</b>\n\n"
        "Bot laeuft im Hintergrund.\n"
        "Zeitplan:\n"
        "08:00 - Morgen-Routine\n"
        "10:00 - Bewerbungen senden\n"
        "18:00 - Abend-Routine"
    )

    # Zeitplan festlegen
    schedule.every().day.at("08:00").do(morgen_routine)
    schedule.every().day.at("10:00").do(bewerbungen_automatisch_senden)
    schedule.every().day.at("18:00").do(abend_routine)

    # Sofort einmal ausführen
    print("\n  Starte erste Routine jetzt...")
    morgen_routine()

    # Endlosschleife
    while True:
        schedule.run_pending()
        jetzt = datetime.now().strftime("%H:%M:%S")
        print(
            f"\r  Laeuft... {jetzt} | "
            f"Naechste Aufgabe: {schedule.next_run()}",
            end=""
        )
        time.sleep(60)


if __name__ == "__main__":
    try:
        auto_start()
    except KeyboardInterrupt:
        print("\n\n  Auto-Start beendet.")
        telegram_senden(
            "<b>Auto-Start gestoppt!</b>\n"
            "Bot wurde manuell beendet."
        )