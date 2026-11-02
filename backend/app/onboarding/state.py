from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest, ServiceUnavailable

from ..extensions import commit_changes, db
from ..models import HousingPreference, LifestylePreference
from ..preferences.questions import QUESTIONS, QUESTIONS_BY_KEY
from ..preferences.validation import WRITABLE_FIELDS, housing_changes, housing_state_errors, lifestyle_answer
from ..serialization import utc_timestamp
from ..validation import nullable_text

REQUIRED_HOUSING_FIELDS = ("city", "budget_min", "budget_max", "move_in_date", "lease_months")


def onboarding_state(user):
    """Derive missing and invalid answers from saved data using shared validators."""
    missing = []
    errors = {}
    if user.full_name is None or (isinstance(user.full_name, str) and not user.full_name.strip()):
        missing.append("profile.full_name")
    for field, maximum in (("full_name", 100), ("bio", 1000)):
        try:
            nullable_text(getattr(user, field), field, maximum, trim=field == "full_name",
                          allow_blank=field != "full_name")
        except BadRequest as error:
            errors[f"profile.{field}"] = error.description

    housing = db.session.get(HousingPreference, user.id)
    if housing is None:
        missing.extend(f"housing.{field}" for field in REQUIRED_HOUSING_FIELDS)
    else:
        state = {field: getattr(housing, field) for field in WRITABLE_FIELDS}
        for field in REQUIRED_HOUSING_FIELDS:
            if state[field] is None or (field == "city" and not state[field].strip()):
                missing.append(f"housing.{field}")
        # API dates are strings; convert the saved date before using the same validator.
        data = {**state, "move_in_date": housing.move_in_date.isoformat() if housing.move_in_date else None}
        for field, value in data.items():
            try:
                housing_changes({field: value})
            except BadRequest as error:
                errors[f"housing.{field}"] = error.description
        if not any(key.startswith("housing.") for key in errors):
            errors.update({f"housing.{field}": message for field, message in housing_state_errors(state).items()})

    rows = db.session.execute(db.select(LifestylePreference).filter_by(user_id=user.id)).scalars().all()
    saved = {row.question_key: row for row in rows}
    for question in QUESTIONS:
        row = saved.get(question["question_key"])
        if question["required_for_onboarding"]:
            for field in ("own_answer", "roommate_answer"):
                if row is None or getattr(row, field) is None:
                    missing.append(f"lifestyle.{question['question_key']}.{field}")
    for row in rows:
        question = QUESTIONS_BY_KEY.get(row.question_key)
        if question is None:
            errors[f"lifestyle.{row.question_key}"] = "Unknown lifestyle question."
            continue
        try:
            lifestyle_answer({"own_answer": row.own_answer, "roommate_answer": row.roommate_answer,
                              "is_requirement": row.is_requirement}, question)
        except BadRequest as error:
            errors[f"lifestyle.{row.question_key}"] = error.description
    for field in missing:
        errors.setdefault(field, "An answer is required.")
    eligible = not errors
    return {"completed": user.onboarding_completed_at is not None and eligible,
            "onboarding_completed_at": utc_timestamp(user.onboarding_completed_at),
            "eligible": eligible, "missing_fields": missing, "errors": errors}


def save_user_answers(user):
    """Save edits and reset invalidated completion together in one transaction."""
    try:
        if user.onboarding_completed_at is not None and not onboarding_state(user)["eligible"]:
            user.onboarding_completed_at = None
        commit_changes()
    except SQLAlchemyError:
        # Eligibility queries can autoflush edits before the final commit.
        db.session.rollback()
        raise ServiceUnavailable("The database write failed; please retry.") from None
