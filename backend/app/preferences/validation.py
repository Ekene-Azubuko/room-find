from datetime import date
from decimal import Decimal, InvalidOperation
import re

from werkzeug.exceptions import BadRequest

from ..validation import nullable_text, reject_unknown_fields

ANSWER_FIELDS = {"city", "neighborhood", "budget_min", "budget_max", "move_in_date", "lease_months"}
FLAG_FIELDS = {"city_is_requirement", "neighborhood_is_requirement", "budget_is_requirement", "move_in_is_requirement", "lease_is_requirement"}
WRITABLE_FIELDS = ANSWER_FIELDS | FLAG_FIELDS


def budget_amount(value, field):
    """Validate an exact USD amount within NUMERIC(10,2), without silent rounding."""
    if value is None:
        return None
    if not isinstance(value, (str, int, Decimal)) or isinstance(value, bool):
        raise BadRequest(f"{field} must be a decimal amount or null.")
    if isinstance(value, str) and (not value.strip() or len(value) > 64):
        raise BadRequest(f"{field} must be a decimal amount or null.")
    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise BadRequest(f"{field} must be a decimal amount or null.") from None
    if not amount.is_finite() or not 0 <= amount <= Decimal("99999999.99"):
        raise BadRequest(f"{field} must be between 0 and 99999999.99.")
    rounded = amount.quantize(Decimal("0.01"))
    if rounded != amount:
        raise BadRequest(f"{field} must have at most two decimal places.")
    return rounded if rounded else Decimal("0.00")


def move_in_date(value):
    """Require a real calendar date in the documented YYYY-MM-DD format."""
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise BadRequest("move_in_date must be a valid YYYY-MM-DD date or null.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise BadRequest("move_in_date must be a valid YYYY-MM-DD date or null.") from None


def housing_changes(data):
    """Validate supplied housing fields without changing the saved record."""
    reject_unknown_fields(data, WRITABLE_FIELDS)
    changes = {}
    for field, value in data.items():
        if field in FLAG_FIELDS:
            if type(value) is not bool:
                raise BadRequest(f"{field} must be a Boolean.")
        elif field in {"city", "neighborhood"}:
            value = nullable_text(value, field, 100 if field == "city" else 200, trim=True, allow_blank=False)
        elif field in {"budget_min", "budget_max"}:
            value = budget_amount(value, field)
        elif field == "move_in_date":
            value = move_in_date(value)
        elif value is not None and (type(value) is not int or not 0 < value <= 2147483647):
            raise BadRequest("lease_months must be a positive integer or null (maximum 2147483647).")
        changes[field] = value
    return changes


def housing_state_errors(state):
    """Identify inconsistent budget bounds and flags in the merged answers."""
    errors = {}
    minimum, maximum = state["budget_min"], state["budget_max"]
    if minimum is not None and maximum is not None and minimum > maximum:
        errors["budget_min"] = "budget_min must not exceed budget_max."
    answered = {
        "city_is_requirement": state["city"] is not None,
        "neighborhood_is_requirement": state["neighborhood"] is not None,
        "budget_is_requirement": minimum is not None or maximum is not None,
        "move_in_is_requirement": state["move_in_date"] is not None,
        "lease_is_requirement": state["lease_months"] is not None,
    }
    for field, present in answered.items():
        if state[field] and not present:
            errors[field] = f"{field} requires its corresponding answer."

    return errors


def validate_housing_state(state):
    """Reject inconsistent merged housing answers using shared validation rules."""
    errors = housing_state_errors(state)
    if errors:
        raise BadRequest(next(iter(errors.values())))


def lifestyle_answer(data, question):
    """Validate the complete replacement of one own/roommate answer pair."""
    fields = {"own_answer", "roommate_answer", "is_requirement"}
    reject_unknown_fields(data, fields)
    missing = fields - set(data)
    if missing:
        raise BadRequest("Required fields: " + ", ".join(sorted(missing)) + ".")
    for field, choices in (("own_answer", question["own_answers"]),
                           ("roommate_answer", question["roommate_answers"])):
        value = data[field]
        if value is not None and (not isinstance(value, str) or value not in choices):
            raise BadRequest(f"{field} must be null or a supported choice for {question['question_key']}.")
    if type(data["is_requirement"]) is not bool:
        raise BadRequest("is_requirement must be a Boolean.")
    if data["is_requirement"] and data["roommate_answer"] in (None, "no_preference"):
        raise BadRequest("is_requirement requires a specific roommate_answer.")
    return data
