# Overview

KSWiFi Backend Service is a FastAPI-based REST API for managing virtual eSIM data packs and cellular connectivity services. The application provides comprehensive user authentication, data pack management, eSIM provisioning with QR code generation, and administrative oversight capabilities. It's designed to handle the backend operations for a virtual mobile network operator (MVNO) or eSIM service provider.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Framework
- **FastAPI**: Modern Python web framework chosen for its automatic API documentation, type hints support, and high performance
- **SQLAlchemy ORM**: Database abstraction layer providing model definitions and query capabilities
- **Pydantic**: Data validation and serialization using Python type annotations

## Authentication & Security
- **JWT (JSON Web Tokens)**: Stateless authentication mechanism with configurable expiration
- **bcrypt**: Password hashing using industry-standard cryptographic functions
- **Role-based access control**: Admin privileges system for administrative operations
- **Rate limiting**: In-memory request throttling to prevent API abuse

## Data Storage
- **Flexible database support**: Configured to work with both SQLite (development) and PostgreSQL (production)
- **Connection pooling**: Optimized database connections with health checks and recycling
- **Schema management**: Automated table creation and migration support

## Core Domain Models
- **User management**: Account creation, authentication, and profile management
- **Data pack system**: Virtual data allowances with usage tracking and expiration
- **eSIM provisioning**: Virtual SIM card generation with activation codes and QR codes
- **Usage logging**: Detailed tracking of data consumption and user activities
- **Administrative oversight**: System monitoring and user management capabilities

## API Design Patterns
- **RESTful endpoints**: Standard HTTP methods and status codes
- **Dependency injection**: FastAPI's dependency system for database sessions and authentication
- **Response models**: Structured JSON responses with data validation
- **Error handling**: Consistent HTTP exception handling with descriptive messages

## Configuration Management
- **Environment-based settings**: Centralized configuration using environment variables
- **Development vs production**: Debug modes and database selection based on environment
- **Security configuration**: Configurable JWT settings, CORS policies, and rate limits

# External Dependencies

## Core Framework Dependencies
- **FastAPI**: Web framework and API development
- **uvicorn**: ASGI server for running the FastAPI application
- **SQLAlchemy**: Database ORM and connection management
- **Pydantic**: Data validation and settings management

## Security Libraries
- **PyJWT**: JWT token creation and verification
- **passlib[bcrypt]**: Password hashing and verification
- **python-multipart**: Form data parsing for authentication endpoints

## eSIM & QR Code Generation
- **qrcode**: QR code image generation for eSIM activation
- **Pillow**: Image processing library for QR code rendering

## Development & Logging
- **python-dotenv**: Environment variable loading from .env files
- **Built-in logging**: Python's logging module with file rotation

## CORS & Middleware
- **FastAPI CORS middleware**: Cross-origin request handling for web frontends
- **Custom rate limiting**: In-memory request throttling implementation

## Database Drivers
- **SQLite**: Built-in Python database support for development
- **PostgreSQL drivers**: Production database connectivity (psycopg2 or asyncpg when configured)

The architecture emphasizes modularity, security, and scalability while maintaining simplicity for development and deployment across different environments.