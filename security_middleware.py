"""
Security Middleware: Rate-Limiting, CSRF, Secure Cookies, XSS-Schutz
Sprint 1 – XsiKOM v10.0
"""
import os
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


# ─────────────────────────────────────────────────────────────────
# B2 – CSRF SCHUTZ
# ─────────────────────────────────────────────────────────────────

csrf = CSRFProtect()


# ─────────────────────────────────────────────────────────────────
# B4 – XSS SCHUTZ
# ─────────────────────────────────────────────────────────────────

ERLAUBTE_TAGS = [
    "b", "strong", "i", "em", "u",
    "p", "br", "ul", "ol", "li",
    "h1", "h2", "h3", "h4",
    "code", "pre", "blockquote",
]

ERLAUBTE_ATTRIBUTE = {"*": ["style"]}


def xss_clean(text: str) -> str:
    """Bereinigt KI-Output gegen XSS."""
    if not text:
        return ""
    text = text.replace("\n", "<br>")
    return bleach.clean(
        text,
        tags=ERLAUBTE_TAGS,
        attributes=ERLAUBTE_ATTRIBUTE,
        strip=True,
    )


def xss_text(text: str) -> str:
    """Für reinen Text – kein HTML erlaubt."""
    if not text:
        return ""
    return bleach.clean(text, tags=[], strip=True)


# ─────────────────────────────────────────────────────────────────
# INITIALISIERUNG
# ─────────────────────────────────────────────────────────────────

def init_security(app):
    """Initialisiert alle Security-Komponenten."""

    # B2: CSRF
    csrf.init_app(app)

    # B1: Rate Limiter
    limiter.init_app(app)

    # B3: Secure Cookies
    IS_PROD = os.environ.get("RENDER")

    app.config.update(
        SESSION_COOKIE_HTTPONLY   = True,
        SESSION_COOKIE_SAMESITE   = "Lax",
        SESSION_COOKIE_SECURE     = bool(IS_PROD),
        WTF_CSRF_TIME_LIMIT       = 3600,
        WTF_CSRF_SSL_STRICT       = False,
        SEND_FILE_MAX_AGE_DEFAULT = 0,
    )

    # B3: Security Headers
    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"]         = "SAMEORIGIN"
        response.headers["X-XSS-Protection"]        = "1; mode=block"
        response.headers["Referrer-Policy"]          = (
            "strict-origin-when-cross-origin"
        )
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net "
            "https://api.qrserver.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: "
            "https://api.qrserver.com; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )
        return response

    print("✅ Security Middleware aktiv")
    print("   B1: Rate-Limiting    ✅")
    print("   B2: CSRF-Schutz      ✅")
    print("   B3: Secure Cookies   ✅")
    print("   B4: XSS-Schutz       ✅")