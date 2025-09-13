"""
Unit tests for Pydantic mission domain models.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from pydantic import ValidationError

from app.models.mission import (
    Mission,
    SpacecraftConfig,
    TrajectoryPlan,
    SimulationResult,
    MissionConstraints,
    MissionTimeline,
    Maneuver,
    RiskFactor,
    DateRange,
    TransferType,
    CelestialBody,
    VehicleType,
    RiskLevel
)


class TestDateRange:
    """Test DateRange model validation."""
    
    def test_valid_date_range(self):
        """Test valid date range creation."""
        start = datetime.now()
        end = start + timedelta(days=30)
        date_range = DateRange(start=start, end=end)
        
        assert date_range.start == start
        assert date_range.end == end
    
    def test_invalid_date_range(self):
        """Test invalid date range (end before start)."""
        start = datetime.now()
        end = start - timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            DateRange(start=start, end=end)
        
        assert "End date must be after start date" in str(exc_info.value)


class TestManeuver:
    """Test Maneuver model validation."""
    
    def test_valid_maneuver(self):
        """Test valid maneuver creation."""
        maneuver = Maneuver(
            name="Trans-lunar injection",
            delta_v_ms=3200.0,
            duration_s=300.0,
            timestamp_days=0.5
        )
        
        assert maneuver.name == "Trans-lunar injection"
        assert maneuver.delta_v_ms == 3200.0
        assert maneuver.duration_s == 300.0
        assert maneuver.timestamp_days == 0.5
    
    def test_excessive_delta_v(self):
        """Test validation of excessive delta-v."""
        with pytest.raises(ValidationError) as exc_info:
            Maneuver(
                name="Impossible maneuver",
                delta_v_ms=15000.0,  # Exceeds typical limits
                duration_s=300.0,
                timestamp_days=0.5
            )
        
        assert "Delta-v exceeds typical chemical propulsion limits" in str(exc_info.value)
    
    def test_negative_values(self):
        """Test validation of negative values."""
        with pytest.raises(ValidationError):
            Maneuver(
                name="Invalid maneuver",
                delta_v_ms=-100.0,  # Negative delta-v
                duration_s=300.0,
                timestamp_days=0.5
            )


class TestSpacecraftConfig:
    """Test SpacecraftConfig model validation."""
    
    def test_valid_spacecraft_config(self):
        """Test valid spacecraft configuration."""
        config = SpacecraftConfig(
            vehicle_type=VehicleType.MEDIUM_SAT,
            name="Test Satellite",
            mass_kg=1000.0,
            fuel_capacity_kg=400.0,
            thrust_n=500.0,
            specific_impulse_s=300.0,
            payload_mass_kg=200.0,
            power_w=2000.0
        )
        
        assert config.vehicle_type == VehicleType.MEDIUM_SAT
        assert config.mass_kg == 1000.0
        assert config.fuel_capacity_kg == 400.0
        assert config.payload_mass_kg == 200.0
    
    def test_payload_mass_validation(self):
        """Test payload mass cannot exceed total mass."""
        with pytest.raises(ValidationError) as exc_info:
            SpacecraftConfig(
                vehicle_type=VehicleType.MEDIUM_SAT,
                name="Invalid Satellite",
                mass_kg=1000.0,
                fuel_capacity_kg=400.0,
                thrust_n=500.0,
                specific_impulse_s=300.0,
                payload_mass_kg=1200.0,  # Exceeds total mass
                power_w=2000.0
            )
        
        assert "Payload mass must be less than total spacecraft mass" in str(exc_info.value)
    
    def test_fuel_capacity_validation(self):
        """Test fuel capacity cannot exceed 90% of total mass."""
        with pytest.raises(ValidationError) as exc_info:
            SpacecraftConfig(
                vehicle_type=VehicleType.MEDIUM_SAT,
                name="Invalid Satellite",
                mass_kg=1000.0,
                fuel_capacity_kg=950.0,  # Exceeds 90% of total mass
                thrust_n=500.0,
                specific_impulse_s=300.0,
                payload_mass_kg=200.0,
                power_w=2000.0
            )
        
        assert "Fuel capacity cannot exceed 90% of total mass" in str(exc_info.value)
    
    def test_mass_ratio_calculation(self):
        """Test mass ratio calculation."""
        config = SpacecraftConfig(
            vehicle_type=VehicleType.MEDIUM_SAT,
            name="Test Satellite",
            mass_kg=1000.0,
            fuel_capacity_kg=400.0,
            thrust_n=500.0,
            specific_impulse_s=300.0,
            payload_mass_kg=200.0
        )
        
        expected_mass_ratio = 1000.0 / (1000.0 - 400.0)  # wet_mass / dry_mass
        assert abs(config.mass_ratio - expected_mass_ratio) < 0.001
    
    def test_thrust_to_weight_ratio(self):
        """Test thrust-to-weight ratio calculation."""
        config = SpacecraftConfig(
            vehicle_type=VehicleType.MEDIUM_SAT,
            name="Test Satellite",
            mass_kg=1000.0,
            fuel_capacity_kg=400.0,
            thrust_n=9810.0,  # Equal to weight at Earth surface
            specific_impulse_s=300.0,
            payload_mass_kg=200.0
        )
        
        assert abs(config.thrust_to_weight_ratio - 1.0) < 0.001


class TestTrajectoryPlan:
    """Test TrajectoryPlan model validation."""
    
    def test_valid_trajectory_plan(self):
        """Test valid trajectory plan creation."""
        launch_window = DateRange(
            start=datetime.now(),
            end=datetime.now() + timedelta(days=30)
        )
        
        maneuvers = [
            Maneuver(name="Launch", delta_v_ms=9500.0, duration_s=600.0, timestamp_days=0.0),
            Maneuver(name="Course correction", delta_v_ms=50.0, duration_s=30.0, timestamp_days=10.0)
        ]
        
        trajectory = TrajectoryPlan(
            launch_window=launch_window,
            departure_body=CelestialBody.EARTH,
            target_body=CelestialBody.MARS,
            transfer_type=TransferType.HOHMANN,
            maneuvers=maneuvers,
            total_delta_v=9550.0,
            flight_time_days=260.0
        )
        
        assert trajectory.departure_body == CelestialBody.EARTH
        assert trajectory.target_body == CelestialBody.MARS
        assert len(trajectory.maneuvers) == 2
        assert trajectory.total_delta_v == 9550.0
    
    def test_same_departure_target_validation(self):
        """Test validation that departure and target bodies must be different."""
        launch_window = DateRange(
            start=datetime.now(),
            end=datetime.now() + timedelta(days=30)
        )
        
        with pytest.raises(ValidationError) as exc_info:
            TrajectoryPlan(
                launch_window=launch_window,
                departure_body=CelestialBody.EARTH,
                target_body=CelestialBody.EARTH,  # Same as departure
                transfer_type=TransferType.HOHMANN,
                maneuvers=[],
                total_delta_v=0.0,
                flight_time_days=1.0
            )
        
        assert "Target body must be different from departure body" in str(exc_info.value)
    
    def test_maneuver_chronological_order(self):
        """Test that maneuvers must be in chronological order."""
        launch_window = DateRange(
            start=datetime.now(),
            end=datetime.now() + timedelta(days=30)
        )
        
        maneuvers = [
            Maneuver(name="Second", delta_v_ms=100.0, duration_s=30.0, timestamp_days=10.0),
            Maneuver(name="First", delta_v_ms=100.0, duration_s=30.0, timestamp_days=5.0)  # Out of order
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            TrajectoryPlan(
                launch_window=launch_window,
                departure_body=CelestialBody.EARTH,
                target_body=CelestialBody.MARS,
                transfer_type=TransferType.HOHMANN,
                maneuvers=maneuvers,
                total_delta_v=200.0,
                flight_time_days=260.0
            )
        
        assert "Maneuvers must be in chronological order" in str(exc_info.value)
    
    def test_delta_v_consistency(self):
        """Test that total delta-v matches sum of maneuvers."""
        launch_window = DateRange(
            start=datetime.now(),
            end=datetime.now() + timedelta(days=30)
        )
        
        maneuvers = [
            Maneuver(name="Launch", delta_v_ms=9500.0, duration_s=600.0, timestamp_days=0.0),
            Maneuver(name="Course correction", delta_v_ms=50.0, duration_s=30.0, timestamp_days=10.0)
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            TrajectoryPlan(
                launch_window=launch_window,
                departure_body=CelestialBody.EARTH,
                target_body=CelestialBody.MARS,
                transfer_type=TransferType.HOHMANN,
                maneuvers=maneuvers,
                total_delta_v=8000.0,  # Doesn't match sum (9550)
                flight_time_days=260.0
            )
        
        assert "Total delta-v does not match sum of maneuvers" in str(exc_info.value)


class TestRiskFactor:
    """Test RiskFactor model validation."""
    
    def test_valid_risk_factor(self):
        """Test valid risk factor creation."""
        risk = RiskFactor(
            category="Technical",
            description="Propulsion system failure",
            probability=0.05,
            impact=RiskLevel.HIGH,
            mitigation="Redundant propulsion systems"
        )
        
        assert risk.category == "Technical"
        assert risk.probability == 0.05
        assert risk.impact == RiskLevel.HIGH
    
    def test_probability_bounds(self):
        """Test probability must be between 0 and 1."""
        with pytest.raises(ValidationError):
            RiskFactor(
                category="Technical",
                description="Test risk",
                probability=1.5,  # Invalid probability
                impact=RiskLevel.LOW
            )


class TestSimulationResult:
    """Test SimulationResult model validation."""
    
    def test_valid_simulation_result(self):
        """Test valid simulation result creation."""
        mission_id = uuid4()
        
        result = SimulationResult(
            mission_id=mission_id,
            success_probability=0.85,
            total_duration_days=260.0,
            fuel_consumption_kg=800.0,
            cost_estimate_usd=50000000.0,
            performance_metrics={"efficiency": 0.9, "accuracy": 0.95}
        )
        
        assert result.mission_id == mission_id
        assert result.success_probability == 0.85
        assert result.total_duration_days == 260.0
        assert "efficiency" in result.performance_metrics
    
    def test_performance_metrics_validation(self):
        """Test performance metrics must contain finite values."""
        mission_id = uuid4()
        
        with pytest.raises(ValidationError) as exc_info:
            SimulationResult(
                mission_id=mission_id,
                success_probability=0.85,
                total_duration_days=260.0,
                fuel_consumption_kg=800.0,
                cost_estimate_usd=50000000.0,
                performance_metrics={"efficiency": float('inf')}  # Invalid infinite value
            )
        
        assert "Performance metric efficiency must be finite" in str(exc_info.value)


class TestMission:
    """Test Mission model validation and methods."""
    
    def create_valid_mission(self) -> Mission:
        """Helper to create a valid mission for testing."""
        spacecraft_config = SpacecraftConfig(
            vehicle_type=VehicleType.MEDIUM_SAT,
            name="Test Satellite",
            mass_kg=1000.0,
            fuel_capacity_kg=400.0,
            thrust_n=500.0,
            specific_impulse_s=300.0,
            payload_mass_kg=200.0
        )
        
        launch_window = DateRange(
            start=datetime.now(),
            end=datetime.now() + timedelta(days=30)
        )
        
        trajectory = TrajectoryPlan(
            launch_window=launch_window,
            departure_body=CelestialBody.EARTH,
            target_body=CelestialBody.MARS,
            transfer_type=TransferType.HOHMANN,
            maneuvers=[
                Maneuver(name="Launch", delta_v_ms=9500.0, duration_s=600.0, timestamp_days=0.0)
            ],
            total_delta_v=9500.0,
            flight_time_days=260.0
        )
        
        timeline = MissionTimeline(
            launch_date=datetime.now(),
            major_milestones=[
                {"name": "Launch", "date": datetime.now(), "description": "Mission launch"}
            ]
        )
        
        constraints = MissionConstraints()
        
        return Mission(
            name="Mars Sample Return",
            description="A mission to collect samples from Mars and return them to Earth",
            objectives=["Collect soil samples", "Return to Earth", "Analyze samples"],
            spacecraft_config=spacecraft_config,
            trajectory=trajectory,
            timeline=timeline,
            constraints=constraints
        )
    
    def test_valid_mission_creation(self):
        """Test valid mission creation."""
        mission = self.create_valid_mission()
        
        assert mission.name == "Mars Sample Return"
        assert len(mission.objectives) == 3
        assert mission.spacecraft_config.vehicle_type == VehicleType.MEDIUM_SAT
        assert mission.trajectory.target_body == CelestialBody.MARS
    
    def test_objectives_validation(self):
        """Test objectives validation."""
        mission_data = self.create_valid_mission().model_dump()
        mission_data['objectives'] = ["a"]  # Less than 5 characters
        
        with pytest.raises(ValidationError) as exc_info:
            Mission(**mission_data)
        
        assert "Each objective must be at least 5 characters long" in str(exc_info.value)
    
    def test_mission_complexity_calculation(self):
        """Test mission complexity calculation."""
        mission = self.create_valid_mission()
        complexity = mission.calculate_mission_complexity()
        
        assert isinstance(complexity, float)
        assert 0.0 <= complexity <= 5.0
    
    def test_mission_feasibility_validation(self):
        """Test mission feasibility validation."""
        mission = self.create_valid_mission()
        
        # Create an infeasible mission by modifying the spacecraft to have insufficient delta-v capability
        # Reduce fuel capacity to make the mission infeasible
        mission.spacecraft_config.fuel_capacity_kg = 50.0  # Very low fuel capacity
        mission.trajectory.total_delta_v = 9500.0  # High delta-v requirement
        
        issues = mission.validate_mission_feasibility()
        
        assert len(issues) > 0
        assert any("Insufficient delta-v capability" in issue for issue in issues)
    
    def test_updated_at_validation(self):
        """Test that updated_at cannot be before created_at."""
        mission_data = self.create_valid_mission().model_dump()
        created_time = datetime.now()
        updated_time = created_time - timedelta(hours=1)  # Before created time
        
        mission_data['created_at'] = created_time
        mission_data['updated_at'] = updated_time
        
        with pytest.raises(ValidationError) as exc_info:
            Mission(**mission_data)
        
        assert "Updated timestamp cannot be before created timestamp" in str(exc_info.value)


class TestMissionTimeline:
    """Test MissionTimeline model validation."""
    
    def test_valid_timeline(self):
        """Test valid timeline creation."""
        timeline = MissionTimeline(
            launch_date=datetime.now(),
            major_milestones=[
                {
                    "name": "Launch",
                    "date": datetime.now(),
                    "description": "Mission launch from Earth"
                }
            ]
        )
        
        assert len(timeline.major_milestones) == 1
        assert timeline.major_milestones[0]["name"] == "Launch"
    
    def test_milestone_validation(self):
        """Test milestone validation requires specific fields."""
        with pytest.raises(ValidationError) as exc_info:
            MissionTimeline(
                launch_date=datetime.now(),
                major_milestones=[
                    {"name": "Launch"}  # Missing required fields
                ]
            )
        
        assert "Milestone must contain fields" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])