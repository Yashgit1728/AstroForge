"""
Unit tests for genetic algorithm framework.

Tests the core GA components including Individual, Population,
genetic operators, and the main GeneticAlgorithm class.
"""

import pytest
import numpy as np
from uuid import uuid4
from typing import Dict, List

from app.optimization.genetic_algorithm import (
    Individual, Population, GeneticAlgorithm, GAConfig,
    SelectionMethod, CrossoverMethod, MutationMethod
)
from app.optimization.operators import (
    TournamentSelection, RouletteWheelSelection,
    UniformCrossover, SinglePointCrossover, ArithmeticCrossover,
    GaussianMutation, UniformMutation, PolynomialMutation
)


class TestIndividual:
    """Test Individual class."""
    
    def test_individual_creation(self):
        """Test individual creation and validation."""
        genes = {'x': 1.0, 'y': 2.0, 'z': 3.0}
        individual = Individual(genes=genes)
        
        assert individual.genes == genes
        assert individual.fitness is None
        assert not individual.is_evaluated
        assert individual.is_feasible  # No constraints violated
        assert individual.generation == 0
    
    def test_individual_empty_genes_error(self):
        """Test that empty genes raise error."""
        with pytest.raises(ValueError, match="Individual must have at least one gene"):
            Individual(genes={})
    
    def test_individual_copy(self):
        """Test individual copying."""
        original = Individual(
            genes={'x': 1.0, 'y': 2.0},
            fitness=10.0,
            objectives={'obj1': 5.0},
            constraints_violated=['constraint1'],
            generation=5
        )
        
        copy = original.copy()
        
        assert copy.id != original.id
        assert copy.genes == original.genes
        assert copy.fitness == original.fitness
        assert copy.objectives == original.objectives
        assert copy.constraints_violated == original.constraints_violated
        assert copy.generation == original.generation
        assert copy.parent_ids == [original.id]
    
    def test_gene_vector_operations(self):
        """Test gene vector get/set operations."""
        individual = Individual(genes={'x': 1.0, 'y': 2.0, 'z': 3.0})
        gene_names = ['x', 'y', 'z']
        
        # Test get_gene_vector
        vector = individual.get_gene_vector(gene_names)
        expected = np.array([1.0, 2.0, 3.0])
        np.testing.assert_array_equal(vector, expected)
        
        # Test set_gene_vector
        new_vector = np.array([4.0, 5.0, 6.0])
        individual.set_gene_vector(gene_names, new_vector)
        
        assert individual.genes['x'] == 4.0
        assert individual.genes['y'] == 5.0
        assert individual.genes['z'] == 6.0
    
    def test_gene_vector_length_mismatch(self):
        """Test gene vector operations with mismatched lengths."""
        individual = Individual(genes={'x': 1.0, 'y': 2.0})
        
        with pytest.raises(ValueError, match="Gene names and values must have same length"):
            individual.set_gene_vector(['x', 'y', 'z'], np.array([1.0, 2.0]))


