#!/usr/bin/env python3
"""
Quick fix script to add missing columns to candidate_profiles table.
Run this script to fix the database schema without running full migrations.
"""

import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def fix_database_schema():
    """Add all missing columns to candidate_profiles and interview_templates tables."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    try:
        async with engine.begin() as conn:
            print("Checking and adding missing columns...")
            
            # SQL to add all missing columns if they don't exist
            fix_sql = """
            DO $$ 
            BEGIN
                -- Add role_name if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'candidate_profiles' AND column_name = 'role_name'
                ) THEN
                    ALTER TABLE candidate_profiles ADD COLUMN role_name VARCHAR;
                    CREATE INDEX IF NOT EXISTS ix_candidate_profiles_role_name ON candidate_profiles(role_name);
                    RAISE NOTICE 'Added column: role_name';
                END IF;
                
                -- Add resume_filename if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'candidate_profiles' AND column_name = 'resume_filename'
                ) THEN
                    ALTER TABLE candidate_profiles ADD COLUMN resume_filename VARCHAR;
                    RAISE NOTICE 'Added column: resume_filename';
                END IF;
                
                -- Add resume_path if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'candidate_profiles' AND column_name = 'resume_path'
                ) THEN
                    ALTER TABLE candidate_profiles ADD COLUMN resume_path VARCHAR;
                    RAISE NOTICE 'Added column: resume_path';
                END IF;
                
                -- Add resume_json if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'candidate_profiles' AND column_name = 'resume_json'
                ) THEN
                    ALTER TABLE candidate_profiles ADD COLUMN resume_json JSONB;
                    RAISE NOTICE 'Added column: resume_json';
                END IF;
                
                -- Add jd_json if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'candidate_profiles' AND column_name = 'jd_json'
                ) THEN
                    ALTER TABLE candidate_profiles ADD COLUMN jd_json JSONB;
                    RAISE NOTICE 'Added column: jd_json';
                END IF;
                
                -- Add match_score if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'candidate_profiles' AND column_name = 'match_score'
                ) THEN
                    ALTER TABLE candidate_profiles ADD COLUMN match_score DOUBLE PRECISION;
                    RAISE NOTICE 'Added column: match_score';
                END IF;
                
                -- Add parse_status if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'candidate_profiles' AND column_name = 'parse_status'
                ) THEN
                    ALTER TABLE candidate_profiles ADD COLUMN parse_status VARCHAR NOT NULL DEFAULT 'pending';
                    RAISE NOTICE 'Added column: parse_status';
                END IF;
                
                -- Add parsed_at if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'candidate_profiles' AND column_name = 'parsed_at'
                ) THEN
                    ALTER TABLE candidate_profiles ADD COLUMN parsed_at TIMESTAMP WITH TIME ZONE;
                    RAISE NOTICE 'Added column: parsed_at';
                END IF;
                
                -- Add resume_text if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'candidate_profiles' AND column_name = 'resume_text'
                ) THEN
                    ALTER TABLE candidate_profiles ADD COLUMN resume_text TEXT;
                    RAISE NOTICE 'Added column: resume_text';
                END IF;
                
                -- Add is_rule_based to interview_templates if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_templates' AND column_name = 'is_rule_based'
                ) THEN
                    ALTER TABLE interview_templates ADD COLUMN is_rule_based BOOLEAN NOT NULL DEFAULT false;
                    RAISE NOTICE 'Added column: interview_templates.is_rule_based';
                END IF;
                
                -- Add verification tracking columns to interview_sessions
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'face_verification_alerts'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN face_verification_alerts INTEGER NOT NULL DEFAULT 0;
                    RAISE NOTICE 'Added column: interview_sessions.face_verification_alerts';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'voice_verification_alerts'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN voice_verification_alerts INTEGER NOT NULL DEFAULT 0;
                    RAISE NOTICE 'Added column: interview_sessions.voice_verification_alerts';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'last_face_verification'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN last_face_verification TIMESTAMP WITH TIME ZONE;
                    RAISE NOTICE 'Added column: interview_sessions.last_face_verification';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'last_voice_verification'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN last_voice_verification TIMESTAMP WITH TIME ZONE;
                    RAISE NOTICE 'Added column: interview_sessions.last_voice_verification';
                END IF;
                
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'interview_sessions' AND column_name = 'termination_reason'
                ) THEN
                    ALTER TABLE interview_sessions ADD COLUMN termination_reason VARCHAR;
                    RAISE NOTICE 'Added column: interview_sessions.termination_reason';
                END IF;
                
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
                    
                    CREATE INDEX IF NOT EXISTS ix_interview_responses_session_id 
                        ON interview_responses(session_id);
                    CREATE INDEX IF NOT EXISTS ix_interview_responses_question_id 
                        ON interview_responses(question_id);
                    
                    RAISE NOTICE 'Created interview_responses table';
                END IF;
            END $$;
            """
            
            await conn.execute(text(fix_sql))
            print("✓ Successfully added all missing columns to candidate_profiles and interview_templates!")
            print("\nYou can now restart your backend server and try running seeds again.")
            
    except Exception as e:
        print(f"✗ Error fixing database schema: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_database_schema())
