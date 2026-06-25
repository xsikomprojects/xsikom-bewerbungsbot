"""
Main Routes: Dashboard, Lebenslauf, Uploads, Bewerbungen
Alle Imports kommen aus shared.py – kein Import aus webapp.py!
"""
from flask import render_template_string, request, redirect, session, send_file
from shared import H, DB, UF, AE, tipp, bz, pl, ps, af, ds, ul, udel
import sqlite3
import os
from datetime import datetime


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


def _plan_info():
    """Gibt (plan_label, limit_label, badge_html, upgrade_html) zurück."""
    premium      = session.get("premium")
    plan_label   = "Premium" if premium else "Free"
    limit_label  = "∞"      if premium else "5"
    badge_html   = '<span class="bg">⭐ PREMIUM</span>' if premium else ""
    upgrade_html = (
        '<a href="/premium" class="bt b3">💎 Upgrade</a>'
        if not premium else ""
    )
    return plan_label, limit_label, badge_html, upgrade_html


def _schnellaktionen():
    """Gibt die Schnellaktions-Kacheln als HTML zurück."""
    kacheln = [
        ("/aaliyah",      "🤖", "Aaliyah",    "KI Chat"),
        ("/avinu",        "⚡", "AVINU",       "Global Jobs"),
        ("/xsi",          "🤖", "XSI",         "Auto-Bewerber"),
        ("/lebenslauf",   "📝", "Lebenslauf",  "Bearbeiten"),
        ("/pdf-lebenslauf","📄","PDF",          "Generator"),
    ]
    kacheln_html = "".join(
        f'<a href="{url}" style="text-decoration:none">'
        f'<div class="sc">'
        f'<div class="si">{icon}</div>'
        f'<div class="sv">{titel}</div>'
        f'<div class="sl">{untertitel}</div>'
        f'</div></a>'
        for url, icon, titel, untertitel in kacheln
    )
    return '<div class="gr">' + kacheln_html + '</div>'


# ─────────────────────────────────────────────────────────────────
# ROUTE-REGISTRIERUNG
# ─────────────────────────────────────────────────────────────────

