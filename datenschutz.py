"""
DSGVO Datenschutz-Modul
"""
import json
import os
from datetime import datetime


DATENSCHUTZ_TEXT = """
DATENSCHUTZERKLAERUNG NACH DSGVO

XsiKOM-BewerbungsBOT
Stand: """ + datetime.now().strftime("%d.%m.%Y") + """

=====================================================

1. VERANTWORTLICHER

Komi Tevi
Am Koenigsfloss 12
55252 Mainz-Kastel
Deutschland

E-Mail:  xsikom.projects@gmail.com
Telefon: +49 178 8977320

=====================================================

2. ART DER GESPEICHERTEN DATEN

Wir speichern folgende Daten:

PERSOENLICHE DATEN:
- Name (Vor- und Nachname)
- E-Mail Adresse
- Telefonnummer
- Adresse
- Geburtsdatum

BEWERBUNGSDATEN:
- Lebenslauf
- Zeugnisse
- Zertifikate
- Anschreiben
- Bewerbungshistorie

LOGIN-DATEN:
- Benutzername
- Passwort (verschluesselt mit PBKDF2 SHA-256)
- Letzter Login
- IP-Adresse (anonymisiert)

=====================================================

3. ZWECK DER DATENVERARBEITUNG

Ihre Daten werden ausschliesslich verwendet fuer:
- Erstellung von Bewerbungsunterlagen
- Versand von Bewerbungen
- Verwaltung Ihres Profils
- Statistische Auswertungen (anonymisiert)

=====================================================

4. RECHTSGRUNDLAGE

Die Verarbeitung erfolgt auf Basis von:
- Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)
- Art. 6 Abs. 1 lit. b DSGVO (Vertrag)

=====================================================

5. SPEICHERDAUER

- Aktive Konten: Dauer der Nutzung
- Inaktive Konten: 12 Monate
- Bewerbungen: Bis zu 24 Monate
- Logs: 30 Tage

=====================================================

6. IHRE RECHTE NACH DSGVO

Sie haben das Recht auf:
- Auskunft (Art. 15 DSGVO)
- Berichtigung (Art. 16 DSGVO)
- Loeschung (Art. 17 DSGVO)
- Einschraenkung (Art. 18 DSGVO)
- Datenuebertragbarkeit (Art. 20 DSGVO)
- Widerspruch (Art. 21 DSGVO)

Anfragen bitte an: xsikom.projects@gmail.com

=====================================================

7. DATENSICHERHEIT

Wir verwenden:
- SSL/TLS Verschluesselung
- PBKDF2 SHA-256 Passwort-Hashing
- Fernet Symmetrische Verschluesselung
- Rate Limiting gegen Brute-Force
- Session Management mit Timeout
- Audit Logging

=====================================================

8. DRITTE PARTEIEN

Folgende Dienste werden genutzt:
- Gmail (Google) - E-Mail-Versand
- Telegram - Benachrichtigungen
- Jobportale - Stellensuche

Daten werden nur uebertragen wenn noetig.

=====================================================

9. COOKIES & TRACKING

Die Desktop-App speichert lokal:
- Login-Token (verschluesselt)
- Einstellungen
- Nutzungsstatistiken (anonym)

Keine Tracking-Cookies oder Werbung!

=====================================================

10. AUFSICHTSBEHOERDE

Bei Beschwerden wenden Sie sich an:

Landesbeauftragter fuer Datenschutz
Rheinland-Pfalz
Hintere Bleiche 34
55116 Mainz

=====================================================
"""


IMPRESSUM = """
IMPRESSUM

Angaben gemaess § 5 TMG:

Komi Tevi
Am Koenigsfloss 12
55252 Mainz-Kastel
Deutschland

KONTAKT:
Telefon: +49 178 8977320
E-Mail:  xsikom.projects@gmail.com

VERANTWORTLICH FUER DEN INHALT:
Komi Tevi (Anschrift wie oben)

=====================================================

HAFTUNGSAUSSCHLUSS:

INHALTE:
Die Inhalte wurden mit groesster Sorgfalt erstellt.
Fuer Richtigkeit, Vollstaendigkeit und Aktualitaet
koennen wir jedoch keine Gewaehr uebernehmen.

LINKS:
Unsere App enthaelt Links zu externen Webseiten
(Jobportale). Auf deren Inhalte haben wir keinen
Einfluss. Fuer die Inhalte verlinkter Seiten ist
stets der jeweilige Anbieter verantwortlich.

URHEBERRECHT:
Die durch die Betreiber erstellten Inhalte und
Werke unterliegen dem deutschen Urheberrecht.

=====================================================

STREITSCHLICHTUNG:

Die Europaeische Kommission stellt eine Plattform
zur Online-Streitbeilegung (OS) bereit:
https://ec.europa.eu/consumers/odr

Wir sind nicht bereit oder verpflichtet,
an Streitbeilegungsverfahren teilzunehmen.

=====================================================

XsiKOM-BewerbungsBOT (c) """ + str(datetime.now().year) + """
Alle Rechte vorbehalten.
"""


