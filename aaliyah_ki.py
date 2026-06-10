"""
Aaliyah - KI Bewerbungs-Assistentin
"""
import sqlite3
from datetime import datetime
import random
import os

DB_NAME = "bewerbungen.db"


class Aaliyah:
    """KI-Assistentin für Bewerbungen."""

    NAME    = "Aaliyah"
    VERSION = "2.0"

    BEGRUESSUNG = [
        "Hallo! Ich bin Aaliyah, deine KI-Bewerbungsassistentin! Wie kann ich dir helfen?",
        "Hi! Aaliyah hier! Bereit für deine nächste Bewerbung?",
        "Willkommen! Ich bin Aaliyah - lass uns deine Bewerbungen optimieren!",
    ]

    TIPPS_BEWERBUNG = [
        "Passe dein Anschreiben immer an die konkrete Stelle an!",
        "Erwähne im Anschreiben konkrete Projekte oder Technologien der Firma.",
        "Nutze Keywords aus der Stellenanzeige in deinem Lebenslauf.",
        "Halte dein Anschreiben auf maximal eine Seite.",
        "Vermeide Wiederholungen zwischen Anschreiben und Lebenslauf.",
        "Zeige Motivation - warum genau diese Firma?",
        "Erwähne konkrete IT-Kenntnisse die zur Stelle passen.",
        "Nutze aktive Formulierungen statt Passiv.",
        "Prüfe deine E-Mail auf Rechtschreibung vor dem Senden.",
        "Sende Bewerbungen am Dienstag oder Mittwoch morgens.",
    ]

    TIPPS_LEBENSLAUF = [
        "Strukturiere deinen Lebenslauf chronologisch (neueste zuerst).",
        "Füge konkrete Projekte mit Technologien hinzu.",
        "Quantifiziere deine Erfolge (z.B. '99.9% Uptime erreicht').",
        "Passe Skills an jede Stelle individuell an.",
        "Maximal 2 Seiten für den Lebenslauf.",
        "Verwende ein professionelles Foto.",
        "Füge Links zu GitHub/Portfolio hinzu wenn vorhanden.",
        "Liste Zertifizierungen prominent auf.",
    ]

    TIPPS_VORBEREITUNG = [
        "Recherchiere die Firma vor dem Gespräch!",
        "Bereite Fragen an den Arbeitgeber vor.",
        "Übe deine Selbstpräsentation (2 Minuten).",
        "Kenne deine Stärken und Schwächen.",
        "Bereite konkrete Beispiele aus deiner Erfahrung vor.",
        "Kleide dich angemessen für das Gespräch.",
        "Sei 10 Minuten früher da.",
        "Bringe Unterlagen mit (Lebenslauf, Block, Stift).",
    ]

    ANTWORTEN = {
        "hallo":      "Hallo! Schön dich zu sehen! Wie kann ich helfen?",
        "hi":         "Hi! Was kann ich für dich tun?",
        "hilfe":      "Ich kann dir helfen bei:\n- Bewerbungstipps\n- Lebenslauf-Optimierung\n- Vorstellungsgespräch-Vorbereitung\n- Anschreiben-Feedback\n- Gehaltsverhandlung\n\nFrag mich einfach!",
        "tipps":      random.choice(TIPPS_BEWERBUNG) if 'TIPPS_BEWERBUNG' in dir() else "Hier ist ein Tipp: Passe dein Anschreiben immer individuell an!",
        "lebenslauf": "Für deinen Lebenslauf:\n1. Chronologische Reihenfolge\n2. Konkrete Projekte nennen\n3. IT-Skills hervorheben\n4. Maximal 2 Seiten\n5. Professionelles Layout",
        "anschreiben": "Anschreiben-Tipps:\n1. Individueller Bezug zur Stelle\n2. Keywords aus Anzeige nutzen\n3. Konkrete Motivation zeigen\n4. Maximal 1 Seite\n5. Fehlerfrei!",
        "gehalt":     "Gehaltsverhandlung-Tipps:\n- Recherchiere Marktwert (Glassdoor, Kununu)\n- Nenne eine Spanne, keine fixe Zahl\n- Begründe mit Qualifikation\n- Warte auf das Angebot des Arbeitgebers\n- Für Praktikum: 800-1200€ monatlich üblich",
        "gespräch":   "Vorstellungsgespräch:\n- Selbstpräsentation üben (2 Min)\n- Fragen an Arbeitgeber vorbereiten\n- STAR-Methode für Antworten\n- Körperhaltung beachten\n- Nachfassen nach dem Gespräch",
        "netzwerk":   "Netzwerktechnik-Interview:\n- OSI-Modell erklären können\n- TCP vs UDP Unterschiede\n- VLAN Konfiguration\n- Routing Protokolle\n- Firewall Grundlagen\n- DNS/DHCP Ablauf",
        "motivation": "Motivation zeigen:\n- Warum diese Firma?\n- Warum diese Position?\n- Was kannst du beitragen?\n- Wo siehst du dich in 5 Jahren?\n- Was reizt dich an der Technologie?",
        "stress":     "Umgang mit Stress:\n- Regelmäßige Pausen machen\n- Prioritäten setzen\n- Nicht zu viele Bewerbungen gleichzeitig\n- Erfolge feiern\n- Sport und Ausgleich",
        "danke":      "Gerne! Ich bin immer für dich da! Viel Erfolg bei deinen Bewerbungen!",
        "tschüss":    "Tschüss! Viel Erfolg! Denk dran: Jede Absage bringt dich näher zur Zusage!",
    }

    def __init__(self):
        self.verlauf = []
        self.letzte_tipps = []

    def begruessung(self):
        """Gibt Begrüßung zurück."""
        return random.choice(self.BEGRUESSUNG)

    def antwort(self, frage):
        """Gibt Antwort auf Frage."""
        frage_lower = frage.lower().strip()

        # Direkte Treffer
        for key, antwort in self.ANTWORTEN.items():
            if key in frage_lower:
                self.verlauf.append({
                    "frage":   frage,
                    "antwort": antwort,
                    "zeit":    datetime.now().strftime("%H:%M"),
                })
                return antwort

        # Keyword-Suche
        keywords = {
            "bewerbung":  self.TIPPS_BEWERBUNG,
            "lebenslauf": self.TIPPS_LEBENSLAUF,
            "cv":         self.TIPPS_LEBENSLAUF,
            "gespräch":   self.TIPPS_VORBEREITUNG,
            "interview":  self.TIPPS_VORBEREITUNG,
            "vorstellung": self.TIPPS_VORBEREITUNG,
            "gehalt":     ["Gehaltstipps: Marktwert recherchieren, Spanne nennen, begründen!"],
            "netzwerk":   ["Netzwerk-Tipps: OSI-Modell, TCP/IP, VLAN, Routing üben!"],
            "it":         ["IT-Tipps: Projekte hervorheben, Zertifizierungen zeigen!"],
            "praktikum":  ["Praktikum-Tipps: Lernbereitschaft zeigen, Fragen stellen!"],
            "fehler":     ["Fehler vermeiden: Rechtschreibung prüfen, Formatierung konsistent!"],
            "angst":      ["Lampenfieber: Vorbereitung ist key! Übe vor dem Spiegel."],
            "absage":     ["Absagen sind normal! Jede bringt dich weiter. Nicht aufgeben!"],
        }

        for key, tipps in keywords.items():
            if key in frage_lower:
                tipp = random.choice(tipps)
                if tipp in self.letzte_tipps and len(tipps) > 1:
                    tipp = random.choice([t for t in tipps if t != tipp])
                self.letzte_tipps.append(tipp)

                antwort = f"Hier ist ein Tipp für dich:\n\n{tipp}"
                self.verlauf.append({
                    "frage":   frage,
                    "antwort": antwort,
                    "zeit":    datetime.now().strftime("%H:%M"),
                })
                return antwort

        # Standard-Antwort
        antwort = (
            "Interessante Frage! Hier sind einige allgemeine Tipps:\n\n"
            "- Sei authentisch in deinen Bewerbungen\n"
            "- Zeige konkrete IT-Erfahrung\n"
            "- Bereite dich gut auf Gespräche vor\n"
            "- Frag nach wenn du unsicher bist!\n\n"
            "Probier mal: 'tipps bewerbung' oder 'hilfe lebenslauf'"
        )

        self.verlauf.append({
            "frage":   frage,
            "antwort": antwort,
            "zeit":    datetime.now().strftime("%H:%M"),
        })
        return antwort

    def zufalls_tipp(self):
        """Gibt einen zufälligen Tipp."""
        alle_tipps = (
            self.TIPPS_BEWERBUNG +
            self.TIPPS_LEBENSLAUF +
            self.TIPPS_VORBEREITUNG
        )
        return random.choice(alle_tipps)

    def bewertung_anschreiben(self, text):
        """Gibt Feedback zu einem Anschreiben-Text."""
        feedback = []
        score = 50

        if len(text) < 200:
            feedback.append("⚠️ Anschreiben ist sehr kurz. Mehr Details hinzufügen!")
        elif len(text) > 3000:
            feedback.append("⚠️ Anschreiben ist sehr lang. Kürzen auf max. 1 Seite!")
        else:
            feedback.append("✅ Gute Länge!")
            score += 10

        keywords = ["motivation", "erfahrung", "kenntnisse", "team", "unternehmen"]
        gefundene = [k for k in keywords if k in text.lower()]
        if len(gefundene) >= 3:
            feedback.append("✅ Gute Keywords verwendet!")
            score += 15
        else:
            feedback.append("⚠️ Mehr relevante Keywords einbauen!")

        if "sie" in text.lower():
            feedback.append("✅ Direkte Ansprache verwendet!")
            score += 5

        if "ich" in text.lower():
            feedback.append("✅ Persönliche Perspektive!")
            score += 5

        score = min(100, score)

        bewertung = f"📊 Aaliyahs Bewertung: {score}/100\n\n"
        for f in feedback:
            bewertung += f"{f}\n"

        return bewertung

    def verlauf_anzeigen(self):
        """Zeigt den Gesprächsverlauf."""
        return self.verlauf[-10:]

    def verlauf_leeren(self):
        """Leert den Verlauf."""
        self.verlauf = []


if __name__ == "__main__":
    aaliyah = Aaliyah()
    print(aaliyah.begruessung())
    print(aaliyah.antwort("tipps bewerbung"))
    print(aaliyah.antwort("lebenslauf"))
    print(aaliyah.zufalls_tipp())