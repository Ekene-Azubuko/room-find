from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import HousingPreference

PATH = "/api/preferences/housing"


def test_absent_first_save_update_and_persistence(authenticated_client, app, database_config):
    """First save creates one row; later saves persist merged values across factories."""
    response = authenticated_client.get(PATH)
    assert response.status_code == 200
    assert response.json == {"housing": None}
    response = authenticated_client.patch(PATH, json={
        "city": " Seattle ", "budget_min": "900.10", "budget_max": 1200,
        "move_in_date": "2027-02-01", "lease_months": 12, "city_is_requirement": True})
    assert response.status_code == 200
    saved = response.json["housing"]
    assert saved["city"] == "Seattle"
    assert saved["budget_min"] == "900.10" and saved["budget_max"] == "1200.00"
    assert saved["budget_is_requirement"] is False
    assert saved["move_in_date"] == "2027-02-01"
    assert saved["updated_at"].endswith("+00:00")
    response = authenticated_client.patch(PATH, json={"lease_months": 6})
    assert response.status_code == 200
    updated = response.json["housing"]
    assert updated["city"] == "Seattle" and updated["lease_months"] == 6
    assert updated["updated_at"] > saved["updated_at"]
    assert authenticated_client.patch(PATH, json={"lease_months": 6}).json["housing"] == updated
    assert authenticated_client.patch(PATH, json={}).json["housing"] == updated
    second = create_app(database_config)
    with second.app_context():
        rows = db.session.execute(db.select(HousingPreference)).scalars().all()
        assert len(rows) == 1
        assert rows[0].budget_min == Decimal("900.10") and rows[0].lease_months == 6


@pytest.mark.parametrize("patch", [{"budget_min": "1500.01"}, {"budget_max": "899.99"}])
def test_budgets_validate_against_saved_bounds(authenticated_client, patch):
    """One incoming budget bound must remain compatible with its saved counterpart."""
    original = authenticated_client.patch(PATH, json={"budget_min": 900, "budget_max": 1500}).json
    response = authenticated_client.patch(PATH, json={"city": "Must not save", **patch})
    assert response.status_code == 400
    assert response.json == {"error": "budget_min must not exceed budget_max."}
    assert authenticated_client.get(PATH).json == original


@pytest.mark.parametrize("field,value", [
    ("budget_min", -1), ("budget_max", "-0.01"), ("budget_min", True),
    ("budget_min", "NaN"), ("budget_max", "Infinity"), ("budget_min", "abc"),
    ("budget_max", "100000000.00"), ("budget_min", "1.001"), ("budget_min", []),
    ("budget_min", ""), ("budget_max", "1e99999"),
    ("move_in_date", "2027-02-29"), ("move_in_date", "2027-13-01"),
    ("move_in_date", "20270201"), ("move_in_date", "2027-02-01T12:00:00Z"),
    ("move_in_date", 20270201), ("lease_months", 0), ("lease_months", -1),
    ("lease_months", True), ("lease_months", 1.5), ("lease_months", "12"),
    ("lease_months", 2147483648), ("city", ""), ("city", "   "),
    ("city", "x" * 101), ("city", False), ("city_is_requirement", "false"),
    ("budget_is_requirement", 1), ("move_in_is_requirement", None),
    ("lease_is_requirement", []), ("user_id", 2), ("id", 2), ("updated_at", "forged"),
    ("unknown", "value")])
def test_invalid_housing_values_are_atomic(authenticated_client, field, value):
    """Malformed, overflowing and unauthorized fields leave saved values untouched."""
    original = authenticated_client.patch(PATH, json={"city": "Portland"}).json
    response = authenticated_client.patch(PATH, json={"city": "Should not save", field: value})
    assert response.status_code == 400
    assert field in response.json["error"]
    assert authenticated_client.get(PATH).json == original


@pytest.mark.parametrize("answer,flag,value", [
    ("city", "city_is_requirement", "Seattle"),
    ("budget_max", "budget_is_requirement", "1500.00"),
    ("move_in_date", "move_in_is_requirement", "2028-02-29"),
    ("lease_months", "lease_is_requirement", 12)])
def test_requirement_flags_and_clearing(authenticated_client, answer, flag, value):
    """Required answers cannot disappear unless their requirement flag is cleared too."""
    response = authenticated_client.patch(PATH, json={flag: True})
    assert response.status_code == 400
    assert response.json == {"error": f"{flag} requires its corresponding answer."}
    assert authenticated_client.get(PATH).json == {"housing": None}
    response = authenticated_client.patch(PATH, json={answer: value, flag: True})
    assert response.status_code == 200
    original = response.json
    response = authenticated_client.patch(PATH, json={answer: None})
    assert response.status_code == 400
    assert flag in response.json["error"]
    assert authenticated_client.get(PATH).json == original
    response = authenticated_client.patch(PATH, json={answer: None, flag: False})
    assert response.status_code == 200
    assert response.json["housing"][answer] is None
    assert response.json["housing"][flag] is False


