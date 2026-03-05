#!/usr/bin/env python3
"""
Quick fix script to create interview_responses table.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def fix_interview_responses():
    """Create interview_responses table."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("Creating interview_responses table...")
            
            fix_sql = """
            DO $$ 
            BEGIN
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
                    
                    CREATE INDEX IF NOT EXISTS ix_interview_responses_session_id 
                        ON interview_responses(session_id);
                    CREATE INDEX IF NOT EXISTS ix_interview_responses_question_id 
                        ON interview_responses(question_id);
                    
                    RAISE NOTICE 'Created interview_responses table';
                ELSE
                    RAISE NOTICE 'Table interview_responses already exists';
                END IF;
            END $$;
            """
            
            await conn.execute(text(fix_sql))
            print("✓ Successfully created interview_responses table!")
            
    except Exception as e:
        print(f"✗ Error creating interview_responses table: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_interview_responses())
