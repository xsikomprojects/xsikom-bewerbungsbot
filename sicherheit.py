"""
Sicherheitsmodul fuer XsiKOM-BewerbungsBOT
- Passwort-Hashing mit bcrypt
- SQL-Injection Schutz
- Rate Limiting
- Session Management
- Verschluesselung sensibler Daten
"""
import hashlib
import secrets
import os
import json
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import base64


# ============================================================
# VERSCHLÜSSELUNG
# ============================================================
def schluessel_erstellen():
    """Erstellt einen sicheren Verschluesselungsschluessel."""
    pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ".schluessel"
    )
    if not os.path.exists(pfad):
        key = Fernet.generate_key()
        with open(pfad, "wb") as f:
            f.write(key)
        os.chmod(pfad, 0o600)  # Nur Owner kann lesen
    with open(pfad, "rb") as f:
        return f.read()


def daten_verschluesseln(text):
    """Verschluesselt Text mit Fernet."""
    f = Fernet(schluessel_erstellen())
    return f.encrypt(text.encode()).decode()


def daten_entschluesseln(verschluesselt):
    """Entschluesselt Text mit Fernet."""
    f = Fernet(schluessel_erstellen())
    return f.decrypt(verschluesselt.encode()).decode()


# ============================================================
# PASSWORT SICHERHEIT
# ============================================================
def passwort_hash_sicher(passwort):
    """Sicheres Passwort-Hashing mit Salt (PBKDF2)."""
    salt = secrets.token_bytes(32)
    hash_pw = hashlib.pbkdf2_hmac(
        "sha256",
        passwort.encode(),
        salt,
        100000  # 100.000 Iterationen
    )
    return base64.b64encode(salt + hash_pw).decode()


def passwort_pruefen_sicher(passwort, hash_gespeichert):
    """Prueft Passwort gegen Hash."""
    try:
        decoded = base64.b64decode(hash_gespeichert)
        salt = decoded[:32]
        hash_pw = decoded[32:]
        neuer_hash = hashlib.pbkdf2_hmac(
            "sha256",
            passwort.encode(),
            salt,
            100000
        )
        return secrets.compare_digest(hash_pw, neuer_hash)
    except Exception:
        return False


# ============================================================
# PASSWORT STÄRKE
# ============================================================
def passwort_staerke(passwort):
    """Bewertet die Staerke eines Passworts."""
    score = 0
    feedback = []

    if len(passwort) < 8:
        feedback.append("Mindestens 8 Zeichen!")
    elif len(passwort) >= 12:
        score += 2
    else:
        score += 1

    if any(c.isupper() for c in passwort):
        score += 1
    else:
        feedback.append("Mindestens 1 Grossbuchstabe!")

    if any(c.islower() for c in passwort):
        score += 1
    else:
        feedback.append("Mindestens 1 Kleinbuchstabe!")

    if any(c.isdigit() for c in passwort):
        score += 1
    else:
        feedback.append("Mindestens 1 Ziffer!")

    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in passwort):
        score += 1
    else:
        feedback.append("Mindestens 1 Sonderzeichen!")

    if score >= 5:
        staerke = "Sehr Stark"
        farbe = "#2DD4A8"
    elif score >= 4:
        staerke = "Stark"
        farbe = "#FFD93D"
    elif score >= 3:
        staerke = "Mittel"
        farbe = "#FF8C42"
    else:
        staerke = "Schwach"
        farbe = "#FF5252"

    return {
        "score":    score,
        "staerke":  staerke,
        "farbe":    farbe,
        "feedback": feedback
    }


# ============================================================
# SESSION MANAGEMENT
# ============================================================
class SessionManager:

    def __init__(self):
        self.sessions  = {}
        self.timeout   = 3600  # 1 Stunde

    def session_erstellen(self, user_id):
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            "user_id":  user_id,
            "erstellt": time.time(),
            "ip":       None,
        }
        return token

    def session_pruefen(self, token):
        if token not in self.sessions:
            return None
        s = self.sessions[token]
        if time.time() - s["erstellt"] > self.timeout:
            del self.sessions[token]
            return None
        s["erstellt"] = time.time()  # Refresh
        return s

    def session_loeschen(self, token):
        if token in self.sessions:
            del self.sessions[token]


# ============================================================
# RATE LIMITING (Brute-Force Schutz)
# ============================================================
class RateLimiter:

    def __init__(self):
        self.versuche       = {}
        self.max_versuche   = 5
        self.sperrzeit      = 900  # 15 Minuten

    def versuch_pruefen(self, ip_oder_user):
        jetzt = time.time()
        if ip_oder_user not in self.versuche:
            self.versuche[ip_oder_user] = []

        # Alte Versuche entfernen
        self.versuche[ip_oder_user] = [
            t for t in self.versuche[ip_oder_user]
            if jetzt - t < self.sperrzeit
        ]

        if len(self.versuche[ip_oder_user]) >= self.max_versuche:
            return False, "Zu viele Versuche! Warte 15 Min."

        self.versuche[ip_oder_user].append(jetzt)
        return True, "OK"

    def reset(self, ip_oder_user):
        if ip_oder_user in self.versuche:
            del self.versuche[ip_oder_user]


# ============================================================
# SQL INJECTION SCHUTZ
# ============================================================
def sql_sicher(text):
    """Bereinigt Text fuer SQL (immer Prepared Statements verwenden!)."""
    if not isinstance(text, str):
        return text
    gefaehrlich = [
        "DROP", "DELETE", "TRUNCATE", "EXEC",
        "UNION", "SELECT *", "--", "/*", "*/"
    ]
    text_upper = text.upper()
    for g in gefaehrlich:
        if g in text_upper:
            return text.replace(g, "")
    return text


# ============================================================
# AUDIT LOG
# ============================================================
def audit_log(aktion, user="anonym", details=""):
    """Loggt sicherheitsrelevante Aktionen."""
    log_pfad = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "audit.log"
    )
    eintrag = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"{user:<20} | {aktion:<25} | {details}\n"
    )
    with open(log_pfad, "a", encoding="utf-8") as f:
        f.write(eintrag)


# ============================================================
# DATENSCHUTZ
# ============================================================
def email_anonymisieren(email):
    """Anonymisiert E-Mail fuer Logs (a***@example.com)."""
    if "@" not in email:
        return "***"
    name, domain = email.split("@", 1)
    if len(name) <= 1:
        return f"*@{domain}"
    return f"{name[0]}***@{domain}"


def ip_anonymisieren(ip):
    """Anonymisiert IP-Adresse (DSGVO)."""
    if not ip:
        return "***"
    teile = ip.split(".")
    if len(teile) == 4:
        return f"{teile[0]}.{teile[1]}.{teile[2]}.0"
    return "***"


if __name__ == "__main__":
    # Test
    print("Sicherheitsmodul Tests")
    print("-" * 50)

    # Passwort hashen
    pw = "TestPassword123!"
    hash_pw = passwort_hash_sicher(pw)
    print(f"Hash: {hash_pw[:50]}...")
    print(f"Pruefung OK: {passwort_pruefen_sicher(pw, hash_pw)}")

    # Verschluesselung
    text = "Geheime Daten"
    enc = daten_verschluesseln(text)
    dec = daten_entschluesseln(enc)
    print(f"\nVerschluesselt: {enc[:50]}...")
    print(f"Entschluesselt: {dec}")

    # Staerke
    staerke = passwort_staerke(pw)
    print(f"\nPasswort-Staerke: {staerke['staerke']}")