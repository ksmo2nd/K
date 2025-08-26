-- Complete Supabase Schema for KSWiFi Backend
-- Run this in your Supabase SQL Editor to create all required tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS users (
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
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User devices table (for push notifications)
CREATE TABLE IF NOT EXISTS user_devices (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    push_token TEXT UNIQUE NOT NULL,
    device_type TEXT, -- 'ios', 'android', 'web'
    device_name TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User subscriptions table
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subscription_type TEXT NOT NULL, -- 'free', 'unlimited'
    plan_type TEXT DEFAULT 'free', -- 'free', 'unlimited_required', 'premium'
    status TEXT DEFAULT 'active', -- 'active', 'expired', 'cancelled'
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- eSIMs table
CREATE TABLE IF NOT EXISTS esims (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    iccid TEXT UNIQUE NOT NULL,
    imsi TEXT,
    msisdn TEXT, -- Phone number (can be NULL for internet-only eSIMs)
    activation_code TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'active', 'suspended', 'expired'
    apn TEXT DEFAULT 'kswifi.internet',
    username TEXT,
    password TEXT,
    bundle_size_mb INTEGER,
    activated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data packs table
CREATE TABLE IF NOT EXISTS data_packs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    data_mb INTEGER NOT NULL,
    used_data_mb INTEGER DEFAULT 0,
    remaining_data_mb INTEGER,
    price_ngn INTEGER DEFAULT 0,
    price_usd DECIMAL(10,2) DEFAULT 0.00,
    status TEXT DEFAULT 'active', -- 'active', 'exhausted', 'expired', 'cancelled'
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Internet sessions table
CREATE TABLE IF NOT EXISTS internet_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_name TEXT NOT NULL,
    data_mb INTEGER NOT NULL,
    data_used_mb INTEGER DEFAULT 0,
    data_remaining_mb INTEGER,
    price_ngn INTEGER DEFAULT 0,
    price_usd DECIMAL(10,2) DEFAULT 0.00,
    status TEXT DEFAULT 'downloading', -- 'downloading', 'available', 'active', 'exhausted', 'expired'
    progress_percent INTEGER DEFAULT 0,
    esim_id UUID REFERENCES esims(id) ON DELETE SET NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    activated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data usage logs table
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_pack_id UUID REFERENCES data_packs(id) ON DELETE SET NULL,
    session_id UUID REFERENCES internet_sessions(id) ON DELETE SET NULL,
    data_used_mb INTEGER NOT NULL,
    usage_type TEXT, -- 'session_download', 'internet_browsing', 'background'
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data usage table (for eSIM monitoring)
CREATE TABLE IF NOT EXISTS data_usage (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    esim_id UUID REFERENCES esims(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_used_mb INTEGER NOT NULL,
    data_remaining_mb INTEGER,
    usage_period TEXT, -- 'daily', 'weekly', 'monthly'
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info', -- 'info', 'warning', 'success', 'error'
    read BOOLEAN DEFAULT FALSE,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_push_token ON user_devices(push_token);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_esims_user_id ON esims(user_id);
CREATE INDEX IF NOT EXISTS idx_esims_iccid ON esims(iccid);
CREATE INDEX IF NOT EXISTS idx_esims_status ON esims(status);
CREATE INDEX IF NOT EXISTS idx_data_packs_user_id ON data_packs(user_id);
CREATE INDEX IF NOT EXISTS idx_data_packs_status ON data_packs(status);
CREATE INDEX IF NOT EXISTS idx_internet_sessions_user_id ON internet_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_internet_sessions_status ON internet_sessions(status);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created_at ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_data_usage_esim_id ON data_usage(esim_id);
CREATE INDEX IF NOT EXISTS idx_data_usage_user_id ON data_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_devices_updated_at BEFORE UPDATE ON user_devices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_subscriptions_updated_at BEFORE UPDATE ON user_subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_esims_updated_at BEFORE UPDATE ON esims FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_data_packs_updated_at BEFORE UPDATE ON data_packs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_internet_sessions_updated_at BEFORE UPDATE ON internet_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Set remaining_data_mb for data_packs
CREATE OR REPLACE FUNCTION set_remaining_data_mb()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.remaining_data_mb IS NULL THEN
        NEW.remaining_data_mb = NEW.data_mb - COALESCE(NEW.used_data_mb, 0);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER set_data_packs_remaining BEFORE INSERT OR UPDATE ON data_packs FOR EACH ROW EXECUTE FUNCTION set_remaining_data_mb();

-- Set remaining_data_mb for internet_sessions
CREATE OR REPLACE FUNCTION set_session_remaining_data_mb()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.data_remaining_mb IS NULL THEN
        NEW.data_remaining_mb = NEW.data_mb - COALESCE(NEW.data_used_mb, 0);
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER set_sessions_remaining BEFORE INSERT OR UPDATE ON internet_sessions FOR EACH ROW EXECUTE FUNCTION set_session_remaining_data_mb();

-- Insert some sample data for testing (optional)
-- Uncomment if you want test data

/*
-- Sample user
INSERT INTO users (id, email, first_name, last_name) VALUES 
('123e4567-e89b-12d3-a456-426614174000', 'test@kswifi.com', 'Test', 'User')
ON CONFLICT (email) DO NOTHING;

-- Sample user subscription (unlimited)
INSERT INTO user_subscriptions (user_id, subscription_type, status) VALUES 
('123e4567-e89b-12d3-a456-426614174000', 'unlimited', 'active')
ON CONFLICT DO NOTHING;
*/

-- Success message
SELECT 'KSWiFi database schema created successfully! 🎉' as message;

-- Fix missing columns (run these if you get column not found errors)

-- Add plan_type column to user_subscriptions if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_subscriptions' 
                   AND column_name = 'plan_type') THEN
        ALTER TABLE user_subscriptions ADD COLUMN plan_type TEXT DEFAULT 'free';
    END IF;
END $$;

-- Ensure data_used_mb exists in internet_sessions (should already exist)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'internet_sessions' 
                   AND column_name = 'data_used_mb') THEN
        ALTER TABLE internet_sessions ADD COLUMN data_used_mb INTEGER DEFAULT 0;
    END IF;
END $$;

-- Refresh PostgREST schema cache (critical for API to see new columns)
NOTIFY pgrst, 'reload schema';