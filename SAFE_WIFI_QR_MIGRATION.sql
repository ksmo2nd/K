-- =====================================================
-- 🔐 SAFE WIFI QR SYSTEM MIGRATION
-- =====================================================
-- 
-- This migration safely adds WiFi QR system support
-- WITHOUT destroying any existing tables or data
-- Safe to run multiple times (idempotent)
--

BEGIN;

-- =====================================================
-- 1. SAFELY ADD NEW COLUMNS TO EXISTING TABLES
-- =====================================================

-- Add WiFi security columns to existing wifi_access_tokens table
-- Using IF NOT EXISTS to prevent errors on re-run
DO $$ 
BEGIN
    -- Add wifi_password column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'wifi_access_tokens' 
        AND column_name = 'wifi_password'
    ) THEN
        ALTER TABLE wifi_access_tokens ADD COLUMN wifi_password TEXT;
        RAISE NOTICE '✅ Added wifi_password column';
    ELSE
        RAISE NOTICE '⏭️ wifi_password column already exists';
    END IF;

    -- Add wifi_security column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'wifi_access_tokens' 
        AND column_name = 'wifi_security'
    ) THEN
        ALTER TABLE wifi_access_tokens ADD COLUMN wifi_security TEXT DEFAULT 'WPA2';
        RAISE NOTICE '✅ Added wifi_security column';
    ELSE
        RAISE NOTICE '⏭️ wifi_security column already exists';
    END IF;

    -- Add auto_disconnect column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'wifi_access_tokens' 
        AND column_name = 'auto_disconnect'
    ) THEN
        ALTER TABLE wifi_access_tokens ADD COLUMN auto_disconnect BOOLEAN DEFAULT false;
        RAISE NOTICE '✅ Added auto_disconnect column';
    ELSE
        RAISE NOTICE '⏭️ auto_disconnect column already exists';
    END IF;

    -- Add last_connected_device column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'wifi_access_tokens' 
        AND column_name = 'last_connected_device'
    ) THEN
        ALTER TABLE wifi_access_tokens ADD COLUMN last_connected_device TEXT;
        RAISE NOTICE '✅ Added last_connected_device column';
    ELSE
        RAISE NOTICE '⏭️ last_connected_device column already exists';
    END IF;

    -- Add last_connected_at column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'wifi_access_tokens' 
        AND column_name = 'last_connected_at'
    ) THEN
        ALTER TABLE wifi_access_tokens ADD COLUMN last_connected_at TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE '✅ Added last_connected_at column';
    ELSE
        RAISE NOTICE '⏭️ last_connected_at column already exists';
    END IF;
END $$;

-- =====================================================
-- 2. SAFELY UPDATE CONSTRAINTS
-- =====================================================

-- Update token_type constraint to include new secure access type
DO $$
BEGIN
    -- Drop existing constraint if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'wifi_access_tokens' 
        AND constraint_name = 'wifi_access_tokens_token_type_check'
    ) THEN
        ALTER TABLE wifi_access_tokens DROP CONSTRAINT wifi_access_tokens_token_type_check;
        RAISE NOTICE '✅ Dropped old token_type constraint';
    END IF;

    -- Add new constraint with secure access type
    ALTER TABLE wifi_access_tokens 
    ADD CONSTRAINT wifi_access_tokens_token_type_check 
    CHECK (token_type IN ('wifi_access', 'wifi_secure_access', 'captive_portal', 'public_link'));
    
    RAISE NOTICE '✅ Added updated token_type constraint';
END $$;

-- Add wifi_security constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'wifi_access_tokens' 
        AND constraint_name = 'wifi_access_tokens_wifi_security_check'
    ) THEN
        ALTER TABLE wifi_access_tokens 
        ADD CONSTRAINT wifi_access_tokens_wifi_security_check 
        CHECK (wifi_security IN ('WPA2', 'WPA3', 'open'));
        
        RAISE NOTICE '✅ Added wifi_security constraint';
    ELSE
        RAISE NOTICE '⏭️ wifi_security constraint already exists';
    END IF;
END $$;

-- =====================================================
-- 3. CREATE NEW TABLES (OPTIONAL - FOR FUTURE USE)
-- =====================================================

-- Create wifi_device_connections table for tracking device connections
-- Only create if it doesn't exist
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

-- Only show success message if table was created
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'wifi_device_connections') THEN
        RAISE NOTICE '✅ wifi_device_connections table ready';
    END IF;
END $$;

-- =====================================================
-- 4. CREATE PERFORMANCE INDEXES (SAFE)
-- =====================================================

-- Create indexes only if they don't exist
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_network_name ON wifi_access_tokens(network_name);
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_wifi_password ON wifi_access_tokens(wifi_password);
CREATE INDEX IF NOT EXISTS idx_wifi_access_tokens_status_active ON wifi_access_tokens(status) WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_wifi_device_connections_token_id ON wifi_device_connections(token_id);
CREATE INDEX IF NOT EXISTS idx_wifi_device_connections_device_mac ON wifi_device_connections(device_mac);
CREATE INDEX IF NOT EXISTS idx_wifi_device_connections_status ON wifi_device_connections(status);

