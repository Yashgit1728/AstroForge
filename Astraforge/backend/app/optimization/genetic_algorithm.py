"""
Core genetic algorithm framework for mission parameter optimization.

This module provides the base classes and interfaces for genetic algorithm
implementation, including individual representation, population management,
and evolution operators.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import random
import numpy as np
from uuid import uuid4, UUID


class SelectionMethod(str, Enum):
    """Selection methods for genetic algorithm."""
    TOURNAMENT = "tournament"
    ROULETTE_WHEEL = "roulette_wheel"
    RANK = "rank"
    ELITIST = "elitist"


class CrossoverMethod(str, Enum):
    """Crossover methods for genetic algorithm."""
    SINGLE_POINT = "single_point"
    TWO_POINT = "two_point"
    UNIFORM = "uniform"
    ARITHMETIC = "arithmetic"


class MutationMethod(str, Enum):
    """Mutation methods for genetic algorithm."""
    GAUSSIAN = "gaussian"
    UNIFORM = "uniform"
    POLYNOMIAL = "polynomial"
    ADAPTIVE = "adaptive"


@dataclass
class Individual:
    """
    Represents an individual solution in the genetic algorithm.
    
    Each individual contains genes (parameters), fitness values,
    and metadata for tracking evolution progress.
    """
    id: UUID = field(default_factory=uuid4)
    genes: Dict[str, float] = field(default_factory=dict)
    fitness: Optional[float] = None
    objectives: Dict[str, float] = field(default_factory=dict)
    constraints_violated: List[str] = field(default_factory=list)
    generation: int = 0
    parent_ids: List[UUID] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate individual after initialization."""
        if not self.genes:
            raise ValueError("Individual must have at least one gene")
    
    @property
    def is_feasible(self) -> bool:
        """Check if individual satisfies all constraints."""
        return len(self.constraints_violated) == 0
    
    @property
    def is_evaluated(self) -> bool:
        """Check if individual has been evaluated."""
        return self.fitness is not None
    
    def copy(self) -> 'Individual':
        """Create a deep copy of the individual."""
        return Individual(
            id=uuid4(),
            genes=self.genes.copy(),
            fitness=self.fitness,
            objectives=self.objectives.copy(),
            constraints_violated=self.constraints_violated.copy(),
            generation=self.generation,
            parent_ids=[self.id]
        )
    
    def get_gene_vector(self, gene_names: List[str]) -> np.ndarray:
        """Get genes as numpy array in specified order."""
        return np.array([self.genes[name] for name in gene_names])
    
    def set_gene_vector(self, gene_names: List[str], values: np.ndarray):
        """Set genes from numpy array in specified order."""
        if len(gene_names) != len(values):
            raise ValueError("Gene names and values must have same length")
        
        for name, value in zip(gene_names, values):
            self.genes[name] = float(value)


@dataclass
class Population:
    """
    Manages a population of individuals in the genetic algorithm.
    
    Provides methods for population initialization, evaluation,
    and statistical analysis.
    """
    individuals: List[Individual] = field(default_factory=list)
    generation: int = 0
    max_size: int = 100
    
    def __post_init__(self):
        """Validate population after initialization."""
        if self.max_size <= 0:
            raise ValueError("Population max_size must be positive")
    
    def __len__(self) -> int:
        """Return population size."""
        return len(self.individuals)
    
    def __iter__(self):
        """Iterate over individuals."""
        return iter(self.individuals)
    
    def __getitem__(self, index: int) -> Individual:
        """Get individual by index."""
        return self.individuals[index]
    
    def add_individual(self, individual: Individual):
        """Add individual to population."""
        if len(self.individuals) >= self.max_size:
            raise ValueError(f"Population already at maximum size ({self.max_size})")
        
        individual.generation = self.generation
        self.individuals.append(individual)
    
    def remove_individual(self, index: int) -> Individual:
        """Remove and return individual at index."""
        if not 0 <= index < len(self.individuals):
            raise IndexError("Individual index out of range")
        
        return self.individuals.pop(index)
    
    def clear(self):
        """Remove all individuals from population."""
        self.individuals.clear()
    
    def get_best_individual(self, maximize: bool = True) -> Optional[Individual]:
        """Get individual with best fitness."""
        if not self.individuals:
            return None
        
        evaluated_individuals = [ind for ind in self.individuals if ind.is_evaluated]
        if not evaluated_individuals:
            return None
        
        if maximize:
            return max(evaluated_individuals, key=lambda x: x.fitness)
        else:
            return min(evaluated_individuals, key=lambda x: x.fitness)
    
    def get_feasible_individuals(self) -> List[Individual]:
        """Get all feasible individuals."""
        return [ind for ind in self.individuals if ind.is_feasible]
    
    def get_fitness_statistics(self) -> Dict[str, float]:
        """Calculate fitness statistics for evaluated individuals."""
        evaluated = [ind for ind in self.individuals if ind.is_evaluated]
        if not evaluated:
            return {}
        
        fitness_values = [ind.fitness for ind in evaluated]
        return {
            'mean': np.mean(fitness_values),
            'std': np.std(fitness_values),
            'min': np.min(fitness_values),
            'max': np.max(fitness_values),
            'median': np.median(fitness_values)
        }
    
    def sort_by_fitness(self, maximize: bool = True):
        """Sort population by fitness (in-place)."""
        evaluated = [ind for ind in self.individuals if ind.is_evaluated]
        unevaluated = [ind for ind in self.individuals if not ind.is_evaluated]
        
        evaluated.sort(key=lambda x: x.fitness, reverse=maximize)
        self.individuals = evaluated + unevaluated


