@echo off
echo === Multilingual Mandi Setup Verification ===
echo.

echo Checking Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python --version
    echo [OK] Python found
) else (
    echo [ERROR] Python not found. Please install Python 3.11+
)
echo.

echo Checking Node.js...
node --version >nul 2>&1
if %errorlevel% equ 0 (
    node --version
    echo [OK] Node.js found
) else (
    echo [ERROR] Node.js not found. Please install Node.js 18+
)
echo.

echo Checking npm...
npm --version >nul 2>&1
if %errorlevel% equ 0 (
    npm --version
    echo [OK] npm found
) else (
    echo [ERROR] npm not found
)
echo.

echo Checking Docker...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    docker --version
    echo [OK] Docker found
    docker info >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Docker is running
    ) else (
        echo [WARNING] Docker is installed but not running. Please start Docker Desktop
    )
) else (
    echo [ERROR] Docker not found. Please install Docker Desktop
    echo Download from: https://www.docker.com/products/docker-desktop
)
echo.

echo === Project Structure ===
if exist "backend\app\main.py" (
    echo [OK] Backend structure created
) else (
    echo [ERROR] Backend structure missing
)

if exist "frontend\package.json" (
    echo [OK] Frontend structure created
) else (
    echo [ERROR] Frontend structure missing
)

if exist "docker-compose.yml" (
    echo [OK] Docker Compose configuration created
) else (
    echo [ERROR] Docker Compose configuration missing
)

if exist "backend\.env" (
    echo [OK] Backend .env file created
) else (
    echo [WARNING] Backend .env file missing
)

if exist "frontend\.env" (
    echo [OK] Frontend .env file created
) else (
    echo [WARNING] Frontend .env file missing
)

echo.
echo === Next Steps ===
echo 1. Install Docker Desktop if not already installed
echo 2. Start Docker Desktop
echo 3. Run: docker compose up -d
echo 4. Setup backend: cd backend ^&^& python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
echo 5. Run migrations: alembic upgrade head
echo 6. Setup frontend: cd frontend ^&^& npm install
echo 7. Start backend: python -m app.main
echo 8. Start frontend: npm run dev
echo.
pause
