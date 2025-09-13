-- Initialize AstraForge database
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create initial database structure will be handled by Alembic migrations
-- This file is mainly for any initial setup that needs to happen before migrations