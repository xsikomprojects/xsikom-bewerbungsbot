"""
Security Middleware: Rate-Limiting, CSRF, Secure Cookies, XSS-Schutz
Sprint 1 – XsiKOM v10.0
"""
import bleach
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect


# ─────────────────────────────────────────────────────────────────
# B1 – RATE LIMITING
# ─────────────────────────────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Strenge Limits für sensible Routen
LOGIN_LIMIT    = "5 per minute"
REGISTER_LIMIT = "3 per minute"
RESET_LIMIT    = "3 per hour"
KI_LIMIT       = "20 per minute"


# ─────────────────────────────────────────────────────────────────
# B2 – CSRF SCHUTZ
# ─────────────────────────────────────────────────────────────────

csrf = CSRFProtect()


# ─────────────────────────────────────────────────────────────────
# B4 – XSS SCHUTZ
# ─────────────────────────────────────────────────────────────────

# Erlaubte HTML-Tags für KI-Antworten
ERLAUBTE_TAGS = [
    "b", "strong", "i", "em", "u",
    "p", "br", "ul", "ol", "li",
    "h1", "h2", "h3", "h4",
    "code", "pre", "blockquote",
]

ERLAUBTE_ATTRIBUTE = {
    "*": ["style"],
}


def xss_clean(text: str) -> str:
    """
    Bereinigt KI-Output und User-Input gegen XSS.
    Behält Zeilenumbrüche als <br> bei.
    """
    if not text:
        return ""
    # Zeilenumbrüche zuerst schützen
    text = text.replace("\n", "<br>")
    # bleach bereinigt alles nicht Erlaubte
    return bleach.clean(
        text,
        tags=ERLAUBTE_TAGS,
        attributes=ERLAUBTE_ATTRIBUTE,
        strip=True,
    )


def xss_text(text: str) -> str:
    """
    Für reinen Text – KEIN HTML erlaubt.
    Für Formulareingaben (Firma, Position, etc.)
    """
    if not text:
        return ""
    return bleach.clean(text, tags=[], strip=True)


# ─────────────────────────────────────────────────────────────────
# INITIALISIERUNG
# ─────────────────────────────────────────────────────────────────

def init_security(app):
    """
    Initialisiert alle Security-Komponenten.
    Wird in webapp.py aufgerufen.
    """

    # ── B2: CSRF ─────────────────────────────────────────────────
    csrf.init_app(app)

    # ── B1: Rate Limiter ─────────────────────────────────────────
    limiter.init_app(app)

    # ── B3: Secure Cookies & Session ─────────────────────────────
    app.config.update(
        # Session-Cookie Sicherheit
        SESSION_COOKIE_HTTPONLY  = True,   # JS kann Cookie nicht lesen
        SESSION_COOKIE_SAMESITE  = "Lax",  # CSRF-Schutz
        SESSION_COOKIE_SECURE    = False,  # True wenn HTTPS (Produktion!)

        # CSRF-Token Cookie
        WTF_CSRF_TIME_LIMIT      = 3600,   # 1 Stunde
        WTF_CSRF_SSL_STRICT      = False,  # True in Produktion!

        # Sicherheits-Header
        SEND_FILE_MAX_AGE_DEFAULT = 0,
    )

    # ── B3: Security Headers ──────────────────────────────────────
    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"]  = "nosniff"
        response.headers["X-Frame-Options"]          = "SAMEORIGIN"
        response.headers["X-XSS-Protection"]         = "1; mode=block"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = (
            "geolocation=(), microphone=(), camera=()"
        )
        # CSP – Content Security Policy
        response.headers["Content-Security-Policy"]  = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )
        return response

    print("✅ Security Middleware aktiv")
    print("   B1: Rate-Limiting    ✅")
    print("   B2: CSRF-Schutz      ✅")
    print("   B3: Secure Cookies   ✅")
    print("   B4: XSS-Schutz       ✅")