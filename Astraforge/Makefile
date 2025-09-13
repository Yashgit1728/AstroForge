# AstraForge Development Makefile

.PHONY: help setup dev build test lint clean

# Default target
help:
	@echo "AstraForge Development Commands:"
	@echo "  setup     - Set up development environment"
	@echo "  dev       - Start development servers"
	@echo "  build     - Build frontend and backend"
	@echo "  test      - Run all tests"
	@echo "  lint      - Run linting and formatting"
	@echo "  clean     - Clean build artifacts"

# Set up development environment
setup:
	@echo "🚀 Setting up development environment..."
	@if [ -f scripts/dev-setup.sh ]; then \
		chmod +x scripts/dev-setup.sh && ./scripts/dev-setup.sh; \
	else \
		echo "❌ Setup script not found"; \
	fi

# Start development servers
dev:
	@echo "🚀 Starting development servers..."
	docker-compose up

# Build applications
build:
	@echo "🏗️ Building applications..."
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "Building backend..."
	cd backend && python -m build

# Run tests
test:
	@echo "🧪 Running tests..."
	@echo "Testing frontend..."
	cd frontend && npm run test
	@echo "Testing backend..."
	cd backend && python -m pytest

# Run linting and formatting
lint:
	@echo "🔍 Running linting and formatting..."
	@echo "Linting frontend..."
	cd frontend && npm run lint:fix
	@echo "Linting backend..."
	cd backend && ruff check --fix . && ruff format .

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.cache
	rm -rf backend/dist
	rm -rf backend/.pytest_cache
	rm -rf backend/__pycache__
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +