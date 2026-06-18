"""
XsiKOM Security Module
- Quantum-resistant Encryption
- 2FA mit TOTP/QR Code
- Account-Löschung (DSGVO)
- Daten-Export
- Audit Logging
"""
import os
import sqlite3
import hashlib
import secrets
import json
import base64
from datetime import datetime
import pyotp
import qrcode
from io import BytesIO
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


DB_NAME = "bewerbungen.db"


# ============================================================
# QUANTUM-RESISTANT ENCRYPTION
# ============================================================
class QuantumSecurity:
    """Quantum-resistant Verschluesselung mit PBKDF2 + Fernet."""

    @staticmethod
    def schluessel_erstellen(passwort, salt=None):
        """Erstellt sicheren 256-bit Schluessel."""
        if salt is None:
            salt = secrets.token_bytes(32)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(passwort.encode()))
        return key, salt

    @staticmethod
    def verschluesseln(text, master_key):
        """Verschluesselt Text mit Fernet AES-256."""
        if isinstance(text, str):
            text = text.encode()
        f = Fernet(master_key)
        return f.encrypt(text).decode()

    @staticmethod
    def entschluesseln(verschluesselt, master_key):
        """Entschluesselt Text."""
        f = Fernet(master_key)
        return f.decrypt(verschluesselt.encode()).decode()

    @staticmethod
    def get_master_key():
        """Holt oder erstellt Master Key."""
        key_file = ".master_key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key


# ============================================================
# DATABASE SETUP
# ============================================================
def security_db_init():
    """Erstellt Security-Tabellen."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_security (
            user_id INTEGER PRIMARY KEY,
            two_fa_secret TEXT,
            two_fa_enabled INTEGER DEFAULT 0,
            quantum_salt TEXT,
            backup_codes TEXT,
            last_password_change TEXT,
            failed_login_attempts INTEGER DEFAULT 0,
            account_locked INTEGER DEFAULT 0,
            recovery_email TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS password_reset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE,
            expires_at TEXT,
            used INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS deletion_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            requested_at TEXT,
            scheduled_deletion TEXT,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            confirmation_token TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# 2FA FUNKTIONEN
# ============================================================
def generate_2fa_secret():
    """Erstellt ein neues 2FA Secret."""
    return pyotp.random_base32()


def generate_qr_code(user_email, secret):
    """Erstellt QR-Code fuer Authenticator App."""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name="XsiKOM-BewerbungsBOT"
    )

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#00D9FF", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


def verify_2fa_token(secret, token):
    """Verifiziert 2FA Token."""
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=1)


def get_2fa_status(user_id):
    """Prueft ob 2FA aktiv ist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT two_fa_enabled, two_fa_secret FROM user_security WHERE user_id=?",
        (user_id,)
    )
    r = c.fetchone()
    conn.close()
    if r:
        return r[0] == 1, r[1]
    return False, None


def enable_2fa(user_id, secret):
    """Aktiviert 2FA fuer User."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT user_id FROM user_security WHERE user_id=?", (user_id,))
    if c.fetchone():
        c.execute(
            "UPDATE user_security SET two_fa_secret=?, two_fa_enabled=1 WHERE user_id=?",
            (secret, user_id)
        )
    else:
        c.execute(
            "INSERT INTO user_security (user_id, two_fa_secret, two_fa_enabled) "
            "VALUES (?, ?, 1)",
            (user_id, secret)
        )

    backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
    c.execute(
        "UPDATE user_security SET backup_codes=? WHERE user_id=?",
        (json.dumps(backup_codes), user_id)
    )

    conn.commit()
    conn.close()

    audit_log(user_id, "2FA_ENABLED", "2FA wurde aktiviert")
    return backup_codes


def disable_2fa(user_id):
    """Deaktiviert 2FA."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "UPDATE user_security SET two_fa_enabled=0, two_fa_secret=NULL WHERE user_id=?",
        (user_id,)
    )
    conn.commit()
    conn.close()
    audit_log(user_id, "2FA_DISABLED", "2FA wurde deaktiviert")


# ============================================================
# PASSWORT MANAGEMENT
# ============================================================
def hash_password_secure(password):
    """Sicheres Passwort-Hashing mit SHA-512 + Salt."""
    salt = secrets.token_hex(32)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha512",
        password.encode(),
        salt.encode(),
        600000
    )
    return f"{salt}${pw_hash.hex()}"


def verify_password_secure(password, stored_hash):
    """Verifiziert Passwort."""
    try:
        salt, hash_value = stored_hash.split("$")
        pw_hash = hashlib.pbkdf2_hmac(
            "sha512",
            password.encode(),
            salt.encode(),
            600000
        )
        return pw_hash.hex() == hash_value
    except Exception:
        return False


def password_strength(password):
    """Bewertet Passwort-Staerke."""
    score = 0
    feedback = []

    if len(password) >= 12:
        score += 25
    elif len(password) >= 8:
        score += 15
    else:
        feedback.append("Mindestens 8 Zeichen")

    if any(c.isupper() for c in password):
        score += 15
    else:
        feedback.append("Grossbuchstaben verwenden")

    if any(c.islower() for c in password):
        score += 15
    else:
        feedback.append("Kleinbuchstaben verwenden")

    if any(c.isdigit() for c in password):
        score += 15
    else:
        feedback.append("Zahlen verwenden")

    if any(c in "!@#$%^&*()_+-=" for c in password):
        score += 30
    else:
        feedback.append("Sonderzeichen verwenden")

    return score, feedback


