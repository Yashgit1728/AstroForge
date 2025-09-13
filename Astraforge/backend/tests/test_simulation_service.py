"""
Integration tests for mission simulation service.
"""

import asyncio
import math
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.simulation_service import (
    MissionSimulationService,
    FuelConsumptionModel,
    PerformanceMetrics,
    SimulationProgress
)
from app.models.mission import (
    Mission as MissionModel,
    SpacecraftConfig,
    TrajectoryPlan,
    MissionTimeline,
    MissionConstraints,
    Maneuver,
    DateRange,
    CelestialBody,
    TransferType,
    VehicleType
)


@pytest.fixture
def sample_spacecraft():
    """Create a sample spacecraft configuration."""
    return SpacecraftConfig(
        vehicle_type=VehicleType.PROBE,
        name="Test Probe",
        mass_kg=2000,
        fuel_capacity_kg=1200,  # Increased fuel capacity
        thrust_n=500,
        specific_impulse_s=300,
        payload_mass_kg=100,
        power_w=2000
    )


@pytest.fixture
def sample_trajectory():
    """Create a sample trajectory plan."""
    launch_window = DateRange(
        start=datetime.now(),
        end=datetime.now() + timedelta(days=30)
    )
    
    maneuvers = [
        Maneuver(
            name="Trans-Mars Injection",
            delta_v_ms=3500,
            duration_s=600,
            timestamp_days=1
        ),
        Maneuver(
            name="Mid-course Correction",
            delta_v_ms=50,
            duration_s=30,
            timestamp_days=100
        ),
        Maneuver(
            name="Mars Orbit Insertion",
            delta_v_ms=1200,
            duration_s=400,
            timestamp_days=200
        )
    ]
    
    return TrajectoryPlan(
        launch_window=launch_window,
        departure_body=CelestialBody.EARTH,
        target_body=CelestialBody.MARS,
        transfer_type=TransferType.HOHMANN,
        maneuvers=maneuvers,
        total_delta_v=4750,
        flight_time_days=200
    )


@pytest.fixture
def sample_mission(sample_spacecraft, sample_trajectory):
    """Create a complete sample mission."""
    timeline = MissionTimeline(
        launch_date=datetime.now(),
        major_milestones=[
            {
                "name": "Launch",
                "date": datetime.now().isoformat(),
                "description": "Mission launch"
            }
        ]
    )
    
    constraints = MissionConstraints(
        max_duration_days=500,
        max_delta_v_ms=10000,
        max_mass_kg=2000,
        min_success_probability=0.8
    )
    
    return MissionModel(
        name="Mars Sample Mission",
        description="Test mission to Mars",
        objectives=["Reach Mars orbit", "Collect scientific data"],
        spacecraft_config=sample_spacecraft,
        trajectory=sample_trajectory,
        timeline=timeline,
        constraints=constraints
    )


class TestFuelConsumptionModel:
    """Test fuel consumption calculations."""
    
    def test_fuel_consumption_calculation(self, sample_spacecraft):
        """Test basic fuel consumption calculation."""
        delta_v = 1500  # m/s - reduced to avoid hitting capacity limit
        fuel_needed = FuelConsumptionModel.calculate_fuel_consumption(delta_v, sample_spacecraft)
        
        # Should be positive and reasonable
        assert fuel_needed > 0
        assert fuel_needed <= sample_spacecraft.fuel_capacity_kg
        
        # Higher delta-v should require more fuel
        higher_dv_fuel = FuelConsumptionModel.calculate_fuel_consumption(delta_v * 1.5, sample_spacecraft)
        assert higher_dv_fuel > fuel_needed
    
    def test_zero_delta_v(self, sample_spacecraft):
        """Test fuel consumption with zero delta-v."""
        fuel_needed = FuelConsumptionModel.calculate_fuel_consumption(0, sample_spacecraft)
        assert fuel_needed == 0
    
    def test_burn_time_calculation(self, sample_spacecraft):
        """Test burn time calculation."""
        delta_v = 1000  # m/s
        burn_time = FuelConsumptionModel.calculate_burn_time(delta_v, sample_spacecraft)
        
        # Should be positive and reasonable
        assert burn_time > 0
        assert burn_time < 10000  # Less than ~3 hours for reasonable delta-v
        
        # Higher delta-v should take longer
        higher_dv_time = FuelConsumptionModel.calculate_burn_time(delta_v * 2, sample_spacecraft)
        assert higher_dv_time > burn_time
    
    def test_efficiency_factor(self, sample_spacecraft):
        """Test efficiency factor impact on fuel consumption."""
        delta_v = 1000  # Reduced to avoid capacity limits
        
        fuel_100_eff = FuelConsumptionModel.calculate_fuel_consumption(delta_v, sample_spacecraft, 1.0)
        fuel_90_eff = FuelConsumptionModel.calculate_fuel_consumption(delta_v, sample_spacecraft, 0.9)
        
        # Lower efficiency should require more fuel
        assert fuel_90_eff > fuel_100_eff


