import pytest
from sqlalchemy.exc import SQLAlchemyError

from app import create_app
from app.extensions import db
from app.models import LifestylePreference
from app.preferences.questions import QUESTIONS

PATH = "/api/preferences/lifestyle"
ANSWER = {"own_answer": "early", "roommate_answer": "late", "is_requirement": True}


def test_questions_and_empty_answers(authenticated_client):
    """Questions expose ordered single-choice definitions and initially no saved rows."""
    response = authenticated_client.get(PATH + "/questions")
    assert response.status_code == 200
    assert response.json == {"questions": QUESTIONS}
    assert [question["display_order"] for question in response.json["questions"]] == list(range(1, len(QUESTIONS) + 1))
    assert len({question["question_key"] for question in QUESTIONS}) == len(QUESTIONS)
    for question in QUESTIONS:
        assert question["question"] and question["roommate_question"]
        assert "no_preference" not in question["own_answers"]
        assert "no_preference" in question["roommate_answers"]
    assert authenticated_client.get(PATH).json == {"answers": []}


def test_replacement_separation_order_and_persistence(authenticated_client, database_config):
    """PUT replaces one pair, preserves other rows, and survives a new app instance."""
    pets = {"own_answer": "has_pets", "roommate_answer": "no_pets", "is_requirement": False}
    assert authenticated_client.put(PATH + "/pets", json=pets).status_code == 200
    response = authenticated_client.put(PATH + "/sleep_schedule", json=ANSWER)
    assert response.status_code == 200
    assert response.json["answer"]["own_answer"] == "early"
    assert response.json["answer"]["roommate_answer"] == "late"
    original_time = response.json["answer"]["updated_at"]
    replacement = {"own_answer": None, "roommate_answer": "no_preference", "is_requirement": False}
    response = authenticated_client.put(PATH + "/sleep_schedule", json=replacement)
    assert response.status_code == 200
    assert response.json["answer"]["updated_at"] > original_time
    answers = authenticated_client.get(PATH).json["answers"]
    assert [answer["question_key"] for answer in answers] == ["sleep_schedule", "pets"]
    assert answers[0]["own_answer"] is None and answers[0]["roommate_answer"] == "no_preference"
    assert answers[1]["own_answer"] == "has_pets"
    second = create_app(database_config)
    with second.app_context():
        rows = db.session.execute(db.select(LifestylePreference)).scalars().all()
        assert len(rows) == 2
        assert db.session.get(LifestylePreference, (1, "sleep_schedule")).own_answer is None
    response = authenticated_client.put(PATH + "/sleep_schedule", json={**replacement, "roommate_answer": None})
    assert response.status_code == 200
    assert response.json["answer"]["roommate_answer"] is None


@pytest.mark.parametrize("data,error", [
    ({}, "Required fields"), ({"own_answer": "early"}, "Required fields"),
    ({**ANSWER, "own_answer": "no_preference"}, "own_answer"),
    ({**ANSWER, "own_answer": ["early", "late"]}, "own_answer"),
    ({**ANSWER, "own_answer": "early,late"}, "own_answer"),
    ({**ANSWER, "roommate_answer": 1}, "roommate_answer"),
    ({**ANSWER, "roommate_answer": "unsupported"}, "roommate_answer"),
    ({**ANSWER, "roommate_answer": None}, "specific roommate_answer"),
    ({**ANSWER, "roommate_answer": "no_preference"}, "specific roommate_answer"),
    ({**ANSWER, "is_requirement": 1}, "Boolean"),
    ({**ANSWER, "is_requirement": "false"}, "Boolean"),
    ({**ANSWER, "is_requirement": None}, "Boolean"),
    ({**ANSWER, "user_id": 2}, "user_id"), ({**ANSWER, "updated_at": "forged"}, "updated_at"),
    ({**ANSWER, "extra": False}, "extra")])
def test_invalid_replacement_is_atomic(authenticated_client, data, error):
    """Rejected replacement bodies leave all saved fields and timestamps unchanged."""
    original = authenticated_client.put(PATH + "/sleep_schedule", json=ANSWER).json["answer"]
    response = authenticated_client.put(PATH + "/sleep_schedule", json=data)
    assert response.status_code == 400
    assert error in response.json["error"]
    assert authenticated_client.get(PATH).json == {"answers": [original]}


