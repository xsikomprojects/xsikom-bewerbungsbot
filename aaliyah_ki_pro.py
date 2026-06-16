"""
Aaliyah KI - Pro Version mit Groq (Llama 3)
Komi Tevi - 2026
"""
import os
import requests
import json
from datetime import datetime


class AaliyahPro:
    """Echte KI-Assistentin mit Groq API."""

    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"
        self.verlauf = []
        self.system_prompt = self._system_prompt()

    def _system_prompt(self):
        return """Du bist Aaliyah, eine professionelle KI-Assistentin
fuer Bewerbungen und Karriereberatung.

Deine Aufgaben:
- Hilf bei Bewerbungen, Lebenslaeufen und Anschreiben
- Gib konkrete IT-Karriere-Tipps
- Berate zu Vorstellungsgespraechen
- Hilf bei Gehaltsverhandlungen
- Analysiere Texte und gib Verbesserungsvorschlaege
- Sei freundlich, motivierend und professionell

Spezialisierung: IT-Bereich
- Netzwerktechnik
- Systemadministration
- IT-Support
- Fachinformatiker
- Praktika fuer IT-Fachtechniker

Sprich deutsch, sei kurz und praezise.
Verwende Emojis sparsam.
Antworte in 2-4 Saetzen, ausser bei komplexen Fragen."""

    def antwort(self, frage, kontext=""):
        """Sendet Frage an Groq KI."""
        if not self.api_key:
            return self._fallback_antwort(frage)

        # Verlauf aufbauen
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # Letzte 5 Nachrichten als Kontext
        for v in self.verlauf[-5:]:
            messages.append({"role": "user", "content": v["frage"]})
            messages.append({"role": "assistant", "content": v["antwort"]})

        # Neue Frage
        full_frage = frage
        if kontext:
            full_frage = f"Kontext: {kontext}\n\nFrage: {frage}"

        messages.append({"role": "user", "content": full_frage})

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                antwort = data["choices"][0]["message"]["content"]

                # Verlauf speichern
                self.verlauf.append({
                    "frage": frage,
                    "antwort": antwort,
                    "zeit": datetime.now().isoformat()
                })

                return antwort
            else:
                print(f"Groq Error: {response.status_code}")
                print(response.text)
                return self._fallback_antwort(frage)

        except Exception as e:
            print(f"KI Fehler: {e}")
            return self._fallback_antwort(frage)

    def lebenslauf_analyse(self, lebenslauf_text):
        """Analysiert einen Lebenslauf."""
        frage = f"""Bitte analysiere diesen Lebenslauf
und gib konkrete Verbesserungsvorschlaege:

{lebenslauf_text}

Bewerte:
1. Vollstaendigkeit
2. Layout-Tipps
3. Was fehlt?
4. Was kann verbessert werden?
5. Bewertung von 1-10"""

        return self.antwort(frage)

    def anschreiben_generieren(self, firma, position, kenntnisse):
        """Generiert ein individuelles Anschreiben."""
        frage = f"""Erstelle ein professionelles Bewerbungsanschreiben:

Firma: {firma}
Position: {position}
Meine Kenntnisse: {kenntnisse}

Anforderungen:
- Maximal 1 Seite
- Professionell aber persoenlich
- Auf die Stelle zugeschnitten
- Mit konkretem Bezug zur Firma
- Deutsche Sprache
- Briefform: "Sehr geehrte Damen und Herren"
- Schluss: "Mit freundlichen Gruessen"

Erstelle den kompletten Anschreiben-Text."""

        return self.antwort(frage)

    def gehalt_beratung(self, position, erfahrung, ort):
        """Berät zu Gehaltsverhandlungen."""
        frage = f"""Berate mich zur Gehaltsverhandlung:

Position: {position}
Erfahrung: {erfahrung}
Ort: {ort}

Gib mir:
1. Marktueblichen Gehaltsrahmen
2. Verhandlungstipps
3. Was darf ich fordern?
4. Was sind rote Linien?"""

        return self.antwort(frage)

    def gespraech_vorbereitung(self, firma, position):
        """Bereitet auf Vorstellungsgespräch vor."""
        frage = f"""Bereite mich auf das Vorstellungsgespraech vor:

Firma: {firma}
Position: {position}

Gib mir:
1. 5 wahrscheinliche Fragen
2. Tipps zur Selbstpraesentation
3. Welche Fragen soll ich stellen?
4. Was sollte ich vorher recherchieren?
5. Kleidungstipps"""

        return self.antwort(frage)

    def _fallback_antwort(self, frage):
        """Fallback wenn API nicht funktioniert."""
        frage_lower = frage.lower()

        if "hallo" in frage_lower or "hi" in frage_lower:
            return "Hallo! Ich bin Aaliyah. Leider ist meine KI gerade offline. Verwende einfache Fragen wie 'tipps', 'gehalt', 'lebenslauf'."

        if "tipps" in frage_lower:
            return ("Bewerbungstipps:\n"
                    "1. Anschreiben individuell anpassen\n"
                    "2. Konkrete Projekte erwaehnen\n"
                    "3. Keywords nutzen\n"
                    "4. Max 1 Seite Anschreiben\n"
                    "5. Auf Rechtschreibung achten")

        if "lebenslauf" in frage_lower:
            return ("Lebenslauf-Tipps:\n"
                    "1. Chronologisch (neueste zuerst)\n"
                    "2. Max 2 Seiten\n"
                    "3. IT-Skills hervorheben\n"
                    "4. Konkrete Projekte nennen\n"
                    "5. Professionelles Layout")

        if "gehalt" in frage_lower:
            return ("Gehalt-Tipps:\n"
                    "- IT-Praktikum: 800-1200 EUR/Monat\n"
                    "- Junior IT-Techniker: 30-40k EUR/Jahr\n"
                    "- Marktwert recherchieren (Glassdoor)\n"
                    "- Spanne nennen, nicht fixe Zahl")

        if "netzwerk" in frage_lower:
            return ("Netzwerk-Interview Themen:\n"
                    "- OSI-Modell (7 Schichten)\n"
                    "- TCP vs UDP\n"
                    "- VLAN Konfiguration\n"
                    "- Routing Protokolle (OSPF, BGP)\n"
                    "- Firewall Grundlagen\n"
                    "- DNS/DHCP Funktionsweise")

        return ("Frag mich konkret zu:\n"
                "- Bewerbung\n"
                "- Lebenslauf\n"
                "- Anschreiben\n"
                "- Gehalt\n"
                "- Vorstellungsgespraech\n"
                "- IT-Themen (Netzwerk, etc.)")

    def verlauf_leeren(self):
        """Loescht den Gesprächsverlauf."""
        self.verlauf = []


# Test
if __name__ == "__main__":
    aaliyah = AaliyahPro()
    print("Aaliyah Pro gestartet!")
    print("-" * 50)

    # Test 1: Einfache Frage
    print("Frage: Was sind Tipps fuer eine IT-Bewerbung?")
    print(f"Antwort: {aaliyah.antwort('Was sind Tipps fuer eine IT-Bewerbung?')}")
    print()