"""
Mission optimization service using genetic algorithms.

This service integrates the genetic algorithm framework with mission simulation
to optimize mission parameters for multiple objectives like fuel efficiency,
mission duration, and success probability.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from uuid import UUID, uuid4
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ..models.mission import Mission, SpacecraftConfig, TrajectoryPlan, SimulationResult
from ..optimization.genetic_algorithm import Individual, GAConfig, GeneticAlgorithm
from ..optimization.multi_objective import (
    MultiObjectiveGA, ObjectiveFunction, ObjectiveType, ParetoFront
)
from ..optimization.operators import (
    TournamentSelection, UniformCrossover, GaussianMutation
)
from ..services.simulation_service import MissionSimulationService
from ..services.validation_service import MissionValidationService

logger = logging.getLogger(__name__)


class OptimizationObjective(str, Enum):
    """Available optimization objectives."""
    MINIMIZE_FUEL = "minimize_fuel"
    MINIMIZE_DURATION = "minimize_duration"
    MINIMIZE_COST = "minimize_cost"
    MAXIMIZE_SUCCESS_PROBABILITY = "maximize_success_probability"
    MINIMIZE_DELTA_V = "minimize_delta_v"
    MINIMIZE_RISK = "minimize_risk"


class OptimizationStatus(str, Enum):
    """Optimization job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OptimizationParameter:
    """Represents a parameter to be optimized."""
    name: str
    min_value: float
    max_value: float
    current_value: float
    parameter_type: str  # 'spacecraft', 'trajectory', 'timeline'
    description: str = ""
    
    def __post_init__(self):
        """Validate parameter bounds."""
        if self.min_value >= self.max_value:
            raise ValueError(f"Invalid bounds for parameter {self.name}: min >= max")
        if not self.min_value <= self.current_value <= self.max_value:
            raise ValueError(f"Current value for {self.name} is outside bounds")


@dataclass
class OptimizationConstraint:
    """Represents a constraint for optimization."""
    name: str
    constraint_function: Callable[[Mission], bool]
    description: str = ""
    weight: float = 1.0  # Penalty weight for constraint violation


@dataclass
class OptimizationConfig:
    """Configuration for mission optimization."""
    objectives: List[OptimizationObjective]
    parameters: List[OptimizationParameter]
    constraints: List[OptimizationConstraint] = field(default_factory=list)
    
    # GA configuration
    population_size: int = 50
    max_generations: int = 100
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    elitism_rate: float = 0.1
    tournament_size: int = 3
    
    # Convergence criteria
    convergence_threshold: float = 1e-6
    max_stagnant_generations: int = 20
    
    # Simulation settings
    enable_detailed_simulation: bool = True
    simulation_timeout_seconds: int = 300
    
    def __post_init__(self):
        """Validate optimization configuration."""
        if not self.objectives:
            raise ValueError("At least one optimization objective must be specified")
        if not self.parameters:
            raise ValueError("At least one optimization parameter must be specified")
        if self.population_size <= 0:
            raise ValueError("Population size must be positive")
        if self.max_generations <= 0:
            raise ValueError("Max generations must be positive")


@dataclass
class OptimizationProgress:
    """Tracks optimization progress."""
    generation: int = 0
    best_fitness: float = float('-inf')
    mean_fitness: float = 0.0
    population_diversity: float = 0.0
    evaluations_completed: int = 0
    time_elapsed_seconds: float = 0.0
    convergence_metric: float = float('inf')
    pareto_front_size: int = 0
    
    # Current best solutions
    best_individual: Optional[Individual] = None
    pareto_optimal_solutions: List[Individual] = field(default_factory=list)


