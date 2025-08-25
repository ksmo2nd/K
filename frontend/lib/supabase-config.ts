// Supabase configuration - REQUIRES real environment variables in production
const supabaseUrlEnv = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKeyEnv = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Validate required environment variables
if (!supabaseUrlEnv || !supabaseAnonKeyEnv) {
  // Allow build to complete but warn about missing environment variables
  console.warn(
    '⚠️  MISSING SUPABASE ENVIRONMENT VARIABLES:\n' +
    '- NEXT_PUBLIC_SUPABASE_URL\n' +
    '- NEXT_PUBLIC_SUPABASE_ANON_KEY\n\n' +
    'Please set these in your Vercel project settings.\n' +
    'Get these from your Supabase project settings.\n' +
    'Using placeholders for build process.'
  );
}

// Export with environment variables or build-time placeholders
export const supabaseUrl: string = supabaseUrlEnv || 'https://your-project.supabase.co';
export const supabaseAnonKey: string = supabaseAnonKeyEnv || 'your-anon-key-here';
