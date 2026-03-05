#!/usr/bin/env python3
"""Direct script to create interview_responses table"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def create_table():
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("Creating interview_responses table...")
            
            # Drop table if exists (for testing)
            # await conn.execute(text("DROP TABLE IF EXISTS interview_responses CASCADE;"))
            
            sql = """
            CREATE TABLE IF NOT EXISTS interview_responses (
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
            """
            await conn.execute(text(sql))
            print("✓ Created interview_responses table")
            
            # Create indexes
            index1_sql = """
            CREATE INDEX IF NOT EXISTS ix_interview_responses_session_id 
            ON interview_responses(session_id);
            """
            await conn.execute(text(index1_sql))
            print("✓ Created index on session_id")
            
            index2_sql = """
            CREATE INDEX IF NOT EXISTS ix_interview_responses_question_id 
            ON interview_responses(question_id);
            """
            await conn.execute(text(index2_sql))
            print("✓ Created index on question_id")
            
            print("\n✓ Successfully created interview_responses table and indexes!")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_table())
