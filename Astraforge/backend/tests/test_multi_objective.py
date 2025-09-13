"""
Unit tests for multi-objective optimization components.

Tests Pareto dominance, non-dominated sorting, crowding distance,
and multi-objective genetic algorithm functionality.
"""

import pytest
import numpy as np
from typing import List

from app.optimization.genetic_algorithm import Individual, Population, GAConfig
from app.optimization.multi_objective import (
    ObjectiveFunction, ObjectiveType, dominates, ParetoFront,
    NonDominatedSorting, CrowdingDistance, MultiObjectiveGA
)
from app.optimization.operators import (
    TournamentSelection, UniformCrossover, GaussianMutation
)


class TestObjectiveFunction:
    """Test ObjectiveFunction class."""
    
    def test_objective_function_creation(self):
        """Test objective function creation."""
        def test_func(individual: Individual) -> float:
            return sum(individual.genes.values())
        
        obj = ObjectiveFunction(
            name="sum_genes",
            function=test_func,
            objective_type=ObjectiveType.MINIMIZE,
            weight=2.0
        )
        
        assert obj.name == "sum_genes"
        assert obj.function == test_func
        assert obj.objective_type == ObjectiveType.MINIMIZE
        assert obj.weight == 2.0
    
    def test_objective_function_evaluate(self):
        """Test objective function evaluation."""
        def test_func(individual: Individual) -> float:
            return sum(individual.genes.values())
        
        obj = ObjectiveFunction(name="sum_genes", function=test_func)
        individual = Individual(genes={'x': 1.0, 'y': 2.0, 'z': 3.0})
        
        result = obj.evaluate(individual)
        
        assert result == 6.0
        assert individual.objectives['sum_genes'] == 6.0
    
    def test_objective_function_evaluation_error(self):
        """Test objective function evaluation with error."""
        def error_func(individual: Individual) -> float:
            raise ValueError("Test error")
        
        obj = ObjectiveFunction(name="error_func", function=error_func)
        individual = Individual(genes={'x': 1.0})
        
        with pytest.raises(ValueError, match="Test error"):
            obj.evaluate(individual)
        
        # Check that error value is stored
        assert individual.objectives['error_func'] == float('inf')
    
    def test_invalid_objective_name(self):
        """Test invalid objective name."""
        def test_func(individual: Individual) -> float:
            return 0.0
        
        with pytest.raises(ValueError, match="Objective name cannot be empty"):
            ObjectiveFunction(name="", function=test_func)
    
    def test_invalid_weight(self):
        """Test invalid weight."""
        def test_func(individual: Individual) -> float:
            return 0.0
        
        with pytest.raises(ValueError, match="Objective weight must be positive"):
            ObjectiveFunction(name="test", function=test_func, weight=0.0)


