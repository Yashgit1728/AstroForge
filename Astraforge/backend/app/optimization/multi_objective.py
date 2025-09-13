"""
Multi-objective optimization with Pareto front calculation.

This module implements multi-objective genetic algorithms (MOGA) with
Pareto dominance, non-dominated sorting, and Pareto front management.
"""

from typing import List, Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import numpy as np
from .genetic_algorithm import Individual, Population, GeneticAlgorithm, GAConfig


class ObjectiveType(str, Enum):
    """Objective optimization direction."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


@dataclass
class ObjectiveFunction:
    """Represents a single objective function."""
    name: str
    function: Callable[[Individual], float]
    objective_type: ObjectiveType = ObjectiveType.MINIMIZE
    weight: float = 1.0
    
    def __post_init__(self):
        """Validate objective function."""
        if not self.name:
            raise ValueError("Objective name cannot be empty")
        if self.weight <= 0:
            raise ValueError("Objective weight must be positive")
    
    def evaluate(self, individual: Individual) -> float:
        """Evaluate objective for an individual."""
        try:
            value = self.function(individual)
            # Store in individual's objectives
            individual.objectives[self.name] = value
            return value
        except Exception as e:
            # Handle evaluation errors
            individual.objectives[self.name] = float('inf') if self.objective_type == ObjectiveType.MINIMIZE else float('-inf')
            raise e


def dominates(individual1: Individual, individual2: Individual, objectives: List[ObjectiveFunction]) -> bool:
    """
    Check if individual1 dominates individual2 in Pareto sense.
    
    Args:
        individual1: First individual
        individual2: Second individual
        objectives: List of objective functions
    
    Returns:
        True if individual1 dominates individual2
    """
    if not individual1.objectives or not individual2.objectives:
        return False
    
    better_in_any = False
    
    for obj in objectives:
        obj_name = obj.name
        if obj_name not in individual1.objectives or obj_name not in individual2.objectives:
            continue
        
        val1 = individual1.objectives[obj_name]
        val2 = individual2.objectives[obj_name]
        
        if obj.objective_type == ObjectiveType.MINIMIZE:
            if val1 > val2:  # individual1 is worse in this objective
                return False
            elif val1 < val2:  # individual1 is better in this objective
                better_in_any = True
        else:  # MAXIMIZE
            if val1 < val2:  # individual1 is worse in this objective
                return False
            elif val1 > val2:  # individual1 is better in this objective
                better_in_any = True
    
    return better_in_any


@dataclass
class ParetoFront:
    """Represents a Pareto front of non-dominated solutions."""
    individuals: List[Individual] = field(default_factory=list)
    rank: int = 0
    
    def __len__(self) -> int:
        """Return number of individuals in front."""
        return len(self.individuals)
    
    def __iter__(self):
        """Iterate over individuals in front."""
        return iter(self.individuals)
    
    def add_individual(self, individual: Individual):
        """Add individual to front."""
        self.individuals.append(individual)
    
    def remove_individual(self, individual: Individual):
        """Remove individual from front."""
        if individual in self.individuals:
            self.individuals.remove(individual)
    
    def clear(self):
        """Remove all individuals from front."""
        self.individuals.clear()
    
    def get_objective_ranges(self, objectives: List[ObjectiveFunction]) -> Dict[str, Tuple[float, float]]:
        """Get min/max ranges for each objective in the front."""
        if not self.individuals:
            return {}
        
        ranges = {}
        for obj in objectives:
            obj_name = obj.name
            values = [ind.objectives.get(obj_name, 0) for ind in self.individuals if obj_name in ind.objectives]
            if values:
                ranges[obj_name] = (min(values), max(values))
        
        return ranges
    
    def calculate_hypervolume(self, objectives: List[ObjectiveFunction], reference_point: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate hypervolume indicator for the front.
        
        Args:
            objectives: List of objective functions
            reference_point: Reference point for hypervolume calculation
        
        Returns:
            Hypervolume value
        """
        if not self.individuals or len(objectives) > 3:
            # Hypervolume calculation is complex for >3 objectives
            return 0.0
        
        # Use default reference point if not provided
        if reference_point is None:
            reference_point = {}
            for obj in objectives:
                obj_name = obj.name
                values = [ind.objectives.get(obj_name, 0) for ind in self.individuals if obj_name in ind.objectives]
                if values:
                    if obj.objective_type == ObjectiveType.MINIMIZE:
                        reference_point[obj_name] = max(values) * 1.1
                    else:
                        reference_point[obj_name] = min(values) * 0.9
        
        # Simple hypervolume calculation for 2D case
        if len(objectives) == 2:
            return self._calculate_2d_hypervolume(objectives, reference_point)
        else:
            # For higher dimensions, return approximation
            return len(self.individuals)
    
    def _calculate_2d_hypervolume(self, objectives: List[ObjectiveFunction], reference_point: Dict[str, float]) -> float:
        """Calculate 2D hypervolume using sweep line algorithm."""
        if len(objectives) != 2:
            return 0.0
        
        obj1, obj2 = objectives
        ref1, ref2 = reference_point[obj1.name], reference_point[obj2.name]
        
        # Get points and sort
        points = []
        for ind in self.individuals:
            if obj1.name in ind.objectives and obj2.name in ind.objectives:
                x = ind.objectives[obj1.name]
                y = ind.objectives[obj2.name]
                
                # Transform for minimization
                if obj1.objective_type == ObjectiveType.MAXIMIZE:
                    x = -x
                    ref1 = -ref1
                if obj2.objective_type == ObjectiveType.MAXIMIZE:
                    y = -y
                    ref2 = -ref2
                
                points.append((x, y))
        
        if not points:
            return 0.0
        
        # Sort points by first objective
        points.sort()
        
        # Calculate hypervolume
        hypervolume = 0.0
        prev_x = ref1
        
        for x, y in points:
            if x > prev_x:
                hypervolume += (x - prev_x) * (ref2 - y)
                prev_x = x
        
        return max(0.0, hypervolume)


