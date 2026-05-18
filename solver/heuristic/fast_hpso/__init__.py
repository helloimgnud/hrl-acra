# solver/heuristic/fast_hpso/__init__.py
from .fast_hpso_solver import FastHPSOSolver

from base.environment import SolutionStepEnvironment
from base.register import Register

Register.register('fast_hpso', {
    'solver': FastHPSOSolver,
    'env': SolutionStepEnvironment,
})

__all__ = ['FastHPSOSolver']