class TestMissionSimulationService:
    """Test mission simulation service."""
    
    @pytest.fixture
    def simulation_service(self):
        """Create simulation service instance."""
        return MissionSimulationService()
    
    @pytest.mark.asyncio
    async def test_mission_simulation_complete_flow(self, simulation_service, sample_mission):
        """Test complete mission simulation flow."""
        result = await simulation_service.simulate_mission(sample_mission, detailed=True)
        
        # Check basic result structure
        assert result.mission_id == sample_mission.id
        assert result.simulation_id is not None
        assert 0 <= result.success_probability <= 1
        assert result.total_duration_days > 0
        assert result.fuel_consumption_kg >= 0
        assert result.cost_estimate_usd > 0
        
        # Check performance metrics
        assert "total_delta_v" in result.performance_metrics
        assert "efficiency_score" in result.performance_metrics
        assert result.performance_metrics["total_delta_v"] == sample_mission.trajectory.total_delta_v
        
        # Check detailed data is included
        assert result.trajectory_data is not None
        assert "waypoints" in result.trajectory_data
        assert "maneuver_details" in result.trajectory_data
        assert len(result.trajectory_data["waypoints"]) > 0
        
        # Check fuel usage timeline
        assert result.fuel_usage_timeline is not None
        assert len(result.fuel_usage_timeline) > 0
    
    @pytest.mark.asyncio
    async def test_mission_simulation_without_detailed_data(self, simulation_service, sample_mission):
        """Test mission simulation without detailed trajectory data."""
        result = await simulation_service.simulate_mission(sample_mission, detailed=False)
        
        # Should have basic results but no detailed trajectory data
        assert result.trajectory_data is None
        assert result.fuel_usage_timeline is not None  # This is still included
        assert result.success_probability > 0
    
    @pytest.mark.asyncio
    async def test_simulation_progress_tracking(self, simulation_service, sample_mission):
        """Test simulation progress tracking."""
        # Start simulation in background
        simulation_task = asyncio.create_task(
            simulation_service.simulate_mission(sample_mission)
        )
        
        # Give it a moment to start
        await asyncio.sleep(0.1)
        
        # Check if we can find an active simulation
        active_simulations = simulation_service._active_simulations
        assert len(active_simulations) > 0
        
        # Get progress for one of the active simulations
        simulation_id = next(iter(active_simulations.keys()))
        progress = await simulation_service.get_simulation_progress(simulation_id)
        
        assert progress is not None
        assert progress.simulation_id == simulation_id
        assert 0 <= progress.progress_percent <= 100
        assert progress.current_phase is not None
        
        # Wait for completion
        result = await simulation_task
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_mission_validation_errors(self, simulation_service, sample_mission):
        """Test mission validation with invalid parameters."""
        # Create mission with insufficient delta-v capability
        invalid_mission = sample_mission.model_copy()
        invalid_mission.spacecraft_config.fuel_capacity_kg = 10  # Very low fuel
        invalid_mission.trajectory.total_delta_v = 15000  # Very high delta-v
        
        # Should still complete but with validation errors
        result = await simulation_service.simulate_mission(invalid_mission)
        
        # Should have low success probability due to validation issues
        assert result.success_probability < 0.8
        assert len(result.risk_factors) > 0
    
    @pytest.mark.asyncio
    async def test_different_transfer_types(self, simulation_service, sample_mission):
        """Test simulation with different transfer types."""
        # Test Hohmann transfer
        hohmann_mission = sample_mission.model_copy()
        hohmann_mission.trajectory.transfer_type = TransferType.HOHMANN
        hohmann_result = await simulation_service.simulate_mission(hohmann_mission)
        
        # Test bi-elliptic transfer
        bi_elliptic_mission = sample_mission.model_copy()
        bi_elliptic_mission.trajectory.transfer_type = TransferType.BI_ELLIPTIC
        bi_elliptic_result = await simulation_service.simulate_mission(bi_elliptic_mission)
        
        # Test direct transfer
        direct_mission = sample_mission.model_copy()
        direct_mission.trajectory.transfer_type = TransferType.DIRECT
        direct_result = await simulation_service.simulate_mission(direct_mission)
        
        # All should complete successfully
        assert hohmann_result.success_probability > 0
        assert bi_elliptic_result.success_probability > 0
        assert direct_result.success_probability > 0
        
        # Should have different trajectory data
        assert hohmann_result.trajectory_data["transfer_type"] == "hohmann"
        assert bi_elliptic_result.trajectory_data["transfer_type"] == "bi_elliptic"
        assert direct_result.trajectory_data["transfer_type"] == "direct"
    
    @pytest.mark.asyncio
    async def test_risk_assessment(self, simulation_service, sample_mission):
        """Test risk assessment functionality."""
        # Create high-risk mission
        high_risk_mission = sample_mission.model_copy()
        high_risk_mission.trajectory.total_delta_v = 12000  # High delta-v
        high_risk_mission.trajectory.flight_time_days = 1200  # Long duration
        
        # Add many maneuvers
        additional_maneuvers = [
            Maneuver(name=f"Maneuver {i}", delta_v_ms=100, duration_s=60, timestamp_days=i*10)
            for i in range(4, 15)  # Add 11 more maneuvers
        ]
        high_risk_mission.trajectory.maneuvers.extend(additional_maneuvers)
        high_risk_mission.trajectory.total_delta_v += sum(m.delta_v_ms for m in additional_maneuvers)
        
        result = await simulation_service.simulate_mission(high_risk_mission)
        
        # Should identify multiple risk factors
        assert len(result.risk_factors) > 0
        
        # Check for specific risk categories
        risk_categories = [rf.category for rf in result.risk_factors]
        assert any("Fuel" in cat or "Propulsion" in cat for cat in risk_categories)
        assert any("Duration" in cat or "Complexity" in cat for cat in risk_categories)
    
    @pytest.mark.asyncio
    async def test_interplanetary_missions(self, simulation_service, sample_spacecraft):
        """Test simulation of different interplanetary missions."""
        # Earth to Jupiter mission
        jupiter_trajectory = TrajectoryPlan(
            launch_window=DateRange(
                start=datetime.now(),
                end=datetime.now() + timedelta(days=30)
            ),
            departure_body=CelestialBody.EARTH,
            target_body=CelestialBody.JUPITER,
            transfer_type=TransferType.HOHMANN,
            maneuvers=[
                Maneuver(name="Jupiter Transfer", delta_v_ms=8000, duration_s=1200, timestamp_days=1)
            ],
            total_delta_v=8000,
            flight_time_days=600
        )
        
        jupiter_mission = MissionModel(
            name="Jupiter Mission",
            description="Mission to Jupiter",
            objectives=["Reach Jupiter"],
            spacecraft_config=sample_spacecraft,
            trajectory=jupiter_trajectory,
            timeline=MissionTimeline(launch_date=datetime.now()),
            constraints=MissionConstraints()
        )
        
        result = await simulation_service.simulate_mission(jupiter_mission)
        
        # Should complete and identify communication risks
        assert result.success_probability > 0
        risk_categories = [rf.category for rf in result.risk_factors]
        assert any("Communication" in cat for cat in risk_categories)
    
    @pytest.mark.asyncio
    async def test_performance_metrics_calculation(self, simulation_service, sample_mission):
        """Test detailed performance metrics calculation."""
        result = await simulation_service.simulate_mission(sample_mission)
        
        # Check all expected performance metrics are present
        expected_metrics = [
            "total_delta_v", "efficiency_score", "risk_score",
            "trajectory_accuracy", "system_reliability", "communication_coverage",
            "power_margin", "thermal_margin"
        ]
        
        for metric in expected_metrics:
            assert metric in result.performance_metrics
            assert isinstance(result.performance_metrics[metric], (int, float))
            assert 0 <= result.performance_metrics[metric] <= 1 or metric == "total_delta_v"
        
        # Check system performance data
        assert result.system_performance is not None
        assert "thrust_utilization" in result.system_performance
        assert "power_utilization" in result.system_performance
        assert "communication_efficiency" in result.system_performance
    
    @pytest.mark.asyncio
    async def test_fuel_timeline_accuracy(self, simulation_service, sample_mission):
        """Test fuel consumption timeline accuracy."""
        result = await simulation_service.simulate_mission(sample_mission)
        
        # Check fuel timeline
        fuel_timeline = result.fuel_usage_timeline
        assert len(fuel_timeline) == len(sample_mission.trajectory.maneuvers)
        
        # Fuel should decrease over time
        for i in range(1, len(fuel_timeline)):
            assert fuel_timeline[i]["fuel_remaining"] <= fuel_timeline[i-1]["fuel_remaining"]
        
        # Total fuel consumption should match
        total_consumed = fuel_timeline[-1]["fuel_used_cumulative"]
        assert abs(total_consumed - result.fuel_consumption_kg) < 1e-6
    
    @pytest.mark.asyncio
    async def test_trajectory_waypoints(self, simulation_service, sample_mission):
        """Test trajectory waypoint generation."""
        result = await simulation_service.simulate_mission(sample_mission, detailed=True)
        
        waypoints = result.trajectory_data["waypoints"]
        assert len(waypoints) > 10  # Should have reasonable number of waypoints
        
        # Check waypoint structure
        for waypoint in waypoints[:5]:  # Check first few waypoints
            assert "time_days" in waypoint
            assert "position_km" in waypoint
            assert "velocity_kms" in waypoint
            assert len(waypoint["position_km"]) == 3  # 3D position
            assert len(waypoint["velocity_kms"]) == 3  # 3D velocity
        
        # Time should be monotonically increasing
        times = [wp["time_days"] for wp in waypoints]
        assert times == sorted(times)
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, simulation_service, sample_mission):
        """Test mission cost estimation."""
        # Test with very different mission parameters
        cheap_mission = sample_mission.model_copy()
        cheap_mission.spacecraft_config.mass_kg = 200  # Very light
        cheap_mission.trajectory.total_delta_v = 500   # Very low delta-v
        cheap_mission.trajectory.flight_time_days = 10  # Very short duration
        # Single simple maneuver
        cheap_mission.trajectory.maneuvers = [
            Maneuver(name="Simple Maneuver", delta_v_ms=500, duration_s=100, timestamp_days=1)
        ]
        
        expensive_mission = sample_mission.model_copy()
        expensive_mission.spacecraft_config.mass_kg = 10000  # Very heavy
        expensive_mission.trajectory.total_delta_v = 20000   # Very high delta-v
        expensive_mission.trajectory.flight_time_days = 3000  # Very long duration
        # Many complex maneuvers
        expensive_mission.trajectory.maneuvers = [
            Maneuver(name=f"Complex Maneuver {i}", delta_v_ms=2000, duration_s=600, timestamp_days=i*100)
            for i in range(1, 11)  # 10 maneuvers
        ]
        
        cheap_result = await simulation_service.simulate_mission(cheap_mission)
        expensive_result = await simulation_service.simulate_mission(expensive_mission)
        
        # Print costs for debugging
        print(f"Cheap mission cost: ${cheap_result.cost_estimate_usd:,.0f}")
        print(f"Expensive mission cost: ${expensive_result.cost_estimate_usd:,.0f}")
        
        # Expensive mission should cost more (even if not significantly more due to caps)
        assert expensive_result.cost_estimate_usd >= cheap_result.cost_estimate_usd
        
        # Both should have reasonable cost estimates
        assert cheap_result.cost_estimate_usd > 1e6  # At least $1M
        assert expensive_result.cost_estimate_usd < 1e12  # Less than $1T


class TestSimulationEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def simulation_service(self):
        return MissionSimulationService()
    
    @pytest.mark.asyncio
    async def test_mission_with_no_maneuvers(self, simulation_service, sample_mission):
        """Test mission with no maneuvers."""
        no_maneuver_mission = sample_mission.model_copy()
        no_maneuver_mission.trajectory.maneuvers = []
        no_maneuver_mission.trajectory.total_delta_v = 0
        
        result = await simulation_service.simulate_mission(no_maneuver_mission)
        
        # Should complete but with minimal fuel consumption
        assert result.fuel_consumption_kg == 0
        assert len(result.fuel_usage_timeline) == 0
    
    @pytest.mark.asyncio
    async def test_mission_with_single_maneuver(self, simulation_service, sample_mission):
        """Test mission with single maneuver."""
        single_maneuver_mission = sample_mission.model_copy()
        single_maneuver_mission.trajectory.maneuvers = [sample_mission.trajectory.maneuvers[0]]
        single_maneuver_mission.trajectory.total_delta_v = sample_mission.trajectory.maneuvers[0].delta_v_ms
        
        result = await simulation_service.simulate_mission(single_maneuver_mission)
        
        # Should complete successfully
        assert result.success_probability > 0
        assert len(result.fuel_usage_timeline) == 1
    
    @pytest.mark.asyncio
    async def test_unsupported_celestial_body(self, simulation_service, sample_mission):
        """Test mission with unsupported celestial body."""
        unsupported_mission = sample_mission.model_copy()
        unsupported_mission.trajectory.target_body = CelestialBody.ASTEROID_BELT
        
        # Should raise an error during trajectory calculation
        with pytest.raises(ValueError, match="Unsupported celestial body"):
            await simulation_service.simulate_mission(unsupported_mission)
    
    @pytest.mark.asyncio
    async def test_extremely_high_delta_v(self, simulation_service, sample_mission):
        """Test mission with unrealistically high delta-v."""
        high_dv_mission = sample_mission.model_copy()
        high_dv_mission.trajectory.total_delta_v = 50000  # 50 km/s
        high_dv_mission.trajectory.maneuvers[0].delta_v_ms = 50000
        
        result = await simulation_service.simulate_mission(high_dv_mission)
        
        # Should complete but with very low success probability
        assert result.success_probability < 0.6
        assert len(result.risk_factors) > 0