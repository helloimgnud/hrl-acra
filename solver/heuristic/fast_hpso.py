# =============================================================================
# Fast Hybrid PSO (HPSO) Solver — adapted for HRL-ACRA codebase
#
# Two public entry-points
#   1. FastHPSOSolver.solve(instance)
#        Pure meta-heuristic: runs HPSO, deploys the global-best particle.
#        Drop-in replacement for hrl_ra as OnlineEnv sub_solver.
#
#   2. FastHPSOSolver.run_and_get_candidates(v_net, p_net, k)
#        Hybrid support: runs HPSO, returns the top-k unique particles
#        (with proxy costs) for downstream RL selection.
# =============================================================================

import copy
import math
import random

import networkx as nx

from base import Solution
from solver.solver import Solver

# ── sentinel ──────────────────────────────────────────────────────────────────
_INFEASIBLE = 1e9


# ─────────────────────────────────────────────────────────────────────────────
# Minimal base class (mirrors virne's BaseMetaHeuristicSolver interface)
# ─────────────────────────────────────────────────────────────────────────────

class BaseMetaHeuristicSolver(Solver):
    """
    Thin wrapper that gives meta-heuristic solvers a uniform solve() interface.

    Subclasses implement meta_run(v_net, p_net) → Solution.
    solve() calls meta_run() then applies the result to the real p_net via
    controller.deploy() so that resource deductions happen exactly once and
    are always consistent with the solution's link_paths_info.
    """

    def solve(self, instance):
        v_net, p_net = instance["v_net"], instance["p_net"]
        solution = self.meta_run(v_net, p_net)
        if solution["result"]:
            # Apply the dry-run resource deductions to the real p_net
            self.controller.deploy(v_net, p_net, solution)
        return solution

    def meta_run(self, v_net, p_net):
        raise NotImplementedError


# =============================================================================
# 1.  Fast proxy fitness  (hop-distance × bandwidth, no resource reservation)
# =============================================================================

def _fast_fitness(particle, p_net, v_net, node_res_attr_names, link_res_attr_names):
    """
    Estimate mapping cost WITHOUT reserving any resources.

    Returns _INFEASIBLE when any node or connectivity constraint is violated.
    """
    vnodes = list(v_net.nodes())

    if len(set(particle)) < len(vnodes):   # non-injective mapping
        return _INFEASIBLE

    mapping = {}
    for i, v in enumerate(vnodes):
        s = particle[i]
        for attr in node_res_attr_names:
            if p_net.nodes[s].get(attr, 0) < v_net.nodes[v].get(attr, 0):
                return _INFEASIBLE
        mapping[v] = s

    est_link_cost = 0.0
    for (u, v) in v_net.edges():
        s_u, s_v = mapping[u], mapping[v]
        if s_u == s_v:
            continue
        try:
            hops = nx.shortest_path_length(p_net, s_u, s_v)
        except nx.NetworkXNoPath:
            return _INFEASIBLE
        demand = (v_net.edges[u, v].get(link_res_attr_names[0], 0)
                  if link_res_attr_names else 1)
        est_link_cost += hops * demand

    return est_link_cost


# =============================================================================
# 2.  Swarm initialisation
# =============================================================================

def _init_swarm(p_net, v_net, n_particles, node_res_attr_names):
    """Build initial swarm via largest-first greedy placement with top-3 random."""
    vnodes_sorted = sorted(
        v_net.nodes(),
        key=lambda v: sum(v_net.nodes[v].get(a, 0) for a in node_res_attr_names),
        reverse=True,
    )
    sub_sorted = sorted(
        p_net.nodes(),
        key=lambda s: sum(p_net.nodes[s].get(a, 0) for a in node_res_attr_names),
        reverse=True,
    )
    vnode_idx = {v: i for i, v in enumerate(v_net.nodes())}

    swarm = []
    for _ in range(n_particles):
        particle = [None] * v_net.num_nodes
        used: set = set()
        ok = True
        for v in vnodes_sorted:
            cands = [
                s for s in sub_sorted
                if all(p_net.nodes[s].get(a, 0) >= v_net.nodes[v].get(a, 0)
                       for a in node_res_attr_names)
                and s not in used
            ]
            if not cands:
                ok = False
                break
            k = random.randint(1, min(3, len(cands)))
            s = random.choice(cands[:k])
            particle[vnode_idx[v]] = s
            used.add(s)
        if ok:
            swarm.append(particle)

    sub_list = list(p_net.nodes())
    while len(swarm) < n_particles:
        if len(sub_list) < v_net.num_nodes:
            break
        random.shuffle(sub_list)
        swarm.append(sub_list[: v_net.num_nodes])

    return swarm


# =============================================================================
# 3.  Discrete PSO operators
# =============================================================================

def _op_minus(Xi, Xj):
    return [1 if Xi[k] == Xj[k] else 0 for k in range(len(Xi))]


