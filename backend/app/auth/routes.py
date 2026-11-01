import sqlite3

from flask import Blueprint, jsonify
from werkzeug.security import generate_password_hash

from ..db import get_db
from ..validation import json_object, normalize_email


auth = Blueprint("auth", __name__)


@auth.post("/register")
def register():
    """Create a user with a unique email and a securely hashed password."""
    data = json_object()
    email = normalize_email(data.get("email"))
    password = data.get("password")
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
