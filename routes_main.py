"""
Main Routes: Dashboard, Lebenslauf, Uploads, Bewerbungen
F1: Charts, F6: Tags, F3: Dark/Light Mode
F9: Teilen, F10: Erfolgs-Statistik
"""
from flask import (
    render_template_string, request,
    redirect, session, send_file, jsonify
)
from shared import (
    H, DB, UF, AE, tipp, bz, pl, ps, af, ds, ul, udel,
    chart_daten_laden, tags_laden, tag_hinzufuegen,
    tag_loeschen, alle_tags_user, STANDARD_TAGS,
    get_theme, set_theme,
    erfolgs_statistik, teilen_links,
)
import sqlite3
import os
import json
from datetime import datetime


# ─────────────────────────────────────────────────────────────────
# HILFSFUNKTIONEN
# ─────────────────────────────────────────────────────────────────

def _login_required():
    if "user_id" not in session:
        return redirect("/login")
    return None


def _db_connect():
    cn = sqlite3.connect(DB)
    cc = cn.cursor()
    return cn, cc


def _plan_info():
    premium     = session.get("premium")
    plan_label  = "Premium" if premium else "Free"
    limit_label = "∞"       if premium else "5"
    badge       = (
        '<span class="bg">⭐ PREMIUM</span>' if premium else ""
    )
    upgrade     = (
        '<a href="/premium" class="bt b3">💎 Upgrade</a>'
        if not premium else ""
    )
    return plan_label, limit_label, badge, upgrade


def _tag_html(tags):
    """Tags als HTML-Badges."""
    if not tags:
        return ""
    return "".join(
        f'<span class="tg tg-{t[2]}">'
        f'{t[1]}'
        f'<a href="/tag/loeschen/{t[0]}" '
        f'style="color:inherit;margin-left:4px;opacity:0.7">×</a>'
        f'</span>'
        for t in tags
    )


def _standard_tags_html(bewerbung_id):
    """Standard-Tag-Buttons."""
    return "".join(
        f'<a href="/tag/add/{bewerbung_id}'
        f'?tag={t}&farbe={f}&back=/bewerbungen" '
        f'class="tg tg-{f}" '
        f'style="text-decoration:none;cursor:pointer">'
        f'{t}</a>'
        for t, f in STANDARD_TAGS
    )


# ─────────────────────────────────────────────────────────────────
# ROUTE-REGISTRIERUNG
# ─────────────────────────────────────────────────────────────────

