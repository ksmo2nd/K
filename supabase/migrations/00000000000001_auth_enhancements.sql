-- Additional tables for enhanced authentication and notifications

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('welcome', 'low_data_alert', 'usage_threshold_alert', 'pack_expired', 'esim_activated')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create user_devices table for push notifications
CREATE TABLE IF NOT EXISTS user_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    push_token TEXT NOT NULL,
    device_type TEXT NOT NULL CHECK (device_type IN ('ios', 'android', 'web')),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(push_token)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_user_devices_user_id ON user_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_user_devices_active ON user_devices(active);

-- Create trigger to update updated_at on user_devices
CREATE TRIGGER update_user_devices_updated_at
    BEFORE UPDATE ON user_devices
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS policies for notifications
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own notifications"
    ON notifications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own notifications"
    ON notifications FOR UPDATE
    USING (auth.uid() = user_id);

-- RLS policies for user_devices
ALTER TABLE user_devices ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own devices"
    ON user_devices FOR ALL
    USING (auth.uid() = user_id);

-- Add alert tracking columns to data_packs
ALTER TABLE data_packs 
ADD COLUMN IF NOT EXISTS alert_75_sent BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS alert_90_sent BOOLEAN DEFAULT FALSE;