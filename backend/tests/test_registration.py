import pytest
from werkzeug.security import check_password_hash

from app import create_app
from app.extensions import db
from app.models import User


def test_health(client):
    """Health reports the existing public contract."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_registration_hash_normalization_and_persistence(app, client):
    """Registration stores a hash and survives a new application instance."""
    response = client.post("/api/auth/register", json={
        "email": "  Alex@Example.COM ", "password": "long-password"})
    assert response.status_code == 201
    assert response.json == {"user": {"id": 1, "email": "alex@example.com"}}
    with app.app_context():
        row = db.session.execute(db.select(User)).scalar_one()
        assert row.password_hash != "long-password"
        assert check_password_hash(row.password_hash, "long-password")
    second = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": app.config["SQLALCHEMY_DATABASE_URI"]})
    duplicate = second.test_client().post("/api/auth/register", json={
        "email": "ALEX@example.com", "password": "another-password"})
    assert duplicate.status_code == 409
    assert duplicate.json == {"error": "An account with this email already exists."}


@pytest.mark.parametrize("data", [None, [], {}, {"email": 12},
    {"email": "bad", "password": "long-password"},
    {"email": "a b@example.com", "password": "long-password"},
    {"email": "a" * 250 + "@example.com", "password": "long-password"},
    {"email": "a@example.com", "password": 12},
    {"email": "a@example.com", "password": "short"},
    {"email": "a@example.com", "password": "x" * 129}])
def test_invalid_fields(client, data):
    """Invalid bodies return a safe JSON validation error."""
    import json
    response = client.post("/api/auth/register", data=json.dumps(data),
                           content_type="application/json")
    assert response.status_code == 400
    assert isinstance(response.json["error"], str)
    assert "password_hash" not in response.json


def test_malformed_and_missing_content_type(client):
    """Malformed JSON and unsupported content types have distinct errors."""
    response = client.post("/api/auth/register", data="{", content_type="application/json")
    assert response.status_code == 400
    assert response.json == {"error": "Request body must be a valid JSON object."}
    response = client.post("/api/auth/register", data="{}")
    assert response.status_code == 415
    assert response.json == {"error": "Content-Type must be application/json."}


def test_duplicate_failure_does_not_poison_later_registration(client):
    """A uniqueness violation is rolled back before the next account write."""
    data = {"email": "a@example.com", "password": "long-password"}
    assert client.post("/api/auth/register", json=data).status_code == 201
    duplicate = client.post("/api/auth/register", json=data)
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json["error"]
    response = client.post("/api/auth/register", json={**data, "email": "b@example.com"})
    assert response.status_code == 201
    assert response.json["user"]["email"] == "b@example.com"
