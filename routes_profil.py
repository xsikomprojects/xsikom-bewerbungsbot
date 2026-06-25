"""
Profil Routes: Profil bearbeiten, Passwort, 2FA, Export, Loeschen
Alle Imports kommen aus shared.py – kein Import aus webapp.py!
"""
from flask import render_template_string, request, redirect, session, Response
from shared import H, DB, hp
from security import (
    generate_2fa_secret, generate_qr_code,
    verify_2fa_token, get_2fa_status,
    enable_2fa, disable_2fa,
    request_account_deletion, cancel_deletion,
    get_deletion_status, export_user_data,
    audit_log, get_audit_log,
)
import sqlite3
import json as json_module


# ─────────────────────────────────────────────────────────────────
# HILFSFUNKTIONEN
# ─────────────────────────────────────────────────────────────────

def _login_required():
    """Gibt Redirect zurück wenn nicht eingeloggt, sonst None."""
    if "user_id" not in session:
        return redirect("/login")
    return None


def _db_connect():
    """Öffnet DB-Verbindung und gibt (conn, cursor) zurück."""
    cn = sqlite3.connect(DB)
    cc = cn.cursor()
    return cn, cc


def _profil_nav():
    """Gibt die Profil-Navigations-Kacheln als HTML zurück."""
    return (
        '<div class="gr">'

        '<a href="/profil/edit" style="text-decoration:none">'
        '<div class="sc">'
        '<div class="si">👤</div>'
        '<div class="sv">Daten</div>'
        '<div class="sl">Bearbeiten</div>'
        '</div></a>'

        '<a href="/profil/password" style="text-decoration:none">'
        '<div class="sc">'
        '<div class="si">🔑</div>'
        '<div class="sv">Passwort</div>'
        '<div class="sl">Aendern</div>'
        '</div></a>'

        '<a href="/profil/2fa" style="text-decoration:none">'
        '<div class="sc">'
        '<div class="si">🔐</div>'
        '<div class="sv">2FA</div>'
        '<div class="sl">Einrichten</div>'
        '</div></a>'

        '<a href="/profil/export" style="text-decoration:none">'
        '<div class="sc">'
        '<div class="si">📥</div>'
        '<div class="sv">Export</div>'
        '<div class="sl">DSGVO Daten</div>'
        '</div></a>'

        '<a href="/profil/audit" style="text-decoration:none">'
        '<div class="sc">'
        '<div class="si">📊</div>'
        '<div class="sv">Audit</div>'
        '<div class="sl">Sicherheits-Log</div>'
        '</div></a>'

        '<a href="/profil/delete" style="text-decoration:none">'
        '<div class="sc" style="border-color:var(--rd)">'
        '<div class="si">🗑️</div>'
        '<div class="sv" style="color:var(--rd)">Loeschen</div>'
        '<div class="sl">Account</div>'
        '</div></a>'

        '</div>'
    )


def _sicherheits_info():
    """Gibt die Sicherheits-Infobox als HTML zurück."""
    return (
        '<div class="cd" style="margin-top:30px">'
        '<h3>🔒 Sicherheit</h3>'
        '<ul style="line-height:2">'
        '<li>✅ AES-256 Verschluesselung</li>'
        '<li>✅ PBKDF2 600.000 Iterationen</li>'
        '<li>✅ SHA-512 Passwort-Hashing</li>'
        '<li>✅ HTTPS Ende-zu-Ende</li>'
        '<li>✅ DSGVO-konform</li>'
        '</ul></div>'
    )


# ─────────────────────────────────────────────────────────────────
# ROUTE-REGISTRIERUNG
# ─────────────────────────────────────────────────────────────────

