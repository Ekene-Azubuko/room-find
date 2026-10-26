import re
import sqlite3

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from .db import get_db


api = Blueprint("api", __name__)


@api.get("/health")
def health():
    """Return the API's health status."""
    return jsonify({"status": "ok"}), 200


@api.post("/auth/register")
def register():
    """Create a user with a unique email and a securely hashed password."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json."}), 415

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a valid JSON object."}), 400

    email = data.get("email")
    password = data.get("password")
    if not isinstance(email, str):
        return jsonify({"error": "A valid email is required."}), 400

    # Normalize emails so case and surrounding whitespace cannot create duplicates.
    email = email.strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return jsonify({"error": "A valid email is required."}), 400
    if not isinstance(password, str) or not 8 <= len(password) <= 128:
        return jsonify({"error": "Password must contain 8 to 128 characters."}), 400

    password_hash = generate_password_hash(password)
    database = get_db()
    try:
        with database:
            result = database.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
    except sqlite3.IntegrityError:
        return jsonify({"error": "An account with this email already exists."}), 409

    return jsonify({"user": {"id": result.lastrowid, "email": email}}), 201
