import pytest

from app import create_app
from app.extensions import db
from app.models import User, utc_now


def test_profile_read_update_persistence_and_noop(authenticated_client, database_config):
    """Profile edits persist across app instances and unchanged saves retain timestamps."""
    original = authenticated_client.get("/api/profile")
    assert original.status_code == 200
    assert original.json["profile"]["full_name"] is None
    response = authenticated_client.patch("/api/profile", json={"full_name": " Alex Smith ", "bio": "Hello"})
    assert response.status_code == 200
    saved = response.json["profile"]
    assert saved["full_name"] == "Alex Smith"
    assert saved["bio"] == "Hello"
    assert saved["updated_at"] > original.json["profile"]["updated_at"]
    assert saved["created_at"] == original.json["profile"]["created_at"]
    assert "password" not in saved and "password_hash" not in saved
    response = authenticated_client.patch("/api/profile", json={"full_name": "Alex Smith"})
    assert response.json["profile"] == saved
    assert authenticated_client.patch("/api/profile", json={}).json["profile"] == saved
    second = create_app(database_config)
    with second.app_context():
        user = db.session.get(User, saved["id"])
        assert user.full_name == "Alex Smith" and user.bio == "Hello"


def test_partial_update_and_clear(authenticated_client):
    """Omitted values survive PATCH and explicit null clears incomplete profiles."""
    authenticated_client.patch("/api/profile", json={"full_name": "Alex", "bio": "Keep me"})
    response = authenticated_client.patch("/api/profile", json={"full_name": None})
    assert response.status_code == 200
    assert response.json["profile"]["full_name"] is None
    assert response.json["profile"]["bio"] == "Keep me"
    response = authenticated_client.patch("/api/profile", json={"bio": None})
    assert response.status_code == 200
    assert response.json["profile"]["bio"] is None


@pytest.mark.parametrize("data,field", [
    ({"full_name": ""}, "full_name"), ({"full_name": " \t "}, "full_name"),
    ({"full_name": 1}, "full_name"), ({"full_name": []}, "full_name"),
    ({"full_name": "x" * 101}, "full_name"), ({"bio": "x" * 1001}, "bio"),
    ({"bio": True}, "bio"), ({"bio": {}}, "bio")])
def test_invalid_profile_is_atomic(authenticated_client, data, field):
    """Invalid fields reject the whole request without changing data or timestamps."""
    original = authenticated_client.get("/api/profile").json
    response = authenticated_client.patch("/api/profile", json={"full_name": "Should not save", **data})
    assert response.status_code == 400
    assert field in response.json["error"]
    assert authenticated_client.get("/api/profile").json == original


@pytest.mark.parametrize("field", ["id", "user_id", "email", "password", "password_hash",
    "created_at", "updated_at", "onboarding_completed_at", "unknown"])
def test_server_owned_fields_rejected(authenticated_client, field):
    """Only profile fields can be supplied by clients."""
    response = authenticated_client.patch("/api/profile", json={field: "forged"})
    assert response.status_code == 400
    assert "read-only" in response.json["error"]
    assert field in response.json["error"]


def test_profile_length_boundaries(authenticated_client):
    """The documented maximum name and biography lengths are accepted."""
    response = authenticated_client.patch("/api/profile", json={"full_name": "x" * 100, "bio": "x" * 1000})
    assert response.status_code == 200
    assert len(response.json["profile"]["bio"]) == 1000


def test_profile_requires_authentication(csrf_client):
    """Both routes require authentication even with a valid CSRF token."""
    for method in ("get", "patch"):
        token = csrf_client.get("/api/auth/csrf").json["csrf_token"]
        response = getattr(csrf_client, method)("/api/profile", json={}, headers={"X-CSRF-Token": token})
        assert response.status_code == 401
        assert response.json == {"error": "Authentication required."}


def test_profile_requires_csrf(authenticated_client):
    """An authenticated browser cannot update a profile without valid CSRF."""
    authenticated_client.environ_base.pop("HTTP_X_CSRF_TOKEN")
    response = authenticated_client.patch("/api/profile", json={"full_name": "Alex"})
    assert response.status_code == 400
    assert response.json == {"error": "A valid CSRF token is required."}


def test_profile_user_isolation(authenticated_client, app):
    """A second account remains inaccessible through identity fields or URL guesses."""
    other = app.test_client()
    token = other.get("/api/auth/csrf").json["csrf_token"]
    credentials = {"email": "other@example.com", "password": "other-password"}
    other.environ_base["HTTP_X_CSRF_TOKEN"] = token
    user_id = other.post("/api/auth/register", json=credentials).json["user"]["id"]
    assert other.post("/api/auth/login", json=credentials).status_code == 200
    other.environ_base["HTTP_X_CSRF_TOKEN"] = other.get("/api/auth/csrf").json["csrf_token"]
    other.patch("/api/profile", json={"full_name": "Other"})
    response = authenticated_client.patch("/api/profile", json={"user_id": user_id, "full_name": "Hijacked"})
    assert response.status_code == 400
    assert "user_id" in response.json["error"]
    assert authenticated_client.get(f"/api/profile/{user_id}").status_code == 404
    assert authenticated_client.get(f"/api/profile?user_id={user_id}").json["profile"]["id"] == 1
    assert other.get("/api/profile").json["profile"]["full_name"] == "Other"


def test_completed_profile_cannot_clear_fields(authenticated_client, app):
    """Null clearing is limited to incomplete profiles without adding completion routes."""
    authenticated_client.patch("/api/profile", json={"full_name": "Alex", "bio": "Hello"})
    with app.app_context():
        db.session.get(User, 1).onboarding_completed_at = utc_now()
        db.session.commit()
    response = authenticated_client.patch("/api/profile", json={"bio": None})
    assert response.status_code == 400
    assert response.json == {"error": "Completed profiles cannot clear profile fields."}
    assert authenticated_client.get("/api/profile").json["profile"]["bio"] == "Hello"
