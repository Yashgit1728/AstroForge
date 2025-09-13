"""
Gallery API endpoints for mission browsing, search, and discovery.
"""
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..core.auth import get_current_user
from ..schemas.mission import MissionSummaryResponse, MissionListResponse
from ..services.gallery_service import GalleryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gallery", tags=["gallery"])


# Response schemas
class FeaturedMissionsResponse(BaseModel):
    """Response schema for featured missions."""
    missions: List[MissionSummaryResponse]
    total_count: int


class ExampleMissionsResponse(BaseModel):
    """Response schema for example missions."""
    missions: List[MissionSummaryResponse]
    category: Optional[str]
    difficulty: Optional[int]
    total_count: int


class PopularMissionsResponse(BaseModel):
    """Response schema for popular missions."""
    missions: List[MissionSummaryResponse]
    time_period: str
    total_count: int


class SearchFilters(BaseModel):
    """Search filters for advanced search."""
    target_body: Optional[str] = None
    vehicle_type: Optional[str] = None
    difficulty_min: Optional[int] = Field(None, ge=1, le=5)
    difficulty_max: Optional[int] = Field(None, ge=1, le=5)
    has_simulation: Optional[bool] = None
    include_public: bool = True
    sort_by: str = "relevance"
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class GalleryStatsResponse(BaseModel):
    """Response schema for gallery statistics."""
    total_missions: int
    simulated_missions: int
    recent_missions: int
    simulation_rate: float
    categories: Dict[str, int]
    difficulty_distribution: Dict[int, int]


