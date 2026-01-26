# Multilingual Mandi - Setup Guide

This guide will help you set up the Multilingual Mandi development environment.

## Prerequisites Checklist

Before starting, ensure you have:

- ✅ Python 3.11 or higher
- ✅ Node.js 18 or higher
- ✅ Docker Desktop (includes Docker Compose)
- ✅ Git (for version control)

### Installing Prerequisites

#### Python
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

#### Node.js
- Download from: https://nodejs.org/
- Choose the LTS version

#### Docker Desktop
- Windows/Mac: https://www.docker.com/products/docker-desktop
- Linux: https://docs.docker.com/engine/install/

## Verification

Run the setup verification script to check your environment:

**Windows (Command Prompt):**
```cmd
setup-verify.cmd
```

**Windows (PowerShell):**
```powershell
.\setup-verify.ps1
```

## Step-by-Step Setup

### 1. Start Infrastructure Services

Start PostgreSQL and Redis using Docker Compose:

```bash
docker compose up -d
```

Verify services are running:
```bash
docker compose ps
```

You should see:
- `multilingual-mandi-postgres` (PostgreSQL 15)
- `multilingual-mandi-redis` (Redis 7)

### 2. Backend Setup

#### Create Virtual Environment

Navigate to the backend directory:
```bash
cd backend
```

Create and activate a Python virtual environment:

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment

The `.env` file has already been created with default values. Review and modify if needed:

```bash
# View current configuration
type .env  # Windows
cat .env   # Linux/Mac
```

#### Run Database Migrations

Initialize the database schema:

```bash
alembic upgrade head
```

This will create all necessary tables (users, conversations, messages, transactions).

#### Start Backend Server

```bash
python -m app.main
```

The backend will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 3. Frontend Setup

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

#### Install Dependencies

```bash
npm install
```

This will install:
- React 18
- TypeScript
- Vite (build tool)
- Workbox (PWA support)
- Zustand (state management)

#### Configure Environment

The `.env` file has already been created. It points to the backend API:

```
VITE_API_URL=http://localhost:8000/api/v1
```

#### Start Development Server

```bash
npm run dev
```

The frontend will be available at: http://localhost:5173

## Verification

### Backend Verification

1. Open http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

2. Open http://localhost:8000/docs
   - Should show the interactive API documentation

3. Test database connection:
   ```bash
   # In backend directory with venv activated
   python -c "from app.core.database import engine; print('Database connected!' if engine.connect() else 'Failed')"
   ```

4. Test Redis connection:
   ```bash
   python -c "from app.core.redis_client import redis_client; print('Redis connected!' if redis_client.ping() else 'Failed')"
   ```

### Frontend Verification

1. Open http://localhost:5173
   - Should show "Multilingual Mandi" welcome page

2. Check browser console (F12)
   - Should see service worker registration (PWA)

3. Check network tab
   - Should show successful connection to backend

## Project Structure

```
multilingual-mandi/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py      # Environment configuration
│   │   │   ├── database.py    # Database connection
│   │   │   └── redis_client.py # Redis client
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── conversation.py
│   │   │   └── transaction.py
│   │   └── main.py            # FastAPI application
│   ├── alembic/               # Database migrations
│   │   ├── versions/          # Migration files
│   │   └── env.py
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   └── alembic.ini           # Alembic configuration
├── frontend/                  # React TypeScript PWA
│   ├── src/
│   │   ├── App.tsx           # Main application component
│   │   ├── main.tsx          # Entry point
│   │   └── index.css         # Global styles
│   ├── package.json          # Node dependencies
│   ├── vite.config.ts        # Vite configuration (includes PWA)
│   ├── tsconfig.json         # TypeScript configuration
│   └── .env                  # Environment variables
├── docker-compose.yml        # Docker services (PostgreSQL, Redis)
├── README.md                 # Project overview
└── SETUP.md                  # This file

```

## Common Issues and Solutions

### Docker Issues

**Problem:** Docker command not found
- **Solution:** Install Docker Desktop and ensure it's running

**Problem:** Port 5432 or 6379 already in use
- **Solution:** Stop other PostgreSQL/Redis instances or change ports in docker-compose.yml

### Backend Issues

**Problem:** Module not found errors
- **Solution:** Ensure virtual environment is activated and dependencies are installed

**Problem:** Database connection failed
- **Solution:** Ensure Docker containers are running (`docker compose ps`)

**Problem:** Alembic migration fails
- **Solution:** Check DATABASE_URL in .env file and ensure PostgreSQL is running

### Frontend Issues

**Problem:** npm install fails
- **Solution:** Clear npm cache (`npm cache clean --force`) and try again

**Problem:** Port 5173 already in use
- **Solution:** Change port in vite.config.ts or stop other Vite instances

## Development Workflow

### Daily Development

1. Start Docker services (if not running):
   ```bash
   docker compose up -d
   ```

2. Start backend (in backend directory with venv activated):
   ```bash
   python -m app.main
   ```

3. Start frontend (in frontend directory):
   ```bash
   npm run dev
   ```

### Creating Database Migrations

When you modify models:

```bash
cd backend
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

### Stopping Services

```bash
# Stop backend: Ctrl+C in terminal

# Stop frontend: Ctrl+C in terminal

# Stop Docker services:
docker compose down
```

## Next Steps

Now that your environment is set up, you can:

1. Review the requirements: `.kiro/specs/multilingual-mandi/requirements.md`
2. Review the design: `.kiro/specs/multilingual-mandi/design.md`
3. Start implementing tasks: `.kiro/specs/multilingual-mandi/tasks.md`

The next task is **Task 2: Implement Demo Price Data Provider**

## Support

For issues or questions:
- Check the main README.md
- Review the design document
- Check Docker logs: `docker compose logs`
- Check backend logs in the terminal