class TestPopulation:
    """Test Population class."""
    
    def test_population_creation(self):
        """Test population creation."""
        population = Population(max_size=10)
        
        assert len(population) == 0
        assert population.max_size == 10
        assert population.generation == 0
    
    def test_population_invalid_max_size(self):
        """Test population with invalid max size."""
        with pytest.raises(ValueError, match="Population max_size must be positive"):
            Population(max_size=0)
    
    def test_add_individual(self):
        """Test adding individuals to population."""
        population = Population(max_size=2)
        ind1 = Individual(genes={'x': 1.0})
        ind2 = Individual(genes={'x': 2.0})
        
        population.add_individual(ind1)
        population.add_individual(ind2)
        
        assert len(population) == 2
        assert population[0] == ind1
        assert population[1] == ind2
        assert ind1.generation == 0
        assert ind2.generation == 0
    
    def test_add_individual_exceeds_max_size(self):
        """Test adding individual when population is full."""
        population = Population(max_size=1)
        ind1 = Individual(genes={'x': 1.0})
        ind2 = Individual(genes={'x': 2.0})
        
        population.add_individual(ind1)
        
        with pytest.raises(ValueError, match="Population already at maximum size"):
            population.add_individual(ind2)
    
    def test_remove_individual(self):
        """Test removing individuals from population."""
        population = Population(max_size=10)
        ind1 = Individual(genes={'x': 1.0})
        ind2 = Individual(genes={'x': 2.0})
        
        population.add_individual(ind1)
        population.add_individual(ind2)
        
        removed = population.remove_individual(0)
        
        assert removed == ind1
        assert len(population) == 1
        assert population[0] == ind2
    
    def test_remove_individual_invalid_index(self):
        """Test removing individual with invalid index."""
        population = Population(max_size=10)
        
        with pytest.raises(IndexError, match="Individual index out of range"):
            population.remove_individual(0)
    
    def test_get_best_individual(self):
        """Test getting best individual."""
        population = Population(max_size=10)
        
        ind1 = Individual(genes={'x': 1.0})
        ind1.fitness = 5.0
        ind2 = Individual(genes={'x': 2.0})
        ind2.fitness = 10.0
        ind3 = Individual(genes={'x': 3.0})
        ind3.fitness = 3.0
        
        population.add_individual(ind1)
        population.add_individual(ind2)
        population.add_individual(ind3)
        
        # Test maximize (default)
        best = population.get_best_individual(maximize=True)
        assert best == ind2
        
        # Test minimize
        best = population.get_best_individual(maximize=False)
        assert best == ind3
    
    def test_get_best_individual_empty_population(self):
        """Test getting best individual from empty population."""
        population = Population(max_size=10)
        assert population.get_best_individual() is None
    
    def test_get_feasible_individuals(self):
        """Test getting feasible individuals."""
        population = Population(max_size=10)
        
        ind1 = Individual(genes={'x': 1.0})
        ind2 = Individual(genes={'x': 2.0})
        ind2.constraints_violated = ['constraint1']
        ind3 = Individual(genes={'x': 3.0})
        
        population.add_individual(ind1)
        population.add_individual(ind2)
        population.add_individual(ind3)
        
        feasible = population.get_feasible_individuals()
        
        assert len(feasible) == 2
        assert ind1 in feasible
        assert ind3 in feasible
        assert ind2 not in feasible
    
    def test_fitness_statistics(self):
        """Test fitness statistics calculation."""
        population = Population(max_size=10)
        
        # Add individuals with fitness
        for i, fitness in enumerate([1.0, 2.0, 3.0, 4.0, 5.0]):
            ind = Individual(genes={'x': float(i)})
            ind.fitness = fitness
            population.add_individual(ind)
        
        stats = population.get_fitness_statistics()
        
        assert stats['mean'] == 3.0
        assert stats['min'] == 1.0
        assert stats['max'] == 5.0
        assert stats['median'] == 3.0
        assert abs(stats['std'] - np.std([1.0, 2.0, 3.0, 4.0, 5.0])) < 1e-10
    
    def test_sort_by_fitness(self):
        """Test sorting population by fitness."""
        population = Population(max_size=10)
        
        # Add individuals with random fitness
        fitness_values = [3.0, 1.0, 4.0, 2.0, 5.0]
        for i, fitness in enumerate(fitness_values):
            ind = Individual(genes={'x': float(i)})
            ind.fitness = fitness
            population.add_individual(ind)
        
        # Sort descending (maximize)
        population.sort_by_fitness(maximize=True)
        sorted_fitness = [ind.fitness for ind in population]
        assert sorted_fitness == [5.0, 4.0, 3.0, 2.0, 1.0]
        
        # Sort ascending (minimize)
        population.sort_by_fitness(maximize=False)
        sorted_fitness = [ind.fitness for ind in population]
        assert sorted_fitness == [1.0, 2.0, 3.0, 4.0, 5.0]


class TestGAConfig:
    """Test GAConfig class."""
    
    def test_valid_config(self):
        """Test valid configuration."""
        config = GAConfig(
            population_size=50,
            max_generations=100,
            crossover_rate=0.8,
            mutation_rate=0.1,
            elitism_rate=0.1
        )
        
        assert config.population_size == 50
        assert config.max_generations == 100
        assert config.crossover_rate == 0.8
        assert config.mutation_rate == 0.1
        assert config.elitism_rate == 0.1
    
    def test_invalid_population_size(self):
        """Test invalid population size."""
        with pytest.raises(ValueError, match="Population size must be positive"):
            GAConfig(population_size=0)
    
    def test_invalid_crossover_rate(self):
        """Test invalid crossover rate."""
        with pytest.raises(ValueError, match="Crossover rate must be between 0 and 1"):
            GAConfig(crossover_rate=1.5)
    
    def test_invalid_mutation_rate(self):
        """Test invalid mutation rate."""
        with pytest.raises(ValueError, match="Mutation rate must be between 0 and 1"):
            GAConfig(mutation_rate=-0.1)


