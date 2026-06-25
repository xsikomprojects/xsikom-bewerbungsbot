"""
Extra Routes: Premium, PDF, Tutorial, Updates, Install, Landing
Alle Imports kommen aus shared.py – kein Import aus webapp.py!
"""
from flask import render_template_string, request, redirect, session, send_file
from shared import H, DB, CE, hp, pa, pl
import sqlite3
import stripe
import os


# ─────────────────────────────────────────────────────────────────
# HILFSFUNKTIONEN
# ─────────────────────────────────────────────────────────────────

def _login_required():
    """Gibt Redirect zurück wenn nicht eingeloggt, sonst None."""
    if "user_id" not in session:
        return redirect("/login")
    return None


def _user_or_none():
    """Gibt session zurück wenn eingeloggt, sonst None."""
    return session if "user_id" in session else None


def _kacheln(items):
    """
    Erstellt Kachel-Grid HTML.
    items = [(url, icon, titel, untertitel), ...]
    """
    html = "".join(
        f'<a href="{url}" style="text-decoration:none">'
        f'<div class="sc">'
        f'<div class="si">{icon}</div>'
        f'<div class="sv">{titel}</div>'
        f'<div class="sl">{sub}</div>'
        f'</div></a>'
        for url, icon, titel, sub in items
    )
    return '<div class="gr">' + html + '</div>'


# ─────────────────────────────────────────────────────────────────
# ROUTE-REGISTRIERUNG
# ─────────────────────────────────────────────────────────────────

