#!/bin/bash

# AstraForge Development Setup Script

set -e

echo "🚀 Setting up AstraForge development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please update it with your configuration."
fi

# Set up frontend
echo "📦 Setting up frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# Set up backend
echo "🐍 Setting up backend dependencies..."
cd backend
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
pip install -r requirements-dev.txt
cd ..

echo "🐳 Starting Docker services..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate
alembic upgrade head
cd ..

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Run 'docker-compose up' to start all services"
echo "3. Frontend: http://localhost:5173"
echo "4. Backend API: http://localhost:8000"
echo "5. API Docs: http://localhost:8000/docs"