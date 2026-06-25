"""
Auth Routes: Login, Register, Logout, Password-Reset
Sprint 1: Rate-Limiting + XSS-Schutz + CSRF
"""
from flask import render_template_string, request, redirect, session
from flask_wtf.csrf import generate_csrf
from shared import H, DB, bp, ba, hp, CE
from security import (
    create_password_reset_token,
    verify_reset_token,
    use_reset_token,
    audit_log,
)
from security_middleware import limiter, xss_text
import sqlite3


# ─────────────────────────────────────────────────────────────────
# HILFSFUNKTIONEN
# ─────────────────────────────────────────────────────────────────

def _db_connect():
    cn = sqlite3.connect(DB)
    cc = cn.cursor()
    return cn, cc


# ─────────────────────────────────────────────────────────────────
# ROUTE-REGISTRIERUNG
# ─────────────────────────────────────────────────────────────────

def register_auth_routes(app):

    # ════════════════════════════════════════════════════════════
    # INDEX
    # ════════════════════════════════════════════════════════════

    @app.route("/")
    def index():
        return (
            redirect("/dashboard")
            if "user_id" in session
            else redirect("/login")
        )

    # ════════════════════════════════════════════════════════════
    # LOGIN
    # ════════════════════════════════════════════════════════════

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("5 per minute")
    def login():
        msg   = ""
        token = generate_csrf()

        if request.method == "POST":
            username = xss_text(
                request.form.get("username", "").strip()
            )
            password = request.form.get("password", "").strip()
            r        = bp(username, password)

            if r:
                session.permanent   = True
                session["user_id"]  = r["id"]
                session["username"] = r["benutzername"]
                session["vorname"]  = r["vorname"]
                session["nachname"] = r["nachname"]
                session["rolle"]    = r["rolle"]
                session["premium"]  = r["premium"]
                audit_log(r["id"], "LOGIN", "Login")
                return redirect("/dashboard")

            msg = '<div class="al ae">❌ Login falsch!</div>'

        c = (
            '<div style="max-width:450px;margin:60px auto">'
            '<div class="cd">'
            '<h1 style="text-align:center">🔐 Anmelden</h1>'
            + msg +
            '<form method="POST">'
            f'<input type="hidden" name="csrf_token" value="{token}">'
            '<input type="text" name="username" '
            'placeholder="Benutzername" required '
            'autocomplete="username">'
            '<input type="password" name="password" '
            'placeholder="Passwort" required '
            'autocomplete="current-password">'
            '<button type="submit" class="bt b1" style="width:100%">'
            '🚀 Anmelden</button>'
            '</form>'
            '<p style="text-align:center;margin-top:25px">'
            '<a href="/register">✨ Neuen Account</a></p>'
            '<p style="text-align:center;margin-top:10px">'
            '<a href="/password-reset" '
            'style="color:var(--t3);font-size:13px">'
            '🔑 Passwort vergessen?</a></p>'
            '</div></div>'
        )
        return render_template_string(H, content=c, user=None)

    # ════════════════════════════════════════════════════════════
    # REGISTER
    # ════════════════════════════════════════════════════════════

    @app.route("/register", methods=["GET", "POST"])
    @limiter.limit("3 per minute")
    def register():
        msg   = ""
        token = generate_csrf()

        if request.method == "POST":
            u  = xss_text(request.form.get("username",  "").strip())
            p  =          request.form.get("password",  "").strip()
            e  = xss_text(request.form.get("email",     "").strip())
            vn = xss_text(request.form.get("vorname",   "").strip())
            nn = xss_text(request.form.get("nachname",  "").strip())
            kt = xss_text(request.form.get("kunde_typ", "privat"))
            ds =          request.form.get("datenschutz")
            ag =          request.form.get("agb")
            wr =          request.form.get("widerruf")

            if not all([u, p, e, ds, ag, wr]):
                msg = '<div class="al ae">❌ Alle Felder ausfuellen!</div>'
            elif len(p) < 6:
                msg = '<div class="al ae">❌ Min. 6 Zeichen!</div>'
            elif "@" not in e or "." not in e:
                msg = '<div class="al ae">❌ Ungueltige E-Mail!</div>'
            elif ba(u, p, e, vn, nn, kt):
                return redirect("/login")
            else:
                msg = '<div class="al ae">❌ Name bereits vergeben!</div>'

        c = (
            '<div style="max-width:600px;margin:30px auto">'
            '<div class="cd">'
            '<h1>✨ Registrieren</h1>'
            + msg +
            '<form method="POST">'
            f'<input type="hidden" name="csrf_token" value="{token}">'
            '<select name="kunde_typ" required>'
            '<option value="privat">👤 Privat</option>'
            '<option value="firma">🏢 Firma</option>'
            '</select>'
            '<input type="text" name="username" '
            'placeholder="Benutzername" required>'
            '<input type="password" name="password" '
            'placeholder="Passwort (min. 6 Zeichen)" required>'
            '<input type="email" name="email" '
            'placeholder="E-Mail" required>'
            '<input type="text" name="vorname" '
            'placeholder="Vorname">'
            '<input type="text" name="nachname" '
            'placeholder="Nachname">'
            '<div style="margin-top:20px;padding:20px;'
            'background:rgba(10,14,26,0.5);border-radius:12px">'
            '<p><input type="checkbox" name="datenschutz" '
            'required style="width:auto"> '
            '<a href="/datenschutz" target="_blank">Datenschutz</a></p>'
            '<p><input type="checkbox" name="agb" '
            'required style="width:auto"> '
            '<a href="/agb" target="_blank">AGB</a></p>'
            '<p><input type="checkbox" name="widerruf" '
            'required style="width:auto"> '
            '<a href="/widerruf" target="_blank">Widerruf</a></p>'
            '</div>'
            '<button type="submit" class="bt b2" style="width:100%">'
            '🚀 Account erstellen</button>'
            '</form>'
            '<p style="text-align:center;margin-top:20px">'
            '<a href="/login">← Login</a></p>'
            '</div></div>'
        )
        return render_template_string(H, content=c, user=None)

    # ════════════════════════════════════════════════════════════
    # LOGOUT
    # ════════════════════════════════════════════════════════════

    @app.route("/logout")
    def logout():
        if "user_id" in session:
            audit_log(session["user_id"], "LOGOUT", "")
        session.clear()
        return redirect("/login")

    # ════════════════════════════════════════════════════════════
    # PASSWORD RESET – ANFRAGE
    # ════════════════════════════════════════════════════════════

    @app.route("/password-reset", methods=["GET", "POST"])
    @limiter.limit("3 per hour")
    def password_reset_request():
        msg   = ""
        token = generate_csrf()

        if request.method == "POST":
            email  = xss_text(request.form.get("email", "").strip())
            cn, cc = _db_connect()
            cc.execute(
                "SELECT id FROM benutzer WHERE email=?", (email,)
            )
            u = cc.fetchone()
            cn.close()

            if u:
                t2   = create_password_reset_token(u[0])
                link = f"{request.host_url}password-reset/{t2}"
                msg  = (
                    f'<div class="al ao">'
                    f'🔑 <a href="{link}">Reset-Link</a>'
                    f'</div>'
                )
            else:
                msg = (
                    '<div class="al ao">'
                    '📧 Falls bekannt, wurde ein Link verschickt.'
                    '</div>'
                )

        c = (
            '<div style="max-width:450px;margin:60px auto">'
            '<div class="cd">'
            '<h1>🔑 Passwort vergessen</h1>'
            + msg +
            '<form method="POST">'
            f'<input type="hidden" name="csrf_token" value="{token}">'
            '<input type="email" name="email" '
            'placeholder="deine@email.de" required>'
            '<button type="submit" class="bt b1" style="width:100%">'
            '📧 Link anfordern</button>'
            '</form>'
            '<p style="text-align:center;margin-top:20px">'
            '<a href="/login">← Login</a></p>'
            '</div></div>'
        )
        return render_template_string(H, content=c, user=None)

    # ════════════════════════════════════════════════════════════
    # PASSWORD RESET – NEUES PASSWORT
    # ════════════════════════════════════════════════════════════

    @app.route("/password-reset/<reset_token>", methods=["GET", "POST"])
    @limiter.limit("5 per hour")
    def password_reset_new(reset_token):
        uid        = verify_reset_token(reset_token)
        csrf_token = generate_csrf()

        if not uid:
            c = (
                '<div style="max-width:450px;margin:60px auto">'
                '<div class="cd">'
                '<h1>❌ Link ungueltig</h1>'
                '<p style="color:var(--t3)">Abgelaufen oder '
                'bereits verwendet.</p>'
                '<a href="/password-reset" class="bt b1">'
                '🔑 Neuen Link anfordern</a>'
                '</div></div>'
            )
            return render_template_string(H, content=c, user=None)

        msg = ""

        if request.method == "POST":
            new  = request.form.get("new_password",     "")
            conf = request.form.get("confirm_password", "")

            if len(new) < 8:
                msg = '<div class="al ae">❌ Min. 8 Zeichen!</div>'
            elif new != conf:
                msg = '<div class="al ae">❌ Unterschiedlich!</div>'
            else:
                cn, cc = _db_connect()
                cc.execute(
                    "UPDATE benutzer SET passwort=? WHERE id=?",
                    (hp(new), uid)
                )
                cn.commit()
                cn.close()
                use_reset_token(reset_token)
                return redirect("/login")

        c = (
            '<div style="max-width:450px;margin:60px auto">'
            '<div class="cd">'
            '<h1>🔑 Neues Passwort</h1>'
            + msg +
            '<form method="POST">'
            f'<input type="hidden" name="csrf_token" '
            f'value="{csrf_token}">'
            '<input type="password" name="new_password" '
            'placeholder="Neues Passwort" required>'
            '<input type="password" name="confirm_password" '
            'placeholder="Bestaetigen" required>'
            '<button type="submit" class="bt b2" style="width:100%">'
            '✅ Speichern</button>'
            '</form>'
            '</div></div>'
        )
        return render_template_string(H, content=c, user=None)