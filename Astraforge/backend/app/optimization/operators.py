"""
Genetic algorithm operators for selection, crossover, and mutation.

This module implements various genetic operators that can be used
with the genetic algorithm framework.
"""

import random
import numpy as np
from typing import List, Tuple
from .genetic_algorithm import (
    Individual, Population, SelectionOperator, 
    CrossoverOperator, MutationOperator
)


class TournamentSelection(SelectionOperator):
    """Tournament selection operator."""
    
    def __init__(self, tournament_size: int = 3):
        """
        Initialize tournament selection.
        
        Args:
            tournament_size: Number of individuals in each tournament
        """
        if tournament_size <= 0:
            raise ValueError("Tournament size must be positive")
        self.tournament_size = tournament_size
    
    def apply(self, *args, **kwargs):
        """Apply tournament selection (delegates to select method)."""
        return self.select(*args, **kwargs)
    
    def select(self, population: Population, num_parents: int) -> List[Individual]:
        """Select parents using tournament selection."""
        if len(population) == 0:
            return []
        
        # Get only evaluated individuals
        evaluated_individuals = [ind for ind in population if ind.is_evaluated]
        if not evaluated_individuals:
            return []
        
        parents = []
        for _ in range(num_parents):
            # Select tournament participants
            tournament_size = min(self.tournament_size, len(evaluated_individuals))
            tournament = random.sample(evaluated_individuals, tournament_size)
            
            # Select winner (highest fitness)
            winner = max(tournament, key=lambda x: x.fitness if x.fitness is not None else float('-inf'))
            parents.append(winner)
        
        return parents


class RouletteWheelSelection(SelectionOperator):
    """Roulette wheel (fitness proportionate) selection operator."""
    
    def __init__(self, scaling_factor: float = 1.0):
        """
        Initialize roulette wheel selection.
        
        Args:
            scaling_factor: Factor to scale fitness values for selection pressure
        """
        self.scaling_factor = scaling_factor
    
    def apply(self, *args, **kwargs):
        """Apply roulette wheel selection (delegates to select method)."""
        return self.select(*args, **kwargs)
    
    def select(self, population: Population, num_parents: int) -> List[Individual]:
        """Select parents using roulette wheel selection."""
        evaluated_individuals = [ind for ind in population if ind.is_evaluated]
        if not evaluated_individuals:
            return []
        
        # Get fitness values and handle negative fitness
        fitness_values = [ind.fitness for ind in evaluated_individuals]
        min_fitness = min(fitness_values)
        
        # Shift fitness values to be non-negative
        if min_fitness < 0:
            adjusted_fitness = [f - min_fitness + 1e-6 for f in fitness_values]
        else:
            adjusted_fitness = [f + 1e-6 for f in fitness_values]  # Add small value to avoid zero
        
        # Apply scaling
        scaled_fitness = [f ** self.scaling_factor for f in adjusted_fitness]
        total_fitness = sum(scaled_fitness)
        
        if total_fitness == 0:
            # Fallback to random selection
            return random.sample(evaluated_individuals, min(num_parents, len(evaluated_individuals)))
        
        # Calculate selection probabilities
        probabilities = [f / total_fitness for f in scaled_fitness]
        
        # Select parents
        parents = []
        for _ in range(num_parents):
            r = random.random()
            cumulative_prob = 0.0
            
            for i, prob in enumerate(probabilities):
                cumulative_prob += prob
                if r <= cumulative_prob:
                    parents.append(evaluated_individuals[i])
                    break
            else:
                # Fallback if rounding errors occur
                parents.append(evaluated_individuals[-1])
        
        return parents


