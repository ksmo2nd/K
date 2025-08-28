-- Fix WiFi Table Columns to Match Code
-- Add missing columns that the code expects

-- Add missing columns to wifi_access_tokens table
ALTER TABLE public.wifi_access_tokens 
ADD COLUMN IF NOT EXISTS qr_code_data TEXT;

ALTER TABLE public.wifi_access_tokens 
ADD COLUMN IF NOT EXISTS redirect_url TEXT;

ALTER TABLE public.wifi_access_tokens 
ADD COLUMN IF NOT EXISTS bandwidth_limit_mbps INTEGER;

-- Update token_type constraint to include 'wifi_secure_access'
ALTER TABLE public.wifi_access_tokens 
DROP CONSTRAINT IF EXISTS wifi_access_tokens_token_type_check;

ALTER TABLE public.wifi_access_tokens 
ADD CONSTRAINT wifi_access_tokens_token_type_check 
CHECK (token_type IN ('wifi_qr', 'captive_portal', 'direct_access', 'wifi_secure_access'));

-- Verify the columns exist
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'wifi_access_tokens' 
AND column_name IN ('qr_code_data', 'redirect_url', 'bandwidth_limit_mbps', 'token_type')
ORDER BY column_name;