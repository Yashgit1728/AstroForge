"""
Optimization engine for space mission parameter optimization.

This module provides genetic algorithm-based optimization for mission parameters,
including multi-objective optimization with Pareto front calculation.
"""

from .genetic_algorithm import (
    GeneticAlgorithm,
    Individual,
    Population,
    SelectionMethod,
    CrossoverMethod,
    MutationMethod
)
from .operators import (
    TournamentSelection,
    RouletteWheelSelection,
    UniformCrossover,
    SinglePointCrossover,
    GaussianMutation,
    UniformMutation
)
from .multi_objective import (
    MultiObjectiveGA,
    ParetoFront,
    ObjectiveFunction,
    dominates
)

__all__ = [
    'GeneticAlgorithm',
    'Individual',
    'Population',
    'SelectionMethod',
    'CrossoverMethod', 
    'MutationMethod',
    'TournamentSelection',
    'RouletteWheelSelection',
    'UniformCrossover',
    'SinglePointCrossover',
    'GaussianMutation',
    'UniformMutation',
    'MultiObjectiveGA',
    'ParetoFront',
    'ObjectiveFunction',
    'dominates'
]