from flask import Blueprint, g, jsonify
from werkzeug.exceptions import NotFound

from ..auth.security import login_required
from ..extensions import commit_changes, db
from ..models import HousingPreference, LifestylePreference, User
from ..serialization import utc_timestamp
from ..validation import json_object
from .questions import QUESTIONS, QUESTIONS_BY_KEY
from .validation import lifestyle_answer
from .validation import ANSWER_FIELDS, FLAG_FIELDS, WRITABLE_FIELDS, housing_changes, validate_housing_state

preferences = Blueprint("preferences", __name__)


def serialize_housing(row):
    """Serialize housing answers with consistent two-decimal money strings."""
    if row is None:
        return None
    data = {field: getattr(row, field) for field in WRITABLE_FIELDS}
    for field in ("budget_min", "budget_max"):
        data[field] = format(data[field], ".2f") if data[field] is not None else None
    data["move_in_date"] = row.move_in_date.isoformat() if row.move_in_date else None
    data["updated_at"] = utc_timestamp(row.updated_at)
    return data


@preferences.get("/housing")
@login_required
def get_housing():
    """Read only the current user's housing preferences, or null before first save."""
    row = db.session.get(HousingPreference, g.user.id)
    return jsonify({"housing": serialize_housing(row)})


@preferences.patch("/housing")
@login_required
def update_housing():
    """Validate the merged preferences before creating or updating the user's row."""
    changes = housing_changes(json_object())
    # Lock the parent even before the first housing row exists to serialize saves.
    db.session.execute(db.select(User).where(User.id == g.user.id).with_for_update()).scalar_one()
    row = db.session.get(HousingPreference, g.user.id)
    state = ({field: getattr(row, field) for field in WRITABLE_FIELDS} if row is not None
             else {**dict.fromkeys(ANSWER_FIELDS), **dict.fromkeys(FLAG_FIELDS, False)})
    state.update(changes)
    validate_housing_state(state)
    if row is None:
        row = HousingPreference(user_id=g.user.id, **state)
        db.session.add(row)
    else:
        for field, value in changes.items():
            setattr(row, field, value)
    db.session.commit()
    return jsonify({"housing": serialize_housing(row)})


@preferences.get("/lifestyle/questions")
@login_required
def get_lifestyle_questions():
    """Return the shared questionnaire in its stable display order."""
    return jsonify({"questions": QUESTIONS})


def serialize_lifestyle(row):
    """Expose one saved answer without accepting or exposing a selectable user ID."""
    return {"question_key": row.question_key, "own_answer": row.own_answer,
            "roommate_answer": row.roommate_answer, "is_requirement": row.is_requirement,
            "updated_at": utc_timestamp(row.updated_at)}


@preferences.get("/lifestyle")
@login_required
def get_lifestyle():
    """Return the current user's saved answers in questionnaire order."""
    rows = db.session.execute(db.select(LifestylePreference).filter_by(user_id=g.user.id)).scalars()
    saved = {row.question_key: row for row in rows}
    return jsonify({"answers": [serialize_lifestyle(saved[question["question_key"]])
                               for question in QUESTIONS if question["question_key"] in saved]})


@preferences.put("/lifestyle/<question_key>")
@login_required
def replace_lifestyle(question_key):
    """Replace one validated answer pair without modifying other questions."""
    question = QUESTIONS_BY_KEY.get(question_key)
    if question is None:
        raise NotFound("Unknown lifestyle question.")
    data = lifestyle_answer(json_object(), question)
    # Serialize first saves as well as replacements using the parent account row.
    db.session.execute(db.select(User).where(User.id == g.user.id).with_for_update()).scalar_one()
    row = db.session.get(LifestylePreference, (g.user.id, question_key))
    if row is None:
        row = LifestylePreference(user_id=g.user.id, question_key=question_key)
        db.session.add(row)
    for field, value in data.items():
        setattr(row, field, value)
    commit_changes()
    return jsonify({"answer": serialize_lifestyle(row)})
