"""Create users housing and lifestyle preferences

Revision ID: 607cab6b5c7b
Revises: 
Create Date: 2026-11-01 01:45:25.904029

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '607cab6b5c7b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create account and preference tables with PostgreSQL constraints."""
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.Text(), nullable=False),
    sa.Column('full_name', sa.String(length=100), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('housing_preferences',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('budget_min', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('budget_max', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('move_in_date', sa.Date(), nullable=True),
    sa.Column('lease_months', sa.Integer(), nullable=True),
    sa.Column('city_is_requirement', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('budget_is_requirement', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('move_in_is_requirement', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('lease_is_requirement', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('budget_max >= 0', name='housing_budget_max_nonnegative'),
    sa.CheckConstraint('budget_min <= budget_max', name='housing_budget_order'),
    sa.CheckConstraint('budget_min >= 0', name='housing_budget_min_nonnegative'),
    sa.CheckConstraint('lease_months > 0', name='housing_lease_positive'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('lifestyle_preferences',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('question_key', sa.String(length=50), nullable=False),
    sa.Column('own_answer', sa.String(length=100), nullable=True),
    sa.Column('roommate_answer', sa.String(length=100), nullable=True),
    sa.Column('is_requirement', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'question_key')
    )


def downgrade():
    """Remove the initial schema in dependent-first order."""
    op.drop_table('lifestyle_preferences')
    op.drop_table('housing_preferences')
    op.drop_table('users')
