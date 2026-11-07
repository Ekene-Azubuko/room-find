"""Identify explicitly seeded discovery profiles without publishing real accounts."""
from alembic import op
import sqlalchemy as sa

revision = "c3e91d8b2a40"
down_revision = "b2f8c41a9d10"
branch_labels = None
depends_on = None


def upgrade():
    """Add an optional unique identifier for the four demo roommates."""
    op.add_column("users", sa.Column("demo_key", sa.String(30), nullable=True))
    op.create_unique_constraint("users_demo_key_key", "users", ["demo_key"])


def downgrade():
    """Remove only the demo identifier, preserving profile and account data."""
    op.drop_constraint("users_demo_key_key", "users", type_="unique")
    op.drop_column("users", "demo_key")