class UniformCrossover(CrossoverOperator):
    """Uniform crossover operator."""
    
    def __init__(self, swap_probability: float = 0.5):
        """
        Initialize uniform crossover.
        
        Args:
            swap_probability: Probability of swapping each gene
        """
        if not 0 <= swap_probability <= 1:
            raise ValueError("Swap probability must be between 0 and 1")
        self.swap_probability = swap_probability
    
    def apply(self, *args, **kwargs):
        """Apply uniform crossover (delegates to crossover method)."""
        return self.crossover(*args, **kwargs)
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Perform uniform crossover between two parents."""
        # Create offspring copies
        offspring1 = parent1.copy()
        offspring2 = parent2.copy()
        
        # Get common genes
        common_genes = set(parent1.genes.keys()) & set(parent2.genes.keys())
        
        # Perform uniform crossover
        for gene_name in common_genes:
            if random.random() < self.swap_probability:
                # Swap genes
                offspring1.genes[gene_name] = parent2.genes[gene_name]
                offspring2.genes[gene_name] = parent1.genes[gene_name]
        
        # Update parent information
        offspring1.parent_ids = [parent1.id, parent2.id]
        offspring2.parent_ids = [parent1.id, parent2.id]
        
        # Reset fitness (needs re-evaluation)
        offspring1.fitness = None
        offspring2.fitness = None
        offspring1.objectives.clear()
        offspring2.objectives.clear()
        offspring1.constraints_violated.clear()
        offspring2.constraints_violated.clear()
        
        return offspring1, offspring2


class SinglePointCrossover(CrossoverOperator):
    """Single-point crossover operator."""
    
    def apply(self, *args, **kwargs):
        """Apply single-point crossover (delegates to crossover method)."""
        return self.crossover(*args, **kwargs)
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Perform single-point crossover between two parents."""
        # Get common genes
        common_genes = list(set(parent1.genes.keys()) & set(parent2.genes.keys()))
        if len(common_genes) <= 1:
            # Not enough genes for crossover, return copies
            return parent1.copy(), parent2.copy()
        
        # Select crossover point
        crossover_point = random.randint(1, len(common_genes) - 1)
        
        # Create offspring
        offspring1 = parent1.copy()
        offspring2 = parent2.copy()
        
        # Perform crossover
        for i, gene_name in enumerate(common_genes):
            if i >= crossover_point:
                offspring1.genes[gene_name] = parent2.genes[gene_name]
                offspring2.genes[gene_name] = parent1.genes[gene_name]
        
        # Update parent information
        offspring1.parent_ids = [parent1.id, parent2.id]
        offspring2.parent_ids = [parent1.id, parent2.id]
        
        # Reset fitness
        offspring1.fitness = None
        offspring2.fitness = None
        offspring1.objectives.clear()
        offspring2.objectives.clear()
        offspring1.constraints_violated.clear()
        offspring2.constraints_violated.clear()
        
        return offspring1, offspring2


