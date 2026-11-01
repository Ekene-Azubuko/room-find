import json
import re
from decimal import Decimal, InvalidOperation

from flask import request
from werkzeug.exceptions import BadRequest, UnsupportedMediaType


def json_object():
    """Require a JSON object before validating its individual fields."""
    if not request.is_json:
        raise UnsupportedMediaType("Content-Type must be application/json.")
    try:
        # Parse decimal JSON numbers exactly so money never passes through a float.
        data = json.loads(request.get_data(), parse_float=Decimal)
    except (ValueError, InvalidOperation):
        raise BadRequest("Request body must be a valid JSON object.") from None
    if not isinstance(data, dict):
        raise BadRequest("Request body must be a valid JSON object.")
    return data


def normalize_email(value):
    """Validate and normalize the email used for identity and uniqueness."""
    if not isinstance(value, str):
        raise BadRequest("A valid email is required.")
    value = value.strip().lower()
    if len(value) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise BadRequest("A valid email is required.")
    return value


def reject_unknown_fields(data, allowed):
    """Reject client fields outside the endpoint's explicit writable set."""
    unknown = set(data) - set(allowed)
    if unknown:
        raise BadRequest("Unknown or read-only fields: " + ", ".join(sorted(unknown)) + ".")


def nullable_text(value, field, maximum, trim=False, allow_blank=True):
    """Validate nullable text and optionally normalize surrounding whitespace."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise BadRequest(f"{field} must be a string or null.")
    if trim:
        value = value.strip()
    if len(value) > maximum:
        raise BadRequest(f"{field} must contain at most {maximum} characters.")
    if not allow_blank and not value.strip():
        raise BadRequest(f"{field} must not be blank.")
    return value
