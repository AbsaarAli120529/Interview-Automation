-- Quick fix: Add is_rule_based column to interview_templates
-- Run this command in your PostgreSQL database:

ALTER TABLE interview_templates ADD COLUMN IF NOT EXISTS is_rule_based BOOLEAN NOT NULL DEFAULT false;
