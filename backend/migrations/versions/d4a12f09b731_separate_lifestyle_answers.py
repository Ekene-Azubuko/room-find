"""Retain original combined answers while clearing interpretations the UI did not collect."""
from alembic import op
import sqlalchemy as sa

revision = "d4a12f09b731"
down_revision = "c3e91d8b2a40"
branch_labels = None
depends_on = None


def upgrade():
    """Archive affected pairs and leave ambiguous facts unanswered without inventing data."""
    op.add_column("lifestyle_preferences", sa.Column("legacy_answers", sa.JSON(), nullable=True))
    op.execute("""
        UPDATE lifestyle_preferences SET legacy_answers = json_build_object(
            'own_answer', own_answer, 'roommate_answer', roommate_answer,
            'is_requirement', is_requirement)
        WHERE question_key IN ('pets', 'smoking', 'cleanliness')
    """)
    # Equal values came from the combined UI; their personal meaning is unknown.
    op.execute("""
        UPDATE lifestyle_preferences SET own_answer = NULL
        WHERE (question_key = 'pets' AND own_answer = 'okay_with_pets')
           OR (question_key = 'smoking' AND own_answer = 'any')
           OR (question_key IN ('smoking', 'cleanliness') AND own_answer = roommate_answer)
           OR (question_key = 'pets' AND own_answer = 'no_pets' AND roommate_answer = 'no_pets')
    """)
    op.execute("""
        UPDATE lifestyle_preferences SET roommate_answer = NULL, is_requirement = false
        WHERE (question_key = 'pets' AND roommate_answer = 'has_pets')
           OR (question_key = 'smoking' AND roommate_answer = 'smoker')
    """)
    op.execute("""
        UPDATE lifestyle_preferences SET roommate_answer = 'no_preference', is_requirement = false
        WHERE question_key = 'pets' AND roommate_answer = 'okay_with_pets'
    """)


def downgrade():
    """Restore archived pairs before removing the archive column."""
    op.execute("""
        UPDATE lifestyle_preferences SET own_answer = legacy_answers->>'own_answer',
            roommate_answer = legacy_answers->>'roommate_answer',
            is_requirement = (legacy_answers->>'is_requirement')::boolean
        WHERE legacy_answers IS NOT NULL
    """)
    op.drop_column("lifestyle_preferences", "legacy_answers")
