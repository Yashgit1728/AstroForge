@echo off
REM AstraForge Development Setup Script for Windows

echo 🚀 Setting up AstraForge development environment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker first.
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ✅ Created .env file. Please update it with your configuration.
)

REM Set up frontend
echo 📦 Setting up frontend dependencies...
cd frontend
if not exist node_modules (
    npm install
)
cd ..

REM Set up backend
echo 🐍 Setting up backend dependencies...
cd backend
if not exist venv (
    python -m venv venv
)

REM Activate virtual environment and install dependencies
call venv\Scripts\activate
pip install -r requirements-dev.txt
cd ..

echo 🐳 Starting Docker services...
docker-compose up -d postgres

REM Wait for PostgreSQL to be ready
echo ⏳ Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak >nul

REM Run database migrations
echo 🗄️ Running database migrations...
cd backend
call venv\Scripts\activate
alembic upgrade head
cd ..

echo ✅ Development environment setup complete!
echo.
echo 🎯 Next steps:
echo 1. Update .env file with your API keys
echo 2. Run 'docker-compose up' to start all services
echo 3. Frontend: http://localhost:5173
echo 4. Backend API: http://localhost:8000
echo 5. API Docs: http://localhost:8000/docs