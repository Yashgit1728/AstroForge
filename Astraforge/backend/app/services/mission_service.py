"""
Mission service for handling mission CRUD operations and business logic.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from ..models.database import Mission as DBMission, SimulationResult as DBSimulationResult
from ..models.mission import Mission as MissionModel, SimulationResult as SimulationResultModel
from ..schemas.mission import (
    MissionCreateRequest,
    MissionUpdateRequest,
    MissionResponse,
    MissionSummaryResponse,
    MissionListResponse
)

logger = logging.getLogger(__name__)


class MissionService:
    """Service for mission management operations."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize mission service with database session."""
        self.db = db_session
    
    async def create_mission(
        self,
        request: MissionCreateRequest,
        user_id: Optional[str] = None
    ) -> MissionResponse:
        """
        Create a new mission.
        
        Args:
            request: Mission creation request
            user_id: Optional user ID for ownership
            
        Returns:
            Created mission response
            
        Raises:
            ValueError: If mission data is invalid
        """
        try:
            # Create mission model for validation
            mission_model = MissionModel(
                name=request.name,
                description=request.description,
                objectives=request.objectives,
                spacecraft_config=request.spacecraft_config,
                trajectory=request.trajectory,
                timeline=request.timeline,
                constraints=request.constraints,
                user_id=user_id,
                is_public=request.is_public,
                difficulty_rating=request.difficulty_rating
            )
            
            # Validate mission feasibility
            issues = mission_model.validate_mission_feasibility()
            if issues:
                logger.warning(f"Mission feasibility issues: {issues}")
                # Don't block creation, but log issues
            
            # Create database record
            db_mission = DBMission(
                id=mission_model.id,
                name=mission_model.name,
                description=mission_model.description,
                objectives=mission_model.objectives,
                spacecraft_config=mission_model.spacecraft_config.model_dump(),
                trajectory=mission_model.trajectory.model_dump(),
                timeline=mission_model.timeline.model_dump(),
                constraints=mission_model.constraints.model_dump(),
                created_at=mission_model.created_at,
                updated_at=mission_model.updated_at,
                user_id=user_id,
                is_public=request.is_public,
                difficulty_rating=request.difficulty_rating
            )
            
            self.db.add(db_mission)
            await self.db.commit()
            await self.db.refresh(db_mission)
            
            logger.info(f"Created mission {db_mission.id} for user {user_id}")
            
            return MissionResponse.from_model(mission_model)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create mission: {e}")
            raise ValueError(f"Failed to create mission: {str(e)}")
    
    async def get_mission(
        self,
        mission_id: UUID,
        user_id: Optional[str] = None
    ) -> Optional[MissionResponse]:
        """
        Get a mission by ID.
        
        Args:
            mission_id: Mission ID
            user_id: Optional user ID for access control
            
        Returns:
            Mission response or None if not found/accessible
        """
        try:
            # Build query with access control
            query = select(DBMission).where(DBMission.id == mission_id)
            
            # Add access control - user can see their own missions or public ones
            if user_id:
                query = query.where(
                    or_(
                        DBMission.user_id == user_id,
                        DBMission.is_public == True
                    )
                )
            else:
                query = query.where(DBMission.is_public == True)
            
            # Include latest simulation result
            query = query.options(selectinload(DBMission.simulation_results))
            
            result = await self.db.execute(query)
            db_mission = result.scalar_one_or_none()
            
            if not db_mission:
                return None
            
            # Convert to domain model
            mission_model = self._db_to_model(db_mission)
            return MissionResponse.from_model(mission_model)
            
        except Exception as e:
            logger.error(f"Failed to get mission {mission_id}: {e}")
            return None
    
    async def update_mission(
        self,
        mission_id: UUID,
        request: MissionUpdateRequest,
        user_id: Optional[str] = None
    ) -> Optional[MissionResponse]:
        """
        Update an existing mission.
        
        Args:
            mission_id: Mission ID
            request: Update request
            user_id: User ID for ownership verification
            
        Returns:
            Updated mission response or None if not found/accessible
        """
        try:
            # Get existing mission with ownership check
            query = select(DBMission).where(DBMission.id == mission_id)
            if user_id:
                query = query.where(DBMission.user_id == user_id)
            
            result = await self.db.execute(query)
            db_mission = result.scalar_one_or_none()
            
            if not db_mission:
                return None
            
            # Update fields that are provided
            update_data = request.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                if field in ['spacecraft_config', 'trajectory', 'timeline', 'constraints']:
                    # Convert Pydantic models to dict for JSON storage
                    if value is not None:
                        setattr(db_mission, field, value.model_dump())
                else:
                    setattr(db_mission, field, value)
            
            db_mission.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(db_mission)
            
            # Convert back to domain model
            mission_model = self._db_to_model(db_mission)
            
            logger.info(f"Updated mission {mission_id} for user {user_id}")
            
            return MissionResponse.from_model(mission_model)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update mission {mission_id}: {e}")
            raise ValueError(f"Failed to update mission: {str(e)}")
    
    async def delete_mission(
        self,
        mission_id: UUID,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a mission.
        
        Args:
            mission_id: Mission ID
            user_id: User ID for ownership verification
            
        Returns:
            True if deleted, False if not found/accessible
        """
        try:
            # Get mission with ownership check
            query = select(DBMission).where(DBMission.id == mission_id)
            if user_id:
                query = query.where(DBMission.user_id == user_id)
            
            result = await self.db.execute(query)
            db_mission = result.scalar_one_or_none()
            
            if not db_mission:
                return False
            
            await self.db.delete(db_mission)
            await self.db.commit()
            
            logger.info(f"Deleted mission {mission_id} for user {user_id}")
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete mission {mission_id}: {e}")
            return False
    
    async def list_missions(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        target_body: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        difficulty_min: Optional[int] = None,
        difficulty_max: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_public: bool = True
    ) -> MissionListResponse:
        """
        List missions with filtering and pagination.
        
        Args:
            user_id: Optional user ID for access control
            page: Page number (1-based)
            page_size: Number of items per page
            search: Search term for name/description
            target_body: Filter by target celestial body
            vehicle_type: Filter by vehicle type
            difficulty_min: Minimum difficulty rating
            difficulty_max: Maximum difficulty rating
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            include_public: Whether to include public missions
            
        Returns:
            Paginated mission list response
        """
        try:
            # Build base query
            query = select(DBMission)
            count_query = select(func.count(DBMission.id))
            
            # Access control filters
            access_filters = []
            if user_id:
                access_filters.append(DBMission.user_id == user_id)
            if include_public:
                access_filters.append(DBMission.is_public == True)
            
            if access_filters:
                access_condition = or_(*access_filters)
                query = query.where(access_condition)
                count_query = count_query.where(access_condition)
            
            # Search filter
            if search:
                search_condition = or_(
                    DBMission.name.ilike(f"%{search}%"),
                    DBMission.description.ilike(f"%{search}%")
                )
                query = query.where(search_condition)
                count_query = count_query.where(search_condition)
            
            # Target body filter (stored in trajectory JSON)
            if target_body:
                query = query.where(
                    DBMission.trajectory['target_body'].astext == target_body
                )
                count_query = count_query.where(
                    DBMission.trajectory['target_body'].astext == target_body
                )
            
            # Vehicle type filter (stored in spacecraft_config JSON)
            if vehicle_type:
                query = query.where(
                    DBMission.spacecraft_config['vehicle_type'].astext == vehicle_type
                )
                count_query = count_query.where(
                    DBMission.spacecraft_config['vehicle_type'].astext == vehicle_type
                )
            
            # Difficulty filters
            if difficulty_min is not None:
                query = query.where(DBMission.difficulty_rating >= difficulty_min)
                count_query = count_query.where(DBMission.difficulty_rating >= difficulty_min)
            
            if difficulty_max is not None:
                query = query.where(DBMission.difficulty_rating <= difficulty_max)
                count_query = count_query.where(DBMission.difficulty_rating <= difficulty_max)
            
            # Sorting
            sort_column = getattr(DBMission, sort_by, DBMission.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            
            # Execute queries
            missions_result = await self.db.execute(query)
            count_result = await self.db.execute(count_query)
            
            db_missions = missions_result.scalars().all()
            total_count = count_result.scalar()
            
            # Convert to response models
            mission_summaries = [
                MissionSummaryResponse.from_model(self._db_to_model(db_mission))
                for db_mission in db_missions
            ]
            
            return MissionListResponse(
                missions=mission_summaries,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_next=offset + page_size < total_count,
                has_previous=page > 1
            )
            
        except Exception as e:
            logger.error(f"Failed to list missions: {e}")
            raise ValueError(f"Failed to list missions: {str(e)}")
    
    async def search_missions(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[MissionSummaryResponse]:
        """
        Search missions by text query.
        
        Args:
            query: Search query
            user_id: Optional user ID for access control
            limit: Maximum number of results
            
        Returns:
            List of matching mission summaries
        """
        try:
            # Build search query with ranking
            search_query = select(DBMission).where(
                or_(
                    DBMission.name.ilike(f"%{query}%"),
                    DBMission.description.ilike(f"%{query}%"),
                    func.array_to_string(DBMission.objectives, ' ').ilike(f"%{query}%")
                )
            )
            
            # Access control
            if user_id:
                search_query = search_query.where(
                    or_(
                        DBMission.user_id == user_id,
                        DBMission.is_public == True
                    )
                )
            else:
                search_query = search_query.where(DBMission.is_public == True)
            
            # Order by relevance (name matches first, then description)
            search_query = search_query.order_by(
                DBMission.name.ilike(f"%{query}%").desc(),
                DBMission.created_at.desc()
            ).limit(limit)
            
            result = await self.db.execute(search_query)
            db_missions = result.scalars().all()
            
            return [
                MissionSummaryResponse.from_model(self._db_to_model(db_mission))
                for db_mission in db_missions
            ]
            
        except Exception as e:
            logger.error(f"Failed to search missions: {e}")
            return []
    
    def _db_to_model(self, db_mission: DBMission) -> MissionModel:
        """Convert database model to domain model."""
        from ..models.mission import (
            SpacecraftConfig, TrajectoryPlan, MissionTimeline, MissionConstraints
        )
        
        # Get latest simulation result if available
        latest_simulation = None
        if db_mission.simulation_results:
            latest_result = max(
                db_mission.simulation_results,
                key=lambda x: x.simulation_timestamp
            )
            latest_simulation = SimulationResultModel(
                mission_id=latest_result.mission_id,
                simulation_id=latest_result.simulation_id,
                success_probability=latest_result.success_probability,
                total_duration_days=latest_result.total_duration_days,
                fuel_consumption_kg=latest_result.fuel_consumption_kg,
                cost_estimate_usd=latest_result.cost_estimate_usd,
                risk_factors=latest_result.risk_factors,
                performance_metrics=latest_result.performance_metrics,
                simulation_timestamp=latest_result.simulation_timestamp,
                trajectory_data=latest_result.trajectory_data,
                fuel_usage_timeline=latest_result.fuel_usage_timeline,
                system_performance=latest_result.system_performance
            )
        
        return MissionModel(
            id=db_mission.id,
            name=db_mission.name,
            description=db_mission.description,
            objectives=db_mission.objectives,
            spacecraft_config=SpacecraftConfig(**db_mission.spacecraft_config),
            trajectory=TrajectoryPlan(**db_mission.trajectory),
            timeline=MissionTimeline(**db_mission.timeline),
            constraints=MissionConstraints(**db_mission.constraints),
            created_at=db_mission.created_at,
            updated_at=db_mission.updated_at,
            user_id=db_mission.user_id,
            is_public=db_mission.is_public,
            difficulty_rating=db_mission.difficulty_rating,
            latest_simulation=latest_simulation
        )


# Export service
__all__ = ['MissionService']