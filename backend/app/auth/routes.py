from sqlalchemy.exc import IntegrityError

from flask import Blueprint, jsonify
from werkzeug.security import generate_password_hash

from ..extensions import db
from ..models import User
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

    user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        if getattr(error.orig, "sqlstate", None) != "23505":
            raise
        return jsonify({"error": "An account with this email already exists."}), 409

    return jsonify({"user": user.public_identity()}), 201
