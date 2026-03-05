"""create interview_responses table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-03 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create interview_responses table
    op.execute(text("""
        DO $$ 
        BEGIN
            -- Create interview_responses table if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'interview_responses'
            ) THEN
                CREATE TABLE interview_responses (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL,
                    question_id UUID NOT NULL,
                    answer_text TEXT,
                    answer_audio_url VARCHAR,
                    answer_mode VARCHAR NOT NULL,
                    ai_score DOUBLE PRECISION,
                    ai_feedback TEXT,
                    evaluation_json JSONB,
                    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    CONSTRAINT fk_interview_responses_session_id 
                        FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
                    CONSTRAINT fk_interview_responses_question_id 
                        FOREIGN KEY (question_id) REFERENCES interview_session_questions(id) ON DELETE CASCADE
                );
                
                CREATE INDEX ix_interview_responses_session_id 
                    ON interview_responses(session_id);
                CREATE INDEX ix_interview_responses_question_id 
                    ON interview_responses(question_id);
                    
                RAISE NOTICE 'Created interview_responses table';
            ELSE
                RAISE NOTICE 'Table interview_responses already exists';
            END IF;
        END $$;
    """))


def downgrade() -> None:
    op.execute(text("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'interview_responses'
            ) THEN
                DROP TABLE interview_responses;
            END IF;
        END $$;
    """))
