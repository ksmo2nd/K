# KSWiFi App

## Project Overview
A modern mobile-first application for managing WiFi data packs and eSIM services, built with Next.js and powered by Supabase.

## Quick Start

1. **Setup Environment**
   ```bash
   # Copy environment file
   cp .env.example .env.local
   # Add your Supabase project URL and anon key
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Start Development Server**
   ```bash
   npm run dev
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
- Supabase (Database, Auth, Real-time & API)
- PostgreSQL (via Supabase)
- Row Level Security (RLS)

### Frontend
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Supabase JS Client

### Mobile
- Capacitor
- Native iOS/Android support

## Project Structure

```
.
├── frontend/            # Next.js web application
│   ├── app/            # Next.js App Router pages
│   ├── components/     # React components
│   ├── lib/           # Utility functions and API client
│   └── hooks/         # Custom React hooks
├── android/            # Android platform files
├── ios/               # iOS platform files
├── supabase/          # Database migrations and config
└── docker-compose.yml # Optional containerized development
```

## Development

### Prerequisites
- Node.js 18+
- Supabase account
- Xcode (for iOS development)
- Android Studio (for Android development)

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

- User authentication via Supabase Auth
- WiFi data pack management
- eSIM provisioning and management
- Mobile app support (iOS & Android)
- Real-time data usage tracking
- QR code generation for eSIM activation
- Row Level Security (RLS) for data protection

## API Documentation

The app uses Supabase's auto-generated API. You can view the API documentation in your Supabase dashboard under API section.

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
