-- Create tables for KSWiFi Backend Service

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE user_status AS ENUM ('active', 'suspended', 'deleted');
CREATE TYPE data_pack_status AS ENUM ('active', 'expired', 'exhausted');
CREATE TYPE esim_status AS ENUM ('pending', 'active', 'suspended', 'cancelled');

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone_number TEXT,
    status user_status DEFAULT 'active',
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Create data_packs table
CREATE TABLE IF NOT EXISTS data_packs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    total_data_mb FLOAT NOT NULL,
    used_data_mb FLOAT DEFAULT 0.0,
    remaining_data_mb FLOAT NOT NULL,
    price FLOAT NOT NULL,
    currency TEXT DEFAULT 'USD',
    status data_pack_status DEFAULT 'active',
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create esims table
CREATE TABLE IF NOT EXISTS esims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    iccid TEXT UNIQUE NOT NULL,
    imsi TEXT UNIQUE NOT NULL,
    msisdn TEXT,
    activation_code TEXT UNIQUE NOT NULL,
    qr_code_data TEXT NOT NULL,
    status esim_status DEFAULT 'pending',
    activated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    apn TEXT DEFAULT 'internet',
    username TEXT,
    password TEXT
);

-- Create usage_logs table
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    data_pack_id UUID REFERENCES data_packs(id) ON DELETE CASCADE,
    data_used_mb FLOAT NOT NULL,
    session_duration INTEGER,
    location TEXT,
    device_info TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_data_packs_user_id ON data_packs(user_id);
CREATE INDEX IF NOT EXISTS idx_esims_user_id ON esims(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_data_pack_id ON usage_logs(data_pack_id);

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_packs_updated_at
    BEFORE UPDATE ON data_packs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_esims_updated_at
    BEFORE UPDATE ON esims
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create RLS policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_packs ENABLE ROW LEVEL SECURITY;
ALTER TABLE esims ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view their own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);

-- Data packs policies
CREATE POLICY "Users can view their own data packs"
    ON data_packs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own data packs"
    ON data_packs FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- eSIMs policies
CREATE POLICY "Users can view their own eSIMs"
    ON esims FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own eSIMs"
    ON esims FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Usage logs policies
CREATE POLICY "Users can view their own usage logs"
    ON usage_logs FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own usage logs"
    ON usage_logs FOR INSERT
    WITH CHECK (auth.uid() = user_id);
