-- =====================================================
-- COMPLETE SUPABASE SCHEMA FOR KSWIFI - PRODUCTION READY
-- Run this ONCE in Supabase SQL Editor to fix ALL issues
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Drop existing tables in correct order (safety first)
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS data_usage CASCADE;
DROP TABLE IF EXISTS usage_logs CASCADE;
DROP TABLE IF EXISTS internet_sessions CASCADE;
DROP TABLE IF EXISTS data_packs CASCADE;
DROP TABLE IF EXISTS esims CASCADE;
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS user_devices CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Users table (extends Supabase auth.users)
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone_number TEXT,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User profiles table
CREATE TABLE user_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User devices table (for push notifications)
CREATE TABLE user_devices (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    push_token TEXT UNIQUE NOT NULL,
    device_type TEXT CHECK (device_type IN ('ios', 'android', 'web')),
    device_name TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User subscriptions table
CREATE TABLE user_subscriptions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subscription_type TEXT NOT NULL CHECK (subscription_type IN ('free', 'unlimited')),
    plan_type TEXT DEFAULT 'free' CHECK (plan_type IN ('free', 'unlimited_required', 'premium')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- eSIMs table
CREATE TABLE esims (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    iccid TEXT UNIQUE NOT NULL,
    imsi TEXT,
    msisdn TEXT,
    activation_code TEXT NOT NULL,
    qr_code_data TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended', 'expired')),
    apn TEXT DEFAULT 'internet',
    username TEXT,
    password TEXT,
    bundle_size_mb INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Data packs table
CREATE TABLE data_packs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    data_mb INTEGER NOT NULL CHECK (data_mb > 0),
    used_data_mb INTEGER DEFAULT 0 CHECK (used_data_mb >= 0),
    remaining_data_mb INTEGER GENERATED ALWAYS AS (data_mb - used_data_mb) STORED,
    price_ngn INTEGER DEFAULT 0 CHECK (price_ngn >= 0),
    price_usd DECIMAL(10,2) DEFAULT 0.00 CHECK (price_usd >= 0),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'exhausted', 'expired', 'cancelled')),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Internet sessions table
CREATE TABLE internet_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL, -- Maps to frontend session IDs like 'default_1gb'
    session_name TEXT NOT NULL,
    data_mb INTEGER NOT NULL CHECK (data_mb > 0),
    data_used_mb INTEGER DEFAULT 0 CHECK (data_used_mb >= 0),
    data_remaining_mb INTEGER GENERATED ALWAYS AS (data_mb - data_used_mb) STORED,
    price_ngn INTEGER DEFAULT 0 CHECK (price_ngn >= 0),
    price_usd DECIMAL(10,2) DEFAULT 0.00 CHECK (price_usd >= 0),
    status TEXT DEFAULT 'downloading' CHECK (status IN ('downloading', 'available', 'active', 'exhausted', 'expired')),
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    plan_type TEXT DEFAULT 'default' CHECK (plan_type IN ('default', 'unlimited_required', 'premium')),
    source_network TEXT,
    network_quality TEXT DEFAULT 'good' CHECK (network_quality IN ('excellent', 'good', 'fair', 'poor')),
    esim_id UUID REFERENCES esims(id) ON DELETE SET NULL,
    download_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    activated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Usage logs table
CREATE TABLE usage_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_pack_id UUID REFERENCES data_packs(id) ON DELETE SET NULL,
    session_id UUID REFERENCES internet_sessions(id) ON DELETE SET NULL,
    data_used_mb INTEGER NOT NULL CHECK (data_used_mb > 0),
    usage_type TEXT CHECK (usage_type IN ('session_download', 'internet_browsing', 'background')),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data usage table (for eSIM monitoring)
CREATE TABLE data_usage (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    esim_id UUID REFERENCES esims(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_used_mb INTEGER NOT NULL CHECK (data_used_mb >= 0),
    data_remaining_mb INTEGER,
    usage_period TEXT CHECK (usage_period IN ('daily', 'weekly', 'monthly')),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications table
CREATE TABLE notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info' CHECK (type IN ('info', 'warning', 'error', 'success')),
    is_read BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- User-related indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX idx_user_devices_push_token ON user_devices(push_token);
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX idx_user_subscriptions_status ON user_subscriptions(status);

-- eSIM-related indexes
CREATE INDEX idx_esims_user_id ON esims(user_id);
CREATE INDEX idx_esims_iccid ON esims(iccid);
CREATE INDEX idx_esims_status ON esims(status);
CREATE INDEX idx_esims_created_at ON esims(created_at);

-- Data pack indexes
CREATE INDEX idx_data_packs_user_id ON data_packs(user_id);
CREATE INDEX idx_data_packs_status ON data_packs(status);
CREATE INDEX idx_data_packs_is_active ON data_packs(is_active);
CREATE INDEX idx_data_packs_expires_at ON data_packs(expires_at);

-- Internet session indexes
CREATE INDEX idx_internet_sessions_user_id ON internet_sessions(user_id);
CREATE INDEX idx_internet_sessions_session_id ON internet_sessions(session_id);
CREATE INDEX idx_internet_sessions_status ON internet_sessions(status);
CREATE INDEX idx_internet_sessions_esim_id ON internet_sessions(esim_id);
CREATE INDEX idx_internet_sessions_created_at ON internet_sessions(created_at);

-- Usage-related indexes
CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);
CREATE INDEX idx_data_usage_esim_id ON data_usage(esim_id);
CREATE INDEX idx_data_usage_user_id ON data_usage(user_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

-- =====================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_devices_updated_at BEFORE UPDATE ON user_devices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_subscriptions_updated_at BEFORE UPDATE ON user_subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_esims_updated_at BEFORE UPDATE ON esims FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_data_packs_updated_at BEFORE UPDATE ON data_packs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_internet_sessions_updated_at BEFORE UPDATE ON internet_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to auto-update data pack status based on usage
CREATE OR REPLACE FUNCTION update_data_pack_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark as exhausted if all data is used
    IF NEW.used_data_mb >= NEW.data_mb THEN
        NEW.status = 'exhausted';
        NEW.is_active = FALSE;
    -- Mark as expired if past expiry date
    ELSIF NEW.expires_at IS NOT NULL AND NEW.expires_at < NOW() THEN
        NEW.status = 'expired';
        NEW.is_active = FALSE;
    -- Keep active if data remaining and not expired
    ELSE
        NEW.status = 'active';
        NEW.is_active = TRUE;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply data pack status trigger
CREATE TRIGGER update_data_pack_status_trigger BEFORE UPDATE ON data_packs FOR EACH ROW EXECUTE FUNCTION update_data_pack_status();

-- Function to auto-update internet session status
CREATE OR REPLACE FUNCTION update_internet_session_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark as exhausted if all data is used
    IF NEW.data_used_mb >= NEW.data_mb THEN
        NEW.status = 'exhausted';
    -- Mark as expired if past expiry date (if set)
    ELSIF NEW.expires_at IS NOT NULL AND NEW.expires_at < NOW() THEN
        NEW.status = 'expired';
    -- Mark as active if download complete
    ELSIF NEW.progress_percent >= 100 THEN
        NEW.status = 'available';
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply internet session status trigger
CREATE TRIGGER update_internet_session_status_trigger BEFORE UPDATE ON internet_sessions FOR EACH ROW EXECUTE FUNCTION update_internet_session_status();

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Function to get user's free quota usage for current month
CREATE OR REPLACE FUNCTION get_user_free_quota_usage(user_uuid UUID)
RETURNS INTEGER AS $$
DECLARE
    total_used INTEGER;
BEGIN
    SELECT COALESCE(SUM(data_mb), 0) INTO total_used
    FROM internet_sessions 
    WHERE user_id = user_uuid 
    AND price_ngn = 0 
    AND created_at >= DATE_TRUNC('month', NOW());
    
    RETURN total_used;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user has unlimited access
CREATE OR REPLACE FUNCTION user_has_unlimited_access(user_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    has_access BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM user_subscriptions 
        WHERE user_id = user_uuid 
        AND subscription_type = 'unlimited' 
        AND status = 'active'
        AND (expires_at IS NULL OR expires_at > NOW())
    ) INTO has_access;
    
    RETURN has_access;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SAMPLE DATA (OPTIONAL - REMOVE IN PRODUCTION)
-- =====================================================

/*
-- Sample user (for testing)
INSERT INTO users (id, email, first_name, last_name) VALUES 
('d715c2d1-106b-4458-9252-f35ea20d7b85', 'test@kswifi.app', 'Test', 'User')
ON CONFLICT (id) DO NOTHING;

-- Sample user subscription (unlimited access)
INSERT INTO user_subscriptions (user_id, subscription_type, plan_type, status) VALUES 
('d715c2d1-106b-4458-9252-f35ea20d7b85', 'unlimited', 'unlimited_required', 'active')
ON CONFLICT DO NOTHING;
*/

-- =====================================================
-- CRITICAL: REFRESH POSTGREST SCHEMA CACHE
-- =====================================================

-- This is CRITICAL - PostgREST must reload schema to see new tables/columns
NOTIFY pgrst, 'reload schema';

-- Success message
SELECT 'KSWiFi database schema created successfully! 🎉 All tables, indexes, triggers, and functions are ready!' as message;