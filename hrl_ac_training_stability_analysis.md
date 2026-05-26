# HRL-AC Training Stability Analysis & Fix Guide

## 1. Current Situation

### 1.1 Training Metrics Summary

| Epoch | Success Count | Acceptance Rate | R2C Ratio | Cumulative Reward | Runtime |
|:-----:|:-------------:|:---------------:|:---------:|:-----------------:|:-------:|
| 0 | 29 | 2.9% | 0.6253 | 103.34 | 77.72s |
| 1 | 37 | 3.7% | 0.6603 | 186.32 | 81.01s |
| 2 | 528 | 52.8% | 0.7391 | 3312.00 | 370.10s |
| 3 | **814** | **81.4%** | 0.7309 | **5190.52** | 528.34s |
| 4 | 673 | 67.3% | 0.6933 | 3930.87 | 442.89s |
| 5 | 760 | 76.0% | 0.7369 | 4905.02 | 493.04s |
| 6 | 734 | 73.4% | 0.7049 | 4437.52 | 525.08s |
| 7 | 769 | ~77% | 0.7200 | N/A | ~531s |

### 1.2 Observed Pattern: Instability Signature

The training exhibits a **sharp jump + oscillation** pattern rather than smooth progressive improvement:

```
Acceptance Rate
90% |          * (epoch 3)
80% |        * * * * (epoch 5-7)
70% |      *
60% |    *                      ← big jump at epoch 2-3
10% | * *                       ← near-zero for epochs 0-1
 0% |__________________________ Epochs
     0  1  2  3  4  5  6  7
```

This is a **policy collapse / sudden discovery** pattern, not gradual learning. Epochs 0–1 are almost purely rejecting VNRs (968/1000 early rejections at epoch 0), then the agent suddenly learns to accept. After that, acceptance oscillates between 67–81%.

---

## 2. Root Cause Analysis

### 2.1 Primary Cause: `gamma = 1.0` (Now Fixed → 0.99)

**The original bug:** `self.gamma = 1.0` in `HrlAcSolver.__init__` overrides the PPOSolver default **after** the parent `__init__` sets it from config (`rl_gamma=0.99`). With `gamma=1.0`:

- Returns are **undiscounted sums** over the entire episode
- For VNE, an episode can span many timesteps (one per VNR across the lifetime simulation)
- Undiscounted returns blow up in magnitude and variance, making the critic's value baseline wildly inaccurate
- The actor loss receives near-random gradient signal in early training, causing the near-zero acceptance seen in epochs 0–1

**Your fix:** Setting `self.gamma = 0.99` is correct. This is a necessary fix, but not sufficient alone to guarantee stable training.

### 2.2 Secondary Cause: SolutionStep Environment — Binary, Sparse Reward

The `SolutionStepRLEnv` + `OnlineEnv.step()` produces **one reward per entire VNR** (accept/reject decision). The upper-level agent makes a single binary decision, and `fast_hpso` sub-solver executes the full placement. This means:

- No intermediate feedback during VNR processing
- The reward formula in `compute_reward` mixes several signals:

```python
# From hrl_ac/env.py
w_b = solution['v_net_lifetime'] / scale   # lifetime-dependent weight
reward = weight * basic_reward * r2c_ratio  # if success
reward = -weight * wasted_demand * 0.5     # if failure (not early rejection)
reward = 0.0                                # if early rejection
```

The **failure penalty** (`-weight * wasted_demand`) can be large and variable. Early in training, the agent receives large negative rewards for attempting placement and failing (the sub-solver `fast_hpso` is stochastic/heuristic and may fail), which drives the agent toward the safe `early_rejection` (reward = 0) strategy. This explains epochs 0–1 (968 early rejections).

### 2.3 Tertiary Cause: Reward Scale Variance

The reward magnitude depends on `v_net_lifetime`, which is exponentially distributed (`scale=1000`). This means:
- Short-lifetime VNRs: small positive reward on success
- Long-lifetime VNRs: large positive reward on success

And similarly for the failure penalty. This creates **high reward variance** across the batch, making `norm_advantage` less effective because the raw returns themselves are inconsistent.

### 2.4 Compounding Issue: PPO Clipping Under High Variance

With high return variance, old and new policies diverge rapidly between updates. PPO's `eps_clip=0.2` is intended to prevent this, but when the policy is in a poor region (e.g., always rejecting), the ratio `exp(logprob_new - logprob_old)` can be extreme, causing the clipping to dominate and slow escape from bad policies. This explains the stuck behavior in epochs 0–1.

---

## 3. Fix Recommendations

### Fix 1: Confirmed — `gamma = 0.99` ✅

Already applied. This is the most impactful single fix.

**In `solver/learning/hrl_ac/hrl_ac_solver.py`:**
```python
self.gamma = 0.99   # was 1.0 — now correct
```

---

### Fix 2: Reward Clipping / Normalization

The reward scale is uncontrolled. Add explicit reward clipping inside `compute_reward` to bound the signal:

**In `solver/learning/hrl_ac/env.py`:**
```python
def compute_reward(self, solution):
    revenue_benchmark = 100.0
    w_a = 1.0
    w_b = solution['v_net_lifetime'] / self.v_net_simulator.v_sim_setting['lifetime']['scale']
    weight = w_a + w_b

    if solution['result']:
        basic_reward = solution['v_net_revenue'] / revenue_benchmark
        reward = weight * basic_reward * solution['v_net_r2c_ratio']
    elif (not solution['result']) and (not solution['early_rejection']):
        wasted_demand = self.v_net.total_resource_demand / revenue_benchmark
        reward = -weight * wasted_demand * 0.5
    else:
        reward = 0.0

    # ✅ ADD: Clip reward to a bounded range to reduce variance
    reward = max(min(reward, 5.0), -5.0)

    # ... rest of function unchanged
```

