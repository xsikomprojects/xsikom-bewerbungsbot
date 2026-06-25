"""Main Routes: Dashboard, Lebenslauf, Uploads, Bewerbungen"""
from flask import render_template_string, request, redirect, session, send_file
from webapp import H, DB, UF, AE, tipp, bz, pl, ps, af, ds, ul, udel
import sqlite3
import os
from datetime import datetime


def register_main_routes(app):

    @app.route("/dashboard")
    def dashboard():
        if "user_id" not in session:
            return redirect("/login")
        bw = bz(session["user_id"])
        lm = "∞" if session.get("premium") else "5"
        bd = '<span class="bg">⭐ PREMIUM</span>' if session.get("premium") else ""
        up = '<a href="/premium" class="bt b3">💎 Upgrade</a>' if not session.get("premium") else ""
        c = (
            '<h1>👋 Hallo, ' + session.get("vorname", "") + '!</h1>'
            '<div class="cd"><h3>📊 Plan: ' + ("Premium" if session.get("premium") else "Free") + ' ' + bd + '</h3>'
            '<p>Bewerbungen: <strong>' + str(bw) + ' / ' + str(lm) + '</strong></p>' + up + '</div>'
            '<h2 style="margin-top:40px">⚡ Schnellaktionen</h2>'
            '<div class="gr">'
            '<a href="/aaliyah" style="text-decoration:none"><div class="sc"><div class="si">🤖</div><div class="sv">Aaliyah</div><div class="sl">KI Chat</div></div></a>'
            '<a href="/avinu" style="text-decoration:none"><div class="sc"><div class="si">⚡</div><div class="sv">AVINU</div><div class="sl">Global Jobs</div></div></a>'
            '<a href="/xsi" style="text-decoration:none"><div class="sc"><div class="si">🤖</div><div class="sv">XSI</div><div class="sl">Auto-Bewerber</div></div></a>'
            '<a href="/lebenslauf" style="text-decoration:none"><div class="sc"><div class="si">📝</div><div class="sv">Lebenslauf</div><div class="sl">Bearbeiten</div></div></a>'
            '<a href="/pdf-lebenslauf" style="text-decoration:none"><div class="sc"><div class="si">📄</div><div class="sv">PDF</div><div class="sl">Generator</div></div></a>'
            '</div>'
            '<div class="cd" style="margin-top:30px"><h3>💡 Tipp</h3><p>' + tipp() + '</p></div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/lebenslauf", methods=["GET", "POST"])
    def lebenslauf():
        if "user_id" not in session:
            return redirect("/login")
        msg = ""
        if request.method == "POST":
            d = {k: request.form.get(k, "") for k in
                 ["vorname", "nachname", "strasse", "plz", "stadt",
                  "telefon", "email", "geburtsdatum", "kenntnisse", "sprachen"]}
            ps(session["user_id"], d)
            msg = '<div class="al ao">✅ Gespeichert!</div>'
        p = pl(session["user_id"])
        c = (
            '<h1>📝 Lebenslauf</h1>' + msg +
            '<form method="POST">'
            '<div class="cd"><h3>👤 Daten</h3>'
            '<input type="text" name="vorname" placeholder="Vorname" value="' + p.get("vorname", "") + '">'
            '<input type="text" name="nachname" placeholder="Nachname" value="' + p.get("nachname", "") + '">'
            '<input type="text" name="strasse" placeholder="Strasse" value="' + p.get("strasse", "") + '">'
            '<input type="text" name="plz" placeholder="PLZ" value="' + p.get("plz", "") + '">'
            '<input type="text" name="stadt" placeholder="Stadt" value="' + p.get("stadt", "") + '">'
            '<input type="text" name="telefon" placeholder="Telefon" value="' + p.get("telefon", "") + '">'
            '<input type="email" name="email" placeholder="E-Mail" value="' + p.get("email", "") + '">'
            '<input type="text" name="geburtsdatum" placeholder="Geburtsdatum" value="' + p.get("geburtsdatum", "") + '">'
            '</div>'
            '<div class="cd"><h3>💼 Kenntnisse</h3>'
            '<textarea name="kenntnisse" rows="6">' + p.get("kenntnisse", "") + '</textarea></div>'
            '<div class="cd"><h3>🌍 Sprachen</h3>'
            '<textarea name="sprachen" rows="4">' + p.get("sprachen", "") + '</textarea></div>'
            '<button type="submit" class="bt b2">💾 Speichern</button>'
            '</form>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/uploads", methods=["GET", "POST"])
    def uploads():
        if "user_id" not in session:
            return redirect("/login")
        msg = ""
        if request.method == "POST":
            kat = request.form.get("kategorie", "dokument")
            if "datei" in request.files:
                f = request.files["datei"]
                if f and f.filename and af(f.filename):
                    r = ds(f, session["user_id"], kat)
                    if r:
                        msg = '<div class="al ao">✅ ' + r + '!</div>'
        uu = ul(session["user_id"])
        uh = ""
        for u in uu:
            ic = "📄" if u[2] == ".pdf" else "🖼️"
            uh += (
                '<div class="ui"><div>' + ic + ' <strong>' + u[1] + '</strong><br>'
                '<small>' + u[3] + ' - ' + u[5][:16] + '</small></div><div>'
                '<a href="/download/' + str(u[0]) + '" class="bt b1" style="padding:8px 14px">⬇️</a> '
                '<a href="/delete/' + str(u[0]) + '" class="bt b4" style="padding:8px 14px" '
                'onclick="return confirm(\'Loeschen?\')">🗑️</a></div></div>'
            )
        if not uh:
            uh = '<p style="color:var(--t3)">Keine Dateien</p>'
        c = (
            '<h1>📂 Dateien</h1>' + msg +
            '<div class="cd"><form method="POST" enctype="multipart/form-data">'
            '<select name="kategorie" required>'
            '<option value="lebenslauf">📄 Lebenslauf</option>'
            '<option value="zeugnis">📜 Zeugnis</option>'
            '<option value="zertifikat">🏆 Zertifikat</option>'
            '<option value="bild">🖼️ Bewerbungsbild</option></select>'
            '<input type="file" name="datei" required accept=".pdf,.png,.jpg,.jpeg">'
            '<button type="submit" class="bt b2" style="width:100%">🚀 Upload</button>'
            '</form></div>'
            '<div class="cd">' + uh + '</div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/download/<int:uid>")
    def download_datei(uid):
        if "user_id" not in session:
            return redirect("/login")
        cn = sqlite3.connect(DB)
        cc = cn.cursor()
        cc.execute("SELECT pfad, dateiname FROM uploads WHERE id=? AND user_id=?",
                    (uid, session["user_id"]))
        r = cc.fetchone()
        cn.close()
        if r and os.path.exists(r[0]):
            return send_file(r[0], as_attachment=True, download_name=r[1])
        return "Nicht gefunden", 404

    @app.route("/delete/<int:uid>")
    def delete_datei(uid):
        if "user_id" not in session:
            return redirect("/login")
        udel(uid, session["user_id"])
        return redirect("/uploads")

    @app.route("/bewerbungen", methods=["GET", "POST"])
    def bewerbungen():
        if "user_id" not in session:
            return redirect("/login")
        msg = ""
        if request.method == "POST":
            f = request.form.get("firma", "").strip()
            e = request.form.get("email", "").strip()
            bw2 = bz(session["user_id"])
            if not session.get("premium") and bw2 >= 5:
                msg = '<div class="al aw">⚠️ Limit!</div>'
            elif f and e:
                cn = sqlite3.connect(DB)
                cc = cn.cursor()
                try:
                    cc.execute(
                        "INSERT INTO bewerbungen (user_id, firma, email, datum, typ) VALUES (?,?,?,?,?)",
                        (session["user_id"], f, e, datetime.now().isoformat(),
                         request.form.get("typ", "job")))
                except Exception:
                    cc.execute(
                        "INSERT INTO bewerbungen (user_id, firma, email, datum) VALUES (?,?,?,?)",
                        (session["user_id"], f, e, datetime.now().isoformat()))
                cn.commit()
                cn.close()
                msg = '<div class="al ao">✅ ' + f + '!</div>'
        bw2 = bz(session["user_id"])
        lm = "∞" if session.get("premium") else "5"
        c = (
            '<h1>📧 Bewerbungen</h1>'
            '<div class="cd"><h3>📊 ' + str(bw2) + ' / ' + str(lm) + '</h3></div>'
            + msg +
            '<div class="cd"><form method="POST">'
            '<select name="typ">'
            '<option value="job">💼 Job</option>'
            '<option value="praktikum">🎓 Praktikum</option>'
            '<option value="ausbildung">📚 Ausbildung</option>'
            '<option value="werkstudent">🧑‍💻 Werkstudent</option></select>'
            '<input type="text" name="firma" placeholder="Firma" required>'
            '<input type="email" name="email" placeholder="E-Mail" required>'
            '<button type="submit" class="bt b2">💾 Speichern</button>'
            '</form></div>'
        )
        return render_template_string(H, content=c, user=session)