"""Add question_type, coding_problem_id, conversation_round to interview_session_questions

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-05 21:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Extend interview_session_questions to support three question types:
    - question_type: discriminator column (technical / coding / conversational)
    - coding_problem_id: FK to coding_problems
    - conversation_round: round number (1-based) for conversational entries
    """
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c['name'] for c in inspector.get_columns('interview_session_questions')}

    # Add question_type column (default existing rows to 'technical')
    if 'question_type' not in existing_cols:
        op.add_column(
            'interview_session_questions',
            sa.Column(
                'question_type',
                sa.String(20),
                nullable=False,
                server_default='technical'
            )
        )

    # Add coding_problem_id FK
    if 'coding_problem_id' not in existing_cols:
        op.add_column(
            'interview_session_questions',
            sa.Column('coding_problem_id', sa.UUID(), nullable=True)
        )
        op.create_foreign_key(
            'fk_isq_coding_problem_id',
            'interview_session_questions',
            'coding_problems',
            ['coding_problem_id'],
            ['id'],
            ondelete='SET NULL'
        )

    # Add conversation_round column
    if 'conversation_round' not in existing_cols:
        op.add_column(
            'interview_session_questions',
            sa.Column('conversation_round', sa.Integer(), nullable=True)
        )

    # Drop old single-payload check constraint if it exists
    constraints = {c['name'] for c in inspector.get_check_constraints('interview_session_questions')}
    if 'check_question_or_custom_text' in constraints:
        op.drop_constraint('check_question_or_custom_text', 'interview_session_questions', type_='check')

    # Add new question_type check constraint
    if 'check_session_question_type' not in constraints:
        op.create_check_constraint(
            'check_session_question_type',
            'interview_session_questions',
            "question_type IN ('technical', 'coding', 'conversational')"
        )

    # Add new payload check constraint
    if 'check_question_payload' not in constraints:
        op.create_check_constraint(
            'check_question_payload',
            'interview_session_questions',
            "(question_type = 'technical' AND question_id IS NOT NULL) OR "
            "(question_type = 'coding' AND coding_problem_id IS NOT NULL) OR "
            "(question_type = 'conversational' AND conversation_round IS NOT NULL) OR "
            "(custom_text IS NOT NULL)"
        )


def downgrade() -> None:
    """Remove the three new columns and restore old check constraint."""
    op.drop_constraint('check_question_payload', 'interview_session_questions', type_='check')
    op.drop_constraint('check_session_question_type', 'interview_session_questions', type_='check')
    op.drop_constraint('fk_isq_coding_problem_id', 'interview_session_questions', type_='foreignkey')
    op.drop_column('interview_session_questions', 'conversation_round')
    op.drop_column('interview_session_questions', 'coding_problem_id')
    op.drop_column('interview_session_questions', 'question_type')
    op.create_check_constraint(
        'check_question_or_custom_text',
        'interview_session_questions',
        '(question_id IS NOT NULL) OR (custom_text IS NOT NULL)'
    )
