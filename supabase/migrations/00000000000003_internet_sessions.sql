-- Migration: Internet Sessions for KSWiFi
-- Description: Create tables for internet session downloads and management

-- Drop existing dependencies if they exist
DROP INDEX IF EXISTS idx_internet_sessions_user_id;
DROP INDEX IF EXISTS idx_internet_sessions_status;
DROP INDEX IF EXISTS idx_session_usage_logs_session_id;
DROP INDEX IF EXISTS idx_session_usage_logs_user_id;

-- Drop existing tables if they exist (cascade to handle dependencies)
DROP TABLE IF EXISTS session_usage_logs CASCADE;
DROP TABLE IF EXISTS internet_sessions CASCADE;

-- Drop existing types if they exist
DROP TYPE IF EXISTS session_status CASCADE;

-- Create session status enum
CREATE TYPE session_status AS ENUM (
    'downloading',
    'downloaded', 
    'transferring',
    'stored',
    'activating',
    'active',
    'exhausted',
    'expired',
    'failed'
);

-- Internet sessions table
CREATE TABLE IF NOT EXISTS internet_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL, -- Session type identifier (e.g., '5gb', 'unlimited')
    session_name TEXT NOT NULL,
    
    -- Session details
    data_mb INTEGER NOT NULL, -- -1 for unlimited
    price_ngn INTEGER DEFAULT 0,
    validity_days INTEGER NOT NULL DEFAULT 30,
    plan_type TEXT DEFAULT 'standard',
    
    -- Download tracking
    status session_status DEFAULT 'downloading',
    progress_percent INTEGER DEFAULT 0,
    download_started_at TIMESTAMPTZ DEFAULT NOW(),
    download_completed_at TIMESTAMPTZ,
    
    -- Usage tracking
    used_data_mb INTEGER DEFAULT 0,
    activated_at TIMESTAMPTZ,
    last_usage_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    
    -- eSIM integration
    esim_id UUID REFERENCES esims(id),
    
    -- Error handling
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX idx_internet_sessions_user_id ON internet_sessions(user_id);
CREATE INDEX idx_internet_sessions_status ON internet_sessions(status);
CREATE INDEX idx_internet_sessions_session_id ON internet_sessions(session_id);
CREATE INDEX idx_internet_sessions_created_at ON internet_sessions(created_at);
CREATE INDEX idx_internet_sessions_expires_at ON internet_sessions(expires_at);

-- Enable RLS
ALTER TABLE internet_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own sessions" ON internet_sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions" ON internet_sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sessions" ON internet_sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_internet_sessions_updated_at 
    BEFORE UPDATE ON internet_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to get user's free session quota usage
CREATE OR REPLACE FUNCTION get_user_free_quota_usage(user_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    total_mb INTEGER := 0;
    current_month TIMESTAMPTZ;
BEGIN
    -- Get start of current month
    current_month := date_trunc('month', NOW());
    
    -- Sum free sessions (price_ngn = 0) for current month
    SELECT COALESCE(SUM(data_mb), 0) INTO total_mb
    FROM internet_sessions
    WHERE user_id = user_uuid
        AND price_ngn = 0
        AND data_mb > 0  -- Exclude unlimited sessions
        AND download_started_at >= current_month;
    
    RETURN total_mb;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user can download free session
CREATE OR REPLACE FUNCTION can_download_free_session(user_uuid UUID, session_size_mb INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    current_usage_mb INTEGER;
    free_limit_mb INTEGER := 5120; -- 5GB limit
BEGIN
    current_usage_mb := get_user_free_quota_usage(user_uuid);
    
    RETURN (current_usage_mb + session_size_mb) <= free_limit_mb;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to activate a session
CREATE OR REPLACE FUNCTION activate_internet_session(session_uuid UUID, user_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    session_record internet_sessions%ROWTYPE;
    result JSONB;
BEGIN
    -- Get session record
    SELECT * INTO session_record
    FROM internet_sessions
    WHERE id = session_uuid AND user_id = user_uuid;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'Session not found');
    END IF;
    
    -- Check if session can be activated
    IF session_record.status != 'stored' THEN
        RETURN jsonb_build_object('success', false, 'error', 'Session must be downloaded before activation');
    END IF;
    
    -- Check if session has expired
    IF session_record.expires_at < NOW() THEN
        UPDATE internet_sessions 
        SET status = 'expired', updated_at = NOW()
        WHERE id = session_uuid;
        
        RETURN jsonb_build_object('success', false, 'error', 'Session has expired');
    END IF;
    
    -- Activate session
    UPDATE internet_sessions
    SET 
        status = 'active',
        activated_at = NOW(),
        updated_at = NOW()
    WHERE id = session_uuid;
    
    RETURN jsonb_build_object(
        'success', true,
        'session_id', session_uuid,
        'activated_at', NOW(),
        'data_mb', session_record.data_mb
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to track session usage
CREATE OR REPLACE FUNCTION track_session_usage(session_uuid UUID, data_used_mb INTEGER)
RETURNS JSONB AS $$
DECLARE
    session_record internet_sessions%ROWTYPE;
    new_usage_mb INTEGER;
    is_exhausted BOOLEAN := false;
BEGIN
    -- Get current session
    SELECT * INTO session_record
    FROM internet_sessions
    WHERE id = session_uuid AND status = 'active';
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('success', false, 'error', 'Active session not found');
    END IF;
    
    -- Calculate new usage
    new_usage_mb := COALESCE(session_record.used_data_mb, 0) + data_used_mb;
    
    -- Check if exhausted (for non-unlimited plans)
    IF session_record.data_mb > 0 AND new_usage_mb >= session_record.data_mb THEN
        is_exhausted := true;
    END IF;
    
    -- Update usage
    UPDATE internet_sessions
    SET 
        used_data_mb = new_usage_mb,
        last_usage_at = NOW(),
        status = CASE WHEN is_exhausted THEN 'exhausted'::session_status ELSE status END,
        updated_at = NOW()
    WHERE id = session_uuid;
    
    RETURN jsonb_build_object(
        'success', true,
        'data_used_mb', new_usage_mb,
        'data_remaining_mb', CASE 
            WHEN session_record.data_mb > 0 THEN GREATEST(0, session_record.data_mb - new_usage_mb)
            ELSE 999999
        END,
        'is_exhausted', is_exhausted
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add session download tracking to existing data_packs table for backward compatibility
ALTER TABLE data_packs ADD COLUMN IF NOT EXISTS session_id UUID REFERENCES internet_sessions(id);
ALTER TABLE data_packs ADD COLUMN IF NOT EXISTS download_status TEXT DEFAULT 'pending';

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON internet_sessions TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_free_quota_usage(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION can_download_free_session(UUID, INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION activate_internet_session(UUID, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION track_session_usage(UUID, INTEGER) TO authenticated;