@router.get("/featured", response_model=FeaturedMissionsResponse)
async def get_featured_missions(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of missions"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> FeaturedMissionsResponse:
    """
    Get featured missions for the gallery homepage.
    
    Featured missions are high-quality, interesting missions that showcase
    the capabilities of the platform. They are selected based on difficulty,
    simulation results, and community interest.
    """
    try:
        gallery_service = GalleryService(db)
        missions = await gallery_service.get_featured_missions(limit, current_user)
        
        return FeaturedMissionsResponse(
            missions=missions,
            total_count=len(missions)
        )
        
    except Exception as e:
        logger.error(f"Error getting featured missions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/examples", response_model=ExampleMissionsResponse)
async def get_example_missions(
    category: Optional[str] = Query(None, description="Mission category (target body)"),
    difficulty: Optional[int] = Query(None, ge=1, le=5, description="Difficulty level"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of missions"),
    db: AsyncSession = Depends(get_db)
) -> ExampleMissionsResponse:
    """
    Get example missions for learning and inspiration.
    
    Example missions are curated public missions that demonstrate different
    mission types, complexity levels, and best practices. They serve as
    templates and learning resources for users.
    """
    try:
        gallery_service = GalleryService(db)
        missions = await gallery_service.get_example_missions(category, difficulty, limit)
        
        return ExampleMissionsResponse(
            missions=missions,
            category=category,
            difficulty=difficulty,
            total_count=len(missions)
        )
        
    except Exception as e:
        logger.error(f"Error getting example missions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/popular", response_model=PopularMissionsResponse)
async def get_popular_missions(
    time_period: str = Query("week", pattern="^(day|week|month)$", description="Time period"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of missions"),
    db: AsyncSession = Depends(get_db)
) -> PopularMissionsResponse:
    """
    Get popular missions based on recent activity.
    
    Popular missions are determined by recent creation activity and
    simulation runs within the specified time period.
    """
    try:
        gallery_service = GalleryService(db)
        missions = await gallery_service.get_popular_missions(time_period, limit)
        
        return PopularMissionsResponse(
            missions=missions,
            time_period=time_period,
            total_count=len(missions)
        )
        
    except Exception as e:
        logger.error(f"Error getting popular missions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search", response_model=MissionListResponse)
async def search_missions(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    target_body: Optional[str] = Query(None, description="Filter by target body"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    difficulty_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum difficulty"),
    difficulty_max: Optional[int] = Query(None, ge=1, le=5, description="Maximum difficulty"),
    has_simulation: Optional[bool] = Query(None, description="Filter missions with simulations"),
    include_public: bool = Query(True, description="Include public missions"),
    sort_by: str = Query("relevance", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> MissionListResponse:
    """
    Advanced mission search with filtering and ranking.
    
    Performs a comprehensive search across mission names, descriptions, and
    objectives with support for multiple filters and relevance ranking.
    """
    try:
        gallery_service = GalleryService(db)
        
        # Build filters dictionary
        filters = {
            "target_body": target_body,
            "vehicle_type": vehicle_type,
            "difficulty_min": difficulty_min,
            "difficulty_max": difficulty_max,
            "has_simulation": has_simulation,
            "include_public": include_public,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        results = await gallery_service.search_missions_advanced(
            query=q,
            filters=filters,
            user_id=current_user,
            page=page,
            page_size=page_size
        )
        
        return results
        
    except ValueError as e:
        logger.error(f"Search validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching missions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


class AdvancedSearchRequest(BaseModel):
    """Request schema for advanced search."""
    query: str = Field(..., min_length=1, description="Search query")
    filters: SearchFilters = SearchFilters()
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


@router.post("/search/advanced", response_model=MissionListResponse)
async def advanced_search_missions(
    request: AdvancedSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> MissionListResponse:
    """
    Advanced mission search with complex filters.
    
    This endpoint accepts a JSON payload with detailed search criteria
    and returns ranked results with pagination.
    """
    try:
        gallery_service = GalleryService(db)
        
        results = await gallery_service.search_missions_advanced(
            query=request.query,
            filters=request.filters.model_dump(exclude_unset=True),
            user_id=current_user,
            page=request.page,
            page_size=request.page_size
        )
        
        return results
        
    except ValueError as e:
        logger.error(f"Advanced search validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories", response_model=Dict[str, int])
async def get_mission_categories(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, int]:
    """
    Get available mission categories with counts.
    
    Returns a dictionary mapping category names (target bodies) to the
    number of public missions in each category.
    """
    try:
        gallery_service = GalleryService(db)
        categories = await gallery_service.get_mission_categories()
        
        return categories
        
    except Exception as e:
        logger.error(f"Error getting mission categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/difficulty-distribution", response_model=Dict[int, int])
async def get_difficulty_distribution(
    db: AsyncSession = Depends(get_db)
) -> Dict[int, int]:
    """
    Get mission difficulty distribution.
    
    Returns a dictionary mapping difficulty levels (1-5) to the number
    of public missions at each difficulty level.
    """
    try:
        gallery_service = GalleryService(db)
        distribution = await gallery_service.get_difficulty_distribution()
        
        return distribution
        
    except Exception as e:
        logger.error(f"Error getting difficulty distribution: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=GalleryStatsResponse)
async def get_gallery_stats(
    db: AsyncSession = Depends(get_db)
) -> GalleryStatsResponse:
    """
    Get comprehensive gallery statistics.
    
    Returns overall statistics about the mission gallery including
    total missions, simulation rates, categories, and difficulty distribution.
    """
    try:
        gallery_service = GalleryService(db)
        
        # Get basic stats
        stats = await gallery_service.get_gallery_stats()
        
        # Get categories and difficulty distribution
        categories = await gallery_service.get_mission_categories()
        difficulty_distribution = await gallery_service.get_difficulty_distribution()
        
        return GalleryStatsResponse(
            total_missions=stats["total_missions"],
            simulated_missions=stats["simulated_missions"],
            recent_missions=stats["recent_missions"],
            simulation_rate=stats["simulation_rate"],
            categories=categories,
            difficulty_distribution=difficulty_distribution
        )
        
    except Exception as e:
        logger.error(f"Error getting gallery stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/suggestions")
async def get_mission_suggestions(
    based_on: Optional[str] = Query(None, description="Base suggestions on mission ID"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> List[MissionSummaryResponse]:
    """
    Get mission suggestions for discovery.
    
    Returns mission suggestions based on user preferences, similar missions,
    or general recommendations for exploration.
    """
    try:
        gallery_service = GalleryService(db)
        
        # For now, return featured missions as suggestions
        # In the future, this could use ML-based recommendations
        suggestions = await gallery_service.get_featured_missions(limit, current_user)
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error getting mission suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Export router
__all__ = ['router']