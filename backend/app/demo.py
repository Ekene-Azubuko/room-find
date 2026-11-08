"""Explicit, repeatable seed data for the current discovery increment."""
import secrets
from datetime import date

import click
from flask.cli import with_appcontext
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash

from .extensions import db
from .models import HousingPreference, LifestylePreference, User

PERSONAS = [
    {"key": "maya", "full_name": "Maya Chen", "age": 24,
     "occupation": "Product design intern", "life_stage": "Young professional",
     "bio": "Relocating from Seattle for a year-long product design internship. I love a calm home during the week, trying new restaurants, and hosting the occasional dinner.",
     "city": "Brooklyn", "neighborhood": "Williamsburg", "budget": (1600, 1900), "move_in": "2027-01-01",
     "lifestyle": {"sleep_schedule": "early", "cleanliness": "tidy", "smoking": "non_smoker", "pets": "no_pets", "noise": "2", "daytime_visitors": "1_2", "overnight_guests": "less_than_weekly", "roommate_dynamic": "friendly"}},
    {"key": "jordan", "full_name": "Jordan Ellis", "age": 26,
     "occupation": "Software engineer", "life_stage": "Working professional",
     "bio": "Usually coding, cycling, or looking for a new coffee spot. I keep shared spaces neat and enjoy a quiet evening at home. My cat Juniper is part of the move.",
     "city": "Brooklyn", "neighborhood": "Greenpoint", "budget": (1700, 2100), "move_in": "2027-01-15",
     "lifestyle": {"sleep_schedule": "late", "cleanliness": "very_tidy", "smoking": "non_smoker", "pets": "has_pets", "noise": "1", "daytime_visitors": "less_than_weekly", "overnight_guests": "never", "roommate_dynamic": "independent"}},
    {"key": "priya", "full_name": "Priya Nair", "age": 25,
     "occupation": "Graduate student", "life_stage": "Student",
     "bio": "Studying urban planning and exploring the city one neighborhood at a time. Looking for a friendly home with space to study, cook together, and unwind.",
     "city": "Brooklyn", "neighborhood": "Bushwick", "budget": (1300, 1700), "move_in": "2027-02-01",
     "lifestyle": {"sleep_schedule": "flexible", "cleanliness": "moderately_tidy", "smoking": "non_smoker", "pets": "no_pets", "noise": "3", "daytime_visitors": "1_2", "overnight_guests": "less_than_weekly", "roommate_dynamic": "close_friends"}},
    {"key": "elena", "full_name": "Elena Morales", "age": 27,
     "occupation": "Marketing strategist", "life_stage": "Working professional",
     "bio": "An early riser who loves weekend markets, live music, and experimenting in the kitchen. Hoping to find a considerate roommate who enjoys a little conversation over dinner.",
     "city": "Queens", "neighborhood": "Astoria", "budget": (1400, 1800), "move_in": "2027-02-15",
     "lifestyle": {"sleep_schedule": "early", "cleanliness": "tidy", "smoking": "outside_only", "pets": "no_pets", "noise": "2", "daytime_visitors": "3_4", "overnight_guests": "1_2", "roommate_dynamic": "friendly"}},
]
DEMO_KEYS = tuple(persona["key"] for persona in PERSONAS)


@click.command("seed-roommates")
@with_appcontext
def seed_roommates():
    """Insert missing demo personas without replacing existing accounts or answers."""
    added = 0
    try:
        for persona in PERSONAS:
            if db.session.execute(db.select(User.id).filter_by(demo_key=persona["key"])).scalar_one_or_none():
                continue
            user = User(demo_key=persona["key"], email=f"{persona['key']}@roomly-demo.invalid",
                        password_hash=generate_password_hash(secrets.token_urlsafe(48)),
                        **{field: persona[field] for field in ("full_name", "age", "occupation", "life_stage", "bio")})
            user.housing_preference = HousingPreference(
                city=persona["city"], neighborhood=persona["neighborhood"],
                budget_min=persona["budget"][0], budget_max=persona["budget"][1],
                move_in_date=date.fromisoformat(persona["move_in"]), lease_months=12)
            user.lifestyle_preferences = [
                LifestylePreference(question_key=key, own_answer=value, roommate_answer="no_preference")
                for key, value in persona["lifestyle"].items()]
            db.session.add(user)
            added += 1
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise click.ClickException("Could not seed roommates; no changes were saved. Check migrations and demo email conflicts.") from error
    click.echo(f"Added {added} demo roommates; existing profiles were preserved.")
