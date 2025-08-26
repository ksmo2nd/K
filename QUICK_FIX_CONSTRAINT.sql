-- QUICK FIX: Update CHECK constraint to allow wifi_download
-- Copy and paste this into Supabase SQL Editor

-- Drop the existing constraint that's blocking wifi_download
ALTER TABLE internet_sessions DROP CONSTRAINT IF EXISTS internet_sessions_plan_type_check;

-- Add new constraint that includes wifi_download
ALTER TABLE internet_sessions ADD CONSTRAINT internet_sessions_plan_type_check 
CHECK (plan_type IN ('default', 'unlimited_required', 'premium', 'wifi_download'));

-- Refresh PostgREST schema cache
NOTIFY pgrst, 'reload schema';

-- Test message
SELECT 'CHECK constraint updated successfully! wifi_download is now allowed.' as message;