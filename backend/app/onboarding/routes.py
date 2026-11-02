from flask import Blueprint, g, jsonify, request

from ..auth.security import login_required
from ..extensions import commit_changes
from ..models import lock_user, utc_now
from ..validation import json_object, reject_unknown_fields
from .state import onboarding_state

onboarding = Blueprint("onboarding", __name__)


@onboarding.get("")
@login_required
def get_onboarding():
    """Report saved progress without changing the completion marker."""
    return jsonify({"onboarding": onboarding_state(g.user)})


@onboarding.post("/complete")
@login_required
def complete_onboarding():
    """Mark eligible saved data complete while preserving an existing timestamp."""
    if request.content_length or request.is_json:
        reject_unknown_fields(json_object(), set())
    user = lock_user(g.user.id)
    state = onboarding_state(user)
    if not state["eligible"]:
        return jsonify({"error": "Onboarding is incomplete or invalid.", "onboarding": state}), 400
    if user.onboarding_completed_at is None:
        user.onboarding_completed_at = utc_now()
    commit_changes()
    return jsonify({"onboarding": onboarding_state(user)})
