-- KSWiFi Connect Database Tables
-- Creates tables for VPN-based session system
-- SAFE to run - won't destroy existing tables

-- Create kswifi_connect_profiles table
CREATE TABLE IF NOT EXISTS public.kswifi_connect_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    access_token TEXT UNIQUE NOT NULL,
    profile_type TEXT NOT NULL DEFAULT 'kswifi_connect',
    
    -- VPN-specific fields
    client_public_key TEXT NOT NULL,
    client_private_key TEXT NOT NULL, -- Encrypted in production
    client_ip TEXT NOT NULL,
    vpn_config TEXT NOT NULL,
    
    -- Session limits and tracking
    data_limit_mb INTEGER NOT NULL,
    data_used_mb INTEGER DEFAULT 0,
    bandwidth_limit_mbps INTEGER DEFAULT 10,
    
    -- Status and timing
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deactivated', 'expired', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    deactivated_at TIMESTAMP WITH TIME ZONE,
    deactivated_reason TEXT,
    
    -- Constraints
    CONSTRAINT fk_connect_profiles_user_id FOREIGN KEY (user_id) REFERENCES auth.users(id),
    CONSTRAINT unique_active_session UNIQUE (session_id, status) DEFERRABLE INITIALLY DEFERRED
);

-- Create vpn_client_connections table for detailed connection tracking
CREATE TABLE IF NOT EXISTS public.vpn_client_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES kswifi_connect_profiles(id) ON DELETE CASCADE,
    client_public_key TEXT NOT NULL,
    client_ip TEXT NOT NULL,
    
    -- Connection details
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    disconnected_at TIMESTAMP WITH TIME ZONE,
    last_handshake TIMESTAMP WITH TIME ZONE,
    
    -- Data usage tracking
    data_received_mb DECIMAL(10,2) DEFAULT 0,
    data_sent_mb DECIMAL(10,2) DEFAULT 0,
    total_data_mb DECIMAL(10,2) GENERATED ALWAYS AS (data_received_mb + data_sent_mb) STORED,
    
    -- Connection status
    status TEXT NOT NULL DEFAULT 'connected' CHECK (status IN ('connected', 'disconnected', 'expired')),
    disconnect_reason TEXT,
    
    -- Performance metrics
    avg_latency_ms INTEGER,
    peak_bandwidth_mbps DECIMAL(5,2),
    
    -- Unique constraint
    CONSTRAINT unique_active_vpn_connection UNIQUE (profile_id, client_public_key)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_connect_profiles_user_id ON kswifi_connect_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_connect_profiles_session_id ON kswifi_connect_profiles(session_id);
CREATE INDEX IF NOT EXISTS idx_connect_profiles_status ON kswifi_connect_profiles(status);
CREATE INDEX IF NOT EXISTS idx_connect_profiles_expires_at ON kswifi_connect_profiles(expires_at);
CREATE INDEX IF NOT EXISTS idx_connect_profiles_public_key ON kswifi_connect_profiles(client_public_key);

CREATE INDEX IF NOT EXISTS idx_vpn_connections_profile_id ON vpn_client_connections(profile_id);
CREATE INDEX IF NOT EXISTS idx_vpn_connections_client_key ON vpn_client_connections(client_public_key);
CREATE INDEX IF NOT EXISTS idx_vpn_connections_status ON vpn_client_connections(status);
CREATE INDEX IF NOT EXISTS idx_vpn_connections_connected_at ON vpn_client_connections(connected_at);

-- Enable RLS
ALTER TABLE public.kswifi_connect_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vpn_client_connections ENABLE ROW LEVEL SECURITY;

-- RLS Policies for kswifi_connect_profiles
DROP POLICY IF EXISTS "Users can manage their own connect profiles" ON public.kswifi_connect_profiles;
CREATE POLICY "Users can manage their own connect profiles" ON public.kswifi_connect_profiles
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role can manage all connect profiles" ON public.kswifi_connect_profiles;
CREATE POLICY "Service role can manage all connect profiles" ON public.kswifi_connect_profiles
    FOR ALL USING (true);

