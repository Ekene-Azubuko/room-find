from functools import wraps
import secrets

from flask import g, request, session
from werkzeug.exceptions import BadRequest, Unauthorized

from ..extensions import db
from ..models import User


def csrf_token():
    """Create a random token bound to the current signed browser session."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def protect_csrf():
    """Require a matching session token on every routed modifying request."""
    if request.method in {"GET", "HEAD", "OPTIONS"} or request.endpoint is None:
        return
    expected = session.get("csrf_token")
    supplied = request.headers.get("X-CSRF-Token", "")
    if not isinstance(expected, str) or not secrets.compare_digest(expected.encode(), supplied.encode()):
        raise BadRequest("A valid CSRF token is required.")


def login_required(view):
    """Load the authenticated user or return a JSON authentication error."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        """Resolve the session identity before calling a protected route."""
        user_id = session.get("user_id")
        user = db.session.get(User, user_id) if type(user_id) is int else None
        if user is None:
            session.clear()
            raise Unauthorized("Authentication required.")
        g.user = user
        return view(*args, **kwargs)
    return wrapped
