# solver/heuristic/hpso/hpso_solver.py
"""
HPSOSolver — hrl-acra integration of the paper-faithful VNE-HPSO algorithm.

This wrapper is the "hpso" counterpart to fast_hpso_solver.py: same
integration pattern (Mode 1: independent solver instantiated by
BasicScenario; Mode 2: sub-solver instantiated by OnlineEnv when action=1),
same use of NodeRankSolver's solve()/link_mapping() template and the
controller/recorder/counter infrastructure — but the swarm search itself
(`core.hpso_main_loop`) already performs capacity-aware shortest-path
search internally (Eqs. 3/4/6/10/12 of the paper), instead of the
hop-distance proxy fast_hpso uses. The controller's node_mapping() dry run
below therefore mostly *re-confirms* what HPSO already found rather than
discovering link-feasibility for the first time, while still producing
solution['node_slots'] / solution['node_slots_info'] in the exact format
Recorder, Counter and link_mapping() expect — we cannot bypass it even
though HPSO already found the assignment.

Use 'fast_hpso' when raw wall-clock speed matters most and you're fine
deferring full link validation to the controller's one-shot dry run after
the search. Use 'hpso' when you want the search itself to be optimizing
against the paper-accurate cost, e.g. for reproducing the paper's reported
results or for benchmarking algorithmic fidelity.
"""
import copy

from base import Solution
from ..node_rank import NodeRankSolver
from .core import hpso_main_loop, INFEASIBLE


class HPSOSolver(NodeRankSolver):
    """
    Meta-heuristic VNE solver using paper-faithful Hybrid PSO + Simulated
    Annealing (VNE-HPSO, Zhang et al., IEEE Access 2020).

    Inherits NodeRankSolver to reuse:
      - solve() template (node_mapping → link_mapping → return solution)
      - link_mapping() using controller.link_mapping()
      - controller, recorder, counter infrastructure

    Overrides:
      - node_mapping(): replaces greedy ranking with HPSO swarm search

    Does NOT use self.node_rank or self.link_rank inherited from NodeRankSolver.
    """

    name = 'hpso'

    def __init__(self, controller, recorder, counter, **kwargs):
        super(HPSOSolver, self).__init__(controller, recorder, counter, **kwargs)
        self.is_sub_solver = (kwargs.get('solver_name') != 'hpso')

        self.num_particles = kwargs.get('num_particles', 20)
        self.max_iteration = kwargs.get('max_iteration', 30)
        self.w_max = kwargs.get('w_max', 0.9)
        self.w_min = kwargs.get('w_min', 0.5)
        self.beta = kwargs.get('beta', 0.3)
        self.gamma = kwargs.get('gamma', 0.3)
        self.T0 = kwargs.get('T0', 100.0)
        self.cooling_rate = kwargs.get('cooling_rate', 0.95)
        # NOT in the paper's Algorithm 1 — opt-in speed trade-offs, off by
        # default so out-of-the-box behavior stays paper-faithful. See
        # core.hpso_main_loop docstring for what each one trades away.
        self.stop_on_first_feasible = kwargs.get('stop_on_first_feasible', False)
        self.early_stop_patience = kwargs.get('early_stop_patience', None)
        # Inherit shortest_method and k_shortest from Solver base via NodeRankSolver

        # Resolve resource attribute names from controller
        # WHY: avoid hard-coding 'cpu'/'bw'; works with any attribute config
        self._node_res_attrs = [a.name for a in self.controller.node_resource_attrs]
        self._link_res_attrs = [a.name for a in self.controller.link_resource_attrs]

    def solve(self, instance):
        solution = super(HPSOSolver, self).solve(instance)
        if solution['result'] and getattr(self, 'is_sub_solver', False):
            self.controller.deploy(instance['v_net'], instance['p_net'], solution)
        return solution

    # ─────────────────────────────────────────────────────────────────────────
    # Core override: replace greedy node ranking with HPSO search
    # ─────────────────────────────────────────────────────────────────────────

    def node_mapping(self, v_net, p_net, solution):
        """
        Run HPSO (paper-faithful, capacity-aware fitness) to find the best
        node assignment, then commit via controller.

        Returns True on success, False on failure.

        WHY we still call controller.node_mapping() at the end: it updates
        p_net resources AND populates solution['node_slots'] and
        solution['node_slots_info'] in the format expected by Recorder,
        Counter, and subsequent link_mapping(). We cannot bypass it even
        though HPSO already found (and validated) the assignment.
        """
        gbest, pbest, pbest_cost = hpso_main_loop(
            p_net=p_net,
            v_net=v_net,
            node_res_attrs=self._node_res_attrs,
            link_res_attrs=self._link_res_attrs,
            n_particles=self.num_particles,
            max_iteration=self.max_iteration,
            w_max=self.w_max,
            w_min=self.w_min,
            beta=self.beta,
            gamma=self.gamma,
            T0=self.T0,
            cooling_rate=self.cooling_rate,
            stop_on_first_feasible=self.stop_on_first_feasible,
            early_stop_patience=self.early_stop_patience,
        )

        if gbest is None or gbest is INFEASIBLE:
            solution['place_result'] = False
            return False

        # Try gbest first, then fallback through pbests in ascending cost.
        # (Mainly a safety net for races against concurrent resource changes
        # between search and commit; under single-threaded use gbest should
        # already pass controller validation since fitness was capacity-aware.)
        candidates = [gbest] + [
            pbest[i]
            for i in sorted(range(len(pbest)), key=lambda i: pbest_cost[i])
            if pbest_cost[i] < INFEASIBLE
        ]

        vnodes = list(v_net.nodes())

        for particle in candidates:
            # Build sorted_v_nodes and sorted_p_nodes for controller.node_mapping()
            # WHY: controller.node_mapping() expects lists, not a dict.
            # We pass v_nodes and p_nodes in the order HPSO determined, using
            # 'l2s2' matching to enforce the exact particle assignment.
            sorted_v_nodes = vnodes
            sorted_p_nodes = [particle[i] for i in range(len(vnodes))]

            # Reset node_slots before each attempt (controller appends, not overwrites)
            solution['node_slots'] = {}
            solution['node_slots_info'] = {}

            result = self.controller.node_mapping(
                v_net, p_net,
                sorted_v_nodes=sorted_v_nodes,
                sorted_p_nodes=sorted_p_nodes,
                solution=solution,
                reusable=False,
                inplace=False,         # ← DRY RUN: validates on a copy, doesn't modify p_net
                matching_mathod='l2s2',   # l2s2: strict positional matching
            )
            if result:
                return True

        solution['place_result'] = False
        return False

    def link_mapping(self, v_net, p_net, solution):
        if self.link_rank is None:
            sorted_v_links = list(v_net.links)
        else:
            sorted_v_links = sorted(v_net.links, key=lambda l: self.link_rank(v_net, l), reverse=True)
        return self.controller.link_mapping(
            v_net, p_net, solution=solution,
            sorted_v_links=sorted_v_links,
            shortest_method=self.shortest_method,
            k=self.k_shortest,
            inplace=False,        # ← DRY RUN
        )