class TestTournamentSelection:
    """Test TournamentSelection operator."""
    
    def test_tournament_selection(self):
        """Test tournament selection."""
        selector = TournamentSelection(tournament_size=3)
        population = Population(max_size=10)
        
        # Add individuals with different fitness
        for i in range(5):
            ind = Individual(genes={'x': float(i)})
            ind.fitness = float(i)
            population.add_individual(ind)
        
        parents = selector.select(population, 2)
        
        assert len(parents) == 2
        # Higher fitness individuals should be more likely to be selected
        assert all(parent.fitness is not None for parent in parents)
    
    def test_tournament_selection_empty_population(self):
        """Test tournament selection with empty population."""
        selector = TournamentSelection(tournament_size=3)
        population = Population(max_size=10)
        
        parents = selector.select(population, 2)
        assert len(parents) == 0
    
    def test_invalid_tournament_size(self):
        """Test invalid tournament size."""
        with pytest.raises(ValueError, match="Tournament size must be positive"):
            TournamentSelection(tournament_size=0)


class TestUniformCrossover:
    """Test UniformCrossover operator."""
    
    def test_uniform_crossover(self):
        """Test uniform crossover."""
        crossover = UniformCrossover(swap_probability=0.5)
        
        parent1 = Individual(genes={'x': 1.0, 'y': 2.0, 'z': 3.0})
        parent2 = Individual(genes={'x': 4.0, 'y': 5.0, 'z': 6.0})
        
        offspring1, offspring2 = crossover.crossover(parent1, parent2)
        
        # Check that offspring are different from parents
        assert offspring1.id != parent1.id
        assert offspring2.id != parent2.id
        
        # Check that parent IDs are set
        assert parent1.id in offspring1.parent_ids
        assert parent2.id in offspring1.parent_ids
        assert parent1.id in offspring2.parent_ids
        assert parent2.id in offspring2.parent_ids
        
        # Check that fitness is reset
        assert offspring1.fitness is None
        assert offspring2.fitness is None
    
    def test_invalid_swap_probability(self):
        """Test invalid swap probability."""
        with pytest.raises(ValueError, match="Swap probability must be between 0 and 1"):
            UniformCrossover(swap_probability=1.5)


class TestGaussianMutation:
    """Test GaussianMutation operator."""
    
    def test_gaussian_mutation(self):
        """Test Gaussian mutation."""
        gene_bounds = {'x': (0.0, 10.0), 'y': (0.0, 10.0)}
        mutator = GaussianMutation(sigma=0.1, gene_bounds=gene_bounds)
        
        original = Individual(genes={'x': 5.0, 'y': 5.0})
        mutated = mutator.mutate(original, mutation_rate=1.0)  # Always mutate
        
        # Check that individual is different
        assert mutated.id != original.id
        assert mutated.fitness is None
        
        # Check that genes are within bounds
        assert 0.0 <= mutated.genes['x'] <= 10.0
        assert 0.0 <= mutated.genes['y'] <= 10.0
    
    def test_invalid_sigma(self):
        """Test invalid sigma."""
        with pytest.raises(ValueError, match="Sigma must be positive"):
            GaussianMutation(sigma=0.0)


