from flask import Blueprint, g, jsonify
from werkzeug.exceptions import BadRequest

from ..auth.security import login_required
from ..extensions import db
from ..serialization import utc_timestamp
from ..validation import json_object, nullable_text, reject_unknown_fields

profile = Blueprint("profile", __name__)


def serialize_profile(user):
    """Expose profile fields and account metadata without credential material."""
    return {**user.public_identity(), "full_name": user.full_name, "bio": user.bio,
            "onboarding_completed_at": utc_timestamp(user.onboarding_completed_at),
            "created_at": utc_timestamp(user.created_at), "updated_at": utc_timestamp(user.updated_at)}


@profile.get("")
@login_required
def get_profile():
    """Read the authenticated user's profile."""
    return jsonify({"profile": serialize_profile(g.user)})


@profile.patch("")
@login_required
def update_profile():
    """Validate a partial profile change before saving it to the current user."""
    data = json_object()
    reject_unknown_fields(data, {"full_name", "bio"})
    changes = {}
    for field, value in data.items():
        if value is None and g.user.onboarding_completed_at is not None:
            raise BadRequest("Completed profiles cannot clear profile fields.")
        changes[field] = nullable_text(value, field, 100 if field == "full_name" else 1000,
                                       trim=field == "full_name", allow_blank=field != "full_name")
    for field, value in changes.items():
        setattr(g.user, field, value)
    db.session.commit()
    return jsonify({"profile": serialize_profile(g.user)})
