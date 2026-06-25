"""
Extra Routes: Premium, PDF, Tutorial, Updates, Install,
              Landing, Job-Alerts
"""
from flask import (
    render_template_string, request,
    redirect, session, send_file
)
from shared import H, DB, CE, hp, pa, pl
import sqlite3
import stripe
import os


def _login_required():
    if "user_id" not in session:
        return redirect("/login")
    return None


def _user_or_none():
    return session if "user_id" in session else None


def _kacheln(items):
    html = "".join(
        f'<a href="{url}" style="text-decoration:none">'
        f'<div class="sc"><div class="si">{icon}</div>'
        f'<div class="sv">{titel}</div>'
        f'<div class="sl">{sub}</div>'
        f'</div></a>'
        for url, icon, titel, sub in items
    )
    return '<div class="gr">' + html + '</div>'


def register_extra_routes(app):

    @app.route("/landing")
    def landing():
        c = (
            '<section style="text-align:center;padding:40px 0 20px">'
            '<h1>Bewerben ohne Stress</h1>'
            '<p style="font-size:18px;max-width:850px;'
            'margin:0 auto 25px;color:var(--t2)">'
            'XsiKOM hilft dir Jobs zu finden, Bewerbungen schneller '
            'zu schreiben und professioneller aufzutreten.'
            '</p>'
            '<div style="display:flex;gap:15px;'
            'justify-content:center;flex-wrap:wrap">'
            '<a href="/register" class="bt b2">🚀 Kostenlos starten</a>'
            '<a href="/premium" class="bt b1">💎 Premium</a>'
            '<a href="/install" class="bt b5">📱 App</a>'
            '</div></section>'

            '<div class="cd" style="text-align:center;margin:20px 0">'
            '<p><strong>3 KI-Bots</strong> · '
            '<strong>Jobs weltweit</strong> · '
            '<strong>Kostenloser Start</strong></p>'
            '</div>'

            '<h2 style="margin-top:40px">🤖 Warum XsiKOM?</h2>'
            '<div class="gr">'
            '<div class="cd"><h3>🤖 Aaliyah</h3>'
            '<p>KI-Beraterin fuer Anschreiben und Interview.</p>'
            '<a href="/aaliyah" class="bt b5" '
            'style="padding:8px 18px;font-size:13px">'
            'Jetzt fragen</a></div>'
            '<div class="cd"><h3>⚡ AVINU</h3>'
            '<p>Jobs nach Branche, Beruf und Standort.</p>'
            '<a href="/avinu" class="bt b1" '
            'style="padding:8px 18px;font-size:13px">'
            'Jobs suchen</a></div>'
            '<div class="cd"><h3>🤖 XSI</h3>'
            '<p>Bewerbungen mit KI und Vorlagen.</p>'
            '<a href="/xsi" class="bt b2" '
            'style="padding:8px 18px;font-size:13px">'
            'Bewerben</a></div>'
            '</div>'

            '<h2 style="margin-top:40px">👥 Fuer wen?</h2>'
            '<div class="gr">'
            '<div class="sc"><div class="si">🎓</div>'
            '<div class="sv">Schueler</div>'
            '<div class="sl">Praktikum & Ausbildung</div></div>'
            '<div class="sc"><div class="si">🧑‍💻</div>'
            '<div class="sv">Studenten</div>'
            '<div class="sl">Werkstudent & Einstieg</div></div>'
            '<div class="sc"><div class="si">🚀</div>'
            '<div class="sv">Wechsler</div>'
            '<div class="sl">Neustart & Karriere</div></div>'
            '</div>'

            '<h2 style="margin-top:40px">💰 Free oder Premium</h2>'
            '<div class="gr">'
            '<div class="cd"><h3>🆓 Free</h3>'
            '<p style="color:var(--gn);font-size:22px;'
            'font-weight:700">0 EUR</p>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>✅ KI-Beratung</li>'
            '<li>✅ Basis Jobsuche</li>'
            '<li>✅ Lebenslauf-Editor</li>'
            '<li>❌ Alle Vorlagen</li>'
            '</ul>'
            '<a href="/register" class="bt b1" '
            'style="width:100%;margin-top:15px">'
            '🚀 Starten</a></div>'
            '<div class="cd" style="border:2px solid var(--yl)">'
            '<span class="bg">⭐ BELIEBT</span>'
            '<h3 style="margin-top:10px">💎 Premium</h3>'
            '<p style="color:var(--yl);font-size:22px;'
            'font-weight:700">1.99 EUR/Monat</p>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>✅ Alles aus Free</li>'
            '<li>✅ Alle Vorlagen</li>'
            '<li>✅ Internationale Jobs</li>'
            '<li>✅ PDF-Generator</li>'
            '</ul>'
            '<a href="/premium" class="bt b3" '
            'style="width:100%;margin-top:15px">'
            '💎 Premium holen</a></div>'
            '</div>'

            '<div class="cd" style="text-align:center;margin-top:40px;'
            'background:linear-gradient(135deg,'
            'rgba(0,217,255,0.1),rgba(139,92,246,0.1));'
            'border:1px solid var(--cy)">'
            '<h2>Dein naechster Job wartet nicht.</h2>'
            '<p style="font-size:16px;margin-bottom:25px">'
            'Starte jetzt mit XsiKOM!</p>'
            '<div style="display:flex;gap:15px;'
            'justify-content:center;flex-wrap:wrap">'
            '<a href="/register" class="bt b2">'
            '🚀 Kostenlos starten</a>'
            '<a href="/tutorial" class="bt b1">📚 Tutorial</a>'
            '</div></div>'
        )
        return render_template_string(H, content=c, user=_user_or_none())

    @app.route("/alerts", methods=["GET", "POST"])
    def job_alerts():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        from email_service import (
            job_alert_erstellen,
            job_alerts_laden,
        )

        if request.method == "POST":
            email       = request.form.get("email",       "").strip()
            suchbegriff = request.form.get("suchbegriff", "").strip()
            standort    = request.form.get("standort",    "").strip()
            frequenz    = request.form.get("frequenz",    "taeglich")

            if email and suchbegriff and standort:
                ok, info = job_alert_erstellen(
                    uid, email, suchbegriff, standort, frequenz
                )
                if ok:
                    msg = (
                        '<div class="al ao">✅ Alert erstellt! '
                        'Bestaetigung an ' + email + '</div>'
                    )
                else:
                    msg = (
                        '<div class="al ae">❌ '
                        + str(info) + '</div>'
                    )
            else:
                msg = (
                    '<div class="al aw">'
                    '⚠️ Alle Felder ausfuellen!</div>'
                )

        alerts = job_alerts_laden(uid)
        ah = ""
        for a in alerts:
            status = "✅ Aktiv" if a[5] else "⏸️ Pausiert"
            lv     = str(a[6])[:10] if a[6] else "Noch nie"
            ah += (
                '<div class="ui"><div>'
                f'<strong>💼 {a[2]}</strong> in {a[3]}<br>'
                f'<small style="color:var(--t3)">'
                f'📧 {a[1]} · ⏰ {a[4]} · {status} · '
                f'Letzter Versand: {lv}</small>'
                '</div>'
                f'<a href="/alerts/loeschen/{a[0]}" '
                f'class="bt b4" style="padding:8px 14px" '
                f'onclick="return confirm(\'Loeschen?\')">'
                f'🗑️</a></div>'
            )

        if not ah:
            ah = (
                '<p style="color:var(--t3);text-align:center;'
                'padding:20px">Noch keine Alerts</p>'
            )

        c = (
            '<h1>🔔 Job-Alerts</h1>'
            '<p>Werde automatisch ueber neue Jobs informiert!</p>'
            + msg +
            '<div class="cd"><h3>➕ Neuer Alert</h3>'
            '<form method="POST">'
            '<p>📧 E-Mail:</p>'
            '<input type="email" name="email" '
            'placeholder="deine@email.de" required>'
            '<p>💼 Suchbegriff:</p>'
            '<input type="text" name="suchbegriff" '
            'placeholder="IT-Fachtechniker..." required>'
            '<p>📍 Standort:</p>'
            '<input type="text" name="standort" '
            'placeholder="Berlin, Mainz..." required>'
            '<p>⏰ Frequenz:</p>'
            '<select name="frequenz">'
            '<option value="sofort">⚡ Sofort</option>'
            '<option value="taeglich" selected>'
            '📅 Taeglich</option>'
            '<option value="woechentlich">'
            '📆 Woechentlich</option>'
            '</select>'
            '<button type="submit" class="bt b2" '
            'style="width:100%">🔔 Erstellen</button>'
            '</form></div>'
            '<h2>📋 Meine Alerts</h2>'
            '<div class="cd">' + ah + '</div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/alerts/loeschen/<int:aid>")
    def alert_loeschen(aid):
        r = _login_required()
        if r: return r
        from email_service import job_alert_loeschen
        job_alert_loeschen(aid, session["user_id"])
        return redirect("/alerts")

    @app.route("/alerts/abmelden/<int:aid>")
    def alert_abmelden(aid):
        try:
            cn = sqlite3.connect(DB)
            cc = cn.cursor()
            cc.execute(
                "UPDATE job_alerts SET aktiv=0 WHERE id=?", (aid,)
            )
            cn.commit()
            cn.close()
        except Exception:
            pass
        c = (
            '<div style="max-width:500px;margin:60px auto">'
            '<div class="cd" style="text-align:center">'
            '<h1>✅ Abgemeldet</h1>'
            '<p>Keine weiteren Alerts.</p>'
            '<a href="/alerts" class="bt b1">🔔 Alerts</a>'
            '</div></div>'
        )
        return render_template_string(
            H, content=c, user=_user_or_none()
        )

    @app.route("/premium")
    def premium():
        c = (
            '<h1>💎 Premium</h1>'
            '<div class="gr">'
            '<div class="cd"><h2>🆓 Free</h2><h3>0 EUR</h3>'
            '<ul style="list-style:none;padding:0;line-height:2.2">'
            '<li>✓ 5 Bewerbungen/Monat</li>'
            '<li>✓ Aaliyah KI Chat</li>'
            '<li>✓ Basis Job-Suche</li>'
            '<li>✓ Lebenslauf-Editor</li>'
            '<li>✗ Premium-Vorlagen</li>'
            '<li>✗ International</li>'
            '</ul>'
            '<button class="bt b1" style="width:100%">'
            'Aktuell</button></div>'
            '<div class="cd" style="border:2px solid var(--yl)">'
            '<span class="bg">⭐ BELIEBT</span>'
            '<h2 style="margin-top:10px">💎 Premium</h2>'
            '<h3>1.99 EUR/Monat</h3>'
            '<ul style="list-style:none;padding:0;line-height:2.2">'
            '<li>✓ UNBEGRENZT</li>'
            '<li>✓ Alle 3 KI-Bots</li>'
            '<li>✓ 8 Vorlagen</li>'
            '<li>✓ XSI Auto-Sender</li>'
            '<li>✓ International</li>'
            '<li>✓ PDF-Generator</li>'
            '</ul>'
            '<a href="/aktivieren" class="bt b3" '
            'style="width:100%">🚀 Upgrade</a>'
            '</div></div>'
        )
        return render_template_string(
            H, content=c, user=_user_or_none()
        )

    @app.route("/aktivieren", methods=["GET", "POST"])
    def aktivieren():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        if request.method == "POST":
            code = request.form.get("code", "").strip()
            if code == "XSIKOM-ADMIN-2026-PREMIUM":
                pa(uid)
                session["premium"] = 1
                c = (
                    '<h1>🎉 Premium aktiviert!</h1>'
                    '<div class="al ao">✅ Lebenslang!</div>'
                    '<a href="/dashboard" class="bt b1">'
                    '🏠 Dashboard</a>'
                )
                return render_template_string(
                    H, content=c, user=session
                )
            msg = '<div class="al ae">❌ Falscher Code!</div>'

        stripe_btn = ""
        if stripe.api_key and os.environ.get("STRIPE_PRICE_MONAT"):
            stripe_btn = (
                '<a href="/stripe-checkout" class="bt b3" '
                'style="width:100%;margin-top:15px">'
                '💳 Mit Kreditkarte (1.99 EUR)</a>'
            )

        c = (
            '<h1>🔐 Premium aktivieren</h1>'
            + msg +
            '<div class="cd"><h3>🔑 Mit Code</h3>'
            '<form method="POST">'
            '<input type="text" name="code" '
            'placeholder="Premium-Code" required>'
            '<button type="submit" class="bt b2" '
            'style="width:100%">🚀 Aktivieren</button>'
            '</form></div>'
            '<div class="cd"><h3>💳 Mit Zahlung</h3>'
            + (stripe_btn if stripe_btn else
               '<p style="color:var(--t3)">'
               'Stripe wird konfiguriert...</p>') +
            '</div>'
            '<div class="al ai">'
            '💡 Admin-Code: XSIKOM-ADMIN-2026-PREMIUM</div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/stripe-checkout")
    def stripe_checkout():
        r = _login_required()
        if r: return r

        sp = os.environ.get("STRIPE_PRICE_MONAT", "")
        if not stripe.api_key or not sp:
            return redirect("/aktivieren")

        try:
            base = request.host_url.rstrip("/")
            cs   = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": sp, "quantity": 1}],
                mode="subscription",
                success_url=(
                    base + "/stripe-success"
                    + "?session_id={CHECKOUT_SESSION_ID}"
                ),
                cancel_url=base + "/premium",
                metadata={"user_id": str(session["user_id"])},
            )
            return redirect(cs.url, code=303)
        except Exception as e:
            c = (
                '<h1>❌ Stripe Fehler</h1>'
                '<div class="al ae">'
                + str(e)[:200] + '</div>'
                '<a href="/premium" class="bt b1">← Zurueck</a>'
            )
            return render_template_string(
                H, content=c, user=session
            )

    @app.route("/stripe-success")
    def stripe_success():
        r = _login_required()
        if r: return r

        sid = request.args.get("session_id")
        if sid and stripe.api_key:
            try:
                cs = stripe.checkout.Session.retrieve(sid)
                if cs.payment_status == "paid":
                    pa(session["user_id"])
                    session["premium"] = 1
            except Exception:
                pass

        c = (
            '<h1>🎉 Zahlung erfolgreich!</h1>'
            '<div class="al ao">✅ Premium aktiviert!</div>'
            '<a href="/dashboard" class="bt b1">🏠 Dashboard</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/pdf-lebenslauf", methods=["GET", "POST"])
    def pdf_lebenslauf():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        if request.method == "POST":
            vorlage = request.form.get("vorlage", "modern")
            try:
                from pdf_generator import (
                    lebenslauf_generieren, vorlagen_info
                )
                vi = vorlagen_info()
                v  = vi.get(vorlage, {})
                if v.get("premium") and not session.get("premium"):
                    msg = (
                        '<div class="al aw">⚠️ Premium! '
                        '<a href="/premium">Upgrade</a></div>'
                    )
                else:
                    result = lebenslauf_generieren(uid, vorlage)
                    if result:
                        pfad, name = result
                        return send_file(
                            pfad, as_attachment=True,
                            download_name=name
                        )
                    else:
                        msg = (
                            '<div class="al ae">'
                            '❌ Profil ausfuellen!</div>'
                        )
            except Exception as e:
                msg = (
                    '<div class="al ae">❌ '
                    + str(e)[:100] + '</div>'
                )

        try:
            from pdf_generator import vorlagen_info
            vi = vorlagen_info()
        except Exception:
            vi = {
                "modern": {
                    "name": "Modern",
                    "icon": "🎨",
                    "premium": False,
                },
                "klassisch": {
                    "name": "Klassisch",
                    "icon": "📄",
                    "premium": False,
                },
            }

        vh = ""
        for key, v in vi.items():
            pb      = (
                '<span class="bg">💎</span>'
                if v.get("premium") else
                '<span style="color:var(--gn)">FREE</span>'
            )
            checked = " checked" if key == "modern" else ""
            vh += (
                '<label style="display:block;margin:12px 0;'
                'padding:20px;background:rgba(10,14,26,0.5);'
                'border-radius:12px;cursor:pointer">'
                f'<input type="radio" name="vorlage" '
                f'value="{key}"{checked}>'
                f' {v.get("icon","📄")} '
                f'<strong>{v.get("name",key)}</strong> {pb}'
                '</label>'
            )

        c = (
            '<h1>📄 PDF Generator</h1>'
            + msg +
            '<div class="cd"><h3>📝 Vorlage</h3>'
            '<form method="POST">'
            + vh +
            '<button type="submit" class="bt b2" '
            'style="width:100%;margin-top:15px">'
            '📄 PDF erstellen</button>'
            '</form></div>'
            '<div class="al ai">'
            '💡 <a href="/lebenslauf">Profil</a> erst ausfuellen!'
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial")
    def tutorial():
        r = _login_required()
        if r: return r
        c = (
            '<h1>📚 Tutorial</h1>'
            + _kacheln([
                ("/tutorial/start",   "🚀", "Start",   "Erste Schritte"),
                ("/tutorial/aaliyah", "🤖", "Aaliyah", "KI-Beraterin"),
                ("/tutorial/avinu",   "⚡", "AVINU",   "Job-Suche"),
                ("/tutorial/xsi",     "🤖", "XSI",     "Auto-Bewerber"),
                ("/tutorial/faq",     "❓", "FAQ",     "Fragen"),
                ("/tutorial/tipps",   "💡", "Tipps",   "Profi-Tipps"),
            ])
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/start")
    def tutorial_start():
        r = _login_required()
        if r: return r
        c = (
            '<h1>🚀 Erste Schritte</h1>'
            '<div class="cd"><h3>1. Profil ausfuellen</h3>'
            '<p><a href="/lebenslauf">📝 Lebenslauf</a></p></div>'
            '<div class="cd"><h3>2. Unterlagen hochladen</h3>'
            '<p><a href="/uploads">📂 Dateien</a></p></div>'
            '<div class="cd"><h3>3. Jobs suchen</h3>'
            '<p><a href="/avinu">⚡ AVINU</a></p></div>'
            '<div class="cd"><h3>4. Bewerben</h3>'
            '<p><a href="/xsi/neu">🤖 XSI</a></p></div>'
            '<div class="al ao">🎉 In 5 Minuten startklar!</div>'
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/aaliyah")
    def tutorial_aaliyah():
        r = _login_required()
        if r: return r
        c = (
            '<h1>🤖 Aaliyah</h1>'
            '<div class="cd"><h3>Was kann Aaliyah?</h3>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>Anschreiben & Bewerbungstipps</li>'
            '<li>Lebenslauf-Optimierung</li>'
            '<li>Interview-Vorbereitung</li>'
            '<li>Gehaltsverhandlung</li>'
            '</ul></div>'
            '<a href="/aaliyah" class="bt b5">🤖 Fragen</a> '
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/avinu")
    def tutorial_avinu():
        r = _login_required()
        if r: return r
        c = (
            '<h1>⚡ AVINU</h1>'
            '<div class="cd"><h3>So gehts</h3>'
            '<ol style="padding-left:25px;line-height:2.2">'
            '<li>Branche waehlen</li>'
            '<li>Beruf eingeben</li>'
            '<li>Standort eingeben</li>'
            '<li>Jobs suchen!</li>'
            '</ol></div>'
            '<a href="/avinu" class="bt b1">⚡ AVINU</a> '
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/xsi")
    def tutorial_xsi():
        r = _login_required()
        if r: return r
        c = (
            '<h1>🤖 XSI Bot</h1>'
            '<div class="cd"><h3>Bewerbung erstellen</h3>'
            '<ol style="padding-left:25px;line-height:2.2">'
            '<li>Firma eingeben</li>'
            '<li>Position eingeben</li>'
            '<li>Vorlage waehlen</li>'
            '<li>Entwurf oder Senden!</li>'
            '</ol></div>'
            '<a href="/xsi/neu" class="bt b2">🤖 XSI</a> '
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/faq")
    def tutorial_faq():
        r = _login_required()
        if r: return r
        faqs = [
            ("Kostenlos?", "Ja! Free: 5/Monat. Premium: 1.99 EUR."),
            ("KI?", "Llama 3.3 70B via Groq API."),
            ("Sicher?", "AES-256, 2FA, PBKDF2, DSGVO."),
            ("Handy?", "Ja! PWA auf Android und iOS."),
        ]
        c = (
            '<h1>❓ FAQ</h1>'
            + "".join(
                f'<div class="cd"><h3>{f}</h3><p>{a}</p></div>'
                for f, a in faqs
            )
            + '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/tipps")
    def tutorial_tipps():
        r = _login_required()
        if r: return r
        tipps = [
            ("🎯 Profil ausfuellen",
             "Vollstaendiges Profil = bessere Anschreiben!"),
            ("🌍 International",
             "Remote-Jobs weltweit mit AVINU!"),
            ("💎 Premium",
             "Unbegrenzte Bewerbungen!"),
        ]
        c = (
            '<h1>💡 Tipps</h1>'
            + "".join(
                f'<div class="cd"><h3>{t}</h3><p>{b}</p></div>'
                for t, b in tipps
            )
            + '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/updates")
    def updates_seite():
        r = _login_required()
        if r: return r

        try:
            from auto_update import (
                update_status, changelog_laden,
                vorschlaege_laden, ist_update_faellig,
            )
            st      = update_status()
            cl      = changelog_laden(5)
            vs      = vorschlaege_laden(5)
            faellig = ist_update_faellig()
        except Exception:
            st = {
                "version":            "10.0",
                "letztes_update":     "---",
                "naechstes_update":   "---",
                "offene_vorschlaege": 0,
            }
            cl = []
            vs = []
            faellig = True

        cl_html = "".join(
            '<div class="ui"><div>'
            f'<strong>v{c2[1]}</strong> – {str(c2[2])[:16]}'
            f'<br><small style="color:var(--t3)">'
            f'{str(c2[3])[:200]}...</small>'
            '</div></div>'
            for c2 in cl
        ) or '<p style="color:var(--t3)">Keine Updates</p>'

        vs_html = "".join(
            '<div class="ui"><div>'
            + ("✅" if v[4] else "⏳")
            + f' <strong>{v[1]}</strong><br>'
            f'<small style="color:var(--t3)">'
            f'{str(v[2])[:150]}...</small>'
            '</div></div>'
            for v in vs
        ) or '<p style="color:var(--t3)">Keine Vorschlaege</p>'

        update_btn = ""
        if session.get("rolle") == "admin":
            update_btn = (
                '<a href="/updates/jetzt" class="bt b2" '
                'style="width:100%;margin-top:15px">'
                '🤖 Update starten!</a>'
            )

        status_msg = (
            '<div class="al ai">🤖 Update faellig!</div>'
            if faellig else
            '<div class="al ao">✅ Aktuell!</div>'
        )

        c = (
            '<h1>🔄 Updates</h1>'
            '<div class="gr">'
            '<div class="sc"><div class="si">📦</div>'
            f'<div class="sv">v{st["version"]}</div>'
            '<div class="sl">Version</div></div>'
            '<div class="sc"><div class="si">📅</div>'
            f'<div class="sv">'
            f'{str(st["letztes_update"])[:10]}</div>'
            '<div class="sl">Letztes</div></div>'
            '<div class="sc"><div class="si">💡</div>'
            f'<div class="sv">{st["offene_vorschlaege"]}</div>'
            '<div class="sl">Vorschlaege</div></div>'
            '</div>'
            + status_msg + update_btn +
            '<h2>📋 Changelog</h2>'
            '<div class="cd">' + cl_html + '</div>'
            '<h2>💡 Vorschlaege</h2>'
            '<div class="cd">' + vs_html + '</div>'
            '<h2>📝 Feedback</h2>'
            '<div class="cd">'
            '<form method="POST" action="/updates/feedback">'
            '<select name="typ" required>'
            '<option value="bug">🐛 Bug</option>'
            '<option value="feature">✨ Feature</option>'
            '<option value="lob">👍 Lob</option>'
            '</select>'
            '<textarea name="nachricht" rows="4" '
            'placeholder="Feedback..." required></textarea>'
            '<select name="bewertung">'
            '<option value="5">⭐⭐⭐⭐⭐</option>'
            '<option value="4">⭐⭐⭐⭐</option>'
            '<option value="3">⭐⭐⭐</option>'
            '</select>'
            '<button type="submit" class="bt b2" '
            'style="width:100%">📤 Senden</button>'
            '</form></div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/updates/jetzt")
    def update_jetzt():
        r = _login_required()
        if r: return r
        if session.get("rolle") != "admin":
            return redirect("/updates")
        try:
            from auto_update import monatliches_update
            ergebnisse = monatliches_update()
            details = "".join(
                f'<div class="cd"><h3>{titel}</h3>'
                f'<p>{str(inhalt)[:500]}</p></div>'
                for titel, inhalt in ergebnisse
            )
            c = (
                '<h1>✅ Update fertig!</h1>'
                + details +
                '<a href="/updates" class="bt b1">← Zurueck</a>'
            )
        except Exception as e:
            c = (
                '<h1>❌ Fehler</h1>'
                '<div class="al ae">' + str(e)[:200] + '</div>'
                '<a href="/updates" class="bt b1">← Zurueck</a>'
            )
        return render_template_string(H, content=c, user=session)

    @app.route("/updates/feedback", methods=["POST"])
    def update_feedback():
        r = _login_required()
        if r: return r
        try:
            from auto_update import feedback_speichern
            typ       = request.form.get("typ",      "")
            nachricht = request.form.get("nachricht", "")
            bewertung = int(request.form.get("bewertung", 5))
            if typ and nachricht:
                feedback_speichern(
                    session["user_id"], typ, nachricht, bewertung
                )
        except Exception:
            pass
        return redirect("/updates")

    @app.route("/install")
    def install():
        c = (
            '<h1>📱 App installieren</h1>'
            '<div class="cd"><h3>🤖 Android (Chrome)</h3>'
            '<ol style="padding-left:25px;line-height:2.5">'
            '<li>Chrome oeffnen</li>'
            '<li>3-Punkte-Menue</li>'
            '<li>App installieren</li>'
            '<li>✅ Fertig!</li>'
            '</ol></div>'
            '<div class="cd"><h3>🍎 iPhone (Safari)</h3>'
            '<ol style="padding-left:25px;line-height:2.5">'
            '<li>Safari oeffnen</li>'
            '<li>Teilen ⬆️</li>'
            '<li>Zum Home-Bildschirm</li>'
            '<li>✅ Fertig!</li>'
            '</ol></div>'
            '<div class="al ao">'
            '✅ App-Icon + Offline-Modus!'
            '</div>'
        )
        return render_template_string(
            H, content=c, user=_user_or_none()
        )