# Setup Verification Script for Multilingual Mandi
Write-Host "=== Multilingual Mandi Setup Verification ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
}

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
}

# Check npm
Write-Host "Checking npm..." -ForegroundColor Yellow
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if ($npmCmd) {
    $npmVersion = npm --version 2>&1
    Write-Host "✓ npm $npmVersion" -ForegroundColor Green
} else {
    Write-Host "✗ npm not found" -ForegroundColor Red
}

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
    $dockerVersion = docker --version 2>&1
    Write-Host "✓ $dockerVersion" -ForegroundColor Green
    
    # Check if Docker is running
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker is running" -ForegroundColor Green
    } else {
        Write-Host "⚠ Docker is installed but not running. Please start Docker Desktop" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ Docker not found. Please install Docker Desktop" -ForegroundColor Red
    Write-Host "  Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Project Structure ===" -ForegroundColor Cyan

# Check backend structure
if (Test-Path "backend/app/main.py") {
    Write-Host "✓ Backend structure created" -ForegroundColor Green
} else {
    Write-Host "✗ Backend structure missing" -ForegroundColor Red
}

# Check frontend structure
if (Test-Path "frontend/package.json") {
    Write-Host "✓ Frontend structure created" -ForegroundColor Green
} else {
    Write-Host "✗ Frontend structure missing" -ForegroundColor Red
}

# Check Docker Compose
if (Test-Path "docker-compose.yml") {
    Write-Host "✓ Docker Compose configuration created" -ForegroundColor Green
} else {
    Write-Host "✗ Docker Compose configuration missing" -ForegroundColor Red
}

# Check environment files
if (Test-Path "backend/.env") {
    Write-Host "✓ Backend .env file created" -ForegroundColor Green
} else {
    Write-Host "⚠ Backend .env file missing (copy from .env.example)" -ForegroundColor Yellow
}

if (Test-Path "frontend/.env") {
    Write-Host "✓ Frontend .env file created" -ForegroundColor Green
} else {
    Write-Host "⚠ Frontend .env file missing (copy from .env.example)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Install Docker Desktop if not already installed" -ForegroundColor White
Write-Host "2. Start Docker Desktop" -ForegroundColor White
Write-Host "3. Run: docker compose up -d" -ForegroundColor White
Write-Host "4. Setup backend: cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor White
Write-Host "5. Run migrations: alembic upgrade head" -ForegroundColor White
Write-Host "6. Setup frontend: cd frontend && npm install" -ForegroundColor White
Write-Host "7. Start backend: python -m app.main" -ForegroundColor White
Write-Host "8. Start frontend: npm run dev" -ForegroundColor White
Write-Host ""
