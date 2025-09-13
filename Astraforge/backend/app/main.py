"""
AstraForge FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
# from app.core.auth import AuthMiddleware, JWTValidationMiddleware
# from app.api.vehicle_presets import router as vehicle_presets_router
# from app.api.missions import router as missions_router
# from app.api.auth import router as auth_router
# from app.api.gallery import router as gallery_router

app = FastAPI(
    title="AstraForge API",
    description="Space Mission Simulator API",
    version="0.1.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# Configure CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add authentication middleware (temporarily disabled for testing)
# app.add_middleware(AuthMiddleware)
# app.add_middleware(JWTValidationMiddleware)

# Include API routers (temporarily disabled for testing)
# app.include_router(vehicle_presets_router, prefix=settings.API_V1_STR)
# app.include_router(missions_router, prefix=settings.API_V1_STR)
# app.include_router(auth_router, prefix=settings.API_V1_STR)
# app.include_router(gallery_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint"""
    return {"message": "AstraForge API is running"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/test")
async def test_endpoint() -> dict[str, str]:
    """Simple test endpoint"""
    return {"message": "Backend is working!", "timestamp": "2025-09-13"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True if settings.ENVIRONMENT == "development" else False,
    )