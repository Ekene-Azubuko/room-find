from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Unbound extensions keep independent application factories isolated.
db = SQLAlchemy()
migrate = Migrate()
