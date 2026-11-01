import re

from flask import request
from werkzeug.exceptions import BadRequest, UnsupportedMediaType


def json_object():
    """Require a JSON object before validating its individual fields."""
    if not request.is_json:
        raise UnsupportedMediaType("Content-Type must be application/json.")
    data = request.get_json(silent=True)
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