class TestDominance:
    """Test Pareto dominance functions."""
    
    def create_test_objectives(self) -> List[ObjectiveFunction]:
        """Create test objectives for dominance testing."""
        def obj1_func(individual: Individual) -> float:
            return individual.genes.get('x', 0.0)
        
        def obj2_func(individual: Individual) -> float:
            return individual.genes.get('y', 0.0)
        
        return [
            ObjectiveFunction("obj1", obj1_func, ObjectiveType.MINIMIZE),
            ObjectiveFunction("obj2", obj2_func, ObjectiveType.MINIMIZE)
        ]
    
    def test_dominance_clear_case(self):
        """Test clear dominance case."""
        objectives = self.create_test_objectives()
        
        # Individual 1 is better in both objectives (minimization)
        ind1 = Individual(genes={'x': 1.0, 'y': 1.0})
        ind1.objectives = {'obj1': 1.0, 'obj2': 1.0}
        
        ind2 = Individual(genes={'x': 2.0, 'y': 2.0})
        ind2.objectives = {'obj1': 2.0, 'obj2': 2.0}
        
        assert dominates(ind1, ind2, objectives)
        assert not dominates(ind2, ind1, objectives)
    
    def test_no_dominance(self):
        """Test case where neither individual dominates."""
        objectives = self.create_test_objectives()
        
        # Trade-off: ind1 better in obj1, ind2 better in obj2
        ind1 = Individual(genes={'x': 1.0, 'y': 2.0})
        ind1.objectives = {'obj1': 1.0, 'obj2': 2.0}
        
        ind2 = Individual(genes={'x': 2.0, 'y': 1.0})
        ind2.objectives = {'obj1': 2.0, 'obj2': 1.0}
        
        assert not dominates(ind1, ind2, objectives)
        assert not dominates(ind2, ind1, objectives)
    
    def test_dominance_with_maximization(self):
        """Test dominance with maximization objectives."""
        def obj1_func(individual: Individual) -> float:
            return individual.genes.get('x', 0.0)
        
        def obj2_func(individual: Individual) -> float:
            return individual.genes.get('y', 0.0)
        
        objectives = [
            ObjectiveFunction("obj1", obj1_func, ObjectiveType.MAXIMIZE),
            ObjectiveFunction("obj2", obj2_func, ObjectiveType.MAXIMIZE)
        ]
        
        # Individual 1 is better in both objectives (maximization)
        ind1 = Individual(genes={'x': 2.0, 'y': 2.0})
        ind1.objectives = {'obj1': 2.0, 'obj2': 2.0}
        
        ind2 = Individual(genes={'x': 1.0, 'y': 1.0})
        ind2.objectives = {'obj1': 1.0, 'obj2': 1.0}
        
        assert dominates(ind1, ind2, objectives)
        assert not dominates(ind2, ind1, objectives)
    
    def test_dominance_missing_objectives(self):
        """Test dominance with missing objectives."""
        objectives = self.create_test_objectives()
        
        ind1 = Individual(genes={'x': 1.0})
        ind1.objectives = {'obj1': 1.0}  # Missing obj2
        
        ind2 = Individual(genes={'x': 2.0, 'y': 2.0})
        ind2.objectives = {'obj1': 2.0, 'obj2': 2.0}
        
        assert not dominates(ind1, ind2, objectives)
        assert not dominates(ind2, ind1, objectives)


class TestParetoFront:
    """Test ParetoFront class."""
    
    def test_pareto_front_creation(self):
        """Test Pareto front creation."""
        front = ParetoFront(rank=0)
        
        assert len(front) == 0
        assert front.rank == 0
    
    def test_add_remove_individuals(self):
        """Test adding and removing individuals."""
        front = ParetoFront()
        ind1 = Individual(genes={'x': 1.0})
        ind2 = Individual(genes={'x': 2.0})
        
        front.add_individual(ind1)
        front.add_individual(ind2)
        
        assert len(front) == 2
        assert ind1 in front.individuals
        assert ind2 in front.individuals
        
        front.remove_individual(ind1)
        assert len(front) == 1
        assert ind1 not in front.individuals
        assert ind2 in front.individuals
    
    def test_get_objective_ranges(self):
        """Test objective range calculation."""
        def obj1_func(individual: Individual) -> float:
            return individual.genes.get('x', 0.0)
        
        def obj2_func(individual: Individual) -> float:
            return individual.genes.get('y', 0.0)
        
        objectives = [
            ObjectiveFunction("obj1", obj1_func),
            ObjectiveFunction("obj2", obj2_func)
        ]
        
        front = ParetoFront()
        
        # Add individuals with different objective values
        for x, y in [(1.0, 3.0), (2.0, 1.0), (3.0, 2.0)]:
            ind = Individual(genes={'x': x, 'y': y})
            ind.objectives = {'obj1': x, 'obj2': y}
            front.add_individual(ind)
        
        ranges = front.get_objective_ranges(objectives)
        
        assert ranges['obj1'] == (1.0, 3.0)
        assert ranges['obj2'] == (1.0, 3.0)
    
    def test_hypervolume_2d(self):
        """Test 2D hypervolume calculation."""
        def obj1_func(individual: Individual) -> float:
            return individual.genes.get('x', 0.0)
        
        def obj2_func(individual: Individual) -> float:
            return individual.genes.get('y', 0.0)
        
        objectives = [
            ObjectiveFunction("obj1", obj1_func, ObjectiveType.MINIMIZE),
            ObjectiveFunction("obj2", obj2_func, ObjectiveType.MINIMIZE)
        ]
        
        front = ParetoFront()
        
        # Add Pareto optimal points
        points = [(1.0, 3.0), (2.0, 2.0), (3.0, 1.0)]
        for x, y in points:
            ind = Individual(genes={'x': x, 'y': y})
            ind.objectives = {'obj1': x, 'obj2': y}
            front.add_individual(ind)
        
        # Calculate hypervolume with reference point (4, 4)
        reference_point = {'obj1': 4.0, 'obj2': 4.0}
        hypervolume = front.calculate_hypervolume(objectives, reference_point)
        
        assert hypervolume > 0.0  # Should be positive for valid Pareto front


