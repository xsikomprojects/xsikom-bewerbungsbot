"""Extra Routes: Tutorial, Updates, PDF Generator, Premium, Stripe"""
from flask import render_template_string, request, redirect, session, send_file
from webapp import H, DB, CE, hp, pa, pl
import sqlite3
import stripe
import os


def register_extra_routes(app):

    # ============================================================
    # PREMIUM
    # ============================================================
    @app.route("/premium")
    def premium():
        c = (
            '<h1>💎 Premium</h1>'
            '<div class="gr">'
            '<div class="cd">'
            '<h2>🆓 Free</h2><h3>0 €</h3>'
            '<ul style="list-style:none;padding:0;line-height:2.2">'
            '<li>✓ 5 Bewerbungen/Monat</li>'
            '<li>✓ Aaliyah KI Chat</li>'
            '<li>✓ Basis Job-Suche</li>'
            '<li>✓ Lebenslauf-Editor</li>'
            '<li>✗ Premium-Vorlagen</li>'
            '<li>✗ XSI Auto-Sender</li>'
            '<li>✗ International</li></ul>'
            '<button class="bt b1" style="width:100%">Aktuell</button></div>'
            '<div class="cd" style="border:2px solid var(--yl)">'
            '<span class="bg">⭐ BELIEBT</span>'
            '<h2 style="margin-top:10px">💎 Premium</h2>'
            '<h3>1.99 €/Monat</h3>'
            '<ul style="list-style:none;padding:0;line-height:2.2">'
            '<li>✓ UNBEGRENZTE Bewerbungen</li>'
            '<li>✓ Alle 3 KI-Bots</li>'
            '<li>✓ 8 Premium-Vorlagen</li>'
            '<li>✓ XSI Auto-Sender</li>'
            '<li>✓ Alle 10+ Jobportale</li>'
            '<li>✓ International</li>'
            '<li>✓ PDF-Generator</li>'
            '<li>✓ Werbefrei</li></ul>'
            '<a href="/aktivieren" class="bt b3" style="width:100%">🚀 Upgrade</a></div>'
            '</div>'
        )
        return render_template_string(H, content=c,
            user=session if "user_id" in session else None)

    @app.route("/aktivieren", methods=["GET", "POST"])
    def aktivieren():
        if "user_id" not in session:
            return redirect("/login")
        msg = ""
        if request.method == "POST":
            code = request.form.get("code", "").strip()
            if code == "XSIKOM-ADMIN-2026-PREMIUM":
                pa(session["user_id"])
                session["premium"] = 1
                c = (
                    '<h1>🎉 Premium aktiviert!</h1>'
                    '<div class="al ao">✅ Lebenslang Premium!</div>'
                    '<a href="/dashboard" class="bt b1">Dashboard</a>'
                )
                return render_template_string(H, content=c, user=session)
            else:
                msg = '<div class="al ae">❌ Falscher Code!</div>'

        stripe_btn = ""
        if stripe.api_key and os.environ.get("STRIPE_PRICE_MONAT"):
            stripe_btn = (
                '<a href="/stripe-checkout" class="bt b3" '
                'style="width:100%;margin-top:15px">💳 Mit Kreditkarte (1.99€)</a>'
            )

        c = (
            '<h1>🔐 Premium aktivieren</h1>' + msg +
            '<div class="cd"><h3>🔑 Mit Code</h3>'
            '<form method="POST">'
            '<input type="text" name="code" placeholder="Premium-Code" required>'
            '<button type="submit" class="bt b2" style="width:100%">🚀 Aktivieren</button>'
            '</form></div>'
            '<div class="cd"><h3>💳 Mit Zahlung</h3>'
            + (stripe_btn if stripe_btn else
               '<p style="color:var(--t3)">Stripe wird konfiguriert...</p>') +
            '</div>'
            '<div class="al ai">💡 Admin-Code: XSIKOM-ADMIN-2026-PREMIUM</div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/stripe-checkout")
    def stripe_checkout():
        if "user_id" not in session:
            return redirect("/login")
        sp = os.environ.get("STRIPE_PRICE_MONAT", "")
        if not stripe.api_key or not sp:
            return redirect("/aktivieren")
        try:
            d = request.host_url.rstrip("/")
            cs = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": sp, "quantity": 1}],
                mode="subscription",
                success_url=d + "/stripe-success?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=d + "/premium",
                metadata={"user_id": str(session["user_id"])}
            )
            return redirect(cs.url, code=303)
        except Exception as e:
            c = '<h1>❌ Fehler</h1><div class="al ae">' + str(e)[:200] + '</div>'
            return render_template_string(H, content=c, user=session)

    @app.route("/stripe-success")
    def stripe_success():
        if "user_id" not in session:
            return redirect("/login")
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
            '<a href="/dashboard" class="bt b1">Dashboard</a>'
        )
        return render_template_string(H, content=c, user=session)

    # ============================================================
    # PDF LEBENSLAUF GENERATOR
    # ============================================================
    @app.route("/pdf-lebenslauf", methods=["GET", "POST"])
    def pdf_lebenslauf():
        if "user_id" not in session:
            return redirect("/login")
        msg = ""
        if request.method == "POST":
            vorlage = request.form.get("vorlage", "modern")
            try:
                from pdf_generator import lebenslauf_generieren, vorlagen_info
                vi = vorlagen_info()
                v = vi.get(vorlage, {})
                if v.get("premium") and not session.get("premium"):
                    msg = '<div class="al aw">⚠️ Premium! <a href="/premium">Upgrade</a></div>'
                else:
                    result = lebenslauf_generieren(session["user_id"], vorlage)
                    if result:
                        pfad, name = result
                        return send_file(pfad, as_attachment=True, download_name=name)
                    else:
                        msg = '<div class="al ae">❌ Profil ausfuellen! <a href="/lebenslauf">Lebenslauf</a></div>'
            except Exception as e:
                msg = '<div class="al ae">❌ ' + str(e)[:100] + '</div>'

        # Vorlagen anzeigen
        try:
            from pdf_generator import vorlagen_info
            vi = vorlagen_info()
        except Exception:
            vi = {
                "modern": {"name": "Modern", "icon": "🎨", "premium": False},
                "klassisch": {"name": "Klassisch", "icon": "📄", "premium": False},
            }

        vh = ""
        for key, v in vi.items():
            pb = '<span class="bg">💎 PREMIUM</span>' if v.get("premium") else '<span style="color:var(--gn)">✓ FREE</span>'
            checked = ' checked' if key == "modern" else ''
            vh += (
                '<label style="display:block;margin:12px 0;padding:20px;'
                'background:rgba(10,14,26,0.5);border-radius:12px;cursor:pointer;'
                'border:1px solid var(--bd)">'
                '<input type="radio" name="vorlage" value="' + key + '"' + checked + '>'
                ' <span style="font-size:24px">' + v.get("icon", "📄") + '</span>'
                ' <strong style="font-size:16px;margin-left:10px">' + v.get("name", key) + '</strong>'
                ' ' + pb + '</label>'
            )

        c = (
            '<h1>📄 PDF-Lebenslauf Generator</h1>'
            '<p>Erstelle deinen professionellen Lebenslauf als PDF!</p>'
            + msg +
            '<div class="cd"><h3>📝 Vorlage waehlen</h3>'
            '<form method="POST">'
            + vh +
            '<button type="submit" class="bt b2" style="width:100%;margin-top:15px">'
            '📄 PDF erstellen & herunterladen</button>'
            '</form></div>'
            '<div class="al ai">💡 Fuell zuerst dein '
            '<a href="/lebenslauf">Profil</a> aus!</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ============================================================
    # TUTORIAL
    # ============================================================
    @app.route("/tutorial")
    def tutorial():
        if "user_id" not in session:
            return redirect("/login")
        c = (
            '<h1>📚 Tutorial & Hilfe</h1>'
            '<p>Lerne alle Features von XsiKOM kennen!</p>'
            '<div class="gr">'
            '<a href="/tutorial/start" style="text-decoration:none">'
            '<div class="sc"><div class="si">🚀</div><div class="sv">Start</div><div class="sl">Erste Schritte</div></div></a>'
            '<a href="/tutorial/aaliyah" style="text-decoration:none">'
            '<div class="sc"><div class="si">🤖</div><div class="sv">Aaliyah</div><div class="sl">KI-Beraterin</div></div></a>'
            '<a href="/tutorial/avinu" style="text-decoration:none">'
            '<div class="sc"><div class="si">⚡</div><div class="sv">AVINU</div><div class="sl">Job-Suche</div></div></a>'
            '<a href="/tutorial/xsi" style="text-decoration:none">'
            '<div class="sc"><div class="si">🤖</div><div class="sv">XSI</div><div class="sl">Auto-Bewerber</div></div></a>'
            '<a href="/tutorial/faq" style="text-decoration:none">'
            '<div class="sc"><div class="si">❓</div><div class="sv">FAQ</div><div class="sl">Fragen</div></div></a>'
            '<a href="/tutorial/tipps" style="text-decoration:none">'
            '<div class="sc"><div class="si">💡</div><div class="sv">Tipps</div><div class="sl">Profi-Tipps</div></div></a>'
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/start")
    def tutorial_start():
        if "user_id" not in session:
            return redirect("/login")
        c = (
            '<h1>🚀 Erste Schritte</h1>'
            '<div class="cd"><h3>Schritt 1: Profil ausfuellen</h3>'
            '<p>Gehe zu <a href="/lebenslauf">📝 Lebenslauf</a> und gib deine Daten ein.</p></div>'
            '<div class="cd"><h3>Schritt 2: Unterlagen hochladen</h3>'
            '<p>Gehe zu <a href="/uploads">📂 Dateien</a>: Lebenslauf (PDF), Zeugnisse, Foto.</p></div>'
            '<div class="cd"><h3>Schritt 3: Jobs suchen</h3>'
            '<p>Gehe zu <a href="/avinu">⚡ AVINU</a>: Branche, Beruf, Standort waehlen.</p></div>'
            '<div class="cd"><h3>Schritt 4: Auto-Bewerbung</h3>'
            '<p>Gehe zu <a href="/xsi/neu">🤖 XSI</a>: Firma + Position + Vorlage = Fertig!</p></div>'
            '<div class="al ao">🎉 In 5 Minuten startklar!</div>'
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/aaliyah")
    def tutorial_aaliyah():
        if "user_id" not in session:
            return redirect("/login")
        c = (
            '<h1>🤖 Aaliyah Tutorial</h1>'
            '<div class="cd"><h3>Was kann Aaliyah?</h3>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>Bewerbungstipps & Anschreiben</li>'
            '<li>Lebenslauf-Optimierung</li>'
            '<li>Interview-Vorbereitung</li>'
            '<li>Gehaltsverhandlung</li>'
            '<li>IT-Fachwissen (Netzwerk, TCP/IP, etc.)</li></ul></div>'
            '<div class="cd"><h3>Beispiel-Fragen</h3>'
            '<p style="color:var(--cy)">"Wie schreibe ich ein IT-Anschreiben?"</p>'
            '<p style="color:var(--cy)">"Wie verhandle ich Gehalt?"</p>'
            '<p style="color:var(--cy)">"Erklaere TCP/IP fuer mein Interview"</p></div>'
            '<a href="/aaliyah" class="bt b5">🤖 Aaliyah fragen</a> '
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/avinu")
    def tutorial_avinu():
        if "user_id" not in session:
            return redirect("/login")
        c = (
            '<h1>⚡ AVINU Tutorial</h1>'
            '<div class="cd"><h3>So funktioniert AVINU</h3>'
            '<ol style="padding-left:25px;line-height:2.2">'
            '<li>📂 Branche waehlen (14 verfuegbar)</li>'
            '<li>💼 Beruf eingeben (300+ Berufe mit Autocomplete)</li>'
            '<li>📍 Standort eingeben</li>'
            '<li>📏 Umkreis einstellen (5-200 km)</li>'
            '<li>🌍 Optional: International anklicken</li>'
            '<li>🚀 Jobs suchen klicken!</li></ol></div>'
            '<div class="cd"><h3>Nach der Suche</h3>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>⭐ Favorit markieren</li>'
            '<li>🤖 XSI: Direkt Auto-Bewerbung</li>'
            '<li>🔗 Original-Stellenanzeige ansehen</li>'
            '<li>Filter: Alle / Offen / Beworben / Favoriten</li></ul></div>'
            '<a href="/avinu" class="bt b1">⚡ AVINU starten</a> '
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/xsi")
    def tutorial_xsi():
        if "user_id" not in session:
            return redirect("/login")
        c = (
            '<h1>🤖 XSI Bot Tutorial</h1>'
            '<div class="cd"><h3>Vorbereitung</h3>'
            '<p>Bevor du XSI nutzt, lade hoch:</p>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>📄 Lebenslauf als PDF</li>'
            '<li>📜 Zeugnisse als PDF</li>'
            '<li>🏆 Zertifikate als PDF</li>'
            '<li>🖼️ Bewerbungsfoto</li></ul>'
            '<p>Und fuelle dein <a href="/lebenslauf">Profil</a> aus!</p></div>'
            '<div class="cd"><h3>Bewerbung erstellen</h3>'
            '<ol style="padding-left:25px;line-height:2.2">'
            '<li>Art waehlen (Job/Praktikum/Ausbildung/...)</li>'
            '<li>Firma eingeben</li>'
            '<li>Position eingeben</li>'
            '<li>E-Mail der Firma eingeben</li>'
            '<li>Sprache waehlen (DE/EN/FR)</li>'
            '<li>Vorlage waehlen</li>'
            '<li>📝 Entwurf ODER 🚀 Sofort senden!</li></ol></div>'
            '<div class="al ao">✅ XSI erstellt KI-Anschreiben + haengt ALLE Unterlagen automatisch an!</div>'
            '<a href="/xsi/neu" class="bt b2">🤖 XSI starten</a> '
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/faq")
    def tutorial_faq():
        if "user_id" not in session:
            return redirect("/login")
        faqs = [
            ("Ist XsiKOM kostenlos?",
             "Ja! Free: 5 Bewerbungen/Monat. Premium: 1.99 EUR unbegrenzt."),
            ("Wie funktioniert die KI?",
             "Llama 3.3 70B via Groq API. Generiert individuelle Anschreiben."),
            ("Sind meine Daten sicher?",
             "Ja! AES-256, 2FA, PBKDF2 SHA-512, DSGVO konform."),
            ("Kann ich Daten loeschen?",
             "Ja! Profil → Loeschen. 30 Tage Frist."),
            ("Welche Jobportale?",
             "Arbeitsagentur, Indeed (weltweit), StepStone, RemoteOK, Jobicy."),
            ("Welche Sprachen?",
             "Deutsch, Englisch, Franzoesisch fuer Anschreiben."),
            ("Welche Dateiformate?",
             "PDF, PNG, JPG, JPEG, GIF, BMP, WEBP. Bilder werden zu JPG konvertiert."),
            ("Wie Premium aktivieren?",
             "Admin-Code: XSIKOM-ADMIN-2026-PREMIUM oder Stripe Kreditkarte."),
            ("Funktioniert es auf Handy?",
             "Ja! PWA installierbar auf Android und iOS. Auch im Play Store!"),
            ("Was kostet Premium?",
             "1.99 EUR pro Monat. Jederzeit kuendbar."),
        ]
        c = '<h1>❓ FAQ - Haeufige Fragen</h1>'
        for f, a in faqs:
            c += '<div class="cd"><h3>❓ ' + f + '</h3><p>' + a + '</p></div>'
        c += (
            '<div class="al ai">💡 Noch Fragen? Frag '
            '<a href="/aaliyah">🤖 Aaliyah</a>!</div>'
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/tipps")
    def tutorial_tipps():
        if "user_id" not in session:
            return redirect("/login")
        tipps = [
            ("🎯 Profil komplett ausfuellen",
             "Je vollstaendiger dein Profil, desto besser die KI-Anschreiben!"),
            ("📄 Professionelle PDFs hochladen",
             "Gut formatierter Lebenslauf als PDF macht den besten Eindruck."),
            ("🖼️ Gutes Bewerbungsfoto",
             "Professionelles Foto erhoeht die Chancen. XSI haengt es automatisch an."),
            ("🔍 Suchbegriffe variieren",
             "Probiere verschiedene Begriffe: IT-Praktikum, Fachinformatiker, IT-Support..."),
            ("⭐ Favoriten nutzen",
             "Markiere interessante Jobs als Favorit. So verlierst du sie nicht."),
            ("🌍 International suchen",
             "Aktiviere 'International' fuer Remote-Jobs weltweit!"),
            ("📝 Erst Entwurf, dann Senden",
             "Erstelle zuerst einen Entwurf. Pruefe das Anschreiben. Dann sende."),
            ("🤖 Aaliyah vor Interview",
             "Frag Aaliyah nach Infos ueber die Firma und Interview-Fragen!"),
            ("📊 Bewerbungen tracken",
             "Behalte den Ueberblick im XSI Dashboard ueber alle Bewerbungen."),
            ("💎 Premium nutzen",
             "Mit Premium: Unbegrenzte Bewerbungen, alle Vorlagen, voller XSI Bot!"),
        ]
        c = '<h1>💡 Profi-Tipps</h1>'
        for t, b in tipps:
            c += '<div class="cd"><h3>' + t + '</h3><p>' + b + '</p></div>'
        c += '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        return render_template_string(H, content=c, user=session)

    # ============================================================
    # UPDATES
    # ============================================================
    @app.route("/updates")
    def updates_seite():
        if "user_id" not in session:
            return redirect("/login")
        try:
            from auto_update import update_status, changelog_laden, vorschlaege_laden, ist_update_faellig
            st = update_status()
            cl = changelog_laden(5)
            vs = vorschlaege_laden(5)
            faellig = ist_update_faellig()
        except Exception:
            st = {"version": "9.0", "letztes_update": "---",
                  "naechstes_update": "---", "offene_vorschlaege": 0}
            cl = []
            vs = []
            faellig = True

        cl_html = ""
        for c2 in cl:
            cl_html += (
                '<div class="ui"><div><strong>v' + str(c2[1]) + '</strong> - '
                + str(c2[2])[:16] + '<br><small style="color:var(--t3)">'
                + str(c2[3])[:200] + '...</small></div></div>'
            )
        if not cl_html:
            cl_html = '<p style="color:var(--t3)">Noch keine Updates</p>'

        vs_html = ""
        for v in vs:
            icon = "✅" if v[4] else "⏳"
            vs_html += (
                '<div class="ui"><div>' + icon + ' <strong>' + str(v[1]) + '</strong><br>'
                '<small style="color:var(--t3)">' + str(v[2])[:150] + '...</small></div></div>'
            )
        if not vs_html:
            vs_html = '<p style="color:var(--t3)">Keine Vorschlaege</p>'

        update_btn = ""
        if session.get("rolle") == "admin":
            update_btn = '<a href="/updates/jetzt" class="bt b2" style="width:100%;margin-top:15px">🤖 KI-Update starten!</a>'

        status_msg = ""
        if faellig:
            status_msg = '<div class="al ai">🤖 KI-Update faellig!</div>'
        else:
            status_msg = '<div class="al ao">✅ App ist aktuell!</div>'

        c = (
            '<h1>🔄 Updates & KI-Support</h1>'
            '<div class="gr">'
            '<div class="sc"><div class="si">📦</div><div class="sv">v' + st["version"] + '</div><div class="sl">Version</div></div>'
            '<div class="sc"><div class="si">📅</div><div class="sv">' + str(st["letztes_update"])[:10] + '</div><div class="sl">Letztes</div></div>'
            '<div class="sc"><div class="si">⏰</div><div class="sv">' + str(st["naechstes_update"]) + '</div><div class="sl">Naechstes</div></div>'
            '<div class="sc"><div class="si">💡</div><div class="sv">' + str(st["offene_vorschlaege"]) + '</div><div class="sl">Vorschlaege</div></div>'
            '</div>'
            + status_msg + update_btn +
            '<h2 style="margin-top:30px">📋 Changelog</h2>'
            '<div class="cd">' + cl_html + '</div>'
            '<h2>💡 KI-Vorschlaege</h2>'
            '<div class="cd">' + vs_html + '</div>'
            '<h2>📝 Feedback geben</h2>'
            '<div class="cd"><form method="POST" action="/updates/feedback">'
            '<select name="typ" required>'
            '<option value="bug">🐛 Bug melden</option>'
            '<option value="feature">✨ Feature-Wunsch</option>'
            '<option value="lob">👍 Lob</option>'
            '<option value="kritik">👎 Kritik</option></select>'
            '<textarea name="nachricht" rows="4" placeholder="Dein Feedback..." required></textarea>'
            '<select name="bewertung">'
            '<option value="5">⭐⭐⭐⭐⭐ Sehr gut</option>'
            '<option value="4">⭐⭐⭐⭐ Gut</option>'
            '<option value="3">⭐⭐⭐ Mittel</option>'
            '<option value="2">⭐⭐ Schlecht</option>'
            '<option value="1">⭐ Sehr schlecht</option></select>'
            '<button type="submit" class="bt b2" style="width:100%">📤 Feedback senden</button>'
            '</form></div>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/updates/jetzt")
    def update_jetzt():
        if "user_id" not in session:
            return redirect("/login")
        if session.get("rolle") != "admin":
            return redirect("/updates")
        try:
            from auto_update import monatliches_update
            ergebnisse = monatliches_update()
            details = ""
            for titel, inhalt in ergebnisse:
                details += (
                    '<div class="cd"><h3>' + titel + '</h3>'
                    '<p>' + str(inhalt)[:500].replace("\n", "<br>") + '</p></div>'
                )
            c = (
                '<h1>🤖 KI-Update fertig!</h1>'
                '<div class="al ao">✅ ' + str(len(ergebnisse)) + ' Bereiche analysiert!</div>'
                + details +
                '<a href="/updates" class="bt b1">← Zurueck</a>'
            )
        except Exception as e:
            c = (
                '<h1>❌ Update Fehler</h1>'
                '<div class="al ae">' + str(e)[:200] + '</div>'
                '<a href="/updates" class="bt b1">← Zurueck</a>'
            )
        return render_template_string(H, content=c, user=session)

    @app.route("/updates/feedback", methods=["POST"])
    def update_feedback():
        if "user_id" not in session:
            return redirect("/login")
        try:
            from auto_update import feedback_speichern
            typ = request.form.get("typ", "")
            nachricht = request.form.get("nachricht", "")
            bewertung = int(request.form.get("bewertung", 5))
            if typ and nachricht:
                feedback_speichern(session["user_id"], typ, nachricht, bewertung)
        except Exception:
            pass
        return redirect("/updates")

    # ============================================================
    # APP INSTALLIEREN
    # ============================================================
    @app.route("/install")
    def install():
        c = (
            '<h1>📱 App installieren</h1>'
            '<div class="cd"><h3>🤖 Android (Chrome)</h3>'
            '<ol style="padding-left:25px;line-height:2.5">'
            '<li>Oeffne Chrome auf dem Handy</li>'
            '<li>3-Punkte-Menue oben rechts</li>'
            '<li>"App installieren" waehlen</li>'
            '<li>"Installieren" bestaetigen</li>'
            '<li>✅ XsiKOM Icon auf dem Handy!</li></ol></div>'
            '<div class="cd"><h3>🍎 iPhone (Safari)</h3>'
            '<ol style="padding-left:25px;line-height:2.5">'
            '<li>Oeffne Safari (NICHT Chrome!)</li>'
            '<li>Teilen-Symbol ⬆️ tippen</li>'
            '<li>"Zum Home-Bildschirm" waehlen</li>'
            '<li>"Hinzufuegen" tippen</li>'
            '<li>✅ XsiKOM Icon auf dem iPhone!</li></ol></div>'
            '<div class="al ao">✅ Vorteile: App-Icon, Offline-Modus, wie native App!</div>'
        )
        return render_template_string(H, content=c,
            user=session if "user_id" in session else None)