# 🔧 Render Backend Environment Variables Setup

## 📋 **Required Environment Variables**

### **1. Go to Render Dashboard**
1. Open [render.com](https://render.com)
2. Go to your backend service
3. Click **"Environment"** tab
4. Add these variables:

---

## 🔑 **Environment Variables to Set**

### **🗄️ SUPABASE CONFIGURATION**
```
SUPABASE_URL = https://your-project-id.supabase.co
SUPABASE_KEY = eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
SUPABASE_ANON_KEY = eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Where to get these:**
1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **service_role secret** → `SUPABASE_KEY` 
   - **anon public** → `SUPABASE_ANON_KEY`

### **🗃️ DATABASE CONFIGURATION**
```
DATABASE_URL = postgresql://postgres:your-password@db.your-project-id.supabase.co:5432/postgres
```

**Where to get this:**
1. In Supabase dashboard → **Settings** → **Database**
2. Copy the **Connection string** 
3. Replace `[YOUR-PASSWORD]` with your database password

### **🔐 SECURITY**
```
SECRET_KEY = your-32-character-secret-key-here
```

**How to generate:**
```bash
# Run this command to generate a secure key:
openssl rand -hex 32
```

### **🌐 CORS (Optional - for custom domains)**
```
ALLOWED_ORIGINS = ["https://your-frontend-domain.vercel.app","https://your-custom-domain.com"]
```

---

## 📝 **Complete Setup Checklist**

### **✅ Step 1: Supabase Setup**
- [ ] Created Supabase project
- [ ] Got SUPABASE_URL from API settings
- [ ] Got SUPABASE_KEY (service_role) from API settings  
- [ ] Got SUPABASE_ANON_KEY (anon) from API settings
- [ ] Got DATABASE_URL from Database settings

### **✅ Step 2: Generate Secret**
- [ ] Generated SECRET_KEY using `openssl rand -hex 32`

### **✅ Step 3: Render Configuration**
- [ ] Added all 5 required variables in Render
- [ ] Clicked **"Save Changes"**
- [ ] Triggered new deployment

### **✅ Step 4: Verification**
After deployment, check:
- [ ] `https://your-app.onrender.com/health` returns success
- [ ] `https://your-app.onrender.com/debug` shows all vars as "SET"

---

## 🚨 **Common Mistakes to Avoid**

### **❌ Wrong DATABASE_URL Format**
```bash
# WRONG:
DATABASE_URL = postgres://...

# CORRECT:
DATABASE_URL = postgresql://...
```

### **❌ Using Development URLs**
```bash
# WRONG:
SUPABASE_URL = https://localhost:54321

# CORRECT:  
SUPABASE_URL = https://abcdefgh.supabase.co
```

### **❌ Weak Secret Key**
```bash
# WRONG:
SECRET_KEY = mysecret

# CORRECT:
SECRET_KEY = a1b2c3d4e5f6...32-characters-long
```

---

## 🎯 **Expected Result**

After setting up correctly, your `/debug` endpoint should show:
```json
{
  "status": "debug_info_collected",
  "environment_variables": {
    "SUPABASE_URL": "SET",
    "SUPABASE_KEY": "SET", 
    "SUPABASE_ANON_KEY": "SET",
    "DATABASE_URL": "SET",
    "SECRET_KEY": "SET"
  },
  "configuration": {
    "supabase_url_configured": true,
    "database_url_configured": true,
    "secret_key_configured": true
  }
}
```

## 🔄 **After Adding Variables**

1. **Save changes** in Render
2. **Wait for automatic redeploy** (2-3 minutes)
3. **Check logs** for startup messages with ✅ emojis
4. **Test endpoints**: `/health`, `/debug`, `/health/database`

Your backend will be ready! 🚀