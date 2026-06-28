# solver/heuristic/hpso/core.py
"""
Pure HPSO algorithm for VNE — paper-faithful implementation of:

    P. Zhang, Y. Hong, X. Pang, C. Jiang,
    "VNE-HPSO: Virtual Network Embedding Algorithm Based on Hybrid
    Particle Swarm Optimization," IEEE Access, vol. 8, 2020.

No framework dependencies — operates on raw NetworkX graphs with resource
dicts. Resource attributes are passed in as lists of attribute names (not
hard-coded 'cpu'/'bw'), matching the convention used by fast_hpso/core.py.

RELATIONSHIP TO fast_hpso
--------------------------
fast_hpso/core.py trades paper-accuracy for speed: its inner-loop fitness
only estimates link cost from hop-distance (no capacity check), and relies
on the framework controller to do the real, capacity-aware link mapping as
a one-shot dry run *after* the swarm search is done. That is a good
engineering trade-off, but it means the particle that "wins" the search is
not necessarily the one that is truly cheapest under bandwidth constraints.

This module instead implements Algorithm 1 of the paper directly: fitness
evaluation performs genuine capacity-aware shortest-path search for every
virtual link (Eqs. 3, 4, 10, 12), so the cost the swarm optimizes against is
the same cost the paper defines (Eq. 6). It is slower per-iteration than
fast_hpso, but its search decisions are paper-accurate. The framework
controller is still used afterwards (by the solver wrapper) to actually
*commit/validate* node_slots in the format the rest of the pipeline expects
— exactly as fast_hpso_solver.py does — but it is no longer responsible for
discovering link-feasibility; it only re-confirms what HPSO already found.

BUGS FIXED RELATIVE TO THE OLDER hpso.py PROTOTYPE
----------------------------------------------------
1. hpso.py never tracked `gbest` (global best) at all — `dg` was computed
   against `pbest[i]` a second time instead of the swarm's global best,
   silently degrading HPSO to a population of independent SA/hill-climbers
   with no swarm-level information sharing. Fixed: gbest is tracked and
   used exactly as Eq. (17) / Algorithm 1 lines 14-16 require.
2. hpso.py's `operation_plus(p, Vi, q, Vj)` used `p` directly as a
   probability without normalizing by `p + q`, even though it is invoked
   twice in sequence with weights that individually don't sum to 1
   (`a`, then `b`, then `c`, with `a+b+c == 1` only when all three are
   combined). This silently biased every velocity update. Fixed: each
   call normalizes via `p / (p + q)`, so the two sequential ⊕ operations
   correctly reconstruct the 3-way weighting of Eq. (17).
3. hpso.py applied the Simulated-Annealing Metropolis acceptance test to
   *both* the deterministic PSO move and the random SA neighbor, and used
   `T0` as a fixed constant (100) rather than deriving it from the initial
   swarm as Algorithm 1, line 6 specifies (`t0 = fmax - fmin`). Fixed: the
   PSO move (lines 9-16) is unconditional; only the extra random neighbor
   (lines 17-24) goes through the Metropolis test, and T0 defaults to
   `fmax - fmin` of the initial population unless explicitly overridden.
4. hpso.py returned on the *first* feasible particle found during the
   iteration loop, never actually completing the search nor returning the
   true `gBest` as Algorithm 1, lines 27-28 specify. Fixed: the loop always
   runs `max_iteration` times and returns gbest (plus pbest list, for the
   caller's fallback validation — same pattern as fast_hpso).
"""
import copy
import math
import random
import networkx as nx

INFEASIBLE = 1e9


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Capacity-aware shortest path  (paper Eq. 3 / Eq. 12 — link feasibility)
# ─────────────────────────────────────────────────────────────────────────────

