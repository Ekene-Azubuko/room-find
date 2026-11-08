"""Authenticated discovery of explicitly seeded demo profiles."""
from flask import Blueprint, jsonify
from sqlalchemy.orm import selectinload
from werkzeug.exceptions import NotFound

from .auth.security import login_required
from .demo import DEMO_KEYS
from .extensions import db
from .models import User
from .preferences.routes import serialize_lifestyle

discovery = Blueprint("discovery", __name__)


def serialize_roommate(user):
    """Expose only the demo profile fields needed by the discovery interface."""
    housing = user.housing_preference
    return {"id": user.id, "full_name": user.full_name, "age": user.age,
            "occupation": user.occupation, "bio": user.bio, "life_stage": user.life_stage,
            "photo_url": f"/images/{user.demo_key}.jpg", "is_demo": True,
            "housing": {"city": housing.city, "neighborhood": housing.neighborhood,
                        "budget_min": str(housing.budget_min) if housing.budget_min is not None else None, "budget_max": str(housing.budget_max) if housing.budget_max is not None else None,
                        "move_in_date": housing.move_in_date.isoformat() if housing.move_in_date else None, "lease_months": housing.lease_months} if housing else None,
            "answers": [serialize_lifestyle(answer) for answer in sorted(user.lifestyle_preferences, key=lambda row: row.question_key)],
            "lifestyle": {answer.question_key: answer.own_answer for answer in user.lifestyle_preferences}}


def roommate_query():
    """Load only the four seed identities and their related profile data."""
    return db.select(User).where(User.demo_key.in_(DEMO_KEYS)).options(
        selectinload(User.housing_preference), selectinload(User.lifestyle_preferences))


@discovery.get("/roommates")
@login_required
def list_roommates():
    """Return all seeded roommates without calculating or implying a match score."""
    users = db.session.execute(roommate_query().order_by(User.id)).scalars().all()
    response = jsonify({"roommates": [serialize_roommate(user) for user in users]})
    response.headers["Cache-Control"] = "no-store"
    return response


@discovery.get("/roommates/<int:roommate_id>")
@login_required
def get_roommate(roommate_id):
    """Return a single demo persona without allowing access to private real accounts."""
    user = db.session.execute(roommate_query().where(User.id == roommate_id)).scalar_one_or_none()
    if user is None:
        raise NotFound("Roommate profile not found.")
    response = jsonify({"roommate": serialize_roommate(user)})
    response.headers["Cache-Control"] = "no-store"
    return response