class ArithmeticCrossover(CrossoverOperator):
    """Arithmetic crossover operator for real-valued genes."""
    
    def __init__(self, alpha: float = 0.5):
        """
        Initialize arithmetic crossover.
        
        Args:
            alpha: Blending factor (0.5 = average, 0 = parent1, 1 = parent2)
        """
        if not 0 <= alpha <= 1:
            raise ValueError("Alpha must be between 0 and 1")
        self.alpha = alpha
    
    def apply(self, *args, **kwargs):
        """Apply arithmetic crossover (delegates to crossover method)."""
        return self.crossover(*args, **kwargs)
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Perform arithmetic crossover between two parents."""
        # Create offspring
        offspring1 = parent1.copy()
        offspring2 = parent2.copy()
        
        # Get common genes
        common_genes = set(parent1.genes.keys()) & set(parent2.genes.keys())
        
        # Perform arithmetic crossover
        for gene_name in common_genes:
            gene1 = parent1.genes[gene_name]
            gene2 = parent2.genes[gene_name]
            
            # Arithmetic combination
            offspring1.genes[gene_name] = self.alpha * gene1 + (1 - self.alpha) * gene2
            offspring2.genes[gene_name] = (1 - self.alpha) * gene1 + self.alpha * gene2
        
        # Update parent information
        offspring1.parent_ids = [parent1.id, parent2.id]
        offspring2.parent_ids = [parent1.id, parent2.id]
        
        # Reset fitness
        offspring1.fitness = None
        offspring2.fitness = None
        offspring1.objectives.clear()
        offspring2.objectives.clear()
        offspring1.constraints_violated.clear()
        offspring2.constraints_violated.clear()
        
        return offspring1, offspring2


class GaussianMutation(MutationOperator):
    """Gaussian mutation operator."""
    
    def __init__(self, sigma: float = 0.1, gene_bounds: dict = None):
        """
        Initialize Gaussian mutation.
        
        Args:
            sigma: Standard deviation for Gaussian noise (relative to gene range)
            gene_bounds: Dictionary of gene bounds for constraint enforcement
        """
        if sigma <= 0:
            raise ValueError("Sigma must be positive")
        self.sigma = sigma
        self.gene_bounds = gene_bounds or {}
    
    def apply(self, *args, **kwargs):
        """Apply Gaussian mutation (delegates to mutate method)."""
        return self.mutate(*args, **kwargs)
    
    def mutate(self, individual: Individual, mutation_rate: float) -> Individual:
        """Apply Gaussian mutation to individual."""
        mutated = individual.copy()
        
        for gene_name, gene_value in mutated.genes.items():
            if random.random() < mutation_rate:
                # Calculate mutation strength based on gene bounds
                if gene_name in self.gene_bounds:
                    min_val, max_val = self.gene_bounds[gene_name]
                    gene_range = max_val - min_val
                    noise = random.gauss(0, self.sigma * gene_range)
                else:
                    # Use absolute sigma if no bounds available
                    noise = random.gauss(0, self.sigma)
                
                # Apply mutation
                new_value = gene_value + noise
                
                # Enforce bounds if available
                if gene_name in self.gene_bounds:
                    min_val, max_val = self.gene_bounds[gene_name]
                    new_value = max(min_val, min(max_val, new_value))
                
                mutated.genes[gene_name] = new_value
        
        # Reset fitness (needs re-evaluation)
        mutated.fitness = None
        mutated.objectives.clear()
        mutated.constraints_violated.clear()
        
        return mutated


class UniformMutation(MutationOperator):
    """Uniform mutation operator."""
    
    def __init__(self, gene_bounds: dict):
        """
        Initialize uniform mutation.
        
        Args:
            gene_bounds: Dictionary of gene bounds for mutation range
        """
        if not gene_bounds:
            raise ValueError("Gene bounds must be provided for uniform mutation")
        self.gene_bounds = gene_bounds
    
    def apply(self, *args, **kwargs):
        """Apply uniform mutation (delegates to mutate method)."""
        return self.mutate(*args, **kwargs)
    
    def mutate(self, individual: Individual, mutation_rate: float) -> Individual:
        """Apply uniform mutation to individual."""
        mutated = individual.copy()
        
        for gene_name, gene_value in mutated.genes.items():
            if random.random() < mutation_rate and gene_name in self.gene_bounds:
                min_val, max_val = self.gene_bounds[gene_name]
                mutated.genes[gene_name] = random.uniform(min_val, max_val)
        
        # Reset fitness (needs re-evaluation)
        mutated.fitness = None
        mutated.objectives.clear()
        mutated.constraints_violated.clear()
        
        return mutated


class PolynomialMutation(MutationOperator):
    """Polynomial mutation operator (commonly used in NSGA-II)."""
    
    def __init__(self, eta: float = 20.0, gene_bounds: dict = None):
        """
        Initialize polynomial mutation.
        
        Args:
            eta: Distribution index (higher values = lower mutation strength)
            gene_bounds: Dictionary of gene bounds for constraint enforcement
        """
        if eta <= 0:
            raise ValueError("Eta must be positive")
        self.eta = eta
        self.gene_bounds = gene_bounds or {}
    
    def apply(self, *args, **kwargs):
        """Apply polynomial mutation (delegates to mutate method)."""
        return self.mutate(*args, **kwargs)
    
    def mutate(self, individual: Individual, mutation_rate: float) -> Individual:
        """Apply polynomial mutation to individual."""
        mutated = individual.copy()
        
        for gene_name, gene_value in mutated.genes.items():
            if random.random() < mutation_rate and gene_name in self.gene_bounds:
                min_val, max_val = self.gene_bounds[gene_name]
                
                # Normalize gene value
                normalized_value = (gene_value - min_val) / (max_val - min_val)
                
                # Generate random number
                u = random.random()
                
                # Calculate delta
                if u <= 0.5:
                    delta = (2 * u) ** (1 / (self.eta + 1)) - 1
                else:
                    delta = 1 - (2 * (1 - u)) ** (1 / (self.eta + 1))
                
                # Apply mutation
                new_normalized = normalized_value + delta
                new_normalized = max(0, min(1, new_normalized))  # Clamp to [0, 1]
                
                # Denormalize
                mutated.genes[gene_name] = min_val + new_normalized * (max_val - min_val)
        
        # Reset fitness (needs re-evaluation)
        mutated.fitness = None
        mutated.objectives.clear()
        mutated.constraints_violated.clear()
        
        return mutated


class AdaptiveMutation(MutationOperator):
    """Adaptive mutation that adjusts strength based on population diversity."""
    
    def __init__(self, base_sigma: float = 0.1, gene_bounds: dict = None):
        """
        Initialize adaptive mutation.
        
        Args:
            base_sigma: Base mutation strength
            gene_bounds: Dictionary of gene bounds for constraint enforcement
        """
        self.base_sigma = base_sigma
        self.gene_bounds = gene_bounds or {}
        self.diversity_history = []
    
    def apply(self, *args, **kwargs):
        """Apply adaptive mutation (delegates to mutate method)."""
        return self.mutate(*args, **kwargs)
    
    def mutate(self, individual: Individual, mutation_rate: float) -> Individual:
        """Apply adaptive mutation to individual."""
        # Use Gaussian mutation with adaptive sigma
        # (Adaptation logic would be implemented in the GA main loop)
        gaussian_mutator = GaussianMutation(self.base_sigma, self.gene_bounds)
        return gaussian_mutator.mutate(individual, mutation_rate)
    
    def update_diversity(self, diversity: float):
        """Update diversity history for adaptation."""
        self.diversity_history.append(diversity)
        
        # Keep only recent history
        if len(self.diversity_history) > 10:
            self.diversity_history.pop(0)
    
    def get_adaptive_sigma(self) -> float:
        """Calculate adaptive sigma based on diversity history."""
        if len(self.diversity_history) < 2:
            return self.base_sigma
        
        # Increase mutation when diversity is low
        recent_diversity = np.mean(self.diversity_history[-5:])
        if recent_diversity < 0.1:  # Low diversity threshold
            return self.base_sigma * 2.0
        elif recent_diversity > 0.5:  # High diversity threshold
            return self.base_sigma * 0.5
        else:
            return self.base_sigma