def test_budget_requirement_can_keep_one_bound(authenticated_client):
    """A budget requirement remains answered while at least one bound exists."""
    authenticated_client.patch(PATH, json={"budget_min": 0, "budget_max": 1500, "budget_is_requirement": True})
    response = authenticated_client.patch(PATH, json={"budget_max": None})
    assert response.status_code == 200
    assert response.json["housing"]["budget_min"] == "0.00"
    assert response.json["housing"]["budget_is_requirement"] is True


def test_exact_decimal_json_and_precision_limits(authenticated_client):
    """JSON decimals are parsed exactly and never rounded silently to cents."""
    response = authenticated_client.patch(PATH, data='{"budget_min":0.10,"budget_max":99999999.99}',
                                         content_type="application/json")
    assert response.status_code == 200
    assert response.json["housing"]["budget_min"] == "0.10"
    assert response.json["housing"]["budget_max"] == "99999999.99"
    original = response.json
    response = authenticated_client.patch(PATH, data='{"budget_max":99999999.980000001}',
                                         content_type="application/json")
    assert response.status_code == 400
    assert "decimal places" in response.json["error"]
    assert authenticated_client.get(PATH).json == original


def test_clear_all_nullable_fields(authenticated_client):
    """Explicit null clears optional answers while omitted fields remain intact."""
    fields = {"city": "Seattle", "budget_min": 100, "budget_max": 200,
              "move_in_date": "2028-02-29", "lease_months": 12}
    authenticated_client.patch(PATH, json=fields)
    response = authenticated_client.patch(PATH, json=dict.fromkeys(fields))
    assert response.status_code == 200
    assert all(response.json["housing"][field] is None for field in fields)


def test_housing_requires_authentication(csrf_client):
    """Both housing routes reject anonymous sessions with valid CSRF."""
    for method in ("get", "patch"):
        token = csrf_client.get("/api/auth/csrf").json["csrf_token"]
        response = getattr(csrf_client, method)(PATH, json={}, headers={"X-CSRF-Token": token})
        assert response.status_code == 401
        assert response.json == {"error": "Authentication required."}


@pytest.mark.parametrize("token", [None, "invalid"])
def test_housing_requires_csrf(authenticated_client, token):
    """Missing or invalid CSRF prevents writes even for an authenticated user."""
    authenticated_client.environ_base.pop("HTTP_X_CSRF_TOKEN")
    response = authenticated_client.patch(PATH, json={"city": "Seattle"},
        headers={} if token is None else {"X-CSRF-Token": token})
    assert response.status_code == 400
    assert response.json == {"error": "A valid CSRF token is required."}
    assert authenticated_client.get(PATH).json == {"housing": None}


def test_housing_user_isolation(authenticated_client, app):
    """Session identity prevents one user from accessing or modifying another's row."""
    other = app.test_client()
    other.environ_base["HTTP_X_CSRF_TOKEN"] = other.get("/api/auth/csrf").json["csrf_token"]
    credentials = {"email": "other@example.com", "password": "other-password"}
    user_id = other.post("/api/auth/register", json=credentials).json["user"]["id"]
    assert other.post("/api/auth/login", json=credentials).status_code == 200
    other.environ_base["HTTP_X_CSRF_TOKEN"] = other.get("/api/auth/csrf").json["csrf_token"]
    other.patch(PATH, json={"city": "Other city"})
    response = authenticated_client.patch(PATH, json={"user_id": user_id, "city": "Hijacked"})
    assert response.status_code == 400
    assert "user_id" in response.json["error"]
    assert authenticated_client.get(f"{PATH}/{user_id}").status_code == 404
    assert authenticated_client.get(f"{PATH}?user_id={user_id}").json == {"housing": None}
    assert other.get(PATH).json["housing"]["city"] == "Other city"


def test_simultaneous_first_saves_keep_one_merged_row(authenticated_client, app):
    """Concurrent first saves serialize so each succeeds and preserves both patches."""
    cookie_name = app.config["SESSION_COOKIE_NAME"]
    cookie = authenticated_client.get_cookie(cookie_name).value
    token = authenticated_client.environ_base["HTTP_X_CSRF_TOKEN"]

    def save(changes):
        """Send a concurrent request in its own browser and application context."""
        client = app.test_client()
        client.set_cookie(cookie_name, cookie)
        return client.patch(PATH, json=changes, headers={"X-CSRF-Token": token})

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(save, [{"city": "Seattle"}, {"lease_months": 12}]))
    assert [response.status_code for response in responses] == [200, 200]
    saved = authenticated_client.get(PATH).json["housing"]
    assert saved["city"] == "Seattle" and saved["lease_months"] == 12
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count()).select_from(HousingPreference)) == 1


@pytest.mark.parametrize("body", ["{", "[]", "null", '{"budget_min":1e99999999999999999999999999999}'])
def test_invalid_housing_json(authenticated_client, body):
    """Malformed bodies and unrepresentable numbers return JSON errors without writes."""
    response = authenticated_client.patch(PATH, data=body, content_type="application/json")
    assert response.status_code == 400
    assert response.json == {"error": "Request body must be a valid JSON object."}
    assert authenticated_client.get(PATH).json == {"housing": None}
