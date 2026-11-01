from flask import Blueprint, jsonify

health = Blueprint("health", __name__)


@health.get("/health")
def check_health():
    """Return the API's health status."""
    return jsonify({"status": "ok"}), 200
