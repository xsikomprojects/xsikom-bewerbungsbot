"""Auth Routes: Login, Register, Logout, Password-Reset"""
from flask import render_template_string, request, redirect, session
from webapp import H, bp, ba, hp, DB, CE
from security import create_password_reset_token, verify_reset_token, use_reset_token, audit_log
import sqlite3


def register_auth_routes(app):

    @app.route("/")
    def index():
        return redirect("/dashboard") if "user_id" in session else redirect("/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        msg = ""
        if request.method == "POST":
            r = bp(request.form.get("username", "").strip(), request.form.get("password", "").strip())
            if r:
                session["user_id"] = r["id"]
                session["username"] = r["benutzername"]
                session["vorname"] = r["vorname"]
                session["nachname"] = r["nachname"]
                session["rolle"] = r["rolle"]
                session["premium"] = r["premium"]
                audit_log(r["id"], "LOGIN", "Login")
                return redirect("/dashboard")
            msg = '<div class="al ae">❌ Login falsch!</div>'
        c = ('<div style="max-width:450px;margin:60px auto"><div class="cd">'
             '<h1 style="text-align:center">🔐 Anmelden</h1>' + msg +
             '<form method="POST">'
             '<input type="text" name="username" value="admin" placeholder="Benutzername" required>'
             '<input type="password" name="password" placeholder="Passwort" required>'
             '<button type="submit" class="bt b1" style="width:100%">🚀 Anmelden</button>'
             '</form>'
             '<p style="text-align:center;margin-top:25px"><a href="/register">✨ Neuen Account</a></p>'
             '<p style="text-align:center;margin-top:10px">'
             '<a href="/password-reset" style="color:var(--t3);font-size:13px">🔑 Passwort vergessen?</a></p>'
             '</div></div>')
        return render_template_string(H, content=c, user=None)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        msg = ""
        if request.method == "POST":
            u = request.form.get("username", "").strip()
            p = request.form.get("password", "").strip()
            e = request.form.get("email", "").strip()
            if not all([u, p, e, request.form.get("datenschutz"), request.form.get("agb"), request.form.get("widerruf")]):
                msg = '<div class="al ae">❌ Alle Felder!</div>'
            elif len(p) < 6:
                msg = '<div class="al ae">❌ Min. 6 Zeichen!</div>'
            elif ba(u, p, e, request.form.get("vorname", ""), request.form.get("nachname", ""), request.form.get("kunde_typ", "privat")):
                return redirect("/login")
            else:
                msg = '<div class="al ae">❌ Name vergeben!</div>'
        c = ('<div style="max-width:600px;margin:30px auto"><div class="cd">'
             '<h1>✨ Registrieren</h1>' + msg +
             '<form method="POST">'
             '<select name="kunde_typ" required>'
             '<option value="privat">👤 Privat</option>'
             '<option value="firma">🏢 Firma</option></select>'
             '<input type="text" name="username" placeholder="Benutzername" required>'
             '<input type="password" name="password" placeholder="Passwort" required>'
             '<input type="email" name="email" placeholder="E-Mail" required>'
             '<input type="text" name="vorname" placeholder="Vorname">'
             '<input type="text" name="nachname" placeholder="Nachname">'
             '<div style="margin-top:20px;padding:20px;background:rgba(10,14,26,0.5);border-radius:12px">'
             '<p><input type="checkbox" name="datenschutz" required style="width:auto"> '
             '<a href="/datenschutz" target="_blank">Datenschutz</a></p>'
             '<p><input type="checkbox" name="agb" required style="width:auto"> '
             '<a href="/agb" target="_blank">AGB</a></p>'
             '<p><input type="checkbox" name="widerruf" required style="width:auto"> '
             '<a href="/widerruf" target="_blank">Widerruf</a></p></div>'
             '<button type="submit" class="bt b2" style="width:100%">🚀 Account erstellen</button>'
             '</form>'
             '<p style="text-align:center;margin-top:20px"><a href="/login">← Login</a></p>'
             '</div></div>')
        return render_template_string(H, content=c, user=None)

    @app.route("/logout")
    def logout():
        if "user_id" in session:
            audit_log(session["user_id"], "LOGOUT", "")
        session.clear()
        return redirect("/login")

    @app.route("/password-reset", methods=["GET", "POST"])
    def password_reset_request():
        msg = ""
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            cn = sqlite3.connect(DB)
            cc = cn.cursor()
            cc.execute("SELECT id FROM benutzer WHERE email=?", (email,))
            u = cc.fetchone()
            cn.close()
            if u:
                token = create_password_reset_token(u[0])
                link = f"{request.host_url}password-reset/{token}"
                msg = f'<div class="al ao">Link: {link}</div>'
        c = ('<div style="max-width:450px;margin:60px auto"><div class="cd">'
             '<h1>🔑 Reset</h1>' + msg +
             '<form method="POST">'
             '<input type="email" name="email" placeholder="E-Mail" required>'
             '<button type="submit" class="bt b1">📧</button>'
             '</form></div></div>')
        return render_template_string(H, content=c, user=None)

    @app.route("/password-reset/<token>", methods=["GET", "POST"])
    def password_reset_new(token):
        uid = verify_reset_token(token)
        if not uid:
            return render_template_string(H, content="<h1>❌ Ungueltig</h1>", user=None)
        if request.method == "POST":
            new = request.form.get("new_password", "")
            if len(new) >= 8:
                cn = sqlite3.connect(DB)
                cc = cn.cursor()
                cc.execute("UPDATE benutzer SET passwort=? WHERE id=?", (hp(new), uid))
                cn.commit()
                cn.close()
                use_reset_token(token)
                return redirect("/login")
        c = ('<div style="max-width:450px;margin:60px auto"><div class="cd">'
             '<h1>Neues Passwort</h1>'
             '<form method="POST">'
             '<input type="password" name="new_password" required>'
             '<button type="submit" class="bt b2">✅</button>'
             '</form></div></div>')
        return render_template_string(H, content=c, user=None)