# solver/heuristic/fast_hpso/fast_hpso_solver.py
"""
FastHPSOSolver — hrl-acra integration of the Hybrid PSO solver.

Operates in two modes without any code changes:
  Mode 1 (independent): instantiated by BasicScenario; solve() called by BasicScenario.run()
  Mode 2 (sub-solver):  instantiated by OnlineEnv; solve() called by env.step() when action=1

The class is identical in both modes. Mode selection is purely a matter of who
instantiates the solver and who calls solve().
"""
import copy

from base import Solution
from ..node_rank import NodeRankSolver
from .core import hpso_main_loop, INFEASIBLE


class FastHPSOSolver(NodeRankSolver):
    """
    Meta-heuristic VNE solver using Fast Hybrid PSO + Simulated Annealing.

    Inherits NodeRankSolver to reuse:
      - solve() template (node_mapping → link_mapping → return solution)
      - link_mapping() using controller.link_mapping()
      - controller, recorder, counter infrastructure

    Overrides:
      - node_mapping(): replaces greedy ranking with HPSO swarm search

    Does NOT use self.node_rank or self.link_rank inherited from NodeRankSolver.
    """

    name = 'fast_hpso'

    def __init__(self, controller, recorder, counter, **kwargs):
        super(FastHPSOSolver, self).__init__(controller, recorder, counter, **kwargs)
        self.is_sub_solver = (kwargs.get('solver_name') != 'fast_hpso')
        # HPSO hyper-parameters
        self.num_particles = kwargs.get('num_particles', 20)
        self.max_iteration = kwargs.get('max_iteration', 30)
        self.w_max = kwargs.get('w_max', 0.9)
        self.w_min = kwargs.get('w_min', 0.5)
        self.beta = kwargs.get('beta', 0.3)
        self.gamma = kwargs.get('gamma', 0.3)
        self.T0 = kwargs.get('T0', 100.0)
        self.cooling_rate = kwargs.get('cooling_rate', 0.95)
        # Inherit shortest_method and k_shortest from Solver base via NodeRankSolver

        # Resolve resource attribute names from controller
        # WHY: avoid hard-coding 'cpu'/'bw'; works with any attribute config
        self._node_res_attrs = [a.name for a in self.controller.node_resource_attrs]
        self._link_res_attrs = [a.name for a in self.controller.link_resource_attrs]

    def solve(self, instance):
        solution = super(FastHPSOSolver, self).solve(instance)
        if solution['result'] and getattr(self, 'is_sub_solver', False):
            self.controller.deploy(instance['v_net'], instance['p_net'], solution)
        return solution

    # ─────────────────────────────────────────────────────────────────────────
    # Core override: replace greedy node ranking with HPSO search
    # ─────────────────────────────────────────────────────────────────────────

    def node_mapping(self, v_net, p_net, solution):
        """
        Run HPSO to find the best node assignment, then commit via controller.

        Returns True on success, False on failure.

        WHY we still call controller.node_mapping() at the end:
          controller.node_mapping() updates p_net resources AND populates
          solution['node_slots'] and solution['node_slots_info'] in the format
          expected by Recorder, Counter, and subsequent link_mapping().
          We cannot bypass it even though HPSO already found the assignment.
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
        )

        if gbest is None or gbest is INFEASIBLE:
            solution['place_result'] = False
            return False

        # Try gbest first, then fallback through pbests in ascending proxy cost
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
