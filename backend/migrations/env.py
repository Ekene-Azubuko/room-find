from logging.config import fileConfig

from alembic import context
from flask import current_app

config = context.config
fileConfig(config.config_file_name)
db = current_app.extensions["migrate"].db


def run_migrations_offline():
    """Render migration SQL without connecting to the database."""
    context.configure(url=db.engine.url.render_as_string(hide_password=False),
                      target_metadata=db.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Apply or generate migrations using the application's configured engine."""
    with db.engine.connect() as connection:
        context.configure(connection=connection, target_metadata=db.metadata,
                          **current_app.extensions["migrate"].configure_args)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
