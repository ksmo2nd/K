-- Add support for unlimited plans and eSIM activation

-- Add plan_type to data_packs table
ALTER TABLE data_packs ADD COLUMN IF NOT EXISTS plan_type TEXT DEFAULT 'standard';
-- plan_type: 'standard' or 'unlimited'

-- Add NGN currency support
ALTER TABLE data_packs ADD COLUMN IF NOT EXISTS price_ngn FLOAT;

-- Add activation status to data_packs
ALTER TABLE data_packs ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false;
ALTER TABLE data_packs ADD COLUMN IF NOT EXISTS activated_at TIMESTAMPTZ;

-- Link eSIMs to data packs
ALTER TABLE esims ADD COLUMN IF NOT EXISTS data_pack_id UUID REFERENCES data_packs(id);
ALTER TABLE esims ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_data_packs_plan_type ON data_packs(plan_type);
CREATE INDEX IF NOT EXISTS idx_data_packs_is_active ON data_packs(is_active);
CREATE INDEX IF NOT EXISTS idx_esims_is_active ON esims(is_active);
CREATE INDEX IF NOT EXISTS idx_esims_data_pack_id ON esims(data_pack_id);

-- Update data_pack_status enum to include 'inactive'
-- Note: In PostgreSQL, we need to add the new value to the existing enum
ALTER TYPE data_pack_status ADD VALUE IF NOT EXISTS 'inactive';

-- Add a function to activate data pack
CREATE OR REPLACE FUNCTION activate_data_pack(pack_id UUID, esim_id UUID DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
    -- Deactivate any currently active packs for this user
    UPDATE data_packs 
    SET is_active = false 
    WHERE user_id = (SELECT user_id FROM data_packs WHERE id = pack_id)
      AND is_active = true;
    
    -- Activate the selected pack
    UPDATE data_packs 
    SET is_active = true, 
        activated_at = NOW(),
        status = 'active'
    WHERE id = pack_id;
    
    -- If eSIM provided, link it to the pack
    IF esim_id IS NOT NULL THEN
        -- Deactivate other eSIMs for this user
        UPDATE esims 
        SET is_active = false 
        WHERE user_id = (SELECT user_id FROM data_packs WHERE id = pack_id)
          AND is_active = true;
        
        -- Activate the selected eSIM and link to pack
        UPDATE esims 
        SET is_active = true,
            data_pack_id = pack_id,
            status = 'active'
        WHERE id = esim_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add a function to deactivate data pack
CREATE OR REPLACE FUNCTION deactivate_data_pack(pack_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Deactivate the pack
    UPDATE data_packs 
    SET is_active = false 
    WHERE id = pack_id;
    
    -- Deactivate linked eSIMs
    UPDATE esims 
    SET is_active = false,
        status = 'suspended'
    WHERE data_pack_id = pack_id;
END;
$$ LANGUAGE plpgsql;