def register_main_routes(app):

    # ════════════════════════════════════════════════════════════
    # DASHBOARD
    # ════════════════════════════════════════════════════════════

    @app.route("/dashboard")
    def dashboard():
        r = _login_required()
        if r: return r

        uid                                      = session["user_id"]
        bw                                       = bz(uid)
        plan_label, limit_label, badge, upgrade  = _plan_info()

        c = (
            f'<h1>👋 Hallo, {session.get("vorname", "")}!</h1>'

            '<div class="cd">'
            f'<h3>📊 Plan: {plan_label} {badge}</h3>'
            f'<p>Bewerbungen: <strong>{bw} / {limit_label}</strong></p>'
            + upgrade +
            '</div>'

            '<h2 style="margin-top:40px">⚡ Schnellaktionen</h2>'
            + _schnellaktionen() +

            '<div class="cd" style="margin-top:30px">'
            f'<h3>💡 Tipp</h3><p>{tipp()}</p>'
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # LEBENSLAUF
    # ════════════════════════════════════════════════════════════

    @app.route("/lebenslauf", methods=["GET", "POST"])
    def lebenslauf():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        FELDER = [
            ("vorname",       "text",  "Vorname"),
            ("nachname",      "text",  "Nachname"),
            ("strasse",       "text",  "Strasse"),
            ("plz",           "text",  "PLZ"),
            ("stadt",         "text",  "Stadt"),
            ("telefon",       "text",  "Telefon"),
            ("email",         "email", "E-Mail"),
            ("geburtsdatum",  "text",  "Geburtsdatum"),
        ]

        if request.method == "POST":
            d = {
                k: request.form.get(k, "")
                for k, _, _ in FELDER
            }
            d["kenntnisse"] = request.form.get("kenntnisse", "")
            d["sprachen"]   = request.form.get("sprachen",   "")
            ps(uid, d)
            msg = '<div class="al ao">✅ Gespeichert!</div>'

        p = pl(uid)

        felder_html = "".join(
            f'<input type="{typ}" name="{key}" '
            f'placeholder="{label}" '
            f'value="{p.get(key, "")}">'
            for key, typ, label in FELDER
        )

        c = (
            '<h1>📝 Lebenslauf</h1>'
            + msg +
            '<form method="POST">'

            '<div class="cd">'
            '<h3>👤 Persönliche Daten</h3>'
            + felder_html +
            '</div>'

            '<div class="cd">'
            '<h3>💼 Kenntnisse</h3>'
            f'<textarea name="kenntnisse" rows="6">'
            f'{p.get("kenntnisse", "")}</textarea>'
            '</div>'

            '<div class="cd">'
            '<h3>🌍 Sprachen</h3>'
            f'<textarea name="sprachen" rows="4">'
            f'{p.get("sprachen", "")}</textarea>'
            '</div>'

            '<button type="submit" class="bt b2" style="width:100%">'
            '💾 Speichern</button>'
            '</form>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # UPLOADS
    # ════════════════════════════════════════════════════════════

    @app.route("/uploads", methods=["GET", "POST"])
    def uploads():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        if request.method == "POST":
            kat = request.form.get("kategorie", "dokument")
            if "datei" in request.files:
                f = request.files["datei"]
                if f and f.filename and af(f.filename):
                    result = ds(f, uid, kat)
                    if result:
                        msg = (
                            '<div class="al ao">✅ '
                            + result + ' hochgeladen!</div>'
                        )
                    else:
                        msg = '<div class="al ae">❌ Upload fehlgeschlagen!</div>'
                else:
                    msg = '<div class="al ae">❌ Ungültiger Dateityp!</div>'

        # ── Dateien laden ────────────────────────────────────────
        uu = ul(uid)
        if uu:
            uh = "".join(
                '<div class="ui"><div>'
                + ("📄" if u[2] == ".pdf" else "🖼️")
                + f' <strong>{u[1]}</strong><br>'
                f'<small style="color:var(--t3)">'
                f'{u[3]} · {str(u[5])[:16]}</small>'
                '</div><div>'
                f'<a href="/download/{u[0]}" '
                'class="bt b1" style="padding:8px 14px">⬇️</a> '
                f'<a href="/delete/{u[0]}" '
                'class="bt b4" style="padding:8px 14px" '
                "onclick=\"return confirm('Loeschen?')\">🗑️</a>"
                '</div></div>'
                for u in uu
            )
        else:
            uh = '<p style="color:var(--t3);text-align:center;padding:20px">Keine Dateien hochgeladen</p>'

        c = (
            '<h1>📂 Dateien & Uploads</h1>'
            + msg +

            '<div class="cd">'
            '<h3>📤 Neue Datei hochladen</h3>'
            '<form method="POST" enctype="multipart/form-data">'
            '<p>📂 Kategorie:</p>'
            '<select name="kategorie" required>'
            '<option value="lebenslauf">📄 Lebenslauf</option>'
            '<option value="zeugnis">📜 Zeugnis</option>'
            '<option value="zertifikat">🏆 Zertifikat</option>'
            '<option value="bild">🖼️ Bewerbungsbild</option>'
            '</select>'
            '<p>📎 Datei:</p>'
            '<input type="file" name="datei" required '
            'accept=".pdf,.png,.jpg,.jpeg">'
            '<button type="submit" class="bt b2" style="width:100%">'
            '🚀 Hochladen</button>'
            '</form></div>'

            '<div class="cd">'
            '<h3>📁 Meine Dateien</h3>'
            + uh +
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # DOWNLOAD
    # ════════════════════════════════════════════════════════════

    @app.route("/download/<int:fid>")
    def download_datei(fid):
        r = _login_required()
        if r: return r

        cn, cc = _db_connect()
        cc.execute(
            "SELECT pfad, dateiname FROM uploads "
            "WHERE id=? AND user_id=?",
            (fid, session["user_id"])
        )
        row = cc.fetchone()
        cn.close()

        if row and os.path.exists(row[0]):
            return send_file(
                row[0],
                as_attachment=True,
                download_name=row[1]
            )
        return "<h3>❌ Datei nicht gefunden</h3>", 404

    # ════════════════════════════════════════════════════════════
    # DELETE
    # ════════════════════════════════════════════════════════════

    @app.route("/delete/<int:fid>")
    def delete_datei(fid):
        r = _login_required()
        if r: return r

        udel(fid, session["user_id"])
        return redirect("/uploads")

    # ════════════════════════════════════════════════════════════
    # BEWERBUNGEN
    # ════════════════════════════════════════════════════════════

    @app.route("/bewerbungen", methods=["GET", "POST"])
    def bewerbungen():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        if request.method == "POST":
            firma  = request.form.get("firma", "").strip()
            email  = request.form.get("email", "").strip()
            typ    = request.form.get("typ",   "job")
            anzahl = bz(uid)

            if not session.get("premium") and anzahl >= 5:
                msg = (
                    '<div class="al aw">⚠️ Free-Limit erreicht! '
                    '<a href="/premium">💎 Upgrade</a></div>'
                )
            elif firma and email:
                cn, cc = _db_connect()
                try:
                    cc.execute(
                        "INSERT INTO bewerbungen "
                        "(user_id, firma, email, datum, typ) "
                        "VALUES (?,?,?,?,?)",
                        (uid, firma, email,
                         datetime.now().isoformat(), typ)
                    )
                except Exception:
                    cc.execute(
                        "INSERT INTO bewerbungen "
                        "(user_id, firma, email, datum) "
                        "VALUES (?,?,?,?)",
                        (uid, firma, email,
                         datetime.now().isoformat())
                    )
                cn.commit()
                cn.close()
                msg = (
                    '<div class="al ao">✅ Bewerbung bei '
                    + firma + ' gespeichert!</div>'
                )

        anzahl                                   = bz(uid)
        _, limit_label, _, _                     = _plan_info()

        c = (
            '<h1>📧 Bewerbungen</h1>'

            '<div class="cd">'
            f'<h3>📊 {anzahl} / {limit_label} Bewerbungen</h3>'
            '</div>'

            + msg +

            '<div class="cd">'
            '<h3>➕ Neue Bewerbung</h3>'
            '<form method="POST">'
            '<p>📋 Typ:</p>'
            '<select name="typ">'
            '<option value="job">💼 Job</option>'
            '<option value="praktikum">🎓 Praktikum</option>'
            '<option value="ausbildung">📚 Ausbildung</option>'
            '<option value="werkstudent">🧑‍💻 Werkstudent</option>'
            '</select>'
            '<p>🏢 Firma:</p>'
            '<input type="text" name="firma" '
            'placeholder="Firma" required>'
            '<p>📧 E-Mail:</p>'
            '<input type="email" name="email" '
            'placeholder="bewerbung@firma.de" required>'
            '<button type="submit" class="bt b2" style="width:100%">'
            '💾 Speichern</button>'
            '</form></div>'
        )
        return render_template_string(H, content=c, user=session)