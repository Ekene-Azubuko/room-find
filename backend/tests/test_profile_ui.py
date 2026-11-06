from io import BytesIO

import pytest
from PIL import Image


def photo_bytes():
    """Create a valid in-memory upload with known dimensions for normalization checks."""
    content = BytesIO()
    Image.new("RGB", (800, 600), "green").save(content, "PNG")
    content.seek(0)
    return content


def test_ui_profile_and_neighborhood_persist(authenticated_client):
    """Persist the new screen fields and reject invalid changes atomically."""
    fields = {"age": 24, "occupation": "UX researcher", "life_stage": "Young professional"}
    assert authenticated_client.patch("/api/profile", json=fields).status_code == 200
    saved = authenticated_client.get("/api/profile").json["profile"]
    assert all(saved[key] == value for key, value in fields.items())
    for changes in ({"age": True}, {"age": 17}, {"age": 121}, {"occupation": "x" * 101}, {"life_stage": "unsupported"}):
        assert authenticated_client.patch("/api/profile", json=changes).status_code == 400
        assert authenticated_client.get("/api/profile").json["profile"] == saved
    response = authenticated_client.patch("/api/preferences/housing", json={"city": "New York", "neighborhood": " Williamsburg ", "neighborhood_is_requirement": True})
    assert response.status_code == 200
    assert response.json["housing"]["neighborhood"] == "Williamsburg"
    assert authenticated_client.patch("/api/preferences/housing", json={"neighborhood": None}).status_code == 400


def test_photo_normalization_and_authentication(authenticated_client, app):
    """Normalize accepted uploads and keep image bytes behind session authentication."""
    response = authenticated_client.put("/api/profile/photo", data={"photo": (photo_bytes(), "portrait.png")})
    assert response.status_code == 200
    assert response.json["profile"]["photo_url"] == "/api/profile/photo"
    response = authenticated_client.get("/api/profile/photo")
    assert response.status_code == 200 and response.mimetype == "image/jpeg"
    with Image.open(BytesIO(response.data)) as photo:
        assert photo.size == (512, 384)
    assert response.headers["Cache-Control"] == "private, no-store"
    assert app.test_client().get("/api/profile/photo").status_code == 401


@pytest.mark.parametrize("content", [b"not an image", b"x" * (5 * 1024 * 1024 + 1)])
def test_invalid_photo_preserves_existing_image(authenticated_client, content):
    """Reject malformed or oversized photos without overwriting the saved image."""
    authenticated_client.put("/api/profile/photo", data={"photo": (photo_bytes(), "portrait.png")})
    original = authenticated_client.get("/api/profile/photo").data
    response = authenticated_client.put("/api/profile/photo", data={"photo": (BytesIO(content), "bad.png")})
    assert response.status_code in (400, 413)
    assert authenticated_client.get("/api/profile/photo").data == original