def register_profil_routes(app):

    # ════════════════════════════════════════════════════════════
    # PROFIL ÜBERSICHT
    # ════════════════════════════════════════════════════════════

    @app.route("/profil")
    def profil():
        r = _login_required()
        if r: return r

        uid      = session["user_id"]
        tf, _    = get_2fa_status(uid)
        ds       = get_deletion_status(uid)

        # ── Löschungs-Warnung ────────────────────────────────────
        dw = ""
        if ds:
            dw = (
                '<div class="al aw">⚠️ Konto wird geloescht am: '
                + str(ds[0])[:10]
                + ' <a href="/profil/cancel-deletion">↩️ Stornieren</a></div>'
            )

        # ── 2FA-Kachel dynamisch ─────────────────────────────────
        nav = _profil_nav().replace(
            '<div class="si">🔐</div>'
            '<div class="sv">2FA</div>'
            '<div class="sl">Einrichten</div>',
            f'<div class="si">{"✅" if tf else "🔐"}</div>'
            f'<div class="sv">2FA</div>'
            f'<div class="sl">{"Aktiv" if tf else "Einrichten"}</div>',
        )

        c = (
            '<h1>⚙️ Profil & Sicherheit</h1>'
            + dw
            + nav
            + _sicherheits_info()
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # PROFIL BEARBEITEN
    # ════════════════════════════════════════════════════════════

    @app.route("/profil/edit", methods=["GET", "POST"])
    def profil_edit():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        if request.method == "POST":
            vn = request.form.get("vorname", "").strip()
            nn = request.form.get("nachname", "").strip()
            em = request.form.get("email", "").strip()

            cn, cc = _db_connect()
            cc.execute(
                "UPDATE benutzer SET vorname=?, nachname=?, email=? "
                "WHERE id=?",
                (vn, nn, em, uid)
            )
            cn.commit()
            cn.close()

            session["vorname"]   = vn
            session["nachname"]  = nn
            audit_log(uid, "PROFILE_UPDATED", "Profil aktualisiert")
            msg = '<div class="al ao">✅ Gespeichert!</div>'

        cn, cc = _db_connect()
        cc.execute(
            "SELECT vorname, nachname, email FROM benutzer WHERE id=?",
            (uid,)
        )
        u = cc.fetchone()
        cn.close()

        c = (
            '<h1>👤 Profil bearbeiten</h1>'
            + msg +
            '<div class="cd"><form method="POST">'
            '<p>Vorname:</p>'
            f'<input type="text" name="vorname" value="{u[0] or ""}" required>'
            '<p>Nachname:</p>'
            f'<input type="text" name="nachname" value="{u[1] or ""}" required>'
            '<p>E-Mail:</p>'
            f'<input type="email" name="email" value="{u[2] or ""}" required>'
            '<button type="submit" class="bt b2" style="width:100%">'
            '💾 Speichern</button>'
            '</form></div>'
            '<a href="/profil" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # PASSWORT ÄNDERN
    # ════════════════════════════════════════════════════════════

    @app.route("/profil/password", methods=["GET", "POST"])
    def profil_password():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        if request.method == "POST":
            old  = request.form.get("old_password", "")
            new  = request.form.get("new_password", "")
            conf = request.form.get("confirm_password", "")

            cn, cc = _db_connect()
            cc.execute(
                "SELECT passwort FROM benutzer WHERE id=?", (uid,)
            )
            current = cc.fetchone()[0]

            if hp(old) != current:
                msg = '<div class="al ae">❌ Altes Passwort falsch!</div>'
            elif new != conf:
                msg = '<div class="al ae">❌ Passwoerter unterschiedlich!</div>'
            elif len(new) < 8:
                msg = '<div class="al ae">❌ Min. 8 Zeichen!</div>'
            else:
                cc.execute(
                    "UPDATE benutzer SET passwort=? WHERE id=?",
                    (hp(new), uid)
                )
                cn.commit()
                audit_log(uid, "PASSWORD_CHANGED", "Passwort geaendert")
                msg = '<div class="al ao">✅ Passwort geaendert!</div>'

            cn.close()

        c = (
            '<h1>🔑 Passwort aendern</h1>'
            + msg +
            '<div class="cd"><form method="POST">'
            '<p>Altes Passwort:</p>'
            '<input type="password" name="old_password" '
            'placeholder="Altes Passwort" required>'
            '<p>Neues Passwort (min. 8 Zeichen):</p>'
            '<input type="password" name="new_password" '
            'placeholder="Neues Passwort" required>'
            '<p>Bestaetigen:</p>'
            '<input type="password" name="confirm_password" '
            'placeholder="Nochmal eingeben" required>'
            '<button type="submit" class="bt b2" style="width:100%">'
            '🔒 Aendern</button>'
            '</form></div>'
            '<a href="/profil" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # 2FA
    # ════════════════════════════════════════════════════════════

    @app.route("/profil/2fa", methods=["GET", "POST"])
    def profil_2fa():
        r = _login_required()
        if r: return r

        uid     = session["user_id"]
        tf, cu  = get_2fa_status(uid)
        msg     = ""

        if request.method == "POST":
            action = request.form.get("action", "")
            token  = request.form.get("token", "")

            if action == "enable":
                secret = request.form.get("secret", "")
                if verify_2fa_token(secret, token):
                    codes      = enable_2fa(uid, secret)
                    codes_html = (
                        "<br>".join(codes)
                        if isinstance(codes, list) else ""
                    )
                    tf  = True
                    msg = (
                        '<div class="al ao">✅ 2FA aktiviert!'
                        '<h3>🔐 Backup Codes:</h3>'
                        '<div style="background:#0A0E1A;padding:15px;'
                        'border-radius:8px;font-family:monospace;margin-top:10px">'
                        + codes_html +
                        '</div></div>'
                    )
                else:
                    msg = '<div class="al ae">❌ Falscher Code!</div>'

            elif action == "disable":
                if verify_2fa_token(cu, token):
                    disable_2fa(uid)
                    tf  = False
                    msg = '<div class="al ao">✅ 2FA deaktiviert</div>'
                else:
                    msg = '<div class="al ae">❌ Falscher Code!</div>'

        # ── 2FA aktiv: Deaktivieren-Formular ────────────────────
        if tf:
            c = (
                '<h1>🔐 2FA Aktiv</h1>'
                + msg +
                '<div class="cd">'
                '<div class="al ao">✅ 2FA ist aktiv! '
                'Dein Account ist extra sicher.</div>'
                '<h3>2FA deaktivieren</h3>'
                '<form method="POST">'
                '<input type="hidden" name="action" value="disable">'
                '<p>6-stelliger Code aus deiner Authenticator App:</p>'
                '<input type="text" name="token" placeholder="123456" '
                'maxlength="6" required '
                'style="text-align:center;font-size:24px;letter-spacing:10px">'
                '<button type="submit" class="bt b4" style="width:100%">'
                '⚠️ Deaktivieren</button>'
                '</form></div>'
                '<a href="/profil" class="bt b1">← Zurueck</a>'
            )

        # ── 2FA inaktiv: Einrichten-Formular ────────────────────
        else:
            secret = generate_2fa_secret()
            qr     = generate_qr_code(session.get("username", "user"), secret)
            c = (
                '<h1>🔐 2FA einrichten</h1>'
                + msg +
                '<div class="cd">'
                '<h3>📱 Schritt 1: Authenticator App</h3>'
                '<p>Google Authenticator, Microsoft Authenticator '
                'oder Authy installieren.</p>'
                '</div>'

                '<div class="cd">'
                '<h3>📷 Schritt 2: QR-Code scannen</h3>'
                '<div style="text-align:center;background:white;'
                'padding:20px;border-radius:12px">'
                f'<img src="{qr}" style="max-width:300px"></div>'
                '<p style="margin-top:15px;font-family:monospace;'
                f'word-break:break-all">Manuell: {secret}</p>'
                '</div>'

                '<div class="cd">'
                '<h3>✅ Schritt 3: Code eingeben</h3>'
                '<form method="POST">'
                '<input type="hidden" name="action" value="enable">'
                f'<input type="hidden" name="secret" value="{secret}">'
                '<input type="text" name="token" placeholder="123456" '
                'maxlength="6" required '
                'style="text-align:center;font-size:24px;letter-spacing:10px">'
                '<button type="submit" class="bt b2" style="width:100%">'
                '🔐 2FA aktivieren</button>'
                '</form></div>'
                '<a href="/profil" class="bt b1">← Zurueck</a>'
            )

        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # DSGVO EXPORT
    # ════════════════════════════════════════════════════════════

    @app.route("/profil/export")
    def profil_export():
        r = _login_required()
        if r: return r

        uid  = session["user_id"]
        data = export_user_data(uid)
        audit_log(uid, "DATA_EXPORTED", "DSGVO Export")

        return Response(
            json_module.dumps(data, ensure_ascii=False, indent=2),
            mimetype="application/json",
            headers={
                "Content-Disposition":
                    "attachment; filename=xsikom_export.json"
            },
        )

    # ════════════════════════════════════════════════════════════
    # AUDIT LOG
    # ════════════════════════════════════════════════════════════

    @app.route("/profil/audit")
    def profil_audit():
        r = _login_required()
        if r: return r

        uid  = session["user_id"]
        logs = get_audit_log(uid)

        ICONS = {
            "LOGIN":              "🔓",
            "LOGOUT":             "🔒",
            "2FA_ENABLED":        "✅",
            "2FA_DISABLED":       "⚠️",
            "PASSWORD_CHANGED":   "🔑",
            "PROFILE_UPDATED":    "👤",
            "DATA_EXPORTED":      "📥",
            "DELETION_REQUESTED": "🗑️",
        }

        if logs:
            lh = "".join(
                '<tr style="border-bottom:1px solid var(--bd)">'
                f'<td style="padding:12px">{ICONS.get(log[0], "📋")}</td>'
                f'<td style="padding:12px"><strong>{log[0]}</strong></td>'
                f'<td style="padding:12px">{log[1]}</td>'
                f'<td style="padding:12px;font-size:11px;color:var(--t3)">'
                f'{str(log[2])[:16]}</td></tr>'
                for log in logs
            )
        else:
            lh = (
                '<tr><td colspan="4" style="text-align:center;'
                'padding:20px;color:var(--t3)">Keine Eintraege</td></tr>'
            )

        c = (
            '<h1>📊 Sicherheits-Audit Log</h1>'
            '<p>Alle sicherheitsrelevanten Aktivitaeten</p>'
            '<div class="cd">'
            '<table style="width:100%;border-collapse:collapse">'
            '<thead>'
            '<tr style="background:rgba(0,217,255,0.1)">'
            '<th style="padding:12px;text-align:left">📋</th>'
            '<th style="padding:12px;text-align:left">Event</th>'
            '<th style="padding:12px;text-align:left">Details</th>'
            '<th style="padding:12px;text-align:left">Zeit</th>'
            '</tr></thead>'
            '<tbody>' + lh + '</tbody>'
            '</table></div>'
            '<a href="/profil" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # ACCOUNT LÖSCHEN
    # ════════════════════════════════════════════════════════════

    @app.route("/profil/delete", methods=["GET", "POST"])
    def profil_delete():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        if request.method == "POST":
            pw     = request.form.get("password", "")
            reason = request.form.get("reason", "")
            conf   = request.form.get("confirmation", "")

            cn, cc = _db_connect()
            cc.execute(
                "SELECT passwort FROM benutzer WHERE id=?", (uid,)
            )
            current = cc.fetchone()[0]
            cn.close()

            if hp(pw) != current:
                msg = '<div class="al ae">❌ Passwort falsch!</div>'
            elif conf != "LOESCHEN":
                msg = (
                    '<div class="al ae">❌ '
                    'Bitte "LOESCHEN" eingeben!</div>'
                )
            else:
                token, sched = request_account_deletion(uid, reason)
                msg = (
                    '<div class="al ao">✅ Loeschungsantrag eingegangen!'
                    f'<p>Geplante Loeschung: {str(sched)[:10]}</p>'
                    '<p>Du hast 30 Tage zum Stornieren.</p>'
                    '<a href="/profil/cancel-deletion" class="bt b2">'
                    '↩️ Stornieren</a>'
                    '</div>'
                )

        c = (
            '<h1 style="color:var(--rd)">🗑️ Account loeschen</h1>'
            '<div class="al aw">'
            '⚠️ <strong>WARNUNG:</strong> Diese Aktion ist endgueltig!'
            '<ul style="margin-top:10px">'
            '<li>Alle Bewerbungen werden geloescht</li>'
            '<li>Alle Dateien werden geloescht</li>'
            '<li>30 Tage Frist zum Stornieren</li>'
            '</ul></div>'
            + msg +
            '<div class="cd">'
            '<h3>🔐 Account-Loeschung (DSGVO Art. 17)</h3>'
            '<form method="POST">'
            '<p>Grund (optional):</p>'
            '<textarea name="reason" rows="3" '
            'placeholder="Warum loeschen?"></textarea>'
            '<p>Dein Passwort:</p>'
            '<input type="password" name="password" '
            'placeholder="Passwort" required>'
            '<p>Tippe <strong style="color:var(--rd)">LOESCHEN</strong> '
            'zur Bestaetigung:</p>'
            '<input type="text" name="confirmation" '
            'placeholder="LOESCHEN" required>'
            '<button type="submit" class="bt b4" style="width:100%">'
            '🗑️ Account loeschen</button>'
            '</form></div>'
            '<a href="/profil" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # LÖSCHUNG STORNIEREN
    # ════════════════════════════════════════════════════════════

    @app.route("/profil/cancel-deletion")
    def profil_cancel_deletion():
        r = _login_required()
        if r: return r

        cancel_deletion(session["user_id"])

        c = (
            '<h1>↩️ Loeschung storniert</h1>'
            '<div class="al ao">✅ Dein Account bleibt aktiv!</div>'
            '<a href="/profil" class="bt b1">Zum Profil</a>'
        )
        return render_template_string(H, content=c, user=session)