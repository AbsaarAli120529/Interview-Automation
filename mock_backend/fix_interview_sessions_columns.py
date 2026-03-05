#!/usr/bin/env python3
"""
Quick fix script to add verification tracking columns to interview_sessions table.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def fix_interview_sessions():
    """Add verification tracking columns to interview_sessions table."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    try:
        async with engine.begin() as conn:
            print("Adding verification tracking columns to interview_sessions...")
            
            fix_sql = """
            DO $$ 
            BEGIN
                -- Add face_verification_alerts
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'face_verification_alerts'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN face_verification_alerts INTEGER NOT NULL DEFAULT 0;
                    RAISE NOTICE 'Added column: face_verification_alerts';
                ELSE
                    RAISE NOTICE 'Column face_verification_alerts already exists';
                END IF;
                
                -- Add voice_verification_alerts
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'voice_verification_alerts'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN voice_verification_alerts INTEGER NOT NULL DEFAULT 0;
                    RAISE NOTICE 'Added column: voice_verification_alerts';
                ELSE
                    RAISE NOTICE 'Column voice_verification_alerts already exists';
                END IF;
                
                -- Add last_face_verification
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'last_face_verification'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN last_face_verification TIMESTAMP WITH TIME ZONE;
                    RAISE NOTICE 'Added column: last_face_verification';
                ELSE
                    RAISE NOTICE 'Column last_face_verification already exists';
                END IF;
                
                -- Add last_voice_verification
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'last_voice_verification'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN last_voice_verification TIMESTAMP WITH TIME ZONE;
                    RAISE NOTICE 'Added column: last_voice_verification';
                ELSE
                    RAISE NOTICE 'Column last_voice_verification already exists';
                END IF;
                
                -- Add termination_reason
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'termination_reason'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN termination_reason VARCHAR;
                    RAISE NOTICE 'Added column: termination_reason';
                ELSE
                    RAISE NOTICE 'Column termination_reason already exists';
                END IF;
            END $$;
            """
            
            await conn.execute(text(fix_sql))
            print("✓ Successfully added verification tracking columns to interview_sessions!")
            
    except Exception as e:
        print(f"✗ Error fixing interview_sessions schema: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_interview_sessions())
