import requests
from datetime import datetime
from config import TELEGRAM_CONFIG


def telegram_senden(nachricht):
    """Sendet eine Nachricht via Telegram."""
    if not TELEGRAM_CONFIG["aktiv"]:
        return False

    token   = TELEGRAM_CONFIG["token"]
    chat_id = TELEGRAM_CONFIG["chat_id"]

    try:
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id":    chat_id,
            "text":       nachricht,
            "parse_mode": "HTML",
        }
        r = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            return True
        else:
            print(f"  Telegram Fehler: {r.status_code}")
            return False
    except Exception as e:
        print(f"  Telegram Fehler: {e}")
        return False


def telegram_neue_stelle(firma, position, standort, quelle):
    """Benachrichtigung bei neuer Stelle."""
    msg = (
        f"<b>Neue Stelle gefunden!</b>\n\n"
        f"Firma    : {firma}\n"
        f"Position : {position}\n"
        f"Standort : {standort}\n"
        f"Quelle   : {quelle}\n"
        f"Zeit     : {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    return telegram_senden(msg)


def telegram_bewerbung_gesendet(firma, position, email):
    """Benachrichtigung bei gesendeter Bewerbung."""
    msg = (
        f"<b>Bewerbung gesendet!</b>\n\n"
        f"Firma    : {firma}\n"
        f"Position : {position}\n"
        f"E-Mail   : {email}\n"
        f"Zeit     : {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    return telegram_senden(msg)


def telegram_statistiken(stats):
    """Sendet Statistiken via Telegram."""
    msg = (
        f"<b>Statistik - Bewerbungsbot</b>\n\n"
        f"Stellen gefunden   : {stats['stellen']}\n"
        f"Bewerbungen gesamt : {stats['gesamt']}\n"
        f"Heute gesendet     : {stats['heute']}\n\n"
        f"Weiter so, Komi!"
    )
    return telegram_senden(msg)


def telegram_testen():
    """Testet die Telegram Verbindung."""
    print("\n  Teste Telegram Verbindung...")
    print(f"  Token   : ...{TELEGRAM_CONFIG['token'][-10:]}")
    print(f"  Chat-ID : {TELEGRAM_CONFIG['chat_id']}")

    if not TELEGRAM_CONFIG["aktiv"]:
        print("  Telegram ist nicht aktiv!")
        print("  -> aktiv: True in config.py setzen")
        return False

    result = telegram_senden(
        f"<b>Bewerbungsbot Test</b>\n\n"
        f"Hallo Komi!\n"
        f"Dein Bewerbungsbot ist aktiv!\n"
        f"Zeit: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    if result:
        print("  Telegram Nachricht erfolgreich gesendet!")
        print("  Bitte Handy pruefen!")
        return True
    else:
        print("  Telegram Fehler!")
        print("  -> Token und Chat-ID in config.py pruefen")
        return False


if __name__ == "__main__":
    telegram_testen()