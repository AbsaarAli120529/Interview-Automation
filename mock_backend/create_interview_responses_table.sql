-- Create interview_responses table
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

CREATE INDEX IF NOT EXISTS ix_interview_responses_session_id 
    ON interview_responses(session_id);
CREATE INDEX IF NOT EXISTS ix_interview_responses_question_id 
    ON interview_responses(question_id);
