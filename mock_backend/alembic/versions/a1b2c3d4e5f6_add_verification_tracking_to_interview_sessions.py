"""add verification tracking to interview_sessions

Revision ID: a1b2c3d4e5f6
Revises: 512b7bf918c5
Create Date: 2026-03-03 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '71b81e1ac664'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification tracking columns to interview_sessions
    op.execute(text("""
        DO $$ 
        BEGIN
            -- Add face_verification_alerts column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'face_verification_alerts'
            ) THEN
                ALTER TABLE interview_sessions 
                ADD COLUMN face_verification_alerts INTEGER NOT NULL DEFAULT 0;
            END IF;
            
            -- Add voice_verification_alerts column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'voice_verification_alerts'
            ) THEN
                ALTER TABLE interview_sessions 
                ADD COLUMN voice_verification_alerts INTEGER NOT NULL DEFAULT 0;
            END IF;
            
            -- Add last_face_verification column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'last_face_verification'
            ) THEN
                ALTER TABLE interview_sessions 
                ADD COLUMN last_face_verification TIMESTAMP WITH TIME ZONE;
            END IF;
            
            -- Add last_voice_verification column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'last_voice_verification'
            ) THEN
                ALTER TABLE interview_sessions 
                ADD COLUMN last_voice_verification TIMESTAMP WITH TIME ZONE;
            END IF;
            
            -- Add termination_reason column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'termination_reason'
            ) THEN
                ALTER TABLE interview_sessions 
                ADD COLUMN termination_reason VARCHAR;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    op.execute(text("""
        DO $$ 
        BEGIN
            -- Drop columns if they exist
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'face_verification_alerts'
            ) THEN
                ALTER TABLE interview_sessions DROP COLUMN face_verification_alerts;
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'voice_verification_alerts'
            ) THEN
                ALTER TABLE interview_sessions DROP COLUMN voice_verification_alerts;
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'last_face_verification'
            ) THEN
                ALTER TABLE interview_sessions DROP COLUMN last_face_verification;
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'last_voice_verification'
            ) THEN
                ALTER TABLE interview_sessions DROP COLUMN last_voice_verification;
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'interview_sessions' AND column_name = 'termination_reason'
            ) THEN
                ALTER TABLE interview_sessions DROP COLUMN termination_reason;
            END IF;
        END $$;
    """))