def _op_plus(p, Vi, q, Vj):
    if p + q == 0:
        return Vi.copy()
    p_norm = p / (p + q)
    return [
        Vi[i] if (Vi[i] == Vj[i] or random.random() < p_norm) else Vj[i]
        for i in range(len(Vi))
    ]


def _op_multiply(Xi, V, v_net, p_net, node_res_attr_names):
    Xnew = Xi.copy()
    vnodes = list(v_net.nodes())
    used = set(Xnew)
    for i in range(len(V)):
        if V[i] == 0:
            v = vnodes[i]
            used.discard(Xnew[i])
            cands = [
                s for s in p_net.nodes()
                if all(p_net.nodes[s].get(a, 0) >= v_net.nodes[v].get(a, 0)
                       for a in node_res_attr_names)
                and s not in used
            ]
            if cands:
                Xnew[i] = random.choice(cands)
            used.add(Xnew[i])
    return Xnew


# =============================================================================
# 4.  SA neighbour
# =============================================================================

def _sa_neighbor(particle, p_net, v_net, node_res_attr_names):
    neighbor = particle.copy()
    used = set(neighbor)
    vnodes = list(v_net.nodes())
    i = random.randrange(len(particle))
    v = vnodes[i]
    used.discard(particle[i])
    cands = [
        s for s in p_net.nodes()
        if all(p_net.nodes[s].get(a, 0) >= v_net.nodes[v].get(a, 0)
               for a in node_res_attr_names)
        and s not in used
    ]
    if cands:
        neighbor[i] = random.choice(cands)
    return neighbor


# =============================================================================
# 5.  Solver
# =============================================================================