class GeneticOperator(ABC):
    """Abstract base class for genetic operators."""
    
    @abstractmethod
    def apply(self, *args, **kwargs) -> Any:
        """Apply the genetic operator."""
        pass


class SelectionOperator(GeneticOperator):
    """Abstract base class for selection operators."""
    
    @abstractmethod
    def select(self, population: Population, num_parents: int) -> List[Individual]:
        """Select parents from population."""
        pass


class CrossoverOperator(GeneticOperator):
    """Abstract base class for crossover operators."""
    
    @abstractmethod
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Perform crossover between two parents."""
        pass


class MutationOperator(GeneticOperator):
    """Abstract base class for mutation operators."""
    
    @abstractmethod
    def mutate(self, individual: Individual, mutation_rate: float) -> Individual:
        """Mutate an individual."""
        pass


@dataclass
class GAConfig:
    """Configuration parameters for genetic algorithm."""
    population_size: int = 100
    max_generations: int = 100
    selection_method: SelectionMethod = SelectionMethod.TOURNAMENT
    crossover_method: CrossoverMethod = CrossoverMethod.UNIFORM
    mutation_method: MutationMethod = MutationMethod.GAUSSIAN
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    elitism_rate: float = 0.1
    tournament_size: int = 3
    convergence_threshold: float = 1e-6
    max_stagnant_generations: int = 20
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.population_size <= 0:
            raise ValueError("Population size must be positive")
        if self.max_generations <= 0:
            raise ValueError("Max generations must be positive")
        if not 0 <= self.crossover_rate <= 1:
            raise ValueError("Crossover rate must be between 0 and 1")
        if not 0 <= self.mutation_rate <= 1:
            raise ValueError("Mutation rate must be between 0 and 1")
        if not 0 <= self.elitism_rate <= 1:
            raise ValueError("Elitism rate must be between 0 and 1")
        if self.tournament_size <= 0:
            raise ValueError("Tournament size must be positive")


class GeneticAlgorithm:
    """
    Main genetic algorithm implementation.
    
    Provides a flexible framework for evolutionary optimization with
    configurable operators and parameters.
    """
    
    def __init__(
        self,
        config: GAConfig,
        fitness_function: Callable[[Individual], float],
        gene_bounds: Dict[str, Tuple[float, float]],
        constraint_functions: Optional[List[Callable[[Individual], bool]]] = None,
        selection_operator: Optional[SelectionOperator] = None,
        crossover_operator: Optional[CrossoverOperator] = None,
        mutation_operator: Optional[MutationOperator] = None
    ):
        """
        Initialize genetic algorithm.
        
        Args:
            config: GA configuration parameters
            fitness_function: Function to evaluate individual fitness
            gene_bounds: Dictionary mapping gene names to (min, max) bounds
            constraint_functions: List of constraint validation functions
            selection_operator: Custom selection operator (optional)
            crossover_operator: Custom crossover operator (optional)
            mutation_operator: Custom mutation operator (optional)
        """
        self.config = config
        self.fitness_function = fitness_function
        self.gene_bounds = gene_bounds
        self.constraint_functions = constraint_functions or []
        
        # Initialize operators (will be set in operators.py)
        self.selection_operator = selection_operator
        self.crossover_operator = crossover_operator
        self.mutation_operator = mutation_operator
        
        # Evolution tracking
        self.current_generation = 0
        self.best_fitness_history: List[float] = []
        self.mean_fitness_history: List[float] = []
        self.convergence_history: List[float] = []
        self.stagnant_generations = 0
        
        # Population
        self.population = Population(max_size=config.population_size)
        
        # Validate gene bounds
        if not gene_bounds:
            raise ValueError("Gene bounds must be specified")
        
        for gene_name, (min_val, max_val) in gene_bounds.items():
            if min_val >= max_val:
                raise ValueError(f"Invalid bounds for gene {gene_name}: min >= max")
    
    def initialize_population(self) -> Population:
        """Initialize population with random individuals."""
        self.population.clear()
        
        for _ in range(self.config.population_size):
            individual = self._create_random_individual()
            self.population.add_individual(individual)
        
        return self.population
    
    def _create_random_individual(self) -> Individual:
        """Create a random individual within gene bounds."""
        genes = {}
        for gene_name, (min_val, max_val) in self.gene_bounds.items():
            genes[gene_name] = random.uniform(min_val, max_val)
        
        return Individual(genes=genes)
    
    def evaluate_population(self, population: Population):
        """Evaluate fitness for all individuals in population."""
        for individual in population:
            if not individual.is_evaluated:
                self._evaluate_individual(individual)
    
    def _evaluate_individual(self, individual: Individual):
        """Evaluate a single individual."""
        # Check constraints
        individual.constraints_violated = []
        for constraint_func in self.constraint_functions:
            if not constraint_func(individual):
                individual.constraints_violated.append(constraint_func.__name__)
        
        # Calculate fitness
        try:
            individual.fitness = self.fitness_function(individual)
        except Exception as e:
            # Handle evaluation errors by assigning poor fitness
            individual.fitness = float('-inf')
            individual.constraints_violated.append(f"evaluation_error: {str(e)}")
    
    def evolve_generation(self) -> Population:
        """Evolve population for one generation."""
        if not self.selection_operator or not self.crossover_operator or not self.mutation_operator:
            raise ValueError("Genetic operators must be set before evolution")
        
        # Evaluate current population
        self.evaluate_population(self.population)
        
        # Track statistics
        self._update_statistics()
        
        # Check convergence
        if self._check_convergence():
            return self.population
        
        # Create new population
        new_population = Population(max_size=self.config.population_size)
        
        # Elitism: keep best individuals
        num_elites = int(self.config.elitism_rate * self.config.population_size)
        if num_elites > 0:
            self.population.sort_by_fitness(maximize=True)
            for i in range(num_elites):
                elite = self.population[i].copy()
                new_population.add_individual(elite)
        
        # Generate offspring
        while len(new_population) < self.config.population_size:
            # Selection
            parents = self.selection_operator.select(self.population, 2)
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
            
            # Add to new population
            if len(new_population) < self.config.population_size:
                new_population.add_individual(offspring1)
            if len(new_population) < self.config.population_size:
                new_population.add_individual(offspring2)
        
        # Update population and generation
        self.population = new_population
        self.current_generation += 1
        self.population.generation = self.current_generation
        
        return self.population
    
    def _update_statistics(self):
        """Update evolution statistics."""
        stats = self.population.get_fitness_statistics()
        if stats:
            best_fitness = stats['max']
            mean_fitness = stats['mean']
            
            self.best_fitness_history.append(best_fitness)
            self.mean_fitness_history.append(mean_fitness)
            
            # Calculate convergence metric
            if len(self.best_fitness_history) > 1:
                fitness_change = abs(best_fitness - self.best_fitness_history[-2])
                self.convergence_history.append(fitness_change)
                
                # Check stagnation
                if fitness_change < self.config.convergence_threshold:
                    self.stagnant_generations += 1
                else:
                    self.stagnant_generations = 0
    
    def _check_convergence(self) -> bool:
        """Check if algorithm has converged."""
        # Check maximum generations
        if self.current_generation >= self.config.max_generations:
            return True
        
        # Check stagnation
        if self.stagnant_generations >= self.config.max_stagnant_generations:
            return True
        
        return False
    
    def run(self) -> Tuple[Individual, Dict[str, Any]]:
        """
        Run the genetic algorithm until convergence.
        
        Returns:
            Tuple of (best_individual, evolution_statistics)
        """
        # Initialize population
        self.initialize_population()
        
        # Evolution loop
        while not self._check_convergence():
            self.evolve_generation()
        
        # Final evaluation
        self.evaluate_population(self.population)
        
        # Get best individual
        best_individual = self.population.get_best_individual(maximize=True)
        
        # Compile statistics
        statistics = {
            'generations': self.current_generation,
            'best_fitness_history': self.best_fitness_history,
            'mean_fitness_history': self.mean_fitness_history,
            'convergence_history': self.convergence_history,
            'final_population_stats': self.population.get_fitness_statistics(),
            'feasible_solutions': len(self.population.get_feasible_individuals()),
            'total_evaluations': self.current_generation * self.config.population_size
        }
        
        return best_individual, statistics
    
    def get_population_diversity(self) -> float:
        """Calculate population diversity based on gene variance."""
        if len(self.population) < 2:
            return 0.0
        
        gene_names = list(self.gene_bounds.keys())
        gene_matrix = np.array([
            ind.get_gene_vector(gene_names) for ind in self.population
        ])
        
        # Calculate average pairwise distance
        total_distance = 0.0
        count = 0
        
        for i in range(len(gene_matrix)):
            for j in range(i + 1, len(gene_matrix)):
                distance = np.linalg.norm(gene_matrix[i] - gene_matrix[j])
                total_distance += distance
                count += 1
        
        return total_distance / count if count > 0 else 0.0