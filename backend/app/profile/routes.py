from io import BytesIO

from flask import Blueprint, g, jsonify, request, send_file
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.exceptions import BadRequest, NotFound

from ..auth.security import login_required
from ..models import lock_user
from ..onboarding.state import save_user_answers
from ..serialization import utc_timestamp
from ..validation import json_object, nullable_text, reject_unknown_fields

profile = Blueprint("profile", __name__)


def serialize_profile(user):
    """Expose profile fields and account metadata without credential material."""
    return {**user.public_identity(), "full_name": user.full_name, "bio": user.bio,
            "age": user.age, "occupation": user.occupation, "life_stage": user.life_stage,
            "photo_url": "/api/profile/photo" if user.photo else None,
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
    reject_unknown_fields(data, {"full_name", "bio", "age", "occupation", "life_stage"})
    changes = {}
    for field, value in data.items():
        if field == "age":
            if value is not None and (type(value) is not int or not 18 <= value <= 120):
                raise BadRequest("age must be an integer between 18 and 120 or null.")
            changes[field] = value
        elif field == "life_stage":
            if value is not None and value not in ("Student", "Young professional", "Working professional", "Other"):
                raise BadRequest("life_stage must be a supported choice or null.")
            changes[field] = value
        else:
            changes[field] = nullable_text(value, field, 1000 if field == "bio" else 100,
                                           trim=field != "bio", allow_blank=field != "full_name")
    user = lock_user(g.user.id)
    for field, value in changes.items():
        setattr(user, field, value)
    save_user_answers(user)
    return jsonify({"profile": serialize_profile(g.user)})


@profile.put("/photo")
@login_required
def upload_photo():
    """Validate and normalize a bounded JPEG or PNG before storing it on the account."""
    request.max_content_length = 5 * 1024 * 1024 + 65536
    upload = request.files.get("photo")
    if upload is None:
        raise BadRequest("Choose a JPG or PNG photo.")
    content = upload.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise BadRequest("Photo must be 5 MB or smaller.")
    try:
        with Image.open(BytesIO(content)) as source:
            if source.format not in {"JPEG", "PNG"} or source.width * source.height > 25000000:
                raise BadRequest("Choose a JPG or PNG photo up to 25 megapixels.")
            photo = ImageOps.exif_transpose(source).convert("RGB")
            photo.thumbnail((512, 512))
            output = BytesIO()
            # Re-encoding strips metadata and prevents serving arbitrary uploaded bytes.
            photo.save(output, format="JPEG", quality=85)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise BadRequest("The photo could not be read. Choose a valid JPG or PNG.") from None
    user = lock_user(g.user.id)
    user.photo = output.getvalue()
    save_user_answers(user)
    return jsonify({"profile": serialize_profile(user)})


@profile.get("/photo")
@login_required
def get_photo():
    """Serve only the authenticated account's normalized profile photo."""
    if not g.user.photo:
        raise NotFound("No profile photo has been uploaded.")
    response = send_file(BytesIO(g.user.photo), mimetype="image/jpeg")
    response.headers["Cache-Control"] = "private, no-store"
    return response
