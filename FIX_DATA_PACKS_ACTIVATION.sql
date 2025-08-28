-- Fix Data Pack Activation - Add Missing Columns
-- The activate_data_pack RPC function expects these columns but they're missing from the original table

-- Add missing columns to data_packs table
ALTER TABLE public.data_packs 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false;

ALTER TABLE public.data_packs 
ADD COLUMN IF NOT EXISTS activated_at TIMESTAMP WITH TIME ZONE;

-- Add missing columns to esims table (also referenced by the RPC)
ALTER TABLE public.esims 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false;

ALTER TABLE public.esims 
ADD COLUMN IF NOT EXISTS data_pack_id UUID;

-- Add foreign key constraint for data_pack_id
ALTER TABLE public.esims 
ADD CONSTRAINT fk_esims_data_pack_id 
FOREIGN KEY (data_pack_id) REFERENCES data_packs(id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_data_packs_is_active ON data_packs(is_active);
CREATE INDEX IF NOT EXISTS idx_data_packs_user_id_active ON data_packs(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_esims_is_active ON esims(is_active);
CREATE INDEX IF NOT EXISTS idx_esims_data_pack_id ON esims(data_pack_id);

-- Verify the columns were added
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name IN ('data_packs', 'esims')
AND column_name IN ('is_active', 'activated_at', 'data_pack_id')
ORDER BY table_name, column_name;