def test_unknown_question(authenticated_client):
    """An unknown key returns JSON 404 without inserting a row."""
    response = authenticated_client.put(PATH + "/unknown", json=ANSWER)
    assert response.status_code == 404
    assert response.json == {"error": "Unknown lifestyle question."}
    assert authenticated_client.get(PATH).json == {"answers": []}


@pytest.mark.parametrize("method,path", [("get", PATH), ("get", PATH + "/questions"),
                                        ("put", PATH + "/sleep_schedule")])
def test_lifestyle_requires_authentication(csrf_client, method, path):
    """All questionnaire and answer endpoints require a session identity."""
    response = getattr(csrf_client, method)(path, json=ANSWER)
    assert response.status_code == 401
    assert response.json == {"error": "Authentication required."}


@pytest.mark.parametrize("token", [None, "invalid"])
def test_put_requires_csrf(authenticated_client, token):
    """Session authentication alone cannot authorize replacement writes."""
    authenticated_client.environ_base.pop("HTTP_X_CSRF_TOKEN")
    response = authenticated_client.put(PATH + "/sleep_schedule", json=ANSWER,
        headers={} if token is None else {"X-CSRF-Token": token})
    assert response.status_code == 400
    assert response.json == {"error": "A valid CSRF token is required."}
    assert authenticated_client.get(PATH).json == {"answers": []}


def test_lifestyle_user_isolation(authenticated_client, app):
    """Users can save different answers for the same key without crossing identities."""
    authenticated_client.put(PATH + "/sleep_schedule", json=ANSWER)
    other = app.test_client()
    other.environ_base["HTTP_X_CSRF_TOKEN"] = other.get("/api/auth/csrf").json["csrf_token"]
    credentials = {"email": "other@example.com", "password": "long-password"}
    assert other.post("/api/auth/register", json=credentials).status_code == 201
    assert other.post("/api/auth/login", json=credentials).status_code == 200
    other.environ_base["HTTP_X_CSRF_TOKEN"] = other.get("/api/auth/csrf").json["csrf_token"]
    assert other.get(PATH).json == {"answers": []}
    replacement = {**ANSWER, "own_answer": "late"}
    assert other.put(PATH + "/sleep_schedule", json=replacement).status_code == 200
    assert authenticated_client.get(PATH + "?user_id=2").json["answers"][0]["own_answer"] == "early"
    assert other.get(PATH).json["answers"][0]["own_answer"] == "late"


def test_failed_write_rolls_back(authenticated_client, monkeypatch):
    """A database write failure rolls back the answer instead of leaving dirty state."""
    original = authenticated_client.put(PATH + "/sleep_schedule", json=ANSWER).json["answer"]
    rollback = db.session.rollback
    rollbacks = []

    def fail_commit():
        """Simulate a database failure after the route has changed the model."""
        raise SQLAlchemyError("simulated failure")

    def record_rollback():
        """Record and execute the real session rollback."""
        rollbacks.append(True)
        rollback()

    with monkeypatch.context() as patch:
        patch.setattr(db.session, "commit", fail_commit)
        patch.setattr(db.session, "rollback", record_rollback)
        response = authenticated_client.put(PATH + "/sleep_schedule", json={**ANSWER, "own_answer": "late"})
    assert response.status_code == 503
    assert response.json == {"error": "The database write failed; please retry."}
    assert rollbacks == [True]
    assert authenticated_client.get(PATH).json == {"answers": [original]}


@pytest.mark.parametrize("key,own,expectation", [
    ("pets", "has_pets", "no_pets"),
    ("smoking", "smoker", "non_smoker"),
    ("daytime_visitors", "5_7", "1_2"),
    ("overnight_guests", "1_2", "never"),
])
def test_independent_habits_and_limits(authenticated_client, key, own, expectation):
    """Persist asymmetric answers and require importance to refer to a real limit."""
    payload = {"own_answer": own, "roommate_answer": expectation, "is_requirement": True}
    assert authenticated_client.put(PATH + "/" + key, json=payload).status_code == 200
    saved = authenticated_client.get(PATH).json["answers"][0]
    assert all(saved[field] == value for field, value in payload.items())
    for missing in (None, "no_preference"):
        payload.update(roommate_answer=missing)
        assert authenticated_client.put(PATH + "/" + key, json=payload).status_code == 400
        payload.update(own_answer=None, is_requirement=False)
        assert authenticated_client.put(PATH + "/" + key, json=payload).status_code == 200
        saved = authenticated_client.get(PATH).json["answers"][0]
        assert saved["own_answer"] is None and saved["roommate_answer"] == missing
        payload.update(is_requirement=True)