class TestNonDominatedSorting:
    """Test NonDominatedSorting class."""
    
    def create_test_population(self) -> tuple[Population, List[ObjectiveFunction]]:
        """Create test population for sorting."""
        def obj1_func(individual: Individual) -> float:
            return individual.genes.get('x', 0.0)
        
        def obj2_func(individual: Individual) -> float:
            return individual.genes.get('y', 0.0)
        
        objectives = [
            ObjectiveFunction("obj1", obj1_func, ObjectiveType.MINIMIZE),
            ObjectiveFunction("obj2", obj2_func, ObjectiveType.MINIMIZE)
        ]
        
        population = Population(max_size=10)
        
        # Create individuals with known dominance relationships
        test_points = [
            (1.0, 3.0),  # Pareto optimal
            (2.0, 2.0),  # Pareto optimal
            (3.0, 1.0),  # Pareto optimal
            (2.0, 3.0),  # Dominated by (1.0, 3.0) and (2.0, 2.0)
            (3.0, 2.0),  # Dominated by (2.0, 2.0) and (3.0, 1.0)
        ]
        
        for x, y in test_points:
            ind = Individual(genes={'x': x, 'y': y})
            ind.objectives = {'obj1': x, 'obj2': y}
            population.add_individual(ind)
        
        return population, objectives
    
    def test_non_dominated_sorting(self):
        """Test non-dominated sorting."""
        population, objectives = self.create_test_population()
        
        fronts = NonDominatedSorting.sort(population, objectives)
        
        assert len(fronts) >= 1
        
        # First front should contain Pareto optimal solutions
        first_front = fronts[0]
        assert first_front.rank == 0
        assert len(first_front) == 3  # Three Pareto optimal points
        
        # Check that first front contains the expected points
        first_front_points = set()
        for ind in first_front.individuals:
            x, y = ind.objectives['obj1'], ind.objectives['obj2']
            first_front_points.add((x, y))
        
        expected_points = {(1.0, 3.0), (2.0, 2.0), (3.0, 1.0)}
        assert first_front_points == expected_points
    
    def test_empty_population_sorting(self):
        """Test sorting empty population."""
        population = Population(max_size=10)
        objectives = []
        
        fronts = NonDominatedSorting.sort(population, objectives)
        
        assert len(fronts) == 0


class TestCrowdingDistance:
    """Test CrowdingDistance class."""
    
    def test_crowding_distance_calculation(self):
        """Test crowding distance calculation."""
        def obj1_func(individual: Individual) -> float:
            return individual.genes.get('x', 0.0)
        
        def obj2_func(individual: Individual) -> float:
            return individual.genes.get('y', 0.0)
        
        objectives = [
            ObjectiveFunction("obj1", obj1_func),
            ObjectiveFunction("obj2", obj2_func)
        ]
        
        front = ParetoFront()
        
        # Add individuals in a line (should have different crowding distances)
        points = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0), (4.0, 4.0)]
        for x, y in points:
            ind = Individual(genes={'x': x, 'y': y})
            ind.objectives = {'obj1': x, 'obj2': y}
            front.add_individual(ind)
        
        distances = CrowdingDistance.calculate(front, objectives)
        
        # Boundary individuals should have infinite distance
        boundary_individuals = [front.individuals[0], front.individuals[-1]]
        for ind in boundary_individuals:
            assert distances[ind.id] == float('inf')
        
        # Interior individuals should have finite distance
        interior_individuals = front.individuals[1:-1]
        for ind in interior_individuals:
            assert 0.0 <= distances[ind.id] < float('inf')
    
    def test_crowding_distance_small_front(self):
        """Test crowding distance with small front."""
        objectives = []
        front = ParetoFront()
        
        # Add only two individuals
        for x in [1.0, 2.0]:
            ind = Individual(genes={'x': x})
            front.add_individual(ind)
        
        distances = CrowdingDistance.calculate(front, objectives)
        
        # All individuals in small front should have infinite distance
        for ind in front.individuals:
            assert distances[ind.id] == float('inf')


