// Supabase configuration - REQUIRES real environment variables
const supabaseUrlEnv = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKeyEnv = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Validate required environment variables
if (!supabaseUrlEnv || !supabaseAnonKeyEnv) {
  throw new Error(
    'Missing required Supabase environment variables. Please set:\n' +
    '- NEXT_PUBLIC_SUPABASE_URL\n' +
    '- NEXT_PUBLIC_SUPABASE_ANON_KEY\n\n' +
    'Get these from your Supabase project settings.'
  );
}

// Export validated strings (safe to assert as string after validation)
export const supabaseUrl: string = supabaseUrlEnv;
export const supabaseAnonKey: string = supabaseAnonKeyEnv;
