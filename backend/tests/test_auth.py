import time

import pytest
from itsdangerous import TimestampSigner

from app import create_app
from app.extensions import db
from app.models import User


CREDENTIALS = {"email": "alex@example.com", "password": "long-password"}


def test_login_normalization_session_reset_and_safe_serialization(csrf_client):
    """Login normalizes identity, removes old state, and stores no credentials."""
    assert csrf_client.post("/api/auth/register", json=CREDENTIALS).status_code == 201
    with csrf_client.session_transaction() as session:
        session["old_state"] = "discard-me"
    response = csrf_client.post("/api/auth/login", json={**CREDENTIALS, "email": " ALEX@EXAMPLE.COM "})
    assert response.status_code == 200
    assert response.json == {"user": {"id": 1, "email": "alex@example.com"}}
    with csrf_client.session_transaction() as session:
        assert dict(session) == {"user_id": 1, "_permanent": True}
    for _ in range(2):
        assert csrf_client.get("/api/auth/me").json == response.json


@pytest.mark.parametrize("credentials", [
    {**CREDENTIALS, "password": "wrong-password"},
    {**CREDENTIALS, "email": "unknown@example.com"},
    {**CREDENTIALS, "password": None}])
def test_login_errors_are_indistinguishable(csrf_client, credentials):
    """Wrong passwords and missing accounts return the same safe error."""
    csrf_client.post("/api/auth/register", json=CREDENTIALS)
    response = csrf_client.post("/api/auth/login", json=credentials)
    assert response.status_code == 401
    assert response.json == {"error": "Invalid email or password."}
    assert csrf_client.get("/api/auth/me").status_code == 401


def test_missing_session(client):
    """Unauthenticated requests receive JSON instead of a redirect."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json == {"error": "Authentication required."}
    assert "Location" not in response.headers


def test_tampered_session(authenticated_client, app):
    """A modified cookie signature cannot authenticate a browser."""
    name = app.config["SESSION_COOKIE_NAME"]
    cookie = authenticated_client.get_cookie(name)
    authenticated_client.set_cookie(name, "x" + cookie.value[1:])
    response = authenticated_client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json == {"error": "Authentication required."}


def test_expired_session(csrf_client, app, monkeypatch):
    """A correctly signed cookie beyond its lifetime loses authentication."""
    csrf_client.post("/api/auth/register", json=CREDENTIALS)
    old_time = int(time.time()) - int(app.permanent_session_lifetime.total_seconds()) - 60
    def expired_timestamp(self):
        """Sign test cookies as though they were issued before the expiry window."""
        return old_time

    with monkeypatch.context() as patch:
        patch.setattr(TimestampSigner, "get_timestamp", expired_timestamp)
        token = csrf_client.get("/api/auth/csrf").json["csrf_token"]
        csrf_client.environ_base["HTTP_X_CSRF_TOKEN"] = token
        assert csrf_client.post("/api/auth/login", json=CREDENTIALS).status_code == 200
    response = csrf_client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json == {"error": "Authentication required."}


def test_logout_and_csrf_rotation(authenticated_client):
    """Logout clears the browser session and invalidates its old CSRF token."""
    old_token = authenticated_client.environ_base["HTTP_X_CSRF_TOKEN"]
    response = authenticated_client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json == {"message": "Logged out."}
    with authenticated_client.session_transaction() as session:
        assert dict(session) == {}
    assert authenticated_client.get("/api/auth/me").status_code == 401
    response = authenticated_client.post("/api/auth/login", json=CREDENTIALS)
    assert response.status_code == 400
    assert response.json == {"error": "A valid CSRF token is required."}
    new_token = authenticated_client.get("/api/auth/csrf").json["csrf_token"]
    assert new_token != old_token
    response = authenticated_client.post("/api/auth/login", json=CREDENTIALS,
                                         headers={"X-CSRF-Token": new_token})
    assert response.status_code == 200
    # Successful login clears the pre-login token too.
    response = authenticated_client.post("/api/auth/logout", headers={"X-CSRF-Token": new_token})
    assert response.status_code == 400
    assert response.json == {"error": "A valid CSRF token is required."}


@pytest.mark.parametrize("path", ["/api/auth/register", "/api/auth/login", "/api/auth/logout"])
@pytest.mark.parametrize("token", [None, "invalid-token", "☃"])
def test_modifications_require_csrf(client, path, token):
    """Missing and invalid tokens fail before any modifying auth action."""
    client.get("/api/auth/csrf")
    headers = {} if token is None else {"X-CSRF-Token": token}
    response = client.post(path, json=CREDENTIALS, headers=headers)
    assert response.status_code == 400
    assert response.json == {"error": "A valid CSRF token is required."}


def test_csrf_is_browser_bound(app, client):
    """A token obtained in one browser cannot authorize another browser."""
    token = client.get("/api/auth/csrf").json["csrf_token"]
    other = app.test_client()
    other.get("/api/auth/csrf")
    response = other.post("/api/auth/register", json=CREDENTIALS, headers={"X-CSRF-Token": token})
    assert response.status_code == 400
    assert response.json == {"error": "A valid CSRF token is required."}


def test_deleted_account_loses_access(authenticated_client, app):
    """A valid session for a deleted account cannot access protected routes."""
    with app.app_context():
        db.session.delete(db.session.get(User, 1))
        db.session.commit()
    response = authenticated_client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json == {"error": "Authentication required."}


def test_cookie_flags_and_secret_configuration(database_config, monkeypatch):
    """HTTPS cookies have secure attributes and startup requires an external secret."""
    application = create_app({**database_config, "SESSION_COOKIE_SECURE": True})
    response = application.test_client().get("/api/auth/csrf")
    cookie = response.headers["Set-Cookie"]
    assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert response.headers["Cache-Control"] == "no-store"
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({**database_config, "SECRET_KEY": None})
