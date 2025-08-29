# ✅ FIXED: Duplicate Key Constraint Error

## 🚨 **Issue Identified**

**Error**: `duplicate key value violates unique constraint "unique_active_session"`
**Cause**: Trying to create multiple active connect profiles for the same session

## 🔍 **Root Cause**

The database has a unique constraint:
```sql
CONSTRAINT unique_active_session UNIQUE (session_id, status)
```

This prevents having multiple active profiles for the same session, but the backend was trying to create a new profile every time without checking if one already exists.

---

## ✅ **Fix Applied**

### **Smart Profile Management**
**Before:**
```python
# Always tried to create new profile
response = get_supabase_client().table('kswifi_connect_profiles').insert(profile_record).execute()
# ❌ Failed if profile already existed
```

**After:**
```python
# Check if active profile exists first
existing_response = get_supabase_client().table('kswifi_connect_profiles')\
    .select('*')\
    .eq('session_id', session_id)\
    .eq('status', 'active')\
    .execute()

if existing_response.data:
    # ✅ Reuse existing profile
    stored_profile = existing_response.data[0]
    vpn_config = stored_profile['vpn_config']
    logger.info(f"🔍 Reusing existing connect profile: {stored_profile['id']}")
else:
    # ✅ Create new profile only if none exists
    response = get_supabase_client().table('kswifi_connect_profiles').insert(profile_record).execute()
    stored_profile = response.data[0]
    logger.info(f"🔍 Created new connect profile: {stored_profile['id']}")
```

---

## 🎯 **How It Works Now**

### **First Time User Generates Connect Code:**
1. ✅ Checks for existing active profile → None found
2. ✅ Creates new profile with VPN config
3. ✅ Returns QR code with new profile

### **User Generates Connect Code Again (Same Session):**
1. ✅ Checks for existing active profile → Found existing one
2. ✅ Reuses existing profile and VPN config
3. ✅ Returns QR code with same profile (no duplicate)

### **Benefits:**
- ✅ **No duplicate key errors**
- ✅ **Consistent VPN configuration** for same session
- ✅ **Database integrity maintained**
- ✅ **User gets same QR code** for same session

---

## 🧪 **Expected Behavior**

### **Logs You'll See:**
**First Generation:**
```
🔍 CONNECT: Generating profile for session 8e0c8ade-885f-457f-97e0
🔍 Created new connect profile: abc123def456
✅ Connect Code generated successfully
```

**Subsequent Generations:**
```
🔍 CONNECT: Generating profile for session 8e0c8ade-885f-457f-97e0
🔍 Reusing existing connect profile: abc123def456
✅ Connect Code generated successfully
```

---

## 🎉 **Status: FIXED**

**The duplicate key constraint error is resolved!**

**Users can now:**
- ✅ Generate Connect Codes multiple times for the same session
- ✅ Get consistent VPN profiles
- ✅ No more database constraint errors
- ✅ Reliable QR code generation

**Try generating a Connect Code now - it should work perfectly!** 🚀