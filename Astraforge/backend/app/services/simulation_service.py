"""
Mission simulation service for physics-based mission analysis.

This service implements comprehensive mission simulation including:
- Physics-based trajectory calculation
- Fuel consumption modeling
- Performance metric calculation
- Timeline generation
- Progress tracking for long-running simulations
"""

import asyncio
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field

import numpy as np
from pydantic import BaseModel

from ..models.mission import (
    Mission as MissionModel,
    SimulationResult as SimulationResultModel,
    SpacecraftConfig,
    TrajectoryPlan,
    Maneuver,
    RiskFactor,
    CelestialBody,
    TransferType,
    RiskLevel
)
from ..physics.orbital_mechanics import (
    OrbitalMechanics,
    DeltaVCalculator,
    TrajectoryCalculator,
    CELESTIAL_BODIES
)


@dataclass
class SimulationProgress:
    """Progress tracking for simulation execution."""
    simulation_id: UUID
    progress_percent: float = 0.0
    current_phase: str = "initializing"
    phases_completed: List[str] = field(default_factory=list)
    estimated_completion_time: Optional[datetime] = None
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class FuelConsumptionModel:
    """Fuel consumption modeling for spacecraft."""
    
    @staticmethod
    def calculate_fuel_consumption(delta_v: float, spacecraft: SpacecraftConfig, 
                                 efficiency_factor: float = 0.95) -> float:
        """
        Calculate fuel consumption using rocket equation.
        
        Args:
            delta_v: Required delta-v in m/s
            spacecraft: Spacecraft configuration
            efficiency_factor: Engine efficiency (0-1)
        
        Returns:
            Fuel consumption in kg
        """
        if delta_v <= 0:
            return 0.0
        
        # Effective specific impulse accounting for efficiency
        isp_eff = spacecraft.specific_impulse_s * efficiency_factor
        
        # Rocket equation: Δv = Isp * g0 * ln(m0/m1)
        # Rearranged: m1 = m0 / exp(Δv / (Isp * g0))
        g0 = 9.81  # Standard gravity
        
        mass_ratio = math.exp(delta_v / (isp_eff * g0))
        
        # Calculate fuel needed
        dry_mass = spacecraft.mass_kg - spacecraft.fuel_capacity_kg
        wet_mass_needed = dry_mass * mass_ratio
        fuel_needed = wet_mass_needed - dry_mass
        
        # Ensure we don't exceed fuel capacity and handle edge cases
        if fuel_needed <= 0:
            return 0.0
        
        return min(fuel_needed, spacecraft.fuel_capacity_kg)
    
    @staticmethod
    def calculate_burn_time(delta_v: float, spacecraft: SpacecraftConfig) -> float:
        """
        Calculate burn time for maneuver.
        
        Args:
            delta_v: Required delta-v in m/s
            spacecraft: Spacecraft configuration
        
        Returns:
            Burn time in seconds
        """
        if delta_v <= 0 or spacecraft.thrust_n <= 0:
            return 0.0
        
        # Simplified calculation assuming constant mass
        # More accurate would account for changing mass during burn
        acceleration = spacecraft.thrust_n / spacecraft.mass_kg
        return delta_v / acceleration


@dataclass
class PerformanceMetrics:
    """Mission performance metrics."""
    total_delta_v: float
    fuel_consumption_kg: float
    mission_duration_days: float
    success_probability: float
    cost_estimate_usd: float
    efficiency_score: float
    risk_score: float
    
    # Detailed metrics
    trajectory_accuracy: float = 0.95
    system_reliability: float = 0.90
    communication_coverage: float = 0.85
    power_margin: float = 0.20
    thermal_margin: float = 0.15


