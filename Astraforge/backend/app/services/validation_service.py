"""
Mission validation and feasibility checking service.

This service implements comprehensive mission validation including:
- Constraint validation for mission parameters
- Feasibility analysis with alternative suggestions
- Risk factor assessment algorithms
- Physics-based validation checks
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np
from pydantic import BaseModel

from ..models.mission import (
    Mission as MissionModel,
    SpacecraftConfig,
    TrajectoryPlan,
    Maneuver,
    RiskFactor,
    CelestialBody,
    TransferType,
    VehicleType,
    RiskLevel
)
from ..physics.orbital_mechanics import (
    DeltaVCalculator,
    TrajectoryCalculator,
    CELESTIAL_BODIES
)


class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    severity: ValidationSeverity
    category: str
    message: str
    parameter: Optional[str] = None
    current_value: Optional[Any] = None
    suggested_value: Optional[Any] = None
    mitigation: Optional[str] = None


@dataclass
class FeasibilityAnalysis:
    """Mission feasibility analysis results."""
    is_feasible: bool
    feasibility_score: float  # 0.0 to 1.0
    confidence_level: float   # 0.0 to 1.0
    primary_constraints: List[str]
    alternative_suggestions: List[Dict[str, Any]]
    risk_assessment: List[RiskFactor]


@dataclass
class ValidationResult:
    """Complete validation result."""
    is_valid: bool
    overall_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue]
    feasibility: FeasibilityAnalysis
    recommendations: List[str]


class MissionValidationService:
    """Service for comprehensive mission validation and feasibility checking."""
    
    def __init__(self):
        self._validation_cache: Dict[str, ValidationResult] = {}
    
    async def validate_mission(self, mission: MissionModel, 
                             detailed: bool = True) -> ValidationResult:
        """
        Perform comprehensive mission validation.
        
        Args:
            mission: Mission to validate
            detailed: Whether to perform detailed physics validation
        
        Returns:
            Complete validation result with issues and recommendations
        """
        issues = []
        
        # Basic parameter validation
        issues.extend(await self._validate_basic_parameters(mission))
        
        # Spacecraft configuration validation
        issues.extend(await self._validate_spacecraft_config(mission.spacecraft_config))
        
        # Trajectory validation
        issues.extend(await self._validate_trajectory(mission.trajectory))
        
        # Physics-based validation
        if detailed:
            issues.extend(await self._validate_physics_constraints(mission))
        
        # Mission constraints validation
        issues.extend(await self._validate_mission_constraints(mission))
        
        # Feasibility analysis
        feasibility = await self._analyze_feasibility(mission, issues)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(mission, issues)
        
        # Calculate overall validation score
        overall_score = self._calculate_validation_score(issues, feasibility)
        
        # Determine if mission is valid (no critical or error issues)
        is_valid = not any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] 
                          for issue in issues)
        
        return ValidationResult(
            is_valid=is_valid,
            overall_score=overall_score,
            issues=issues,
            feasibility=feasibility,
            recommendations=recommendations
        )
    
    async def _validate_basic_parameters(self, mission: MissionModel) -> List[ValidationIssue]:
        """Validate basic mission parameters."""
        issues = []
        
        # Mission name and description
        if len(mission.name.strip()) < 3:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Mission Definition",
                message="Mission name is very short",
                parameter="name",
                current_value=mission.name,
                mitigation="Provide a more descriptive mission name"
            ))
        
        if len(mission.description.strip()) < 10:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Mission Definition",
                message="Mission description is very brief",
                parameter="description",
                current_value=len(mission.description),
                mitigation="Provide a more detailed mission description"
            ))
        
        # Mission objectives
        if len(mission.objectives) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Mission Definition",
                message="Mission must have at least one objective",
                parameter="objectives",
                current_value=len(mission.objectives),
                suggested_value=1,
                mitigation="Define clear mission objectives"
            ))
        
        # Check for duplicate objectives
        if len(mission.objectives) != len(set(mission.objectives)):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Mission Definition",
                message="Mission has duplicate objectives",
                parameter="objectives",
                mitigation="Remove duplicate objectives"
            ))
        
        return issues
    
    async def _validate_spacecraft_config(self, spacecraft: SpacecraftConfig) -> List[ValidationIssue]:
        """Validate spacecraft configuration."""
        issues = []
        
        # Mass validation
        if spacecraft.mass_kg <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="Spacecraft Configuration",
                message="Spacecraft mass must be positive",
                parameter="mass_kg",
                current_value=spacecraft.mass_kg,
                suggested_value=1000.0
            ))
        
        # Fuel capacity validation
        if spacecraft.fuel_capacity_kg < 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="Spacecraft Configuration",
                message="Fuel capacity cannot be negative",
                parameter="fuel_capacity_kg",
                current_value=spacecraft.fuel_capacity_kg,
                suggested_value=0.0
            ))
        
        if spacecraft.fuel_capacity_kg >= spacecraft.mass_kg:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Spacecraft Configuration",
                message="Fuel capacity cannot exceed total spacecraft mass",
                parameter="fuel_capacity_kg",
                current_value=spacecraft.fuel_capacity_kg,
                suggested_value=spacecraft.mass_kg * 0.8,
                mitigation="Reduce fuel capacity or increase total mass"
            ))
        
        # Thrust validation
        if spacecraft.thrust_n <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Spacecraft Configuration",
                message="Thrust must be positive",
                parameter="thrust_n",
                current_value=spacecraft.thrust_n,
                suggested_value=100.0
            ))
        
        # Specific impulse validation
        if spacecraft.specific_impulse_s <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Spacecraft Configuration",
                message="Specific impulse must be positive",
                parameter="specific_impulse_s",
                current_value=spacecraft.specific_impulse_s,
                suggested_value=300.0
            ))
        
        if spacecraft.specific_impulse_s > 500:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Spacecraft Configuration",
                message="Specific impulse is very high for chemical propulsion",
                parameter="specific_impulse_s",
                current_value=spacecraft.specific_impulse_s,
                mitigation="Verify propulsion system type or reduce Isp"
            ))
        
        # Payload mass validation
        if spacecraft.payload_mass_kg < 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Spacecraft Configuration",
                message="Payload mass cannot be negative",
                parameter="payload_mass_kg",
                current_value=spacecraft.payload_mass_kg,
                suggested_value=0.0
            ))
        
        if spacecraft.payload_mass_kg >= spacecraft.mass_kg:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Spacecraft Configuration",
                message="Payload mass cannot exceed total spacecraft mass",
                parameter="payload_mass_kg",
                current_value=spacecraft.payload_mass_kg,
                suggested_value=spacecraft.mass_kg * 0.3,
                mitigation="Reduce payload mass or increase total mass"
            ))
        
        # Thrust-to-weight ratio check
        twr = spacecraft.thrust_to_weight_ratio
        if twr < 0.01:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Spacecraft Configuration",
                message="Very low thrust-to-weight ratio may cause long burn times",
                parameter="thrust_n",
                current_value=twr,
                suggested_value=0.1,
                mitigation="Increase thrust or reduce mass"
            ))
        
        # Power validation
        if spacecraft.power_w <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Spacecraft Configuration",
                message="Power generation should be positive",
                parameter="power_w",
                current_value=spacecraft.power_w,
                suggested_value=1000.0
            ))
        
        return issues
    
    async def _validate_trajectory(self, trajectory: TrajectoryPlan) -> List[ValidationIssue]:
        """Validate trajectory plan."""
        issues = []
        
        # Launch window validation
        if trajectory.launch_window.end <= trajectory.launch_window.start:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Trajectory",
                message="Launch window end must be after start",
                parameter="launch_window",
                mitigation="Correct launch window dates"
            ))
        
        # Celestial body validation
        if trajectory.departure_body == trajectory.target_body:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Trajectory",
                message="Departure and target bodies must be different",
                parameter="target_body",
                mitigation="Select different target body"
            ))
        
        # Delta-V validation
        if trajectory.total_delta_v <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Trajectory",
                message="Total delta-V must be positive",
                parameter="total_delta_v",
                current_value=trajectory.total_delta_v,
                suggested_value=1000.0
            ))
        
        if trajectory.total_delta_v > 50000:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Trajectory",
                message="Very high delta-V requirement",
                parameter="total_delta_v",
                current_value=trajectory.total_delta_v,
                mitigation="Consider alternative trajectory or staging"
            ))
        
        # Flight time validation
        if trajectory.flight_time_days <= 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Trajectory",
                message="Flight time must be positive",
                parameter="flight_time_days",
                current_value=trajectory.flight_time_days,
                suggested_value=30.0
            ))
        
        if trajectory.flight_time_days > 10000:  # ~27 years
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Trajectory",
                message="Very long mission duration",
                parameter="flight_time_days",
                current_value=trajectory.flight_time_days,
                mitigation="Consider shorter trajectory or mission redesign"
            ))
        
        # Maneuver validation
        issues.extend(await self._validate_maneuvers(trajectory.maneuvers, trajectory.total_delta_v))
        
        return issues
    
    async def _validate_maneuvers(self, maneuvers: List[Maneuver], 
                                total_delta_v: float) -> List[ValidationIssue]:
        """Validate individual maneuvers."""
        issues = []
        
        if len(maneuvers) == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Maneuvers",
                message="Mission has no maneuvers defined",
                parameter="maneuvers",
                mitigation="Define required maneuvers for the mission"
            ))
            return issues
        
        # Check chronological order
        timestamps = [m.timestamp_days for m in maneuvers]
        if timestamps != sorted(timestamps):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Maneuvers",
                message="Maneuvers are not in chronological order",
                parameter="maneuvers",
                mitigation="Reorder maneuvers by timestamp"
            ))
        
        # Check delta-V consistency
        maneuver_delta_v_sum = sum(m.delta_v_ms for m in maneuvers)
        delta_v_difference = abs(maneuver_delta_v_sum - total_delta_v)
        
        if delta_v_difference > 100:  # 100 m/s tolerance
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="Maneuvers",
                message=f"Maneuver delta-V sum ({maneuver_delta_v_sum:.0f} m/s) doesn't match total ({total_delta_v:.0f} m/s)",
                parameter="total_delta_v",
                current_value=total_delta_v,
                suggested_value=maneuver_delta_v_sum,
                mitigation="Adjust total delta-V to match maneuver sum"
            ))
        
        # Validate individual maneuvers
        for i, maneuver in enumerate(maneuvers):
            if maneuver.delta_v_ms <= 0:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="Maneuvers",
                    message=f"Maneuver '{maneuver.name}' has non-positive delta-V",
                    parameter=f"maneuvers[{i}].delta_v_ms",
                    current_value=maneuver.delta_v_ms,
                    suggested_value=100.0
                ))
            
            if maneuver.delta_v_ms > 15000:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="Maneuvers",
                    message=f"Maneuver '{maneuver.name}' has very high delta-V",
                    parameter=f"maneuvers[{i}].delta_v_ms",
                    current_value=maneuver.delta_v_ms,
                    mitigation="Consider splitting into multiple maneuvers"
                ))
            
            if maneuver.duration_s <= 0:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="Maneuvers",
                    message=f"Maneuver '{maneuver.name}' has non-positive duration",
                    parameter=f"maneuvers[{i}].duration_s",
                    current_value=maneuver.duration_s,
                    suggested_value=60.0
                ))
            
            if maneuver.timestamp_days < 0:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="Maneuvers",
                    message=f"Maneuver '{maneuver.name}' has negative timestamp",
                    parameter=f"maneuvers[{i}].timestamp_days",
                    current_value=maneuver.timestamp_days,
                    suggested_value=0.0
                ))
        
        return issues
    
    async def _validate_physics_constraints(self, mission: MissionModel) -> List[ValidationIssue]:
        """Validate physics-based constraints."""
        issues = []
        
        # Delta-V capability check
        spacecraft = mission.spacecraft_config
        trajectory = mission.trajectory
        
        # Calculate theoretical delta-V capability
        if spacecraft.fuel_capacity_kg > 0 and spacecraft.specific_impulse_s > 0:
            dry_mass = spacecraft.mass_kg - spacecraft.fuel_capacity_kg
            if dry_mass > 0:
                mass_ratio = spacecraft.mass_kg / dry_mass
                theoretical_dv = spacecraft.specific_impulse_s * 9.81 * math.log(mass_ratio)
                
                if theoretical_dv < trajectory.total_delta_v:
                    deficit = trajectory.total_delta_v - theoretical_dv
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        category="Physics Constraints",
                        message=f"Insufficient delta-V capability: need {trajectory.total_delta_v:.0f} m/s, have {theoretical_dv:.0f} m/s (deficit: {deficit:.0f} m/s)",
                        parameter="fuel_capacity_kg",
                        current_value=spacecraft.fuel_capacity_kg,
                        suggested_value=spacecraft.fuel_capacity_kg * (trajectory.total_delta_v / theoretical_dv),
                        mitigation="Increase fuel capacity, improve specific impulse, or reduce delta-V requirements"
                    ))
        
        # Interplanetary transfer validation
        if trajectory.departure_body in CELESTIAL_BODIES and trajectory.target_body in CELESTIAL_BODIES:
            try:
                interplanetary_dv = DeltaVCalculator.interplanetary_delta_v(
                    trajectory.departure_body, trajectory.target_body
                )
                
                if trajectory.total_delta_v < interplanetary_dv['total_delta_v'] * 0.8:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="Physics Constraints",
                        message=f"Delta-V may be insufficient for interplanetary transfer (typical requirement: {interplanetary_dv['total_delta_v']:.0f} m/s)",
                        parameter="total_delta_v",
                        current_value=trajectory.total_delta_v,
                        suggested_value=interplanetary_dv['total_delta_v'],
                        mitigation="Increase delta-V budget or verify trajectory calculations"
                    ))
                
            except ValueError:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="Physics Constraints",
                    message="Cannot validate interplanetary transfer for selected bodies",
                    parameter="target_body",
                    mitigation="Verify celestial body selection"
                ))
        
        # Transfer type validation
        if trajectory.departure_body in CELESTIAL_BODIES and trajectory.target_body in CELESTIAL_BODIES:
            dep_data = CELESTIAL_BODIES[trajectory.departure_body]
            tgt_data = CELESTIAL_BODIES[trajectory.target_body]
            
            # Check if bi-elliptic might be more efficient
            if hasattr(dep_data, 'orbital_radius') and hasattr(tgt_data, 'orbital_radius'):
                r1 = dep_data.get('orbital_radius', 1e8)
                r2 = tgt_data.get('orbital_radius', 1.5e8)
                ratio = max(r1, r2) / min(r1, r2)
                
                if ratio > 11.94 and trajectory.transfer_type == TransferType.HOHMANN:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        category="Physics Constraints",
                        message="Bi-elliptic transfer might be more efficient for this distance ratio",
                        parameter="transfer_type",
                        current_value=trajectory.transfer_type,
                        suggested_value=TransferType.BI_ELLIPTIC,
                        mitigation="Consider bi-elliptic transfer for better fuel efficiency"
                    ))
        
        return issues
    
    async def _validate_mission_constraints(self, mission: MissionModel) -> List[ValidationIssue]:
        """Validate mission against defined constraints."""
        issues = []
        constraints = mission.constraints
        
        # Duration constraint
        if mission.trajectory.flight_time_days > constraints.max_duration_days:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Mission Constraints",
                message=f"Mission duration ({mission.trajectory.flight_time_days:.0f} days) exceeds constraint ({constraints.max_duration_days:.0f} days)",
                parameter="flight_time_days",
                current_value=mission.trajectory.flight_time_days,
                suggested_value=constraints.max_duration_days,
                mitigation="Reduce mission duration or relax constraints"
            ))
        
        # Delta-V constraint
        if mission.trajectory.total_delta_v > constraints.max_delta_v_ms:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Mission Constraints",
                message=f"Total delta-V ({mission.trajectory.total_delta_v:.0f} m/s) exceeds constraint ({constraints.max_delta_v_ms:.0f} m/s)",
                parameter="total_delta_v",
                current_value=mission.trajectory.total_delta_v,
                suggested_value=constraints.max_delta_v_ms,
                mitigation="Reduce delta-V requirements or relax constraints"
            ))
        
        # Mass constraint
        if mission.spacecraft_config.mass_kg > constraints.max_mass_kg:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="Mission Constraints",
                message=f"Spacecraft mass ({mission.spacecraft_config.mass_kg:.0f} kg) exceeds constraint ({constraints.max_mass_kg:.0f} kg)",
                parameter="mass_kg",
                current_value=mission.spacecraft_config.mass_kg,
                suggested_value=constraints.max_mass_kg,
                mitigation="Reduce spacecraft mass or relax constraints"
            ))
        
        return issues
    
    async def _analyze_feasibility(self, mission: MissionModel, 
                                 issues: List[ValidationIssue]) -> FeasibilityAnalysis:
        """Analyze mission feasibility and generate alternatives."""
        
        # Count issues by severity
        critical_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
        error_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING)
        
        # Calculate feasibility score
        feasibility_score = 1.0
        feasibility_score -= critical_count * 0.5  # Critical issues heavily impact feasibility
        feasibility_score -= error_count * 0.2    # Error issues moderately impact feasibility
        feasibility_score -= warning_count * 0.05 # Warning issues slightly impact feasibility
        feasibility_score = max(feasibility_score, 0.0)
        
        # Determine if mission is feasible
        is_feasible = critical_count == 0 and error_count == 0
        
        # Calculate confidence level
        confidence_level = 0.9 - (warning_count * 0.1)
        confidence_level = max(confidence_level, 0.1)
        
        # Identify primary constraints
        primary_constraints = []
        for issue in issues:
            if issue.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]:
                primary_constraints.append(issue.category)
        
        # Remove duplicates while preserving order
        primary_constraints = list(dict.fromkeys(primary_constraints))
        
        # Generate alternative suggestions
        alternatives = await self._generate_alternatives(mission, issues)
        
        # Generate risk assessment
        risk_assessment = await self._assess_validation_risks(mission, issues)
        
        return FeasibilityAnalysis(
            is_feasible=is_feasible,
            feasibility_score=feasibility_score,
            confidence_level=confidence_level,
            primary_constraints=primary_constraints,
            alternative_suggestions=alternatives,
            risk_assessment=risk_assessment
        )
    
    async def _generate_alternatives(self, mission: MissionModel, 
                                   issues: List[ValidationIssue]) -> List[Dict[str, Any]]:
        """Generate alternative mission configurations."""
        alternatives = []
        
        # Alternative 1: Reduce delta-V requirements
        dv_issues = [issue for issue in issues if 'delta' in issue.message.lower()]
        if dv_issues:
            alternatives.append({
                "name": "Reduced Delta-V Mission",
                "description": "Lower delta-V requirements through trajectory optimization",
                "changes": {
                    "total_delta_v": mission.trajectory.total_delta_v * 0.8,
                    "transfer_type": TransferType.HOHMANN,
                    "flight_time_days": mission.trajectory.flight_time_days * 1.2
                },
                "trade_offs": ["Longer mission duration", "Potentially less flexible trajectory"],
                "feasibility_improvement": 0.3
            })
        
        # Alternative 2: Increase spacecraft capability
        capability_issues = [issue for issue in issues if 'fuel' in issue.message.lower() or 'mass' in issue.message.lower()]
        if capability_issues:
            alternatives.append({
                "name": "Enhanced Spacecraft",
                "description": "Increase spacecraft fuel capacity and performance",
                "changes": {
                    "fuel_capacity_kg": mission.spacecraft_config.fuel_capacity_kg * 1.5,
                    "mass_kg": mission.spacecraft_config.mass_kg * 1.3,
                    "specific_impulse_s": min(mission.spacecraft_config.specific_impulse_s * 1.1, 450)
                },
                "trade_offs": ["Higher cost", "Larger launch vehicle required"],
                "feasibility_improvement": 0.4
            })
        
        # Alternative 3: Staged mission approach
        if mission.trajectory.total_delta_v > 10000:
            alternatives.append({
                "name": "Multi-Stage Mission",
                "description": "Break mission into multiple stages with refueling or staging",
                "changes": {
                    "mission_phases": 2,
                    "delta_v_per_stage": mission.trajectory.total_delta_v / 2,
                    "staging_location": "Earth orbit" if mission.trajectory.departure_body == CelestialBody.EARTH else "departure orbit"
                },
                "trade_offs": ["Increased complexity", "Higher cost", "Additional launch requirements"],
                "feasibility_improvement": 0.5
            })
        
        # Alternative 4: Different target or trajectory
        if mission.trajectory.target_body in [CelestialBody.JUPITER, CelestialBody.SATURN]:
            alternatives.append({
                "name": "Nearer Target Mission",
                "description": "Target closer celestial body for reduced requirements",
                "changes": {
                    "target_body": CelestialBody.MARS if mission.trajectory.target_body != CelestialBody.MARS else CelestialBody.VENUS,
                    "total_delta_v": mission.trajectory.total_delta_v * 0.6,
                    "flight_time_days": mission.trajectory.flight_time_days * 0.4
                },
                "trade_offs": ["Different science objectives", "Reduced mission scope"],
                "feasibility_improvement": 0.6
            })
        
        return alternatives
    
    async def _assess_validation_risks(self, mission: MissionModel, 
                                     issues: List[ValidationIssue]) -> List[RiskFactor]:
        """Assess risks based on validation issues."""
        risks = []
        
        # High delta-V risk
        if mission.trajectory.total_delta_v > 12000:
            risks.append(RiskFactor(
                category="Mission Feasibility",
                description="High delta-V requirements increase mission complexity and failure risk",
                probability=0.3,
                impact=RiskLevel.HIGH,
                mitigation="Consider trajectory optimization or staging"
            ))
        
        # Long duration risk
        if mission.trajectory.flight_time_days > 1000:
            risks.append(RiskFactor(
                category="Mission Duration",
                description="Extended mission duration increases system degradation and operational risks",
                probability=0.25,
                impact=RiskLevel.MEDIUM,
                mitigation="Implement robust system health monitoring and redundancy"
            ))
        
        # Validation issue risk
        critical_issues = [issue for issue in issues if issue.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            risks.append(RiskFactor(
                category="Design Validation",
                description=f"Critical validation issues detected: {len(critical_issues)} issues",
                probability=0.8,
                impact=RiskLevel.CRITICAL,
                mitigation="Resolve all critical validation issues before proceeding"
            ))
        
        error_issues = [issue for issue in issues if issue.severity == ValidationSeverity.ERROR]
        if error_issues:
            risks.append(RiskFactor(
                category="Design Validation",
                description=f"Design errors detected: {len(error_issues)} issues",
                probability=0.5,
                impact=RiskLevel.HIGH,
                mitigation="Address all error-level validation issues"
            ))
        
        return risks
    
    async def _generate_recommendations(self, mission: MissionModel, 
                                      issues: List[ValidationIssue]) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        # Group issues by category
        issue_categories = {}
        for issue in issues:
            if issue.category not in issue_categories:
                issue_categories[issue.category] = []
            issue_categories[issue.category].append(issue)
        
        # Generate category-specific recommendations
        for category, category_issues in issue_categories.items():
            critical_issues = [i for i in category_issues if i.severity == ValidationSeverity.CRITICAL]
            error_issues = [i for i in category_issues if i.severity == ValidationSeverity.ERROR]
            
            if critical_issues:
                recommendations.append(f"CRITICAL: Address {len(critical_issues)} critical {category.lower()} issues immediately")
            
            if error_issues:
                recommendations.append(f"HIGH PRIORITY: Resolve {len(error_issues)} {category.lower()} errors before mission approval")
        
        # Specific recommendations based on common issues
        if any('delta' in issue.message.lower() and 'insufficient' in issue.message.lower() for issue in issues):
            recommendations.append("Consider trajectory optimization, staging, or improved propulsion system")
        
        if any('fuel' in issue.message.lower() for issue in issues):
            recommendations.append("Review fuel budget and consider margin increases")
        
        if any('duration' in issue.message.lower() for issue in issues):
            recommendations.append("Evaluate mission timeline and consider duration constraints")
        
        if any('mass' in issue.message.lower() for issue in issues):
            recommendations.append("Optimize spacecraft design for mass efficiency")
        
        # General recommendations
        if len(issues) > 10:
            recommendations.append("Consider mission scope reduction due to high number of validation issues")
        
        if not any(issue.severity == ValidationSeverity.CRITICAL for issue in issues):
            recommendations.append("Mission appears technically feasible with addressed issues")
        
        return recommendations
    
    def _calculate_validation_score(self, issues: List[ValidationIssue], 
                                  feasibility: FeasibilityAnalysis) -> float:
        """Calculate overall validation score."""
        # Base score from feasibility
        score = feasibility.feasibility_score * 0.7
        
        # Confidence contribution
        score += feasibility.confidence_level * 0.2
        
        # Issue severity penalty
        severity_weights = {
            ValidationSeverity.CRITICAL: -0.3,
            ValidationSeverity.ERROR: -0.1,
            ValidationSeverity.WARNING: -0.02,
            ValidationSeverity.INFO: 0.0
        }
        
        for issue in issues:
            score += severity_weights.get(issue.severity, 0.0)
        
        # Normalize to 0-1 range
        return max(min(score, 1.0), 0.0)