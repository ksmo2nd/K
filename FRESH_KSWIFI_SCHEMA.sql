-- =====================================================
-- 🚀 FRESH KSWIFI DATABASE SCHEMA
-- =====================================================
-- This schema is designed to match ALL codebase features
-- Safe to run - will clear existing data and start fresh
-- No triggers that interfere with status updates
-- No generated columns that cause INSERT errors
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 🧹 CLEAN SLATE - DROP EXISTING TABLES
-- =====================================================
-- Drop tables in correct order to avoid foreign key conflicts
DROP TABLE IF EXISTS usage_logs CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS user_devices CASCADE;
DROP TABLE IF EXISTS internet_sessions CASCADE;
DROP TABLE IF EXISTS data_packs CASCADE;
DROP TABLE IF EXISTS esims CASCADE;
DROP TABLE IF EXISTS user_subscriptions CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop any existing triggers and functions
DROP TRIGGER IF EXISTS update_internet_session_status_trigger ON internet_sessions CASCADE;
DROP TRIGGER IF EXISTS update_data_pack_status_trigger ON data_packs CASCADE;
DROP FUNCTION IF EXISTS update_internet_session_status() CASCADE;
DROP FUNCTION IF EXISTS update_data_pack_status() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- =====================================================
-- 👥 USERS & AUTHENTICATION
-- =====================================================

-- Users table (matches Supabase auth.users structure)
CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email TEXT UNIQUE,
    phone TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sign_in_at TIMESTAMP WITH TIME ZONE,
    email_confirmed_at TIMESTAMP WITH TIME ZONE,
    phone_confirmed_at TIMESTAMP WITH TIME ZONE
);

-- User profiles table
CREATE TABLE user_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    first_name TEXT,
    last_name TEXT,
    avatar_url TEXT,
    phone_number TEXT,
    country TEXT DEFAULT 'NG',
    timezone TEXT DEFAULT 'Africa/Lagos',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User devices for push notifications
CREATE TABLE user_devices (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    device_id TEXT,
    push_token TEXT UNIQUE,
    platform TEXT CHECK (platform IN ('ios', 'android', 'web')),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User subscriptions
CREATE TABLE user_subscriptions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_type TEXT DEFAULT 'free' CHECK (plan_type IN ('free', 'premium', 'unlimited')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    auto_renew BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 📱 ESIM MANAGEMENT
-- =====================================================

-- eSIMs table
CREATE TABLE esims (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    iccid TEXT NOT NULL UNIQUE, -- Integrated Circuit Card Identifier
    imsi TEXT, -- International Mobile Subscriber Identity
    msisdn TEXT, -- Mobile phone number (can be NULL for data-only)
    activation_code TEXT NOT NULL,
    qr_code_data TEXT, -- LPA string for QR codes
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'active', 'suspended', 'cancelled')),
    apn TEXT DEFAULT 'kswifi.data',
    username TEXT,
    password TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 📦 DATA PACKS
-- =====================================================

-- Data packs table (NO GENERATED COLUMNS to avoid INSERT errors)
CREATE TABLE data_packs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    data_mb INTEGER NOT NULL CHECK (data_mb > 0),
    used_data_mb INTEGER DEFAULT 0 CHECK (used_data_mb >= 0),
    -- remaining_data_mb calculated in application, not database
    price_ngn INTEGER DEFAULT 0 CHECK (price_ngn >= 0),
    price_usd DECIMAL(10,2) DEFAULT 0.00 CHECK (price_usd >= 0),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'exhausted', 'expired', 'cancelled')),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 🌐 INTERNET SESSIONS
-- =====================================================

