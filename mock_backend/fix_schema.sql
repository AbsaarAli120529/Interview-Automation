-- Quick fix SQL script to add missing columns to candidate_profiles and interview_templates tables
-- Run this directly in your PostgreSQL database

-- Connect to your database and run this:
-- psql -U postgres -d interview_db -f fix_schema.sql

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
    
    RAISE NOTICE 'Schema fix completed successfully!';
END $$;