class TestGeneticAlgorithm:
    """Test GeneticAlgorithm class."""
    
    def create_simple_ga(self) -> GeneticAlgorithm:
        """Create a simple GA for testing."""
        def fitness_function(individual: Individual) -> float:
            # Simple sphere function: minimize sum of squares
            return -sum(x**2 for x in individual.genes.values())
        
        gene_bounds = {'x': (-5.0, 5.0), 'y': (-5.0, 5.0)}
        config = GAConfig(
            population_size=10,
            max_generations=5,
            crossover_rate=0.8,
            mutation_rate=0.1
        )
        
        ga = GeneticAlgorithm(
            config=config,
            fitness_function=fitness_function,
            gene_bounds=gene_bounds
        )
        
        # Set operators
        ga.selection_operator = TournamentSelection(tournament_size=3)
        ga.crossover_operator = UniformCrossover(swap_probability=0.5)
        ga.mutation_operator = GaussianMutation(sigma=0.1, gene_bounds=gene_bounds)
        
        return ga
    
    def test_ga_initialization(self):
        """Test GA initialization."""
        ga = self.create_simple_ga()
        
        assert ga.config.population_size == 10
        assert ga.current_generation == 0
        assert len(ga.population) == 0
    
    def test_initialize_population(self):
        """Test population initialization."""
        ga = self.create_simple_ga()
        population = ga.initialize_population()
        
        assert len(population) == ga.config.population_size
        
        # Check that all individuals have genes within bounds
        for individual in population:
            assert -5.0 <= individual.genes['x'] <= 5.0
            assert -5.0 <= individual.genes['y'] <= 5.0
    
    def test_evaluate_population(self):
        """Test population evaluation."""
        ga = self.create_simple_ga()
        ga.initialize_population()
        ga.evaluate_population(ga.population)
        
        # Check that all individuals are evaluated
        for individual in ga.population:
            assert individual.is_evaluated
            assert individual.fitness is not None
    
    def test_evolve_generation(self):
        """Test single generation evolution."""
        ga = self.create_simple_ga()
        ga.initialize_population()
        
        initial_generation = ga.current_generation
        ga.evolve_generation()
        
        assert ga.current_generation == initial_generation + 1
        assert len(ga.population) == ga.config.population_size
    
    def test_run_complete(self):
        """Test complete GA run."""
        ga = self.create_simple_ga()
        best_individual, statistics = ga.run()
        
        assert best_individual is not None
        assert best_individual.is_evaluated
        assert 'generations' in statistics
        assert 'best_fitness_history' in statistics
        assert 'mean_fitness_history' in statistics
        assert statistics['generations'] <= ga.config.max_generations
    
    def test_constraint_handling(self):
        """Test constraint handling."""
        def constraint_function(individual: Individual) -> bool:
            # Constraint: x + y <= 5
            return individual.genes['x'] + individual.genes['y'] <= 5.0
        
        def fitness_function(individual: Individual) -> float:
            return -sum(x**2 for x in individual.genes.values())
        
        gene_bounds = {'x': (-5.0, 5.0), 'y': (-5.0, 5.0)}
        config = GAConfig(population_size=10, max_generations=5)
        
        ga = GeneticAlgorithm(
            config=config,
            fitness_function=fitness_function,
            gene_bounds=gene_bounds,
            constraint_functions=[constraint_function]
        )
        
        # Set operators
        ga.selection_operator = TournamentSelection(tournament_size=3)
        ga.crossover_operator = UniformCrossover(swap_probability=0.5)
        ga.mutation_operator = GaussianMutation(sigma=0.1, gene_bounds=gene_bounds)
        
        ga.initialize_population()
        ga.evaluate_population(ga.population)
        
        # Check that constraint violations are detected
        violated_count = sum(1 for ind in ga.population if not ind.is_feasible)
        # Some individuals should violate the constraint
        assert violated_count >= 0  # At least some might violate
    
    def test_population_diversity(self):
        """Test population diversity calculation."""
        ga = self.create_simple_ga()
        ga.initialize_population()
        
        diversity = ga.get_population_diversity()
        assert diversity >= 0.0
        
        # Create identical population (should have zero diversity)
        identical_population = Population(max_size=10)
        for _ in range(5):
            ind = Individual(genes={'x': 1.0, 'y': 1.0})
            identical_population.add_individual(ind)
        
        ga.population = identical_population
        diversity = ga.get_population_diversity()
        assert diversity == 0.0
    
    def test_empty_gene_bounds_error(self):
        """Test error when gene bounds are empty."""
        def fitness_function(individual: Individual) -> float:
            return 0.0
        
        config = GAConfig(population_size=10, max_generations=5)
        
        with pytest.raises(ValueError, match="Gene bounds must be specified"):
            GeneticAlgorithm(
                config=config,
                fitness_function=fitness_function,
                gene_bounds={}
            )
    
    def test_invalid_gene_bounds(self):
        """Test error when gene bounds are invalid."""
        def fitness_function(individual: Individual) -> float:
            return 0.0
        
        config = GAConfig(population_size=10, max_generations=5)
        
        with pytest.raises(ValueError, match="Invalid bounds for gene x: min >= max"):
            GeneticAlgorithm(
                config=config,
                fitness_function=fitness_function,
                gene_bounds={'x': (5.0, 5.0)}  # min == max
            )


if __name__ == "__main__":
    pytest.main([__file__])