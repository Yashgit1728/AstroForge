"""
Integration tests for mission optimization service.

Tests the integration of genetic algorithms with mission simulation
for parameter optimization and multi-objective optimization.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from datetime import datetime

from app.services.optimization_service import (
    MissionOptimizationService, OptimizationConfig, OptimizationParameter,
    OptimizationConstraint, OptimizationObjective, OptimizationStatus
)
from app.models.mission import (
    Mission, SpacecraftConfig, TrajectoryPlan, MissionTimeline, 
    MissionConstraints, SimulationResult, VehicleType, CelestialBody, 
    TransferType, DateRange
)
from app.services.simulation_service import MissionSimulationService
from app.services.validation_service import MissionValidationService


class TestOptimizationParameter:
    """Test OptimizationParameter class."""
    
    def test_valid_parameter(self):
        """Test valid parameter creation."""
        param = OptimizationParameter(
            name="mass_kg",
            min_value=1000.0,
            max_value=5000.0,
            current_value=3000.0,
            parameter_type="spacecraft",
            description="Spacecraft mass"
        )
        
        assert param.name == "mass_kg"
        assert param.min_value == 1000.0
        assert param.max_value == 5000.0
        assert param.current_value == 3000.0
    
    def test_invalid_bounds(self):
        """Test parameter with invalid bounds."""
        with pytest.raises(ValueError, match="Invalid bounds"):
            OptimizationParameter(
                name="mass_kg",
                min_value=5000.0,
                max_value=1000.0,  # max < min
                current_value=3000.0,
                parameter_type="spacecraft"
            )
    
    def test_current_value_outside_bounds(self):
        """Test parameter with current value outside bounds."""
        with pytest.raises(ValueError, match="Current value.*is outside bounds"):
            OptimizationParameter(
                name="mass_kg",
                min_value=1000.0,
                max_value=5000.0,
                current_value=6000.0,  # Outside bounds
                parameter_type="spacecraft"
            )


class TestOptimizationConfig:
    """Test OptimizationConfig class."""
    
    def create_valid_config(self) -> OptimizationConfig:
        """Create valid optimization configuration."""
        parameters = [
            OptimizationParameter(
                name="mass_kg",
                min_value=1000.0,
                max_value=5000.0,
                current_value=3000.0,
                parameter_type="spacecraft"
            ),
            OptimizationParameter(
                name="fuel_capacity_kg",
                min_value=500.0,
                max_value=2000.0,
                current_value=1000.0,
                parameter_type="spacecraft"
            )
        ]
        
        return OptimizationConfig(
            objectives=[OptimizationObjective.MINIMIZE_FUEL],
            parameters=parameters,
            population_size=20,
            max_generations=10
        )
    
    def test_valid_config(self):
        """Test valid configuration creation."""
        config = self.create_valid_config()
        
        assert len(config.objectives) == 1
        assert len(config.parameters) == 2
        assert config.population_size == 20
        assert config.max_generations == 10
    
    def test_no_objectives_error(self):
        """Test error when no objectives specified."""
        parameters = [
            OptimizationParameter(
                name="mass_kg",
                min_value=1000.0,
                max_value=5000.0,
                current_value=3000.0,
                parameter_type="spacecraft"
            )
        ]
        
        with pytest.raises(ValueError, match="At least one optimization objective"):
            OptimizationConfig(
                objectives=[],
                parameters=parameters
            )
    
    def test_no_parameters_error(self):
        """Test error when no parameters specified."""
        with pytest.raises(ValueError, match="At least one optimization parameter"):
            OptimizationConfig(
                objectives=[OptimizationObjective.MINIMIZE_FUEL],
                parameters=[]
            )


class TestMissionOptimizationService:
    """Test MissionOptimizationService class."""
    
    def create_mock_services(self) -> tuple[Mock, Mock]:
        """Create mock simulation and validation services."""
        simulation_service = Mock(spec=MissionSimulationService)
        validation_service = Mock(spec=MissionValidationService)
        
        # Mock simulation result
        mock_sim_result = SimulationResult(
            mission_id=uuid4(),
            success_probability=0.85,
            total_duration_days=365.0,
            fuel_consumption_kg=800.0,
            cost_estimate_usd=1e8,
            risk_factors=[],
            performance_metrics={}
        )
        
        simulation_service.simulate_mission.return_value = mock_sim_result
        
        return simulation_service, validation_service
    
    def create_test_mission(self) -> Mission:
        """Create test mission for optimization."""
        spacecraft_config = SpacecraftConfig(
            vehicle_type=VehicleType.MEDIUM_SAT,
            name="Test Spacecraft",
            mass_kg=3000.0,
            fuel_capacity_kg=1000.0,
            thrust_n=500.0,
            specific_impulse_s=300.0,
            payload_mass_kg=200.0,
            power_w=2000.0
        )
        
        trajectory = TrajectoryPlan(
            launch_window=DateRange(
                start=datetime(2025, 1, 1),
                end=datetime(2025, 12, 31)
            ),
            departure_body=CelestialBody.EARTH,
            target_body=CelestialBody.MARS,
            transfer_type=TransferType.HOHMANN,
            maneuvers=[],
            total_delta_v=6000.0,
            flight_time_days=365.0
        )
        
        timeline = MissionTimeline(
            launch_date=datetime(2025, 6, 1),
            major_milestones=[],
            mission_phases=[]
        )
        
        constraints = MissionConstraints()
        
        return Mission(
            name="Test Mars Mission",
            description="Test mission for optimization",
            objectives=["Reach Mars orbit"],
            spacecraft_config=spacecraft_config,
            trajectory=trajectory,
            timeline=timeline,
            constraints=constraints
        )
    
    def create_test_config(self) -> OptimizationConfig:
        """Create test optimization configuration."""
        parameters = [
            OptimizationParameter(
                name="spacecraft_mass_kg",
                min_value=2000.0,
                max_value=4000.0,
                current_value=3000.0,
                parameter_type="spacecraft"
            ),
            OptimizationParameter(
                name="fuel_capacity_kg",
                min_value=800.0,
                max_value=1200.0,
                current_value=1000.0,
                parameter_type="spacecraft"
            )
        ]
        
        return OptimizationConfig(
            objectives=[OptimizationObjective.MINIMIZE_FUEL],
            parameters=parameters,
            population_size=10,
            max_generations=5
        )
    
    def test_service_initialization(self):
        """Test optimization service initialization."""
        sim_service, val_service = self.create_mock_services()
        
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        assert opt_service.simulation_service == sim_service
        assert opt_service.validation_service == val_service
        assert len(opt_service.active_jobs) == 0
        assert len(opt_service.simulation_cache) == 0
    
    @pytest.mark.asyncio
    async def test_start_optimization(self):
        """Test starting optimization job."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        mission = self.create_test_mission()
        config = self.create_test_config()
        
        job_id = await opt_service.start_optimization(mission, config)
        
        assert job_id is not None
        assert job_id in opt_service.active_jobs
        
        result = opt_service.active_jobs[job_id]
        assert result.mission_id == mission.id
        assert result.config == config
        assert result.status in [OptimizationStatus.PENDING, OptimizationStatus.RUNNING]
    
    def test_individual_to_mission_conversion(self):
        """Test converting GA individual to mission object."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        base_mission = self.create_test_mission()
        
        # Create test individual
        from app.optimization.genetic_algorithm import Individual
        individual = Individual(genes={
            'spacecraft_mass_kg': 3500.0,
            'fuel_capacity_kg': 1100.0
        })
        
        # Convert to mission
        mission = opt_service._individual_to_mission(individual, base_mission)
        
        assert mission.spacecraft_config.mass_kg == 3500.0
        assert mission.spacecraft_config.fuel_capacity_kg == 1100.0
        assert mission.name == base_mission.name
        assert mission.description == base_mission.description
    
    def test_parameter_application(self):
        """Test applying parameters to mission."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        mission = self.create_test_mission()
        
        # Apply spacecraft parameters
        opt_service._apply_parameter_to_mission(mission, "spacecraft_mass_kg", 3500.0)
        opt_service._apply_parameter_to_mission(mission, "fuel_capacity_kg", 1100.0)
        opt_service._apply_parameter_to_mission(mission, "thrust_n", 600.0)
        
        assert mission.spacecraft_config.mass_kg == 3500.0
        assert mission.spacecraft_config.fuel_capacity_kg == 1100.0
        assert mission.spacecraft_config.thrust_n == 600.0
        
        # Apply trajectory parameters
        opt_service._apply_parameter_to_mission(mission, "flight_time_days", 400.0)
        opt_service._apply_parameter_to_mission(mission, "total_delta_v", 6500.0)
        
        assert mission.trajectory.flight_time_days == 400.0
        assert mission.trajectory.total_delta_v == 6500.0
    
    def test_objective_function_creation(self):
        """Test creation of objective functions."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        config = OptimizationConfig(
            objectives=[
                OptimizationObjective.MINIMIZE_FUEL,
                OptimizationObjective.MINIMIZE_DURATION,
                OptimizationObjective.MAXIMIZE_SUCCESS_PROBABILITY
            ],
            parameters=[
                OptimizationParameter(
                    name="mass_kg",
                    min_value=1000.0,
                    max_value=5000.0,
                    current_value=3000.0,
                    parameter_type="spacecraft"
                )
            ]
        )
        
        objectives = opt_service._create_objective_functions(config)
        
        assert len(objectives) == 3
        
        objective_names = [obj.name for obj in objectives]
        assert "fuel_consumption" in objective_names
        assert "mission_duration" in objective_names
        assert "success_probability" in objective_names
    
    def test_fitness_function_creation(self):
        """Test creation of fitness function."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        base_mission = self.create_test_mission()
        config = self.create_test_config()
        
        fitness_func = opt_service._create_fitness_function(base_mission, config)
        
        # Test fitness function
        from app.optimization.genetic_algorithm import Individual
        individual = Individual(genes={
            'spacecraft_mass_kg': 3000.0,
            'fuel_capacity_kg': 1000.0
        })
        
        fitness = fitness_func(individual)
        
        # Should return a finite fitness value
        assert fitness != float('-inf')
        assert fitness != float('inf')
        
        # Check that objectives were populated
        assert 'fuel_consumption_kg' in individual.objectives
        assert 'total_duration_days' in individual.objectives
        assert 'success_probability' in individual.objectives
    
    def test_cache_key_creation(self):
        """Test simulation cache key creation."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        from app.optimization.genetic_algorithm import Individual
        
        # Create two identical individuals
        ind1 = Individual(genes={'x': 1.0, 'y': 2.0})
        ind2 = Individual(genes={'x': 1.0, 'y': 2.0})
        
        # Create different individual
        ind3 = Individual(genes={'x': 1.0, 'y': 3.0})
        
        key1 = opt_service._create_cache_key(ind1)
        key2 = opt_service._create_cache_key(ind2)
        key3 = opt_service._create_cache_key(ind3)
        
        # Identical individuals should have same key
        assert key1 == key2
        
        # Different individuals should have different keys
        assert key1 != key3
    
    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        from app.models.mission import RiskFactor, RiskLevel
        
        # Create simulation result with risk factors
        sim_result = SimulationResult(
            mission_id=uuid4(),
            success_probability=0.8,
            total_duration_days=365.0,
            fuel_consumption_kg=800.0,
            cost_estimate_usd=1e8,
            risk_factors=[
                RiskFactor(
                    category="technical",
                    description="Engine failure risk",
                    probability=0.1,
                    impact=RiskLevel.HIGH
                ),
                RiskFactor(
                    category="environmental",
                    description="Solar storm risk",
                    probability=0.05,
                    impact=RiskLevel.MEDIUM
                )
            ],
            performance_metrics={}
        )
        
        risk_score = opt_service._calculate_risk_score(sim_result)
        
        # Risk score should be positive
        assert risk_score > 0.0
        
        # Should include success probability component
        expected_success_risk = (1.0 - 0.8) * 10.0
        assert risk_score >= expected_success_risk
    
    def test_constraint_function_creation(self):
        """Test creation of constraint functions."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        base_mission = self.create_test_mission()
        
        # Create test constraint
        def mass_constraint(mission: Mission) -> bool:
            return mission.spacecraft_config.mass_kg <= 3500.0
        
        constraint = OptimizationConstraint(
            name="max_mass",
            constraint_function=mass_constraint,
            description="Maximum spacecraft mass"
        )
        
        constraint_func = opt_service._create_constraint_function(constraint, base_mission)
        
        # Test constraint function
        from app.optimization.genetic_algorithm import Individual
        
        # Individual that satisfies constraint
        ind1 = Individual(genes={'spacecraft_mass_kg': 3000.0})
        assert constraint_func(ind1) == True
        
        # Individual that violates constraint
        ind2 = Individual(genes={'spacecraft_mass_kg': 4000.0})
        assert constraint_func(ind2) == False
    
    def test_get_optimization_status(self):
        """Test getting optimization status."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        # Test non-existent job
        result = opt_service.get_optimization_status(uuid4())
        assert result is None
        
        # Add a job manually
        job_id = uuid4()
        from app.services.optimization_service import OptimizationResult
        
        opt_result = OptimizationResult(
            job_id=job_id,
            mission_id=uuid4(),
            status=OptimizationStatus.RUNNING,
            config=self.create_test_config()
        )
        
        opt_service.active_jobs[job_id] = opt_result
        
        # Test existing job
        result = opt_service.get_optimization_status(job_id)
        assert result == opt_result
    
    def test_cancel_optimization(self):
        """Test cancelling optimization job."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        # Test non-existent job
        success = opt_service.cancel_optimization(uuid4())
        assert success == False
        
        # Add running job
        job_id = uuid4()
        from app.services.optimization_service import OptimizationResult
        
        opt_result = OptimizationResult(
            job_id=job_id,
            mission_id=uuid4(),
            status=OptimizationStatus.RUNNING,
            config=self.create_test_config()
        )
        
        opt_service.active_jobs[job_id] = opt_result
        
        # Cancel job
        success = opt_service.cancel_optimization(job_id)
        assert success == True
        assert opt_result.status == OptimizationStatus.CANCELLED
        assert opt_result.completed_at is not None
    
    def test_cleanup_completed_jobs(self):
        """Test cleanup of old completed jobs."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        from app.services.optimization_service import OptimizationResult
        from datetime import timedelta
        
        # Add old completed job
        old_job_id = uuid4()
        old_time = datetime.now() - timedelta(hours=25)  # Older than 24 hours
        
        old_result = OptimizationResult(
            job_id=old_job_id,
            mission_id=uuid4(),
            status=OptimizationStatus.COMPLETED,
            config=self.create_test_config(),
            completed_at=old_time
        )
        
        # Add recent completed job
        recent_job_id = uuid4()
        recent_time = datetime.now() - timedelta(hours=1)  # Recent
        
        recent_result = OptimizationResult(
            job_id=recent_job_id,
            mission_id=uuid4(),
            status=OptimizationStatus.COMPLETED,
            config=self.create_test_config(),
            completed_at=recent_time
        )
        
        # Add running job
        running_job_id = uuid4()
        running_result = OptimizationResult(
            job_id=running_job_id,
            mission_id=uuid4(),
            status=OptimizationStatus.RUNNING,
            config=self.create_test_config()
        )
        
        opt_service.active_jobs[old_job_id] = old_result
        opt_service.active_jobs[recent_job_id] = recent_result
        opt_service.active_jobs[running_job_id] = running_result
        
        # Cleanup with 24 hour threshold
        opt_service.cleanup_completed_jobs(max_age_hours=24)
        
        # Old job should be removed
        assert old_job_id not in opt_service.active_jobs
        
        # Recent and running jobs should remain
        assert recent_job_id in opt_service.active_jobs
        assert running_job_id in opt_service.active_jobs
    
    def test_get_active_jobs(self):
        """Test getting list of active jobs."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        # Initially empty
        jobs = opt_service.get_active_jobs()
        assert len(jobs) == 0
        
        # Add some jobs
        from app.services.optimization_service import OptimizationResult
        
        for i in range(3):
            job_id = uuid4()
            result = OptimizationResult(
                job_id=job_id,
                mission_id=uuid4(),
                status=OptimizationStatus.RUNNING,
                config=self.create_test_config()
            )
            opt_service.active_jobs[job_id] = result
        
        jobs = opt_service.get_active_jobs()
        assert len(jobs) == 3
    
    def test_clear_simulation_cache(self):
        """Test clearing simulation cache."""
        sim_service, val_service = self.create_mock_services()
        opt_service = MissionOptimizationService(sim_service, val_service)
        
        # Add some cache entries
        opt_service.simulation_cache["key1"] = Mock()
        opt_service.simulation_cache["key2"] = Mock()
        
        assert len(opt_service.simulation_cache) == 2
        
        # Clear cache
        opt_service.clear_simulation_cache()
        
        assert len(opt_service.simulation_cache) == 0


if __name__ == "__main__":
    pytest.main([__file__])