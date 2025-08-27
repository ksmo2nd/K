-- =====================================================
-- 🔒 DUAL eSIM SYSTEM EXTENSION FOR KSWIFI
-- =====================================================
-- This extension adds support for:
-- 1. Private osmo-smdpp eSIM profiles (password protected)
-- 2. Public WiFi-first captive portal access
-- 
-- SAFE TO RUN: Won't affect existing tables or data
-- =====================================================

-- Enable UUID extension (safe to run multiple times)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 🔒 PRIVATE OSMO-SMDPP eSIM PROFILES
-- =====================================================

-- Table for osmo-smdpp generated eSIM profiles
CREATE TABLE IF NOT EXISTS osmo_esim_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES internet_sessions(id) ON DELETE CASCADE,
    
    -- GSMA-compliant profile data
    iccid TEXT NOT NULL UNIQUE,
    imsi TEXT NOT NULL UNIQUE,
    ki TEXT NOT NULL, -- Encryption key
    opc TEXT NOT NULL, -- Operator code
    
    -- SM-DP+ server data
    smdp_server TEXT DEFAULT 'osmo.kswifi.local',
    activation_code TEXT NOT NULL UNIQUE,
    profile_id TEXT NOT NULL UNIQUE,
    
    -- Profile metadata
    profile_name TEXT DEFAULT 'KSWiFi Private',
    profile_nickname TEXT,
    profile_state TEXT DEFAULT 'available' CHECK (profile_state IN ('available', 'downloaded', 'installed', 'enabled', 'disabled', 'deleted')),
    
    -- Network configuration
    apn TEXT DEFAULT 'internet',
    apn_username TEXT,
    apn_password TEXT,
    
    -- Access control
    access_type TEXT DEFAULT 'private' CHECK (access_type IN ('private', 'restricted')),
    password_hash TEXT, -- For OLAmilekan@$112 validation
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    installed_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- 🌐 PUBLIC WIFI-FIRST CAPTIVE PORTAL
-- =====================================================

-- Table for public WiFi access tokens
CREATE TABLE IF NOT EXISTS wifi_access_tokens (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES internet_sessions(id) ON DELETE CASCADE,
    
    -- Token data
    access_token TEXT NOT NULL UNIQUE,
    qr_code_data TEXT NOT NULL,
    token_type TEXT DEFAULT 'wifi_access' CHECK (token_type IN ('wifi_access', 'captive_portal', 'public_link')),
    
    -- Network access configuration
    network_name TEXT DEFAULT 'KSWiFi-Public',
    captive_portal_url TEXT,
    redirect_url TEXT,
    bandwidth_limit_mbps INTEGER DEFAULT 10,
    time_limit_minutes INTEGER DEFAULT 60,
    
    -- Usage tracking
    data_used_mb INTEGER DEFAULT 0,
    data_limit_mb INTEGER NOT NULL,
    sessions_used INTEGER DEFAULT 0,
    max_sessions INTEGER DEFAULT 1,
    
    -- Token status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'used', 'expired', 'revoked')),
    
    -- Access metadata
    device_info JSONB,
    ip_address INET,
    mac_address TEXT,
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    first_used_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- 🌍 CAPTIVE PORTAL SESSIONS
-- =====================================================

-- Table for active captive portal sessions
CREATE TABLE IF NOT EXISTS captive_portal_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    access_token_id UUID REFERENCES wifi_access_tokens(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session identification
    session_token TEXT NOT NULL UNIQUE,
    mac_address TEXT NOT NULL,
    ip_address INET NOT NULL,
    
    -- Session data
    data_used_mb INTEGER DEFAULT 0,
    bandwidth_used_mbps DECIMAL(10,2) DEFAULT 0,
    duration_minutes INTEGER DEFAULT 0,
    
    -- Session status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'expired', 'terminated')),
    
    -- Device information
    device_type TEXT,
    user_agent TEXT,
    device_fingerprint TEXT,
    
    -- Network information
    gateway_ip INET,
    dns_servers TEXT[],
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    terminated_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- 📊 INDEXES FOR PERFORMANCE
-- =====================================================

