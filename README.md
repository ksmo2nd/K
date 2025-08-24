# KSWiFi App

## Project Overview
Full-stack application for managing WiFi data packs and eSIM services.

## Quick Start

1. **Setup Environment**
   ```bash
   # Copy environment file
   cp .env.example .env.local
   ```

2. **Start Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

3. **Start Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Mobile Development**
   ```bash
   # iOS
   npm run ios

   # Android
   npm run android
   ```

## Features

- User authentication via Supabase
- WiFi data pack management
- eSIM service integration
- Real-time data usage monitoring
- Cross-platform mobile support (iOS & Android)

## Tech Stack

### Backend
- FastAPI
- Supabase (Database & Auth)
- Python 3.12+

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- shadcn/ui components

### Mobile
- Capacitor
- Native iOS/Android support

## Project Structure

```
.
├── backend/              # FastAPI server
├── frontend/            # Next.js web application
├── android/             # Android platform files
├── ios/                 # iOS platform files
├── supabase/           # Database migrations
└── docker-compose.yml  # Development environment
```

## Development

### Prerequisites
- Node.js 18+
- Python 3.12+
- Docker & Docker Compose
- Xcode (for iOS)
- Android Studio (for Android)

### Environment Setup
1. Configure Supabase credentials
2. Set up environment variables
3. Install dependencies for both frontend and backend

### Database Migrations
```bash
supabase db push
```

## Deployment

### Backend
```bash
docker-compose up backend
```

### Frontend
```bash
docker-compose up frontend
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Open a Pull Request

## License
This project is licensed under the MIT License.

- User aut## Project Structure

```
K/
├── frontend/           # Next.js Web Application
│   ├── app/           # Pages and routing
│   ├── components/    # React components
│   ├── lib/          # Frontend utilities
│   ├── public/       # Static assets
│   ├── styles/       # Global styles
│   └── hooks/        # React hooks
├── backend/           # FastAPI Backend
│   ├── app/          # Application code
│   │   ├── routes/   # API endpoints
│   │   ├── models/   # Database models
│   │   └── utils/    # Backend utilities
│   └── tests/        # Backend tests
├── android/          # Android application
├── ios/             # iOS application
├── supabase/        # Database migrations
└── docker-compose.yml # Container configuration
```authorization
- Data pack management
- eSIM provisioning and management
- Mobile app support (iOS & Android)
- Real-time data usage tracking
- QR code generation for eSIM activation

## Tech Stack

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- Supabase (Database & Authentication)
- JWT Authentication
- OpenAPI Documentation

### Frontend
- Next.js
- React
- Tailwind CSS
- shadcn/ui Components
- Supabase Client

### Mobile
- Capacitor
- iOS & Android Support

## Prerequisites

- Node.js 18+
- Python 3.11+
- Supabase Account
- (Optional) Xcode for iOS development
- (Optional) Android Studio for Android development

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/ksmo2nd/K.git
   cd K
   ```

2. **Install dependencies**
   ```bash
   # Install frontend dependencies
   npm install

   # Install backend dependencies
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   
   Create `.env.local` file:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   ```

   Create `.env.backend` file:
   ```env
   DATABASE_URL=your-database-url
   JWT_SECRET_KEY=your-secret-key
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

4. **Database Setup**
   
   Run the SQL migrations in your Supabase project:
   ```sql
   -- Run the contents of supabase/migrations/00000000000000_initial_schema.sql
   ```

5. **Start the Development Servers**

   Backend:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   Frontend:
   ```bash
   npm run dev
   ```

6. **Mobile Development**

   Build the web app:
   ```bash
   npm run build
   npx cap sync
   ```

   iOS:
   ```bash
   npx cap open ios
   ```

   Android:
   ```bash
   npx cap open android
   ```

## Project Structure

```
K/
├── app/                  # Next.js pages
├── components/           # React components
├── lib/                  # Shared utilities
├── public/              # Static assets
├── styles/              # Global styles
├── routes/              # Backend API routes
├── models.py            # Database models
├── database.py          # Database configuration
├── auth.py              # Authentication logic
├── main.py             # FastAPI application
└── supabase/           # Database migrations
```

## API Documentation

Once the backend server is running, visit:
- OpenAPI documentation: http://localhost:8000/docs
- ReDoc documentation: http://localhost:8000/redoc

## Mobile App Building

### iOS
1. Open Xcode workspace in `ios/App`
2. Configure signing
3. Build and run

### Android
1. Open Android project in `android/`
2. Configure signing
3. Build and run

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

[MIT License](LICENSE)