This prevents extreme rewards from dominating the batch statistics and destabilizing the value function.

---

### Fix 3: Reduce Failure Penalty for Early Training

The failure penalty (`-weight * wasted_demand * 0.5`) punishes the agent for trying. This encourages the rejection-safe policy in epochs 0–1. Reduce the penalty coefficient:

```python
# Current (too aggressive early in training):
reward = -weight * wasted_demand * 0.5

# Recommended: scale down the penalty
reward = -weight * wasted_demand * 0.1   # or 0.2
```

Alternatively, use a **penalty annealing schedule** that starts small and grows as training progresses:

```python
# In hrl_ac_solver.py:
penalty_coef = min(0.5, 0.05 + self.time_step / 50000)   # ramps from 0.05 → 0.5

# Then pass penalty_coef into env and use it in compute_reward
reward = -weight * wasted_demand * penalty_coef
```

---

### Fix 4: Lower Learning Rate, Especially for Critic

The current `lr_actor = lr_critic = 1e-3`. Note that in `HrlAcSolver.__init__`, the optimizer is already divided by 10:

```python
self.optimizer = torch.optim.Adam([
    {'params': self.policy.actor.parameters(), 'lr': self.lr_actor / 10},   # = 1e-4
    {'params': self.policy.critic.parameters(), 'lr': self.lr_critic / 10}, # = 1e-4
])
```

So effective lr = 1e-4. This is reasonable, but if instability persists, try:

```bash
# Command line: reduce lr further
python main.py \
  --solver_name="hrl_ac" \
  --sub_solver_name="fast_hpso" \
  --lr_actor=3e-4 \      # effective: 3e-5
  --lr_critic=3e-4 \     # effective: 3e-5
  --seed=21 \
  ...
```

---

### Fix 5: Reduce `eps_clip` for More Conservative Policy Updates

With `eps_clip=0.2`, PPO allows up to ±20% ratio change per update. Early in training with noisy gradients, this can overshoot. Reduce to `0.1` for the first phase of training:

```python
# In hrl_ac_solver.py __init__:
self.eps_clip = 0.1   # more conservative (default from config: 0.2)
```

Or pass via command line: `--eps_clip=0.1`

---

### Fix 6: Increase `coef_entropy_loss` to Maintain Exploration

The current `coef_entropy_loss=0.05` (set in `HrlAcSolver.__init__`, overriding the config's 0.01) encourages exploration. This is good — do not reduce it. If the agent oscillates between acceptance modes, consider **increasing** it slightly:

```python
self.coef_entropy_loss = 0.08   # encourage more exploration to escape local optima
```

---

### Fix 7: Normalize Reward by Lifetime Before Computing Returns

Instead of clipping, normalize the reward by the VNR lifetime to remove the systematic scale dependency:

```python
def compute_reward(self, solution):
    revenue_benchmark = 100.0
    lifetime_scale = self.v_net_simulator.v_sim_setting['lifetime']['scale']
    
    # Remove lifetime-dependent weight (it adds variance without improving signal quality)
    if solution['result']:
        basic_reward = solution['v_net_revenue'] / revenue_benchmark
        reward = basic_reward * solution['v_net_r2c_ratio']    # no lifetime weight
    elif (not solution['result']) and (not solution['early_rejection']):
        wasted_demand = self.v_net.total_resource_demand / revenue_benchmark
        reward = -wasted_demand * 0.1
    else:
        reward = 0.0
    
    # ... rest unchanged
```

This trades off some reward signal richness for significantly lower variance.

---

## 4. Recommended Training Command (After Fixes)

```bash
python main.py \
  --solver_name="hrl_ac" \
  --sub_solver_name="fast_hpso" \
  --save_interval=1 \
  --eval_interval=10 \
  --num_train_epochs=500 \
  --summary_file_name="stable_v2_exp-wx_100a-hrl_ac-fast_hpso.csv" \
  --seed=21 \
  --eps_clip=0.1 \
  --lr_actor=3e-4 \
  --lr_critic=3e-4 \
  --coef_entropy_loss=0.05
```

---

## 5. Expected Behavior After Fixes

With `gamma=0.99` + reward clipping + reduced failure penalty:

```
Acceptance Rate (expected trajectory)
90% |                      * * * * * *   (converges ~epoch 20-30)
80% |              * * * *
70% |          * *
60% |      * *
40% |    *
20% |  *
 5% | *                                  ← epochs 0-1 still low but not near-zero
 0% |_____________________________________________ Epochs
     0  1  2  3  4  5  6  7  8  10  15  20  30
```

The key difference is a **gradual ramp-up** rather than a binary jump. Epoch-to-epoch variance should stay within ±5% acceptance rate rather than the current ±14%.

---

## 6. Summary Table of Fixes

| Fix | File | Change | Priority | Expected Impact |
|-----|------|--------|----------|-----------------|
| `gamma = 0.99` | `hrl_ac_solver.py` | Already done | **Critical** | Eliminates undiscounted return blowup |
| Reward clipping `[-5, 5]` | `hrl_ac/env.py` | `reward = max(min(reward, 5.), -5.)` | **High** | Reduces return variance |
| Reduce failure penalty | `hrl_ac/env.py` | `0.5 → 0.1` multiplier | **High** | Prevents rejection-safe collapse |
| Lower `eps_clip` | config / solver | `0.2 → 0.1` | Medium | Smoother policy updates |
| Lower `lr_actor/critic` | command line | `1e-3 → 3e-4` | Medium | Less oscillation per update |
| Increase entropy coef | `hrl_ac_solver.py` | `0.05 → 0.08` | Low | Maintains exploration diversity |

Apply in priority order. The first three alone should visibly stabilize the acceptance rate curve.