class TestMultiObjectiveGA:
    """Test MultiObjectiveGA class."""
    
    def create_test_moga(self) -> MultiObjectiveGA:
        """Create test multi-objective GA."""
        def obj1_func(individual: Individual) -> float:
            # Minimize sum of squares
            return sum(x**2 for x in individual.genes.values())
        
        def obj2_func(individual: Individual) -> float:
            # Minimize sum of absolute values
            return sum(abs(x) for x in individual.genes.values())
        
        objectives = [
            ObjectiveFunction("sphere", obj1_func, ObjectiveType.MINIMIZE),
            ObjectiveFunction("manhattan", obj2_func, ObjectiveType.MINIMIZE)
        ]
        
        gene_bounds = {'x': (-5.0, 5.0), 'y': (-5.0, 5.0)}
        config = GAConfig(
            population_size=20,
            max_generations=5,
            crossover_rate=0.8,
            mutation_rate=0.1
        )
        
        moga = MultiObjectiveGA(
            config=config,
            objectives=objectives,
            gene_bounds=gene_bounds
        )
        
        # Set operators
        moga.selection_operator = TournamentSelection(tournament_size=3)
        moga.crossover_operator = UniformCrossover(swap_probability=0.5)
        moga.mutation_operator = GaussianMutation(sigma=0.1, gene_bounds=gene_bounds)
        
        return moga
    
    def test_moga_initialization(self):
        """Test MOGA initialization."""
        moga = self.create_test_moga()
        
        assert len(moga.objectives) == 2
        assert moga.config.population_size == 20
        assert len(moga.pareto_fronts) == 0
    
    def test_moga_population_evaluation(self):
        """Test MOGA population evaluation."""
        moga = self.create_test_moga()
        moga.initialize_population()
        moga.evaluate_population(moga.population)
        
        # Check that all individuals are evaluated with all objectives
        for individual in moga.population:
            assert individual.is_evaluated
            assert 'sphere' in individual.objectives
            assert 'manhattan' in individual.objectives
    
    def test_moga_evolution(self):
        """Test MOGA evolution."""
        moga = self.create_test_moga()
        moga.initialize_population()
        
        initial_generation = moga.current_generation
        moga.evolve_generation()
        
        assert moga.current_generation == initial_generation + 1
        assert len(moga.pareto_fronts) > 0
        assert len(moga.pareto_front_history) > 0
    
    def test_get_pareto_optimal_solutions(self):
        """Test getting Pareto optimal solutions."""
        moga = self.create_test_moga()
        moga.initialize_population()
        moga.evolve_generation()
        
        pareto_optimal = moga.get_pareto_optimal_solutions()
        
        assert isinstance(pareto_optimal, list)
        # Should have at least one Pareto optimal solution
        assert len(pareto_optimal) >= 1
    
    def test_convergence_metrics(self):
        """Test convergence metrics calculation."""
        moga = self.create_test_moga()
        moga.initialize_population()
        moga.evolve_generation()
        
        metrics = moga.calculate_convergence_metrics()
        
        assert 'pareto_front_size' in metrics
        assert 'total_fronts' in metrics
        assert 'hypervolume' in metrics
        assert metrics['pareto_front_size'] >= 1
        assert metrics['total_fronts'] >= 1
    
    def test_moga_complete_run(self):
        """Test complete MOGA run."""
        moga = self.create_test_moga()
        best_individual, statistics = moga.run()
        
        assert best_individual is not None
        assert best_individual.is_evaluated
        assert len(best_individual.objectives) == 2
        assert 'generations' in statistics
        assert statistics['generations'] <= moga.config.max_generations
    
    def test_no_objectives_error(self):
        """Test error when no objectives provided."""
        gene_bounds = {'x': (-5.0, 5.0)}
        config = GAConfig(population_size=10, max_generations=5)
        
        with pytest.raises(ValueError, match="At least one objective function must be provided"):
            MultiObjectiveGA(
                config=config,
                objectives=[],
                gene_bounds=gene_bounds
            )


if __name__ == "__main__":
    pytest.main([__file__])