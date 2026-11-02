from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Unbound extensions keep independent application factories isolated.
db = SQLAlchemy()
migrate = Migrate()


def commit_changes():
    """Commit a write or roll it back before returning a safe database failure."""
    from sqlalchemy.exc import SQLAlchemyError
    from werkzeug.exceptions import ServiceUnavailable

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise ServiceUnavailable("The database write failed; please retry.") from None
