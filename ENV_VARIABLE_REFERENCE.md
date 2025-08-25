# 🔧 **Environment Variable Name Reference**

## ✅ **EXACT Names Expected by Backend**

Your KSWiFi backend expects these **EXACT** environment variable names:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ...your-service-role-key
SUPABASE_ANON_KEY=eyJ...your-anon-key  
DATABASE_URL=postgresql://postgres:password@db.project.supabase.co:5432/postgres?sslmode=require&pgbouncer=true
SECRET_KEY=your-32-char-secret-key
```

## 🚨 **Common Name Mismatches That Cause "Network Unreachable"**

### ❌ **Wrong Names** → ✅ **Correct Names**

| ❌ You might have | ✅ Backend expects |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `SUPABASE_URL` |
| `SUPABASE_SERVICE_ROLE_KEY` | `SUPABASE_KEY` |
| `SUPABASE_SERVICE_KEY` | `SUPABASE_KEY` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `SUPABASE_ANON_KEY` |
| `DB_URL` | `DATABASE_URL` |
| `POSTGRES_URL` | `DATABASE_URL` |
| `JWT_SECRET` | `SECRET_KEY` |
| `APP_SECRET` | `SECRET_KEY` |

## 🛠 **Quick Fix for Render**

1. **Check your Render environment variables**
2. **Rename any mismatched variables** to the exact names above
3. **Redeploy** your service

## 🔍 **How to Verify in Render**

1. Go to your Render service dashboard
2. Click "Environment" tab
3. Look for these **exact** variable names:
   - ✅ `SUPABASE_URL` (not NEXT_PUBLIC_SUPABASE_URL)
   - ✅ `SUPABASE_KEY` (not SUPABASE_SERVICE_ROLE_KEY) 
   - ✅ `SUPABASE_ANON_KEY` (not NEXT_PUBLIC_SUPABASE_ANON_KEY)
   - ✅ `DATABASE_URL` (not DB_URL or POSTGRES_URL)
   - ✅ `SECRET_KEY` (not JWT_SECRET)

## 💡 **Why This Causes "Network Unreachable"**

When the backend can't find `DATABASE_URL`, it tries to connect to `undefined`, which causes:
```
[Errno 101] Network is unreachable
```

The network is fine - the app just doesn't know **where** to connect!

## 🎯 **Most Likely Culprit**

Based on the codebase, the most common mismatch is:
- You have: `NEXT_PUBLIC_SUPABASE_ANON_KEY` 
- Backend needs: `SUPABASE_ANON_KEY`

The `NEXT_PUBLIC_` prefix is for frontend variables, but the backend needs the plain names.