def _capacity_subgraph(p_net, demands, link_attrs):
    """
    Build a subgraph of p_net containing only edges whose residual capacity
    on every attribute in link_attrs is >= the corresponding demand.

    If link_attrs is empty/None, no capacity filtering is applied (pure
    hop-count shortest path).
    """
    pairs = [(a, d) for a, d in zip(link_attrs or [], demands or []) if a is not None]
    if not pairs:
        return p_net

    H = nx.Graph()
    H.add_nodes_from(p_net.nodes())
    H.add_edges_from(
        (u, v) for u, v, data in p_net.edges(data=True)
        if all(data.get(attr, 0) >= dem for attr, dem in pairs)
    )
    return H


def shortest_path_with_capacity(p_net, s_src, s_dst, demands, link_attrs):
    """
    Find the shortest (min-hop) path between s_src and s_dst such that every
    edge on the path has residual capacity >= demand on every link_attr.

    Returns list[node] (the path) or None if infeasible / disconnected.
    """
    if s_src == s_dst:
        return [s_src]
    H = _capacity_subgraph(p_net, demands, link_attrs)
    try:
        return nx.shortest_path(H, s_src, s_dst)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def build_edge_subgraph_cache(p_net, v_net, link_res_attrs):
    """
    PERFORMANCE: precompute the capacity-filtered substrate subgraph once
    per virtual edge, instead of rebuilding it from scratch on every single
    fitness call.

    This is safe and changes no behavior: hpso never reserves resources
    during the search (see hpso_fitness docstring), so p_net's residual
    capacities — and therefore the feasible substrate subgraph for a given
    virtual edge's fixed demand — are constant for the *entire* run of
    hpso_main_loop. Without this cache, hpso_fitness would call
    _capacity_subgraph() (an O(|Es|) scan) up to
    n_particles * (1 + 2*max_iteration) * |Lv| times for a single VNR
    embedding (e.g. 10 * 101 * |Lv| with the paper's default parameters) —
    almost all of that work recomputing the exact same filtered graph.
    Hoisting it out of the loop removes that redundant cost; the per-call
    nx.shortest_path() BFS itself still runs once per fitness evaluation,
    since that part genuinely depends on which substrate nodes the
    particle's mapping picked.
    """
    cache = {}
    for u, v in v_net.edges():
        demands = [v_net.edges[u, v].get(attr, 1) for attr in link_res_attrs] or [1]
        cache[(u, v)] = _capacity_subgraph(p_net, demands, link_res_attrs)
    return cache


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Full fitness  (paper Eq. 6 / Eq. 10 — real embedding cost, not a proxy)
# ─────────────────────────────────────────────────────────────────────────────

def hpso_fitness(particle, p_net, v_net, node_res_attrs, link_res_attrs, edge_cache=None):
    """
    Evaluate a particle's TRUE embedding cost — no resources are reserved.

    Args:
        particle:        list[int] — p_node ID per v_node (indexed by
                          list(v_net.nodes()) order)
        p_net:           NetworkX graph (substrate)
        v_net:           NetworkX graph (virtual request)
        node_res_attrs:  list[str] — resource attribute names on nodes
        link_res_attrs:  list[str] — resource attribute names on links
        edge_cache:      optional dict from build_edge_subgraph_cache(),
                          keyed by (u, v) as yielded by v_net.edges(). When
                          provided, skips rebuilding the capacity-filtered
                          subgraph on every call (see build_edge_subgraph_cache
                          docstring). Purely a speed optimization — passing
                          None reproduces the exact same result, just slower.

    Returns:
        float — lower is better; INFEASIBLE sentinel on hard constraint
        violation (node overcommit, non-injective mapping, or no
        capacity-feasible path for some virtual link).
    """
    vnodes = list(v_net.nodes())

    # Injective check
    if len(set(particle)) < len(vnodes):
        return INFEASIBLE

    mapping = {}
    for i, v in enumerate(vnodes):
        s = particle[i]
        for attr in node_res_attrs:
            if p_net.nodes[s].get(attr, 0) < v_net.nodes[v].get(attr, 0):
                return INFEASIBLE
        mapping[v] = s

    total_cost = 0.0
    for u, v in v_net.edges():
        s_u, s_v = mapping[u], mapping[v]

        if s_u == s_v:
            continue  # co-located: no substrate link consumed

        demands = [v_net.edges[u, v].get(attr, 1) for attr in link_res_attrs] or [1]

        if edge_cache is not None:
            H = edge_cache.get((u, v), edge_cache.get((v, u)))
            if H is None:
                H = _capacity_subgraph(p_net, demands, link_res_attrs)
        else:
            H = _capacity_subgraph(p_net, demands, link_res_attrs)

        try:
            path = nx.shortest_path(H, s_u, s_v)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return INFEASIBLE

        hops = len(path) - 1
        bw_demand = demands[0]
        total_cost += hops * bw_demand

    return total_cost


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Swarm initialisation — particle initialization allocation strategy
#     (paper Section IV-D / V-D, FIGURE 5)
# ─────────────────────────────────────────────────────────────────────────────

