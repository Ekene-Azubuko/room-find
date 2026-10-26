from flask import Flask


def create_app():
    """Create the Flask application and register its API routes."""
    app = Flask(__name__)

    # Import inside the factory to avoid circular imports.
    from .routes import api

    app.register_blueprint(api, url_prefix="/api")
    return app