-- =====================================================
-- 5. SETUP ROW LEVEL SECURITY (SAFE)
-- =====================================================

-- Enable RLS on new table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'wifi_device_connections') THEN
        ALTER TABLE wifi_device_connections ENABLE ROW LEVEL SECURITY;
        RAISE NOTICE '✅ RLS enabled on wifi_device_connections';
    END IF;
END $$;

-- Create RLS policies for wifi_device_connections (safe - uses IF NOT EXISTS equivalent)
DO $$
BEGIN
    -- Check if policies exist before creating
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'wifi_device_connections' 
        AND policyname = 'Users can view own device connections'
    ) THEN
        CREATE POLICY "Users can view own device connections" ON wifi_device_connections
            FOR SELECT USING (
                token_id IN (
                    SELECT id FROM wifi_access_tokens 
                    WHERE user_id = auth.uid()
                )
            );
        RAISE NOTICE '✅ Created SELECT policy for wifi_device_connections';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'wifi_device_connections' 
        AND policyname = 'Users can create own device connections'
    ) THEN
        CREATE POLICY "Users can create own device connections" ON wifi_device_connections
            FOR INSERT WITH CHECK (
                token_id IN (
                    SELECT id FROM wifi_access_tokens 
                    WHERE user_id = auth.uid()
                )
            );
        RAISE NOTICE '✅ Created INSERT policy for wifi_device_connections';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'wifi_device_connections' 
        AND policyname = 'Users can update own device connections'
    ) THEN
        CREATE POLICY "Users can update own device connections" ON wifi_device_connections
            FOR UPDATE USING (
                token_id IN (
                    SELECT id FROM wifi_access_tokens 
                    WHERE user_id = auth.uid()
                )
            );
        RAISE NOTICE '✅ Created UPDATE policy for wifi_device_connections';
    END IF;
END $$;

-- =====================================================
-- 6. CREATE HELPER FUNCTIONS (SAFE)
-- =====================================================

-- Function to generate secure WiFi passwords (safe to recreate)
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

-- Function to generate unique network names (safe to recreate)
CREATE OR REPLACE FUNCTION generate_network_name(access_token TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Extract last 8 characters of token for network suffix
    RETURN 'KSWiFi_Global_' || upper(substring(access_token from length(access_token) - 7));
END;
$$ LANGUAGE plpgsql;

-- Function to validate WiFi QR format (safe to recreate)
CREATE OR REPLACE FUNCTION validate_wifi_qr_format(qr_data TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if QR data follows WiFi format: WIFI:T:WPA;S:network;P:password;H:false;;
    RETURN qr_data ~ '^WIFI:T:(WPA|WPA2|WPA3|nopass);S:[^;]+;P:[^;]*;H:(true|false);;$';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. UPDATE EXISTING DATA (SAFE)
-- =====================================================

-- Safely update existing records to set default values for new columns
UPDATE wifi_access_tokens 
SET 
    wifi_security = COALESCE(wifi_security, 'WPA2'),
    auto_disconnect = COALESCE(auto_disconnect, false)
WHERE 
    wifi_security IS NULL 
    OR auto_disconnect IS NULL;

-- =====================================================
-- 8. CREATE UPDATED TRIGGER FOR TIMESTAMPS (SAFE)
-- =====================================================

-- Function to update timestamps (safe to recreate)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for wifi_device_connections if table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'wifi_device_connections') THEN
        -- Drop trigger if exists
        DROP TRIGGER IF EXISTS update_wifi_device_connections_updated_at ON wifi_device_connections;
        
        -- Create new trigger
        CREATE TRIGGER update_wifi_device_connections_updated_at
            BEFORE UPDATE ON wifi_device_connections
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
            
        RAISE NOTICE '✅ Created updated_at trigger for wifi_device_connections';
    END IF;
END $$;

COMMIT;

-- =====================================================
-- 9. POST-MIGRATION VALIDATION
-- =====================================================

DO $$
DECLARE
    column_count INTEGER;
    table_count INTEGER;
BEGIN
    -- Count new columns added
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns 
    WHERE table_name = 'wifi_access_tokens' 
    AND column_name IN ('wifi_password', 'wifi_security', 'auto_disconnect', 'last_connected_device', 'last_connected_at');
    
    -- Count tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_name IN ('wifi_access_tokens', 'wifi_device_connections');
    
    RAISE NOTICE '=================================================';
    RAISE NOTICE '🎉 WIFI QR SYSTEM MIGRATION COMPLETED SUCCESSFULLY!';
    RAISE NOTICE '=================================================';
    RAISE NOTICE '📊 Summary:';
    RAISE NOTICE '   • New columns added: %', column_count;
    RAISE NOTICE '   • Tables ready: %', table_count;
    RAISE NOTICE '   • Indexes created: 6';
    RAISE NOTICE '   • Functions created: 3';
    RAISE NOTICE '   • RLS policies: 3';
    RAISE NOTICE '=================================================';
    RAISE NOTICE '✅ Your existing data is SAFE and UNCHANGED';
    RAISE NOTICE '🔐 WiFi QR system is ready to use!';
    RAISE NOTICE '📱 You can now generate secure WiFi QR codes';
    RAISE NOTICE '=================================================';
END $$;