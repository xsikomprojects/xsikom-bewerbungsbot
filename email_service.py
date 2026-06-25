"""
Email Service: Job-Alerts, Benachrichtigungen
F2: Job-Alerts per E-Mail
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import sqlite3

DB      = "bewerbungen.db"
MAIL_USER = os.environ.get("MAIL_USER", "")
MAIL_PASS = os.environ.get("MAIL_PASS", "")
MAIL_FROM = os.environ.get("MAIL_FROM", "XsiKOM <xsikom.projects@gmail.com>")


# ─────────────────────────────────────────────────────────────────
# HILFSFUNKTIONEN
# ─────────────────────────────────────────────────────────────────

def _db_connect():
    cn = sqlite3.connect(DB)
    cc = cn.cursor()
    return cn, cc


def _html_email(titel, inhalt, abmelde_link=""):
    """Erstellt schönes HTML-E-Mail Template."""
    return f"""
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{titel}</title>
</head>
<body style="margin:0;padding:0;background:#0A0E1A;font-family:'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:40px 20px">
<table width="600" cellpadding="0" cellspacing="0"
style="background:rgba(20,28,48,0.95);border-radius:20px;
border:1px solid rgba(0,217,255,0.3);overflow:hidden">

<!-- Header -->
<tr><td style="background:linear-gradient(135deg,#00D9FF,#8B5CF6);
padding:30px;text-align:center">
<h1 style="margin:0;color:white;font-size:28px;font-weight:700">
⚡ XsiKOM
</h1>
<p style="margin:5px 0 0;color:rgba(255,255,255,0.8);font-size:14px">
KI-Bewerbungsassistent
</p>
</td></tr>

<!-- Inhalt -->
<tr><td style="padding:40px 30px;color:#E2E8F0">
{inhalt}
</td></tr>

<!-- Footer -->
<tr><td style="padding:20px 30px;border-top:1px solid rgba(255,255,255,0.1);
text-align:center">
<p style="color:#6B7280;font-size:12px;margin:0">
© 2026 XsiKOM DIGITAL Projects · 
<a href="https://xsikom.de" style="color:#00D9FF">xsikom.de</a>
</p>
{f'<p style="margin-top:8px"><a href="{abmelde_link}" style="color:#6B7280;font-size:11px">Abmelden</a></p>' if abmelde_link else ''}
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""


