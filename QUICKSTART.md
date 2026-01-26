# Multilingual Mandi - Quick Start Guide

## ✅ Infrastructure is Running!

Your Docker services are up and running:
- ✅ PostgreSQL 15 (port 5432) - Healthy
- ✅ Redis 7 (port 6379) - Healthy

## Next Steps

### 1. Setup Backend (Python/FastAPI)

Open a new terminal and run:

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Database Migrations

With the virtual environment activated:

```cmd
alembic upgrade head
```

This will create all database tables (users, conversations, messages, transactions).

### 3. Start Backend Server

```cmd
python -m app.main
```

The backend will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 4. Setup Frontend (React/TypeScript)

Open another terminal and run:

```cmd
cd frontend
npm install
```

### 5. Start Frontend Development Server

```cmd
npm run dev
```

The frontend will be available at: http://localhost:5173

## Verification

Once both servers are running, verify:

1. **Backend Health**: Open http://localhost:8000/health
   - Should return: `{"status": "healthy"}`

2. **API Documentation**: Open http://localhost:8000/docs
   - Interactive Swagger UI for testing APIs

3. **Frontend**: Open http://localhost:5173
   - Should show "Multilingual Mandi" welcome page

## Managing Docker Services

### View running containers:
```cmd
docker compose ps
```

### View logs:
```cmd
docker compose logs -f
```

### Stop services:
```cmd
docker compose down
```

### Restart services:
```cmd
docker compose restart
```

## Troubleshooting

### Backend Issues

**Problem**: Module not found errors
- **Solution**: Ensure virtual environment is activated and dependencies are installed

**Problem**: Database connection failed
- **Solution**: Ensure Docker containers are running (`docker compose ps`)

### Frontend Issues

**Problem**: npm install fails
- **Solution**: Clear npm cache (`npm cache clean --force`) and try again

**Problem**: Port 5173 already in use
- **Solution**: Stop other Vite instances or change port in vite.config.ts

### Docker Issues

**Problem**: Port already in use
- **Solution**: Stop other PostgreSQL/Redis instances or change ports in docker-compose.yml

## What's Next?

Now that your environment is set up, you can start implementing features:

1. Review the spec: `.kiro/specs/multilingual-mandi/`
2. Check the task list: `.kiro/specs/multilingual-mandi/tasks.md`
3. Next task: **Task 2 - Implement Demo Price Data Provider**

## Project Structure

```
multilingual-mandi/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── core/        # Configuration & database
│   │   ├── models/      # Database models
│   │   └── main.py      # FastAPI app
│   ├── alembic/         # Database migrations
│   └── requirements.txt
├── frontend/            # React TypeScript PWA
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yml   # PostgreSQL & Redis
```

## Useful Commands

### Backend
```cmd
# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Start server
python -m app.main
```

### Frontend
```cmd
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker
```cmd
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Restart services
docker compose restart
```

## Support

For detailed setup instructions, see [SETUP.md](SETUP.md)

For project status and accomplishments, see [PROJECT_STATUS.md](PROJECT_STATUS.md)
