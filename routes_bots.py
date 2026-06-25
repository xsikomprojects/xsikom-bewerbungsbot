"""Bot Routes: Aaliyah KI, AVINU Job-Suche, XSI Auto-Bewerber"""
from flask import render_template_string, request, redirect, session
from webapp import H, DB, ki, pl
from avinu_ki import (
    alle_jobs_suchen, get_alle_berufe, jobs_speichern, jobs_laden,
    vorlagen_laden, anschreiben_generieren, auto_bewerbung_erstellen,
    job_favorit_toggle, job_loeschen, BRANCHEN
)
from xsi_bot import (
    xsi_anschreiben_komplett, xsi_betreff_erstellen,
    xsi_email_senden, xsi_bewerbung_speichern,
    xsi_bewerbung_status_update, xsi_bewerbungen_laden,
    xsi_templates_laden, xsi_statistiken, xsi_unterlagen_pruefen
)
import sqlite3


def register_bot_routes(app):

    # ============================================================
    # AALIYAH KI
    # ============================================================
    @app.route("/aaliyah", methods=["GET", "POST"])
    def aaliyah_route():
        if "user_id" not in session:
            return redirect("/login")
        antwort = ""
        if request.method == "POST":
            frage = request.form.get("frage", "")
            if frage:
                a = ki(frage).replace("\n", "<br>")
                antwort = (
                    '<div class="al ai" style="flex-direction:column;align-items:start">'
                    '<strong>🤖 Aaliyah:</strong>'
                    '<div style="margin-top:10px">' + a + '</div></div>'
                )
        c = (
            '<h1>🤖 Aaliyah KI</h1>'
            '<div class="cd">'
            '<form method="POST">'
            '<input type="text" name="frage" placeholder="Frag Aaliyah..." required>'
            '<button type="submit" class="bt b5" style="width:100%">📤 Senden</button>'
            '</form>'
            + antwort +
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ============================================================
    # AVINU JOB-SUCHE
    # ============================================================
    @app.route("/avinu", methods=["GET", "POST"])
    def avinu_dashboard():
        if "user_id" not in session:
            return redirect("/login")

        msg = ""
        if request.method == "POST":
            branche = request.form.get("branche", "")
            suchbegriff = request.form.get("suchbegriff", "")
            standort = request.form.get("standort", "")
            radius = int(request.form.get("radius", 25))
            international = request.form.get("international") == "yes"

            if not suchbegriff and branche:
                suchbegriff = BRANCHEN.get(branche, ["Job"])[0]

            if suchbegriff and standort:
                try:
                    alle = alle_jobs_suchen(suchbegriff, standort, radius, international)
                    if alle:
                        n = jobs_speichern(session["user_id"], alle, branche, radius)
                        intl = " 🌍" if international else " 🇩🇪"
                        msg = '<div class="al ao">✅ ' + str(n) + ' neue Jobs' + intl + '!</div>'
                    else:
                        msg = '<div class="al aw">⚠️ Keine Jobs gefunden!</div>'
                except Exception as e:
                    msg = '<div class="al ae">❌ ' + str(e)[:100] + '</div>'

        ft = request.args.get("filter", "offen")
        jobs = jobs_laden(session["user_id"], ft)

        # Berufe Autocomplete
        bo = ""
        for beruf in get_alle_berufe():
            bo += '<option value="' + beruf + '">'

        # Branchen Dropdown
        namen = {
            "it": "💻 IT", "handwerk": "🔧 Handwerk",
            "gesundheit": "🏥 Gesundheit", "verwaltung": "📋 Verwaltung",
            "verkauf": "🛒 Verkauf", "logistik": "📦 Logistik",
            "gastronomie": "🍽️ Gastronomie", "bildung": "📚 Bildung",
            "marketing": "📱 Marketing", "finanzen": "💰 Finanzen",
            "transport": "🚚 Transport", "produktion": "🏭 Produktion",
            "reinigung": "🧹 Reinigung", "sicherheit": "🛡️ Sicherheit"
        }
        bh = ""
        for k, v in namen.items():
            bh += '<option value="' + k + '">' + v + '</option>'

        # Jobs HTML
        jh = ""
        for j in jobs[:30]:
            bb = ''
            if j[11]:
                bb = '<span style="background:var(--gn);color:white;padding:4px 10px;border-radius:12px;font-size:11px">✅</span>'
            fav = j[13] if len(j) > 13 else 0
            land = j[15] if len(j) > 15 else "DE"
            flags = {
                "DE": "🇩🇪", "US": "🇺🇸", "UK": "🇬🇧", "FR": "🇫🇷",
                "EU": "🇪🇺", "WORLD": "🌍", "INT": "🌍"
            }
            fg = flags.get(land, "🌍")
            url_link = ''
            if j[6]:
                url_link = '<a href="' + j[6] + '" target="_blank">🔗</a>'
            beschr = ""
            if j[5] and len(j[5]) > 200:
                beschr = j[5][:200] + "..."
            elif j[5]:
                beschr = j[5]

            jh += (
                '<div class="cd">'
                '<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:15px">'
                '<div style="flex:1;min-width:280px">'
                '<h3>' + fg + ' ' + str(j[3]) + ' ' + bb + '</h3>'
                '<p style="color:var(--cy);font-size:16px">🏢 <strong>' + str(j[2]) + '</strong></p>'
                '<p style="color:var(--t2);font-size:13px">📍 ' + str(j[4]) + ' · 🔗 ' + str(j[9]) + ' · 🏷️ ' + str(j[8]) + '</p>'
            )
            if beschr:
                jh += '<p style="color:var(--t3);font-size:13px">' + beschr + '</p>'
            jh += '<p>' + url_link + '</p></div>'
            jh += (
                '<div style="display:flex;flex-direction:column;gap:8px">'
                '<a href="/xsi/schnell/' + str(j[0]) + '" class="bt b2">🤖 XSI</a>'
                '<a href="/avinu/favorit/' + str(j[0]) + '" class="bt b3" style="padding:8px 14px">'
                + ("⭐" if fav else "☆") + '</a>'
                '<a href="/avinu/loeschen/' + str(j[0]) + '" class="bt b4" style="padding:8px 14px" '
                'onclick="return confirm(\'Loeschen?\')">🗑️</a>'
                '</div></div></div>'
            )

        if not jh:
            jh = '<p style="text-align:center;color:var(--t3);padding:40px">Keine Jobs!</p>'

        # Statistiken
        cn = sqlite3.connect(DB)
        cc = cn.cursor()
        cc.execute("SELECT COUNT(*) FROM jobs WHERE user_id=?", (session["user_id"],))
        total = cc.fetchone()[0]
        try:
            cc.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND beworben=1", (session["user_id"],))
            bc = cc.fetchone()[0]
            cc.execute("SELECT COUNT(*) FROM jobs WHERE user_id=? AND favorit=1", (session["user_id"],))
            fc = cc.fetchone()[0]
        except Exception:
            bc = fc = 0
        cn.close()

        c = (
            '<h1>⚡ AVINU - Global Jobs</h1>'
            '<p>10+ Portale · 300+ Berufe · 🌍</p>'
            + msg +
            '<div class="cd"><h3>🔍 Job-Suche</h3>'
            '<form method="POST">'
            '<p>📂 Branche:</p>'
            '<select name="branche"><option value="">--</option>' + bh + '</select>'
            '<p>💼 Beruf:</p>'
            '<input type="text" name="suchbegriff" placeholder="IT-Fachtechniker, Praktikum..." list="bl" required>'
            '<datalist id="bl">' + bo + '</datalist>'
            '<p>📍 Standort:</p>'
            '<input type="text" name="standort" placeholder="Berlin, Mainz..." required>'
            '<p>📏 Umkreis: <span id="rv">25</span> km</p>'
            '<input type="range" name="radius" min="5" max="200" value="25" step="5" '
            'oninput="document.getElementById(\'rv\').textContent=this.value" '
            'style="width:100%;margin-bottom:15px">'
            '<div style="margin:20px 0;padding:15px;background:rgba(0,217,255,0.1);border-radius:12px">'
            '<label style="display:flex;align-items:center;gap:10px;cursor:pointer">'
            '<input type="checkbox" name="international" value="yes" style="width:auto">'
            '<span>🌍 <strong>International</strong></span></label></div>'
            '<button type="submit" class="bt b1" style="width:100%">🚀 Jobs suchen</button>'
            '</form></div>'
            '<div class="gr" style="margin:30px 0">'
            '<a href="/avinu?filter=alle" style="text-decoration:none">'
            '<div class="sc"><div class="si">💼</div><div class="sv">' + str(total) + '</div><div class="sl">Alle</div></div></a>'
            '<a href="/avinu?filter=offen" style="text-decoration:none">'
            '<div class="sc"><div class="si">📋</div><div class="sv">' + str(total - bc) + '</div><div class="sl">Offen</div></div></a>'
            '<a href="/avinu?filter=beworben" style="text-decoration:none">'
            '<div class="sc"><div class="si">✅</div><div class="sv">' + str(bc) + '</div><div class="sl">Beworben</div></div></a>'
            '<a href="/avinu?filter=favoriten" style="text-decoration:none">'
            '<div class="sc"><div class="si">⭐</div><div class="sv">' + str(fc) + '</div><div class="sl">Favoriten</div></div></a>'
            '</div>'
            '<h2>🎯 Jobs (' + str(len(jobs)) + ')</h2>'
            + jh
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/avinu/favorit/<int:jid>")
    def avinu_favorit(jid):
        if "user_id" not in session:
            return redirect("/login")
        job_favorit_toggle(jid, session["user_id"])
        return redirect("/avinu")

    @app.route("/avinu/loeschen/<int:jid>")
    def avinu_loeschen(jid):
        if "user_id" not in session:
            return redirect("/login")
        job_loeschen(jid, session["user_id"])
        return redirect("/avinu")

    # ============================================================
    # XSI BOT
    # ============================================================
    @app.route("/xsi")
    def xsi_dashboard():
        if "user_id" not in session:
            return redirect("/login")
        st = xsi_statistiken(session["user_id"])
        ch = xsi_unterlagen_pruefen(session["user_id"])

        us = ""
        if not ch["komplett"]:
            ms = []
            if not ch["lebenslauf"]:
                ms.append("Lebenslauf")
            if not ch["zeugnis"]:
                ms.append("Zeugnis")
            if not ch["zertifikat"]:
                ms.append("Zertifikat")
            if not ch["bild"]:
                ms.append("Foto")
            us = '<div class="al aw">⚠️ Fehlend: ' + ", ".join(ms) + ' <a href="/uploads">Hochladen</a></div>'
        else:
            us = '<div class="al ao">✅ Alle Unterlagen da!</div>'

        bw = xsi_bewerbungen_laden(session["user_id"])
        bh = ""
        for b in bw[:10]:
            ic = {"erstellt": "📝", "gesendet": "✅", "antwort": "💬", "absage": "❌"}.get(b[9], "📋")
            bh += (
                '<div class="ui"><div>' + ic + ' <strong>' + str(b[4]) + '</strong> bei ' + str(b[3]) +
                '<br><small style="color:var(--t3)">An: ' + str(b[5] or "N/A") + ' · ' + str(b[9]) +
                '</small></div>'
                '<a href="/xsi/detail/' + str(b[0]) + '" class="bt b1" style="padding:8px 14px">👁️</a></div>'
            )
        if not bh:
            bh = '<p style="text-align:center;color:var(--t3)">Noch keine</p>'

        c = (
            '<h1>🤖 XSI Bot - Auto-Bewerber</h1>'
            '<p>Automatisch Bewerbungen erstellen & senden!</p>'
            + us +
            '<div class="gr" style="margin:30px 0">'
            '<a href="/xsi/neu" style="text-decoration:none">'
            '<div class="sc"><div class="si">✨</div><div class="sv">Neu</div><div class="sl">Bewerbung</div></div></a>'
            '<div class="sc"><div class="si">📧</div><div class="sv">' + str(st["gesendet"]) + '</div><div class="sl">Gesendet</div></div>'
            '<div class="sc"><div class="si">📝</div><div class="sv">' + str(st["erstellt"]) + '</div><div class="sl">Entwuerfe</div></div>'
            '<div class="sc"><div class="si">📂</div><div class="sv">' + str(st["unterlagen"]) + '</div><div class="sl">Unterlagen</div></div>'
            '</div>'
            '<h2>📧 Bewerbungen</h2>'
            '<div class="cd">' + bh + '</div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/xsi/neu", methods=["GET", "POST"])
    def xsi_neu():
        if "user_id" not in session:
            return redirect("/login")
        pr = pl(session["user_id"])
        msg = ""

        if request.method == "POST":
            fi = request.form.get("firma", "").strip()
            po = request.form.get("position", "").strip()
            em = request.form.get("empfaenger", "").strip()
            ti = request.form.get("template_id", "")
            sp = request.form.get("sprache", "de")
            ak = request.form.get("aktion", "erstellen")

            if fi and po and ti:
                cn = sqlite3.connect(DB)
                cc = cn.cursor()
                cc.execute("SELECT * FROM xsi_templates WHERE id=?", (int(ti),))
                t = cc.fetchone()
                cn.close()

                if t:
                    bt2 = xsi_betreff_erstellen(t[2], fi, po, pr)
                    an = xsi_anschreiben_komplett(t[3], fi, po, pr, sp)
                    bi = xsi_bewerbung_speichern(
                        session["user_id"], 0, fi, po, em, bt2, an, "erstellt", sp
                    )

                    if ak == "senden" and em:
                        ok, info = xsi_email_senden(em, bt2, an, session["user_id"], pr)
                        if ok:
                            xsi_bewerbung_status_update(bi, "gesendet")
                            msg = '<div class="al ao">✅ An ' + fi + ' gesendet! ' + info + '</div>'
                        else:
                            msg = '<div class="al ae">❌ ' + info + '</div>'
                    else:
                        msg = '<div class="al ao">✅ Entwurf gespeichert!</div>'

        tp = xsi_templates_laden(premium=session.get("premium", False))
        th = ""
        for t in tp:
            pb = '<span class="bg">💎</span>' if t[5] else ''
            th += (
                '<label style="display:block;margin:10px 0;padding:16px;'
                'background:rgba(10,14,26,0.5);border-radius:12px;cursor:pointer">'
                '<input type="radio" name="template_id" value="' + str(t[0]) + '" required>'
                ' <strong>' + t[1] + '</strong> ' + pb +
                '<br><small style="color:var(--t3)">Betreff: ' + t[2][:50] + '... | ' + t[4].upper() + '</small>'
                '</label>'
            )

        ch = xsi_unterlagen_pruefen(session["user_id"])
        uh = ""
        for kat, ok in [("📄 Lebenslauf", ch["lebenslauf"]), ("📜 Zeugnis", ch["zeugnis"]),
                         ("🏆 Zertifikat", ch["zertifikat"]), ("🖼️ Foto", ch["bild"])]:
            uh += '<span style="margin-right:15px">' + ("✅" if ok else "❌") + ' ' + kat + '</span>'

        upload_btn = ''
        if not ch["komplett"]:
            upload_btn = '<a href="/uploads" class="bt b3">📂 Hochladen</a>'

        c = (
            '<h1>✨ Neue Bewerbung mit XSI</h1>' + msg +
            '<div class="cd"><h3>📋 Unterlagen</h3>'
            '<div style="margin:10px 0">' + uh + '</div>'
            + upload_btn + '</div>'
            '<div class="cd"><h3>📧 Bewerbung</h3>'
            '<form method="POST">'
            '<p>📋 Art:</p><select name="typ">'
            '<option value="job">💼 Job</option>'
            '<option value="praktikum">🎓 Praktikum</option>'
            '<option value="ausbildung">📚 Ausbildung</option>'
            '<option value="initiativ">💡 Initiativ</option>'
            '<option value="werkstudent">🧑‍💻 Werkstudent</option>'
            '<option value="minijob">💶 Minijob</option></select>'
            '<p>🏢 Firma:</p>'
            '<input type="text" name="firma" placeholder="SAP, Telekom..." required>'
            '<p>💼 Position:</p>'
            '<input type="text" name="position" placeholder="IT-Fachtechniker, Praktikant..." required>'
            '<p>📧 E-Mail der Firma:</p>'
            '<input type="email" name="empfaenger" placeholder="bewerbung@firma.de">'
            '<p>🌍 Sprache:</p><select name="sprache">'
            '<option value="de">🇩🇪 Deutsch</option>'
            '<option value="en">🇬🇧 English</option>'
            '<option value="fr">🇫🇷 Francais</option></select>'
            '<p>📝 Vorlage:</p>' + th +
            '<div style="display:flex;gap:10px;margin-top:20px">'
            '<button type="submit" name="aktion" value="erstellen" class="bt b1" style="flex:1">📝 Entwurf</button>'
            '<button type="submit" name="aktion" value="senden" class="bt b2" style="flex:1">🚀 Senden!</button>'
            '</div></form></div>'
            '<div class="al ai">💡 XSI generiert KI-Anschreiben + haengt ALLE Unterlagen an!</div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/xsi/schnell/<int:jid>")
    def xsi_schnell(jid):
        if "user_id" not in session:
            return redirect("/login")
        cn = sqlite3.connect(DB)
        cc = cn.cursor()
        cc.execute("SELECT firma, position FROM jobs WHERE id=? AND user_id=?",
                    (jid, session["user_id"]))
        j = cc.fetchone()
        cn.close()
        if not j:
            return redirect("/avinu")
        return redirect("/xsi/neu?firma=" + str(j[0]) + "&position=" + str(j[1]))

    @app.route("/xsi/detail/<int:bid>")
    def xsi_detail(bid):
        if "user_id" not in session:
            return redirect("/login")
        cn = sqlite3.connect(DB)
        cc = cn.cursor()
        cc.execute("SELECT * FROM xsi_bewerbungen WHERE id=? AND user_id=?",
                    (bid, session["user_id"]))
        b = cc.fetchone()
        cn.close()
        if not b:
            return redirect("/xsi")
        si = {"erstellt": "📝 Entwurf", "gesendet": "✅ Gesendet",
              "antwort": "💬 Antwort", "absage": "❌ Absage"}.get(b[9], b[9])
        c = (
            '<h1>📧 Bewerbung</h1>'
            '<div class="cd"><h3>' + si + '</h3>'
            '<p><strong>🏢</strong> ' + str(b[3]) + '</p>'
            '<p><strong>💼</strong> ' + str(b[4]) + '</p>'
            '<p><strong>📧</strong> ' + str(b[5] or "N/A") + '</p>'
            '<p><strong>📝</strong> ' + str(b[6]) + '</p>'
            '<p><strong>📎</strong> ' + str(b[8] or "Keine") + '</p></div>'
            '<div class="cd"><h3>✉️ Anschreiben</h3>'
            '<textarea rows="20">' + str(b[7]) + '</textarea></div>'
            '<a href="/xsi" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)