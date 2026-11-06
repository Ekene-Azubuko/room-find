"""Add fields used by the profile setup screens.

Revision ID: b2f8c41a9d10
Revises: 607cab6b5c7b
"""
from alembic import op
import sqlalchemy as sa

revision = "b2f8c41a9d10"
down_revision = "607cab6b5c7b"
branch_labels = None
depends_on = None


def upgrade():
    """Add nullable profile details and neighborhood without changing existing answers."""
    op.add_column("users", sa.Column("age", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("occupation", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("life_stage", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("photo", sa.LargeBinary(), nullable=True))
    op.add_column("housing_preferences", sa.Column("neighborhood", sa.String(200), nullable=True))
    op.add_column("housing_preferences", sa.Column("neighborhood_is_requirement", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    """Remove the UI-specific fields when explicitly downgrading this migration."""
    op.drop_column("housing_preferences", "neighborhood_is_requirement")
    op.drop_column("housing_preferences", "neighborhood")
    for field in ("photo", "life_stage", "occupation", "age"):
        op.drop_column("users", field)
