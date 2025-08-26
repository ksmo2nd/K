-- Fix internet session status trigger that was preventing status='active' updates
-- The trigger was forcing status back to 'available' whenever progress_percent >= 100
-- This prevented sessions from being marked as 'active' during activation

-- Update the trigger function to only auto-set 'available' when transitioning from 'downloading'
-- This allows manual activation (available -> active) to work properly
CREATE OR REPLACE FUNCTION update_internet_session_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark as exhausted if all data is used
    IF NEW.data_used_mb >= NEW.data_mb THEN
        NEW.status = 'exhausted';
    -- Mark as expired if past expiry date (if set)
    ELSIF NEW.expires_at IS NOT NULL AND NEW.expires_at < NOW() THEN
        NEW.status = 'expired';
    -- Mark as available if download complete (but only if transitioning from downloading)
    -- This prevents overriding manual activation (available -> active)
    ELSIF NEW.progress_percent >= 100 AND OLD.status = 'downloading' THEN
        NEW.status = 'available';
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Notify PostgREST to reload schema cache
NOTIFY pgrst, 'reload schema';

SELECT 'Internet session status trigger fixed! Sessions can now be properly activated.' as message;