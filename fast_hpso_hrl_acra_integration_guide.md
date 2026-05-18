# Fast HPSO Integration Guide for `hrl-acra`
## Engineering Design Document + Implementation Handbook

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Codebase Analysis: Three-Way Comparison](#2-codebase-analysis-three-way-comparison)
3. [Solver Lifecycle in hrl-acra](#3-solver-lifecycle-in-hrl-acra)
4. [Integration Architecture Design](#4-integration-architecture-design)
5. [Reusable Solver Core](#5-reusable-solver-core)
6. [Independent Solver Mode](#6-independent-solver-mode)
7. [HRL-AC Sub-Solver Mode](#7-hrl-ac-sub-solver-mode)
8. [RL/HRL Compatibility Analysis](#8-rlhrl-compatibility-analysis)
9. [Step-by-Step Implementation Order](#9-step-by-step-implementation-order)
10. [Common Pitfalls and Debugging](#10-common-pitfalls-and-debugging)
11. [Performance and Maintainability](#11-performance-and-maintainability)

---

## 1. Architecture Overview

### 1.1 Expected Directory Structure

```
hrl-acra/
├── solver/
│   ├── solver.py                          # Base Solver class
│   ├── heuristic/
│   │   ├── __init__.py                    # Registers solvers via Register.register()
│   │   ├── node_rank.py                   # NRMRankSolver, GRCRankSolver, etc.
│   │   └── fast_hpso/                     # NEW — entire HPSO package
│   │       ├── __init__.py                # Re-exports; triggers registration
│   │       ├── core.py                    # HPSO algorithm (no framework coupling)
│   │       └── fast_hpso_solver.py        # FastHPSOSolver(NodeRankSolver) + sub-solver wrapper
│   └── learning/
│       └── hrl_ac/
│           ├── env.py                     # OnlineEnv — ADD 'fast_hpso' branch here
│           ├── hrl_ac_solver.py
│           └── __init__.py
├── base/
│   ├── loader.py                          # ADD fast_hpso to load_simulator()
│   └── register.py                        # SolverLibrary dict
└── settings/
    └── fast_hpso_setting.yaml             # NEW — hyper-parameter defaults
```

**Why a sub-package instead of a single file?** The `core.py`/`fast_hpso_solver.py` split enforces the critical constraint: zero framework imports in the algorithm layer. `core.py` depends only on `networkx`, `random`, `math`, and `copy`. This makes unit-testing and future reuse trivial, and avoids accidental coupling to `base.*` or `controller.*` inside the hot inner loop.

### 1.2 Class Inheritance Hierarchy

```
Solver                                      (solver/solver.py)
└── NodeRankSolver(Solver)                  (solver/heuristic/node_rank.py)
    ├── NRMRankSolver(NodeRankSolver)       [existing]
    ├── GRCRankSolver(NodeRankSolver)       [existing]
    └── FastHPSOSolver(NodeRankSolver)      [NEW — primary class]
```

`FastHPSOSolver` inherits `NodeRankSolver` because:
- It reuses `link_mapping()` (BFS/k-shortest path routing) from `NodeRankSolver` — the framework's battle-tested link mapper.
- It overrides only `node_mapping()` — replacing ranked greedy assignment with HPSO swarm search.
- `solve()` in `NodeRankSolver` already handles the two-stage (node mapping → link mapping) flow that HPSO requires.
- Registration, lifecycle callbacks, and the `controller`/`recorder`/`counter` dependencies are inherited.

This is the same pattern used by all existing heuristic solvers and matches the project coding style precisely.

### 1.3 Dependency Relationships

```
fast_hpso_solver.py
    depends-on → core.py               (pure algorithm, no framework)
    depends-on → NodeRankSolver        (link_mapping, solve template)
    depends-on → Controller            (place, route, node_mapping, link_mapping)
    depends-on → Solution              (result container)
    depends-on → SolutionStepEnvironment (env for independent mode)

OnlineEnv (hrl_ac/env.py)
    depends-on → FastHPSOSolver        (as sub_solver when sub_solver_name='fast_hpso')
    depends-on → Solver.solve()        (standard interface)
```

---

## 2. Codebase Analysis: Three-Way Comparison

### 2.1 `fast_hpso.py` (Standalone)

**What it is**: A pure Python algorithm operating directly on NetworkX graphs. No framework concepts.

**Key characteristics**:
- Particle = `list[int]` (physical node IDs, one per virtual node)
- Fitness = `fast_fitness()` — proxy hop-distance × BW (no resource reservation)
- Final validation = `build_and_reserve()` — real Dijkstra + `reserve_node()` / `reserve_path()` that mutate the graph in-place
- Resources tracked as raw dict attributes (`nodes[s]['cpu']`, `edges[u,v]['bw']`)
- Hard-coded attribute names: `'cpu'` and `'bw'`

**Limitation for hrl-acra**: `build_and_reserve()` directly modifies the substrate graph. In `hrl-acra`, resource management goes through `Controller` (which also tracks `solution['node_slots']`, `solution['link_paths_info']`, etc. for `Recorder` and `Counter`). You cannot call `reserve_node()` directly — the framework will lose track of resource state.

### 2.2 `virne/fast_hpso_solver.py` (Virne Integration)

**What it is**: A production-quality adaptation for the `virne` framework. Architecturally very similar to what we need for `hrl-acra`.

**Key characteristics**:
- Registered via `@SolverRegistry.register` (virne's equivalent of `Register.register`)
- Inherits `BaseMetaHeuristicSolver` (virne's base, analogous to `NodeRankSolver` here)
- Multi-resource: uses `v_net.get_node_attrs(types=['resource'])` not hard-coded `'cpu'`
- `_try_deploy_particle()` → `controller.deploy_with_node_slots(inplace=False)` — dry-run validation
- `meta_run()` implements the main loop; base class `solve()` handles lifecycle
- `solve_batch()` adds batch support for virne's `TimeWindowSystem`

**Adaptation requirement**: `virne` uses `SolverRegistry`, `Logger`, `Solution.from_v_net()`. `hrl-acra` uses `Register`, no explicit Logger, `Solution(v_net)`. The algorithmic code is identical; only integration plumbing changes.

### 2.3 `hrl-acra/node_rank.py` (Target Framework)

**What it is**: The canonical heuristic solver pattern in `hrl-acra`.

**Key characteristics**:
- `NodeRankSolver.solve(instance)` is the top-level entrypoint; returns a `Solution` object
- `instance = {'v_net': v_net, 'p_net': p_net}` — passed from `BasicScenario.run()`
- `node_mapping(v_net, p_net, solution)` calls `controller.node_mapping(sorted_v_nodes, sorted_p_nodes, ...)`
- `link_mapping(v_net, p_net, solution)` calls `controller.link_mapping(...)`
- Solvers set `self.node_rank` (a callable that ranks nodes) and `self.link_rank`
- Registration in `__init__.py`: `Register.register('nrm_rank', {'solver': NRMRankSolver, 'env': SolutionStepEnvironment})`

### 2.4 Concept Mapping Table

| Concept | standalone | virne | hrl-acra |
|---|---|---|---|
| Solver registration | none (direct call) | `@SolverRegistry.register` | `Register.register(name, {'solver': Cls, 'env': Env})` |
| Solve entry point | `hpso_embed(sub, vnr)` | `BaseMetaHeuristicSolver.solve(instance)` | `NodeRankSolver.solve(instance)` |
| Node mapping | `init_particles_hpso` + `hpso_embed` | `meta_run(v_net, p_net)` | `node_mapping(v_net, p_net, solution)` |
| Link mapping | `build_and_reserve` (inline) | `controller.deploy_with_node_slots` | `controller.link_mapping(...)` |
| Resource reservation | `reserve_node/path` (direct) | `controller.deploy_with_node_slots(inplace=False)` then `deploy()` | `controller.node_mapping + link_mapping (inplace=True)` |
| Resource attributes | hard-coded `'cpu'/'bw'` | `get_node_attrs(types=['resource'])` | `self.node_resource_attrs` from controller |
| Solution container | `(mapping, link_paths)` tuple | `Solution.from_v_net(v_net)` | `Solution(v_net)` |
| Failure handling | `return None` | `solution['result'] = False` | `solution['result'] = False` + `rollback_for_failure` |
| Sub-solver usage | N/A | N/A | `OnlineEnv.sub_solver.solve(instance)` |

---

## 3. Solver Lifecycle in hrl-acra

Understanding the exact call chain is essential before writing any code.

### 3.1 Independent Solver Lifecycle

```
main.py: run(config)
  → load_simulator('fast_hpso') → (SolutionStepEnvironment, FastHPSOSolver)
  → BasicScenario.from_config(Env, Solver, config)
      → Counter, Controller, Recorder created from config
      → p_net loaded; v_net_simulator created
      → env = SolutionStepEnvironment(p_net, v_net_sim, controller, recorder, counter, **config)
      → solver = FastHPSOSolver(controller, recorder, counter, **config)
  → scenario.run()
      → env.reset() → instance = {'v_net': v_net, 'p_net': p_net}
      → loop:
          solution = solver.solve(instance)
          next_instance, reward, done, info = env.step(solution)
          if done: break
      → env.summary_records()
```

**Key insight**: `solver.solve(instance)` must return a `Solution` object with `solution['result']` set. The environment's `step()` (in `SolutionStepEnvironment`) then calls `controller.deploy()` to actually commit resources to `p_net`.

### 3.2 HRL-AC Sub-Solver Lifecycle

```
main.py: run(config)  [config.solver_name = 'hrl_ac']
  → load_simulator('hrl_ac') → (OnlineEnv, HrlAcSolver)
  → BasicScenario.from_config(OnlineEnv, HrlAcSolver, config)
  → scenario.run()
      → env.reset()
      → HrlAcSolver.learn(env, num_epochs=...)
          → OnlineAgent.learn():
              obs = env.reset()
              for each VNR:
                  action = policy.act(obs)      # 0=reject, 1=accept
                  next_obs, reward, done, info = env.step(action)
                    → OnlineEnv.step(action):
                        if action == 1:
                            solution = self.sub_solver.solve(instance)  # ← HERE
                        else:
                            solution = Solution(v_net); solution['early_rejection'] = True
                        return super().step(solution)   # → SolutionStepRLEnv.step(solution)
```

**Key insight for sub-solver**: `sub_solver.solve(instance)` must have exactly the same signature and return contract as in independent mode. The sub-solver is just a `Solver` object with a `solve()` method — it does not need to know it is inside HRL.

---

## 4. Integration Architecture Design

### 4.1 Two-Mode Architecture

The design uses **one class** (`FastHPSOSolver`) for both modes, with **zero mode-specific code inside the class**. The mode distinction lives entirely in:
1. How the solver is instantiated (standalone vs. as `self.sub_solver` in `OnlineEnv`)
2. Which environment calls `solve()`

```
┌─────────────────────────────────────────────────────────────────┐
│                      fast_hpso/core.py                          │
│  (pure algorithm — no hrl-acra imports)                         │
│  fast_fitness(), init_swarm(), op_minus/plus/multiply(),        │
│  sa_neighbor(), hpso_main_loop() → best_particle: list[int]     │
└─────────────────────────┬───────────────────────────────────────┘
                          │  particle: list[int]
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│               fast_hpso/fast_hpso_solver.py                     │
│  FastHPSOSolver(NodeRankSolver)                                  │
│                                                                  │
│  node_mapping(v_net, p_net, solution):                          │
│    particle = hpso_main_loop(v_net, p_net, self.hpso_config)   │
│    if particle is None: return False                            │
│    node_slots = particle_to_node_slots(particle, v_net)        │
│    return controller.node_mapping(sorted_v, sorted_p, solution) │
│                                                                  │
│  solve(instance):   [inherited from NodeRankSolver]             │
│    node_mapping(...) → link_mapping(...) → return solution      │
└─────────────────────┬──────────────────────┬────────────────────┘
                      │                      │
         Mode 1: Independent          Mode 2: Sub-Solver
                      │                      │
         SolutionStepEnvironment      OnlineEnv.sub_solver
         BasicScenario.run()          HrlAcSolver.learn()
```

### 4.2 Why `NodeRankSolver` Is the Right Parent

The HPSO algorithm replaces *node ranking* (how to order physical nodes for greedy assignment) with *swarm search* (PSO finds the optimal node assignment directly). But link mapping is unchanged — both HPSO and NRM use BFS/k-shortest path routing. Therefore:

- **Override** `node_mapping()` — replace greedy rank-based assignment with HPSO particle evaluation
- **Inherit** `link_mapping()` — unchanged, uses `controller.link_mapping()`
- **Inherit** `solve()` — the two-stage template is correct for HPSO

This mirrors how `GRCRankSolver` differs from `NRMRankSolver` only in which `node_rank` callable is used, except HPSO's `node_mapping()` override is more substantial since it doesn't use `self.node_rank` at all.

---

## 5. Reusable Solver Core

### 5.1 `solver/heuristic/fast_hpso/core.py`

This file contains **only** the HPSO algorithm. No `hrl-acra` framework imports. Based directly on `fast_hpso.py` with the multi-resource generalization from `virne/fast_hpso_solver.py`.

```python
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
```

**Why this design**: `hpso_main_loop` returns raw particle data, not a `Solution`. The framework wrapper decides how to validate and commit the result. This makes `core.py` entirely testable without any framework setup.

---

## 6. Independent Solver Mode

### 6.1 `solver/heuristic/fast_hpso/fast_hpso_solver.py`

```python
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
                inplace=True,
                matching_mathod='l2s2',   # l2s2: strict positional matching
            )
            if result:
                return True

        solution['place_result'] = False
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # link_mapping() and solve() are fully inherited from NodeRankSolver
    # ─────────────────────────────────────────────────────────────────────────
```

### 6.2 `solver/heuristic/fast_hpso/__init__.py`

```python
# solver/heuristic/fast_hpso/__init__.py
from .fast_hpso_solver import FastHPSOSolver

from base.environment import SolutionStepEnvironment
from base.register import Register

Register.register('fast_hpso', {
    'solver': FastHPSOSolver,
    'env': SolutionStepEnvironment,
})

__all__ = ['FastHPSOSolver']
```

### 6.3 Update `solver/heuristic/__init__.py`

```python
# solver/heuristic/__init__.py  (ADD these lines)
from .fast_hpso import FastHPSOSolver
# ... existing imports ...

__all__ = [
    NodeRankSolver,
    GRCRankSolver,
    OrderRankSolver,
    NRMRankSolver,
    FastHPSOSolver,    # ADD
]
```

### 6.4 Update `base/loader.py`

```python
# base/loader.py  — ADD fast_hpso branch
def load_simulator(solver_name):
    if solver_name == 'fast_hpso':
        from solver.heuristic.fast_hpso import FastHPSOSolver
        Env, Solver = SolutionStepEnvironment, FastHPSOSolver
    elif solver_name == 'grc_rank':
        # ... existing ...
    # ...
    return Env, Solver
```

### 6.5 Usage

```bash
python main.py --solver_name fast_hpso --num_particles 20 --max_iteration 30
```

---

## 7. HRL-AC Sub-Solver Mode

### 7.1 Update `solver/learning/hrl_ac/env.py`

The only change needed is adding one `elif` branch to `OnlineEnv.__init__()`. The rest of `OnlineEnv` is untouched.

```python
# solver/learning/hrl_ac/env.py  — EXISTING __init__, ADD branch

def __init__(self, p_net, v_net_simulator, controller, recorder, counter,
             verbose=False, allow_rejection=False, **kwargs):
    # ... existing init code ...
    sub_solver_name = kwargs.get('sub_solver_name', 'nrm_rank')
    kwargs_for_sub_solver = copy.deepcopy(kwargs)
    kwargs_for_sub_solver['verbose'] = 0

    print(f'Employ {sub_solver_name} as sub solver')

    if sub_solver_name == 'nrm_rank':
        self.sub_solver = NRMRankSolver(self.controller, self.recorder, self.counter,
                                        **kwargs_for_sub_solver)
    elif sub_solver_name == 'grc_rank':
        self.sub_solver = GRCRankSolver(self.controller, self.recorder, self.counter,
                                        **kwargs_for_sub_solver)
    elif sub_solver_name == 'hrl_ra':
        # ... existing hrl_ra code ...
        pass
    elif sub_solver_name == 'fast_hpso':                      # ← ADD THIS BLOCK
        from solver.heuristic.fast_hpso import FastHPSOSolver
        self.sub_solver = FastHPSOSolver(
            self.controller, self.recorder, self.counter,
            **kwargs_for_sub_solver
        )
    else:
        raise NotImplementedError(
            f'Please specify an available sub solver: not {sub_solver_name}!'
        )
```

**That is the entire HRL integration**. No other changes needed. When the upper HRL-AC agent outputs action=1 (accept), `OnlineEnv.step()` calls `self.sub_solver.solve(instance)`, which runs HPSO and returns a `Solution`. The existing `SolutionStepRLEnv.step(solution)` handles deployment, recording, and reward computation.

### 7.2 Usage

```bash
python main.py --solver_name hrl_ac --sub_solver_name fast_hpso \
    --num_particles 20 --max_iteration 30
```

### 7.3 Interaction Protocol Between HRL-AC and fast_hpso

```
HRL-AC upper agent:
  obs = OnlineEnv.get_observation()    → graph embeddings of p_net + v_net
  action = policy.act(obs)             → Categorical(2): 0=reject, 1=accept

OnlineEnv.step(action=1):
  instance = {'v_net': self.v_net, 'p_net': self.p_net}
  solution = self.sub_solver.solve(instance)
      → FastHPSOSolver.solve(instance)
          → node_mapping(v_net, p_net, solution)
              → hpso_main_loop(p_net, v_net, ...) → gbest particle
              → controller.node_mapping(sorted_v, sorted_p, solution, inplace=True)
                  → modifies p_net (subtracts node resources)
                  → populates solution['node_slots']
          → link_mapping(v_net, p_net, solution)
              → controller.link_mapping(v_net, p_net, solution, shortest_method=...)
                  → modifies p_net (subtracts link resources)
                  → populates solution['link_paths']
          → solution['result'] = True / False
          → return solution
  ↓
  super().step(solution)              → SolutionStepRLEnv.step(solution)
      if solution['result']:
          controller.deploy(v_net, p_net, solution)   # NOTE: see §7.4
      else:
          rollback_for_failure()      → p_net = deepcopy(p_net_backup)
      reward = compute_reward(solution)
      buffer.add(obs, action, reward, ...)
```

### 7.4 Critical: Resource Management Double-Update Risk

**Problem**: `FastHPSOSolver.solve()` calls `controller.node_mapping(..., inplace=True)` and `controller.link_mapping(..., inplace=True)`, which **immediately subtracts resources from `p_net`**. Then `SolutionStepRLEnv.step()` calls `controller.deploy(v_net, p_net, solution)` on success, which **subtracts resources again**.

**Solution**: Do NOT use `inplace=True` in the sub-solver context, OR ensure `controller.deploy()` is not called again.

Looking at `SolutionStepEnvironment.step()` more carefully:

```python
# base/environment.py: SolutionStepEnvironment.step(solution)
if solution['result']:
    self.controller.deploy(self.v_net, self.p_net, self.solution)
```

And `controller.deploy()`:
```python
# base/controller.py: deploy()
def deploy(self, v_net, p_net, solution):
    if not solution['result']: return False
    for (v_node_id, p_node_id), used in solution['node_slots_info'].items():
        self.update_node_resources(p_net, p_node_id, used, operator='-')
    for (v_link, p_link), used in solution['link_paths_info'].items():
        self.update_link_resources(p_net, p_link, used, operator='-')
```

**This means**: If `solve()` already modified `p_net` in-place (via `inplace=True`), and then `deploy()` is called again, resources are double-subtracted. **This is a critical bug.**

**Two correct approaches**:

**Approach A (Recommended)**: Use `inplace=False` in `node_mapping` so `solve()` does a dry-run and returns a valid `solution`, but `p_net` is unmodified. Let `deploy()` do the actual resource commitment.

```python
# In FastHPSOSolver.node_mapping():
result = self.controller.node_mapping(
    v_net, p_net,
    sorted_v_nodes=sorted_v_nodes,
    sorted_p_nodes=sorted_p_nodes,
    solution=solution,
    reusable=False,
    inplace=False,         # ← DRY RUN: validates on a copy, doesn't modify p_net
    matching_mathod='l2s2',
)
```

```python
# In FastHPSOSolver.link_mapping() override:
def link_mapping(self, v_net, p_net, solution):
    if self.link_rank is None:
        sorted_v_links = list(v_net.links)
    else:
        # ... same as NodeRankSolver ...
    return self.controller.link_mapping(
        v_net, p_net, solution=solution,
        sorted_v_links=sorted_v_links,
        shortest_method=self.shortest_method,
        k=self.k_shortest,
        inplace=False,        # ← DRY RUN
    )
```

With `inplace=False` throughout `solve()`, the returned `solution` is fully populated with valid `node_slots` and `link_paths`, but `p_net` is unchanged. `SolutionStepEnvironment.step()` then calls `deploy()` once, which commits correctly.

**Approach B**: Override `solve()` entirely so it does not call `deploy()`. This is more invasive and loses the NodeRankSolver template benefit.

**Recommendation: Use Approach A.** Set `inplace=False` in both `node_mapping` and `link_mapping` inside `FastHPSOSolver`.

> **Note on `inplace=False` for node_mapping in controller**: Looking at `controller.node_mapping()`, the `inplace` parameter controls whether `p_net = p_net if inplace else copy.deepcopy(p_net)`. With `inplace=False`, the controller modifies an internal copy that is discarded. But `solution['node_slots']` IS still populated — the solution dict is passed by reference and mutated regardless of `inplace`. So `inplace=False` gives us a validated `solution` without touching the real `p_net`. Same for `link_mapping`.

---

## 8. RL/HRL Compatibility Analysis

### 8.1 Deterministic vs. Stochastic Behavior

HPSO uses `random.random()` and `random.choice()` throughout. This has implications for HRL:

**Impact on HRL-AC training**: The upper agent (PPO) acts on state `obs_t` and receives reward `r_t`. The reward depends on whether the sub-solver succeeds. With a stochastic sub-solver, two identical observations at the same `p_net` state may yield different rewards:

- Iteration A: HPSO succeeds → `reward = (w_a + w_b) * revenue * r2c`
- Iteration B: HPSO fails → `reward = -0.01 * N`

This **increases reward variance** for the upper agent. PPO handles variance through advantage normalization (`norm_advantage=True`), but high variance can destabilize training, especially early when acceptance rates are low.

**Mitigation strategies**:
1. **Seed the HPSO**: `random.seed(seed + v_net_id)` inside `solve()` — makes HPSO deterministic per VNR. Reduces variance but limits diversity across training epochs.
2. **Increase `num_particles` and `max_iteration`**: More thorough search → higher acceptance rate → less variance in reward sign.
3. **Use HPSO only for evaluation**: During PPO training, use `NRMRankSolver` (deterministic, fast) as sub-solver. After training, switch to `FastHPSOSolver` for evaluation. This decouples sub-solver stochasticity from PPO gradient updates.
4. **Accept the variance**: With `norm_reward=True` and sufficient `batch_size`, PPO is robust to moderate variance. Empirically test first.

### 8.2 Implications for PPO Exploration

The HRL-AC agent learns to predict **which VNRs are worth accepting** based on graph features. With HPSO as sub-solver:

- HPSO is more powerful than NRM → higher embedding success rate → upper agent sees less rejection penalty → reward signal shifts upward
- Upper agent may become over-permissive (accept everything) if HPSO rarely fails
- This can hurt long-term performance: accepting marginal VNRs fragments the substrate

**Recommendation**: The reward function in `OnlineEnv.compute_reward()` already accounts for this via `v_net_r2c_ratio`. If HPSO succeeds on a VNR with poor r2c ratio, the upper agent still gets a lower reward. No changes needed to the reward function.

### 8.3 Early Rejection Interactions

When the upper agent outputs action=0 (reject), `sub_solver.solve()` is **never called**. HPSO has no influence on rejection decisions. The early rejection path is:

```python
# OnlineEnv.step(action=0):
solution = Solution(self.v_net)
solution['early_rejection'] = True
# reward = 0 (from compute_reward)
```

HPSO's determinism/stochasticity does not affect rejection rewards at all.

### 8.4 Episode Transition Consistency

`SolutionStepRLEnv.step()` calls `transit_obs()` after each VNR decision (success or failure). `transit_obs()` processes all leave events and advances to the next arrive event. This is identical regardless of sub-solver. HPSO does not interact with the event loop.

**One subtle issue**: If HPSO modifies `p_net` during `solve()` (via `inplace=True`) and then the embedding fails (returns `solution['result']=False`), the `rollback_for_failure()` call restores `p_net = deepcopy(p_net_backup)`. This discards any HPSO-induced partial state correctly. As long as Approach A (inplace=False) is used, this scenario cannot occur.

### 8.5 Reward Propagation

```
Upper agent (HRL-AC) reward chain:
  env.step(action) → sub_solver.solve() → solution
  → compute_reward(solution) in OnlineEnv
  → reward stored in buffer
  → GAE returns computed over entire simulation episode
  → PPO update

HPSO influences reward only via solution['result'] and solution['v_net_r2c_ratio'].
No reward flows back INTO the HPSO solver itself — HPSO has no parameters to update.
```

This is the key architectural cleanness of the design: HPSO is a deterministic (or stochastic) black-box that the PPO agent conditions on. PPO learns admission control; HPSO provides embedding quality. They do not share gradients.

---

## 9. Step-by-Step Implementation Order

### Step 1: Create the core module (no framework dependencies)

Create `solver/heuristic/fast_hpso/core.py` with content from §5.1.

**Test independently** without any hrl-acra setup:
```python
# test_core.py
import networkx as nx
from solver.heuristic.fast_hpso.core import hpso_main_loop

G_sub = nx.waxman_graph(50, alpha=0.5, beta=0.2)
for n in G_sub.nodes(): G_sub.nodes[n]['cpu'] = 80
for e in G_sub.edges(): G_sub.edges[e]['bw'] = 80

G_vnr = nx.gnm_random_graph(4, 4)
for n in G_vnr.nodes(): G_vnr.nodes[n]['cpu'] = 20
for e in G_vnr.edges(): G_vnr.edges[e]['bw'] = 10

gbest, pbest, costs = hpso_main_loop(G_sub, G_vnr, ['cpu'], ['bw'])
print(f'gbest: {gbest}, cost: {costs[0] if costs else None}')
```

**Why first**: If the core algorithm has bugs, you want to know before wrapping it in framework plumbing.

### Step 2: Implement `FastHPSOSolver` skeleton

Create `solver/heuristic/fast_hpso/fast_hpso_solver.py` with `node_mapping()` from §6.1 using `inplace=False` (Approach A from §7.4).

Add the `__init__.py` and Register call.

### Step 3: Integrate into `loader.py` and `solver/heuristic/__init__.py`

Add the `fast_hpso` branch to `load_simulator()` and export `FastHPSOSolver`.

### Step 4: Test in independent solver mode

```bash
python main.py --solver_name fast_hpso --num_v_nets 100 --num_particles 10 --max_iteration 10
```

Verify:
- Acceptance rate comparable to `nrm_rank` baseline
- No resource double-deduction (check `p_net_available_resource` in records)
- `solution['result']` consistency with `solution['node_slots']` / `solution['link_paths']`

### Step 5: Add the HRL-AC sub-solver branch

Edit `solver/learning/hrl_ac/env.py` as per §7.1.

### Step 6: Test in HRL-AC sub-solver mode

```bash
python main.py --solver_name hrl_ac --sub_solver_name fast_hpso \
    --num_particles 10 --max_iteration 10 --num_train_epochs 5
```

Verify:
- No crash on `OnlineEnv.__init__()`
- `sub_solver.solve(instance)` returns valid Solution
- `compute_reward()` correctly uses `solution['result']` and `solution['v_net_r2c_ratio']`

### Step 7: Validate reward and resource accounting

Run a short simulation and compare `total_revenue / total_cost` between:
- `solver_name=nrm_rank` (baseline)
- `solver_name=fast_hpso` (should be ≥ nrm_rank if HPSO is working)
- `solver_name=hrl_ac sub_solver_name=fast_hpso` (should be ≥ both after training)

### Step 8: Add `settings/fast_hpso_setting.yaml`

```yaml
# settings/fast_hpso_setting.yaml
num_particles: 20
max_iteration: 30
w_max: 0.9
w_min: 0.5
beta: 0.3
gamma: 0.3
T0: 100.0
cooling_rate: 0.95
shortest_method: 'k_shortest'
k_shortest: 10
```

---

## 10. Common Pitfalls and Debugging

### Pitfall 1: Resource Double-Deduction

**Symptom**: `p_net_available_resource` drops faster than expected; acceptance rate starts high then collapses as substrate runs out.

**Cause**: `inplace=True` in `solve()` + `controller.deploy()` in `env.step()`.

**Fix**: Enforce `inplace=False` in `FastHPSOSolver.node_mapping()` and `link_mapping()` as described in §7.4.

**Debug command**:
```python
# After each solve(), assert p_net resources unchanged:
import copy
p_net_before = copy.deepcopy(p_net)
solution = solver.solve(instance)
# Check node resources
for n in p_net.nodes():
    for attr in ['cpu']:
        assert p_net.nodes[n][attr] == p_net_before.nodes[n][attr], \
            f"solve() modified p_net at node {n}!"
```

### Pitfall 2: Particle Index vs. Node ID Confusion

**Symptom**: Wrong virtual nodes mapped to wrong physical nodes; constraint violations that shouldn't exist.

**Cause**: `particle[i]` corresponds to `list(v_net.nodes())[i]`, NOT to v_node ID `i`. If v_net has nodes `[2, 5, 7]`, then `particle[0]` is the assignment for v_node `2`, not v_node `0`.

**Fix**: Always resolve: `vnodes = list(v_net.nodes()); v = vnodes[i]`.

**Debug**: Add assertion at the start of `node_mapping()`:
```python
assert len(particle) == len(list(v_net.nodes())), "Particle length mismatch"
```

### Pitfall 3: `solution['node_slots']` Not Reset Between Fallback Attempts

**Symptom**: Second fallback particle attempt inherits partial state from first failed attempt.

**Cause**: `controller.node_mapping()` appends to `solution['node_slots']` rather than replacing it.

**Fix**: Explicitly reset before each attempt:
```python
for particle in candidates:
    solution['node_slots'] = {}
    solution['node_slots_info'] = {}
    result = self.controller.node_mapping(...)
    if result: return True
```

### Pitfall 4: `Register.register()` Called Before Class Definition

**Symptom**: `KeyError: 'fast_hpso'` in `load_simulator()` even after adding the branch.

**Cause**: The `__init__.py` that calls `Register.register()` was not imported before `load_simulator()` is called.

**Fix**: Ensure `from solver.heuristic.fast_hpso import FastHPSOSolver` appears in `solver/heuristic/__init__.py` AND that `solver/heuristic/__init__.py` is imported somewhere in the startup chain (it is, via `base/loader.py`'s existing `from solver.heuristic.node_rank import *`). Add `import solver.heuristic.fast_hpso` if needed.

### Pitfall 5: HPSO Returns `None` Swarm for Small Substrates

**Symptom**: All VNRs rejected; `solution['place_result'] = False` always.

**Cause**: `init_swarm()` returns empty list when no physical node satisfies v_node constraints (fully fragmented substrate).

**Fix**: This is correct behavior — the substrate genuinely cannot embed the VNR. Verify by checking `p_net_available_resource` in records. If substrate is fresh and HPSO still fails, check attribute name resolution: are `self._node_res_attrs` correctly resolved from `self.controller.node_resource_attrs`?

**Debug**:
```python
print(f'node_res_attrs: {self._node_res_attrs}')
print(f'p_net cpu sample: {p_net.nodes[0].get("cpu", "MISSING")}')
print(f'v_net cpu sample: {v_net.nodes[list(v_net.nodes())[0]].get("cpu", "MISSING")}')
```

### Pitfall 6: `matching_mathod='l2s2'` Fails When Sorted Lists Mismatch

**Symptom**: `node_mapping()` returns False even when particle looks feasible.

**Cause**: `controller.node_mapping()` with `matching_mathod='l2s2'` enforces strict positional pairing: `sorted_v_nodes[i]` must map to `sorted_p_nodes[i]`. If `particle[i]` does not satisfy constraints for `sorted_v_nodes[i]`, the whole mapping fails.

**Why this matters**: The proxy fitness may accept a particle where some physical node satisfies the resource check in `fast_fitness()` but the controller's `check_node_constraints()` uses a slightly different calculation (e.g., considers all node attributes including non-resource ones).

**Fix**: Validate particles in `node_mapping()` before passing to controller:
```python
for i, v in enumerate(sorted_v_nodes):
    ok, _ = self.controller.check_node_constraints(v_net, p_net, v, sorted_p_nodes[i])
    if not ok:
        continue  # skip this particle
```

Or rely on the fallback loop: the controller will return False and we move to the next pbest candidate.

---

## 11. Performance and Maintainability

### 11.1 Performance Bottlenecks

1. **`fast_fitness` inner loop**: `nx.shortest_path_length()` is called for every virtual link per particle per iteration. For a swarm of 20 particles, 30 iterations, 5 virtual links: 3,000 BFS calls per VNR. Pre-compute the BFS distance matrix once per call to `node_mapping()`:

```python
# In node_mapping(), before hpso_main_loop():
# Pre-compute all-pairs shortest path lengths (or APSP subset for used p_nodes)
# Pass as lookup table to fast_fitness via closure or extra argument
import numpy as np
pnodes = list(p_net.nodes())
dist_matrix = dict(nx.all_pairs_shortest_path_length(p_net))
# Pass to core.py as optional argument; fast_fitness uses it if available
```

2. **`op_multiply` candidate filtering**: O(|S|) per virtual node per particle. Pre-compute feasible p_nodes per v_node once before the main loop:
```python
feasible_per_vnode = {
    v: [s for s in p_net.nodes() if all(p_net.nodes[s].get(a,0) >= v_net.nodes[v].get(a,0) for a in node_res_attrs)]
    for v in v_net.nodes()
}
```

3. **`copy.deepcopy(swarm)`** for pbest: use `[p.copy() for p in swarm]` since particles are flat lists.

### 11.2 Maintainability Recommendations

- **Keep `core.py` free of framework imports**: this is the most important maintainability rule. If someone later wants to port the algorithm to another framework, they only need `core.py`.
- **Use `**kwargs` forwarding**: all HPSO hyper-parameters flow through `**kwargs` from the config system. No hard-coded magic numbers outside of default values in `__init__`.
- **Document the two-mode semantics in the class docstring**: future contributors must understand that `FastHPSOSolver` is intentionally framework-agnostic with respect to its operating mode.
- **Add a `validate_config()` method**: check that `num_particles >= 1`, `max_iteration >= 1`, etc. at construction time rather than failing silently inside the algorithm.

### 11.3 Future Extensibility

| Extension | Where to add | Notes |
|---|---|---|
| Multi-resource fitness | `core.py:fast_fitness` | Already multi-resource via `node_res_attrs` list |
| BW-aware proxy fitness | `core.py:fast_fitness` | Replace `hops * demand` with `hops * demand / min_bw_on_path` |
| Parallel particle evaluation | `core.py:hpso_main_loop` | `fast_fitness` is stateless; use `ThreadPoolExecutor` |
| Adaptive cooling | `core.py:hpso_main_loop` | Track SA acceptance ratio; adjust `T` dynamically |
| HPSO as HRL-RA lower agent | New `SubRLEnv` variant | Would require wrapping HPSO in `JointPRStepSubRLEnv` interface — substantial work |
| Elitism | `core.py:hpso_main_loop` | Preserve top-k particles unchanged across iterations |
| Population restart | `core.py:hpso_main_loop` | Detect convergence (all pbest_cost within ε) → re-init fraction of swarm |

---

## Appendix: Complete File Checklist

| File | Action |
|---|---|
| `solver/heuristic/fast_hpso/__init__.py` | CREATE — exports + Register.register() |
| `solver/heuristic/fast_hpso/core.py` | CREATE — pure HPSO algorithm |
| `solver/heuristic/fast_hpso/fast_hpso_solver.py` | CREATE — FastHPSOSolver class |
| `solver/heuristic/__init__.py` | MODIFY — add FastHPSOSolver import and export |
| `base/loader.py` | MODIFY — add 'fast_hpso' branch to load_simulator() |
| `solver/learning/hrl_ac/env.py` | MODIFY — add 'fast_hpso' branch in OnlineEnv.__init__() |
| `settings/fast_hpso_setting.yaml` | CREATE — default hyper-parameters |

Total files modified: 3. Total files created: 4. The existing `OnlineEnv`, `HrlAcSolver`, `BasicScenario`, `SolutionStepEnvironment`, `Controller`, `Recorder`, `Counter`, and `Solution` classes require **zero changes**.
