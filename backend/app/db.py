import sqlite3

from flask import current_app, g


def get_db():
    """Open one SQLite connection per application context."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(error=None):
    """Close the database connection when the application context ends."""
    database = g.pop("db", None)
    if database is not None:
        database.close()
