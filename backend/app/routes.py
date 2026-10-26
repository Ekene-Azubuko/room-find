from flask import Blueprint, jsonify


api = Blueprint("api", __name__)


@api.get("/health")
def health():
    """Return the API's health status."""
    return jsonify({"status": "ok"}), 200
