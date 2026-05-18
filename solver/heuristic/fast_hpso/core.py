# solver/heuristic/fast_hpso/core.py
"""
Pure HPSO algorithm for VNE.
No framework dependencies — operates on raw NetworkX graphs with resource dicts.
Resource attributes are passed in as lists of attribute names (not hard-coded 'cpu'/'bw').
"""
import copy
import math
import random
import networkx as nx

INFEASIBLE = 1e9


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Proxy fitness  (inner loop — no resource reservation)
# ─────────────────────────────────────────────────────────────────────────────

def fast_fitness(particle, p_net, v_net, node_res_attrs, link_res_attrs):
    """
    Evaluate a particle WITHOUT reserving any resources.

    Args:
        particle:        list[int] — p_node ID per v_node (indexed by list(v_net.nodes()) order)
        p_net:           NetworkX graph (substrate)
        v_net:           NetworkX graph (virtual request)
        node_res_attrs:  list[str] — resource attribute names on nodes (e.g. ['cpu'])
        link_res_attrs:  list[str] — resource attribute names on links (e.g. ['bw'])

    Returns:
        float — lower is better; INFEASIBLE sentinel on hard constraint violation
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

    est_link_cost = 0.0
    for u, v in v_net.edges():
        s_u, s_v = mapping[u], mapping[v]
        if s_u == s_v:
            continue
        try:
            hops = nx.shortest_path_length(p_net, s_u, s_v)
        except nx.NetworkXNoPath:
            return INFEASIBLE
        demand = v_net.edges[u, v].get(link_res_attrs[0], 1) if link_res_attrs else 1
        est_link_cost += hops * demand

    return est_link_cost


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Swarm initialisation
# ─────────────────────────────────────────────────────────────────────────────

def init_swarm(p_net, v_net, n_particles, node_res_attrs):
    """
    Build initial swarm with CPU-aware greedy + Top-K randomness.

    WHY: pure random produces mostly infeasible particles; pure greedy produces
    near-identical particles with no diversity. Top-K greedy is the sweet spot.
    """
    vnodes_sorted = sorted(
        v_net.nodes(),
        key=lambda v: sum(v_net.nodes[v].get(a, 0) for a in node_res_attrs),
        reverse=True,
    )
    pnodes_sorted = sorted(
        p_net.nodes(),
        key=lambda s: sum(p_net.nodes[s].get(a, 0) for a in node_res_attrs),
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

    # Fallback: pure random injective particles
    pnode_list = list(p_net.nodes())
    while len(swarm) < n_particles:
        if len(pnode_list) < v_net.number_of_nodes():
            break
        random.shuffle(pnode_list)
        swarm.append(pnode_list[: v_net.number_of_nodes()])

    return swarm


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Discrete PSO operators  (preserved verbatim from fast_hpso.py)
# ─────────────────────────────────────────────────────────────────────────────

def op_minus(Xi, Xj):
    """Velocity = agreement vector: 1 where Xi and Xj agree, 0 otherwise."""
    return [1 if Xi[k] == Xj[k] else 0 for k in range(len(Xi))]


def op_plus(p, Vi, q, Vj):
    """Merge two velocity vectors: sample from Vi with prob p/(p+q)."""
    if p + q == 0:
        return Vi.copy()
    p_norm = p / (p + q)
    return [
        Vi[i] if (Vi[i] == Vj[i] or random.random() < p_norm) else Vj[i]
        for i in range(len(Vi))
    ]


def op_multiply(Xi, V, v_net, p_net, node_res_attrs):
    """
    Apply velocity to position.
    Dimensions where V[i]=0 → re-sample from feasible p_nodes (maintains injectivity).
    Dimensions where V[i]=1 → keep current assignment.
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
# 4.  SA neighbour generator
# ─────────────────────────────────────────────────────────────────────────────

def sa_neighbor(particle, p_net, v_net, node_res_attrs):
    """Single-position swap to a new feasible p_node."""
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
# 5.  Main loop  — returns best_particle list[int] or None
# ─────────────────────────────────────────────────────────────────────────────

def hpso_main_loop(p_net, v_net, node_res_attrs, link_res_attrs,
                   n_particles=20, max_iteration=30,
                   w_max=0.9, w_min=0.5, beta=0.3, gamma=0.3,
                   T0=100.0, cooling_rate=0.95):
    """
    Run the full HPSO + SA search.

    Returns:
        (best_particle: list[int], pbest_list: list[list[int]], pbest_costs: list[float])
        or (None, [], []) if swarm could not be initialised.

    Caller is responsible for final Dijkstra validation (build_and_reserve or
    controller.node_mapping + link_mapping).

    WHY this signature returns pbest alongside gbest: the virne version demonstrated
    that gbest may fail full BW validation while a pbest with slightly higher proxy cost
    succeeds. Returning all pbests lets the caller implement the fallback loop cheaply.
    """
    num_v = v_net.number_of_nodes()
    swarm = init_swarm(p_net, v_net, n_particles, node_res_attrs)
    if not swarm:
        return None, [], []

    velocities = [[random.randint(0, 1) for _ in range(num_v)] for _ in range(len(swarm))]
    pbest = copy.deepcopy(swarm)
    pbest_cost = [fast_fitness(p, p_net, v_net, node_res_attrs, link_res_attrs) for p in swarm]

    gbest = None
    gbest_cost = INFEASIBLE
    for i, cost in enumerate(pbest_cost):
        if cost < gbest_cost:
            gbest_cost = cost
            gbest = swarm[i].copy()

    T = T0

    for it in range(max_iteration):
        alpha = w_max - (w_max - w_min) * it / max_iteration
        total = alpha + beta + gamma
        a, b, c = (alpha / total, beta / total, gamma / total) if total else (0.33, 0.33, 0.34)

        for i in range(len(swarm)):
            # PSO velocity update
            dp = op_minus(pbest[i], swarm[i])
            dg = op_minus(gbest, swarm[i]) if gbest else [0] * num_v
            v_inertia = op_plus(a, velocities[i], b, dp)
            velocities[i] = op_plus(1 - c, v_inertia, c, dg)

            new_pos = op_multiply(swarm[i], velocities[i], v_net, p_net, node_res_attrs)
            new_cost = fast_fitness(new_pos, p_net, v_net, node_res_attrs, link_res_attrs)

            if new_cost < pbest_cost[i]:
                pbest[i] = new_pos.copy()
                pbest_cost[i] = new_cost
                if new_cost < gbest_cost:
                    gbest = new_pos.copy()
                    gbest_cost = new_cost

            swarm[i] = new_pos

            # SA perturbation
            if T > 0.1:
                cand = sa_neighbor(swarm[i], p_net, v_net, node_res_attrs)
                cand_cost = fast_fitness(cand, p_net, v_net, node_res_attrs, link_res_attrs)
                delta = cand_cost - new_cost
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
                        pbest[i] = cand.copy()
                        pbest_cost[i] = cand_cost
                        if cand_cost < gbest_cost:
                            gbest = cand.copy()
                            gbest_cost = cand_cost

        T *= cooling_rate

    return gbest, pbest, pbest_cost
