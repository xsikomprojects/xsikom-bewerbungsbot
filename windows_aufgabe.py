import os
import subprocess
from datetime import datetime


def aufgabe_erstellen():
    """
    Erstellt eine Windows Aufgabenplanung
    die den Bot automatisch startet.
    """

    # Aktueller Pfad
    bot_pfad   = os.path.dirname(os.path.abspath(__file__))
    python_exe = os.path.join(bot_pfad, "venv", "Scripts", "python.exe")
    script     = os.path.join(bot_pfad, "auto_start.py")
    log_pfad   = os.path.join(bot_pfad, "bot_log.txt")

    print("\n  WINDOWS AUFGABENPLANUNG EINRICHTEN")
    print("  " + "="*50)
    print(f"  Bot-Ordner  : {bot_pfad}")
    print(f"  Python      : {python_exe}")
    print(f"  Script      : {script}")
    print("  " + "="*50)

    # Batch-Datei erstellen (einfacher Start)
    bat_pfad = os.path.join(bot_pfad, "start_bot.bat")
    with open(bat_pfad, "w") as f:
        f.write(f"@echo off\n")
        f.write(f"cd /d {bot_pfad}\n")
        f.write(f"echo Bot startet... >> {log_pfad}\n")
        f.write(f"echo %date% %time% >> {log_pfad}\n")
        f.write(
            f'"{python_exe}" "{script}" '
            f'>> "{log_pfad}" 2>&1\n'
        )

    print(f"\n  Batch-Datei erstellt: {bat_pfad}")

    print("\n  Aufgabenplanung Optionen:")
    print("  1. Taeglich um 08:00 Uhr")
    print("  2. Beim PC-Start (Login)")
    print("  3. Alle 6 Stunden")
    print("  4. Alle (1, 2 und 3 zusammen)")
    print("  0. Abbrechen")

    wahl = input("\n  Auswahl: ").strip()

    if wahl == "0":
        print("  Abgebrochen.")
        return

    aufgaben = []

    if wahl in ["1", "4"]:
        aufgaben.append({
            "name":    "BewerbungsBot_Taeglich",
            "trigger": "DAILY",
            "zeit":    "08:00",
        })

    if wahl in ["2", "4"]:
        aufgaben.append({
            "name":    "BewerbungsBot_PC_Start",
            "trigger": "ONLOGON",
            "zeit":    None,
        })

    if wahl in ["3", "4"]:
        aufgaben.append({
            "name":    "BewerbungsBot_6h",
            "trigger": "HOURLY",
            "zeit":    "6",
        })

    for aufgabe in aufgaben:
        try:
            if aufgabe["trigger"] == "DAILY":
                cmd = (
                    f'schtasks /create /tn "{aufgabe["name"]}" '
                    f'/tr "{bat_pfad}" '
                    f'/sc DAILY '
                    f'/st {aufgabe["zeit"]} '
                    f'/f'
                )
            elif aufgabe["trigger"] == "ONLOGON":
                cmd = (
                    f'schtasks /create /tn "{aufgabe["name"]}" '
                    f'/tr "{bat_pfad}" '
                    f'/sc ONLOGON '
                    f'/f'
                )
            elif aufgabe["trigger"] == "HOURLY":
                cmd = (
                    f'schtasks /create /tn "{aufgabe["name"]}" '
                    f'/tr "{bat_pfad}" '
                    f'/sc HOURLY '
                    f'/mo {aufgabe["zeit"]} '
                    f'/f'
                )

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"  Aufgabe erstellt: {aufgabe['name']}")
            else:
                print(f"  Fehler bei: {aufgabe['name']}")
                print(f"  {result.stderr}")

        except Exception as e:
            print(f"  Fehler: {e}")

    print("\n  " + "="*50)
    print("  AUFGABENPLANUNG ABGESCHLOSSEN!")
    print("  " + "="*50)
    print("\n  Bot wird jetzt automatisch gestartet:")

    if wahl in ["1", "4"]:
        print("  - Jeden Tag um 08:00 Uhr")
    if wahl in ["2", "4"]:
        print("  - Bei jedem PC-Start")
    if wahl in ["3", "4"]:
        print("  - Alle 6 Stunden")

    print(f"\n  Log-Datei: {log_pfad}")
    print("\n  Aufgaben pruefen mit:")
    print("  schtasks /query /tn BewerbungsBot*")


def aufgabe_entfernen():
    """Entfernt alle Bot-Aufgaben."""
    aufgaben = [
        "BewerbungsBot_Taeglich",
        "BewerbungsBot_PC_Start",
        "BewerbungsBot_6h",
    ]

    print("\n  Entferne alle Bot-Aufgaben...")

    for name in aufgaben:
        try:
            cmd    = f'schtasks /delete /tn "{name}" /f'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"  Entfernt: {name}")
            else:
                print(f"  Nicht gefunden: {name}")
        except Exception as e:
            print(f"  Fehler: {e}")

    print("\n  Alle Aufgaben entfernt!")


def aufgaben_anzeigen():
    """Zeigt alle Bot-Aufgaben an."""
    print("\n  Aktive Bot-Aufgaben:")
    print("  " + "="*50)
    os.system("schtasks /query /fo LIST /v | findstr BewerbungsBot")
    print("  " + "="*50)


if __name__ == "__main__":
    print("\n  WINDOWS AUFGABENPLANUNG")
    print("  1. Aufgaben erstellen")
    print("  2. Aufgaben anzeigen")
    print("  3. Aufgaben entfernen")
    wahl = input("  Auswahl: ").strip()

    if wahl == "1":
        aufgabe_erstellen()
    elif wahl == "2":
        aufgaben_anzeigen()
    elif wahl == "3":
        aufgabe_entfernen()