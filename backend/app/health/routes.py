from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import ServiceUnavailable

from ..extensions import db

health = Blueprint("health", __name__)


@health.get("/health")
def check_health():
    """Report readiness only when the configured PostgreSQL service is reachable."""
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        raise ServiceUnavailable("Database is not ready.") from None
    return jsonify({"status": "ok"}), 200
