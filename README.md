# KSWiFi App

## Project Overview
A modern mobile-first application for managing WiFi data packs and eSIM services, built with Next.js frontend, FastAPI backend, and Supabase for database & auth.

## Quick Start

1. **Setup Environment**
   ```bash
   # Copy environment file
   cp .env.example .env.local
   # Add your Supabase project URL and anon key
   ```

2. **Install Dependencies**
   ```bash
   # Install frontend dependencies
   npm install
   
   # Install backend dependencies
   cd backend && pip install -r requirements.txt
   ```

3. **Start Development Servers**
   ```bash
   # Start both frontend and backend
   npm run dev
   
   # Or start individually:
   npm run frontend:dev  # Frontend only
   npm run backend:dev   # Backend only
   ```

4. **Mobile Development**
   ```bash
   # iOS
   npm run mobile:ios

   # Android
   npm run mobile:android
   ```

## Features

- User authentication via Supabase
- WiFi data pack management
- eSIM service integration
- Real-time data usage monitoring
- Cross-platform mobile support (iOS & Android)

## Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Supabase** - Database, Auth, and Real-time features
- **PostgreSQL** - Primary database (via Supabase)
- **Redis** - Background task queue and caching
- **Async SQLAlchemy** - Database ORM
- **Celery + APScheduler** - Background task processing

### Frontend
- **Next.js 15** - React framework with App Router
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Modern component library
- **Supabase JS Client** - Real-time auth and data

### Mobile
- **Capacitor** - Cross-platform mobile runtime
- **Native iOS/Android** - Platform-specific builds

### Infrastructure
- **Docker** - Containerization
- **Row Level Security (RLS)** - Database security
- **Structured Logging** - Observability

## Project Structure

```
.
├── frontend/            # Next.js web application
│   ├── app/            # Next.js App Router pages
│   ├── components/     # React components
│   ├── lib/           # API client and utilities
│   └── hooks/         # Custom React hooks
├── backend/            # FastAPI backend service
│   ├── app/           # Application code
│   │   ├── core/      # Configuration and database
│   │   ├── services/  # Business logic services
│   │   ├── routes/    # API endpoints
│   │   └── models/    # Data models and enums
│   └── requirements.txt
├── android/            # Android platform files
├── ios/               # iOS platform files
├── supabase/          # Database migrations and config
└── docker-compose.yml # Development environment
```

## Development

### Prerequisites
- **Node.js 18+** - Frontend development
- **Python 3.12+** - Backend development
- **Supabase account** - Database and auth
- **Redis** (optional, for background tasks)
- **Xcode** (for iOS development)
- **Android Studio** (for Android development)
- **Docker** (optional, for containerized development)

### Environment Setup
1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Copy `.env.example` to `.env.local`
3. Add your Supabase project URL and anon key
4. Install dependencies: `npm install`

### Database Setup
```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Push database migrations
supabase db push
```

## Deployment

### Frontend (Vercel)
```bash
# Deploy to Vercel
vercel

# Or connect your GitHub repo to Vercel for auto-deployment
```

### Database
Database is automatically managed by Supabase. No separate deployment needed.

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Open a Pull Request

## Features

### Core Features
- 🔐 **User Authentication** - Secure auth via Supabase
- 📱 **Data Pack Management** - Purchase and manage data bundles
- 🌐 **eSIM Integration** - Real eSIM provider integration
- 📊 **Usage Monitoring** - Real-time data consumption tracking
- 🔔 **Smart Notifications** - Low balance and usage alerts
- 📱 **Mobile Apps** - Native iOS & Android support

### Advanced Features
- ⚡ **Background Monitoring** - Automatic data balance checks
- 🧮 **Dynamic Pricing** - Smart bundle calculation
- 📈 **Usage Analytics** - Detailed consumption insights
- 🔒 **Row Level Security** - Database-level user isolation
- 🔄 **Real-time Sync** - Live data updates
- 🎯 **Push Notifications** - Cross-platform alerts
- 📋 **QR Code Generation** - eSIM activation codes

## API Documentation

### Backend API
Once the backend server is running, visit:
- **OpenAPI/Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Supabase API
Database operations and real-time features are handled through Supabase:
- **Supabase Dashboard**: [Your Project Dashboard](https://supabase.com/dashboard)
- **Auto-generated API docs** available in your Supabase project

## Mobile App Building

### iOS
1. Open Xcode workspace in `ios/App`
2. Configure signing and provisioning profiles
3. Build and run on device or simulator

### Android
1. Open Android project in `android/`
2. Configure signing certificates
3. Build and run on device or emulator

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License.
