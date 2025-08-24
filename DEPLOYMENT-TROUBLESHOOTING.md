# 🚀 KSWiFi Backend Deployment Troubleshooting

## ❌ Error: "Port scan timeout reached, no open ports detected"

This error occurs when deploying to services like **Railway**, **Render**, **Heroku**, etc. that expect your app to bind to a specific port.

## ✅ **SOLUTIONS:**

### 1. **For Railway/Render/Vercel:**
```bash
# Use the PORT environment variable provided by the service
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 2. **For Docker deployments:**
```dockerfile
# In your Dockerfile
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. **For Heroku:**
```bash
# Heroku provides PORT automatically
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 4. **Local development:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 **Deployment Service Configurations:**

### **Railway:**
```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "always"
```

### **Render:**
```yaml
# render.yaml
services:
  - type: web
    name: kswifi-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    healthCheckPath: "/health"
```

### **Vercel (serverless):**
```json
{
  "functions": {
    "backend/app/main.py": {
      "runtime": "@vercel/python"
    }
  },
  "routes": [
    { "src": "/api/(.*)", "dest": "/backend/app/main.py" }
  ]
}
```

## 🛠 **Environment Variables Required:**

Make sure these are set in your deployment service:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-public-key
DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres

# Security
SECRET_KEY=your-production-secret-key

# eSIM Provider (replace with real credentials)
ESIM_PROVIDER_API_URL=https://your-esim-provider.com/api
ESIM_PROVIDER_API_KEY=your-api-key
ESIM_PROVIDER_USERNAME=your-username
ESIM_PROVIDER_PASSWORD=your-password

# Optional: Custom port (usually provided by deployment service)
PORT=8000
```

## 🔍 **Debugging Steps:**

1. **Check if your service is binding to the correct port:**
   ```bash
   curl http://localhost:$PORT/health
   ```

2. **Verify environment variables are loaded:**
   ```bash
   echo $PORT
   echo $SUPABASE_URL
   ```

3. **Test local startup:**
   ```bash
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. **Check health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

## 📋 **Common Issues:**

- **Missing PORT variable**: Some services require you to use their provided PORT
- **Wrong host binding**: Use `0.0.0.0` not `localhost` or `127.0.0.1`
- **Missing health check**: Add `/health` endpoint for monitoring
- **Environment variables**: Ensure all required vars are set in deployment

## 🎯 **Quick Fix:**

If you're getting the port scan error, try this startup command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

This uses the deployment service's PORT if available, or defaults to 8000.