def register_main_routes(app):

    # ════════════════════════════════════════════════════════════
    # F3: THEME
    # ════════════════════════════════════════════════════════════

    @app.route("/theme/<theme>")
    def theme_setzen(theme):
        if "user_id" in session:
            set_theme(session["user_id"], theme)
            session["theme"] = theme
        return "", 204

    # ════════════════════════════════════════════════════════════
    # F6: TAG ROUTEN
    # ════════════════════════════════════════════════════════════

    @app.route("/tag/add/<int:bid>")
    def tag_add(bid):
        r = _login_required()
        if r: return r

        tag     = request.args.get("tag",   "").strip()[:30]
        farbe   = request.args.get("farbe", "cy")
        zurueck = request.args.get("back",  "/bewerbungen")

        if tag:
            tag_hinzufuegen(session["user_id"], bid, tag, farbe)
        return redirect(zurueck)

    @app.route("/tag/loeschen/<int:tid>")
    def tag_del(tid):
        r = _login_required()
        if r: return r

        tag_loeschen(tid, session["user_id"])
        return redirect(request.referrer or "/bewerbungen")

    # ════════════════════════════════════════════════════════════
    # F1: DASHBOARD MIT CHARTS
    # ════════════════════════════════════════════════════════════

    @app.route("/dashboard")
    def dashboard():
        r = _login_required()
        if r: return r

        uid                                     = session["user_id"]
        bw                                      = bz(uid)
        plan_label, limit_label, badge, upgrade = _plan_info()
        cd = chart_daten_laden(uid)

        wochen_json = json.dumps({
            "labels": cd["wochen"]["labels"],
            "daten":  cd["wochen"]["daten"],
        })
        monate_json = json.dumps({
            "labels": cd["monate"]["labels"],
            "daten":  cd["monate"]["daten"],
        })
        status_json = json.dumps({
            "labels": cd["status"]["labels"],
            "daten":  cd["status"]["daten"],
        })

        charts_html = (
            '<div class="cd">'
            '<h3>📊 Bewerbungs-Statistik</h3>'
            '<div style="display:flex;gap:10px;'
            'margin-bottom:20px;flex-wrap:wrap">'
            '<button onclick="zeigChart(\'wochen\')" '
            'class="bt b1" style="padding:8px 16px;font-size:13px">'
            '📅 Wochen</button>'
            '<button onclick="zeigChart(\'monate\')" '
            'class="bt b5" style="padding:8px 16px;font-size:13px">'
            '📆 Monate</button>'
            '<button onclick="zeigChart(\'status\')" '
            'class="bt b2" style="padding:8px 16px;font-size:13px">'
            '🎯 Status</button>'
            '</div>'
            '<div class="ch">'
            '<canvas id="myChart"></canvas>'
            '</div>'
            f'<p style="text-align:center;color:var(--t3);'
            f'margin-top:10px">Gesamt: '
            f'<strong style="color:var(--cy)">'
            f'{cd["gesamt"]} Bewerbungen</strong></p>'
            '</div>'
            f'<script>'
            f'var wD={wochen_json};'
            f'var mD={monate_json};'
            f'var sD={status_json};'
            f'var myChart=null;'
            f'function zeigChart(typ){{'
            f'if(myChart)myChart.destroy();'
            f'var ctx=document.getElementById("myChart").getContext("2d");'
            f'var d=typ==="wochen"?wD:typ==="monate"?mD:sD;'
            f'var isD=typ==="status";'
            f'myChart=new Chart(ctx,{{'
            f'type:isD?"doughnut":"bar",'
            f'data:{{labels:d.labels,datasets:[{{label:"Bewerbungen",'
            f'data:d.daten,'
            f'backgroundColor:isD?["rgba(0,217,255,0.7)",'
            f'"rgba(16,244,177,0.7)","rgba(255,71,87,0.7)",'
            f'"rgba(255,217,61,0.7)","rgba(139,92,246,0.7)"]:'
            f'"rgba(0,217,255,0.5)",'
            f'borderColor:isD?["#00D9FF","#10F4B1","#FF4757",'
            f'"#FFD93D","#8B5CF6"]:"#00D9FF",'
            f'borderWidth:2,borderRadius:isD?0:8}}]}},'
            f'options:{{responsive:true,maintainAspectRatio:false,'
            f'plugins:{{legend:{{labels:{{color:"#A0AEC0"}}}}}},'
            f'scales:isD?{{}}:{{x:{{ticks:{{color:"#A0AEC0"}},'
            f'grid:{{color:"rgba(255,255,255,0.05)"}}}},'
            f'y:{{ticks:{{color:"#A0AEC0"}},'
            f'grid:{{color:"rgba(255,255,255,0.05)"}},'
            f'beginAtZero:true}}}}}}}});'
            f'}}'
            f'document.addEventListener("DOMContentLoaded",'
            f'function(){{zeigChart("wochen");}});'
            f'</script>'
        )

        c = (
            f'<h1>👋 Hallo, {session.get("vorname", "")}!</h1>'
            '<div class="cd">'
            f'<h3>📊 Plan: {plan_label} {badge}</h3>'
            f'<p>Bewerbungen: <strong>{bw} / {limit_label}</strong></p>'
            + upgrade +
            '</div>'
            + charts_html +
            '<h2 style="margin-top:40px">⚡ Schnellaktionen</h2>'
            '<div class="gr">'
            '<a href="/aaliyah" style="text-decoration:none">'
            '<div class="sc"><div class="si">🤖</div>'
            '<div class="sv">Aaliyah</div>'
            '<div class="sl">KI Chat</div></div></a>'
            '<a href="/avinu" style="text-decoration:none">'
            '<div class="sc"><div class="si">⚡</div>'
            '<div class="sv">AVINU</div>'
            '<div class="sl">Global Jobs</div></div></a>'
            '<a href="/xsi" style="text-decoration:none">'
            '<div class="sc"><div class="si">🤖</div>'
            '<div class="sv">XSI</div>'
            '<div class="sl">Auto-Bewerber</div></div></a>'
            '<a href="/lebenslauf" style="text-decoration:none">'
            '<div class="sc"><div class="si">📝</div>'
            '<div class="sv">Lebenslauf</div>'
            '<div class="sl">Bearbeiten</div></div></a>'
            '<a href="/statistik" style="text-decoration:none">'
            '<div class="sc"><div class="si">📈</div>'
            '<div class="sv">Statistik</div>'
            '<div class="sl">Erfolge</div></div></a>'
            '</div>'
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
            ("vorname",      "text",  "Vorname"),
            ("nachname",     "text",  "Nachname"),
            ("strasse",      "text",  "Strasse"),
            ("plz",          "text",  "PLZ"),
            ("stadt",        "text",  "Stadt"),
            ("telefon",      "text",  "Telefon"),
            ("email",        "email", "E-Mail"),
            ("geburtsdatum", "text",  "Geburtsdatum"),
        ]

        if request.method == "POST":
            d = {k: request.form.get(k, "") for k, _, _ in FELDER}
            d["kenntnisse"] = request.form.get("kenntnisse", "")
            d["sprachen"]   = request.form.get("sprachen",   "")
            ps(uid, d)
            msg = '<div class="al ao">✅ Gespeichert!</div>'

        p = pl(uid)

        felder_html = "".join(
            f'<input type="{typ}" name="{key}" '
            f'placeholder="{label}" value="{p.get(key, "")}">'
            for key, typ, label in FELDER
        )

        c = (
            '<h1>📝 Lebenslauf</h1>'
            + msg +
            '<form method="POST">'
            '<div class="cd"><h3>👤 Persoenliche Daten</h3>'
            + felder_html +
            '</div>'
            '<div class="cd"><h3>💼 Kenntnisse</h3>'
            f'<textarea name="kenntnisse" rows="6">'
            f'{p.get("kenntnisse", "")}</textarea>'
            '</div>'
            '<div class="cd"><h3>🌍 Sprachen</h3>'
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
                        msg = (
                            '<div class="al ae">'
                            '❌ Upload fehlgeschlagen!</div>'
                        )
                else:
                    msg = (
                        '<div class="al ae">'
                        '❌ Ungueltiger Dateityp!</div>'
                    )

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
            uh = (
                '<p style="color:var(--t3);text-align:center;'
                'padding:20px">Keine Dateien hochgeladen</p>'
            )

        c = (
            '<h1>📂 Dateien & Uploads</h1>'
            + msg +
            '<div class="cd"><h3>📤 Neue Datei hochladen</h3>'
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
            '<div class="cd"><h3>📁 Meine Dateien</h3>'
            + uh +
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # DOWNLOAD / DELETE
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
                row[0], as_attachment=True, download_name=row[1]
            )
        return "<h3>❌ Datei nicht gefunden</h3>", 404

    @app.route("/delete/<int:fid>")
    def delete_datei(fid):
        r = _login_required()
        if r: return r

        udel(fid, session["user_id"])
        return redirect("/uploads")

    # ════════════════════════════════════════════════════════════
    # F6: BEWERBUNGEN MIT TAGS
    # ════════════════════════════════════════════════════════════

    @app.route("/bewerbungen", methods=["GET", "POST"])
    def bewerbungen():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        if request.method == "POST":
            firma  = request.form.get("firma",  "").strip()
            email  = request.form.get("email",  "").strip()
            typ    = request.form.get("typ",    "job")
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

        cn, cc = _db_connect()
        cc.execute(
            "SELECT id, firma, email, status, datum, typ "
            "FROM bewerbungen WHERE user_id=? "
            "ORDER BY id DESC",
            (uid,)
        )
        bws    = cc.fetchall()
        cn.close()

        anzahl          = bz(uid)
        _, limit_label, _, _ = _plan_info()

        # Tag-Filter
        tag_filter = request.args.get("tag", "")
        user_tags  = alle_tags_user(uid)

        tag_filter_html = (
            '<div style="margin:15px 0;display:flex;'
            'flex-wrap:wrap;gap:8px;align-items:center">'
            '<span style="color:var(--t3);font-size:13px">'
            'Filter:</span>'
            '<a href="/bewerbungen" '
            'class="tg tg-cy" style="text-decoration:none">Alle</a>'
        )
        for ut, uf2 in user_tags:
            tag_filter_html += (
                f'<a href="/bewerbungen?tag={ut}" '
                f'class="tg tg-{uf2}" '
                f'style="text-decoration:none">{ut}</a>'
            )
        tag_filter_html += '</div>'

        # Bewerbungen HTML
        bh = ""
        for b in bws:
            bid        = b[0]
            tags       = tags_laden(uid, bid)

            if tag_filter:
                tag_namen = [t[1] for t in tags]
                if tag_filter not in tag_namen:
                    continue

            tag_badges = _tag_html(tags)
            std_tags   = _standard_tags_html(bid)

            status_farbe = {
                "gesendet":  "cy",
                "offen":     "t2",
                "interview": "gn",
                "absage":    "rd",
                "zusage":    "gn",
            }.get(b[3] or "offen", "t2")

            bh += (
                '<div class="cd" style="margin:10px 0">'
                '<div style="display:flex;'
                'justify-content:space-between;'
                'flex-wrap:wrap;gap:10px">'
                '<div style="flex:1">'
                f'<h3 style="margin-bottom:5px">🏢 {b[1]}</h3>'
                f'<p style="font-size:13px;color:var(--t2)">'
                f'📧 {b[2]} · 📋 {b[5] or "job"} · '
                f'📅 {str(b[4])[:10]}</p>'
                f'<span class="tg tg-{status_farbe}">'
                f'{b[3] or "offen"}</span>'
                + (
                    f'<div style="margin-top:8px">{tag_badges}</div>'
                    if tag_badges else ""
                )
                + '<details style="margin-top:8px">'
                '<summary style="color:var(--cy);cursor:pointer;'
                'font-size:13px">🏷️ Tag hinzufuegen</summary>'
                '<div style="margin-top:8px;padding:10px;'
                'background:rgba(0,0,0,0.2);border-radius:8px">'
                + std_tags +
                f'<form method="GET" action="/tag/add/{bid}" '
                f'style="display:flex;gap:8px;margin-top:8px">'
                f'<input type="hidden" name="back" '
                f'value="/bewerbungen">'
                f'<input type="text" name="tag" '
                f'placeholder="Eigener Tag..." '
                f'style="margin:0;padding:8px 12px;font-size:13px">'
                f'<select name="farbe" '
                f'style="margin:0;padding:8px;'
                f'font-size:13px;width:auto">'
                f'<option value="cy">🔵 Blau</option>'
                f'<option value="gn">🟢 Gruen</option>'
                f'<option value="yl">🟡 Gelb</option>'
                f'<option value="rd">🔴 Rot</option>'
                f'<option value="pu">🟣 Lila</option>'
                f'</select>'
                f'<button type="submit" class="bt b1" '
                f'style="padding:8px 14px;font-size:13px">+</button>'
                f'</form>'
                '</div></details>'
                '</div></div></div>'
            )

        if not bh:
            bh = (
                '<p style="text-align:center;color:var(--t3);'
                'padding:20px">Keine Bewerbungen gefunden</p>'
            )

        c = (
            '<h1>📧 Bewerbungen</h1>'
            '<div class="cd">'
            f'<h3>📊 {anzahl} / {limit_label} Bewerbungen</h3>'
            '</div>'
            + msg
            + tag_filter_html +
            '<div class="cd"><h3>➕ Neue Bewerbung</h3>'
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
            '<h2>📋 Meine Bewerbungen</h2>'
            + bh
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # F10: ERFOLGS-STATISTIK
    # ════════════════════════════════════════════════════════════

    @app.route("/statistik")
    def statistik():
        r = _login_required()
        if r: return r

        uid  = session["user_id"]
        stat = erfolgs_statistik(uid)

        monat_labels = [m[0] for m in stat["pro_monat"]]
        monat_daten  = [m[1] for m in stat["pro_monat"]]
        typ_labels   = [t[0] or "sonstige" for t in stat["pro_typ"]]
        typ_daten    = [t[1] for t in stat["pro_typ"]]

        monat_json = json.dumps({
            "labels": monat_labels, "daten": monat_daten
        })
        typ_json = json.dumps({
            "labels": typ_labels, "daten": typ_daten
        })

        avg_antwort   = 25.0
        avg_erfolg    = 5.0
        avg_interview = 15.0

        def bewertung(wert, avg):
            if wert >= avg * 1.5:   return "🟢 Sehr gut"
            elif wert >= avg:        return "🟡 Gut"
            elif wert >= avg * 0.5:  return "🟠 Ausbaufaehig"
            else:                    return "🔴 Verbesserungsbedarf"

        c = (
            '<h1>📈 Erfolgs-Statistik</h1>'
            '<p>Analysiere deine Bewerbungserfolge!</p>'

            '<div class="gr" style="margin:30px 0">'
            '<div class="sc"><div class="si">📧</div>'
            f'<div class="sv">{stat["gesamt"]}</div>'
            '<div class="sl">Bewerbungen</div></div>'

            '<div class="sc"><div class="si">💬</div>'
            f'<div class="sv">{stat["antwortrate"]}%</div>'
            '<div class="sl">Antwortrate</div></div>'

            '<div class="sc"><div class="si">🎯</div>'
            f'<div class="sv">{stat["interview_rate"]}%</div>'
            '<div class="sl">Interview-Rate</div></div>'

            '<div class="sc"><div class="si">✅</div>'
            f'<div class="sv">{stat["erfolgsrate"]}%</div>'
            '<div class="sl">Erfolgsrate</div></div>'
            '</div>'

            '<div class="gr">'
            '<div class="cd"><h3>📊 Deine Zahlen</h3>'
            f'<p>📧 Gesamt: <strong>{stat["gesamt"]}</strong></p>'
            f'<p>💬 Mit Antwort: <strong>{stat["mit_antwort"]}</strong></p>'
            f'<p>🎯 Interviews: <strong>{stat["interviews"]}</strong></p>'
            f'<p>✅ Zusagen: <strong style="color:var(--gn)">'
            f'{stat["zusagen"]}</strong></p>'
            f'<p>❌ Absagen: <strong style="color:var(--rd)">'
            f'{stat["absagen"]}</strong></p>'
            '</div>'

            '<div class="cd"><h3>📈 Vergleich</h3>'
            f'<p>Antwortrate: <strong>{stat["antwortrate"]}%</strong> '
            f'(Ø {avg_antwort}%) '
            f'{bewertung(stat["antwortrate"], avg_antwort)}</p>'
            f'<p>Interview-Rate: <strong>{stat["interview_rate"]}%</strong> '
            f'(Ø {avg_interview}%) '
            f'{bewertung(stat["interview_rate"], avg_interview)}</p>'
            f'<p>Erfolgsrate: <strong>{stat["erfolgsrate"]}%</strong> '
            f'(Ø {avg_erfolg}%) '
            f'{bewertung(stat["erfolgsrate"], avg_erfolg)}</p>'
            '<div class="al ai" style="margin-top:15px">'
            '💡 Branchen-Durchschnitt laut Studien 2024</div>'
            '</div>'
            '</div>'

            '<div class="cd"><h3>📅 Bewerbungen pro Monat</h3>'
            '<div class="ch"><canvas id="monatChart"></canvas></div>'
            '</div>'

            '<div class="cd"><h3>📋 Nach Typ</h3>'
            '<div class="ch"><canvas id="typChart"></canvas></div>'
            '</div>'

            '<div class="cd"><h3>💡 Persoenliche Tipps</h3>'
            + (
                '<div class="al ao">✅ Super Antwortrate!</div>'
                if stat["antwortrate"] >= avg_antwort else
                '<div class="al aw">⚠️ Antwortrate niedrig: '
                'Bewerbungen individueller gestalten!</div>'
            )
            + (
                '<div class="al ao">✅ Tolle Interview-Rate!</div>'
                if stat["interview_rate"] >= avg_interview else
                '<div class="al ai">💡 Mehr Interviews? '
                '<a href="/aaliyah">Aaliyah fragen!</a></div>'
            )
            + '</div>'

            f'<script>'
            f'var mD={monat_json};var tD={typ_json};'
            f'new Chart(document.getElementById("monatChart"),{{'
            f'type:"bar",data:{{labels:mD.labels,'
            f'datasets:[{{label:"Bewerbungen",data:mD.daten,'
            f'backgroundColor:"rgba(0,217,255,0.5)",'
            f'borderColor:"#00D9FF",borderWidth:2,borderRadius:8}}]}},'
            f'options:{{responsive:true,maintainAspectRatio:false,'
            f'plugins:{{legend:{{labels:{{color:"#A0AEC0"}}}}}},'
            f'scales:{{x:{{ticks:{{color:"#A0AEC0"}},'
            f'grid:{{color:"rgba(255,255,255,0.05)"}}}},'
            f'y:{{ticks:{{color:"#A0AEC0"}},'
            f'grid:{{color:"rgba(255,255,255,0.05)"}},'
            f'beginAtZero:true}}}}}}}});'
            f'new Chart(document.getElementById("typChart"),{{'
            f'type:"doughnut",data:{{labels:tD.labels,'
            f'datasets:[{{data:tD.daten,'
            f'backgroundColor:["rgba(0,217,255,0.7)",'
            f'"rgba(16,244,177,0.7)","rgba(255,217,61,0.7)",'
            f'"rgba(139,92,246,0.7)","rgba(255,71,87,0.7)"],'
            f'borderWidth:2}}]}},'
            f'options:{{responsive:true,maintainAspectRatio:false,'
            f'plugins:{{legend:{{labels:{{color:"#A0AEC0"}}}}}}}}}})'
            f'</script>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # F9: TEILEN
    # ════════════════════════════════════════════════════════════

    @app.route("/teilen")
    def teilen():
        r = _login_required()
        if r: return r

        url   = "https://xsikom.de"
        text  = "Ich nutze XsiKOM – den KI-Bewerbungsassistenten!"
        links = teilen_links(url, text)

        c = (
            '<h1>🔗 XsiKOM teilen</h1>'
            '<p>Teile XsiKOM mit Freunden und Familie!</p>'

            '<div class="cd"><h3>📱 App teilen</h3>'
            '<div class="gr">'
            f'<a href="{links["whatsapp"]}" target="_blank" '
            f'class="bt b2">💬 WhatsApp</a>'
            f'<a href="{links["telegram"]}" target="_blank" '
            f'class="bt b1">✈️ Telegram</a>'
            f'<a href="{links["twitter"]}" target="_blank" '
            f'class="bt b5">🐦 Twitter/X</a>'
            f'<a href="{links["linkedin"]}" target="_blank" '
            f'class="bt b1">💼 LinkedIn</a>'
            f'<a href="{links["email"]}" '
            f'class="bt b3">📧 E-Mail</a>'
            '</div>'
            '<div style="margin-top:20px">'
            '<p>🔗 Direkt-Link:</p>'
            '<div style="display:flex;gap:10px">'
            f'<input type="text" id="share-link" '
            f'value="{url}" readonly style="flex:1;margin:0">'
            '<button onclick="copyLink()" class="bt b2">'
            '📋 Kopieren</button>'
            '</div></div></div>'

            '<div class="cd"><h3>📷 QR-Code</h3>'
            '<div style="text-align:center;padding:20px;'
            'background:white;border-radius:12px;'
            'display:inline-block">'
            f'<img src="https://api.qrserver.com/v1/create-qr-code/'
            f'?size=200x200&data={url}" '
            f'alt="QR-Code" style="display:block">'
            '</div>'
            '<p style="margin-top:15px;color:var(--t3);font-size:13px">'
            'QR-Code scannen und XsiKOM direkt oeffnen!</p>'
            '</div>'

            '<div class="cd"><h3>💼 Job teilen</h3>'
            '<p>Teile einen interessanten Job:</p>'
            '<input type="text" id="job-url" '
            'placeholder="Job-URL eingeben...">'
            '<input type="text" id="job-text" '
            'placeholder="Kurze Beschreibung...">'
            '<button type="button" onclick="jobTeilen()" '
            'class="bt b1" style="width:100%">'
            '🔗 Job-Links erstellen</button>'
            '<div id="job-links" style="margin-top:15px"></div>'
            '</div>'

            '<div class="cd"><h3>👤 Profil teilen</h3>'
            '<div class="al ai">'
            '💡 Teile dein Profil mit Arbeitgebern!'
            '</div>'
            '<a href="/teilen/profil" class="bt b2">'
            '👤 Profil-Link erstellen</a>'
            '</div>'

            '<script>'
            'function copyLink(){'
            'var inp=document.getElementById("share-link");'
            'inp.select();'
            'navigator.clipboard.writeText(inp.value);'
            'alert("Link kopiert!");}'
            'function jobTeilen(){'
            'var url=document.getElementById("job-url").value;'
            'var text=document.getElementById("job-text").value;'
            'if(!url){alert("URL eingeben!");return;}'
            'var enc=encodeURIComponent;'
            'var html="<div class=\'gr\'>"'
            '+"<a href=\'https://wa.me/?text="'
            '+enc(text)+"%20"+enc(url)'
            '+"\' target=\'_blank\' class=\'bt b2\'>💬 WhatsApp</a>"'
            '+"<a href=\'https://t.me/share/url?url="'
            '+enc(url)+"&text="+enc(text)'
            '+"\' target=\'_blank\' class=\'bt b1\'>✈️ Telegram</a>"'
            '+"<a href=\'https://twitter.com/intent/tweet?text="'
            '+enc(text)+"&url="+enc(url)'
            '+"\' target=\'_blank\' class=\'bt b5\'>🐦 Twitter</a>"'
            '+"</div>";'
            'document.getElementById("job-links").innerHTML=html;}'
            '</script>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/teilen/profil")
    def teilen_profil():
        r = _login_required()
        if r: return r

        uid   = session["user_id"]
        p     = pl(uid)
        url   = f"https://xsikom.de/profil/public/{uid}"
        text  = (
            f"Schau dir mein Bewerbungsprofil an: "
            f"{p.get('vorname','')} {p.get('nachname','')}"
        )
        links = teilen_links(url, text)

        c = (
            '<h1>👤 Profil teilen</h1>'
            '<div class="cd"><h3>🔗 Dein Profil-Link</h3>'
            '<div style="display:flex;gap:10px;margin-bottom:20px">'
            f'<input type="text" value="{url}" '
            f'readonly style="flex:1;margin:0">'
            '<button onclick="navigator.clipboard.writeText(\''
            + url +
            '\');alert(\'Kopiert!\')" class="bt b2">📋</button>'
            '</div>'
            '<div class="gr">'
            f'<a href="{links["whatsapp"]}" target="_blank" '
            f'class="bt b2">💬 WhatsApp</a>'
            f'<a href="{links["telegram"]}" target="_blank" '
            f'class="bt b1">✈️ Telegram</a>'
            f'<a href="{links["linkedin"]}" target="_blank" '
            f'class="bt b1">💼 LinkedIn</a>'
            f'<a href="{links["email"]}" '
            f'class="bt b3">📧 E-Mail</a>'
            '</div></div>'
            '<a href="/teilen" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)