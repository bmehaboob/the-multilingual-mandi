# Multilingual Mandi

Voice-first Progressive Web Application for multilingual agricultural trade in India.

## Project Structure

```
multilingual-mandi/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── core/        # Core configuration and database
│   │   ├── models/      # SQLAlchemy models
│   │   └── main.py      # FastAPI application
│   ├── alembic/         # Database migrations
│   ├── requirements.txt
│   └── .env.example
├── frontend/            # React TypeScript PWA
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
└── docker-compose.yml   # Local development services
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker Desktop (includes Docker Compose)
  - Windows/Mac: Download from https://www.docker.com/products/docker-desktop
  - Linux: Follow instructions at https://docs.docker.com/engine/install/

## Quick Setup Verification

Run the setup verification script to check your environment:

**Windows (Command Prompt):**
```cmd
setup-verify.cmd
```

**Windows (PowerShell):**
```powershell
.\setup-verify.ps1
```

This will verify all prerequisites are installed and the project structure is correct.

For detailed setup instructions, see [SETUP.md](SETUP.md).

## Setup Instructions

### 1. Start Infrastructure Services

Start PostgreSQL and Redis using Docker Compose:

```bash
docker-compose up -d
```

Verify services are running:
```bash
docker-compose ps
```

### 2. Backend Setup

Create and activate Python virtual environment:

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` file from example:

```bash
copy .env.example .env
```

Run database migrations:

```bash
alembic upgrade head
```

Start the backend server:

```bash
python -m app.main
```

Backend will be available at: http://localhost:8000

API documentation: http://localhost:8000/docs

### 3. Frontend Setup

Install dependencies:

```bash
cd frontend
npm install
```

Create `.env` file from example:

```bash
copy .env.example .env
```

Start the development server:

```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

### 4. Verify Setup

- Backend health check: http://localhost:8000/health
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL 15+
- **Cache**: Redis
- **ORM**: SQLAlchemy
- **Migrations**: Alembic

### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite
- **PWA**: Workbox (via vite-plugin-pwa)
- **State Management**: Zustand

### Infrastructure
- **Containerization**: Docker Compose
- **Database**: PostgreSQL 15
- **Cache**: Redis 7

## Development

### Backend Commands

```bash
# Run server with auto-reload
python -m app.main

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Frontend Commands

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

## Next Steps

Refer to `.kiro/specs/multilingual-mandi/tasks.md` for the implementation roadmap.