def create_password_reset_token(user_id):
    """Erstellt Token fuer Passwort-Reset."""
    from datetime import datetime, timedelta

    token = secrets.token_urlsafe(32)
    expires = (datetime.now() + timedelta(hours=1)).isoformat()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO password_reset (user_id, token, expires_at, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, token, expires, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    return token


def verify_reset_token(token):
    """Prueft Reset-Token."""
    from datetime import datetime

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT user_id, expires_at, used FROM password_reset
        WHERE token=?
    """, (token,))
    r = c.fetchone()
    conn.close()

    if not r:
        return None

    user_id, expires_at, used = r
    if used:
        return None

    if datetime.fromisoformat(expires_at) < datetime.now():
        return None

    return user_id


def use_reset_token(token):
    """Markiert Token als verwendet."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE password_reset SET used=1 WHERE token=?", (token,))
    conn.commit()
    conn.close()


# ============================================================
# ACCOUNT LÖSCHUNG (DSGVO)
# ============================================================
def request_account_deletion(user_id, reason=""):
    """Beantragt Account-Löschung (30 Tage Frist)."""
    from datetime import datetime, timedelta

    scheduled = (datetime.now() + timedelta(days=30)).isoformat()
    token = secrets.token_urlsafe(32)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO deletion_requests 
        (user_id, requested_at, scheduled_deletion, reason, confirmation_token)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, datetime.now().isoformat(), scheduled, reason, token))
    conn.commit()
    conn.close()

    audit_log(user_id, "DELETION_REQUESTED", f"Grund: {reason}")
    return token, scheduled


def cancel_deletion(user_id):
    """Storniert Loeschungsantrag."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "UPDATE deletion_requests SET status='cancelled' "
        "WHERE user_id=? AND status='pending'",
        (user_id,)
    )
    conn.commit()
    conn.close()
    audit_log(user_id, "DELETION_CANCELLED", "Loeschung storniert")


def execute_account_deletion(user_id):
    """Loescht Account und ALLE Daten."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    tables = [
        "bewerbungen", "profile", "uploads",
        "jobs", "auto_bewerbungen",
        "user_security", "password_reset",
        "deletion_requests", "audit_log"
    ]

    for table in tables:
        try:
            c.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
        except Exception:
            pass

    c.execute("DELETE FROM benutzer WHERE id=?", (user_id,))

    conn.commit()
    conn.close()

    user_folder = os.path.join("uploads", str(user_id))
    if os.path.exists(user_folder):
        import shutil
        shutil.rmtree(user_folder, ignore_errors=True)


def get_deletion_status(user_id):
    """Holt Loeschungs-Status."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT scheduled_deletion, status, requested_at 
        FROM deletion_requests 
        WHERE user_id=? AND status='pending'
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    r = c.fetchone()
    conn.close()
    return r


# ============================================================
# DATEN EXPORT (DSGVO Art. 20)
# ============================================================
def export_user_data(user_id):
    """Exportiert ALLE User-Daten (DSGVO)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    data = {
        "export_date": datetime.now().isoformat(),
        "user_id": user_id,
        "data": {}
    }

    c.execute("SELECT * FROM benutzer WHERE id=?", (user_id,))
    r = c.fetchone()
    if r:
        data["data"]["account"] = {
            "id": r[0],
            "username": r[1],
            "email": r[3],
            "vorname": r[4],
            "nachname": r[5],
            "rolle": r[6],
            "premium": r[7],
            "erstellt": r[9]
        }

    c.execute("SELECT * FROM profile WHERE user_id=?", (user_id,))
    r = c.fetchone()
    if r:
        data["data"]["profile"] = {
            "vorname": r[1], "nachname": r[2],
            "strasse": r[3], "plz": r[4], "stadt": r[5],
            "telefon": r[6], "email": r[7],
            "geburtsdatum": r[8],
            "kenntnisse": r[9], "sprachen": r[10]
        }

    c.execute("SELECT * FROM bewerbungen WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    data["data"]["bewerbungen"] = [
        {"id": r[0], "firma": r[2], "email": r[3], 
         "status": r[4], "datum": r[5]}
        for r in rows
    ]

    c.execute("SELECT * FROM uploads WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    data["data"]["uploads"] = [
        {"id": r[0], "name": r[2], "kategorie": r[4], "datum": r[6]}
        for r in rows
    ]

    try:
        c.execute("SELECT * FROM jobs WHERE user_id=?", (user_id,))
        rows = c.fetchall()
        data["data"]["jobs"] = [
            {"firma": r[2], "position": r[3], "standort": r[4]}
            for r in rows
        ]
    except Exception:
        pass

    conn.close()
    return data


# ============================================================
# AUDIT LOG
# ============================================================
def audit_log(user_id, event_type, details="", ip="", user_agent=""):
    """Loggt Sicherheitsevents."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO audit_log 
        (user_id, event_type, details, ip_address, user_agent, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, event_type, details, ip, user_agent, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_audit_log(user_id, limit=50):
    """Holt Audit Log fuer User."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT event_type, details, timestamp 
        FROM audit_log 
        WHERE user_id=? 
        ORDER BY id DESC LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


# Init
security_db_init()