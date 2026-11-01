from sqlalchemy.exc import IntegrityError

from flask import Blueprint, g, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash

from .security import csrf_token, login_required

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


@auth.get("/csrf")
def get_csrf():
    """Return a token for subsequent modifying requests from this browser."""
    response = jsonify({"csrf_token": csrf_token()})
    response.headers["Cache-Control"] = "no-store"
    return response


@auth.post("/login")
def login():
    """Authenticate credentials and replace previous browser session state."""
    data = json_object()
    email = normalize_email(data.get("email"))
    password = data.get("password")
    user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if (not isinstance(password, str) or not 8 <= len(password) <= 128
            or user is None or not check_password_hash(user.password_hash, password)):
        return jsonify({"error": "Invalid email or password."}), 401
    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return jsonify({"user": user.public_identity()})


@auth.post("/logout")
@login_required
def logout():
    """Clear this browser's session and authenticated access."""
    session.clear()
    return jsonify({"message": "Logged out."})


@auth.get("/me")
@login_required
def me():
    """Return the current user's safe account identity."""
    return jsonify({"user": g.user.public_identity()})
