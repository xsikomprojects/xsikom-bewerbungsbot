"""
XsiKOM-BewerbungsBOT v10.0 MODULAR
Template und Funktionen sind in shared.py!
"""
from dotenv import load_dotenv
load_dotenv()
import os
import secrets
import stripe
from shared import dbi, aa, GK, H, DB, hp, ki, pl
from datetime import timedelta
from flask import Flask, send_from_directory, make_response
from security_middleware import init_security


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(hours=2)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

# ── Security initialisieren ───────────────────────────────────────
init_security(app)


# ── Routes registrieren ───────────────────────────────────────────
from routes_auth   import register_auth_routes
from routes_main   import register_main_routes
from routes_bots   import register_bot_routes
from routes_profil import register_profil_routes
from routes_legal  import register_legal_routes
from routes_extra  import register_extra_routes

register_auth_routes(app)
register_main_routes(app)
register_bot_routes(app)
register_profil_routes(app)
register_legal_routes(app)
register_extra_routes(app)


# ── PWA & Static ──────────────────────────────────────────────────
@app.route("/manifest.json")
def manifest():
    return send_from_directory(
        ".", "manifest.json", mimetype="application/json"
    )


@app.route("/sw.js")
def service_worker():
    r = make_response(
        send_from_directory(
            ".", "sw.js", mimetype="application/javascript"
        )
    )
    r.headers["Service-Worker-Allowed"] = "/"
    return r


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


@app.route("/.well-known/assetlinks.json")
def assetlinks():
    return send_from_directory(
        ".well-known", "assetlinks.json",
        mimetype="application/json"
    )


# ── Init ──────────────────────────────────────────────────────────
dbi()
aa()

if __name__ == "__main__":
    print("=" * 60)
    print("  XsiKOM v10.0 MODULAR + SECURE")
    print("  KI:", "ONLINE" if GK else "OFFLINE")
    print("  URL: http://localhost:5000")
    print("=" * 60)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