class FastHPSOSolver(BaseMetaHeuristicSolver):
    """
    Fast Hybrid PSO Solver for Virtual Network Embedding.

    Hyper-parameters (all overridable via kwargs)
    ───────────────────────────────────────────────
    num_particles   swarm size                  (20)
    max_iteration   PSO+SA iterations           (30)
    w_max / w_min   inertia weight bounds       (0.9 / 0.5)
    beta            cognitive weight            (0.3)
    gamma           social weight               (0.3)
    T0              initial SA temperature      (100)
    cooling_rate    SA geometric factor         (0.95)
    shortest_method link-mapping method         ('k_shortest')
    k_shortest      k for k-shortest paths      (10)
    """

    def __init__(self, controller, recorder, counter, **kwargs):
        super().__init__(controller, recorder, counter, **kwargs)

        self.num_particles  = kwargs.get("num_particles",  20)
        self.max_iteration  = kwargs.get("max_iteration",  30)
        self.w_max          = kwargs.get("w_max",          0.9)
        self.w_min          = kwargs.get("w_min",          0.5)
        self.beta           = kwargs.get("beta",           0.3)
        self.gamma          = kwargs.get("gamma",          0.3)
        self.T0             = kwargs.get("T0",             100.0)
        self.cooling_rate   = kwargs.get("cooling_rate",   0.95)
        self.shortest_method = kwargs.get("shortest_method", "k_shortest")
        self.k_shortest      = kwargs.get("k_shortest",      10)

        # Cache attr names from controller (set after controller is initialised)
        self._node_res_attrs = None
        self._link_res_attrs = None

    # ── attribute name helpers ────────────────────────────────────────────────

    def _get_node_res_attr_names(self):
        if self._node_res_attrs is None:
            self._node_res_attrs = [a.name for a in self.controller.node_resource_attrs]
        return self._node_res_attrs

    def _get_link_res_attr_names(self):
        if self._link_res_attrs is None:
            self._link_res_attrs = [a.name for a in self.controller.link_resource_attrs]
        return self._link_res_attrs

    # ── helpers ───────────────────────────────────────────────────────────────

    def _particle_to_node_slots(self, particle, v_net):
        vnodes = list(v_net.nodes())
        return {vnodes[i]: particle[i] for i in range(len(vnodes))}

    def _try_deploy_particle(self, particle, v_net, p_net):
        """
        Dry-run deployment via inplace=False on a p_net copy.
        Returns a populated Solution (result True/False).
        The REAL p_net is NOT modified here; caller uses controller.deploy().
        """
        node_slots = self._particle_to_node_slots(particle, v_net)
        solution = Solution(v_net)
        self.controller.deploy_with_node_slots(
            v_net, p_net, node_slots, solution,
            inplace=False,
            shortest_method=self.shortest_method,
            k_shortest=self.k_shortest,
        )
        self.counter.count_solution(v_net, solution)
        return solution

    def _fitness(self, particle, p_net, v_net):
        return _fast_fitness(
            particle, p_net, v_net,
            self._get_node_res_attr_names(),
            self._get_link_res_attr_names(),
        )

    # ── core PSO/SA loop (shared by meta_run and run_and_get_candidates) ──────

    def _run_swarm(self, v_net, p_net):
        """
        Execute the full HPSO+SA loop.

        Returns
        -------
        gbest      : best particle found (list of p_node indices)
        gbest_cost : proxy cost of gbest
        pbest      : per-particle personal best particles
        pbest_cost : per-particle personal best costs
        """
        node_res_attrs = self._get_node_res_attr_names()
        link_res_attrs = self._get_link_res_attr_names()
        num_v = v_net.num_nodes

        swarm = _init_swarm(p_net, v_net, self.num_particles, node_res_attrs)
        if not swarm:
            return None, _INFEASIBLE, [], []

        velocities = [
            [random.randint(0, 1) for _ in range(num_v)]
            for _ in range(len(swarm))
        ]

        pbest      = copy.deepcopy(swarm)
        pbest_cost = [self._fitness(p, p_net, v_net) for p in swarm]

        gbest      = None
        gbest_cost = _INFEASIBLE

        for i, cost in enumerate(pbest_cost):
            if cost < gbest_cost:
                gbest_cost = cost
                gbest = swarm[i].copy()

        T = self.T0

        for it in range(self.max_iteration):
            alpha = self.w_max - (self.w_max - self.w_min) * it / self.max_iteration
            total = alpha + self.beta + self.gamma
            a, b, c = (
                (alpha / total, self.beta / total, self.gamma / total)
                if total != 0 else (0.33, 0.33, 0.34)
            )

            for i in range(len(swarm)):
                dp = _op_minus(pbest[i], swarm[i])
                dg = _op_minus(gbest, swarm[i]) if gbest is not None else [0] * num_v

                v_inertia   = _op_plus(a, velocities[i], b, dp)
                velocities[i] = _op_plus(1 - c, v_inertia, c, dg)

                new_pos  = _op_multiply(swarm[i], velocities[i], v_net, p_net, node_res_attrs)
                new_cost = self._fitness(new_pos, p_net, v_net)

                if new_cost < pbest_cost[i]:
                    pbest[i]      = new_pos.copy()
                    pbest_cost[i] = new_cost
                    if new_cost < gbest_cost:
                        gbest      = new_pos.copy()
                        gbest_cost = new_cost

                swarm[i] = new_pos

                # SA perturbation
                if T > 0.1:
                    cand      = _sa_neighbor(swarm[i], p_net, v_net, node_res_attrs)
                    cand_cost = self._fitness(cand, p_net, v_net)
                    delta     = cand_cost - new_cost
                    if delta < 0:
                        accept = True
                    else:
                        try:
                            prob = math.exp(-delta / T)
                        except OverflowError:
                            prob = 0.0
                        accept = random.random() < prob

                    if accept:
                        swarm[i] = cand
                        if cand_cost < pbest_cost[i]:
                            pbest[i]      = cand.copy()
                            pbest_cost[i] = cand_cost
                            if cand_cost < gbest_cost:
                                gbest      = cand.copy()
                                gbest_cost = cand_cost

            T *= self.cooling_rate

        return gbest, gbest_cost, pbest, pbest_cost

    # ── public API ────────────────────────────────────────────────────────────

    def meta_run(self, v_net, p_net):
        """
        Full HPSO run → best feasible Solution (dry-run, p_net unchanged).
        BaseMetaHeuristicSolver.solve() will call controller.deploy() afterwards.
        """
        gbest, gbest_cost, pbest, pbest_cost = self._run_swarm(v_net, p_net)

        if gbest is None or gbest_cost >= _INFEASIBLE:
            return Solution(v_net)

        solution = self._try_deploy_particle(gbest, v_net, p_net)

        # Fallback: try remaining pbests in ascending cost order
        if not solution["result"]:
            for idx in sorted(range(len(pbest)), key=lambda i: pbest_cost[i]):
                if pbest_cost[idx] >= _INFEASIBLE:
                    break
                solution = self._try_deploy_particle(pbest[idx], v_net, p_net)
                if solution["result"]:
                    break

        return solution

    def run_and_get_candidates(self, v_net, p_net, k=5):
        """
        Run HPSO and return the top-k unique, node-feasible particles.

        Parameters
        ----------
        v_net : VirtualNetwork
        p_net : PhysicalNetwork  (will NOT be modified — we work on a copy)
        k     : number of candidates to return

        Returns
        -------
        list of (particle: list[int], proxy_cost: float)
            Sorted ascending by proxy_cost.  May have fewer than k entries.
        """
        p_net_copy = copy.deepcopy(p_net)
        _, _, pbest, pbest_cost = self._run_swarm(v_net, p_net_copy)

        # Deduplicate by particle identity
        seen = {}
        for particle, cost in zip(pbest, pbest_cost):
            if cost >= _INFEASIBLE:
                continue
            key = tuple(particle)
            if key not in seen or cost < seen[key][1]:
                seen[key] = (particle, cost)

        sorted_cands = sorted(seen.values(), key=lambda x: x[1])
        return sorted_cands[:k]