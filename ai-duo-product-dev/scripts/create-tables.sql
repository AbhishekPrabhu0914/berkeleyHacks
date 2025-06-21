-- Create tables for AI Duo Product Development application

-- Sessions table to store user requirements and session info
CREATE TABLE IF NOT EXISTS ai_sessions (
    id TEXT PRIMARY KEY,
    requirement TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    final_result TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table to store agent conversations
CREATE TABLE IF NOT EXISTS ai_messages (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES ai_sessions(id) ON DELETE CASCADE,
    agent TEXT NOT NULL CHECK (agent IN ('swe', 'pm')),
    content TEXT NOT NULL,
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_ai_messages_session_id ON ai_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_messages_created_at ON ai_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_created_at ON ai_sessions(created_at);

-- Add RLS (Row Level Security) policies if needed
ALTER TABLE ai_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_messages ENABLE ROW LEVEL SECURITY;

-- Create policies to allow public access for demo purposes
-- In production, you'd want proper user authentication
CREATE POLICY "Allow public access to ai_sessions" ON ai_sessions
    FOR ALL USING (true);

CREATE POLICY "Allow public access to ai_messages" ON ai_messages
    FOR ALL USING (true);
