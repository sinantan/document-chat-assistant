# Document Chat Assistant

A document chat assistant that allows users to upload PDF documents and chat with them using AI.

## Features

- JWT Authentication (register/login)
- PDF document upload and processing
- AI-powered chat with documents using Gemini API
- Multi-database architecture (PostgreSQL + MongoDB GridFS + Redis)
- Containerized deployment with Docker

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Authentication**: JWT tokens
- **Databases**: PostgreSQL, MongoDB GridFS, Redis
- **AI**: Gemini API (OpenAI-compatible)
- **PDF Processing**: PyPDF2
- **Containerization**: Docker + docker-compose

## Architecture

The application follows a clean architecture pattern:

- **API Layer**: FastAPI endpoints for HTTP handling
- **Service Layer**: Business logic and orchestration
- **Repository Layer**: Data access abstraction
- **Models**: SQLAlchemy ORM models
- **Schemas**: Pydantic models for request/response validation


## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register a new user with email and password
- `POST /api/v1/auth/login` - Login user and get JWT access/refresh tokens
- `POST /api/v1/auth/refresh` - Refresh expired access token using refresh token
- `GET /api/v1/auth/me` - Get current authenticated user profile

### Documents
- `POST /api/v1/documents` - Upload PDF document for processing and chat
- `GET /api/v1/documents` - List all user's uploaded documents with pagination
- `GET /api/v1/documents/{document_id}` - Get specific document details and status
- `GET /api/v1/documents/{document_id}/chunks` - Get processed text chunks from document
- `DELETE /api/v1/documents/{document_id}` - Delete document and all related conversations

### Chat & Conversations  
- `POST /api/v1/messages` - Send chat message to start new or continue existing conversation
- `GET /api/v1/messages/conversations` - List all user's conversations with documents
- `GET /api/v1/messages/conversations/{conversation_id}` - Get specific conversation details
- `GET /api/v1/messages/conversations/{conversation_id}/messages` - Get conversation message history
- `DELETE /api/v1/messages/conversations/{conversation_id}` - Delete conversation and all messages

## Application Flow

1. **User Registration/Login** → Get JWT tokens for authentication
2. **Document Upload** → PDF is stored in MongoDB GridFS and parsed into text chunks
3. **Start Chat** → Send message with document_id to create new conversation
4. **Continue Chat** → Send messages with conversation_id to continue existing conversation
5. **AI Processing** → Gemini API processes document context + user message to generate responses
6. **Conversation Management** → View, list, and delete conversations as needed



## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Poetry (for dependency management)

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd document-chat-assistant
```

### 2. Configure Environment Variables

Edit `.env` file with your settings:

```bash
# Required: Add your Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Update other settings as needed
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
```

## Running the Project

### Option 1: Full Docker Setup (Recommended)

```bash
# Start all services (databases + application)
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

Application will be available at: http://localhost:8000

### Option 2: Local Development

```bash
# Install dependencies
make dev-install

# Start only database services
make docker-up-dev

# Run database migrations
make upgrade

# Start the application locally
make run
```

## API Documentation

Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc


## API Usage Examples

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

Response will include access token:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 3. Upload PDF Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/your/document.pdf"
```

### 4. List Documents

```bash
curl -X GET "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. Start Chat with Document

```bash
curl -X POST "http://localhost:8000/api/v1/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "document_uuid_here",
    "message": "What is this document about?"
  }'
```

### 6. Continue Existing Conversation

```bash
curl -X POST "http://localhost:8000/api/v1/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conversation_uuid_here",
    "message": "Tell me more about the main topics."
  }'
```

## Environment Variables

Key environment variables (see `.env` for complete list):

```bash
# Application
DEBUG=false
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=document_chat

# MongoDB
MONGO_HOST=localhost
MONGO_DB=document_chat

# Redis
REDIS_HOST=localhost
REDIS_PASSWORD=

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

# File Upload
MAX_FILE_SIZE_MB=50
```

## Development Commands

```bash
# Code formatting and linting
make fmt
make lint

# Testing
make test

# Database migrations
make migrate msg="Your migration message"
make upgrade
make downgrade

# Docker management
make docker-up          # Start all services
make docker-up-dev      # Start only databases
make docker-down        # Stop services
make docker-logs        # View logs
```