def register_extra_routes(app):

    # ════════════════════════════════════════════════════════════
    # LANDING PAGE
    # ════════════════════════════════════════════════════════════

    @app.route("/landing")
    def landing():
        c = (
            # ── Hero ─────────────────────────────────────────────
            '<section style="text-align:center;padding:40px 0 20px">'
            '<h1>Bewerben ohne Stress –<br>'
            'mit KI, Jobsuche und Lebenslauf in einer App.</h1>'
            '<p style="font-size:18px;max-width:850px;'
            'margin:0 auto 25px;color:var(--t2)">'
            'XsiKOM hilft dir, Jobs zu finden, Bewerbungen schneller '
            'zu schreiben und professioneller aufzutreten. '
            'Fuer Praktikum, Ausbildung, Studium und Karrierewechsel.'
            '</p>'
            '<div style="display:flex;gap:15px;'
            'justify-content:center;flex-wrap:wrap">'
            '<a href="/register" class="bt b2">🚀 Kostenlos starten</a>'
            '<a href="/premium" class="bt b1">💎 Premium entdecken</a>'
            '<a href="/install" class="bt b5">📱 App installieren</a>'
            '</div>'
            '</section>'

            # ── Vertrauenszeile ───────────────────────────────────
            '<div class="cd" style="text-align:center;margin:20px 0">'
            '<p style="font-size:16px">'
            '<strong>3 KI-Bots</strong> · '
            '<strong>Jobs weltweit</strong> · '
            '<strong>Lebenslauf-Generator</strong> · '
            '<strong>Kostenloser Start</strong>'
            '</p>'
            '</div>'

            # ── Warum XsiKOM ──────────────────────────────────────
            '<h2 style="margin-top:40px">🤖 Warum XsiKOM?</h2>'
            '<div class="gr">'

            '<div class="cd">'
            '<h3>🤖 Aaliyah</h3>'
            '<p>Deine KI-Beraterin fuer Anschreiben, '
            'Lebenslauf, Interview und Karrierefragen.</p>'
            '<a href="/aaliyah" class="bt b5" '
            'style="padding:8px 18px;font-size:13px">'
            'Jetzt fragen</a>'
            '</div>'

            '<div class="cd">'
            '<h3>⚡ AVINU</h3>'
            '<p>Finde passende Jobs nach Branche, '
            'Beruf, Standort und sogar international.</p>'
            '<a href="/avinu" class="bt b1" '
            'style="padding:8px 18px;font-size:13px">'
            'Jobs suchen</a>'
            '</div>'

            '<div class="cd">'
            '<h3>🤖 XSI</h3>'
            '<p>Erstelle Bewerbungen schneller mit KI, '
            'Vorlagen und strukturiertem Workflow.</p>'
            '<a href="/xsi" class="bt b2" '
            'style="padding:8px 18px;font-size:13px">'
            'Bewerben</a>'
            '</div>'

            '</div>'

            # ── Fuer wen ──────────────────────────────────────────
            '<h2 style="margin-top:40px">👥 Fuer wen ist XsiKOM?</h2>'
            '<div class="gr">'

            '<div class="sc">'
            '<div class="si">🎓</div>'
            '<div class="sv">Schueler</div>'
            '<div class="sl">Praktikum & Ausbildung</div>'
            '</div>'

            '<div class="sc">'
            '<div class="si">🧑‍💻</div>'
            '<div class="sv">Studenten</div>'
            '<div class="sl">Werkstudent & Berufseinstieg</div>'
            '</div>'

            '<div class="sc">'
            '<div class="si">🚀</div>'
            '<div class="sv">Wechsler</div>'
            '<div class="sl">Neustart & Karrierewechsel</div>'
            '</div>'

            '</div>'

            # ── So funktionierts ──────────────────────────────────
            '<h2 style="margin-top:40px">⚡ So funktionierts</h2>'
            '<div class="gr">'

            '<div class="cd" style="text-align:center">'
            '<div style="font-size:40px">1️⃣</div>'
            '<h3>Profil ausfuellen</h3>'
            '<p>Hinterlege deine Daten einmal zentral in XsiKOM.</p>'
            '</div>'

            '<div class="cd" style="text-align:center">'
            '<div style="font-size:40px">2️⃣</div>'
            '<h3>Jobs suchen</h3>'
            '<p>Nutze AVINU fuer passende Stellen '
            'lokal oder international.</p>'
            '</div>'

            '<div class="cd" style="text-align:center">'
            '<div style="font-size:40px">3️⃣</div>'
            '<h3>Bewerbung erstellen</h3>'
            '<p>XSI hilft dir mit KI und Vorlagen '
            'beim Anschreiben.</p>'
            '</div>'

            '<div class="cd" style="text-align:center">'
            '<div style="font-size:40px">4️⃣</div>'
            '<h3>Durchstarten</h3>'
            '<p>Mehr Uebersicht, weniger Stress, '
            'schnellere Bewerbungen.</p>'
            '</div>'

            '</div>'

            # ── Pricing ───────────────────────────────────────────
            '<h2 style="margin-top:40px">💰 Free oder Premium</h2>'
            '<div class="gr">'

            '<div class="cd">'
            '<h3>🆓 Free</h3>'
            '<p style="color:var(--gn);font-size:22px;font-weight:700">'
            '0 EUR</p>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>✅ KI-Beratung</li>'
            '<li>✅ Basis Jobsuche</li>'
            '<li>✅ Lebenslauf-Editor</li>'
            '<li>✅ Kostenlos nutzbar</li>'
            '<li>❌ Alle Vorlagen</li>'
            '<li>❌ Internationale Jobs</li>'
            '</ul>'
            '<a href="/register" class="bt b1" '
            'style="width:100%;margin-top:15px">'
            '🚀 Kostenlos starten</a>'
            '</div>'

            '<div class="cd" style="border:2px solid var(--yl)">'
            '<span class="bg">⭐ BELIEBT</span>'
            '<h3 style="margin-top:10px">💎 Premium</h3>'
            '<p style="color:var(--yl);font-size:22px;font-weight:700">'
            '1.99 EUR/Monat</p>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>✅ Alles aus Free</li>'
            '<li>✅ Alle Vorlagen</li>'
            '<li>✅ Mehr Automatisierung</li>'
            '<li>✅ Internationale Jobs</li>'
            '<li>✅ Erweiterte Funktionen</li>'
            '<li>✅ PDF-Generator</li>'
            '</ul>'
            '<a href="/premium" class="bt b3" '
            'style="width:100%;margin-top:15px">'
            '💎 Premium holen</a>'
            '</div>'

            '</div>'

            # ── Sicherheit ────────────────────────────────────────
            '<div class="cd" style="margin-top:30px">'
            '<h3>🔒 Sicherheit & Datenschutz</h3>'
            '<div class="gr">'
            '<p>✅ CSRF-Schutz</p>'
            '<p>✅ Rate-Limiting</p>'
            '<p>✅ XSS-Schutz</p>'
            '<p>✅ Sichere Sessions</p>'
            '<p>✅ DSGVO-orientiert</p>'
            '<p>✅ AES-256</p>'
            '</div>'
            '</div>'

            # ── Final CTA ─────────────────────────────────────────
            '<div class="cd" style="text-align:center;margin-top:40px;'
            'background:linear-gradient(135deg,rgba(0,217,255,0.1),'
            'rgba(139,92,246,0.1));border:1px solid var(--cy)">'
            '<h2>Dein naechster Job wartet nicht.</h2>'
            '<p style="font-size:16px;margin-bottom:25px">'
            'Starte jetzt mit XsiKOM und bring deine '
            'Bewerbung aufs naechste Level.'
            '</p>'
            '<div style="display:flex;gap:15px;'
            'justify-content:center;flex-wrap:wrap">'
            '<a href="/register" class="bt b2">'
            '🚀 Jetzt kostenlos starten</a>'
            '<a href="/tutorial" class="bt b1">'
            '📚 Tutorial ansehen</a>'
            '</div>'
            '</div>'
        )
        return render_template_string(H, content=c, user=_user_or_none())

    # ════════════════════════════════════════════════════════════
    # PREMIUM
    # ════════════════════════════════════════════════════════════

    @app.route("/premium")
    def premium():
        c = (
            '<h1>💎 Premium</h1>'
            '<div class="gr">'

            '<div class="cd">'
            '<h2>🆓 Free</h2>'
            '<h3>0 EUR</h3>'
            '<ul style="list-style:none;padding:0;line-height:2.2">'
            '<li>✓ 5 Bewerbungen/Monat</li>'
            '<li>✓ Aaliyah KI Chat</li>'
            '<li>✓ Basis Job-Suche</li>'
            '<li>✓ Lebenslauf-Editor</li>'
            '<li>✗ Premium-Vorlagen</li>'
            '<li>✗ XSI Auto-Sender</li>'
            '<li>✗ International</li>'
            '</ul>'
            '<button class="bt b1" style="width:100%">Aktuell</button>'
            '</div>'

            '<div class="cd" style="border:2px solid var(--yl)">'
            '<span class="bg">⭐ BELIEBT</span>'
            '<h2 style="margin-top:10px">💎 Premium</h2>'
            '<h3>1.99 EUR/Monat</h3>'
            '<ul style="list-style:none;padding:0;line-height:2.2">'
            '<li>✓ UNBEGRENZTE Bewerbungen</li>'
            '<li>✓ Alle 3 KI-Bots</li>'
            '<li>✓ 8 Premium-Vorlagen</li>'
            '<li>✓ XSI Auto-Sender</li>'
            '<li>✓ Alle 10+ Jobportale</li>'
            '<li>✓ International</li>'
            '<li>✓ PDF-Generator</li>'
            '<li>✓ Werbefrei</li>'
            '</ul>'
            '<a href="/aktivieren" class="bt b3" style="width:100%">'
            '🚀 Upgrade</a>'
            '</div>'

            '</div>'
        )
        return render_template_string(H, content=c, user=_user_or_none())

    # ════════════════════════════════════════════════════════════
    # PREMIUM AKTIVIEREN
    # ════════════════════════════════════════════════════════════

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
                    '<div class="al ao">✅ Lebenslang Premium!</div>'
                    '<a href="/dashboard" class="bt b1">🏠 Dashboard</a>'
                )
                return render_template_string(H, content=c, user=session)
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
            '<div class="cd">'
            '<h3>🔑 Mit Code</h3>'
            '<form method="POST">'
            '<input type="text" name="code" '
            'placeholder="Premium-Code" required>'
            '<button type="submit" class="bt b2" style="width:100%">'
            '🚀 Aktivieren</button>'
            '</form></div>'
            '<div class="cd">'
            '<h3>💳 Mit Zahlung</h3>'
            + (stripe_btn if stripe_btn else
               '<p style="color:var(--t3)">Stripe wird konfiguriert...</p>') +
            '</div>'
            '<div class="al ai">'
            '💡 Admin-Code: XSIKOM-ADMIN-2026-PREMIUM'
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # STRIPE CHECKOUT
    # ════════════════════════════════════════════════════════════

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
                    base
                    + "/stripe-success"
                    + "?session_id={CHECKOUT_SESSION_ID}"
                ),
                cancel_url=base + "/premium",
                metadata={"user_id": str(session["user_id"])},
            )
            return redirect(cs.url, code=303)

        except Exception as e:
            c = (
                '<h1>❌ Stripe Fehler</h1>'
                '<div class="al ae">' + str(e)[:200] + '</div>'
                '<a href="/premium" class="bt b1">← Zurueck</a>'
            )
            return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # STRIPE SUCCESS
    # ════════════════════════════════════════════════════════════

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

    # ════════════════════════════════════════════════════════════
    # PDF LEBENSLAUF GENERATOR
    # ════════════════════════════════════════════════════════════

    @app.route("/pdf-lebenslauf", methods=["GET", "POST"])
    def pdf_lebenslauf():
        r = _login_required()
        if r: return r

        uid = session["user_id"]
        msg = ""

        if request.method == "POST":
            vorlage = request.form.get("vorlage", "modern")
            try:
                from pdf_generator import lebenslauf_generieren, vorlagen_info
                vi = vorlagen_info()
                v  = vi.get(vorlage, {})

                if v.get("premium") and not session.get("premium"):
                    msg = (
                        '<div class="al aw">⚠️ Premium-Vorlage! '
                        '<a href="/premium">💎 Upgrade</a></div>'
                    )
                else:
                    result = lebenslauf_generieren(uid, vorlage)
                    if result:
                        pfad, name = result
                        return send_file(
                            pfad,
                            as_attachment=True,
                            download_name=name
                        )
                    else:
                        msg = (
                            '<div class="al ae">❌ Profil ausfuellen! '
                            '<a href="/lebenslauf">📝 Lebenslauf</a></div>'
                        )
            except Exception as e:
                msg = '<div class="al ae">❌ ' + str(e)[:100] + '</div>'

        try:
            from pdf_generator import vorlagen_info
            vi = vorlagen_info()
        except Exception:
            vi = {
                "modern":    {"name": "Modern",    "icon": "🎨", "premium": False},
                "klassisch": {"name": "Klassisch", "icon": "📄", "premium": False},
            }

        vh = ""
        for key, v in vi.items():
            pb      = (
                '<span class="bg">💎 PREMIUM</span>'
                if v.get("premium") else
                '<span style="color:var(--gn)">✓ FREE</span>'
            )
            checked = " checked" if key == "modern" else ""
            vh += (
                '<label style="display:block;margin:12px 0;padding:20px;'
                'background:rgba(10,14,26,0.5);border-radius:12px;'
                'cursor:pointer;border:1px solid var(--bd)">'
                f'<input type="radio" name="vorlage" '
                f'value="{key}"{checked}>'
                f' <span style="font-size:24px">{v.get("icon","📄")}</span>'
                f' <strong style="font-size:16px;margin-left:10px">'
                f'{v.get("name", key)}</strong>'
                f' {pb}'
                '</label>'
            )

        c = (
            '<h1>📄 PDF-Lebenslauf Generator</h1>'
            '<p>Erstelle deinen professionellen Lebenslauf als PDF!</p>'
            + msg +
            '<div class="cd">'
            '<h3>📝 Vorlage waehlen</h3>'
            '<form method="POST">'
            + vh +
            '<button type="submit" class="bt b2" '
            'style="width:100%;margin-top:15px">'
            '📄 PDF erstellen & herunterladen</button>'
            '</form></div>'
            '<div class="al ai">'
            '💡 Fuell zuerst dein <a href="/lebenslauf">Profil</a> aus!'
            '</div>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # TUTORIAL
    # ════════════════════════════════════════════════════════════

    @app.route("/tutorial")
    def tutorial():
        r = _login_required()
        if r: return r

        c = (
            '<h1>📚 Tutorial & Hilfe</h1>'
            '<p>Lerne alle Features von XsiKOM kennen!</p>'
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

        schritte = [
            ("Schritt 1: Profil ausfuellen",
             'Gehe zu <a href="/lebenslauf">📝 Lebenslauf</a> '
             'und gib deine Daten ein.'),
            ("Schritt 2: Unterlagen hochladen",
             'Gehe zu <a href="/uploads">📂 Dateien</a>: '
             'Lebenslauf (PDF), Zeugnisse, Foto.'),
            ("Schritt 3: Jobs suchen",
             'Gehe zu <a href="/avinu">⚡ AVINU</a>: '
             'Branche, Beruf, Standort waehlen.'),
            ("Schritt 4: Auto-Bewerbung",
             'Gehe zu <a href="/xsi/neu">🤖 XSI</a>: '
             'Firma + Position + Vorlage = Fertig!'),
        ]
        c = (
            '<h1>🚀 Erste Schritte</h1>'
            + "".join(
                f'<div class="cd"><h3>{t}</h3><p>{b}</p></div>'
                for t, b in schritte
            )
            + '<div class="al ao">🎉 In 5 Minuten startklar!</div>'
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/aaliyah")
    def tutorial_aaliyah():
        r = _login_required()
        if r: return r

        c = (
            '<h1>🤖 Aaliyah Tutorial</h1>'
            '<div class="cd"><h3>Was kann Aaliyah?</h3>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>Bewerbungstipps & Anschreiben</li>'
            '<li>Lebenslauf-Optimierung</li>'
            '<li>Interview-Vorbereitung</li>'
            '<li>Gehaltsverhandlung</li>'
            '<li>IT-Fachwissen (Netzwerk, TCP/IP, etc.)</li>'
            '</ul></div>'
            '<div class="cd"><h3>Beispiel-Fragen</h3>'
            '<p style="color:var(--cy)">"Wie schreibe ich ein IT-Anschreiben?"</p>'
            '<p style="color:var(--cy)">"Wie verhandle ich Gehalt?"</p>'
            '<p style="color:var(--cy)">"Erklaere TCP/IP fuer mein Interview"</p>'
            '</div>'
            '<a href="/aaliyah" class="bt b5">🤖 Aaliyah fragen</a> '
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/avinu")
    def tutorial_avinu():
        r = _login_required()
        if r: return r

        c = (
            '<h1>⚡ AVINU Tutorial</h1>'
            '<div class="cd"><h3>So funktioniert AVINU</h3>'
            '<ol style="padding-left:25px;line-height:2.2">'
            '<li>📂 Branche waehlen (14 verfuegbar)</li>'
            '<li>💼 Beruf eingeben (300+ mit Autocomplete)</li>'
            '<li>📍 Standort eingeben</li>'
            '<li>📏 Umkreis einstellen (5-200 km)</li>'
            '<li>🌍 Optional: International anklicken</li>'
            '<li>🚀 Jobs suchen klicken!</li>'
            '</ol></div>'
            '<div class="cd"><h3>Nach der Suche</h3>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>⭐ Favorit markieren</li>'
            '<li>🤖 XSI: Direkt Auto-Bewerbung</li>'
            '<li>🔗 Original-Stellenanzeige ansehen</li>'
            '<li>Filter: Alle / Offen / Beworben / Favoriten</li>'
            '</ul></div>'
            '<a href="/avinu" class="bt b1">⚡ AVINU starten</a> '
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/xsi")
    def tutorial_xsi():
        r = _login_required()
        if r: return r

        c = (
            '<h1>🤖 XSI Bot Tutorial</h1>'
            '<div class="cd"><h3>Vorbereitung</h3>'
            '<ul style="padding-left:25px;line-height:2.2">'
            '<li>📄 Lebenslauf als PDF</li>'
            '<li>📜 Zeugnisse als PDF</li>'
            '<li>🏆 Zertifikate als PDF</li>'
            '<li>🖼️ Bewerbungsfoto</li>'
            '</ul>'
            '<p>Und fuelle dein <a href="/lebenslauf">Profil</a> aus!</p>'
            '</div>'
            '<div class="cd"><h3>Bewerbung erstellen</h3>'
            '<ol style="padding-left:25px;line-height:2.2">'
            '<li>Art waehlen (Job/Praktikum/Ausbildung/...)</li>'
            '<li>Firma eingeben</li>'
            '<li>Position eingeben</li>'
            '<li>E-Mail der Firma eingeben</li>'
            '<li>Sprache waehlen (DE/EN/FR)</li>'
            '<li>Vorlage waehlen</li>'
            '<li>📝 Entwurf ODER 🚀 Sofort senden!</li>'
            '</ol></div>'
            '<div class="al ao">'
            '✅ XSI erstellt KI-Anschreiben + haengt '
            'ALLE Unterlagen automatisch an!'
            '</div>'
            '<a href="/xsi/neu" class="bt b2">🤖 XSI starten</a> '
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/faq")
    def tutorial_faq():
        r = _login_required()
        if r: return r

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
             "PDF, PNG, JPG, JPEG, GIF, BMP, WEBP. Bilder → JPG konvertiert."),
            ("Wie Premium aktivieren?",
             "Admin-Code: XSIKOM-ADMIN-2026-PREMIUM oder Stripe Kreditkarte."),
            ("Funktioniert es auf Handy?",
             "Ja! PWA installierbar auf Android und iOS. Auch im Play Store!"),
            ("Was kostet Premium?",
             "1.99 EUR pro Monat. Jederzeit kuendbar."),
        ]

        c = (
            '<h1>❓ FAQ - Haeufige Fragen</h1>'
            + "".join(
                f'<div class="cd"><h3>❓ {f}</h3><p>{a}</p></div>'
                for f, a in faqs
            )
            + '<div class="al ai">'
            '💡 Noch Fragen? Frag <a href="/aaliyah">🤖 Aaliyah</a>!'
            '</div>'
            '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    @app.route("/tutorial/tipps")
    def tutorial_tipps():
        r = _login_required()
        if r: return r

        tipps = [
            ("🎯 Profil komplett ausfuellen",
             "Je vollstaendiger dein Profil, desto besser die KI-Anschreiben!"),
            ("📄 Professionelle PDFs hochladen",
             "Gut formatierter Lebenslauf als PDF macht den besten Eindruck."),
            ("🖼️ Gutes Bewerbungsfoto",
             "Professionelles Foto erhoeht die Chancen."),
            ("🔍 Suchbegriffe variieren",
             "Probiere: IT-Praktikum, Fachinformatiker, IT-Support..."),
            ("⭐ Favoriten nutzen",
             "Markiere interessante Jobs als Favorit."),
            ("🌍 International suchen",
             "Aktiviere 'International' fuer Remote-Jobs weltweit!"),
            ("📝 Erst Entwurf, dann Senden",
             "Erstelle zuerst einen Entwurf. Pruefe. Dann sende."),
            ("🤖 Aaliyah vor Interview",
             "Frag Aaliyah nach Infos ueber die Firma!"),
            ("📊 Bewerbungen tracken",
             "Behalte den Ueberblick im XSI Dashboard."),
            ("💎 Premium nutzen",
             "Mit Premium: Unbegrenzte Bewerbungen, alle Vorlagen!"),
        ]

        c = (
            '<h1>💡 Profi-Tipps</h1>'
            + "".join(
                f'<div class="cd"><h3>{t}</h3><p>{b}</p></div>'
                for t, b in tipps
            )
            + '<a href="/tutorial" class="bt b1">← Tutorial</a>'
        )
        return render_template_string(H, content=c, user=session)

    # ════════════════════════════════════════════════════════════
    # UPDATES
    # ════════════════════════════════════════════════════════════

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
            st      = {
                "version":            "10.0",
                "letztes_update":     "---",
                "naechstes_update":   "---",
                "offene_vorschlaege": 0,
            }
            cl      = []
            vs      = []
            faellig = True

        cl_html = "".join(
            '<div class="ui"><div>'
            f'<strong>v{c2[1]}</strong> – {str(c2[2])[:16]}'
            f'<br><small style="color:var(--t3)">'
            f'{str(c2[3])[:200]}...</small>'
            '</div></div>'
            for c2 in cl
        ) or '<p style="color:var(--t3)">Noch keine Updates</p>'

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
                '🤖 KI-Update starten!</a>'
            )

        status_msg = (
            '<div class="al ai">🤖 KI-Update faellig!</div>'
            if faellig else
            '<div class="al ao">✅ App ist aktuell!</div>'
        )

        c = (
            '<h1>🔄 Updates & KI-Support</h1>'
            '<div class="gr">'
            '<div class="sc"><div class="si">📦</div>'
            f'<div class="sv">v{st["version"]}</div>'
            '<div class="sl">Version</div></div>'
            '<div class="sc"><div class="si">📅</div>'
            f'<div class="sv">{str(st["letztes_update"])[:10]}</div>'
            '<div class="sl">Letztes</div></div>'
            '<div class="sc"><div class="si">⏰</div>'
            f'<div class="sv">{st["naechstes_update"]}</div>'
            '<div class="sl">Naechstes</div></div>'
            '<div class="sc"><div class="si">💡</div>'
            f'<div class="sv">{st["offene_vorschlaege"]}</div>'
            '<div class="sl">Vorschlaege</div></div>'
            '</div>'
            + status_msg
            + update_btn +
            '<h2 style="margin-top:30px">📋 Changelog</h2>'
            '<div class="cd">' + cl_html + '</div>'
            '<h2>💡 KI-Vorschlaege</h2>'
            '<div class="cd">' + vs_html + '</div>'
            '<h2>📝 Feedback geben</h2>'
            '<div class="cd">'
            '<form method="POST" action="/updates/feedback">'
            '<p>📋 Typ:</p>'
            '<select name="typ" required>'
            '<option value="bug">🐛 Bug melden</option>'
            '<option value="feature">✨ Feature-Wunsch</option>'
            '<option value="lob">👍 Lob</option>'
            '<option value="kritik">👎 Kritik</option>'
            '</select>'
            '<p>💬 Nachricht:</p>'
            '<textarea name="nachricht" rows="4" '
            'placeholder="Dein Feedback..." required></textarea>'
            '<p>⭐ Bewertung:</p>'
            '<select name="bewertung">'
            '<option value="5">⭐⭐⭐⭐⭐ Sehr gut</option>'
            '<option value="4">⭐⭐⭐⭐ Gut</option>'
            '<option value="3">⭐⭐⭐ Mittel</option>'
            '<option value="2">⭐⭐ Schlecht</option>'
            '<option value="1">⭐ Sehr schlecht</option>'
            '</select>'
            '<button type="submit" class="bt b2" style="width:100%">'
            '📤 Feedback senden</button>'
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
            details    = "".join(
                f'<div class="cd"><h3>{titel}</h3>'
                f'<p>{str(inhalt)[:500].replace(chr(10), "<br>")}</p></div>'
                for titel, inhalt in ergebnisse
            )
            c = (
                '<h1>🤖 KI-Update fertig!</h1>'
                '<div class="al ao">✅ '
                + str(len(ergebnisse))
                + ' Bereiche analysiert!</div>'
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
        r = _login_required()
        if r: return r

        try:
            from auto_update import feedback_speichern
            typ       = request.form.get("typ",       "")
            nachricht = request.form.get("nachricht",  "")
            bewertung = int(request.form.get("bewertung", 5))
            if typ and nachricht:
                feedback_speichern(
                    session["user_id"], typ, nachricht, bewertung
                )
        except Exception:
            pass
        return redirect("/updates")

    # ════════════════════════════════════════════════════════════
    # APP INSTALLIEREN (PWA)
    # ════════════════════════════════════════════════════════════

    @app.route("/install")
    def install():
        c = (
            '<h1>📱 App installieren</h1>'
            '<div class="cd">'
            '<h3>🤖 Android (Chrome)</h3>'
            '<ol style="padding-left:25px;line-height:2.5">'
            '<li>Oeffne Chrome auf dem Handy</li>'
            '<li>3-Punkte-Menue oben rechts</li>'
            '<li>"App installieren" waehlen</li>'
            '<li>"Installieren" bestaetigen</li>'
            '<li>✅ XsiKOM Icon auf dem Handy!</li>'
            '</ol></div>'
            '<div class="cd">'
            '<h3>🍎 iPhone (Safari)</h3>'
            '<ol style="padding-left:25px;line-height:2.5">'
            '<li>Oeffne Safari (NICHT Chrome!)</li>'
            '<li>Teilen-Symbol ⬆️ tippen</li>'
            '<li>"Zum Home-Bildschirm" waehlen</li>'
            '<li>"Hinzufuegen" tippen</li>'
            '<li>✅ XsiKOM Icon auf dem iPhone!</li>'
            '</ol></div>'
            '<div class="al ao">'
            '✅ Vorteile: App-Icon, Offline-Modus, wie native App!'
            '</div>'
        )
        return render_template_string(H, content=c, user=_user_or_none())