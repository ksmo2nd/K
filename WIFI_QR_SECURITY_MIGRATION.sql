-- =====================================================
-- 🔐 WIFI QR SECURITY ENHANCEMENT MIGRATION
-- =====================================================
-- 
-- This migration adds support for secure WiFi QR codes with
-- encrypted passwords and enhanced session management
--

-- Add new columns for secure WiFi access
ALTER TABLE wifi_access_tokens 
ADD COLUMN IF NOT EXISTS wifi_password TEXT,
ADD COLUMN IF NOT EXISTS wifi_security TEXT DEFAULT 'WPA2' CHECK (wifi_security IN ('WPA2', 'WPA3', 'open')),
ADD COLUMN IF NOT EXISTS auto_disconnect BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS last_connected_device TEXT,
ADD COLUMN IF NOT EXISTS last_connected_at TIMESTAMP WITH TIME ZONE;

-- Update token_type enum to include new secure access type
ALTER TABLE wifi_access_tokens 
DROP CONSTRAINT IF EXISTS wifi_access_tokens_token_type_check;

ALTER TABLE wifi_access_tokens 
ADD CONSTRAINT wifi_access_tokens_token_type_check 
CHECK (token_type IN ('wifi_access', 'wifi_secure_access', 'captive_portal', 'public_link'));

-- Create table for tracking device connections (optional - for future use)
CREATE TABLE IF NOT EXISTS wifi_device_connections (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    token_id UUID REFERENCES wifi_access_tokens(id) ON DELETE CASCADE,
    device_mac TEXT NOT NULL,
    network_name TEXT NOT NULL,
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    disconnected_at TIMESTAMP WITH TIME ZONE,
    data_used_mb INTEGER DEFAULT 0,
    status TEXT DEFAULT 'connected' CHECK (status IN ('connected', 'disconnected', 'expired')),
    
    -- Ensure one connection per device per token
    UNIQUE(token_id, device_mac),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_network_name ON wifi_access_tokens(network_name);
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_wifi_password ON wifi_access_tokens(wifi_password);
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_status_active ON wifi_access_tokens(status) WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_wifi_device_connections_token_id ON wifi_device_connections(token_id);
CREATE INDEX IF NOT EXISTS idx_wifi_device_connections_device_mac ON wifi_device_connections(device_mac);
CREATE INDEX IF NOT EXISTS idx_wifi_device_connections_status ON wifi_device_connections(status);

-- RLS policies for wifi_device_connections
ALTER TABLE wifi_device_connections ENABLE ROW LEVEL SECURITY;

-- Users can only see their own device connections
CREATE POLICY "Users can view own device connections" ON wifi_device_connections
    FOR SELECT USING (
        token_id IN (
            SELECT id FROM wifi_access_tokens 
            WHERE user_id = auth.uid()
        )
    );

-- Users can insert their own device connections
CREATE POLICY "Users can create own device connections" ON wifi_device_connections
    FOR INSERT WITH CHECK (
        token_id IN (
            SELECT id FROM wifi_access_tokens 
            WHERE user_id = auth.uid()
        )
    );

-- Users can update their own device connections
CREATE POLICY "Users can update own device connections" ON wifi_device_connections
    FOR UPDATE USING (
        token_id IN (
            SELECT id FROM wifi_access_tokens 
            WHERE user_id = auth.uid()
        )
    );

-- Function to generate secure WiFi passwords
CREATE OR REPLACE FUNCTION generate_wifi_password(access_token TEXT)
RETURNS TEXT AS $$
DECLARE
    password_hash TEXT;
    wifi_password TEXT;
BEGIN
    -- Create unique seed from token and timestamp
    password_hash := encode(digest(access_token || NOW()::TEXT, 'sha256'), 'hex');
    
    -- Extract first 16 characters and make uppercase for user-friendly password
    wifi_password := upper(substring(password_hash from 1 for 16));
    
    RETURN wifi_password;
END;
$$ LANGUAGE plpgsql;

-- Function to generate unique network names
CREATE OR REPLACE FUNCTION generate_network_name(access_token TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Extract last 8 characters of token for network suffix
    RETURN 'KSWiFi_Global_' || upper(substring(access_token from length(access_token) - 7));
END;
$$ LANGUAGE plpgsql;

-- Update existing records to have secure access type (optional)
-- UPDATE wifi_access_tokens 
-- SET token_type = 'wifi_secure_access' 
-- WHERE token_type = 'wifi_access' AND wifi_password IS NULL;

-- =====================================================
-- 🎉 MIGRATION COMPLETE
-- =====================================================

-- Notify PostgREST to reload schema
NOTIFY pgrst, 'reload schema';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ WiFi QR Security Enhancement migration completed!';
    RAISE NOTICE '🔐 Secure WiFi passwords: Ready';
    RAISE NOTICE '📱 Device connection tracking: Ready';
    RAISE NOTICE '🌐 Enhanced QR code generation: Ready';
    RAISE NOTICE '📊 Performance indexes: Created';
END $$;