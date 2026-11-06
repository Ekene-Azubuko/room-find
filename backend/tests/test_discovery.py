from app.extensions import db
from app.models import User


def test_seed_is_repeatable_and_preserves_accounts(app, authenticated_client):
    """Seeding adds exactly four personas without replacing real accounts or edits."""
    runner = app.test_cli_runner()
    result = runner.invoke(args=["seed-roommates"])
    assert result.exit_code == 0, result.output
    assert "Added 4" in result.output
    with app.app_context():
        maya = db.session.execute(db.select(User).filter_by(demo_key="maya")).scalar_one()
        maya.bio = "Preserve this edited bio."
        db.session.commit()
    result = runner.invoke(args=["seed-roommates"])
    assert result.exit_code == 0 and "Added 0" in result.output
    with app.app_context():
        assert len(db.session.execute(db.select(User)).scalars().all()) == 5
        maya = db.session.execute(db.select(User).filter_by(demo_key="maya")).scalar_one()
        assert maya.bio == "Preserve this edited bio."
        assert len(maya.lifestyle_preferences) == 7
        assert maya.housing_preference.neighborhood == "Williamsburg"
    assert authenticated_client.get("/api/auth/me").json["user"]["email"] == "alex@example.com"


def test_discovery_is_private_and_only_lists_demo_profiles(app, client, authenticated_client):
    """The API publishes four seeded profiles without credentials or real accounts."""
    assert app.test_client().get("/api/roommates").status_code == 401
    assert authenticated_client.get("/api/roommates").json == {"roommates": []}
    result = app.test_cli_runner().invoke(args=["seed-roommates"])
    assert result.exit_code == 0, result.output
    response = authenticated_client.get("/api/roommates")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    roommates = response.json["roommates"]
    assert len(roommates) == 4
    assert {user["full_name"] for user in roommates} == {"Maya Chen", "Jordan Ellis", "Priya Nair", "Elena Morales"}
    for user in roommates:
        assert user["is_demo"]
        assert not {"email", "password_hash", "compatibility", "score"} & user.keys()
        assert user["housing"]["budget_min"]
        assert user["lifestyle"]["sleep_schedule"]


def test_seed_collision_rolls_back_without_claiming_real_accounts(app, authenticated_client):
    """A conflicting email fails the whole seed without marking a real user as demo."""
    with app.app_context():
        db.session.add(User(email="jordan@roomly-demo.invalid", password_hash="existing"))
        db.session.commit()
    result = app.test_cli_runner().invoke(args=["seed-roommates"])
    assert result.exit_code != 0
    assert "no changes were saved" in result.output
    assert authenticated_client.get("/api/roommates").json == {"roommates": []}


def test_demo_profiles_cannot_log_in(app, csrf_client):
    """Demo profiles remain non-login identities even if a password hash is changed."""
    from werkzeug.security import generate_password_hash

    assert app.test_cli_runner().invoke(args=["seed-roommates"]).exit_code == 0
    with app.app_context():
        user = db.session.execute(db.select(User).filter_by(demo_key="maya")).scalar_one()
        user.password_hash = generate_password_hash("known-password")
        db.session.commit()
    response = csrf_client.post("/api/auth/login", json={"email": "maya@roomly-demo.invalid", "password": "known-password"})
    assert response.status_code == 401


def test_profile_detail_and_private_account_boundaries(app, authenticated_client):
    """Detail links work for all personas but cannot expose arbitrary account IDs."""
    assert app.test_cli_runner().invoke(args=["seed-roommates"]).exit_code == 0
    roommates = authenticated_client.get("/api/roommates").json["roommates"]
    for roommate in roommates:
        url = f"/api/roommates/{roommate['id']}"
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.json == {"roommate": roommate}
        assert response.headers["Cache-Control"] == "no-store"
        assert app.test_client().get(url).status_code == 401
    own_id = authenticated_client.get("/api/auth/me").json["user"]["id"]
    for roommate_id in (own_id, 99999):
        response = authenticated_client.get(f"/api/roommates/{roommate_id}")
        assert response.status_code == 404
        assert response.json == {"error": "Roommate profile not found."}
