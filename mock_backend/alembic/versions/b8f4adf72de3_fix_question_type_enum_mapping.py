"""fix question_type enum mapping

Revision ID: b8f4adf72de3
Revises: b2c3d4e5f6a7
Create Date: 2026-03-05 16:08:07.590527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8f4adf72de3'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("UPDATE questions SET question_type = LOWER(question_type::text)::questiontype")


def downgrade() -> None:
    """Downgrade schema."""
    pass