class NonDominatedSorting:
    """Non-dominated sorting for multi-objective optimization."""
    
    @staticmethod
    def sort(population: Population, objectives: List[ObjectiveFunction]) -> List[ParetoFront]:
        """
        Perform non-dominated sorting on population.
        
        Args:
            population: Population to sort
            objectives: List of objective functions
        
        Returns:
            List of Pareto fronts ordered by rank
        """
        individuals = [ind for ind in population if ind.objectives]
        if not individuals:
            return []
        
        # Initialize domination data
        domination_count = {}  # Number of individuals that dominate this individual
        dominated_individuals = {}  # Individuals dominated by this individual
        
        for ind in individuals:
            domination_count[ind.id] = 0
            dominated_individuals[ind.id] = []
        
        # Calculate domination relationships
        for i, ind1 in enumerate(individuals):
            for j, ind2 in enumerate(individuals):
                if i != j:
                    if dominates(ind1, ind2, objectives):
                        dominated_individuals[ind1.id].append(ind2)
                    elif dominates(ind2, ind1, objectives):
                        domination_count[ind1.id] += 1
        
        # Create fronts
        fronts = []
        current_front = ParetoFront(rank=0)
        
        # First front: individuals with domination count = 0
        for ind in individuals:
            if domination_count[ind.id] == 0:
                current_front.add_individual(ind)
        
        if len(current_front) > 0:
            fronts.append(current_front)
        
        # Subsequent fronts
        front_rank = 0
        while len(fronts[front_rank]) > 0:
            next_front = ParetoFront(rank=front_rank + 1)
            
            for ind1 in fronts[front_rank]:
                for ind2 in dominated_individuals[ind1.id]:
                    domination_count[ind2.id] -= 1
                    if domination_count[ind2.id] == 0:
                        next_front.add_individual(ind2)
            
            if len(next_front) > 0:
                fronts.append(next_front)
                front_rank += 1
            else:
                break
        
        return fronts


class CrowdingDistance:
    """Crowding distance calculation for diversity preservation."""
    
    @staticmethod
    def calculate(front: ParetoFront, objectives: List[ObjectiveFunction]) -> Dict[str, float]:
        """
        Calculate crowding distance for individuals in a front.
        
        Args:
            front: Pareto front
            objectives: List of objective functions
        
        Returns:
            Dictionary mapping individual IDs to crowding distances
        """
        distances = {ind.id: 0.0 for ind in front.individuals}
        
        if len(front) <= 2:
            # Boundary individuals get infinite distance
            for ind in front.individuals:
                distances[ind.id] = float('inf')
            return distances
        
        # Calculate distance for each objective
        for obj in objectives:
            obj_name = obj.name
            
            # Get individuals with this objective value
            valid_individuals = [ind for ind in front.individuals if obj_name in ind.objectives]
            if len(valid_individuals) <= 2:
                continue
            
            # Sort by objective value
            valid_individuals.sort(key=lambda x: x.objectives[obj_name])
            
            # Get objective range
            obj_min = valid_individuals[0].objectives[obj_name]
            obj_max = valid_individuals[-1].objectives[obj_name]
            obj_range = obj_max - obj_min
            
            if obj_range == 0:
                continue
            
            # Boundary individuals get infinite distance
            distances[valid_individuals[0].id] = float('inf')
            distances[valid_individuals[-1].id] = float('inf')
            
            # Calculate distance for interior individuals
            for i in range(1, len(valid_individuals) - 1):
                prev_val = valid_individuals[i - 1].objectives[obj_name]
                next_val = valid_individuals[i + 1].objectives[obj_name]
                distances[valid_individuals[i].id] += (next_val - prev_val) / obj_range
        
        return distances


class MultiObjectiveGA(GeneticAlgorithm):
    """Multi-objective genetic algorithm implementation."""
    
    def __init__(
        self,
        config: GAConfig,
        objectives: List[ObjectiveFunction],
        gene_bounds: Dict[str, Tuple[float, float]],
        constraint_functions: Optional[List[Callable[[Individual], bool]]] = None,
        **kwargs
    ):
        """
        Initialize multi-objective genetic algorithm.
        
        Args:
            config: GA configuration
            objectives: List of objective functions
            gene_bounds: Gene bounds dictionary
            constraint_functions: Constraint functions
            **kwargs: Additional arguments for parent class
        """
        if not objectives:
            raise ValueError("At least one objective function must be provided")
        
        self.objectives = objectives
        
        # Create combined fitness function for parent class
        def combined_fitness(individual: Individual) -> float:
            # Evaluate all objectives
            total_fitness = 0.0
            for obj in self.objectives:
                try:
                    value = obj.evaluate(individual)
                    # Normalize and weight
                    if obj.objective_type == ObjectiveType.MAXIMIZE:
                        total_fitness += obj.weight * value
                    else:
                        total_fitness -= obj.weight * value
                except Exception:
                    return float('-inf')
            return total_fitness
        
        super().__init__(
            config=config,
            fitness_function=combined_fitness,
            gene_bounds=gene_bounds,
            constraint_functions=constraint_functions,
            **kwargs
        )
        
        # Multi-objective specific attributes
        self.pareto_fronts: List[ParetoFront] = []
        self.pareto_front_history: List[List[ParetoFront]] = []
    
    def evaluate_population(self, population: Population):
        """Evaluate population with multi-objective functions."""
        for individual in population:
            if not individual.is_evaluated:
                self._evaluate_individual_multi_objective(individual)
    
    def _evaluate_individual_multi_objective(self, individual: Individual):
        """Evaluate individual with all objective functions."""
        # Check constraints first
        individual.constraints_violated = []
        for constraint_func in self.constraint_functions:
            if not constraint_func(individual):
                individual.constraints_violated.append(constraint_func.__name__)
        
        # Evaluate all objectives
        individual.objectives.clear()
        total_fitness = 0.0
        
        for obj in self.objectives:
            try:
                value = obj.evaluate(individual)
                # Contribute to combined fitness
                if obj.objective_type == ObjectiveType.MAXIMIZE:
                    total_fitness += obj.weight * value
                else:
                    total_fitness -= obj.weight * value
            except Exception as e:
                individual.fitness = float('-inf')
                individual.constraints_violated.append(f"objective_error_{obj.name}: {str(e)}")
                return
        
        individual.fitness = total_fitness
    
    def evolve_generation(self) -> Population:
        """Evolve population using NSGA-II-like approach."""
        # Evaluate population
        self.evaluate_population(self.population)
        
        # Perform non-dominated sorting
        self.pareto_fronts = NonDominatedSorting.sort(self.population, self.objectives)
        
        # Track Pareto front history
        self.pareto_front_history.append([front for front in self.pareto_fronts])
        
        # Update statistics
        self._update_statistics()
        
        # Check convergence
        if self._check_convergence():
            return self.population
        
        # Create new population using NSGA-II selection
        new_population = self._nsga2_selection()
        
        # Apply genetic operators
        offspring_population = self._generate_offspring(new_population)
        
        # Combine parent and offspring populations
        combined_population = Population(max_size=len(new_population) + len(offspring_population))
        for ind in new_population:
            combined_population.add_individual(ind)
        for ind in offspring_population:
            combined_population.add_individual(ind)
        
        # Evaluate combined population
        self.evaluate_population(combined_population)
        
        # Select next generation
        self.population = self._nsga2_environmental_selection(combined_population)
        self.current_generation += 1
        self.population.generation = self.current_generation
        
        return self.population
    
    def _nsga2_selection(self) -> Population:
        """Select parents using NSGA-II approach."""
        selected_population = Population(max_size=self.config.population_size)
        
        # Add individuals from fronts in order
        for front in self.pareto_fronts:
            if len(selected_population) + len(front) <= self.config.population_size:
                # Add entire front
                for ind in front:
                    selected_population.add_individual(ind.copy())
            else:
                # Add partial front using crowding distance
                remaining_slots = self.config.population_size - len(selected_population)
                if remaining_slots > 0:
                    distances = CrowdingDistance.calculate(front, self.objectives)
                    # Sort by crowding distance (descending)
                    sorted_individuals = sorted(
                        front.individuals,
                        key=lambda x: distances[x.id],
                        reverse=True
                    )
                    for i in range(remaining_slots):
                        selected_population.add_individual(sorted_individuals[i].copy())
                break
        
        return selected_population
    
    def _generate_offspring(self, parent_population: Population) -> Population:
        """Generate offspring using genetic operators."""
        if not self.selection_operator or not self.crossover_operator or not self.mutation_operator:
            raise ValueError("Genetic operators must be set before evolution")
        
        offspring_population = Population(max_size=self.config.population_size)
        
        while len(offspring_population) < self.config.population_size:
            # Selection
            parents = self.selection_operator.select(parent_population, 2)
            if len(parents) < 2:
                break
            
            # Crossover
            if random.random() < self.config.crossover_rate:
                offspring1, offspring2 = self.crossover_operator.crossover(parents[0], parents[1])
            else:
                offspring1, offspring2 = parents[0].copy(), parents[1].copy()
            
            # Mutation
            offspring1 = self.mutation_operator.mutate(offspring1, self.config.mutation_rate)
            offspring2 = self.mutation_operator.mutate(offspring2, self.config.mutation_rate)
            
            # Add to offspring population
            if len(offspring_population) < self.config.population_size:
                offspring_population.add_individual(offspring1)
            if len(offspring_population) < self.config.population_size:
                offspring_population.add_individual(offspring2)
        
        return offspring_population
    
    def _nsga2_environmental_selection(self, combined_population: Population) -> Population:
        """Select next generation using NSGA-II environmental selection."""
        # Perform non-dominated sorting
        fronts = NonDominatedSorting.sort(combined_population, self.objectives)
        
        new_population = Population(max_size=self.config.population_size)
        
        # Add individuals from fronts
        for front in fronts:
            if len(new_population) + len(front) <= self.config.population_size:
                # Add entire front
                for ind in front:
                    new_population.add_individual(ind)
            else:
                # Add partial front using crowding distance
                remaining_slots = self.config.population_size - len(new_population)
                if remaining_slots > 0:
                    distances = CrowdingDistance.calculate(front, self.objectives)
                    # Sort by crowding distance (descending)
                    sorted_individuals = sorted(
                        front.individuals,
                        key=lambda x: distances[x.id],
                        reverse=True
                    )
                    for i in range(remaining_slots):
                        new_population.add_individual(sorted_individuals[i])
                break
        
        return new_population
    
    def get_pareto_front(self, rank: int = 0) -> Optional[ParetoFront]:
        """Get Pareto front by rank."""
        if 0 <= rank < len(self.pareto_fronts):
            return self.pareto_fronts[rank]
        return None
    
    def get_pareto_optimal_solutions(self) -> List[Individual]:
        """Get all Pareto optimal solutions (rank 0)."""
        front = self.get_pareto_front(0)
        return front.individuals if front else []
    
    def calculate_convergence_metrics(self) -> Dict[str, float]:
        """Calculate multi-objective convergence metrics."""
        if not self.pareto_fronts or len(self.pareto_fronts) == 0:
            return {}
        
        first_front = self.pareto_fronts[0]
        
        metrics = {
            'pareto_front_size': len(first_front),
            'total_fronts': len(self.pareto_fronts),
            'hypervolume': first_front.calculate_hypervolume(self.objectives)
        }
        
        # Calculate spacing metric (diversity)
        if len(first_front) > 1:
            distances = []
            individuals = first_front.individuals
            
            for i, ind1 in enumerate(individuals):
                min_distance = float('inf')
                for j, ind2 in enumerate(individuals):
                    if i != j:
                        # Calculate Euclidean distance in objective space
                        distance = 0.0
                        for obj in self.objectives:
                            obj_name = obj.name
                            if obj_name in ind1.objectives and obj_name in ind2.objectives:
                                diff = ind1.objectives[obj_name] - ind2.objectives[obj_name]
                                distance += diff ** 2
                        distance = np.sqrt(distance)
                        min_distance = min(min_distance, distance)
                
                if min_distance != float('inf'):
                    distances.append(min_distance)
            
            if distances:
                mean_distance = np.mean(distances)
                spacing = np.sqrt(np.mean([(d - mean_distance) ** 2 for d in distances]))
                metrics['spacing'] = spacing
        
        return metrics