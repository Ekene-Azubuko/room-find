import pytest

from app.extensions import db
from app.models import HousingPreference, LifestylePreference, User
from app.preferences.questions import QUESTIONS

PATH = "/api/onboarding"


def test_new_and_partial_progress(authenticated_client):
    """Progress precisely names missing answers and GET never completes onboarding."""
    state = authenticated_client.get(PATH).json["onboarding"]
    assert not state["completed"] and not state["eligible"]
    assert state["onboarding_completed_at"] is None
    expected = {"profile.full_name", "housing.city", "housing.budget_min", "housing.budget_max",
                "housing.move_in_date", "housing.lease_months"}
    expected.update(f"lifestyle.{question['question_key']}.{field}" for question in QUESTIONS
                    for field in ("own_answer", "roommate_answer"))
    assert set(state["missing_fields"]) == expected
    authenticated_client.patch("/api/profile", json={"full_name": "Alex"})
    authenticated_client.patch("/api/preferences/housing", json={"city": "Seattle"})
    response = authenticated_client.post(PATH + "/complete")
    assert response.status_code == 400
    assert response.json["error"] == "Onboarding is incomplete or invalid."
    assert set(response.json["onboarding"]["missing_fields"]) == expected - {"profile.full_name", "housing.city"}
    assert response.json["onboarding"]["onboarding_completed_at"] is None


def test_completion_no_preference_and_idempotence(eligible_client):
    """Explicit no_preference is answered; completion is explicit and idempotent."""
    state = eligible_client.get(PATH).json["onboarding"]
    assert state == {"completed": False, "eligible": True, "onboarding_completed_at": None,
                     "missing_fields": [], "errors": {}}
    response = eligible_client.post(PATH + "/complete", json={})
    assert response.status_code == 200
    completed = response.json["onboarding"]
    assert completed["completed"] and completed["onboarding_completed_at"].endswith("+00:00")
    assert eligible_client.post(PATH + "/complete").json["onboarding"] == completed
    assert eligible_client.get("/api/profile").json["profile"]["onboarding_completed_at"] == completed["onboarding_completed_at"]


@pytest.mark.parametrize("path,method,data", [
    ("/api/profile", "patch", {"full_name": "Updated Name"}),
    ("/api/preferences/housing", "patch", {"city": "Portland"}),
    ("/api/preferences/lifestyle/sleep_schedule", "put",
     {"own_answer": "late", "roommate_answer": "early", "is_requirement": True}),
    ("/api/profile", "patch", {"bio": None})])
def test_valid_and_optional_edits_preserve_completion(completed_client, path, method, data):
    """Valid required edits and clearing optional bio retain the original timestamp."""
    original = completed_client.get(PATH).json
    assert getattr(completed_client, method)(path, json=data).status_code == 200
    assert completed_client.get(PATH).json == original


@pytest.mark.parametrize("path,method,data,missing", [
    ("/api/profile", "patch", {"full_name": None}, "profile.full_name"),
    ("/api/preferences/housing", "patch", {"city": None}, "housing.city"),
    ("/api/preferences/housing", "patch", {"budget_min": None}, "housing.budget_min"),
    ("/api/preferences/housing", "patch", {"budget_max": None}, "housing.budget_max"),
    ("/api/preferences/housing", "patch", {"move_in_date": None}, "housing.move_in_date"),
    ("/api/preferences/housing", "patch", {"lease_months": None}, "housing.lease_months"),
    ("/api/preferences/lifestyle/sleep_schedule", "put",
     {"own_answer": None, "roommate_answer": "no_preference", "is_requirement": False}, "lifestyle.sleep_schedule.own_answer"),
    ("/api/preferences/lifestyle/sleep_schedule", "put",
     {"own_answer": "early", "roommate_answer": None, "is_requirement": False}, "lifestyle.sleep_schedule.roommate_answer")])
def test_clearing_required_answers_resets_completion(completed_client, path, method, data, missing):
    """Every required field can be cleared and resets completion in the same save."""
    response = getattr(completed_client, method)(path, json=data)
    assert response.status_code == 200
    state = completed_client.get(PATH).json["onboarding"]
    assert not state["completed"] and not state["eligible"]
    assert state["onboarding_completed_at"] is None
    assert state["missing_fields"] == [missing]
    assert completed_client.get("/api/profile").json["profile"]["onboarding_completed_at"] is None


@pytest.mark.parametrize("kind,error_key", [("name", "profile.full_name"), ("bio", "profile.bio"),
    ("housing", "housing.city_is_requirement"), ("lifestyle", "lifestyle.sleep_schedule")])