-- Internet sessions table (NO TRIGGERS to interfere with status updates)
CREATE TABLE internet_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL, -- Maps to frontend session IDs like 'default_1gb'
    session_name TEXT NOT NULL,
    data_mb INTEGER NOT NULL CHECK (data_mb > 0),
    data_used_mb INTEGER DEFAULT 0 CHECK (data_used_mb >= 0),
    -- data_remaining_mb calculated in application, not database
    price_ngn INTEGER DEFAULT 0 CHECK (price_ngn >= 0),
    price_usd DECIMAL(10,2) DEFAULT 0.00 CHECK (price_usd >= 0),
    status TEXT DEFAULT 'downloading' CHECK (status IN ('downloading', 'available', 'active', 'exhausted', 'expired', 'failed')),
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent >= 0 AND progress_percent <= 100),
    plan_type TEXT DEFAULT 'default' CHECK (plan_type IN ('default', 'unlimited_required', 'premium', 'wifi_download')),
    source_network TEXT,
    network_quality TEXT DEFAULT 'good' CHECK (network_quality IN ('excellent', 'good', 'fair', 'poor')),
    esim_id UUID REFERENCES esims(id) ON DELETE SET NULL,
    download_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    download_completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    activated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 📊 USAGE TRACKING
-- =====================================================

-- Usage logs table
CREATE TABLE usage_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_pack_id UUID REFERENCES data_packs(id) ON DELETE SET NULL,
    session_id UUID REFERENCES internet_sessions(id) ON DELETE SET NULL,
    data_used_mb INTEGER NOT NULL CHECK (data_used_mb > 0),
    usage_type TEXT DEFAULT 'data_usage' CHECK (usage_type IN ('data_usage', 'session_download', 'esim_activation')),
    source_network TEXT,
    device_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 🔔 NOTIFICATIONS
-- =====================================================

-- Notifications table
CREATE TABLE notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info' CHECK (type IN ('info', 'warning', 'error', 'success')),
    read BOOLEAN DEFAULT FALSE,
    action_url TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 🔄 AUTOMATIC TIMESTAMP UPDATES
-- =====================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_devices_updated_at 
    BEFORE UPDATE ON user_devices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_subscriptions_updated_at 
    BEFORE UPDATE ON user_subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_esims_updated_at 
    BEFORE UPDATE ON esims 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_packs_updated_at 
    BEFORE UPDATE ON data_packs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_internet_sessions_updated_at 
    BEFORE UPDATE ON internet_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notifications_updated_at 
    BEFORE UPDATE ON notifications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 📈 INDEXES FOR PERFORMANCE
-- =====================================================

-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX idx_user_devices_push_token ON user_devices(push_token);

-- eSIM lookups
CREATE INDEX idx_esims_user_id ON esims(user_id);
CREATE INDEX idx_esims_status ON esims(status);
CREATE INDEX idx_esims_iccid ON esims(iccid);

-- Data pack lookups
CREATE INDEX idx_data_packs_user_id ON data_packs(user_id);
CREATE INDEX idx_data_packs_status ON data_packs(status);
CREATE INDEX idx_data_packs_user_status ON data_packs(user_id, status);

-- Internet session lookups
CREATE INDEX idx_internet_sessions_user_id ON internet_sessions(user_id);
CREATE INDEX idx_internet_sessions_status ON internet_sessions(status);
CREATE INDEX idx_internet_sessions_user_status ON internet_sessions(user_id, status);
CREATE INDEX idx_internet_sessions_source_network ON internet_sessions(source_network);

-- Usage log lookups
CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_data_pack_id ON usage_logs(data_pack_id);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);

-- Notification lookups
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, read);

-- =====================================================
-- 🔐 ROW LEVEL SECURITY (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE esims ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_packs ENABLE ROW LEVEL SECURITY;
ALTER TABLE internet_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Users can access their own data
CREATE POLICY "Users can access their own data" ON users
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "Users can access their own profile" ON user_profiles
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own devices" ON user_devices
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own subscriptions" ON user_subscriptions
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own eSIMs" ON esims
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own data packs" ON data_packs
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own sessions" ON internet_sessions
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own usage logs" ON usage_logs
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own notifications" ON notifications
    FOR ALL USING (auth.uid() = user_id);

-- =====================================================
-- 🎉 SCHEMA COMPLETE
-- =====================================================

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload schema';

-- Success message
SELECT '🎉 FRESH KSWIFI SCHEMA CREATED SUCCESSFULLY!' as message,
       '✅ All tables, indexes, triggers, and RLS policies are ready!' as status,
       '🧹 All existing data has been cleared for a fresh start!' as note,
       '🔒 No problematic triggers or generated columns!' as safety;