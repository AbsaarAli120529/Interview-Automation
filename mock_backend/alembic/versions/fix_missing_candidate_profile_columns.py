"""Fix missing candidate_profile columns

Revision ID: fix_missing_columns
Revises: 71b81e1ac664
Create Date: 2026-03-03 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'fix_missing_columns'
down_revision: Union[str, Sequence[str], None] = '71b81e1ac664'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add all missing columns to candidate_profiles table safely using raw SQL."""
    # Use raw SQL to add columns only if they don't exist (PostgreSQL syntax)
    op.execute(text("""
        DO $$ 
        BEGIN
            -- Add role_name if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'candidate_profiles' AND column_name = 'role_name'
            ) THEN
                ALTER TABLE candidate_profiles ADD COLUMN role_name VARCHAR;
                CREATE INDEX IF NOT EXISTS ix_candidate_profiles_role_name ON candidate_profiles(role_name);
            END IF;
            
            -- Add resume_filename if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'candidate_profiles' AND column_name = 'resume_filename'
            ) THEN
                ALTER TABLE candidate_profiles ADD COLUMN resume_filename VARCHAR;
            END IF;
            
            -- Add resume_path if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'candidate_profiles' AND column_name = 'resume_path'
            ) THEN
                ALTER TABLE candidate_profiles ADD COLUMN resume_path VARCHAR;
            END IF;
            
            -- Add resume_json if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'candidate_profiles' AND column_name = 'resume_json'
            ) THEN
                ALTER TABLE candidate_profiles ADD COLUMN resume_json JSONB;
            END IF;
            
            -- Add jd_json if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'candidate_profiles' AND column_name = 'jd_json'
            ) THEN
                ALTER TABLE candidate_profiles ADD COLUMN jd_json JSONB;
            END IF;
            
            -- Add match_score if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'candidate_profiles' AND column_name = 'match_score'
            ) THEN
                ALTER TABLE candidate_profiles ADD COLUMN match_score DOUBLE PRECISION;
            END IF;
            
            -- Add parse_status if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'candidate_profiles' AND column_name = 'parse_status'
            ) THEN
                ALTER TABLE candidate_profiles ADD COLUMN parse_status VARCHAR NOT NULL DEFAULT 'pending';
            END IF;
            
            -- Add parsed_at if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'candidate_profiles' AND column_name = 'parsed_at'
            ) THEN
                ALTER TABLE candidate_profiles ADD COLUMN parsed_at TIMESTAMP WITH TIME ZONE;
            END IF;
            
            -- Add resume_text if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'candidate_profiles' AND column_name = 'resume_text'
            ) THEN
                ALTER TABLE candidate_profiles ADD COLUMN resume_text TEXT;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    """Remove the columns (optional - can be left empty for safety)."""
    # Optionally remove columns, but safer to leave them
    pass
