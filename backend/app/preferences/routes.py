from flask import Blueprint, g, jsonify

from ..auth.security import login_required
from ..extensions import db
from ..models import HousingPreference, User
from ..serialization import utc_timestamp
from ..validation import json_object
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