@dataclass
class OptimizationResult:
    """Results from mission optimization."""
    job_id: UUID
    mission_id: UUID
    status: OptimizationStatus
    config: OptimizationConfig
    
    # Results
    best_mission: Optional[Mission] = None
    pareto_optimal_missions: List[Mission] = field(default_factory=list)
    optimization_statistics: Dict[str, Any] = field(default_factory=dict)
    
    # Progress tracking
    progress: OptimizationProgress = field(default_factory=OptimizationProgress)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class MissionOptimizationService:
    """Service for optimizing mission parameters using genetic algorithms."""
    
    def __init__(
        self,
        simulation_service: MissionSimulationService,
        validation_service: MissionValidationService
    ):
        """
        Initialize optimization service.
        
        Args:
            simulation_service: Service for mission simulation
            validation_service: Service for mission validation
        """
        self.simulation_service = simulation_service
        self.validation_service = validation_service
        
        # Active optimization jobs
        self.active_jobs: Dict[UUID, OptimizationResult] = {}
        
        # Cache for simulation results to avoid re-computation
        self.simulation_cache: Dict[str, SimulationResult] = {}
        
        logger.info("Mission optimization service initialized")
    
    async def start_optimization(
        self,
        base_mission: Mission,
        config: OptimizationConfig
    ) -> UUID:
        """
        Start mission optimization job.
        
        Args:
            base_mission: Base mission to optimize
            config: Optimization configuration
            
        Returns:
            Job ID for tracking optimization progress
        """
        job_id = uuid4()
        
        # Create optimization result
        result = OptimizationResult(
            job_id=job_id,
            mission_id=base_mission.id,
            status=OptimizationStatus.PENDING,
            config=config,
            started_at=datetime.now()
        )
        
        self.active_jobs[job_id] = result
        
        # Start optimization in background
        asyncio.create_task(self._run_optimization(base_mission, result))
        
        logger.info(f"Started optimization job {job_id} for mission {base_mission.id}")
        return job_id
    
    async def _run_optimization(
        self,
        base_mission: Mission,
        result: OptimizationResult
    ):
        """Run the optimization process."""
        try:
            result.status = OptimizationStatus.RUNNING
            result.started_at = datetime.now()
            
            # Create objective functions
            objectives = self._create_objective_functions(result.config)
            
            # Create gene bounds from parameters
            gene_bounds = {
                param.name: (param.min_value, param.max_value)
                for param in result.config.parameters
            }
            
            # Create constraint functions
            constraint_functions = [
                self._create_constraint_function(constraint, base_mission)
                for constraint in result.config.constraints
            ]
            
            # Configure genetic algorithm
            ga_config = GAConfig(
                population_size=result.config.population_size,
                max_generations=result.config.max_generations,
                crossover_rate=result.config.crossover_rate,
                mutation_rate=result.config.mutation_rate,
                elitism_rate=result.config.elitism_rate,
                tournament_size=result.config.tournament_size,
                convergence_threshold=result.config.convergence_threshold,
                max_stagnant_generations=result.config.max_stagnant_generations
            )
            
            # Create fitness function
            fitness_function = self._create_fitness_function(base_mission, result.config)
            
            # Choose algorithm based on number of objectives
            if len(objectives) == 1:
                # Single-objective optimization
                ga = GeneticAlgorithm(
                    config=ga_config,
                    fitness_function=fitness_function,
                    gene_bounds=gene_bounds,
                    constraint_functions=constraint_functions
                )
                
                # Set operators
                ga.selection_operator = TournamentSelection(tournament_size=ga_config.tournament_size)
                ga.crossover_operator = UniformCrossover(swap_probability=0.5)
                ga.mutation_operator = GaussianMutation(sigma=0.1, gene_bounds=gene_bounds)
                
                # Run optimization with progress tracking
                best_individual, statistics = await self._run_single_objective_ga(ga, result)
                
                # Convert best individual to mission
                if best_individual:
                    result.best_mission = self._individual_to_mission(best_individual, base_mission)
                
            else:
                # Multi-objective optimization
                moga = MultiObjectiveGA(
                    config=ga_config,
                    objectives=objectives,
                    gene_bounds=gene_bounds,
                    constraint_functions=constraint_functions
                )
                
                # Set operators
                moga.selection_operator = TournamentSelection(tournament_size=ga_config.tournament_size)
                moga.crossover_operator = UniformCrossover(swap_probability=0.5)
                moga.mutation_operator = GaussianMutation(sigma=0.1, gene_bounds=gene_bounds)
                
                # Run optimization with progress tracking
                best_individual, statistics = await self._run_multi_objective_ga(moga, result)
                
                # Convert Pareto optimal solutions to missions
                pareto_optimal = moga.get_pareto_optimal_solutions()
                result.pareto_optimal_missions = [
                    self._individual_to_mission(ind, base_mission)
                    for ind in pareto_optimal
                ]
                
                if best_individual:
                    result.best_mission = self._individual_to_mission(best_individual, base_mission)
            
            result.optimization_statistics = statistics
            result.status = OptimizationStatus.COMPLETED
            result.completed_at = datetime.now()
            
            logger.info(f"Optimization job {result.job_id} completed successfully")
            
        except Exception as e:
            result.status = OptimizationStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()
            
            logger.error(f"Optimization job {result.job_id} failed: {e}")
    
    def _create_objective_functions(
        self,
        config: OptimizationConfig
    ) -> List[ObjectiveFunction]:
        """Create objective functions from configuration."""
        objectives = []
        
        for obj_type in config.objectives:
            if obj_type == OptimizationObjective.MINIMIZE_FUEL:
                def fuel_objective(individual: Individual) -> float:
                    # Extract fuel consumption from simulation result
                    if 'fuel_consumption_kg' in individual.objectives:
                        return individual.objectives['fuel_consumption_kg']
                    return float('inf')
                
                objectives.append(ObjectiveFunction(
                    name="fuel_consumption",
                    function=fuel_objective,
                    objective_type=ObjectiveType.MINIMIZE
                ))
            
            elif obj_type == OptimizationObjective.MINIMIZE_DURATION:
                def duration_objective(individual: Individual) -> float:
                    if 'total_duration_days' in individual.objectives:
                        return individual.objectives['total_duration_days']
                    return float('inf')
                
                objectives.append(ObjectiveFunction(
                    name="mission_duration",
                    function=duration_objective,
                    objective_type=ObjectiveType.MINIMIZE
                ))
            
            elif obj_type == OptimizationObjective.MINIMIZE_COST:
                def cost_objective(individual: Individual) -> float:
                    if 'cost_estimate_usd' in individual.objectives:
                        return individual.objectives['cost_estimate_usd']
                    return float('inf')
                
                objectives.append(ObjectiveFunction(
                    name="mission_cost",
                    function=cost_objective,
                    objective_type=ObjectiveType.MINIMIZE
                ))
            
            elif obj_type == OptimizationObjective.MAXIMIZE_SUCCESS_PROBABILITY:
                def success_objective(individual: Individual) -> float:
                    if 'success_probability' in individual.objectives:
                        return individual.objectives['success_probability']
                    return 0.0
                
                objectives.append(ObjectiveFunction(
                    name="success_probability",
                    function=success_objective,
                    objective_type=ObjectiveType.MAXIMIZE
                ))
            
            elif obj_type == OptimizationObjective.MINIMIZE_DELTA_V:
                def delta_v_objective(individual: Individual) -> float:
                    if 'total_delta_v' in individual.objectives:
                        return individual.objectives['total_delta_v']
                    return float('inf')
                
                objectives.append(ObjectiveFunction(
                    name="total_delta_v",
                    function=delta_v_objective,
                    objective_type=ObjectiveType.MINIMIZE
                ))
            
            elif obj_type == OptimizationObjective.MINIMIZE_RISK:
                def risk_objective(individual: Individual) -> float:
                    if 'risk_score' in individual.objectives:
                        return individual.objectives['risk_score']
                    return float('inf')
                
                objectives.append(ObjectiveFunction(
                    name="risk_score",
                    function=risk_objective,
                    objective_type=ObjectiveType.MINIMIZE
                ))
        
        return objectives
    
    def _create_constraint_function(
        self,
        constraint: OptimizationConstraint,
        base_mission: Mission
    ) -> Callable[[Individual], bool]:
        """Create constraint function for genetic algorithm."""
        def constraint_func(individual: Individual) -> bool:
            try:
                # Convert individual to mission
                mission = self._individual_to_mission(individual, base_mission)
                # Evaluate constraint
                return constraint.constraint_function(mission)
            except Exception:
                return False
        
        constraint_func.__name__ = constraint.name
        return constraint_func
    
    def _create_fitness_function(
        self,
        base_mission: Mission,
        config: OptimizationConfig
    ) -> Callable[[Individual], float]:
        """Create fitness function that runs simulation and evaluates objectives."""
        def fitness_function(individual: Individual) -> float:
            try:
                # Convert individual to mission
                mission = self._individual_to_mission(individual, base_mission)
                
                # Create cache key
                cache_key = self._create_cache_key(individual)
                
                # Check cache first
                if cache_key in self.simulation_cache:
                    sim_result = self.simulation_cache[cache_key]
                else:
                    # Run simulation
                    sim_result = self.simulation_service.simulate_mission(mission)
                    self.simulation_cache[cache_key] = sim_result
                
                # Extract objective values
                individual.objectives.update({
                    'fuel_consumption_kg': sim_result.fuel_consumption_kg,
                    'total_duration_days': sim_result.total_duration_days,
                    'cost_estimate_usd': sim_result.cost_estimate_usd,
                    'success_probability': sim_result.success_probability,
                    'total_delta_v': mission.trajectory.total_delta_v,
                    'risk_score': self._calculate_risk_score(sim_result)
                })
                
                # Calculate combined fitness (for single-objective GA)
                fitness = 0.0
                for obj_type in config.objectives:
                    if obj_type == OptimizationObjective.MINIMIZE_FUEL:
                        fitness -= sim_result.fuel_consumption_kg / 1000.0  # Normalize
                    elif obj_type == OptimizationObjective.MINIMIZE_DURATION:
                        fitness -= sim_result.total_duration_days / 365.0  # Normalize
                    elif obj_type == OptimizationObjective.MINIMIZE_COST:
                        fitness -= sim_result.cost_estimate_usd / 1e9  # Normalize
                    elif obj_type == OptimizationObjective.MAXIMIZE_SUCCESS_PROBABILITY:
                        fitness += sim_result.success_probability
                    elif obj_type == OptimizationObjective.MINIMIZE_DELTA_V:
                        fitness -= mission.trajectory.total_delta_v / 10000.0  # Normalize
                    elif obj_type == OptimizationObjective.MINIMIZE_RISK:
                        fitness -= self._calculate_risk_score(sim_result)
                
                return fitness
                
            except Exception as e:
                logger.warning(f"Fitness evaluation failed: {e}")
                return float('-inf')
        
        return fitness_function
    
    def _individual_to_mission(self, individual: Individual, base_mission: Mission) -> Mission:
        """Convert genetic algorithm individual to mission object."""
        # Create a copy of the base mission
        mission = Mission(
            id=base_mission.id,
            name=base_mission.name,
            description=base_mission.description,
            objectives=base_mission.objectives.copy(),
            spacecraft_config=SpacecraftConfig(**base_mission.spacecraft_config.model_dump()),
            trajectory=TrajectoryPlan(**base_mission.trajectory.model_dump()),
            timeline=base_mission.timeline.model_copy(),
            constraints=base_mission.constraints.model_copy(),
            created_at=base_mission.created_at,
            user_id=base_mission.user_id,
            is_public=base_mission.is_public,
            difficulty_rating=base_mission.difficulty_rating
        )
        
        # Apply parameter values from individual
        for gene_name, gene_value in individual.genes.items():
            self._apply_parameter_to_mission(mission, gene_name, gene_value)
        
        return mission
    
    def _apply_parameter_to_mission(self, mission: Mission, param_name: str, param_value: float):
        """Apply parameter value to mission object."""
        # Map parameter names to mission attributes
        if param_name == "spacecraft_mass_kg":
            mission.spacecraft_config.mass_kg = param_value
        elif param_name == "fuel_capacity_kg":
            mission.spacecraft_config.fuel_capacity_kg = param_value
        elif param_name == "thrust_n":
            mission.spacecraft_config.thrust_n = param_value
        elif param_name == "specific_impulse_s":
            mission.spacecraft_config.specific_impulse_s = param_value
        elif param_name == "payload_mass_kg":
            mission.spacecraft_config.payload_mass_kg = param_value
        elif param_name == "power_w":
            mission.spacecraft_config.power_w = param_value
        elif param_name == "flight_time_days":
            mission.trajectory.flight_time_days = param_value
        elif param_name == "total_delta_v":
            mission.trajectory.total_delta_v = param_value
        # Add more parameter mappings as needed
    
    def _create_cache_key(self, individual: Individual) -> str:
        """Create cache key for simulation results."""
        # Create deterministic key from gene values
        gene_items = sorted(individual.genes.items())
        return str(hash(tuple(gene_items)))
    
    def _calculate_risk_score(self, sim_result: SimulationResult) -> float:
        """Calculate risk score from simulation result."""
        risk_score = 0.0
        
        # Add risk based on success probability
        risk_score += (1.0 - sim_result.success_probability) * 10.0
        
        # Add risk from risk factors
        for risk_factor in sim_result.risk_factors:
            risk_score += risk_factor.probability * 5.0
        
        return risk_score
    
    async def _run_single_objective_ga(
        self,
        ga: GeneticAlgorithm,
        result: OptimizationResult
    ) -> Tuple[Optional[Individual], Dict[str, Any]]:
        """Run single-objective GA with progress tracking."""
        ga.initialize_population()
        
        while not ga._check_convergence():
            # Evolve generation
            ga.evolve_generation()
            
            # Update progress
            result.progress.generation = ga.current_generation
            result.progress.evaluations_completed = ga.current_generation * ga.config.population_size
            result.progress.population_diversity = ga.get_population_diversity()
            
            if ga.best_fitness_history:
                result.progress.best_fitness = ga.best_fitness_history[-1]
            if ga.mean_fitness_history:
                result.progress.mean_fitness = ga.mean_fitness_history[-1]
            if ga.convergence_history:
                result.progress.convergence_metric = ga.convergence_history[-1]
            
            # Get best individual
            best_individual = ga.population.get_best_individual(maximize=True)
            if best_individual:
                result.progress.best_individual = best_individual
            
            # Allow other tasks to run
            await asyncio.sleep(0.01)
        
        # Final evaluation
        ga.evaluate_population(ga.population)
        best_individual = ga.population.get_best_individual(maximize=True)
        
        statistics = {
            'generations': ga.current_generation,
            'best_fitness_history': ga.best_fitness_history,
            'mean_fitness_history': ga.mean_fitness_history,
            'convergence_history': ga.convergence_history,
            'final_population_stats': ga.population.get_fitness_statistics(),
            'feasible_solutions': len(ga.population.get_feasible_individuals()),
            'total_evaluations': ga.current_generation * ga.config.population_size
        }
        
        return best_individual, statistics
    
    async def _run_multi_objective_ga(
        self,
        moga: MultiObjectiveGA,
        result: OptimizationResult
    ) -> Tuple[Optional[Individual], Dict[str, Any]]:
        """Run multi-objective GA with progress tracking."""
        moga.initialize_population()
        
        while not moga._check_convergence():
            # Evolve generation
            moga.evolve_generation()
            
            # Update progress
            result.progress.generation = moga.current_generation
            result.progress.evaluations_completed = moga.current_generation * moga.config.population_size
            result.progress.population_diversity = moga.get_population_diversity()
            
            if moga.best_fitness_history:
                result.progress.best_fitness = moga.best_fitness_history[-1]
            if moga.mean_fitness_history:
                result.progress.mean_fitness = moga.mean_fitness_history[-1]
            if moga.convergence_history:
                result.progress.convergence_metric = moga.convergence_history[-1]
            
            # Get Pareto front information
            pareto_optimal = moga.get_pareto_optimal_solutions()
            result.progress.pareto_front_size = len(pareto_optimal)
            result.progress.pareto_optimal_solutions = pareto_optimal
            
            if pareto_optimal:
                result.progress.best_individual = pareto_optimal[0]
            
            # Allow other tasks to run
            await asyncio.sleep(0.01)
        
        # Final evaluation
        moga.evaluate_population(moga.population)
        pareto_optimal = moga.get_pareto_optimal_solutions()
        best_individual = pareto_optimal[0] if pareto_optimal else None
        
        statistics = {
            'generations': moga.current_generation,
            'best_fitness_history': moga.best_fitness_history,
            'mean_fitness_history': moga.mean_fitness_history,
            'convergence_history': moga.convergence_history,
            'final_population_stats': moga.population.get_fitness_statistics(),
            'feasible_solutions': len(moga.population.get_feasible_individuals()),
            'total_evaluations': moga.current_generation * moga.config.population_size,
            'pareto_front_size': len(pareto_optimal),
            'convergence_metrics': moga.calculate_convergence_metrics()
        }
        
        return best_individual, statistics
    
    def get_optimization_status(self, job_id: UUID) -> Optional[OptimizationResult]:
        """Get optimization job status and results."""
        return self.active_jobs.get(job_id)
    
    def cancel_optimization(self, job_id: UUID) -> bool:
        """Cancel running optimization job."""
        if job_id in self.active_jobs:
            result = self.active_jobs[job_id]
            if result.status == OptimizationStatus.RUNNING:
                result.status = OptimizationStatus.CANCELLED
                result.completed_at = datetime.now()
                logger.info(f"Cancelled optimization job {job_id}")
                return True
        return False
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Clean up old completed optimization jobs."""
        current_time = datetime.now()
        jobs_to_remove = []
        
        for job_id, result in self.active_jobs.items():
            if result.completed_at:
                age_hours = (current_time - result.completed_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
            logger.info(f"Cleaned up old optimization job {job_id}")
    
    def get_active_jobs(self) -> List[OptimizationResult]:
        """Get list of all active optimization jobs."""
        return list(self.active_jobs.values())
    
    def clear_simulation_cache(self):
        """Clear simulation result cache."""
        self.simulation_cache.clear()
        logger.info("Cleared simulation cache")