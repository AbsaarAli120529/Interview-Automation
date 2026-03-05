-- Add verification tracking columns to interview_sessions table
ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS face_verification_alerts INTEGER NOT NULL DEFAULT 0;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS voice_verification_alerts INTEGER NOT NULL DEFAULT 0;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS last_face_verification TIMESTAMP WITH TIME ZONE;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS last_voice_verification TIMESTAMP WITH TIME ZONE;

ALTER TABLE interview_sessions 
ADD COLUMN IF NOT EXISTS termination_reason VARCHAR;