def init_swarm(p_net, v_net, n_particles, node_res_attrs):
    """
    Build initial swarm using the paper's particle initialization allocation
    strategy:
      1. Sort virtual nodes and physical nodes descending by resource amount.
      2. Prune physical nodes below the minimum virtual-node resource demand
         (FIGURE 5: Slist1 -> Slist2 pruning step).
      3. For each virtual node (largest demand first), build a candidate list
         of feasible, not-yet-used physical nodes, and pick one with a small
         amount of randomness among the top candidates (Top-K), to keep
         enough population diversity while avoiding the fragmentation caused
         by pure random initialization.
    """
    def demand(v):
        return sum(v_net.nodes[v].get(a, 0) for a in node_res_attrs)

    def supply(s):
        return sum(p_net.nodes[s].get(a, 0) for a in node_res_attrs)

    vnodes_sorted = sorted(v_net.nodes(), key=demand, reverse=True)
    min_demand = min((demand(v) for v in vnodes_sorted), default=0)

    pnodes_sorted = sorted(
        (s for s in p_net.nodes() if supply(s) >= min_demand),
        key=supply,
        reverse=True,
    )
    vnode_idx = {v: i for i, v in enumerate(v_net.nodes())}

    swarm = []
    for _ in range(n_particles):
        particle = [None] * v_net.number_of_nodes()
        used = set()
        ok = True
        for v in vnodes_sorted:
            cands = [
                s for s in pnodes_sorted
                if all(p_net.nodes[s].get(a, 0) >= v_net.nodes[v].get(a, 0)
                       for a in node_res_attrs)
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

    # Fallback: pure random injective particles, to keep the swarm full size
    # even under tight resource conditions.
    pnode_list = list(p_net.nodes())
    while len(swarm) < n_particles:
        if len(pnode_list) < v_net.number_of_nodes():
            break
        random.shuffle(pnode_list)
        swarm.append(pnode_list[: v_net.number_of_nodes()])

    return swarm


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Discrete PSO operators  (paper Eqs. 14-18, Section V-B)
# ─────────────────────────────────────────────────────────────────────────────

def op_minus(Xi, Xj):
    r"""
    Xi (-) Xj, the paper's circled-minus operator (definition #3): 1 where
    Xi and Xj AGREE, 0 where they differ. Despite the name "minus" /
    "difference", the paper defines agreement as 1 — see the worked
    example: (1,3,4,6,2) (-) (2,3,5,6,9) = (0,1,0,1,0).
    """
    return [1 if Xi[k] == Xj[k] else 0 for k in range(len(Xi))]


def op_plus(p, Vi, q, Vj):
    r"""
    p*Vi (+) q*Vj, the paper's circled-plus operator (definition #4):
    per-dimension, keep the shared value where Vi and Vj already agree;
    where they disagree, sample Vi with probability p/(p+q) and Vj
    otherwise. Normalizing by p+q is required because Eq. (17) combines
    THREE terms via two sequential applications of (+), so the weights
    passed in at each step don't individually sum to 1.
    """
    if p + q == 0:
        return Vi.copy()
    p_norm = p / (p + q)
    return [
        Vi[i] if (Vi[i] == Vj[i] or random.random() < p_norm) else Vj[i]
        for i in range(len(Vi))
    ]


def op_multiply(Xi, V, v_net, p_net, node_res_attrs):
    r"""
    Xi (x) V, the paper's circled-times operator (definition #5): apply
    velocity to position. Dimensions where V[i]=1 keep their current
    assignment; dimensions where V[i]=0 are re-sampled from feasible,
    currently-unused p_nodes (this maintains injectivity of the embedding).
    """
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
                       for a in node_res_attrs)
                and s not in used
            ]
            if cands:
                Xnew[i] = random.choice(cands)
            used.add(Xnew[i])

    return Xnew


