-- Migration 083: Meeting-Task Integration
-- Adds columns to link tasks back to their source transcripts/meetings

-- Add source_transcript_id to tasks table
ALTER TABLE tasks ADD COLUMN source_transcript_id INTEGER REFERENCES meeting_transcripts(id);

-- Add source_meeting_id to tasks table
ALTER TABLE tasks ADD COLUMN source_meeting_id INTEGER REFERENCES meetings(meeting_id);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_tasks_proposal_status ON tasks(proposal_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_source_transcript ON tasks(source_transcript_id);
CREATE INDEX IF NOT EXISTS idx_tasks_source_meeting ON tasks(source_meeting_id);
CREATE INDEX IF NOT EXISTS idx_meetings_proposal_date ON meetings(proposal_id, meeting_date);
