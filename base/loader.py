# from .environment import SolutionStepEnvironment
# from solver.heuristic.node_rank import *


# def load_simulator(solver_name):
#     # rank
#     if solver_name == 'grc_rank':
#         Env, Solver = SolutionStepEnvironment, GRCRankSolver
#     elif solver_name == 'nrm_rank':
#         Env, Solver = SolutionStepEnvironment, NRMRankSolver
#     elif solver_name == 'pl_rank':
#         Env, Solver = SolutionStepEnvironment, PLRankSolver
#     elif solver_name == 'gae_vne':
#         from solver.learning.gae_vne import GAESolver
#         Env, Solver = SolutionStepEnvironment, GAESolver
#     elif solver_name == 'mcts_vne':
#         from solver.learning.mcts_vne import MCTSSolver
#         Env, Solver = SolutionStepEnvironment, MCTSSolver
#     elif solver_name == 'pg_cnn2':
#         from solver.learning.pg_cnn2 import PgCnn2Solver
#         Env, Solver = SolutionStepEnvironment, PgCnn2Solver
#     elif solver_name == 'a3c_gcn':
#         from solver.learning.a3c_gcn import A3CGCNSolver
#         Env, Solver = SolutionStepEnvironment, A3CGCNSolver
#     elif solver_name == 'hrl_ra':
#         from solver.learning.hrl_ra import HrlRaSolver
#         Env, Solver = SolutionStepEnvironment, HrlRaSolver
#     elif solver_name == 'hrl_ac':
#         from solver.learning.hrl_ac import OnlineEnv, HrlAcSolver
#         Env, Solver = OnlineEnv, HrlAcSolver
#     else:
#         raise ValueError('The solver is not yet supported; \n Please attempt to select another one.', solver_name)
#     return Env, Solver

from .environment import SolutionStepEnvironment
from solver.heuristic.node_rank import GRCRankSolver, NRMRankSolver, PLRankSolver


def load_simulator(solver_name):
    """
    Returns (Env class, Solver class) for the given solver_name.

    Supported names
    ───────────────
    Heuristic (no pre-training)
      grc_rank, nrm_rank, pl_rank

    Learning-based (need pre-training)
      mcts_vne, gae_vne, a3c_gcn, pg_cnn2

    HRL-ACRA original
      hrl_ra   — lower-level RL resource allocator
      hrl_ac   — upper-level RL admission controller  (default sub: nrm_rank)

    Approach 1 — pure HPSO sub-solver
      hrl_ac + sub_solver_name=fast_hpso
        → pass --sub_solver_name=fast_hpso at CLI; no extra entry needed here.
          FastHPSOSolver requires NO pre-training.

    Approach 2 — hybrid RL-HPSO
      hrl_hpso — pre-train the PPO candidate-selector standalone
      hrl_ac + sub_solver_name=hrl_hpso → full hierarchical pipeline
    """

    # ── heuristics ────────────────────────────────────────────────────────────
    if solver_name == "grc_rank":
        Env, Solver = SolutionStepEnvironment, GRCRankSolver
    elif solver_name == "nrm_rank":
        Env, Solver = SolutionStepEnvironment, NRMRankSolver
    elif solver_name == "pl_rank":
        Env, Solver = SolutionStepEnvironment, PLRankSolver

    # ── learning-based ────────────────────────────────────────────────────────
    elif solver_name == "gae_vne":
        from solver.learning.gae_vne import GAESolver
        Env, Solver = SolutionStepEnvironment, GAESolver

    elif solver_name == "mcts_vne":
        from solver.learning.mcts_vne import MCTSSolver
        Env, Solver = SolutionStepEnvironment, MCTSSolver

    elif solver_name == "pg_cnn2":
        from solver.learning.pg_cnn2 import PgCnn2Solver
        Env, Solver = SolutionStepEnvironment, PgCnn2Solver

    elif solver_name == "a3c_gcn":
        from solver.learning.a3c_gcn import A3CGCNSolver
        Env, Solver = SolutionStepEnvironment, A3CGCNSolver

    # ── HRL-ACRA original ─────────────────────────────────────────────────────
    elif solver_name == "hrl_ra":
        from solver.learning.hrl_ra import HrlRaSolver
        Env, Solver = SolutionStepEnvironment, HrlRaSolver

    elif solver_name == "hrl_ac":
        from solver.learning.hrl_ac import OnlineEnv, HrlAcSolver
        Env, Solver = OnlineEnv, HrlAcSolver

    # ── Approach 2: standalone pre-training of HPSOGuidedSolver ──────────────
    elif solver_name == "hrl_hpso":
        # Pre-train the PPO candidate-selector with the same env used by hrl_ra
        from solver.learning.hrl_hpso import HPSOGuidedSolver
        Env, Solver = SolutionStepEnvironment, HPSOGuidedSolver

    else:
        raise ValueError(
            f"Solver '{solver_name}' is not supported.\n"
            "Available: grc_rank | nrm_rank | pl_rank | mcts_vne | gae_vne | "
            "a3c_gcn | pg_cnn2 | hrl_ra | hrl_ac | hrl_hpso"
        )

    return Env, Solver