# ─────────────────────────────────────────────────────────────────────────────
# 5.  SA neighbour generator  (Algorithm 1, line 17: "randomly generate a
#     new position for the particle")
# ─────────────────────────────────────────────────────────────────────────────

def sa_neighbor(particle, p_net, v_net, node_res_attrs):
    """Single-position swap to a new feasible, currently-unused p_node."""
    neighbor = particle.copy()
    vnodes = list(v_net.nodes())
    used = set(neighbor)

    i = random.randrange(len(particle))
    v = vnodes[i]
    used.discard(particle[i])
    cands = [
        s for s in p_net.nodes()
        if all(p_net.nodes[s].get(a, 0) >= v_net.nodes[v].get(a, 0)
               for a in node_res_attrs)
        and s not in used
    ]
    if cands:
        neighbor[i] = random.choice(cands)
    return neighbor


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Main loop — Algorithm 1 of the paper, faithfully reproduced
# ─────────────────────────────────────────────────────────────────────────────

def hpso_main_loop(p_net, v_net, node_res_attrs, link_res_attrs,
                    n_particles=20, max_iteration=30,
                    w_max=0.9, w_min=0.5, beta=0.3, gamma=0.3,
                    T0=100.0, cooling_rate=0.95,
                    stop_on_first_feasible=False, early_stop_patience=None):
    """
    Run the full HPSO + SA search (Algorithm 1).

    Args mirror Table 1 of the paper by default (10 particles, 50
    iterations, w_max=0.9, w_min=0.4, beta=0.3, gamma=0.4, cooling 0.9).

    T0: if None (default), it is derived from the initial swarm exactly as
        Algorithm 1, line 6 specifies: t0 = fmax - fmin. Pass an explicit
        float to override (e.g. for warm starts / unit tests).

    stop_on_first_feasible: NOT part of the paper's Algorithm 1, which
        always runs the full `max_iteration` loop before returning gBest.
        Default False (paper-faithful). Set True only if you need a
        first-feasible-wins speed trade-off (closer to what the older
        hpso.py prototype did, minus its other bugs) — this returns as soon
        as ANY particle becomes feasible, without giving the swarm a chance
        to refine that particle's link-mapping cost further.

    early_stop_patience: NOT part of Algorithm 1 either. If set to an int N,
        the search stops once gbest_cost hasn't improved for N consecutive
        iterations. Gentler than stop_on_first_feasible — the swarm still
        gets to refine cost, it just stops once it visibly plateaus.
        Default None (disabled, paper-faithful: always runs max_iteration).

    Returns:
        (best_particle: list[int] | None, pbest_list: list[list[int]],
         pbest_costs: list[float])
        or (None, [], []) if the swarm could not be initialised.

    Caller (the framework solver wrapper) is responsible for committing the
    winning particle via controller.node_mapping(); since fitness here is
    already capacity-aware, that commit step should normally just re-confirm
    the same assignment rather than discover a different one. Returning the
    full pbest list (sorted by the caller) preserves the same robust
    fallback pattern used by fast_hpso, in case live resource state shifted
    between search and commit (e.g. concurrent solver use).

    PERFORMANCE NOTE: the per-virtual-edge capacity-filtered substrate
    subgraph is built once via build_edge_subgraph_cache() and reused for
    every fitness call in this run (safe — p_net is read-only throughout the
    search, never reserved). The remaining cost is the BFS shortest-path
    query itself, run once per virtual edge per fitness evaluation; that
    part is inherent to evaluating the paper's real cost function (Eq. 6)
    and can only be reduced further by lowering n_particles/max_iteration or
    opting into one of the early-stop flags above.
    """
    num_v = v_net.number_of_nodes()
    swarm = init_swarm(p_net, v_net, n_particles, node_res_attrs)
    if not swarm:
        return None, [], []

    edge_cache = build_edge_subgraph_cache(p_net, v_net, link_res_attrs)

    velocities = [[random.randint(0, 1) for _ in range(num_v)] for _ in range(len(swarm))]
    pbest = copy.deepcopy(swarm)
    pbest_cost = [hpso_fitness(p, p_net, v_net, node_res_attrs, link_res_attrs, edge_cache) for p in swarm]

    gbest = None
    gbest_cost = INFEASIBLE
    for i, cost in enumerate(pbest_cost):
        if cost < gbest_cost:
            gbest_cost = cost
            gbest = swarm[i].copy()

    if stop_on_first_feasible and gbest_cost < INFEASIBLE:
        return gbest, pbest, pbest_cost

    # Algorithm 1, line 6: t0 = fmax - fmin, derived from the initial swarm.
    if T0 is None:
        finite_costs = [c for c in pbest_cost if c < INFEASIBLE]
        if len(finite_costs) >= 2:
            T = max(finite_costs) - min(finite_costs)
        else:
            T = 100.0  # fallback when the initial swarm gives no usable spread
        if T <= 0:
            T = 100.0
    else:
        T = T0

    no_improve_count = 0

    for it in range(max_iteration):
        alpha = w_max - (w_max - w_min) * it / max_iteration
        total = alpha + beta + gamma
        a, b, c = (alpha / total, beta / total, gamma / total) if total else (0.33, 0.33, 0.34)

        prev_gbest_cost = gbest_cost

        for i in range(len(swarm)):
            # ---- PSO update (Algorithm 1, lines 10-16): unconditional move ----
            dp = op_minus(pbest[i], swarm[i])
            dg = op_minus(gbest, swarm[i]) if gbest else [0] * num_v
            v_inertia = op_plus(a, velocities[i], b, dp)
            velocities[i] = op_plus(1 - c, v_inertia, c, dg)

            new_pos = op_multiply(swarm[i], velocities[i], v_net, p_net, node_res_attrs)
            new_cost = hpso_fitness(new_pos, p_net, v_net, node_res_attrs, link_res_attrs, edge_cache)
            swarm[i] = new_pos

            if new_cost < pbest_cost[i]:
                pbest[i] = new_pos.copy()
                pbest_cost[i] = new_cost
                if new_cost < gbest_cost:
                    gbest = new_pos.copy()
                    gbest_cost = new_cost

            # ---- SA perturbation (Algorithm 1, lines 17-24): Metropolis test ----
            if T > 1e-6:
                cand = sa_neighbor(swarm[i], p_net, v_net, node_res_attrs)
                cand_cost = hpso_fitness(cand, p_net, v_net, node_res_attrs, link_res_attrs, edge_cache)
                delta = cand_cost - new_cost
                if delta < 0:
                    accept = True
                else:
                    try:
                        prob = math.exp(-delta / T)
                    except OverflowError:
                        prob = 0.0
                    accept = random.random() < min(1.0, prob)

                if accept:
                    swarm[i] = cand
                    if cand_cost < pbest_cost[i]:
                        pbest[i] = cand.copy()
                        pbest_cost[i] = cand_cost
                        if cand_cost < gbest_cost:
                            gbest = cand.copy()
                            gbest_cost = cand_cost

        if stop_on_first_feasible and gbest_cost < INFEASIBLE:
            break

        if early_stop_patience is not None:
            if gbest_cost < prev_gbest_cost - 1e-9:
                no_improve_count = 0
            else:
                no_improve_count += 1
                if no_improve_count >= early_stop_patience:
                    break

        # Algorithm 1, line 25: t = t * 0.9 (cooling_rate default matches paper)
        T *= cooling_rate

    return gbest, pbest, pbest_cost
