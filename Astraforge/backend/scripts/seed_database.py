#!/usr/bin/env python3
"""
Database seeding script for AstraForge.
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.models.database import Base
from app.services.vehicle_presets import seed_vehicle_presets


async def create_tables():
    """Create database tables if they don't exist."""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Database tables created successfully")


async def seed_vehicle_presets_data():
    """Seed vehicle presets data."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        await seed_vehicle_presets(session)
        print("✅ Vehicle presets seeded successfully")
    
    await engine.dispose()


async def main():
    """Main seeding function."""
    print("🚀 Starting database seeding...")
    
    try:
        # Create tables first
        await create_tables()
        
        # Seed vehicle presets
        await seed_vehicle_presets_data()
        
        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during database seeding: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())