"""
WhatsApp Benachrichtigungen via Twilio API
Kostenlos testen: https://www.twilio.com/try-twilio
"""
from datetime import datetime

# ============================================================
# TWILIO KONFIGURATION
# Kostenlos registrieren auf: https://www.twilio.com
# ============================================================
TWILIO_CONFIG = {
    "account_sid": "DEIN_TWILIO_ACCOUNT_SID",
    "auth_token":  "DEIN_TWILIO_AUTH_TOKEN",
    "von":         "whatsapp:+14155238886",  # Twilio Sandbox
    "an":          "whatsapp:+49178XXXXXXX", # Deine Nummer
    "aktiv":       False,  # True wenn konfiguriert
}


def whatsapp_senden(nachricht):
    """Sendet WhatsApp Nachricht via Twilio."""
    if not TWILIO_CONFIG["aktiv"]:
        print("  WhatsApp: Nicht konfiguriert")
        return False

    try:
        from twilio.rest import Client

        client = Client(
            TWILIO_CONFIG["account_sid"],
            TWILIO_CONFIG["auth_token"]
        )

        msg = client.messages.create(
            body=nachricht,
            from_=TWILIO_CONFIG["von"],
            to=TWILIO_CONFIG["an"]
        )

        print(f"  WhatsApp gesendet: {msg.sid}")
        return True

    except ImportError:
        print("  Twilio nicht installiert!")
        print("  -> pip install twilio")
        return False

    except Exception as e:
        print(f"  WhatsApp Fehler: {e}")
        return False


def whatsapp_neue_stelle(firma, position, standort):
    """WhatsApp bei neuer Stelle."""
    msg = (
        f"Neue Stelle gefunden!\n\n"
        f"Firma    : {firma}\n"
        f"Position : {position}\n"
        f"Standort : {standort}\n"
        f"Zeit     : {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    return whatsapp_senden(msg)


def whatsapp_bewerbung_gesendet(firma, email):
    """WhatsApp bei gesendeter Bewerbung."""
    msg = (
        f"Bewerbung gesendet!\n\n"
        f"Firma : {firma}\n"
        f"Email : {email}\n"
        f"Zeit  : {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    return whatsapp_senden(msg)


def whatsapp_erinnerung(firma, tage):
    """WhatsApp Erinnerung."""
    msg = (
        f"Erinnerung - Keine Antwort!\n\n"
        f"Firma    : {firma}\n"
        f"Gesendet : vor {tage} Tagen\n\n"
        f"Vielleicht nachfragen, Komi?"
    )
    return whatsapp_senden(msg)


def whatsapp_einladung(firma):
    """WhatsApp bei Einladung."""
    msg = (
        f"EINLADUNG ERHALTEN!\n\n"
        f"Firma : {firma}\n"
        f"Zeit  : {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Glueckwunsch, Komi! Viel Erfolg!"
    )
    return whatsapp_senden(msg)


def whatsapp_testen():
    """Testet WhatsApp Verbindung."""
    print("\n  WhatsApp Test...")

    if not TWILIO_CONFIG["aktiv"]:
        print("  WhatsApp ist nicht aktiv!")
        print("\n  So einrichten:")
        print("  1. https://www.twilio.com registrieren")
        print("  2. Account SID und Auth Token kopieren")
        print("  3. WhatsApp Sandbox aktivieren")
        print("  4. In whatsapp_sender.py eintragen")
        print("  5. aktiv: True setzen")
        return False

    return whatsapp_senden(
        f"Bewerbungsbot Test!\n\n"
        f"Hallo Komi!\n"
        f"WhatsApp ist aktiv!\n"
        f"Zeit: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )


if __name__ == "__main__":
    whatsapp_testen()