-- RLS Policies for vpn_client_connections
DROP POLICY IF EXISTS "Users can view their own VPN connections" ON public.vpn_client_connections;
CREATE POLICY "Users can view their own VPN connections" ON public.vpn_client_connections
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM kswifi_connect_profiles 
            WHERE id = profile_id AND user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Service role can manage all VPN connections" ON public.vpn_client_connections;
CREATE POLICY "Service role can manage all VPN connections" ON public.vpn_client_connections
    FOR ALL USING (true);

-- Create helper functions for session management
CREATE OR REPLACE FUNCTION get_active_connect_profiles(p_user_id UUID)
RETURNS TABLE (
    profile_id UUID,
    session_id UUID,
    data_used_mb INTEGER,
    data_limit_mb INTEGER,
    remaining_mb INTEGER,
    bandwidth_limit_mbps INTEGER,
    status TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    client_ip TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cp.id as profile_id,
        cp.session_id,
        cp.data_used_mb,
        cp.data_limit_mb,
        (cp.data_limit_mb - cp.data_used_mb) as remaining_mb,
        cp.bandwidth_limit_mbps,
        cp.status,
        cp.expires_at,
        cp.client_ip
    FROM kswifi_connect_profiles cp
    WHERE cp.user_id = p_user_id
    AND cp.status = 'active'
    AND cp.expires_at > NOW()
    ORDER BY cp.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Create function to update VPN usage
CREATE OR REPLACE FUNCTION update_vpn_usage(
    p_client_public_key TEXT,
    p_data_received_mb DECIMAL,
    p_data_sent_mb DECIMAL
)
RETURNS JSON AS $$
DECLARE
    v_profile_id UUID;
    v_total_usage DECIMAL;
    v_data_limit INTEGER;
    v_expires_at TIMESTAMP WITH TIME ZONE;
    v_result JSON;
BEGIN
    -- Get profile info
    SELECT cp.id, cp.data_limit_mb, cp.expires_at, (cp.data_used_mb + p_data_received_mb + p_data_sent_mb)
    INTO v_profile_id, v_data_limit, v_expires_at, v_total_usage
    FROM kswifi_connect_profiles cp
    WHERE cp.client_public_key = p_client_public_key
    AND cp.status = 'active';
    
    -- Check if profile exists
    IF v_profile_id IS NULL THEN
        RETURN json_build_object('session_valid', false, 'error', 'Profile not found');
    END IF;
    
    -- Check expiry
    IF v_expires_at <= NOW() THEN
        UPDATE kswifi_connect_profiles 
        SET status = 'expired', deactivated_at = NOW(), deactivated_reason = 'time_expired'
        WHERE id = v_profile_id;
        
        RETURN json_build_object('session_valid', false, 'error', 'Session expired');
    END IF;
    
    -- Check data limit
    IF v_total_usage >= v_data_limit THEN
        UPDATE kswifi_connect_profiles 
        SET status = 'expired', deactivated_at = NOW(), deactivated_reason = 'data_limit_exceeded'
        WHERE id = v_profile_id;
        
        RETURN json_build_object('session_valid', false, 'error', 'Data limit exceeded');
    END IF;
    
    -- Update usage
    UPDATE kswifi_connect_profiles 
    SET data_used_mb = v_total_usage, last_used_at = NOW()
    WHERE id = v_profile_id;
    
    -- Update connection tracking
    INSERT INTO vpn_client_connections (profile_id, client_public_key, data_received_mb, data_sent_mb, last_handshake)
    VALUES (v_profile_id, p_client_public_key, p_data_received_mb, p_data_sent_mb, NOW())
    ON CONFLICT (profile_id, client_public_key) 
    DO UPDATE SET 
        data_received_mb = EXCLUDED.data_received_mb,
        data_sent_mb = EXCLUDED.data_sent_mb,
        last_handshake = NOW();
    
    -- Return success with remaining data
    v_result := json_build_object(
        'session_valid', true,
        'data_used_mb', v_total_usage,
        'data_limit_mb', v_data_limit,
        'remaining_mb', (v_data_limit - v_total_usage)
    );
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Verify tables were created
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('kswifi_connect_profiles', 'vpn_client_connections')
ORDER BY table_name, ordinal_position;