AGB = """
ALLGEMEINE GESCHAEFTSBEDINGUNGEN (AGB)

XsiKOM-BewerbungsBOT
Stand: """ + datetime.now().strftime("%d.%m.%Y") + """

=====================================================

§ 1 GELTUNGSBEREICH

Diese AGB gelten fuer alle Nutzer des
XsiKOM-BewerbungsBOT.

=====================================================

§ 2 LEISTUNGSBESCHREIBUNG

KOSTENLOSE VERSION (Freemium):
- 5 Bewerbungen pro Monat
- 1 Lebenslauf-Vorlage
- Basis Aaliyah KI
- 3 Jobportale
- Telegram-Benachrichtigungen
- 10 Stadtsuchen

PREMIUM VERSION (1.99 EUR/Monat):
- UNBEGRENZTE Bewerbungen
- 10 Lebenslauf-Vorlagen
- Premium Aaliyah KI mit allen Tipps
- ALLE 8 Jobportale
- WhatsApp Benachrichtigungen
- 30 Staedte
- Excel/PDF Export
- Charts & Statistiken
- Auto-Bewerbung
- Nachfass-E-Mails automatisch
- Werbefrei

=====================================================

§ 3 VERTRAGSABSCHLUSS

Der Vertrag kommt durch Registrierung zustande.

=====================================================

§ 4 PREISE & ZAHLUNG

Premium-Abo: 1.99 EUR / Monat
- Monatlich kuendbar
- Keine Mindestlaufzeit
- Zahlung via PayPal, Kreditkarte, SEPA

Jaehrliches Abo: 19.99 EUR / Jahr (16% Rabatt!)

=====================================================

§ 5 WIDERRUFSRECHT

Sie haben 14 Tage Widerrufsrecht ab Vertragsschluss.

=====================================================

§ 6 KUENDIGUNG

Jederzeit kuendbar.
Daten werden nach 30 Tagen geloescht.

=====================================================

§ 7 HAFTUNG

Keine Garantie fuer Erfolg von Bewerbungen!
App ist Hilfsmittel - keine Vermittlungsagentur.

=====================================================

§ 8 DATENSCHUTZ

Siehe separate Datenschutzerklaerung.

=====================================================

§ 9 GERICHTSSTAND

Gerichtsstand: Mainz, Deutschland.

=====================================================
"""


def datenschutz_text():
    return DATENSCHUTZ_TEXT


def impressum_text():
    return IMPRESSUM


def agb_text():
    return AGB


def einwilligung_speichern(benutzer, agb=False, datenschutz=False):
    """Speichert Einwilligung des Nutzers."""
    pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "benutzer_daten",
        benutzer,
        "einwilligung.json"
    )
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    daten = {
        "datum":        datetime.now().isoformat(),
        "agb":          agb,
        "datenschutz":  datenschutz,
        "version":      "1.0",
    }
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=2)


def einwilligung_pruefen(benutzer):
    """Prueft ob Einwilligung vorhanden."""
    pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "benutzer_daten",
        benutzer,
        "einwilligung.json"
    )
    if not os.path.exists(pfad):
        return None
    with open(pfad, "r", encoding="utf-8") as f:
        return json.load(f)


def daten_export_dsgvo(benutzer):
    """DSGVO-konformer Daten-Export."""
    import sqlite3
    from database import DB_NAME

    daten = {
        "export_datum": datetime.now().isoformat(),
        "benutzer":     benutzer,
        "bewerbungen":  [],
        "tracker":      [],
        "stellen":      [],
    }

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM bewerbungen")
        daten["bewerbungen"] = c.fetchall()
        c.execute("SELECT * FROM tracker")
        daten["tracker"] = c.fetchall()
        c.execute("SELECT * FROM stellen")
        daten["stellen"] = c.fetchall()
        conn.close()
    except Exception:
        pass

    # Profil laden
    from lebenslauf_editor import benutzer_daten_laden
    profil = benutzer_daten_laden(benutzer)
    if profil:
        daten["profil"] = profil

    # Export-Datei
    export_pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"DSGVO_Export_{benutzer}_{datetime.now().strftime('%Y%m%d')}.json"
    )
    with open(export_pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2, default=str)

    return export_pfad


def daten_loeschen_dsgvo(benutzer):
    """DSGVO Recht auf Vergessenwerden."""
    import sqlite3
    import shutil
    from database import DB_NAME

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("DELETE FROM bewerbungen")
        c.execute("DELETE FROM tracker")
        c.execute("DELETE FROM benutzer WHERE benutzername=?", (benutzer,))
        conn.commit()
        conn.close()
    except Exception:
        pass

    # Profil-Ordner löschen
    pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "benutzer_daten",
        benutzer
    )
    if os.path.exists(pfad):
        shutil.rmtree(pfad)

    return True


if __name__ == "__main__":
    print("DSGVO Modul OK")
    print(f"Datenschutz: {len(DATENSCHUTZ_TEXT)} Zeichen")
    print(f"Impressum: {len(IMPRESSUM)} Zeichen")
    print(f"AGB: {len(AGB)} Zeichen")