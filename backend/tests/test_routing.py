import pytest


def test_blueprints_registered_once(app):
    """Each public route has exactly one registration in the factory."""
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert rules.count("/api/health") == 1
    assert rules.count("/api/auth/register") == 1
    assert rules.count("/api/profile") == 2
    assert rules.count("/api/preferences/housing") == 2
    route_methods = [(rule.rule, method) for rule in app.url_map.iter_rules()
                     for method in rule.methods if method not in {"HEAD", "OPTIONS"}]
    assert len(route_methods) == len(set(route_methods))
    assert set(app.blueprints) == {"health", "auth", "profile", "preferences", "onboarding", "discovery"}


@pytest.mark.parametrize("method,path,status", [
    ("get", "/api/missing", 404), ("post", "/api/health", 405),
    ("get", "/api/auth/register", 405)])
def test_framework_errors_are_json(client, method, path, status):
    """Routing errors share the API's JSON envelope and retain Allow headers."""
    response = getattr(client, method)(path)
    assert response.status_code == status
    assert isinstance(response.json["error"], str)
    if status == 405:
        assert response.headers["Allow"]


def test_readiness_reports_database_failure(client, monkeypatch):
    """Readiness returns safe JSON 503 when PostgreSQL cannot be queried."""
    from sqlalchemy.exc import SQLAlchemyError
    from app.extensions import db

    def fail_query(*args, **kwargs):
        """Simulate an unavailable database without touching development services."""
        raise SQLAlchemyError("unavailable")

    monkeypatch.setattr(db.session, "execute", fail_query)
    response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json == {"error": "Database is not ready."}
