-- WiFi Network Credentials Storage Migration
-- Run this ONLY if you want to store WiFi credentials in database
-- This is SAFE - won't destroy existing tables

-- Create wifi_networks table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.wifi_networks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    network_name VARCHAR(255) NOT NULL UNIQUE,
    ssid VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    security_type VARCHAR(50) NOT NULL DEFAULT 'WPA2',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert your WiFi network credentials
INSERT INTO public.wifi_networks (network_name, ssid, password, security_type, is_active)
VALUES ('primary_network', 'KSWIFI', 'OLAmilekan@$112', 'WPA2', true)
ON CONFLICT (network_name) DO UPDATE SET
    ssid = EXCLUDED.ssid,
    password = EXCLUDED.password,
    security_type = EXCLUDED.security_type,
    updated_at = NOW();

-- Create RLS policy
ALTER TABLE public.wifi_networks ENABLE ROW LEVEL SECURITY;

-- Policy: Allow service role to read/write wifi networks
CREATE POLICY IF NOT EXISTS "Service role can manage wifi networks" ON public.wifi_networks
    FOR ALL USING (true);

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_wifi_networks_active ON public.wifi_networks(is_active);
CREATE INDEX IF NOT EXISTS idx_wifi_networks_network_name ON public.wifi_networks(network_name);

-- Verify the data was inserted
SELECT * FROM public.wifi_networks WHERE network_name = 'primary_network';