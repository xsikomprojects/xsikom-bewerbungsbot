"""
Bot Routes: Aaliyah KI, AVINU Job-Suche, XSI Auto-Bewerber
Alle Imports kommen aus shared.py – kein Import aus webapp.py!
"""
from flask import render_template_string, request, redirect, session
from shared import H, DB, ki, pl
from avinu_ki import (
    alle_jobs_suchen, get_alle_berufe, jobs_speichern, jobs_laden,
    anschreiben_generieren, auto_bewerbung_erstellen,
    job_favorit_toggle, job_loeschen, BRANCHEN
)
from xsi_bot import (
    xsi_anschreiben_komplett, xsi_betreff_erstellen,
    xsi_email_senden, xsi_bewerbung_speichern,
    xsi_bewerbung_status_update, xsi_bewerbungen_laden,
    xsi_templates_laden, xsi_statistiken, xsi_unterlagen_pruefen
)
import sqlite3


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


def _branchen_html():
    """Gibt Branchen als HTML-Options zurück."""
    namen = {
        "it":          "💻 IT",
        "handwerk":    "🔧 Handwerk",
        "gesundheit":  "🏥 Gesundheit",
        "verwaltung":  "📋 Verwaltung",
        "verkauf":     "🛒 Verkauf",
        "logistik":    "📦 Logistik",
        "gastronomie": "🍽️ Gastronomie",
        "bildung":     "📚 Bildung",
        "marketing":   "📱 Marketing",
        "finanzen":    "💰 Finanzen",
        "transport":   "🚚 Transport",
        "produktion":  "🏭 Produktion",
        "reinigung":   "🧹 Reinigung",
        "sicherheit":  "🛡️ Sicherheit",
    }
    return "".join(
        f'<option value="{k}">{v}</option>'
        for k, v in namen.items()
    )


def _berufe_datalist():
    """Gibt Berufe als HTML-Datalist-Options zurück."""
    return "".join(
        f'<option value="{beruf}">'
        for beruf in get_alle_berufe()
    )


def _unterlagen_status(uid):
    """Gibt (check_dict, status_html, upload_btn) zurück."""
    ch = xsi_unterlagen_pruefen(uid)
    fehlend = []
    if not ch["lebenslauf"]:  fehlend.append("Lebenslauf")
    if not ch["zeugnis"]:     fehlend.append("Zeugnis")
    if not ch["zertifikat"]: fehlend.append("Zertifikat")
    if not ch["bild"]:        fehlend.append("Foto")

    if fehlend:
        status_html = (
            '<div class="al aw">⚠️ Fehlend: '
            + ", ".join(fehlend)
            + ' <a href="/uploads">Hochladen</a></div>'
        )
        upload_btn = '<a href="/uploads" class="bt b3">📂 Hochladen</a>'
    else:
        status_html = '<div class="al ao">✅ Alle Unterlagen da!</div>'
        upload_btn  = ""

    uh = "".join(
        f'<span style="margin-right:15px">{"✅" if ok else "❌"} {kat}</span>'
        for kat, ok in [
            ("📄 Lebenslauf", ch["lebenslauf"]),
            ("📜 Zeugnis",    ch["zeugnis"]),
            ("🏆 Zertifikat", ch["zertifikat"]),
            ("🖼️ Foto",       ch["bild"]),
        ]
    )
    return ch, status_html, upload_btn, uh


# ─────────────────────────────────────────────────────────────────
# ROUTE-REGISTRIERUNG
# ─────────────────────────────────────────────────────────────────

