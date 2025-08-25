#!/usr/bin/env python3
"""
Diagnose environment variable name mismatches
"""
import os

def diagnose_env_variables():
    print("🔍 ENVIRONMENT VARIABLE MISMATCH DIAGNOSIS")
    print("=" * 60)
    
    # Expected variables by the backend
    expected_backend_vars = {
        'SUPABASE_URL': 'Backend expects this exact name',
        'SUPABASE_KEY': 'Backend expects this exact name (service role key)', 
        'SUPABASE_ANON_KEY': 'Backend expects this exact name',
        'DATABASE_URL': 'Backend expects this exact name',
        'SECRET_KEY': 'Backend expects this exact name'
    }
    
    # Common alternative names people might use
    alternative_names = {
        'SUPABASE_URL': ['NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_PROJECT_URL'],
        'SUPABASE_KEY': ['SUPABASE_SERVICE_ROLE_KEY', 'SUPABASE_SERVICE_KEY', 'NEXT_PUBLIC_SUPABASE_SERVICE_KEY'],
        'SUPABASE_ANON_KEY': ['NEXT_PUBLIC_SUPABASE_ANON_KEY', 'SUPABASE_ANON', 'SUPABASE_PUBLIC_KEY'],
        'DATABASE_URL': ['DB_URL', 'POSTGRES_URL', 'POSTGRESQL_URL', 'SUPABASE_DB_URL'],
        'SECRET_KEY': ['JWT_SECRET', 'JWT_SECRET_KEY', 'APP_SECRET']
    }
    
    print("\n📋 CHECKING EXPECTED VARIABLES:")
    missing_vars = []
    found_vars = []
    
    for var, description in expected_backend_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: SET ({len(value)} characters)")
            found_vars.append(var)
        else:
            print(f"❌ {var}: NOT SET - {description}")
            missing_vars.append(var)
    
    print(f"\n📋 CHECKING FOR ALTERNATIVE NAMES:")
    potential_mismatches = []
    
    for expected_var in missing_vars:
        print(f"\n🔍 Looking for alternatives to {expected_var}:")
        found_alternatives = []
        
        for alt_name in alternative_names.get(expected_var, []):
            alt_value = os.getenv(alt_name)
            if alt_value:
                print(f"   ✅ Found {alt_name}: SET ({len(alt_value)} characters)")
                found_alternatives.append(alt_name)
                potential_mismatches.append((expected_var, alt_name))
            else:
                print(f"   ⚪ {alt_name}: not set")
        
        if not found_alternatives:
            print(f"   ❌ No alternatives found for {expected_var}")
    
    print(f"\n📋 ALL ENVIRONMENT VARIABLES SET:")
    all_env_vars = dict(os.environ)
    supabase_related = {k: v for k, v in all_env_vars.items() 
                       if any(keyword in k.upper() for keyword in 
                             ['SUPABASE', 'DATABASE', 'DB_', 'POSTGRES', 'SECRET', 'JWT'])}
    
    if supabase_related:
        print("Found these potentially relevant environment variables:")
        for var, value in supabase_related.items():
            print(f"   {var}: {value[:30]}{'...' if len(value) > 30 else ''}")
    else:
        print("No relevant environment variables found!")
    
    print(f"\n" + "=" * 60)
    
    if potential_mismatches:
        print("🚨 POTENTIAL MISMATCHES DETECTED:")
        for expected, found in potential_mismatches:
            print(f"   Expected: {expected}")
            print(f"   You have: {found}")
            print(f"   → Rename {found} to {expected}")
        return False
    elif missing_vars:
        print(f"❌ MISSING VARIABLES: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ ALL EXPECTED VARIABLES ARE SET CORRECTLY!")
        return True

if __name__ == "__main__":
    success = diagnose_env_variables()
    exit(0 if success else 1)