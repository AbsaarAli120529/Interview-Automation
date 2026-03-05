"""add_role_fields_to_template

Revision ID: 1dfa96dbbe22
Revises: 512b7bf918c5
Create Date: 2026-03-02 22:43:43.766417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dfa96dbbe22'
down_revision: Union[str, Sequence[str], None] = '512b7bf918c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Use PostgreSQL DO block to safely add columns if they don't exist
    from sqlalchemy import text
    op.execute(text("""
        DO $$ 
        BEGIN
            -- Add role_name if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_templates' AND column_name = 'role_name'
            ) THEN
                ALTER TABLE interview_templates ADD COLUMN role_name VARCHAR;
            END IF;
            
            -- Add is_default_for_role if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_templates' AND column_name = 'is_default_for_role'
            ) THEN
                ALTER TABLE interview_templates ADD COLUMN is_default_for_role BOOLEAN NOT NULL DEFAULT false;
            END IF;
            
            -- Add is_rule_based if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_templates' AND column_name = 'is_rule_based'
            ) THEN
                ALTER TABLE interview_templates ADD COLUMN is_rule_based BOOLEAN NOT NULL DEFAULT false;
            END IF;
        END $$;
    """))
    
    # Alter description column type if needed
    op.alter_column('interview_templates', 'description',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=True)
    
    # Create index if it doesn't exist
    op.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_interview_templates_role_name 
        ON interview_templates(role_name);
    """))


def downgrade() -> None:
    """Downgrade schema."""
    from sqlalchemy import text
    op.execute(text("DROP INDEX IF EXISTS ix_interview_templates_role_name"))
    op.alter_column('interview_templates', 'description',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=True)
    
    # Drop columns if they exist
    op.execute(text("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_templates' AND column_name = 'is_rule_based'
            ) THEN
                ALTER TABLE interview_templates DROP COLUMN is_rule_based;
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_templates' AND column_name = 'is_default_for_role'
            ) THEN
                ALTER TABLE interview_templates DROP COLUMN is_default_for_role;
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_templates' AND column_name = 'role_name'
            ) THEN
                ALTER TABLE interview_templates DROP COLUMN role_name;
            END IF;
        END $$;
    """))
