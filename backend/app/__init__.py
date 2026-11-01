import os

from flask import Flask
from sqlalchemy.engine import make_url
from werkzeug.exceptions import HTTPException

from .extensions import db, migrate


def create_app(test_config=None):
    """Configure the application, initialize extensions, and register routes once."""
    app = Flask(__name__)
    app.config.from_mapping(SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
                            SQLALCHEMY_TRACK_MODIFICATIONS=False,
                            SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"options": "-c timezone=UTC"}})
    if test_config is not None:
        app.config.update(test_config)
    database_url = app.config.get("SQLALCHEMY_DATABASE_URI")
    if not database_url or make_url(database_url).drivername != "postgresql+psycopg":
        raise RuntimeError("DATABASE_URL must explicitly use postgresql+psycopg.")

    db.init_app(app)
    from . import models
    migrate.init_app(app, db)

    from .auth.routes import auth
    from .health.routes import health
    from .errors import json_http_error

    app.register_blueprint(health, url_prefix="/api")
    app.register_blueprint(auth, url_prefix="/api/auth")
    app.register_error_handler(HTTPException, json_http_error)
    return app
