from decimal import Decimal

import pytest
from flask_migrate import downgrade, upgrade
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.extensions import db
from app.models import HousingPreference, LifestylePreference, User
from conftest import MIGRATIONS, test_database_url as database_url


def test_migrations_initialize_and_repeat(app):
    """The checked-in migration creates an empty schema and can be reapplied safely."""
    with app.app_context():
        downgrade(directory=MIGRATIONS, revision="base")
        assert "users" not in inspect(db.engine).get_table_names()
        upgrade(directory=MIGRATIONS)
        upgrade(directory=MIGRATIONS)
        assert {"users", "housing_preferences", "lifestyle_preferences"} <= set(inspect(db.engine).get_table_names())
        columns = {column["name"]: column for column in inspect(db.engine).get_columns("users")}
        assert columns["created_at"]["type"].timezone
        assert columns["email"]["type"].length == 255


def test_relationships_defaults_and_database_cascades(app):
    """Relationships, UTC timestamps, defaults, and database cascades persist."""
    with app.app_context():
        user = User(email="a@example.com", password_hash="existing-compatible-hash")
        user.housing_preference = HousingPreference(budget_min=Decimal("123.45"))
        user.lifestyle_preferences = [LifestylePreference(question_key="sleep"),
                                     LifestylePreference(question_key="pets", own_answer="no_preference")]
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        db.session.expire_all()
        assert user.housing_preference.budget_min == Decimal("123.45")
        assert user.housing_preference.city_is_requirement is False
        assert len(user.lifestyle_preferences) == 2
        assert user.created_at.utcoffset().total_seconds() == 0
        assert user.updated_at.utcoffset().total_seconds() == 0
        # SQL deletion verifies ON DELETE CASCADE independently of ORM behavior.
        db.session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        db.session.commit()
        assert db.session.execute(db.select(HousingPreference)).scalars().all() == []
        assert db.session.execute(db.select(LifestylePreference)).scalars().all() == []


@pytest.mark.parametrize("values", [
    {"budget_min": -1}, {"budget_max": -1}, {"budget_min": 200, "budget_max": 100},
    {"lease_months": 0}, {"lease_months": -1}])
def test_housing_database_constraints_and_rollback(app, values):
    """PostgreSQL rejects invalid housing values and permits writes after rollback."""
    with app.app_context():
        user = User(email="a@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()
        db.session.add(HousingPreference(user_id=user.id, **values))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        db.session.add(HousingPreference(user_id=user.id, lease_months=12))
        db.session.commit()
        assert db.session.get(HousingPreference, user.id).lease_months == 12


@pytest.mark.parametrize("kind", ["email", "housing_pk", "lifestyle_pk", "housing_fk", "lifestyle_fk"])
def test_unique_primary_and_foreign_keys(app, kind):
    """Actual PostgreSQL constraints reject duplicate identities and orphan rows."""
    with app.app_context():
        user = User(email="a@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()
        db.session.add_all([HousingPreference(user_id=user.id),
                            LifestylePreference(user_id=user.id, question_key="sleep")])
        db.session.commit()
        rows = {
            "email": User(email=user.email, password_hash="hash"),
            "housing_pk": HousingPreference(user_id=user.id),
            "lifestyle_pk": LifestylePreference(user_id=user.id, question_key="sleep"),
            "housing_fk": HousingPreference(user_id=999),
            "lifestyle_fk": LifestylePreference(user_id=999, question_key="sleep"),
        }
        db.session.add(rows[kind])
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        assert db.session.get(User, user.id).email == "a@example.com"


def test_explicit_database_configuration(monkeypatch):
    """An omitted URL or SQLite URL cannot silently create local tables."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="explicitly"):
        create_app()
    with pytest.raises(RuntimeError, match="explicitly"):
        create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://"})


@pytest.mark.parametrize("value", [None, "sqlite://", "postgresql+psycopg://room_find@localhost/room_find",
    "postgresql+psycopg://room_find@localhost/room_find_test"])
def test_test_database_guard(monkeypatch, value):
    """The suite refuses absent or development database configurations."""
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    if value is not None:
        monkeypatch.setenv("TEST_DATABASE_URL", value)
    with pytest.raises(RuntimeError):
        database_url()


def test_test_database_guard_rejects_development_alias(monkeypatch):
    """Even an allowlisted test name cannot equal the configured development target."""
    value = "postgresql+psycopg://room_find_test:password@localhost/room_find_test"
    monkeypatch.setenv("TEST_DATABASE_URL", value)
    monkeypatch.setenv("DATABASE_URL", value)
    with pytest.raises(RuntimeError, match="cannot target"):
        database_url()


def test_combined_answer_migration_preserves_originals(app):
    """Archive legacy pairs, retain accounts and leave uncertain habits unanswered."""
    with app.app_context():
        downgrade(directory=MIGRATIONS, revision="c3e91d8b2a40")
        db.session.execute(text("INSERT INTO users (id, email, password_hash) VALUES (1, 'legacy@example.com', 'hash')"))
        for key, own, roommate in [("pets", "okay_with_pets", "okay_with_pets"),
                                    ("smoking", "non_smoker", "non_smoker"),
                                    ("cleanliness", "tidy", "tidy"),
                                    ("guests", "sometimes", "often")]:
            db.session.execute(text("""INSERT INTO lifestyle_preferences
                (user_id, question_key, own_answer, roommate_answer, is_requirement)
                VALUES (1, :key, :own, :roommate, true)"""),
                {"key": key, "own": own, "roommate": roommate})
        db.session.commit()
        upgrade(directory=MIGRATIONS)
        assert db.session.get(User, 1).email == "legacy@example.com"
        pets = db.session.get(LifestylePreference, (1, "pets"))
        assert pets.own_answer is None and pets.roommate_answer == "no_preference"
        assert pets.is_requirement is False
        assert pets.legacy_answers["own_answer"] == "okay_with_pets"
        smoking = db.session.get(LifestylePreference, (1, "smoking"))
        assert smoking.own_answer is None and smoking.roommate_answer == "non_smoker"
        assert smoking.is_requirement is True
        assert db.session.get(LifestylePreference, (1, "cleanliness")).own_answer is None
        assert db.session.get(LifestylePreference, (1, "guests")).own_answer == "sometimes"
        assert db.session.get(LifestylePreference, (1, "daytime_visitors")) is None
