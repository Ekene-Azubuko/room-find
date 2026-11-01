import os
from datetime import timedelta

from flask import Flask
from sqlalchemy.engine import make_url
from werkzeug.exceptions import HTTPException

from .extensions import db, migrate


def create_app(test_config=None):
    """Configure the application, initialize extensions, and register routes once."""
    app = Flask(__name__)
    app.config.from_mapping(SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
                            SECRET_KEY=os.environ.get("SECRET_KEY"),
                            SESSION_COOKIE_HTTPONLY=True,
                            SESSION_COOKIE_SAMESITE="Lax",
                            SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
                            PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
                            SESSION_REFRESH_EACH_REQUEST=False,
                            SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"options": "-c timezone=UTC"}})
    if test_config is not None:
        app.config.update(test_config)
    database_url = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not database_url or make_url(database_url).drivername != "postgresql+psycopg":
        raise RuntimeError("DATABASE_URL must explicitly use postgresql+psycopg.")

    secret = app.config.get("SECRET_KEY")
    if not isinstance(secret, str) or len(secret) < 32:
        raise RuntimeError("SECRET_KEY must be configured with at least 32 characters.")

    db.init_app(app)
    from . import models
    migrate.init_app(app, db)

    from .auth.routes import auth
    from .health.routes import health
    from .profile.routes import profile
    from .preferences.routes import preferences
    from .errors import json_http_error

    app.register_blueprint(health, url_prefix="/api")
    app.register_blueprint(auth, url_prefix="/api/auth")
    app.register_blueprint(profile, url_prefix="/api/profile")
    app.register_blueprint(preferences, url_prefix="/api/preferences")
    from .auth.security import protect_csrf
    app.before_request(protect_csrf)
    app.register_error_handler(HTTPException, json_http_error)
    return app
