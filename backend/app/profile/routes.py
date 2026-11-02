from flask import Blueprint, g, jsonify

from ..auth.security import login_required
from ..models import lock_user
from ..onboarding.state import save_user_answers
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
        changes[field] = nullable_text(value, field, 100 if field == "full_name" else 1000,
                                       trim=field == "full_name", allow_blank=field != "full_name")
    user = lock_user(g.user.id)
    for field, value in changes.items():
        setattr(user, field, value)
    save_user_answers(user)
    return jsonify({"profile": serialize_profile(g.user)})