def test_invalid_saved_data_blocks_completion(eligible_client, app, kind, error_key):
    """Completion revalidates saved data rather than trusting non-null answers."""
    with app.app_context():
        if kind == "name":
            db.session.get(User, 1).full_name = "  "
        elif kind == "bio":
            db.session.get(User, 1).bio = "x" * 1001
        elif kind == "housing":
            row = db.session.get(HousingPreference, 1)
            row.city = None
            row.city_is_requirement = True
        else:
            db.session.get(LifestylePreference, (1, "sleep_schedule")).is_requirement = True
        db.session.commit()
    response = eligible_client.post(PATH + "/complete")
    assert response.status_code == 400
    assert error_key in response.json["onboarding"]["errors"]
    assert response.json["onboarding"]["onboarding_completed_at"] is None


@pytest.mark.parametrize("path,method,data", [
    ("/api/profile", "patch", {"full_name": ""}),
    ("/api/preferences/housing", "patch", {"budget_min": 9999}),
    ("/api/preferences/lifestyle/sleep_schedule", "put",
     {"own_answer": None, "roommate_answer": "no_preference", "is_requirement": True})])
def test_failed_edits_preserve_answers_and_completion(completed_client, path, method, data):
    """Validation failures change neither saved answers nor completion state."""
    original = completed_client.get(PATH).json
    snapshots = {url: completed_client.get(url).json for url in (
        "/api/profile", "/api/preferences/housing", "/api/preferences/lifestyle")}
    response = getattr(completed_client, method)(path, json=data)
    assert response.status_code == 400 and response.json["error"]
    assert completed_client.get(PATH).json == original
    for url, saved in snapshots.items():
        assert completed_client.get(url).json == saved


@pytest.mark.parametrize("field", ["completed", "onboarding_completed_at", "user_id"])
def test_completion_metadata_cannot_be_submitted(eligible_client, field):
    """Only the server determines completion state and identity."""
    response = eligible_client.post(PATH + "/complete", json={field: True})
    assert response.status_code == 400
    assert field in response.json["error"]
    assert eligible_client.get(PATH).json["onboarding"]["onboarding_completed_at"] is None


def test_onboarding_authentication_csrf_and_isolation(completed_client, app):
    """Anonymous and other-user sessions cannot inspect or complete this user's state."""
    other = app.test_client()
    response = other.get(PATH)
    assert response.status_code == 401 and response.json == {"error": "Authentication required."}
    other.environ_base["HTTP_X_CSRF_TOKEN"] = other.get("/api/auth/csrf").json["csrf_token"]
    response = other.post(PATH + "/complete")
    assert response.status_code == 401 and response.json == {"error": "Authentication required."}
    other.environ_base["HTTP_X_CSRF_TOKEN"] = other.get("/api/auth/csrf").json["csrf_token"]
    credentials = {"email": "other@example.com", "password": "long-password"}
    other.post("/api/auth/register", json=credentials)
    other.post("/api/auth/login", json=credentials)
    other.environ_base["HTTP_X_CSRF_TOKEN"] = other.get("/api/auth/csrf").json["csrf_token"]
    assert not other.get(PATH + "?user_id=1").json["onboarding"]["completed"]
    assert other.post(PATH + "/complete").status_code == 400
    original = completed_client.get(PATH).json
    completed_client.environ_base.pop("HTTP_X_CSRF_TOKEN")
    for headers in ({}, {"X-CSRF-Token": "invalid"}):
        response = completed_client.post(PATH + "/complete", headers=headers)
        assert response.status_code == 400
        assert response.json == {"error": "A valid CSRF token is required."}
    assert completed_client.get(PATH).json == original


def test_failed_completed_edit_rolls_back_completion(completed_client, monkeypatch):
    """A failed commit rolls back both a cleared answer and its completion reset."""
    from sqlalchemy.exc import SQLAlchemyError

    original = completed_client.get("/api/profile").json
    state = completed_client.get(PATH).json

    def fail_commit():
        """Fail after eligibility has reset the in-memory completion timestamp."""
        raise SQLAlchemyError("simulated failure")

    with monkeypatch.context() as patch:
        patch.setattr(db.session, "commit", fail_commit)
        response = completed_client.patch("/api/profile", json={"full_name": None})
    assert response.status_code == 503
    assert response.json == {"error": "The database write failed; please retry."}
    assert completed_client.get("/api/profile").json == original
    assert completed_client.get(PATH).json == state
