import pytest


def test_blueprints_registered_once(app):
    """Each public route has exactly one registration in the factory."""
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert rules.count("/api/health") == 1
    assert rules.count("/api/auth/register") == 1
    assert set(app.blueprints) == {"health", "auth"}


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
