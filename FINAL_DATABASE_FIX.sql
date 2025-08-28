-- FINAL DATABASE FIX for WiFi QR System
-- Run this in your Supabase SQL Editor
-- This fixes the schema mismatch causing "unable to join network"

-- Add missing columns that the WiFi service code expects
ALTER TABLE public.wifi_access_tokens 
ADD COLUMN IF NOT EXISTS qr_code_data TEXT;

ALTER TABLE public.wifi_access_tokens 
ADD COLUMN IF NOT EXISTS redirect_url TEXT;

ALTER TABLE public.wifi_access_tokens 
ADD COLUMN IF NOT EXISTS bandwidth_limit_mbps INTEGER;

-- Fix token_type constraint to allow 'wifi_secure_access'
ALTER TABLE public.wifi_access_tokens 
DROP CONSTRAINT IF EXISTS wifi_access_tokens_token_type_check;

ALTER TABLE public.wifi_access_tokens 
ADD CONSTRAINT wifi_access_tokens_token_type_check 
CHECK (token_type IN ('wifi_qr', 'captive_portal', 'direct_access', 'wifi_secure_access'));

-- Add missing column that might be referenced
ALTER TABLE public.wifi_access_tokens 
ADD COLUMN IF NOT EXISTS data_used_mb INTEGER DEFAULT 0;

-- Verify the fix worked
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'wifi_access_tokens' 
AND column_name IN ('qr_code_data', 'redirect_url', 'bandwidth_limit_mbps', 'data_used_mb', 'token_type')
ORDER BY column_name;