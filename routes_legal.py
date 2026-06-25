"""Legal Routes: Impressum, Datenschutz, AGB, Widerruf, Haftung"""
from flask import render_template_string, session
from webapp import H, CE


def register_legal_routes(app):

    @app.route("/impressum")
    def impressum():
        c = (
            '<h1>📜 Impressum</h1>'
            '<div class="lt">'
            '<h3>Angaben gemaess § 5 TMG</h3>'
            '<p><strong>XsiKOM DIGITAL Projects</strong><br>'
            'Komi Tevi<br>'
            'Am Koenigsfloss 12<br>'
            '55252 Mainz-Kastel<br>'
            'Deutschland</p>'

            '<h3>Kontakt</h3>'
            '<p>Telefon: +49 178 8977320<br>'
            'E-Mail: <a href="mailto:' + CE + '">' + CE + '</a><br>'
            'Web: https://xsikom.de</p>'

            '<h3>Verantwortlich nach § 55 Abs. 2 RStV</h3>'
            '<p>Komi Tevi (Anschrift wie oben)</p>'

            '<h3>Umsatzsteuer</h3>'
            '<p>Kleinunternehmer nach § 19 UStG.</p>'

            '<h3>EU-Streitschlichtung</h3>'
            '<p><a href="https://ec.europa.eu/consumers/odr/" target="_blank">'
            'https://ec.europa.eu/consumers/odr/</a></p>'
            '<p>Wir nehmen nicht an Streitbeilegungsverfahren teil.</p>'

            '<h3>Haftung fuer Inhalte</h3>'
            '<p>Als Diensteanbieter sind wir gemaess § 7 Abs.1 TMG fuer '
            'eigene Inhalte verantwortlich. Nach §§ 8 bis 10 TMG sind wir '
            'nicht verpflichtet, uebermittelte Informationen zu ueberwachen.</p>'

            '<h3>Haftung fuer Links</h3>'
            '<p>Unser Angebot enthaelt Links zu externen Webseiten. '
            'Fuer verlinkte Seiten ist der jeweilige Anbieter verantwortlich.</p>'

            '<h3>Urheberrecht</h3>'
            '<p>Inhalte und Werke unterliegen dem deutschen Urheberrecht.</p>'

            '<p style="margin-top:30px;padding:16px;background:rgba(10,14,26,0.5);'
            'border-radius:12px;font-size:12px">'
            '<strong>Stand:</strong> Juni 2026<br>'
            '<strong>© 2026 XsiKOM DIGITAL Projects - Komi Tevi</strong></p>'
            '</div>'
        )
        return render_template_string(H, content=c,
            user=session if "user_id" in session else None)

    @app.route("/datenschutz")
    def datenschutz():
        c = (
            '<h1>🔒 Datenschutzerklaerung (DSGVO)</h1>'
            '<div class="lt">'

            '<h3>1. Verantwortlicher</h3>'
            '<p><strong>XsiKOM DIGITAL Projects</strong><br>'
            'Komi Tevi<br>'
            'Am Koenigsfloss 12<br>'
            '55252 Mainz-Kastel<br>'
            'E-Mail: <a href="mailto:' + CE + '">' + CE + '</a></p>'

            '<h3>2. Erhobene Daten</h3>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li>Stammdaten (Name, E-Mail, Adresse)</li>'
            '<li>Zugangsdaten (verschluesseltes Passwort)</li>'
            '<li>Bewerbungsdaten und hochgeladene Dateien</li>'
            '<li>Nutzungsdaten (Login-Zeiten, anonymisiert)</li></ul>'

            '<h3>3. Zwecke der Verarbeitung</h3>'
            '<p>Bereitstellung des Bewerbungs-Service (Art. 6 Abs. 1 lit. b DSGVO).</p>'

            '<h3>4. Ihre Rechte (DSGVO)</h3>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li><strong>Auskunft</strong> (Art. 15 DSGVO)</li>'
            '<li><strong>Berichtigung</strong> (Art. 16 DSGVO)</li>'
            '<li><strong>Loeschung</strong> (Art. 17 DSGVO)</li>'
            '<li><strong>Einschraenkung</strong> (Art. 18 DSGVO)</li>'
            '<li><strong>Datenuebertragbarkeit</strong> (Art. 20 DSGVO)</li>'
            '<li><strong>Widerspruch</strong> (Art. 21 DSGVO)</li></ul>'
            '<p>Anfragen: <a href="mailto:' + CE + '">' + CE + '</a></p>'

            '<h3>5. KI-Verarbeitung (Aaliyah, AVINU, XSI)</h3>'
            '<p>Bei Nutzung der KI werden Eingaben an Groq Inc. (USA) uebermittelt. '
            'EU-US Data Privacy Framework. Keine personenbezogenen Daten werden '
            'dauerhaft bei Groq gespeichert.</p>'

            '<h3>6. Cookies</h3>'
            '<p>Nur technisch notwendige Cookies:</p>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li><strong>Session-Cookie:</strong> Fuer Login</li>'
            '<li><strong>CSRF-Token:</strong> Sicherheit</li></ul>'
            '<p>Keine Tracking-Cookies, keine Werbung.</p>'

            '<h3>7. Hosting</h3>'
            '<p>Render Services Inc., San Francisco, USA.<br>'
            'Standardvertragsklauseln der EU vereinbart.</p>'

            '<h3>8. Speicherdauer</h3>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li>Aktive Accounts: Dauer der Nutzung</li>'
            '<li>Inaktive Accounts: 12 Monate</li>'
            '<li>Logs: 30 Tage</li></ul>'

            '<h3>9. Datensicherheit</h3>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li>SSL/TLS Verschluesselung (HTTPS)</li>'
            '<li>AES-256 Datenverschluesselung</li>'
            '<li>PBKDF2 SHA-512 Passwort-Hashing</li>'
            '<li>2-Faktor-Authentifizierung (2FA)</li></ul>'

            '<h3>10. Aufsichtsbehoerde</h3>'
            '<p>Landesbeauftragter fuer den Datenschutz<br>'
            'Rheinland-Pfalz<br>'
            'Hintere Bleiche 34, 55116 Mainz</p>'

            '<p style="margin-top:30px;padding:16px;background:rgba(10,14,26,0.5);'
            'border-radius:12px;font-size:12px">'
            '<strong>Stand:</strong> Juni 2026<br>'
            '<strong>© 2026 XsiKOM DIGITAL Projects</strong></p>'
            '</div>'
        )
        return render_template_string(H, content=c,
            user=session if "user_id" in session else None)

    @app.route("/agb")
    def agb():
        c = (
            '<h1>📋 Allgemeine Geschaeftsbedingungen</h1>'
            '<div class="lt">'

            '<h3>§ 1 Geltungsbereich</h3>'
            '<p>Diese AGB gelten fuer alle Nutzer des XsiKOM-BewerbungsBOT.</p>'

            '<h3>§ 2 Vertragspartner</h3>'
            '<p><strong>XsiKOM DIGITAL Projects</strong><br>'
            'Komi Tevi<br>'
            'Am Koenigsfloss 12, 55252 Mainz-Kastel<br>'
            'E-Mail: <a href="mailto:' + CE + '">' + CE + '</a></p>'

            '<h3>§ 3 Leistungen</h3>'
            '<p><strong>Free-Version (kostenlos):</strong></p>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li>5 Bewerbungen pro Monat</li>'
            '<li>Aaliyah KI Beratung</li>'
            '<li>Basis Job-Suche</li>'
            '<li>Lebenslauf-Editor</li></ul>'
            '<p><strong>Premium (1.99 EUR/Monat):</strong></p>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li>UNBEGRENZTE Bewerbungen</li>'
            '<li>Alle Premium-Vorlagen</li>'
            '<li>XSI Auto-Sender</li>'
            '<li>Alle Jobportale + International</li></ul>'

            '<h3>§ 4 Preise und Zahlung</h3>'
            '<p>Kleinunternehmer nach § 19 UStG. '
            'Zahlung via Stripe (Kreditkarte, PayPal, SEPA).</p>'

            '<h3>§ 5 Widerrufsrecht</h3>'
            '<p>14 Tage fuer Verbraucher. '
            'Siehe <a href="/widerruf">Widerrufsbelehrung</a>.</p>'

            '<h3>§ 6 Kuendigung</h3>'
            '<p>Jederzeit zum Monatsende kuendbar.</p>'

            '<h3>§ 7 Haftung</h3>'
            '<p>Siehe <a href="/haftung">Haftungsausschluss</a>.</p>'
            '<p><strong>Wichtig:</strong> Keine Garantie fuer Erfolg von Bewerbungen. '
            'KI-Inhalte koennen Fehler enthalten.</p>'

            '<h3>§ 8 KI-Nutzung</h3>'
            '<p>Nutzer erkennen an:</p>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li>KI-Inhalte sind nicht fehlerfrei</li>'
            '<li>Inhalte muessen geprueft werden</li>'
            '<li>Nutzung auf eigene Verantwortung</li></ul>'

            '<h3>§ 9 Datenschutz</h3>'
            '<p>Siehe <a href="/datenschutz">Datenschutzerklaerung</a>.</p>'

            '<h3>§ 10 Gerichtsstand</h3>'
            '<p>Mainz, Deutschland. Deutsches Recht.</p>'

            '<p style="margin-top:30px;padding:16px;background:rgba(10,14,26,0.5);'
            'border-radius:12px;font-size:12px">'
            '<strong>Stand:</strong> Juni 2026<br>'
            '<strong>© 2026 XsiKOM DIGITAL Projects</strong></p>'
            '</div>'
        )
        return render_template_string(H, content=c,
            user=session if "user_id" in session else None)

    @app.route("/widerruf")
    def widerruf():
        c = (
            '<h1>↩️ Widerrufsbelehrung</h1>'
            '<div class="lt">'

            '<h3>Widerrufsrecht (§ 312g BGB)</h3>'
            '<p><strong>Sie haben das Recht, binnen 14 Tagen ohne Angabe '
            'von Gruenden diesen Vertrag zu widerrufen.</strong></p>'

            '<h3>Widerruf an</h3>'
            '<div style="padding:16px;background:rgba(10,14,26,0.5);border-radius:12px">'
            '<p><strong>XsiKOM DIGITAL Projects</strong><br>'
            'Komi Tevi<br>'
            'Am Koenigsfloss 12<br>'
            '55252 Mainz-Kastel<br>'
            'E-Mail: <a href="mailto:' + CE + '">' + CE + '</a></p></div>'

            '<h3>Folgen des Widerrufs</h3>'
            '<p>Rueckzahlung binnen 14 Tagen.</p>'

            '<h3>Firmenkunden (B2B)</h3>'
            '<p>Kein gesetzliches Widerrufsrecht. Es gelten unsere AGB.</p>'

            '<h3>Ausschluss</h3>'
            '<p>Widerrufsrecht erlischt bei digitalen Inhalten nach '
            'ausdruecklicher Zustimmung zur sofortigen Ausfuehrung.</p>'

            '<p style="margin-top:30px;padding:16px;background:rgba(10,14,26,0.5);'
            'border-radius:12px;font-size:12px">'
            '<strong>Stand:</strong> Juni 2026<br>'
            '<strong>© 2026 XsiKOM DIGITAL Projects</strong></p>'
            '</div>'
        )
        return render_template_string(H, content=c,
            user=session if "user_id" in session else None)

    @app.route("/haftung")
    def haftung():
        c = (
            '<h1>⚖️ Haftungsausschluss</h1>'
            '<div class="lt">'

            '<h3>1. Haftung fuer Inhalte</h3>'
            '<p>Inhalte mit Sorgfalt erstellt. Keine Gewaehr fuer '
            'Richtigkeit und Vollstaendigkeit.</p>'

            '<h3>2. KI-Generierte Inhalte (WICHTIG!)</h3>'
            '<div class="al aw">'
            '⚠️ <strong>Wichtiger Hinweis zur KI:</strong>'
            '<ul style="padding-left:25px;margin-top:10px">'
            '<li>KI-generierte Inhalte koennen <strong>fehlerhaft</strong> sein</li>'
            '<li>Pruefen Sie alle Inhalte vor Verwendung</li>'
            '<li>Keine Garantie fuer Erfolg von Bewerbungen</li>'
            '<li>KI-Empfehlungen ersetzen keine professionelle Beratung</li>'
            '<li>Nutzung auf eigenes Risiko</li></ul></div>'

            '<h3>3. Haftungsausschluss</h3>'
            '<p>XsiKOM DIGITAL Projects haftet nicht fuer:</p>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li>Direkte oder indirekte Schaeden</li>'
            '<li>Datenverlust durch technische Ausfaelle</li>'
            '<li>Erfolglose Bewerbungen</li>'
            '<li>Fehlerhafte KI-Empfehlungen</li>'
            '<li>Folgeschaeden jeglicher Art</li></ul>'

            '<h3>4. Haftungsbeschraenkung</h3>'
            '<p>Haftung nur bei Vorsatz und grober Fahrlaessigkeit.</p>'

            '<h3>5. Eigenverantwortung</h3>'
            '<ul style="padding-left:25px;line-height:2">'
            '<li>Korrekte Daten eingeben</li>'
            '<li>KI-Inhalte pruefen</li>'
            '<li>Bewerbungsfristen einhalten</li>'
            '<li>Backups erstellen</li></ul>'

            '<h3>6. Anwendbares Recht</h3>'
            '<p>Deutsches Recht. Gerichtsstand: Mainz.</p>'

            '<h3>Kontakt</h3>'
            '<p>E-Mail: <a href="mailto:' + CE + '">' + CE + '</a></p>'

            '<p style="margin-top:30px;padding:16px;background:rgba(10,14,26,0.5);'
            'border-radius:12px;font-size:12px">'
            '<strong>Stand:</strong> Juni 2026<br>'
            '<strong>© 2026 XsiKOM DIGITAL Projects</strong></p>'
            '</div>'
        )
        return render_template_string(H, content=c,
            user=session if "user_id" in session else None)