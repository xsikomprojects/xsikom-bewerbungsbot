"""Profil Routes: Profil bearbeiten, Passwort, 2FA, Export, Loeschen"""
from flask import render_template_string, request, redirect, session, Response
from webapp import H, DB, hp
from security import (
    generate_2fa_secret, generate_qr_code,
    verify_2fa_token, get_2fa_status, enable_2fa, disable_2fa,
    request_account_deletion, cancel_deletion,
    get_deletion_status, export_user_data, audit_log
)
import sqlite3
import json as json_module


def register_profil_routes(app):

    @app.route("/profil")
    def profil():
        if "user_id" not in session:
            return redirect("/login")
        tf, _ = get_2fa_status(session["user_id"])
        ds = get_deletion_status(session["user_id"])

        dw = ""
        if ds:
            dw = (
                '<div class="al aw">⚠️ Konto wird geloescht am: '
                + str(ds[0])[:10] +
                ' <a href="/profil/cancel-deletion">↩️ Stornieren</a></div>'
            )

        c = (
            '<h1>⚙️ Profil & Sicherheit</h1>'
            + dw +
            '<div class="gr">'
            '<a href="/profil/edit" style="text-decoration:none">'
            '<div class="sc"><div class="si">👤</div><div class="sv">Daten</div><div class="sl">Bearbeiten</div></div></a>'
            '<a href="/profil/password" style="text-decoration:none">'
            '<div class="sc"><div class="si">🔑</div><div class="sv">Passwort</div><div class="sl">Aendern</div></div></a>'
            '<a href="/profil/2fa" style="text-decoration:none">'
            '<div class="sc"><div class="si">' + ("✅" if tf else "🔐") + '</div>'
            '<div class="sv">2FA</div><div class="sl">' + ("Aktiv" if tf else "Einrichten") + '</div></div></a>'
            '<a href="/profil/export" style="text-decoration:none">'
            '<div class="sc"><div class="si">📥</div><div class="sv">Export</div><div class="sl">DSGVO Daten</div></div></a>'
            '<a href="/profil/audit" style="text-decoration:none">'
            '<div class="sc"><div class="si">📊</div><div class="sv">Audit</div><div class="sl">Sicherheits-Log</div></div></a>'
            '<a href="/profil/delete" style="text-decoration:none">'
            '<div class="sc" style="border-color:var(--rd)"><div class="si">🗑️</div>'
            '<div class="sv" style="color:var(--rd)">Loeschen</div><div class="sl">Account</div></div></a>'
            '</div>'
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
        return render_template_string(H, content=c, user=session)

    @app.route("/profil/edit", methods=["GET", "POST"])
    def profil_edit():
        if "user_id" not in session:
            return redirect("/login")
        msg = ""
        if request.method == "POST":
            vn = request.form.get("vorname", "").strip()
            nn = request.form.get("nachname", "").strip()
            em = request.form.get("email", "").strip()
            cn = sqlite3.connect(DB)
            cc = cn.cursor()
            cc.execute("UPDATE benutzer SET vorname=?, nachname=?, email=? WHERE id=?",
                       (vn, nn, em, session["user_id"]))
            cn.commit()
            cn.close()
            session["vorname"] = vn
            session["nachname"] = nn
            audit_log(session["user_id"], "PROFILE_UPDATED", "Profil aktualisiert")
            msg = '<div class="al ao">✅ Gespeichert!</div>'

        cn = sqlite3.connect(DB)
        cc = cn.cursor()
        cc.execute("SELECT vorname, nachname, email FROM benutzer WHERE id=?",
                    (session["user_id"],))
        u = cc.fetchone()
        cn.close()

        c = (
            '<h1>👤 Profil bearbeiten</h1>' + msg +
            '<div class="cd"><form method="POST">'
            '<p>Vorname:</p>'
            '<input type="text" name="vorname" value="' + (u[0] or "") + '" required>'
            '<p>Nachname:</p>'
            '<input type="text" name="nachname" value="' + (u[1] or "") + '" required>'
            '<p>E-Mail:</p>'
            '<input type="email" name="email" value="' + (u[2] or "") + '" required>'
            '<button type="submit" class="bt b2" style="width:100%">💾 Speichern</button>'
            '</form></div>'
            '<a href="/profil" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/profil/password", methods=["GET", "POST"])
    def profil_password():
        if "user_id" not in session:
            return redirect("/login")
        msg = ""
        if request.method == "POST":
            old = request.form.get("old_password", "")
            new = request.form.get("new_password", "")
            conf = request.form.get("confirm_password", "")

            cn = sqlite3.connect(DB)
            cc = cn.cursor()
            cc.execute("SELECT passwort FROM benutzer WHERE id=?", (session["user_id"],))
            current = cc.fetchone()[0]

            if hp(old) != current:
                msg = '<div class="al ae">❌ Altes Passwort falsch!</div>'
            elif new != conf:
                msg = '<div class="al ae">❌ Passwoerter unterschiedlich!</div>'
            elif len(new) < 8:
                msg = '<div class="al ae">❌ Min. 8 Zeichen!</div>'
            else:
                cc.execute("UPDATE benutzer SET passwort=? WHERE id=?",
                           (hp(new), session["user_id"]))
                cn.commit()
                audit_log(session["user_id"], "PASSWORD_CHANGED", "Passwort geaendert")
                msg = '<div class="al ao">✅ Passwort geaendert!</div>'
            cn.close()

        c = (
            '<h1>🔑 Passwort aendern</h1>' + msg +
            '<div class="cd"><form method="POST">'
            '<p>Altes Passwort:</p>'
            '<input type="password" name="old_password" placeholder="Altes Passwort" required>'
            '<p>Neues Passwort (min. 8 Zeichen):</p>'
            '<input type="password" name="new_password" placeholder="Neues Passwort" required>'
            '<p>Bestaetigen:</p>'
            '<input type="password" name="confirm_password" placeholder="Nochmal eingeben" required>'
            '<button type="submit" class="bt b2" style="width:100%">🔒 Aendern</button>'
            '</form></div>'
            '<a href="/profil" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/profil/2fa", methods=["GET", "POST"])
    def profil_2fa():
        if "user_id" not in session:
            return redirect("/login")
        uid = session["user_id"]
        tf, cu = get_2fa_status(uid)
        msg = ""

        if request.method == "POST":
            action = request.form.get("action", "")
            token = request.form.get("token", "")

            if action == "enable":
                secret = request.form.get("secret", "")
                if verify_2fa_token(secret, token):
                    codes = enable_2fa(uid, secret)
                    codes_html = "<br>".join(codes) if isinstance(codes, list) else ""
                    tf = True
                    msg = (
                        '<div class="al ao">✅ 2FA aktiviert!'
                        '<h3>🔐 Backup Codes:</h3>'
                        '<div style="background:#0A0E1A;padding:15px;border-radius:8px;'
                        'font-family:monospace;margin-top:10px">'
                        + codes_html + '</div></div>'
                    )
                else:
                    msg = '<div class="al ae">❌ Falscher Code!</div>'

            elif action == "disable":
                if verify_2fa_token(cu, token):
                    disable_2fa(uid)
                    tf = False
                    msg = '<div class="al ao">✅ 2FA deaktiviert</div>'
                else:
                    msg = '<div class="al ae">❌ Falscher Code!</div>'

        if tf:
            c = (
                '<h1>🔐 2FA Aktiv</h1>' + msg +
                '<div class="cd">'
                '<div class="al ao">✅ 2FA ist aktiv! Dein Account ist extra sicher.</div>'
                '<h3>2FA deaktivieren</h3>'
                '<form method="POST">'
                '<input type="hidden" name="action" value="disable">'
                '<p>6-stelliger Code aus deiner Authenticator App:</p>'
                '<input type="text" name="token" placeholder="123456" maxlength="6" required '
                'style="text-align:center;font-size:24px;letter-spacing:10px">'
                '<button type="submit" class="bt b4" style="width:100%">⚠️ Deaktivieren</button>'
                '</form></div>'
                '<a href="/profil" class="bt b1">← Zurueck</a>'
            )
        else:
            secret = generate_2fa_secret()
            qr = generate_qr_code(session.get("username", "user"), secret)
            c = (
                '<h1>🔐 2FA einrichten</h1>' + msg +
                '<div class="cd">'
                '<h3>📱 Schritt 1: Authenticator App</h3>'
                '<p>Google Authenticator, Microsoft Authenticator oder Authy installieren.</p>'
                '</div>'
                '<div class="cd">'
                '<h3>📷 Schritt 2: QR-Code scannen</h3>'
                '<div style="text-align:center;background:white;padding:20px;border-radius:12px">'
                '<img src="' + qr + '" style="max-width:300px"></div>'
                '<p style="margin-top:15px;font-family:monospace;word-break:break-all">'
                'Manuell: ' + secret + '</p>'
                '</div>'
                '<div class="cd">'
                '<h3>✅ Schritt 3: Code eingeben</h3>'
                '<form method="POST">'
                '<input type="hidden" name="action" value="enable">'
                '<input type="hidden" name="secret" value="' + secret + '">'
                '<input type="text" name="token" placeholder="123456" maxlength="6" required '
                'style="text-align:center;font-size:24px;letter-spacing:10px">'
                '<button type="submit" class="bt b2" style="width:100%">🔐 2FA aktivieren</button>'
                '</form></div>'
                '<a href="/profil" class="bt b1">← Zurueck</a>'
            )
        return render_template_string(H, content=c, user=session)

    @app.route("/profil/export")
    def profil_export():
        if "user_id" not in session:
            return redirect("/login")
        data = export_user_data(session["user_id"])
        audit_log(session["user_id"], "DATA_EXPORTED", "DSGVO Export")
        return Response(
            json_module.dumps(data, ensure_ascii=False, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=xsikom_export.json"}
        )

    @app.route("/profil/audit")
    def profil_audit():
        if "user_id" not in session:
            return redirect("/login")

        from security import get_audit_log
        logs = get_audit_log(session["user_id"])

        lh = ""
        if logs:
            for log in logs:
                icons = {
                    "LOGIN": "🔓", "LOGOUT": "🔒",
                    "2FA_ENABLED": "✅", "2FA_DISABLED": "⚠️",
                    "PASSWORD_CHANGED": "🔑", "PROFILE_UPDATED": "👤",
                    "DATA_EXPORTED": "📥", "DELETION_REQUESTED": "🗑️"
                }
                ic = icons.get(log[0], "📋")
                lh += (
                    '<tr style="border-bottom:1px solid var(--bd)">'
                    '<td style="padding:12px">' + ic + '</td>'
                    '<td style="padding:12px"><strong>' + str(log[0]) + '</strong></td>'
                    '<td style="padding:12px">' + str(log[1]) + '</td>'
                    '<td style="padding:12px;font-size:11px;color:var(--t3)">'
                    + str(log[2])[:16] + '</td></tr>'
                )
        else:
            lh = '<tr><td colspan="4" style="text-align:center;padding:20px;color:var(--t3)">Keine Eintraege</td></tr>'

        c = (
            '<h1>📊 Sicherheits-Audit Log</h1>'
            '<p>Alle sicherheitsrelevanten Aktivitaeten</p>'
            '<div class="cd">'
            '<table style="width:100%;border-collapse:collapse">'
            '<thead><tr style="background:rgba(0,217,255,0.1)">'
            '<th style="padding:12px;text-align:left">📋</th>'
            '<th style="padding:12px;text-align:left">Event</th>'
            '<th style="padding:12px;text-align:left">Details</th>'
            '<th style="padding:12px;text-align:left">Zeit</th>'
            '</tr></thead>'
            '<tbody>' + lh + '</tbody></table></div>'
            '<a href="/profil" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/profil/delete", methods=["GET", "POST"])
    def profil_delete():
        if "user_id" not in session:
            return redirect("/login")
        msg = ""
        if request.method == "POST":
            pw = request.form.get("password", "")
            reason = request.form.get("reason", "")
            conf = request.form.get("confirmation", "")

            cn = sqlite3.connect(DB)
            cc = cn.cursor()
            cc.execute("SELECT passwort FROM benutzer WHERE id=?", (session["user_id"],))
            current = cc.fetchone()[0]
            cn.close()

            if hp(pw) != current:
                msg = '<div class="al ae">❌ Passwort falsch!</div>'
            elif conf != "LOESCHEN":
                msg = '<div class="al ae">❌ Bitte "LOESCHEN" eingeben!</div>'
            else:
                token, sched = request_account_deletion(session["user_id"], reason)
                msg = (
                    '<div class="al ao">✅ Loeschungsantrag eingegangen!'
                    '<p>Geplante Loeschung: ' + str(sched)[:10] + '</p>'
                    '<p>Du hast 30 Tage zum Stornieren.</p>'
                    '<a href="/profil/cancel-deletion" class="bt b2">↩️ Stornieren</a>'
                    '</div>'
                )

        c = (
            '<h1 style="color:var(--rd)">🗑️ Account loeschen</h1>'
            '<div class="al aw">'
            '⚠️ <strong>WARNUNG:</strong> Diese Aktion ist endgueltig!'
            '<ul style="margin-top:10px">'
            '<li>Alle Bewerbungen werden geloescht</li>'
            '<li>Alle Dateien werden geloescht</li>'
            '<li>30 Tage Frist zum Stornieren</li></ul></div>'
            + msg +
            '<div class="cd"><h3>🔐 Account-Loeschung (DSGVO Art. 17)</h3>'
            '<form method="POST">'
            '<p>Grund (optional):</p>'
            '<textarea name="reason" rows="3" placeholder="Warum loeschen?"></textarea>'
            '<p>Dein Passwort:</p>'
            '<input type="password" name="password" placeholder="Passwort" required>'
            '<p>Tippe <strong style="color:var(--rd)">LOESCHEN</strong> zur Bestaetigung:</p>'
            '<input type="text" name="confirmation" placeholder="LOESCHEN" required>'
            '<button type="submit" class="bt b4" style="width:100%">🗑️ Account loeschen</button>'
            '</form></div>'
            '<a href="/profil" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/profil/cancel-deletion")
    def profil_cancel_deletion():
        if "user_id" not in session:
            return redirect("/login")
        cancel_deletion(session["user_id"])
        c = (
            '<h1>↩️ Loeschung storniert</h1>'
            '<div class="al ao">✅ Dein Account bleibt aktiv!</div>'
            '<a href="/profil" class="bt b1">Zum Profil</a>'
        )
        return render_template_string(H, content=c, user=session)