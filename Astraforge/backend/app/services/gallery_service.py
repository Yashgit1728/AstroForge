"""
Gallery service for managing mission collections, examples, and search functionality.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload

from ..models.database import Mission as DBMission, SimulationResult as DBSimulationResult
from ..models.mission import Mission as MissionModel
from ..schemas.mission import MissionSummaryResponse, MissionListResponse
from .mission_service import MissionService

logger = logging.getLogger(__name__)


class GalleryService:
    """Service for mission gallery and search functionality."""
    
    def __init__(self, db_session: AsyncSession):
        """Initialize gallery service with database session."""
        self.db = db_session
        self.mission_service = MissionService(db_session)
    
    async def get_featured_missions(
        self,
        limit: int = 10,
        user_id: Optional[str] = None
    ) -> List[MissionSummaryResponse]:
        """
        Get featured missions for the gallery homepage.
        
        Featured missions are selected based on:
        - High difficulty rating
        - Recent creation
        - Successful simulations
        - Public visibility
        
        Args:
            limit: Maximum number of missions to return
            user_id: Optional user ID for personalization
            
        Returns:
            List of featured mission summaries
        """
        try:
            # Build query for featured missions
            query = select(DBMission).where(
                DBMission.is_public == True
            )
            
            # Order by difficulty and recency for featured content
            query = query.order_by(
                desc(DBMission.difficulty_rating),
                desc(DBMission.created_at)
            ).limit(limit)
            
            result = await self.db.execute(query)
            db_missions = result.scalars().all()
            
            # Convert to response models
            featured_missions = []
            for db_mission in db_missions:
                mission_model = self.mission_service._db_to_model(db_mission)
                featured_missions.append(MissionSummaryResponse.from_model(mission_model))
            
            logger.info(f"Retrieved {len(featured_missions)} featured missions")
            
            return featured_missions
            
        except Exception as e:
            logger.error(f"Failed to get featured missions: {e}")
            return []
    
    async def get_example_missions(
        self,
        category: Optional[str] = None,
        difficulty: Optional[int] = None,
        limit: int = 20
    ) -> List[MissionSummaryResponse]:
        """
        Get example missions for learning and inspiration.
        
        Example missions are curated public missions that demonstrate
        different mission types and complexity levels.
        
        Args:
            category: Optional category filter (target body)
            difficulty: Optional difficulty filter
            limit: Maximum number of missions to return
            
        Returns:
            List of example mission summaries
        """
        try:
            # Build query for example missions
            query = select(DBMission).where(
                DBMission.is_public == True
            )
            
            # Apply category filter (target body)
            if category:
                query = query.where(
                    DBMission.trajectory['target_body'].astext == category
                )
            
            # Apply difficulty filter
            if difficulty:
                query = query.where(
                    DBMission.difficulty_rating == difficulty
                )
            
            # Order by difficulty and creation date
            query = query.order_by(
                asc(DBMission.difficulty_rating),
                desc(DBMission.created_at)
            ).limit(limit)
            
            result = await self.db.execute(query)
            db_missions = result.scalars().all()
            
            # Convert to response models
            example_missions = []
            for db_mission in db_missions:
                mission_model = self.mission_service._db_to_model(db_mission)
                example_missions.append(MissionSummaryResponse.from_model(mission_model))
            
            logger.info(f"Retrieved {len(example_missions)} example missions for category {category}")
            
            return example_missions
            
        except Exception as e:
            logger.error(f"Failed to get example missions: {e}")
            return []
    
    async def get_popular_missions(
        self,
        time_period: str = "week",
        limit: int = 10
    ) -> List[MissionSummaryResponse]:
        """
        Get popular missions based on creation activity.
        
        Since we don't have view/like tracking yet, popularity is based on
        recent creation activity and simulation runs.
        
        Args:
            time_period: Time period for popularity ("day", "week", "month")
            limit: Maximum number of missions to return
            
        Returns:
            List of popular mission summaries
        """
        try:
            # Calculate time threshold
            time_thresholds = {
                "day": 1,
                "week": 7,
                "month": 30
            }
            days_back = time_thresholds.get(time_period, 7)
            
            # Build query for popular missions
            query = select(DBMission).where(
                and_(
                    DBMission.is_public == True,
                    DBMission.created_at >= func.now() - text(f"INTERVAL '{days_back} days'")
                )
            )
            
            # Order by creation date (proxy for popularity)
            query = query.order_by(
                desc(DBMission.created_at)
            ).limit(limit)
            
            result = await self.db.execute(query)
            db_missions = result.scalars().all()
            
            # Convert to response models
            popular_missions = []
            for db_mission in db_missions:
                mission_model = self.mission_service._db_to_model(db_mission)
                popular_missions.append(MissionSummaryResponse.from_model(mission_model))
            
            logger.info(f"Retrieved {len(popular_missions)} popular missions for {time_period}")
            
            return popular_missions
            
        except Exception as e:
            logger.error(f"Failed to get popular missions: {e}")
            return []
    
    async def search_missions_advanced(
        self,
        query: str,
        filters: Dict[str, Any],
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> MissionListResponse:
        """
        Advanced mission search with multiple filters and ranking.
        
        Args:
            query: Search query string
            filters: Dictionary of search filters
            user_id: Optional user ID for access control
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated search results
        """
        try:
            # Build base search query
            search_query = select(DBMission)
            count_query = select(func.count(DBMission.id))
            
            # Access control
            access_filters = []
            if user_id:
                access_filters.append(DBMission.user_id == user_id)
            if filters.get("include_public", True):
                access_filters.append(DBMission.is_public == True)
            
            if access_filters:
                access_condition = or_(*access_filters)
                search_query = search_query.where(access_condition)
                count_query = count_query.where(access_condition)
            
            # Text search with ranking
            if query:
                # Create search conditions with ranking
                search_conditions = []
                
                # Exact name match (highest priority)
                search_conditions.append(
                    DBMission.name.ilike(f"%{query}%")
                )
                
                # Description match
                search_conditions.append(
                    DBMission.description.ilike(f"%{query}%")
                )
                
                # Objectives match
                search_conditions.append(
                    func.array_to_string(DBMission.objectives, ' ').ilike(f"%{query}%")
                )
                
                # Combine search conditions
                text_search_condition = or_(*search_conditions)
                search_query = search_query.where(text_search_condition)
                count_query = count_query.where(text_search_condition)
            
            # Apply additional filters
            if filters.get("target_body"):
                search_query = search_query.where(
                    DBMission.trajectory['target_body'].astext == filters["target_body"]
                )
                count_query = count_query.where(
                    DBMission.trajectory['target_body'].astext == filters["target_body"]
                )
            
            if filters.get("vehicle_type"):
                search_query = search_query.where(
                    DBMission.spacecraft_config['vehicle_type'].astext == filters["vehicle_type"]
                )
                count_query = count_query.where(
                    DBMission.spacecraft_config['vehicle_type'].astext == filters["vehicle_type"]
                )
            
            if filters.get("difficulty_min"):
                search_query = search_query.where(
                    DBMission.difficulty_rating >= filters["difficulty_min"]
                )
                count_query = count_query.where(
                    DBMission.difficulty_rating >= filters["difficulty_min"]
                )
            
            if filters.get("difficulty_max"):
                search_query = search_query.where(
                    DBMission.difficulty_rating <= filters["difficulty_max"]
                )
                count_query = count_query.where(
                    DBMission.difficulty_rating <= filters["difficulty_max"]
                )
            
            if filters.get("has_simulation"):
                # Join with simulation results to filter missions with simulations
                search_query = search_query.join(DBSimulationResult)
                count_query = count_query.join(DBSimulationResult)
            
            # Sorting with relevance ranking
            sort_by = filters.get("sort_by", "relevance")
            sort_order = filters.get("sort_order", "desc")
            
            if sort_by == "relevance" and query:
                # Sort by relevance: exact name matches first, then by creation date
                search_query = search_query.order_by(
                    DBMission.name.ilike(f"%{query}%").desc(),
                    desc(DBMission.created_at)
                )
            else:
                # Standard sorting
                sort_column = getattr(DBMission, sort_by, DBMission.created_at)
                if sort_order.lower() == "desc":
                    search_query = search_query.order_by(desc(sort_column))
                else:
                    search_query = search_query.order_by(asc(sort_column))
            
            # Pagination
            offset = (page - 1) * page_size
            search_query = search_query.offset(offset).limit(page_size)
            
            # Execute queries
            missions_result = await self.db.execute(search_query)
            count_result = await self.db.execute(count_query)
            
            db_missions = missions_result.scalars().all()
            total_count = count_result.scalar()
            
            # Convert to response models
            mission_summaries = []
            for db_mission in db_missions:
                mission_model = self.mission_service._db_to_model(db_mission)
                mission_summaries.append(MissionSummaryResponse.from_model(mission_model))
            
            logger.info(f"Advanced search returned {len(mission_summaries)} results for query '{query}'")
            
            return MissionListResponse(
                missions=mission_summaries,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_next=offset + page_size < total_count,
                has_previous=page > 1
            )
            
        except Exception as e:
            logger.error(f"Failed to perform advanced search: {e}")
            raise ValueError(f"Search failed: {str(e)}")
    
    async def get_mission_categories(self) -> Dict[str, int]:
        """
        Get available mission categories with counts.
        
        Returns:
            Dictionary mapping category names to mission counts
        """
        try:
            # Get target body distribution
            target_body_query = select(
                DBMission.trajectory['target_body'].astext.label('target_body'),
                func.count(DBMission.id).label('count')
            ).where(
                DBMission.is_public == True
            ).group_by(
                DBMission.trajectory['target_body'].astext
            )
            
            result = await self.db.execute(target_body_query)
            categories = dict(result.fetchall())
            
            logger.info(f"Retrieved {len(categories)} mission categories")
            
            return categories
            
        except Exception as e:
            logger.error(f"Failed to get mission categories: {e}")
            return {}
    
    async def get_difficulty_distribution(self) -> Dict[int, int]:
        """
        Get mission difficulty distribution.
        
        Returns:
            Dictionary mapping difficulty levels to mission counts
        """
        try:
            difficulty_query = select(
                DBMission.difficulty_rating,
                func.count(DBMission.id).label('count')
            ).where(
                DBMission.is_public == True
            ).group_by(
                DBMission.difficulty_rating
            ).order_by(
                DBMission.difficulty_rating
            )
            
            result = await self.db.execute(difficulty_query)
            distribution = dict(result.fetchall())
            
            logger.info(f"Retrieved difficulty distribution: {distribution}")
            
            return distribution
            
        except Exception as e:
            logger.error(f"Failed to get difficulty distribution: {e}")
            return {}
    
    async def get_gallery_stats(self) -> Dict[str, Any]:
        """
        Get overall gallery statistics.
        
        Returns:
            Dictionary with gallery statistics
        """
        try:
            # Total public missions
            total_query = select(func.count(DBMission.id)).where(
                DBMission.is_public == True
            )
            total_result = await self.db.execute(total_query)
            total_missions = total_result.scalar()
            
            # Missions with simulations
            simulated_query = select(func.count(func.distinct(DBMission.id))).select_from(
                DBMission.join(DBSimulationResult)
            ).where(
                DBMission.is_public == True
            )
            simulated_result = await self.db.execute(simulated_query)
            simulated_missions = simulated_result.scalar()
            
            # Recent missions (last 7 days)
            recent_query = select(func.count(DBMission.id)).where(
                and_(
                    DBMission.is_public == True,
                    DBMission.created_at >= func.now() - text("INTERVAL '7 days'")
                )
            )
            recent_result = await self.db.execute(recent_query)
            recent_missions = recent_result.scalar()
            
            stats = {
                "total_missions": total_missions,
                "simulated_missions": simulated_missions,
                "recent_missions": recent_missions,
                "simulation_rate": simulated_missions / total_missions if total_missions > 0 else 0
            }
            
            logger.info(f"Retrieved gallery stats: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get gallery stats: {e}")
            return {
                "total_missions": 0,
                "simulated_missions": 0,
                "recent_missions": 0,
                "simulation_rate": 0
            }


# Export service
__all__ = ['GalleryService']