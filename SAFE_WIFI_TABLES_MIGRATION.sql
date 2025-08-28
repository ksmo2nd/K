-- Safe WiFi Tables Migration - Compatible with all PostgreSQL versions
-- This will create all necessary tables for WiFi QR system
-- Won't destroy existing tables

-- 1. Create wifi_access_tokens table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.wifi_access_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id UUID,
    access_token TEXT UNIQUE NOT NULL,
    network_name TEXT NOT NULL,
    captive_portal_url TEXT,
    data_limit_mb INTEGER,
    time_limit_minutes INTEGER,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'expired', 'used', 'cancelled')),
    token_type TEXT NOT NULL DEFAULT 'wifi_qr' CHECK (token_type IN ('wifi_qr', 'captive_portal', 'direct_access')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    used_at TIMESTAMP WITH TIME ZONE,
    
    -- WiFi-specific columns
    wifi_password TEXT,
    wifi_security TEXT DEFAULT 'WPA2' CHECK (wifi_security IN ('WPA2', 'WPA3', 'WEP', 'nopass')),
    auto_disconnect BOOLEAN DEFAULT false,
    last_connected_device TEXT,
    last_connected_at TIMESTAMP WITH TIME ZONE
);

-- 2. Create wifi_device_connections table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.wifi_device_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_id UUID REFERENCES wifi_access_tokens(id) ON DELETE CASCADE,
    device_mac TEXT NOT NULL,
    network_name TEXT NOT NULL,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    disconnected_at TIMESTAMP WITH TIME ZONE,
    data_used_mb INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'connected' CHECK (status IN ('connected', 'disconnected', 'expired')),
    
    -- Unique constraint to prevent duplicate connections
    CONSTRAINT unique_active_connection UNIQUE (token_id, device_mac, network_name)
);

-- 3. Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_user_id ON wifi_access_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_session_id ON wifi_access_tokens(session_id);
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_access_token ON wifi_access_tokens(access_token);
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_network_name ON wifi_access_tokens(network_name);
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_status_active ON wifi_access_tokens(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_wifi_device_connections_token_id ON wifi_device_connections(token_id);
CREATE INDEX IF NOT EXISTS idx_wifi_device_connections_device_mac ON wifi_device_connections(device_mac);

-- 4. Enable RLS
ALTER TABLE public.wifi_access_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wifi_device_connections ENABLE ROW LEVEL SECURITY;

-- 5. Drop existing policies if they exist (safe approach)
DROP POLICY IF EXISTS "Users can manage their own WiFi tokens" ON public.wifi_access_tokens;
DROP POLICY IF EXISTS "Service role can manage all WiFi tokens" ON public.wifi_access_tokens;
DROP POLICY IF EXISTS "Users can view their device connections" ON public.wifi_device_connections;
DROP POLICY IF EXISTS "Service role can manage all device connections" ON public.wifi_device_connections;

-- 6. Create RLS policies (without IF NOT EXISTS)
CREATE POLICY "Users can manage their own WiFi tokens" ON public.wifi_access_tokens
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage all WiFi tokens" ON public.wifi_access_tokens
    FOR ALL USING (true);

CREATE POLICY "Users can view their device connections" ON public.wifi_device_connections
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM wifi_access_tokens 
            WHERE id = token_id AND user_id = auth.uid()
        )
    );

CREATE POLICY "Service role can manage all device connections" ON public.wifi_device_connections
    FOR ALL USING (true);

-- 7. Verify tables were created
SELECT 
    'wifi_access_tokens' as table_name,
    COUNT(*) as column_count
FROM information_schema.columns 
WHERE table_name = 'wifi_access_tokens'
UNION ALL
SELECT 
    'wifi_device_connections' as table_name,
    COUNT(*) as column_count
FROM information_schema.columns 
WHERE table_name = 'wifi_device_connections';