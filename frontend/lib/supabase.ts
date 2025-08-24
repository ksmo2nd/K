import { createClient } from '@supabase/supabase-js'
import { supabaseUrl, supabaseAnonKey } from './supabase-config'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type { User, Session } from '@supabase/supabase-js'
