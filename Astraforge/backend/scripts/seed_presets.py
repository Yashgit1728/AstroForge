#!/usr/bin/env python3
"""
Script to seed the database with realistic vehicle presets.
"""
import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.services.vehicle_presets import seed_vehicle_presets


async def main():
    """Main function to seed vehicle presets."""
    print("Seeding vehicle presets...")
    
    async with AsyncSessionLocal() as session:
        try:
            await seed_vehicle_presets(session)
            print("✅ Successfully seeded vehicle presets!")
        except Exception as e:
            print(f"❌ Error seeding presets: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)