"""Health check, used by deployment checks and the load balancer (if any)."""
import socket

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from ..extensions import db

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return jsonify({
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "storage": current_app.config["STORAGE_BACKEND"],
        # Shows which server answered: useful evidence when several instances run.
        "server": socket.gethostname(),
    }), (200 if db_ok else 503)