-- osmo_esim_profiles indexes
CREATE INDEX IF NOT EXISTS idx_osmo_profiles_user_id ON osmo_esim_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_osmo_profiles_session_id ON osmo_esim_profiles(session_id);
CREATE INDEX IF NOT EXISTS idx_osmo_profiles_state ON osmo_esim_profiles(profile_state);
CREATE INDEX IF NOT EXISTS idx_osmo_profiles_access_type ON osmo_esim_profiles(access_type);
CREATE INDEX IF NOT EXISTS idx_osmo_profiles_activation_code ON osmo_esim_profiles(activation_code);

-- wifi_access_tokens indexes
CREATE INDEX IF NOT EXISTS idx_wifi_tokens_user_id ON wifi_access_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_wifi_tokens_session_id ON wifi_access_tokens(session_id);
CREATE INDEX IF NOT EXISTS idx_wifi_tokens_access_token ON wifi_access_tokens(access_token);
CREATE INDEX IF NOT EXISTS idx_wifi_tokens_status ON wifi_access_tokens(status);
CREATE INDEX IF NOT EXISTS idx_wifi_tokens_expires_at ON wifi_access_tokens(expires_at);

-- captive_portal_sessions indexes
CREATE INDEX IF NOT EXISTS idx_captive_sessions_token_id ON captive_portal_sessions(access_token_id);
CREATE INDEX IF NOT EXISTS idx_captive_sessions_user_id ON captive_portal_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_captive_sessions_mac_address ON captive_portal_sessions(mac_address);
CREATE INDEX IF NOT EXISTS idx_captive_sessions_status ON captive_portal_sessions(status);
CREATE INDEX IF NOT EXISTS idx_captive_sessions_expires_at ON captive_portal_sessions(expires_at);

-- =====================================================
-- 🔐 ROW LEVEL SECURITY
-- =====================================================

-- Enable RLS on new tables
ALTER TABLE osmo_esim_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE wifi_access_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE captive_portal_sessions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies with error handling
DO $$
BEGIN
    -- osmo_esim_profiles policies
    BEGIN
        CREATE POLICY "Users can access their own osmo profiles" ON osmo_esim_profiles
            FOR ALL USING (auth.uid() = user_id);
        EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    
    -- wifi_access_tokens policies
    BEGIN
        CREATE POLICY "Users can access their own wifi tokens" ON wifi_access_tokens
            FOR ALL USING (auth.uid() = user_id);
        EXCEPTION WHEN duplicate_object THEN NULL;
    END;
    
    -- captive_portal_sessions policies
    BEGIN
        CREATE POLICY "Users can access their own captive sessions" ON captive_portal_sessions
            FOR ALL USING (auth.uid() = user_id);
        EXCEPTION WHEN duplicate_object THEN NULL;
    END;
END $$;

-- =====================================================
-- 🔧 UTILITY FUNCTIONS
-- =====================================================

-- Function to generate secure activation codes
CREATE OR REPLACE FUNCTION generate_activation_code(prefix TEXT DEFAULT 'LPA')
RETURNS TEXT AS $$
DECLARE
    random_part TEXT;
BEGIN
    -- Generate cryptographically secure random string
    SELECT encode(gen_random_bytes(32), 'base64') INTO random_part;
    -- Remove special characters and make URL-safe
    random_part := replace(replace(replace(random_part, '/', '_'), '+', '-'), '=', '');
    -- Return formatted activation code
    RETURN prefix || ':1$osmo.kswifi.local$' || random_part;
END;
$$ LANGUAGE plpgsql;

-- Function to generate WiFi access tokens
CREATE OR REPLACE FUNCTION generate_wifi_token()
RETURNS TEXT AS $$
DECLARE
    token_part TEXT;
BEGIN
    -- Generate secure token
    SELECT encode(gen_random_bytes(24), 'hex') INTO token_part;
    RETURN 'wifi_' || token_part;
END;
$$ LANGUAGE plpgsql;

-- Function to validate private access password
CREATE OR REPLACE FUNCTION validate_private_access(input_password TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check against the specific password: OLAmilekan@$112
    RETURN input_password = 'OLAmilekan@$112';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 🎉 EXTENSION COMPLETE
-- =====================================================

-- Notify PostgREST to reload schema
NOTIFY pgrst, 'reload schema';

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ KSWiFi Dual eSIM System Extension installed successfully!';
    RAISE NOTICE '🔒 Private osmo-smdpp profiles: Ready';
    RAISE NOTICE '🌐 Public WiFi captive portal: Ready';
    RAISE NOTICE '📊 All indexes and RLS policies: Applied';
END $$;