def register_bot_routes(app):

    # ════════════════════════════════════════════════════════════
    # AALIYAH KI
    # ════════════════════════════════════════════════════════════

    @app.route("/aaliyah", methods=["GET", "POST"])
    def aaliyah_route():
        r = _login_required()
        if r: return r

        antwort = ""
        if request.method == "POST":
            frage = request.form.get("frage", "").strip()
            if frage:
                a = ki(frage).replace("\n", "<br>")
                antwort = (
                    '<div class="al ai" style="flex-direction:column;align-items:start">'
                    '<strong>🤖 Aaliyah:</strong>'
                    '<div style="margin-top:10px">' + a + '</div>'
                    '</div>'
                )

        c = (
            '<h1>🤖 Aaliyah KI</h1>'
            '<div class="cd">'
            '<form method="POST">'
            '<input type="text" name="frage" '
            'placeholder="Frag Aaliyah..." required>'
            '<button type="submit" class="bt b5" style="width:100%">'
            '📤 Senden</button>'
            '</form>'
            + antwort +
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # AVINU JOB-SUCHE
    # ════════════════════════════════════════════════════════════

    @app.route("/avinu", methods=["GET", "POST"])
    def avinu_dashboard():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        # ── POST: Jobs suchen ────────────────────────────────────
        if request.method == "POST":
            branche       = request.form.get("branche", "")
            suchbegriff   = request.form.get("suchbegriff", "").strip()
            standort      = request.form.get("standort", "").strip()
            radius        = int(request.form.get("radius", 25))
            international = request.form.get("international") == "yes"

            if not suchbegriff and branche:
                suchbegriff = BRANCHEN.get(branche, ["Job"])[0]

            if suchbegriff and standort:
                try:
                    alle = alle_jobs_suchen(
                        suchbegriff, standort, radius, international
                    )
                    if alle:
                        n    = jobs_speichern(uid, alle, branche, radius)
                        intl = " 🌍" if international else " 🇩🇪"
                        msg  = (
                            '<div class="al ao">✅ '
                            + str(n) + " neue Jobs" + intl + "!</div>"
                        )
                    else:
                        msg = '<div class="al aw">⚠️ Keine Jobs gefunden!</div>'
                except Exception as e:
                    msg = '<div class="al ae">❌ ' + str(e)[:100] + "</div>"

        # ── Daten laden ──────────────────────────────────────────
        ft   = request.args.get("filter", "offen")
        jobs = jobs_laden(uid, ft)

        # ── Statistiken ──────────────────────────────────────────
        cn, cc = _db_connect()
        cc.execute(
            "SELECT COUNT(*) FROM jobs WHERE user_id=?", (uid,)
        )
        total = cc.fetchone()[0]
        try:
            cc.execute(
                "SELECT COUNT(*) FROM jobs WHERE user_id=? AND beworben=1",
                (uid,)
            )
            bc = cc.fetchone()[0]
            cc.execute(
                "SELECT COUNT(*) FROM jobs WHERE user_id=? AND favorit=1",
                (uid,)
            )
            fc = cc.fetchone()[0]
        except Exception:
            bc = fc = 0
        cn.close()

        # ── Jobs HTML ────────────────────────────────────────────
        FLAGS = {
            "DE": "🇩🇪", "US": "🇺🇸", "UK": "🇬🇧",
            "FR": "🇫🇷", "EU": "🇪🇺", "WORLD": "🌍", "INT": "🌍",
        }
        STATUS_ICONS = {
            "erstellt": "📝", "gesendet": "✅",
            "antwort":  "💬", "absage":   "❌",
        }

        jh = ""
        for j in jobs[:30]:
            beworben   = j[11]
            fav        = j[13] if len(j) > 13 else 0
            land       = j[15] if len(j) > 15 else "DE"
            fg         = FLAGS.get(land, "🌍")
            bb         = (
                '<span style="background:var(--gn);color:white;'
                'padding:4px 10px;border-radius:12px;font-size:11px">✅</span>'
                if beworben else ""
            )
            url_link   = (
                f'<a href="{j[6]}" target="_blank">🔗</a>' if j[6] else ""
            )
            beschr     = (j[5][:200] + "...") if j[5] and len(j[5]) > 200 else (j[5] or "")

            jh += (
                '<div class="cd">'
                '<div style="display:flex;justify-content:space-between;'
                'flex-wrap:wrap;gap:15px">'
                '<div style="flex:1;min-width:280px">'
                f'<h3>{fg} {j[3]} {bb}</h3>'
                f'<p style="color:var(--cy);font-size:16px">🏢 <strong>{j[2]}</strong></p>'
                f'<p style="color:var(--t2);font-size:13px">'
                f'📍 {j[4]} · 🔗 {j[9]} · 🏷️ {j[8]}</p>'
            )
            if beschr:
                jh += f'<p style="color:var(--t3);font-size:13px">{beschr}</p>'
            jh += f'<p>{url_link}</p></div>'
            jh += (
                '<div style="display:flex;flex-direction:column;gap:8px">'
                f'<a href="/xsi/schnell/{j[0]}" class="bt b2">🤖 XSI</a>'
                f'<a href="/avinu/favorit/{j[0]}" class="bt b3" '
                f'style="padding:8px 14px">{"⭐" if fav else "☆"}</a>'
                f'<a href="/avinu/loeschen/{j[0]}" class="bt b4" '
                f'style="padding:8px 14px" '
                f'onclick="return confirm(\'Loeschen?\')">🗑️</a>'
                '</div></div></div>'
            )

        if not jh:
            jh = (
                '<p style="text-align:center;color:var(--t3);padding:40px">'
                'Keine Jobs!</p>'
            )

        # ── Seite zusammenbauen ──────────────────────────────────
        c = (
            '<h1>⚡ AVINU - Global Jobs</h1>'
            '<p>10+ Portale · 300+ Berufe · 🌍</p>'
            + msg +
            '<div class="cd"><h3>🔍 Job-Suche</h3>'
            '<form method="POST">'
            '<p>📂 Branche:</p>'
            '<select name="branche">'
            '<option value="">--</option>'
            + _branchen_html() +
            '</select>'
            '<p>💼 Beruf:</p>'
            '<input type="text" name="suchbegriff" '
            'placeholder="IT-Fachtechniker, Praktikum..." '
            'list="bl" required>'
            '<datalist id="bl">' + _berufe_datalist() + '</datalist>'
            '<p>📍 Standort:</p>'
            '<input type="text" name="standort" '
            'placeholder="Berlin, Mainz..." required>'
            '<p>📏 Umkreis: <span id="rv">25</span> km</p>'
            '<input type="range" name="radius" '
            'min="5" max="200" value="25" step="5" '
            'oninput="document.getElementById(\'rv\').textContent=this.value" '
            'style="width:100%;margin-bottom:15px">'
            '<div style="margin:20px 0;padding:15px;'
            'background:rgba(0,217,255,0.1);border-radius:12px">'
            '<label style="display:flex;align-items:center;'
            'gap:10px;cursor:pointer">'
            '<input type="checkbox" name="international" '
            'value="yes" style="width:auto">'
            '<span>🌍 <strong>International</strong></span>'
            '</label></div>'
            '<button type="submit" class="bt b1" style="width:100%">'
            '🚀 Jobs suchen</button>'
            '</form></div>'

            '<div class="gr" style="margin:30px 0">'
            '<a href="/avinu?filter=alle" style="text-decoration:none">'
            '<div class="sc"><div class="si">💼</div>'
            f'<div class="sv">{total}</div>'
            '<div class="sl">Alle</div></div></a>'

            '<a href="/avinu?filter=offen" style="text-decoration:none">'
            '<div class="sc"><div class="si">📋</div>'
            f'<div class="sv">{total - bc}</div>'
            '<div class="sl">Offen</div></div></a>'

            '<a href="/avinu?filter=beworben" style="text-decoration:none">'
            '<div class="sc"><div class="si">✅</div>'
            f'<div class="sv">{bc}</div>'
            '<div class="sl">Beworben</div></div></a>'

            '<a href="/avinu?filter=favoriten" style="text-decoration:none">'
            '<div class="sc"><div class="si">⭐</div>'
            f'<div class="sv">{fc}</div>'
            '<div class="sl">Favoriten</div></div></a>'
            '</div>'

            f'<h2>🎯 Jobs ({len(jobs)})</h2>'
            + jh
        )
        return render_template_string(H, content=c, user=session)

    # ── Favorit togglen ──────────────────────────────────────────
    @app.route("/avinu/favorit/<int:jid>")
    def avinu_favorit(jid):
        r = _login_required()
        if r: return r
        job_favorit_toggle(jid, session["user_id"])
        return redirect("/avinu")

    # ── Job löschen ───────────────────────────────────────────────
    @app.route("/avinu/loeschen/<int:jid>")
    def avinu_loeschen(jid):
        r = _login_required()
        if r: return r
        job_loeschen(jid, session["user_id"])
        return redirect("/avinu")

    # ════════════════════════════════════════════════════════════
    # XSI BOT
    # ════════════════════════════════════════════════════════════

    @app.route("/xsi")
    def xsi_dashboard():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        st  = xsi_statistiken(uid)
        _, status_html, _, _ = _unterlagen_status(uid)

        # ── Letzte Bewerbungen ───────────────────────────────────
        bw = xsi_bewerbungen_laden(uid)
        bh = ""
        for b in bw[:10]:
            ic = {
                "erstellt": "📝", "gesendet": "✅",
                "antwort":  "💬", "absage":   "❌",
            }.get(b[9], "📋")
            bh += (
                '<div class="ui"><div>'
                f'{ic} <strong>{b[4]}</strong> bei {b[3]}'
                f'<br><small style="color:var(--t3)">'
                f'An: {b[5] or "N/A"} · {b[9]}</small></div>'
                f'<a href="/xsi/detail/{b[0]}" '
                'class="bt b1" style="padding:8px 14px">👁️</a>'
                '</div>'
            )
        if not bh:
            bh = '<p style="text-align:center;color:var(--t3)">Noch keine</p>'

        c = (
            '<h1>🤖 XSI Bot - Auto-Bewerber</h1>'
            '<p>Automatisch Bewerbungen erstellen & senden!</p>'
            + status_html +
            '<div class="gr" style="margin:30px 0">'
            '<a href="/xsi/neu" style="text-decoration:none">'
            '<div class="sc"><div class="si">✨</div>'
            '<div class="sv">Neu</div>'
            '<div class="sl">Bewerbung</div></div></a>'

            '<div class="sc"><div class="si">📧</div>'
            f'<div class="sv">{st["gesendet"]}</div>'
            '<div class="sl">Gesendet</div></div>'

            '<div class="sc"><div class="si">📝</div>'
            f'<div class="sv">{st["erstellt"]}</div>'
            '<div class="sl">Entwuerfe</div></div>'

            '<div class="sc"><div class="si">📂</div>'
            f'<div class="sv">{st["unterlagen"]}</div>'
            '<div class="sl">Unterlagen</div></div>'
            '</div>'

            '<h2>📧 Bewerbungen</h2>'
            '<div class="cd">' + bh + '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ── Neue Bewerbung ────────────────────────────────────────────
    @app.route("/xsi/neu", methods=["GET", "POST"])
    def xsi_neu():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        pr  = pl(uid)
        msg = ""

        if request.method == "POST":
            fi = request.form.get("firma", "").strip()
            po = request.form.get("position", "").strip()
            em = request.form.get("empfaenger", "").strip()
            ti = request.form.get("template_id", "")
            sp = request.form.get("sprache", "de")
            ak = request.form.get("aktion", "erstellen")

            if fi and po and ti:
                cn, cc = _db_connect()
                cc.execute(
                    "SELECT * FROM xsi_templates WHERE id=?", (int(ti),)
                )
                t = cc.fetchone()
                cn.close()

                if t:
                    bt2 = xsi_betreff_erstellen(t[2], fi, po, pr)
                    an  = xsi_anschreiben_komplett(t[3], fi, po, pr, sp)
                    bi  = xsi_bewerbung_speichern(
                        uid, 0, fi, po, em, bt2, an, "erstellt", sp
                    )

                    if ak == "senden" and em:
                        ok, info = xsi_email_senden(em, bt2, an, uid, pr)
                        if ok:
                            xsi_bewerbung_status_update(bi, "gesendet")
                            msg = (
                                '<div class="al ao">✅ An '
                                + fi + " gesendet! " + info + "</div>"
                            )
                        else:
                            msg = '<div class="al ae">❌ ' + info + "</div>"
                    else:
                        msg = '<div class="al ao">✅ Entwurf gespeichert!</div>'

        # ── Templates ────────────────────────────────────────────
        tp = xsi_templates_laden(premium=session.get("premium", False))
        th = ""
        for t in tp:
            pb = '<span class="bg">💎</span>' if t[5] else ""
            th += (
                '<label style="display:block;margin:10px 0;padding:16px;'
                'background:rgba(10,14,26,0.5);border-radius:12px;cursor:pointer">'
                f'<input type="radio" name="template_id" value="{t[0]}" required>'
                f' <strong>{t[1]}</strong> {pb}'
                f'<br><small style="color:var(--t3)">'
                f'Betreff: {t[2][:50]}... | {t[4].upper()}</small>'
                '</label>'
            )

        # ── Unterlagen-Status ────────────────────────────────────
        _, _, upload_btn, uh = _unterlagen_status(uid)

        c = (
            '<h1>✨ Neue Bewerbung mit XSI</h1>'
            + msg +
            '<div class="cd"><h3>📋 Unterlagen</h3>'
            '<div style="margin:10px 0">' + uh + '</div>'
            + upload_btn + '</div>'

            '<div class="cd"><h3>📧 Bewerbung</h3>'
            '<form method="POST">'
            '<p>📋 Art:</p>'
            '<select name="typ">'
            '<option value="job">💼 Job</option>'
            '<option value="praktikum">🎓 Praktikum</option>'
            '<option value="ausbildung">📚 Ausbildung</option>'
            '<option value="initiativ">💡 Initiativ</option>'
            '<option value="werkstudent">🧑‍💻 Werkstudent</option>'
            '<option value="minijob">💶 Minijob</option>'
            '</select>'
            '<p>🏢 Firma:</p>'
            '<input type="text" name="firma" '
            'placeholder="SAP, Telekom..." required>'
            '<p>💼 Position:</p>'
            '<input type="text" name="position" '
            'placeholder="IT-Fachtechniker, Praktikant..." required>'
            '<p>📧 E-Mail der Firma:</p>'
            '<input type="email" name="empfaenger" '
            'placeholder="bewerbung@firma.de">'
            '<p>🌍 Sprache:</p>'
            '<select name="sprache">'
            '<option value="de">🇩🇪 Deutsch</option>'
            '<option value="en">🇬🇧 English</option>'
            '<option value="fr">🇫🇷 Francais</option>'
            '</select>'
            '<p>📝 Vorlage:</p>'
            + th +
            '<div style="display:flex;gap:10px;margin-top:20px">'
            '<button type="submit" name="aktion" value="erstellen" '
            'class="bt b1" style="flex:1">📝 Entwurf</button>'
            '<button type="submit" name="aktion" value="senden" '
            'class="bt b2" style="flex:1">🚀 Senden!</button>'
            '</div></form></div>'
            '<div class="al ai">'
            '💡 XSI generiert KI-Anschreiben + haengt ALLE Unterlagen an!'
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ── Schnell-Bewerbung aus AVINU ───────────────────────────────
    @app.route("/xsi/schnell/<int:jid>")
    def xsi_schnell(jid):
        r = _login_required()
        if r: return r

        cn, cc = _db_connect()
        cc.execute(
            "SELECT firma, position FROM jobs "
            "WHERE id=? AND user_id=?",
            (jid, session["user_id"])
        )
        j = cc.fetchone()
        cn.close()

        if not j:
            return redirect("/avinu")
        return redirect(f"/xsi/neu?firma={j[0]}&position={j[1]}")

    # ── Bewerbung Detail ─────────────────────────────────────────
    @app.route("/xsi/detail/<int:bid>")
    def xsi_detail(bid):
        r = _login_required()
        if r: return r

        cn, cc = _db_connect()
        cc.execute(
            "SELECT * FROM xsi_bewerbungen "
            "WHERE id=? AND user_id=?",
            (bid, session["user_id"])
        )
        b = cc.fetchone()
        cn.close()

        if not b:
            return redirect("/xsi")

        si = {
            "erstellt": "📝 Entwurf",
            "gesendet": "✅ Gesendet",
            "antwort":  "💬 Antwort",
            "absage":   "❌ Absage",
        }.get(b[9], b[9])

        c = (
            '<h1>📧 Bewerbung</h1>'
            '<div class="cd">'
            f'<h3>{si}</h3>'
            f'<p><strong>🏢</strong> {b[3]}</p>'
            f'<p><strong>💼</strong> {b[4]}</p>'
            f'<p><strong>📧</strong> {b[5] or "N/A"}</p>'
            f'<p><strong>📝</strong> {b[6]}</p>'
            f'<p><strong>📎</strong> {b[8] or "Keine"}</p>'
            '</div>'
            '<div class="cd"><h3>✉️ Anschreiben</h3>'
            f'<textarea rows="20">{b[7]}</textarea>'
            '</div>'
            '<a href="/xsi" class="bt b1">← Zurueck</a>'
        )
        return render_template_string(H, content=c, user=session)