#!/usr/bin/env python3
"""
Simple working FastAPI app for AstraForge
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the app
app = FastAPI(
    title="AstraForge API",
    description="Space Mission Simulator API",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "🚀 AstraForge API is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "astraforge-api"}

@app.get("/test")
def test_endpoint():
    return {
        "message": "Backend is working perfectly!",
        "timestamp": "2025-09-13",
        "features": ["AI Mission Generation", "Physics Simulation", "3D Visualization"]
    }

# Simple mission endpoint for testing
@app.post("/api/v1/missions/generate")
def generate_mission(prompt: dict):
    return {
        "id": "mission-123",
        "name": "Mars Exploration Mission",
        "description": f"Generated from: {prompt.get('prompt', 'No prompt provided')}",
        "status": "generated",
        "spacecraft": {
            "type": "probe",
            "mass_kg": 1000,
            "fuel_capacity_kg": 500
        },
        "trajectory": {
            "departure": "Earth",
            "destination": "Mars",
            "duration_days": 260
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AstraForge API server...")
    print("📡 Backend will be available at: http://localhost:8000")
    print("📚 API docs will be available at: http://localhost:8000/docs")
    print("🔧 Health check: http://localhost:8000/health")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )