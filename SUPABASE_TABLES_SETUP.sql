-- 🗄️  KSWiFi Database Schema Setup
-- Run this in Supabase SQL Editor to create all required tables

-- 1. eSIMs Table
CREATE TABLE IF NOT EXISTS esims (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    iccid TEXT UNIQUE NOT NULL,
    imsi TEXT,
    msisdn TEXT,
    activation_code TEXT NOT NULL,
    qr_code_data TEXT,
    status TEXT DEFAULT 'pending',
    apn TEXT DEFAULT 'kswifi.internet',
    username TEXT,
    password TEXT,
    bundle_size_mb INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    activated_at TIMESTAMP WITH TIME ZONE
);

-- 2. Internet Sessions Table
CREATE TABLE IF NOT EXISTS internet_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    session_name TEXT NOT NULL,
    data_mb INTEGER NOT NULL,
    price_ngn INTEGER DEFAULT 0,
    validity_days INTEGER,
    plan_type TEXT DEFAULT 'standard',
    status TEXT DEFAULT 'downloading',
    download_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    progress_percent INTEGER DEFAULT 0,
    esim_id UUID REFERENCES esims(id),
    data_used_mb INTEGER DEFAULT 0,
    data_remaining_mb INTEGER,
    expires_at TIMESTAMP WITH TIME ZONE,
    download_completed_at TIMESTAMP WITH TIME ZONE,
    activated_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- 3. User Subscriptions Table
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    price_ngn INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 4. Data Usage Tracking Table
CREATE TABLE IF NOT EXISTS data_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    esim_id UUID REFERENCES esims(id),
    session_id UUID REFERENCES internet_sessions(id),
    data_used_mb INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    location TEXT,
    device_info TEXT
);

-- 5. Data Packs Table (if needed for bundle service)
CREATE TABLE IF NOT EXISTS data_packs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    total_data_mb INTEGER NOT NULL,
    used_data_mb INTEGER DEFAULT 0,
    remaining_data_mb INTEGER,
    price_ngn INTEGER NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_esims_user_id ON esims(user_id);
CREATE INDEX IF NOT EXISTS idx_esims_status ON esims(status);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON internet_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON internet_sessions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_data_usage_esim ON data_usage(esim_id);
CREATE INDEX IF NOT EXISTS idx_data_packs_user_id ON data_packs(user_id);

-- Row Level Security (RLS) Policies
ALTER TABLE esims ENABLE ROW LEVEL SECURITY;
ALTER TABLE internet_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_packs ENABLE ROW LEVEL SECURITY;

-- Policies for esims
CREATE POLICY "Users can view own esims" ON esims
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own esims" ON esims
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own esims" ON esims
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Policies for internet_sessions
CREATE POLICY "Users can view own sessions" ON internet_sessions
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own sessions" ON internet_sessions
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own sessions" ON internet_sessions
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Policies for user_subscriptions
CREATE POLICY "Users can view own subscriptions" ON user_subscriptions
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own subscriptions" ON user_subscriptions
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- Policies for data_usage
CREATE POLICY "Users can view own usage" ON data_usage
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM esims 
            WHERE esims.id = data_usage.esim_id 
            AND esims.user_id = auth.uid()::text
        )
    );

-- Policies for data_packs
CREATE POLICY "Users can view own data packs" ON data_packs
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own data packs" ON data_packs
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own data packs" ON data_packs
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Success message
SELECT 'KSWiFi database schema created successfully! 🎉' as status;