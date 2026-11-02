import os
from pathlib import Path

import pytest
from flask_migrate import upgrade
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app import create_app
from app.extensions import db

MIGRATIONS = str(Path(__file__).resolve().parents[1] / "migrations")


def test_database_url():
    """Refuse cleanup unless an explicit, dedicated test database and role are used."""
    value = os.environ.get("TEST_DATABASE_URL")
    if not value:
        raise RuntimeError("Set TEST_DATABASE_URL to the dedicated PostgreSQL test database.")
    url = make_url(value)
    if (url.drivername != "postgresql+psycopg" or url.database != "room_find_test"
            or url.username != "room_find_test"):
        raise RuntimeError("Tests require database AND role room_find_test.")
    development = os.environ.get("DATABASE_URL")
    if development:
        dev = make_url(development)
        if (dev.host, dev.port, dev.database) == (url.host, url.port, url.database):
            raise RuntimeError("TEST_DATABASE_URL cannot target DATABASE_URL.")
    return value


@pytest.fixture(scope="session")
def database_config():
    """Apply real migrations to the dedicated database before running tests."""
    config = {"TESTING": True, "SQLALCHEMY_DATABASE_URI": test_database_url(),
              "SECRET_KEY": "test-only-secret-with-at-least-32-characters"}
    application = create_app(config)
    with application.app_context():
        upgrade(directory=MIGRATIONS)
    return config


@pytest.fixture
def app(database_config):
    """Reset only the allowlisted test tables for an isolated application."""
    application = create_app(database_config)
    with application.app_context():
        identity = db.session.execute(text("SELECT current_database(), current_user")).one()
        if tuple(identity) != ("room_find_test", "room_find_test"):
            raise RuntimeError("Refusing to clear a non-test database.")
        db.session.execute(text("TRUNCATE users, housing_preferences, lifestyle_preferences RESTART IDENTITY CASCADE"))
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    """Return an isolated HTTP client."""
    return app.test_client()


@pytest.fixture
def csrf_client(client):
    """Give validation tests a valid CSRF token without bypassing protection."""
    token = client.get("/api/auth/csrf").json["csrf_token"]
    client.environ_base["HTTP_X_CSRF_TOKEN"] = token
    return client


@pytest.fixture
def authenticated_client(csrf_client):
    """Register and log in one user, then refresh the session's CSRF token."""
    credentials = {"email": "alex@example.com", "password": "long-password"}
    assert csrf_client.post("/api/auth/register", json=credentials).status_code == 201
    assert csrf_client.post("/api/auth/login", json=credentials).status_code == 200
    token = csrf_client.get("/api/auth/csrf").json["csrf_token"]
    csrf_client.environ_base["HTTP_X_CSRF_TOKEN"] = token
    return csrf_client


@pytest.fixture
def eligible_client(authenticated_client):
    """Save all required answers without marking onboarding complete."""
    from app.preferences.questions import QUESTIONS

    assert authenticated_client.patch("/api/profile", json={"full_name": "Alex", "bio": "Optional"}).status_code == 200
    assert authenticated_client.patch("/api/preferences/housing", json={
        "city": "Seattle", "budget_min": "900.00", "budget_max": "1500.00",
        "move_in_date": "2027-02-01", "lease_months": 12}).status_code == 200
    for question in QUESTIONS:
        response = authenticated_client.put("/api/preferences/lifestyle/" + question["question_key"], json={
            "own_answer": question["own_answers"][0], "roommate_answer": "no_preference", "is_requirement": False})
        assert response.status_code == 200
    return authenticated_client


@pytest.fixture
def completed_client(eligible_client):
    """Return a browser with a fully completed onboarding record."""
    response = eligible_client.post("/api/onboarding/complete")
    assert response.status_code == 200 and response.json["onboarding"]["completed"]
    return eligible_client
