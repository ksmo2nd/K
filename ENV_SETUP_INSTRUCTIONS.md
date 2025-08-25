# 🔧 Environment Variables Setup

## 🚨 **IMPORTANT: Set These in Your Deployment Platforms**

### **Backend (Render.com)**
Set these environment variables in your Render service:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-service-role-key
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-anon-key

# Database (From Supabase Settings → Database)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.your-project-id.supabase.co:5432/postgres

# Security (Generate with: openssl rand -hex 32)
SECRET_KEY=your-32-character-secret-key-here
```

### **Frontend (Vercel)**
Set these environment variables in your Vercel project:

```bash
# Supabase Public Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-anon-key

# Backend API URL (Your Render backend URL)
NEXT_PUBLIC_BACKEND_URL=https://your-backend-service.onrender.com
```

## 📋 **How to Get These Values**

### **Supabase Values:**
1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to Settings → API
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** → `SUPABASE_ANON_KEY`
   - **service_role** → `SUPABASE_KEY`

### **Database URL:**
1. In Supabase: Settings → Database
2. Copy the **Connection string**
3. Replace `[YOUR-PASSWORD]` with your actual database password

### **Secret Key:**
Run this command to generate:
```bash
openssl rand -hex 32
```

## ✅ **Verification**

After setting environment variables:

1. **Backend**: Deploy and check logs for "Starting KSWiFi Backend Service"
2. **Frontend**: Deploy and check if API calls work
3. **Database**: Test with a simple API endpoint

## 🚫 **What We Removed**

- ❌ `.env.backup` (old placeholder file)
- ❌ `.env.template` (duplicate of .env.example)
- ❌ `backend/.env` (had placeholder values)
- ❌ `frontend/.env` (had localhost values)

## ✅ **What Remains**

- ✅ `.env.example` (template for reference)
- ✅ Environment variables should be set in deployment platforms only