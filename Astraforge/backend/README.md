# AstraForge Backend

FastAPI backend for the AstraForge space mission simulator.

## Tech Stack

- FastAPI with Python 3.11+
- SQLAlchemy 2.0 with async support
- Alembic for database migrations
- Pydantic v2 for data validation
- PostgreSQL database
- httpx for external API calls

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
python -m app.main
# Or with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
app/
├── api/            # API route handlers
├── core/           # Core configuration and utilities
├── models/         # SQLAlchemy models
├── services/       # Business logic services
├── ai/             # AI provider integrations
└── main.py         # FastAPI application entry point

migrations/         # Alembic database migrations
tests/              # Test files
```

## Development Tools

```bash
# Linting and formatting
ruff check .
ruff format .

# Type checking
mypy .

# Run tests
pytest

# Run tests with coverage
pytest --cov=app
```