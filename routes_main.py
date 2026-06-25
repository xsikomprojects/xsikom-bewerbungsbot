"""
Main Routes: Dashboard, Lebenslauf, Uploads, Bewerbungen
F1: Charts, F6: Tags, F3: Dark/Light Mode
"""
from flask import render_template_string, request, redirect, session, send_file, jsonify
from shared import (
    H, DB, UF, AE, tipp, bz, pl, ps, af, ds, ul, udel,
    chart_daten_laden, tags_laden, tag_hinzufuegen,
    tag_loeschen, alle_tags_user, STANDARD_TAGS,
    get_theme, set_theme,
)
import sqlite3
import os
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
    badge       = '<span class="bg">⭐ PREMIUM</span>' if premium else ""
    upgrade     = (
        '<a href="/premium" class="bt b3">💎 Upgrade</a>'
        if not premium else ""
    )
    return plan_label, limit_label, badge, upgrade


def _tag_html(tags):
    """Gibt Tags als HTML-Badges zurück."""
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
    """Gibt Standard-Tag-Buttons zurück."""
    return "".join(
        f'<a href="/tag/add/{bewerbung_id}?tag={t}&farbe={f}" '
        f'class="tg tg-{f}" style="text-decoration:none;cursor:pointer">'
        f'{t}</a>'
        for t, f in STANDARD_TAGS
    )


# ─────────────────────────────────────────────────────────────────
# ROUTE-REGISTRIERUNG
# ─────────────────────────────────────────────────────────────────

def register_main_routes(app):

    # ════════════════════════════════════════════════════════════
    # F3: THEME ROUTE
    # ════════════════════════════════════════════════════════════

    @app.route("/theme/<theme>")
    def theme_setzen(theme):
        if "user_id" in session:
            set_theme(session["user_id"], theme)
            session["theme"] = theme
        return "", 204  # Kein Content zurück

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

        # ── F1: Chart-Daten ──────────────────────────────────────
        cd = chart_daten_laden(uid)

        # Chart.js Daten als JSON
        import json
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

        # ── Charts HTML ──────────────────────────────────────────
        charts_html = (
            '<div class="cd">'
            '<h3>📊 Bewerbungs-Statistik</h3>'

            # Tabs
            '<div style="display:flex;gap:10px;margin-bottom:20px;'
            'flex-wrap:wrap">'
            '<button onclick="zeigChart(\'wochen\')" '
            'class="bt b1" style="padding:8px 16px;font-size:13px" '
            'id="btn-wochen">📅 Wochen</button>'
            '<button onclick="zeigChart(\'monate\')" '
            'class="bt b5" style="padding:8px 16px;font-size:13px" '
            'id="btn-monate">📆 Monate</button>'
            '<button onclick="zeigChart(\'status\')" '
            'class="bt b2" style="padding:8px 16px;font-size:13px" '
            'id="btn-status">🎯 Status</button>'
            '</div>'

            # Chart Canvas
            '<div class="ch">'
            '<canvas id="myChart"></canvas>'
            '</div>'

            # Gesamt
            f'<p style="text-align:center;color:var(--t3);margin-top:10px">'
            f'Gesamt: <strong style="color:var(--cy)">'
            f'{cd["gesamt"]} Bewerbungen</strong></p>'
            '</div>'

            # Chart.js Script
            f'<script>'
            f'var wochenDaten={wochen_json};'
            f'var monateDaten={monate_json};'
            f'var statusDaten={status_json};'
            f'var myChart=null;'
            f'function zeigChart(typ){{'
            f'  if(myChart)myChart.destroy();'
            f'  var ctx=document.getElementById("myChart").getContext("2d");'
            f'  var d=typ==="wochen"?wochenDaten:typ==="monate"?monateDaten:statusDaten;'
            f'  var isDonut=typ==="status";'
            f'  myChart=new Chart(ctx,{{'
            f'    type:isDonut?"doughnut":"bar",'
            f'    data:{{'
            f'      labels:d.labels,'
            f'      datasets:[{{'
            f'        label:"Bewerbungen",'
            f'        data:d.daten,'
            f'        backgroundColor:isDonut?'
            f'          ["rgba(0,217,255,0.7)","rgba(16,244,177,0.7)",'
            f'           "rgba(255,71,87,0.7)","rgba(255,217,61,0.7)",'
            f'           "rgba(139,92,246,0.7)"]:'
            f'          "rgba(0,217,255,0.5)",'
            f'        borderColor:isDonut?'
            f'          ["#00D9FF","#10F4B1","#FF4757","#FFD93D","#8B5CF6"]:'
            f'          "#00D9FF",'
            f'        borderWidth:2,'
            f'        borderRadius:isDonut?0:8'
            f'      }}]'
            f'    }},'
            f'    options:{{'
            f'      responsive:true,'
            f'      maintainAspectRatio:false,'
            f'      plugins:{{'
            f'        legend:{{labels:{{color:"#A0AEC0"}}}},'
            f'      }},'
            f'      scales:isDonut?{{}}:{{'
            f'        x:{{ticks:{{color:"#A0AEC0"}},grid:{{color:"rgba(255,255,255,0.05)"}}}},'
            f'        y:{{ticks:{{color:"#A0AEC0"}},grid:{{color:"rgba(255,255,255,0.05)"}}'
            f'          ,beginAtZero:true}}'
            f'      }}'
            f'    }}'
            f'  }});'
            f'}}'
            f'document.addEventListener("DOMContentLoaded",function(){{'
            f'  zeigChart("wochen");'
            f'}});'
            f'</script>'
        )

        c = (
            f'<h1>👋 Hallo, {session.get("vorname", "")}!</h1>'

            '<div class="cd">'
            f'<h3>📊 Plan: {plan_label} {badge}</h3>'
            f'<p>Bewerbungen: <strong>{bw} / {limit_label}</strong></p>'
            + upgrade +
            '</div>'

            # F1: Charts
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

            '<a href="/pdf-lebenslauf" style="text-decoration:none">'
            '<div class="sc"><div class="si">📄</div>'
            '<div class="sv">PDF</div>'
            '<div class="sl">Generator</div></div></a>'
            '</div>'

            '<div class="cd" style="margin-top:30px">'
            f'<h3>💡 Tipp</h3><p>{tipp()}</p>'
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # F6: TAG ROUTES
    # ════════════════════════════════════════════════════════════

    @app.route("/tag/add/<int:bid>")
    def tag_add(bid):
        r = _login_required()
        if r: return r

        tag   = request.args.get("tag",   "").strip()[:30]
        farbe = request.args.get("farbe", "cy")
        zurueck = request.args.get("back", "/bewerbungen")

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
            '<div class="cd"><h3>👤 Persönliche Daten</h3>'
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
                        msg = '<div class="al ae">❌ Upload fehlgeschlagen!</div>'
                else:
                    msg = '<div class="al ae">❌ Ungültiger Dateityp!</div>'

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
                '<p style="color:var(--t3);text-align:center;padding:20px">'
                'Keine Dateien hochgeladen</p>'
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

        # ── Bewerbungen laden ────────────────────────────────────
        cn, cc = _db_connect()
        cc.execute(
            "SELECT id, firma, email, status, datum, typ "
            "FROM bewerbungen WHERE user_id=? "
            "ORDER BY id DESC",
            (uid,)
        )
        bws = cc.fetchall()
        cn.close()

        anzahl          = bz(uid)
        _, limit_label, _, _ = _plan_info()

        # ── Tag-Filter ───────────────────────────────────────────
        tag_filter = request.args.get("tag", "")
        user_tags  = alle_tags_user(uid)

        tag_filter_html = (
            '<div style="margin:15px 0;display:flex;'
            'flex-wrap:wrap;gap:8px;align-items:center">'
            '<span style="color:var(--t3);font-size:13px">Filter:</span>'
            '<a href="/bewerbungen" '
            'class="tg tg-cy" style="text-decoration:none">Alle</a>'
        )
        for ut, uf in user_tags:
            tag_filter_html += (
                f'<a href="/bewerbungen?tag={ut}" '
                f'class="tg tg-{uf}" style="text-decoration:none">'
                f'{ut}</a>'
            )
        tag_filter_html += '</div>'

        # ── Bewerbungen HTML ─────────────────────────────────────
        bh = ""
        for b in bws:
            bid     = b[0]
            tags    = tags_laden(uid, bid)

            # Tag-Filter anwenden
            if tag_filter:
                tag_namen = [t[1] for t in tags]
                if tag_filter not in tag_namen:
                    continue

            tag_badges = _tag_html(tags)
            std_tags   = _standard_tags_html(bid)

            status_farbe = {
                "gesendet": "cy", "offen": "t2",
                "interview": "gn", "absage": "rd",
            }.get(b[3] or "offen", "t2")

            bh += (
                '<div class="cd" style="margin:10px 0">'
                '<div style="display:flex;justify-content:space-between;'
                'flex-wrap:wrap;gap:10px">'
                '<div style="flex:1">'
                f'<h3 style="margin-bottom:5px">🏢 {b[1]}</h3>'
                f'<p style="font-size:13px;color:var(--t2)">'
                f'📧 {b[2]} · 📋 {b[5] or "job"} · '
                f'📅 {str(b[4])[:10]}</p>'
                f'<span class="tg tg-{status_farbe}">'
                f'{b[3] or "offen"}</span>'
                # Tags anzeigen
                + (f'<div style="margin-top:8px">{tag_badges}</div>'
                   if tag_badges else "") +
                # Standard-Tags hinzufügen
                '<details style="margin-top:8px">'
                '<summary style="color:var(--cy);cursor:pointer;'
                'font-size:13px">🏷️ Tag hinzufügen</summary>'
                '<div style="margin-top:8px;padding:10px;'
                'background:rgba(0,0,0,0.2);border-radius:8px">'
                + std_tags +
                # Eigener Tag
                f'<form method="GET" action="/tag/add/{bid}" '
                f'style="display:flex;gap:8px;margin-top:8px">'
                f'<input type="hidden" name="back" value="/bewerbungen">'
                f'<input type="text" name="tag" '
                f'placeholder="Eigener Tag..." '
                f'style="margin:0;padding:8px 12px;font-size:13px">'
                f'<select name="farbe" '
                f'style="margin:0;padding:8px;font-size:13px;width:auto">'
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
                '<p style="text-align:center;color:var(--t3);padding:20px">'
                'Keine Bewerbungen gefunden</p>'
            )

            c = (
                                         '<h1>📧 Bewerbungen</h1>'

                                         '<div class="cd">'
                                          f'<h3>📊 {anzahl} / {limit_label} Bewerbungen</h3>'
                                         '</div>'

                                        + msg
                                        + tag_filter_html +

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

            '<h2>📋 Meine Bewerbungen</h2>'
            + bh
        )
        return render_template_string(H, content=c, user=session)