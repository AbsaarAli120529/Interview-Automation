"""add report_json column to interviews

Revision ID: 933d04d2d5f1
Revises: 6f15ea94e0a8
Create Date: 2026-03-10 05:17:56.819356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '933d04d2d5f1'
down_revision: Union[str, Sequence[str], None] = '6f15ea94e0a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "interviews",
        sa.Column("report_json", sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("interviews", "report_json")
