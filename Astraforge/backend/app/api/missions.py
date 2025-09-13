"""
Mission management API endpoints.

This module provides CRUD operations for missions, including:
- Mission creation, retrieval, update, and deletion
- Mission search and filtering
- Mission simulation and optimization triggers
- AI-powered mission generation
"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..schemas.mission import (
    MissionCreateRequest,
    MissionUpdateRequest,
    MissionGenerateRequest,
    SimulationRequest,
    OptimizationRequest,
    MissionResponse,
    MissionSummaryResponse,
    MissionListResponse,
    SimulationResponse,
    OptimizationResponse,
    MissionGenerationResponse,
    ErrorResponse
)
from ..services.mission_service import MissionService
from ..services.simulation_service import MissionSimulationService
from ..services.optimization_service import MissionOptimizationService
from ..ai.ideation_service import MissionIdeationService
from ..ai.provider_factory import LLMProviderManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/missions", tags=["missions"])


# Import authentication dependencies
from ..core.auth import get_current_user


@router.post("/", response_model=MissionResponse)
async def create_mission(
    request: MissionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> MissionResponse:
    """
    Create a new mission.
    
    Creates a new mission with the provided specifications. The mission
    will be validated for feasibility before creation.
    """
    try:
        mission_service = MissionService(db)
        mission = await mission_service.create_mission(request, current_user)
        
        logger.info(f"Created mission {mission.id}")
        return mission
        
    except ValueError as e:
        logger.error(f"Mission creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating mission: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(
    mission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> MissionResponse:
    """
    Get a mission by ID.
    
    Retrieves a mission by its ID. Users can only access their own missions
    or public missions.
    """
    try:
        mission_service = MissionService(db)
        mission = await mission_service.get_mission(mission_id, current_user)
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        return mission
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{mission_id}", response_model=MissionResponse)
async def update_mission(
    mission_id: UUID,
    request: MissionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> MissionResponse:
    """
    Update an existing mission.
    
    Updates a mission with the provided data. Only the mission owner
    can update their missions.
    """
    try:
        mission_service = MissionService(db)
        mission = await mission_service.update_mission(mission_id, request, current_user)
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found or access denied")
        
        logger.info(f"Updated mission {mission_id}")
        return mission
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Mission update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{mission_id}")
async def delete_mission(
    mission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete a mission.
    
    Deletes a mission and all associated data. Only the mission owner
    can delete their missions.
    """
    try:
        mission_service = MissionService(db)
        deleted = await mission_service.delete_mission(mission_id, current_user)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Mission not found or access denied")
        
        logger.info(f"Deleted mission {mission_id}")
        return {"message": "Mission deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=MissionListResponse)
async def list_missions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    target_body: Optional[str] = Query(None, description="Filter by target body"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    difficulty_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum difficulty"),
    difficulty_max: Optional[int] = Query(None, ge=1, le=5, description="Maximum difficulty"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    include_public: bool = Query(True, description="Include public missions"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> MissionListResponse:
    """
    List missions with filtering and pagination.
    
    Returns a paginated list of missions with optional filtering by various
    criteria. Users see their own missions plus public missions.
    """
    try:
        mission_service = MissionService(db)
        missions = await mission_service.list_missions(
            user_id=current_user,
            page=page,
            page_size=page_size,
            search=search,
            target_body=target_body,
            vehicle_type=vehicle_type,
            difficulty_min=difficulty_min,
            difficulty_max=difficulty_max,
            sort_by=sort_by,
            sort_order=sort_order,
            include_public=include_public
        )
        
        return missions
        
    except ValueError as e:
        logger.error(f"Mission listing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing missions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search/", response_model=List[MissionSummaryResponse])
async def search_missions(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> List[MissionSummaryResponse]:
    """
    Search missions by text query.
    
    Performs a text search across mission names, descriptions, and objectives.
    Returns missions ranked by relevance.
    """
    try:
        mission_service = MissionService(db)
        missions = await mission_service.search_missions(q, current_user, limit)
        
        return missions
        
    except Exception as e:
        logger.error(f"Error searching missions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate", response_model=MissionGenerationResponse)
async def generate_mission(
    request: MissionGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> MissionGenerationResponse:
    """
    Generate a mission using AI.
    
    Uses AI to generate a complete mission specification based on a natural
    language prompt. Optionally includes alternative mission suggestions.
    """
    try:
        # Initialize AI services
        provider_manager = LLMProviderManager()
        ideation_service = MissionIdeationService(provider_manager)
        
        # Generate mission
        result = await ideation_service.generate_mission(
            user_prompt=request.prompt,
            user_id=request.user_id or current_user,
            provider_preference=request.provider_preference,
            temperature=request.temperature,
            include_alternatives=request.include_alternatives
        )
        
        # Save generated mission to database
        mission_service = MissionService(db)
        saved_mission = await mission_service.create_mission(
            MissionCreateRequest(
                name=result.mission.name,
                description=result.mission.description,
                objectives=result.mission.objectives,
                spacecraft_config=result.mission.spacecraft_config,
                trajectory=result.mission.trajectory,
                timeline=result.mission.timeline,
                constraints=result.mission.constraints,
                is_public=False,  # Generated missions are private by default
                difficulty_rating=result.mission.difficulty_rating
            ),
            current_user
        )
        
        # Convert alternatives to summary responses
        alternatives = []
        if result.alternatives:
            for alt in result.alternatives:
                alternatives.append(MissionSummaryResponse.from_model(alt))
        
        logger.info(f"Generated mission {saved_mission.id} from prompt")
        
        return MissionGenerationResponse(
            mission=saved_mission,
            alternatives=alternatives,
            generation_metadata=result.metadata
        )
        
    except ValueError as e:
        logger.error(f"Mission generation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating mission: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{mission_id}/simulate", response_model=SimulationResponse)
async def simulate_mission(
    mission_id: UUID,
    request: SimulationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> SimulationResponse:
    """
    Run physics-based simulation for a mission.
    
    Executes a comprehensive physics simulation of the mission including
    orbital mechanics, fuel consumption, and performance analysis.
    """
    try:
        # Verify mission access
        mission_service = MissionService(db)
        mission = await mission_service.get_mission(mission_id, current_user)
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Initialize simulation service
        simulation_service = MissionSimulationService(db)
        
        # Run simulation (this might be long-running)
        result = await simulation_service.simulate_mission(
            mission_id=mission_id,
            parameters=request.simulation_parameters,
            include_detailed_results=request.include_detailed_results
        )
        
        logger.info(f"Completed simulation for mission {mission_id}")
        
        return SimulationResponse.from_model(result)
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error simulating mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{mission_id}/optimize", response_model=OptimizationResponse)
async def optimize_mission(
    mission_id: UUID,
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> OptimizationResponse:
    """
    Optimize mission parameters using genetic algorithms.
    
    Runs optimization to find better mission parameters based on specified
    objectives and constraints. This is a long-running operation.
    """
    try:
        # Verify mission access
        mission_service = MissionService(db)
        mission = await mission_service.get_mission(mission_id, current_user)
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Initialize optimization service
        optimization_service = MissionOptimizationService(db)
        
        # Start optimization job
        job = await optimization_service.start_optimization(
            mission_id=mission_id,
            optimization_type=request.optimization_type,
            objectives=request.objectives,
            constraints=request.constraints,
            parameters=request.parameters
        )
        
        logger.info(f"Started optimization job {job.id} for mission {mission_id}")
        
        return OptimizationResponse(
            job_id=job.id,
            mission_id=mission_id,
            status=job.status,
            progress_percent=job.progress_percent,
            created_at=job.created_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Optimization failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error optimizing mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{mission_id}/optimization/{job_id}", response_model=OptimizationResponse)
async def get_optimization_status(
    mission_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[str] = Depends(get_current_user)
) -> OptimizationResponse:
    """
    Get optimization job status and results.
    
    Returns the current status of an optimization job, including progress
    and results if completed.
    """
    try:
        # Verify mission access
        mission_service = MissionService(db)
        mission = await mission_service.get_mission(mission_id, current_user)
        
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        
        # Get optimization job status
        optimization_service = MissionOptimizationService(db)
        job = await optimization_service.get_optimization_job(job_id)
        
        if not job or job.mission_id != mission_id:
            raise HTTPException(status_code=404, detail="Optimization job not found")
        
        return OptimizationResponse(
            job_id=job.id,
            mission_id=job.mission_id,
            status=job.status,
            progress_percent=job.progress_percent,
            results=job.results,
            pareto_front=job.pareto_front,
            best_solution=job.best_solution,
            created_at=job.created_at,
            completed_at=job.completed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Export router
__all__ = ['router']