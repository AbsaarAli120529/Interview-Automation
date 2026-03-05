"""Remove is_rule_based and drop template_questions table

Revision ID: c3d4e5f6a7b8
Revises: ebfb639c6ea6
Create Date: 2026-03-05 21:31:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'ebfb639c6ea6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove fixed-template support:
    - Drop template_questions table (if it still exists)
    - Remove is_rule_based column from interview_templates
    """
    # Drop template_questions table if present (may have been dropped in earlier migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'template_questions' in inspector.get_table_names():
        op.drop_table('template_questions')

    # Remove is_rule_based column
    existing_cols = [c['name'] for c in inspector.get_columns('interview_templates')]
    if 'is_rule_based' in existing_cols:
        op.drop_column('interview_templates', 'is_rule_based')


def downgrade() -> None:
    """Restore is_rule_based column. template_questions table is NOT recreated."""
    op.add_column(
        'interview_templates',
        sa.Column(
            'is_rule_based',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        )
    )
