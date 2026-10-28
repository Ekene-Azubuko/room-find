from flask import Flask
from pathlib import Path


def create_app(test_config=None):
    """Create the Flask application and register its API routes."""
    app = Flask(__name__)
    app.config["DATABASE"] = str(Path(app.instance_path) / "room_find.sqlite")
    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    from .db import close_db, get_db

    app.teardown_appcontext(close_db)
    with app.app_context():
        database = get_db()
        database.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "id INTEGER PRIMARY KEY, "
            "email TEXT NOT NULL UNIQUE, "
            "password_hash TEXT NOT NULL)"
        )
        database.commit()

    # Import inside the factory to avoid circular imports.
    from .routes import api

    app.register_blueprint(api, url_prefix="/api")
    return app