def email_senden(an, betreff, html_inhalt):
    """
    Sendet eine E-Mail via Gmail SMTP.
    Gibt (True, "OK") oder (False, "Fehler") zurück.
    """
    if not MAIL_USER or not MAIL_PASS:
        return False, "E-Mail nicht konfiguriert"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = betreff
        msg["From"]    = MAIL_FROM
        msg["To"]      = an

        msg.attach(MIMEText(html_inhalt, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_USER, MAIL_PASS)
            server.sendmail(MAIL_USER, an, msg.as_string())

        return True, "E-Mail gesendet!"

    except smtplib.SMTPAuthenticationError:
        return False, "Gmail-Authentifizierung fehlgeschlagen"
    except smtplib.SMTPException as e:
        return False, f"SMTP-Fehler: {str(e)[:100]}"
    except Exception as e:
        return False, f"Fehler: {str(e)[:100]}"


# ─────────────────────────────────────────────────────────────────
# F2: JOB-ALERTS
# ─────────────────────────────────────────────────────────────────

def job_alert_erstellen(uid, email, suchbegriff, standort,
                        frequenz="taeglich"):
    """Erstellt einen neuen Job-Alert."""
    try:
        cn, cc = _db_connect()
        cc.execute(
            "CREATE TABLE IF NOT EXISTS job_alerts ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "user_id INTEGER,"
            "email TEXT,"
            "suchbegriff TEXT,"
            "standort TEXT,"
            "frequenz TEXT DEFAULT 'taeglich',"
            "aktiv INTEGER DEFAULT 1,"
            "erstellt TEXT,"
            "letzter_versand TEXT)"
        )
        cc.execute(
            "INSERT INTO job_alerts "
            "(user_id, email, suchbegriff, standort, "
            "frequenz, aktiv, erstellt) "
            "VALUES (?,?,?,?,?,1,?)",
            (uid, email, suchbegriff, standort,
             frequenz, datetime.now().isoformat())
        )
        cn.commit()
        alert_id = cc.lastrowid
        cn.close()

        # Bestätigungs-E-Mail senden
        _bestaetigung_senden(email, suchbegriff, standort,
                             frequenz, alert_id)
        return True, alert_id

    except Exception as e:
        return False, str(e)[:100]


def job_alert_loeschen(alert_id, uid):
    """Löscht einen Job-Alert."""
    try:
        cn, cc = _db_connect()
        cc.execute(
            "DELETE FROM job_alerts WHERE id=? AND user_id=?",
            (alert_id, uid)
        )
        cn.commit()
        cn.close()
        return True
    except Exception:
        return False


def job_alerts_laden(uid):
    """Lädt alle Job-Alerts eines Users."""
    try:
        cn, cc = _db_connect()
        cc.execute(
            "CREATE TABLE IF NOT EXISTS job_alerts ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "user_id INTEGER,"
            "email TEXT,"
            "suchbegriff TEXT,"
            "standort TEXT,"
            "frequenz TEXT DEFAULT 'taeglich',"
            "aktiv INTEGER DEFAULT 1,"
            "erstellt TEXT,"
            "letzter_versand TEXT)"
        )
        cc.execute(
            "SELECT id, email, suchbegriff, standort, "
            "frequenz, aktiv, letzter_versand "
            "FROM job_alerts WHERE user_id=? "
            "ORDER BY id DESC",
            (uid,)
        )
        rows = cc.fetchall()
        cn.close()
        return rows
    except Exception:
        return []


def job_alert_email_senden(uid, alert_id, jobs):
    """Sendet Job-Alert E-Mail mit gefundenen Jobs."""
    try:
        cn, cc = _db_connect()
        cc.execute(
            "SELECT email, suchbegriff, standort "
            "FROM job_alerts WHERE id=? AND user_id=?",
            (alert_id, uid)
        )
        alert = cc.fetchone()
        cn.close()

        if not alert:
            return False, "Alert nicht gefunden"

        email, suchbegriff, standort = alert

        # Jobs HTML
        jobs_html = ""
        for j in jobs[:10]:
            jobs_html += f"""
<div style="background:rgba(0,217,255,0.05);border:1px solid
rgba(0,217,255,0.2);border-radius:12px;padding:20px;margin:15px 0">
<h3 style="margin:0 0 8px;color:#00D9FF">{j.get('titel','')}</h3>
<p style="margin:0 0 5px;color:#A0AEC0">
🏢 {j.get('firma','')} · 📍 {j.get('standort','')}
</p>
<p style="margin:0 0 10px;color:#6B7280;font-size:13px">
{j.get('beschreibung','')[:150]}...
</p>
<a href="{j.get('url','https://xsikom.de/avinu')}"
style="background:linear-gradient(135deg,#00D9FF,#0099CC);
color:white;padding:8px 18px;border-radius:8px;
text-decoration:none;font-size:13px">
🔗 Job ansehen
</a>
</div>
"""

        inhalt = f"""
<h2 style="color:#00D9FF;margin-bottom:5px">
🔔 Neue Jobs für dich!
</h2>
<p style="color:#A0AEC0;margin-bottom:25px">
Suchbegriff: <strong style="color:white">{suchbegriff}</strong> · 
Standort: <strong style="color:white">{standort}</strong>
</p>
<p style="color:#A0AEC0">
Wir haben <strong style="color:#00D9FF">{len(jobs)}</strong> 
neue Jobs gefunden:
</p>
{jobs_html}
<div style="text-align:center;margin-top:30px">
<a href="https://xsikom.de/avinu"
style="background:linear-gradient(135deg,#10F4B1,#059669);
color:white;padding:14px 28px;border-radius:12px;
text-decoration:none;font-weight:600">
⚡ Alle Jobs ansehen
</a>
</div>
"""

        abmelde_link = (
            f"https://xsikom.de/alerts/abmelden/{alert_id}"
        )
        html = _html_email(
            f"🔔 {len(jobs)} neue Jobs: {suchbegriff}",
            inhalt,
            abmelde_link
        )

        ok, info = email_senden(
            email,
            f"🔔 XsiKOM: {len(jobs)} neue Jobs für '{suchbegriff}'",
            html
        )

        if ok:
            cn, cc = _db_connect()
            cc.execute(
                "UPDATE job_alerts SET letzter_versand=? "
                "WHERE id=?",
                (datetime.now().isoformat(), alert_id)
            )
            cn.commit()
            cn.close()

        return ok, info

    except Exception as e:
        return False, str(e)[:100]


def _bestaetigung_senden(email, suchbegriff, standort,
                          frequenz, alert_id):
    """Sendet Bestätigungs-E-Mail für neuen Job-Alert."""
    freq_text = {
        "taeglich":     "täglich",
        "woechentlich": "wöchentlich",
        "sofort":       "sofort",
    }.get(frequenz, frequenz)

    inhalt = f"""
<h2 style="color:#00D9FF">✅ Job-Alert aktiviert!</h2>
<p style="color:#A0AEC0">
Dein Job-Alert wurde erfolgreich eingerichtet.
</p>
<div style="background:rgba(0,217,255,0.05);
border:1px solid rgba(0,217,255,0.2);
border-radius:12px;padding:20px;margin:20px 0">
<p style="margin:5px 0;color:#E2E8F0">
💼 <strong>Suchbegriff:</strong> {suchbegriff}
</p>
<p style="margin:5px 0;color:#E2E8F0">
📍 <strong>Standort:</strong> {standort}
</p>
<p style="margin:5px 0;color:#E2E8F0">
⏰ <strong>Frequenz:</strong> {freq_text}
</p>
</div>
<div style="text-align:center;margin-top:25px">
<a href="https://xsikom.de/avinu"
style="background:linear-gradient(135deg,#00D9FF,#0099CC);
color:white;padding:14px 28px;border-radius:12px;
text-decoration:none;font-weight:600">
⚡ Jetzt Jobs suchen
</a>
</div>
"""

    abmelde_link = (
        f"https://xsikom.de/alerts/abmelden/{alert_id}"
    )
    html = _html_email(
        "✅ Job-Alert aktiviert - XsiKOM",
        inhalt,
        abmelde_link
    )

    email_senden(
        email,
        "✅ XsiKOM: Job-Alert aktiviert!",
        html
    )