class MissionSimulationService:
    """Service for comprehensive mission simulation."""
    
    def __init__(self):
        self._active_simulations: Dict[UUID, SimulationProgress] = {}
        self._simulation_cache: Dict[str, SimulationResultModel] = {}
    
    async def simulate_mission(self, mission: MissionModel, 
                             detailed: bool = True) -> SimulationResultModel:
        """
        Run comprehensive mission simulation.
        
        Args:
            mission: Mission specification to simulate
            detailed: Whether to include detailed trajectory data
        
        Returns:
            Simulation results with performance metrics
        """
        simulation_id = uuid4()
        progress = SimulationProgress(simulation_id=simulation_id)
        self._active_simulations[simulation_id] = progress
        
        try:
            # Phase 1: Validate mission parameters
            progress.current_phase = "validation"
            progress.progress_percent = 10.0
            validation_results = await self._validate_mission_parameters(mission)
            progress.phases_completed.append("validation")
            progress.intermediate_results["validation"] = validation_results
            
            # Phase 2: Calculate trajectory
            progress.current_phase = "trajectory_calculation"
            progress.progress_percent = 30.0
            trajectory_data = await self._calculate_detailed_trajectory(mission)
            progress.phases_completed.append("trajectory_calculation")
            progress.intermediate_results["trajectory"] = trajectory_data
            
            # Phase 3: Fuel consumption analysis
            progress.current_phase = "fuel_analysis"
            progress.progress_percent = 50.0
            fuel_data = await self._analyze_fuel_consumption(mission, trajectory_data)
            progress.phases_completed.append("fuel_analysis")
            progress.intermediate_results["fuel"] = fuel_data
            
            # Phase 4: Performance metrics calculation
            progress.current_phase = "performance_metrics"
            progress.progress_percent = 70.0
            performance = await self._calculate_performance_metrics(mission, trajectory_data, fuel_data)
            progress.phases_completed.append("performance_metrics")
            progress.intermediate_results["performance"] = performance
            
            # Phase 5: Risk assessment
            progress.current_phase = "risk_assessment"
            progress.progress_percent = 85.0
            risk_factors = await self._assess_mission_risks(mission, performance)
            progress.phases_completed.append("risk_assessment")
            progress.intermediate_results["risks"] = risk_factors
            
            # Phase 6: Generate final results
            progress.current_phase = "finalization"
            progress.progress_percent = 95.0
            
            # Create simulation result
            result = SimulationResultModel(
                mission_id=mission.id,
                simulation_id=simulation_id,
                success_probability=performance.success_probability,
                total_duration_days=performance.mission_duration_days,
                fuel_consumption_kg=performance.fuel_consumption_kg,
                cost_estimate_usd=performance.cost_estimate_usd,
                risk_factors=risk_factors,
                performance_metrics={
                    "total_delta_v": performance.total_delta_v,
                    "efficiency_score": performance.efficiency_score,
                    "risk_score": performance.risk_score,
                    "trajectory_accuracy": performance.trajectory_accuracy,
                    "system_reliability": performance.system_reliability,
                    "communication_coverage": performance.communication_coverage,
                    "power_margin": performance.power_margin,
                    "thermal_margin": performance.thermal_margin
                },
                trajectory_data=trajectory_data if detailed else None,
                fuel_usage_timeline=fuel_data.get("timeline"),
                system_performance={
                    "thrust_utilization": fuel_data.get("thrust_utilization", 0.8),
                    "power_utilization": 0.7,
                    "communication_efficiency": 0.85
                }
            )
            
            progress.current_phase = "completed"
            progress.progress_percent = 100.0
            progress.phases_completed.append("finalization")
            
            return result
            
        except Exception as e:
            progress.errors.append(str(e))
            progress.current_phase = "error"
            raise
        
        finally:
            # Keep simulation in cache for a while for progress queries
            await asyncio.sleep(1)  # Brief delay to allow final progress check
    
    async def get_simulation_progress(self, simulation_id: UUID) -> Optional[SimulationProgress]:
        """Get current simulation progress."""
        return self._active_simulations.get(simulation_id)
    
    async def _validate_mission_parameters(self, mission: MissionModel) -> Dict[str, Any]:
        """Validate mission parameters for simulation feasibility."""
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "feasibility_score": 1.0
        }
        
        # Check spacecraft delta-v capability
        theoretical_dv = (mission.spacecraft_config.specific_impulse_s * 9.81 * 
                         math.log(mission.spacecraft_config.mass_ratio))
        
        if theoretical_dv < mission.trajectory.total_delta_v:
            validation_results["errors"].append(
                f"Insufficient delta-v: need {mission.trajectory.total_delta_v:.0f} m/s, "
                f"have {theoretical_dv:.0f} m/s"
            )
            validation_results["is_valid"] = False
            validation_results["feasibility_score"] *= 0.3
        
        # Check thrust-to-weight ratio
        if mission.spacecraft_config.thrust_to_weight_ratio < 0.05:
            validation_results["warnings"].append(
                "Very low thrust-to-weight ratio may cause extended burn times"
            )
            validation_results["feasibility_score"] *= 0.8
        
        # Check mission duration constraints
        if mission.trajectory.flight_time_days > mission.constraints.max_duration_days:
            validation_results["errors"].append(
                f"Mission duration exceeds constraints: {mission.trajectory.flight_time_days:.0f} > "
                f"{mission.constraints.max_duration_days:.0f} days"
            )
            validation_results["is_valid"] = False
            validation_results["feasibility_score"] *= 0.5
        
        # Check maneuver chronology
        timestamps = [m.timestamp_days for m in mission.trajectory.maneuvers]
        if timestamps != sorted(timestamps):
            validation_results["errors"].append("Maneuvers are not in chronological order")
            validation_results["is_valid"] = False
        
        return validation_results
    
    async def _calculate_detailed_trajectory(self, mission: MissionModel) -> Dict[str, Any]:
        """Calculate detailed trajectory with orbital mechanics."""
        trajectory_data = {
            "waypoints": [],
            "orbital_elements": [],
            "maneuver_details": [],
            "total_distance": 0.0,
            "accuracy_metrics": {}
        }
        
        # Get celestial body data
        dep_body = CELESTIAL_BODIES.get(mission.trajectory.departure_body)
        tgt_body = CELESTIAL_BODIES.get(mission.trajectory.target_body)
        
        if not dep_body or not tgt_body:
            raise ValueError("Unsupported celestial body in trajectory")
        
        # Calculate transfer trajectory
        if mission.trajectory.transfer_type == TransferType.HOHMANN:
            transfer_data = self._calculate_hohmann_trajectory(mission, dep_body, tgt_body)
        elif mission.trajectory.transfer_type == TransferType.BI_ELLIPTIC:
            transfer_data = self._calculate_bi_elliptic_trajectory(mission, dep_body, tgt_body)
        else:
            transfer_data = self._calculate_direct_trajectory(mission, dep_body, tgt_body)
        
        trajectory_data.update(transfer_data)
        
        # Calculate detailed maneuver information
        for i, maneuver in enumerate(mission.trajectory.maneuvers):
            burn_time = FuelConsumptionModel.calculate_burn_time(
                maneuver.delta_v_ms, mission.spacecraft_config
            )
            
            maneuver_detail = {
                "index": i,
                "name": maneuver.name,
                "delta_v": maneuver.delta_v_ms,
                "burn_time": burn_time,
                "timestamp": maneuver.timestamp_days,
                "fuel_consumption": FuelConsumptionModel.calculate_fuel_consumption(
                    maneuver.delta_v_ms, mission.spacecraft_config
                )
            }
            trajectory_data["maneuver_details"].append(maneuver_detail)
        
        # Calculate accuracy metrics
        trajectory_data["accuracy_metrics"] = {
            "position_accuracy_km": 10.0,  # Typical navigation accuracy
            "velocity_accuracy_ms": 0.1,
            "timing_accuracy_s": 60.0,
            "total_error_budget": 0.05  # 5% total error
        }
        
        return trajectory_data
    
    def _calculate_hohmann_trajectory(self, mission: MissionModel, 
                                    dep_body: Dict, tgt_body: Dict) -> Dict[str, Any]:
        """Calculate Hohmann transfer trajectory details."""
        # Simplified calculation for demonstration
        # In reality, this would involve complex orbital mechanics
        
        r1 = dep_body.get('orbital_radius', 1.0e8)
        r2 = tgt_body.get('orbital_radius', 1.5e8)
        mu = 1.32712440018e20  # Sun's gravitational parameter
        
        # Calculate transfer orbit
        a_transfer = (r1 + r2) / 2
        transfer_time = math.pi * math.sqrt(a_transfer**3 / mu)
        
        # Generate waypoints
        waypoints = []
        num_points = 50
        
        # Use first maneuver timestamp if available, otherwise start at day 0
        start_time = mission.trajectory.maneuvers[0].timestamp_days if mission.trajectory.maneuvers else 0.0
        
        for i in range(num_points + 1):
            t_frac = i / num_points
            # Simplified elliptical trajectory
            angle = math.pi * t_frac
            r = a_transfer * (1 - 0.1**2) / (1 + 0.1 * math.cos(angle))
            
            waypoints.append({
                "time_days": start_time + (transfer_time / 86400) * t_frac,
                "position_km": [r * math.cos(angle) / 1000, r * math.sin(angle) / 1000, 0],
                "velocity_kms": [
                    -math.sqrt(mu / a_transfer) * math.sin(angle) / 1000,
                    math.sqrt(mu / a_transfer) * (0.1 + math.cos(angle)) / 1000,
                    0
                ]
            })
        
        return {
            "waypoints": waypoints,
            "transfer_type": "hohmann",
            "transfer_time_days": transfer_time / 86400,
            "total_distance": math.pi * a_transfer
        }
    
    def _calculate_bi_elliptic_trajectory(self, mission: MissionModel,
                                        dep_body: Dict, tgt_body: Dict) -> Dict[str, Any]:
        """Calculate bi-elliptic transfer trajectory details."""
        # Simplified bi-elliptic calculation
        r1 = dep_body.get('orbital_radius', 1.0e8)
        r2 = tgt_body.get('orbital_radius', 1.5e8)
        r3 = 3 * max(r1, r2)  # Intermediate radius
        mu = 1.32712440018e20
        
        # Two transfer phases
        a1 = (r1 + r3) / 2
        a2 = (r3 + r2) / 2
        t1 = math.pi * math.sqrt(a1**3 / mu)
        t2 = math.pi * math.sqrt(a2**3 / mu)
        total_time = t1 + t2
        
        # Generate waypoints for both phases
        waypoints = []
        
        # Use first maneuver timestamp if available, otherwise start at day 0
        start_time = mission.trajectory.maneuvers[0].timestamp_days if mission.trajectory.maneuvers else 0.0
        
        # Phase 1: r1 to r3
        for i in range(26):  # 25 points + 1
            t_frac = i / 25
            angle = math.pi * t_frac
            r = a1 * (1 - 0.1**2) / (1 + 0.1 * math.cos(angle))
            
            waypoints.append({
                "time_days": start_time + (t1 / 86400) * t_frac,
                "position_km": [r * math.cos(angle) / 1000, r * math.sin(angle) / 1000, 0],
                "velocity_kms": [
                    -math.sqrt(mu / a1) * math.sin(angle) / 1000,
                    math.sqrt(mu / a1) * (0.1 + math.cos(angle)) / 1000,
                    0
                ]
            })
        
        # Phase 2: r3 to r2
        for i in range(1, 26):  # Skip first point to avoid duplication
            t_frac = i / 25
            angle = math.pi * t_frac
            r = a2 * (1 - 0.1**2) / (1 + 0.1 * math.cos(angle))
            
            waypoints.append({
                "time_days": start_time + (t1 / 86400) + (t2 / 86400) * t_frac,
                "position_km": [r * math.cos(angle) / 1000, r * math.sin(angle) / 1000, 0],
                "velocity_kms": [
                    -math.sqrt(mu / a2) * math.sin(angle) / 1000,
                    math.sqrt(mu / a2) * (0.1 + math.cos(angle)) / 1000,
                    0
                ]
            })
        
        return {
            "waypoints": waypoints,
            "transfer_type": "bi_elliptic",
            "transfer_time_days": total_time / 86400,
            "total_distance": math.pi * (a1 + a2)
        }
    
    def _calculate_direct_trajectory(self, mission: MissionModel,
                                   dep_body: Dict, tgt_body: Dict) -> Dict[str, Any]:
        """Calculate direct transfer trajectory details."""
        # Simplified direct transfer (faster than Hohmann)
        r1 = dep_body.get('orbital_radius', 1.0e8)
        r2 = tgt_body.get('orbital_radius', 1.5e8)
        mu = 1.32712440018e20
        
        # Direct transfer with higher energy
        a_transfer = (r1 + r2) / 2 * 0.8  # Smaller semi-major axis for faster transfer
        transfer_time = 0.7 * math.pi * math.sqrt(a_transfer**3 / mu)
        
        waypoints = []
        num_points = 30
        
        # Use first maneuver timestamp if available, otherwise start at day 0
        start_time = mission.trajectory.maneuvers[0].timestamp_days if mission.trajectory.maneuvers else 0.0
        
        for i in range(num_points + 1):
            t_frac = i / num_points
            angle = 0.7 * math.pi * t_frac  # Shorter arc
            r = a_transfer * (1 - 0.2**2) / (1 + 0.2 * math.cos(angle))
            
            waypoints.append({
                "time_days": start_time + (transfer_time / 86400) * t_frac,
                "position_km": [r * math.cos(angle) / 1000, r * math.sin(angle) / 1000, 0],
                "velocity_kms": [
                    -math.sqrt(mu / a_transfer) * math.sin(angle) / 1000,
                    math.sqrt(mu / a_transfer) * (0.2 + math.cos(angle)) / 1000,
                    0
                ]
            })
        
        return {
            "waypoints": waypoints,
            "transfer_type": "direct",
            "transfer_time_days": transfer_time / 86400,
            "total_distance": 0.7 * math.pi * a_transfer
        }
    
    async def _analyze_fuel_consumption(self, mission: MissionModel, 
                                      trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fuel consumption throughout the mission."""
        fuel_data = {
            "total_consumption": 0.0,
            "consumption_by_maneuver": [],
            "fuel_margin": 0.0,
            "timeline": [],
            "thrust_utilization": 0.0
        }
        
        current_fuel = mission.spacecraft_config.fuel_capacity_kg
        total_burn_time = 0.0
        
        # Calculate fuel consumption for each maneuver
        for maneuver_detail in trajectory_data["maneuver_details"]:
            fuel_used = maneuver_detail["fuel_consumption"]
            burn_time = maneuver_detail["burn_time"]
            
            fuel_data["consumption_by_maneuver"].append({
                "maneuver": maneuver_detail["name"],
                "fuel_used": fuel_used,
                "burn_time": burn_time,
                "remaining_fuel": current_fuel - fuel_used
            })
            
            fuel_data["timeline"].append({
                "time_days": maneuver_detail["timestamp"],
                "fuel_remaining": current_fuel - fuel_used,
                "fuel_used_cumulative": fuel_data["total_consumption"] + fuel_used
            })
            
            current_fuel -= fuel_used
            fuel_data["total_consumption"] += fuel_used
            total_burn_time += burn_time
        
        # Calculate margins and utilization
        fuel_data["fuel_margin"] = current_fuel / mission.spacecraft_config.fuel_capacity_kg
        
        # Thrust utilization (percentage of mission time spent burning)
        mission_duration_s = mission.trajectory.flight_time_days * 24 * 3600
        fuel_data["thrust_utilization"] = total_burn_time / mission_duration_s if mission_duration_s > 0 else 0
        
        return fuel_data
    
    async def _calculate_performance_metrics(self, mission: MissionModel,
                                           trajectory_data: Dict[str, Any],
                                           fuel_data: Dict[str, Any]) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        
        # Basic metrics
        total_delta_v = mission.trajectory.total_delta_v
        fuel_consumption = fuel_data["total_consumption"]
        mission_duration = mission.trajectory.flight_time_days
        
        # Success probability calculation
        base_success = 0.95
        
        # Reduce success probability based on complexity
        complexity_factor = min(len(mission.trajectory.maneuvers) * 0.02, 0.2)
        delta_v_factor = min(total_delta_v / 10000 * 0.2, 0.4)  # More sensitive to high delta-v
        duration_factor = min(mission_duration / 1000 * 0.05, 0.1)
        
        success_probability = base_success - complexity_factor - delta_v_factor - duration_factor
        success_probability = max(success_probability, 0.5)  # Minimum 50%
        
        # Cost estimation (simplified model)
        base_cost = 50e6  # $50M base cost
        mass_cost = mission.spacecraft_config.mass_kg * 15000  # $15k per kg
        delta_v_cost = total_delta_v * 8000  # $8k per m/s delta-v
        duration_cost = mission_duration * 150000  # $150k per day
        complexity_cost = len(mission.trajectory.maneuvers) * 2e6  # $2M per maneuver
        
        cost_estimate = base_cost + mass_cost + delta_v_cost + duration_cost + complexity_cost
        
        # Efficiency score (fuel efficiency vs theoretical minimum)
        theoretical_min_fuel = FuelConsumptionModel.calculate_fuel_consumption(
            total_delta_v, mission.spacecraft_config, efficiency_factor=1.0
        )
        efficiency_score = theoretical_min_fuel / fuel_consumption if fuel_consumption > 0 else 1.0
        efficiency_score = min(efficiency_score, 1.0)
        
        # Risk score (inverse of success probability)
        risk_score = 1.0 - success_probability
        
        return PerformanceMetrics(
            total_delta_v=total_delta_v,
            fuel_consumption_kg=fuel_consumption,
            mission_duration_days=mission_duration,
            success_probability=success_probability,
            cost_estimate_usd=cost_estimate,
            efficiency_score=efficiency_score,
            risk_score=risk_score,
            trajectory_accuracy=trajectory_data["accuracy_metrics"]["total_error_budget"],
            system_reliability=0.90 - risk_score * 0.1,
            communication_coverage=0.85,
            power_margin=0.20,
            thermal_margin=0.15
        )
    
    async def _assess_mission_risks(self, mission: MissionModel, 
                                  performance: PerformanceMetrics) -> List[RiskFactor]:
        """Assess mission risks and generate risk factors."""
        risk_factors = []
        
        # Fuel margin risk
        fuel_margin = (mission.spacecraft_config.fuel_capacity_kg - performance.fuel_consumption_kg) / mission.spacecraft_config.fuel_capacity_kg
        if fuel_margin < 0.1:
            risk_factors.append(RiskFactor(
                category="Fuel Management",
                description=f"Low fuel margin ({fuel_margin:.1%}), limited contingency capability",
                probability=0.3,
                impact=RiskLevel.HIGH,
                mitigation="Consider reducing mission scope or increasing fuel capacity"
            ))
        
        # Mission duration risk
        if performance.mission_duration_days > 1000:
            risk_factors.append(RiskFactor(
                category="Mission Duration",
                description="Extended mission duration increases system degradation risk",
                probability=0.2,
                impact=RiskLevel.MEDIUM,
                mitigation="Implement robust system health monitoring and redundancy"
            ))
        
        # Complexity risk
        if len(mission.trajectory.maneuvers) > 10:
            risk_factors.append(RiskFactor(
                category="Mission Complexity",
                description="High number of maneuvers increases operational risk",
                probability=0.25,
                impact=RiskLevel.MEDIUM,
                mitigation="Simplify trajectory or improve navigation accuracy"
            ))
        
        # Delta-v risk
        if performance.total_delta_v > 12000:
            risk_factors.append(RiskFactor(
                category="Propulsion",
                description="High delta-v requirement stresses propulsion system",
                probability=0.15,
                impact=RiskLevel.HIGH,
                mitigation="Consider alternative trajectory or upgraded propulsion"
            ))
        
        # Communication risk for distant missions
        if mission.trajectory.target_body in [CelestialBody.JUPITER, CelestialBody.SATURN]:
            risk_factors.append(RiskFactor(
                category="Communication",
                description="Long communication delays and reduced signal strength",
                probability=0.4,
                impact=RiskLevel.MEDIUM,
                mitigation="Implement autonomous operation capabilities"
            ))
        
        return risk_factors