# HRL-ACRA Reward System: Root-Cause Analysis & Redesign Guide

## Table of Contents
1. [Confirmed Issue Summary](#1-confirmed-issue-summary)
2. [Root-Cause Analysis](#2-root-cause-analysis)
3. [Mathematical Failure Proof](#3-mathematical-failure-proof)
4. [Why the PPO Policy Collapses](#4-why-the-ppo-policy-collapses)
5. [Secondary Issues: Sparsity, Scaling, Credit Assignment](#5-secondary-issues-sparsity-scaling-credit-assignment)
6. [Proposed Reward Redesign](#6-proposed-reward-redesign)
7. [Improved Reward Equations](#7-improved-reward-equations)
8. [Balancing and Scaling Strategies](#8-balancing-and-scaling-strategies)
9. [Exploration-Preserving Techniques](#9-exploration-preserving-techniques)
10. [PPO-Specific Stabilization Suggestions](#10-ppo-specific-stabilization-suggestions)
11. [Practical Implementation Recommendations](#12-practical-implementation-recommendations)
12. [Expected Behavioral Improvements](#13-expected-behavioral-improvements)

---

## 1. Confirmed Issue Summary

All assumptions in `reward_breakdown.md` are **confirmed correct** after inspecting `env.py`. The
observed "always-accept" policy collapse is caused by **three compounding flaws**:

| # | Flaw | Location in `env.py` | Severity |
|---|------|-----------------------|----------|
| F1 | Failure penalty is ~50× too small relative to success reward | `compute_reward`, Outcome B | Critical |
| F2 | Manual global-average baseline subtraction turns `reject=0` into a large negative | lines 66–72 | Critical |
| F3 | `gamma=1.0` in the solver + no reward normalization on raw reward before baseline subtraction | `hrl_ac_solver.py` | High |

Any one of these alone would degrade policy quality. Together they guarantee collapse.

---

## 2. Root-Cause Analysis

### 2.1 The Three-Outcome Reward Structure (as implemented)

```python
# Outcome A — Accept + sub-solver succeeds
basic_reward = solution['v_net_revenue'] / 100          # ~3.5
weight       = w_a + w_b                                # ~1.5  (w_a=1, w_b=lifetime/scale)
reward       = weight * basic_reward * r2c_ratio        # ≈ +2.52

# Outcome B — Accept + sub-solver fails  (THE BROKEN PENALTY)
reward = -0.01 * self.v_net.num_nodes                   # ≈ -0.05  (for avg 5-node VNR)

# Outcome C — Early rejection
reward = 0
```

The ratio of success reward to failure penalty is **≈ 50.4 : 1** (2.52 / 0.05).

This extreme asymmetry makes the following Expected-Value (EV) calculation the deciding factor:

```
EV(Accept) = p_success × (+2.52) + (1 - p_success) × (−0.05)
EV(Reject) = 0

EV(Accept) > EV(Reject)  iff  p_success > 0.05 / (2.52 + 0.05) ≈ 0.019  (< 2%)
```

This means the agent needs only a **1.9% estimated probability of success** for accepting to be
rational. Even for the hardest VNRs the sub-solver will occasionally succeed, so EV(Accept) is
almost always positive. The agent is incentivised to never reject.

### 2.2 The Global-Average Baseline Corruption

```python
# lines 66–72
average_reward = reward - (self.global_cumulative_reward / self.global_timestep_count)
self.cumulative_reward += average_reward
return average_reward
```

This subtraction is applied to the **raw step reward** before it reaches PPO's rollout buffer.
PPO then applies its own Critic-based Generalized Advantage Estimation (GAE) on top of these
already-modified rewards. The result is that the signal PPO optimises is:

```
r_ppo = r_raw - global_mean(r_raw)
```

Once the global mean stabilises around the average successful-accept reward (≈ +1.5):

```
r_ppo(Success) = +2.52 - 1.50 = +1.02   ← still positive
r_ppo(Reject)  =  0.00 - 1.50 = -1.50   ← appears as a large penalty
r_ppo(Fail)    = -0.05 - 1.50 = -1.55   ← barely worse than rejecting
```

**Rejecting is now treated as almost as bad as failing**, with zero upside. The PPO gradient will
drive the reject-action logit toward −∞.

### 2.3 Interaction with gamma=1.0

`hrl_ac_solver.py` sets `self.gamma = 1.0`. With no discounting and `gae_lambda = 0.98`, all
future rewards are weighted almost equally. Because the "global mean" in the baseline grows
monotonically over training, the baseline value drifts upward, making the effective penalty
for `reject` grow over time. This explains why the collapse gets **worse** in later epochs.

---

## 3. Mathematical Failure Proof

Define:
- `R_s` = success reward ≈ +2.52
- `R_f` = failure penalty ≈ −0.05
- `R_r` = reject reward = 0
- `μ` = running global mean ≈ +1.5 at steady state
- `p` = probability sub-solver succeeds for a given VNR

**What PPO actually sees after baseline subtraction:**

| Outcome | Raw r | r_ppo (after subtraction) |
|---------|-------|---------------------------|
| Accept+Succeed | +2.52 | +1.02 |
| Accept+Fail | −0.05 | −1.55 |
| Reject | 0 | −1.50 |

**PPO advantage for Accept vs Reject:**

```
A(Accept) = p(+1.02) + (1-p)(−1.55)
A(Reject) = −1.50

A(Accept) > A(Reject)
⟺  p(1.02) + (1-p)(−1.55) > −1.50
⟺  p(1.02 + 1.55) > −1.50 + 1.55
⟺  p(2.57) > 0.05
⟺  p > 0.019
```

The break-even success probability is **1.9%**. For any realistic sub-solver, `p >> 0.019`,
so PPO will **always** increase the accept probability via gradient ascent. The reject action
receives a persistent negative advantage, and its probability monotonically decays to zero.

---

## 4. Why the PPO Policy Collapses

### 4.1 Policy Gradient Direction

The PPO surrogate objective is:

```
L(θ) = E_t [ min(r_t(θ) A_t, clip(r_t(θ), 1−ε, 1+ε) A_t) ]
```

where `r_t(θ) = π_θ(a_t|s_t) / π_θ_old(a_t|s_t)` is the probability ratio.

Since A_t(Reject) < 0 persistently, the gradient `∂L/∂θ` consistently **decreases** the
probability of the reject action. After enough gradient steps, the softmax logit for `reject`
becomes so negative that its probability is numerically zero. At this point, the Categorical
distribution has zero entropy and the policy is stuck — PPO's clipping can no longer recover
the action because there are no rollout samples with `action=Reject`.

### 4.2 Entropy Collapse

The binary action distribution has entropy:

```
H(π) = −p_accept log(p_accept) − p_reject log(p_reject)
```

As `p_reject → 0`, `H(π) → 0`. With zero entropy, all rollout trajectories are
identical (always accept), the advantage estimator has zero variance signal for the reject
action, and PPO cannot explore the reject branch. **The collapse is self-reinforcing.**

### 4.3 Critic Bias

The Critic `V(s)` learns to predict the expected future return from state `s`. Once the policy
always accepts, the Critic is trained only on accept trajectories. Its value estimates are
therefore biased upward (they include accept rewards). If you try to force a reject action
during evaluation, the Critic will assign it a large negative advantage, and the actor will
suppress it further. The Critic is now complicit in the collapse.

---

## 5. Secondary Issues: Sparsity, Scaling, Credit Assignment

### 5.1 Reward Sparsity

The reward is only non-zero on Accept+Succeed outcomes. For difficult VNRs (p_success ≈ 0.1),
90% of accept steps yield the tiny penalty (−0.05), which PPO treats as nearly equivalent
to reject (0). This creates **sparse meaningful signal** and high gradient variance, making
it hard for the Critic to converge.

**Fix**: Use a shaped intermediate reward proportional to partial mapping progress
(e.g., fraction of virtual nodes successfully placed before failure), or at minimum a
penalty scaled to the resource demand wasted.

### 5.2 Reward Scaling Mismatch

The success reward is divided by `revenue_benchmark = 100`, giving ≈ 2.52. But the failure
penalty is `0.01 × num_nodes` ≈ 0.05. The two terms differ by 50×. PPO normalises advantages
internally (if `norm_advantage=True`), but because reject always has a near-zero frequency
in rollouts, its normalised advantage is systematically biased.

**Fix**: Choose the failure penalty so the break-even probability `p_break` matches the
*actual* minimum acceptable sub-solver success rate (e.g., 30%):

```
p_break = |R_f| / (R_s + |R_f|) = 0.30
|R_f| = 0.30 × R_s / 0.70 ≈ 1.08  →  target failure reward ≈ −1.1
```

### 5.3 Credit Assignment

The HRL-AC agent makes one binary decision per VNR arrival. The reward for that decision
is returned immediately (single-step episode from the admission controller's perspective).
Credit assignment is therefore not a temporal problem here, but the **effective signal**
the agent receives is corrupted by the baseline subtraction, which acts like a noisy
credit mis-attribution between the accept and reject decisions.

### 5.4 Delayed Reward / Lifetime Bias

The `w_b = lifetime / scale` weight rewards accepting long-lived VNRs more. This is
directionally correct (long-lived VNRs contribute more revenue) but it also means that
failing a long-lived VNR incurs the same small penalty as failing a short-lived one,
making the asymmetry even worse for high-value VNRs.

---

## 6. Proposed Reward Redesign

The redesign targets three properties:

1. **EV(Reject) > EV(Accept) for hard VNRs** — the agent should learn to say no.
2. **No manual baseline subtraction** — let PPO's GAE handle this.
3. **Bounded, normalised reward magnitudes** — prevents Critic divergence.

### Design Principles

```
R_success  =  positive, proportional to VNR value
R_failure  =  negative, proportional to wasted resources, magnitude comparable to R_success
R_reject   =  0  (or a small positive bonus for intelligent rejection)
```

The break-even condition should hold for a configurable minimum acceptance threshold
`p_min` (e.g., 0.25–0.40):

```
|R_failure| = (p_min × R_success) / (1 - p_min)
```

---

## 7. Improved Reward Equations

Replace the entire `compute_reward` method in `env.py` as follows:

```python
def compute_reward(self, solution):
    """
    Redesigned reward for HRL-AC admission control.
    
    Targets a break-even sub-solver success probability of ~30%:
        EV(Accept) > EV(Reject)  iff  p_success > p_min ≈ 0.30
    
    Key changes:
      - Failure penalty scales with actual resource demand wasted (not node count).
      - penalty/success ratio is ~1:2, giving p_break ≈ 0.33.
      - No manual global-average subtraction; PPO's GAE handles the baseline.
      - All values normalised to roughly [-1.5, +2.5] to stabilise Critic training.
    """
    revenue_benchmark = 100.0
    w_a = 1.0
    w_b = solution['v_net_lifetime'] / self.v_net_simulator.v_sim_setting['lifetime']['scale']
    weight = w_a + w_b  # in [1, 2]

    if solution['result']:
        # ── Outcome A: Accept + Successful Mapping ──────────────────────────
        # Reward scales with revenue, lifetime, and resource efficiency.
        basic_reward = solution['v_net_revenue'] / revenue_benchmark
        reward = weight * basic_reward * solution['v_net_r2c_ratio']
        # Typical range: ~[0.5, 5.0]; median ≈ +2.5

    elif (not solution['result']) and (not solution['early_rejection']):
        # ── Outcome B: Accept + Mapping Failed ──────────────────────────────
        # Penalise proportionally to the resource demand that was wasted AND
        # the weight (long-lived, high-demand VNR failures are worse).
        # total_resource_demand is typically in [100, 600].
        wasted_demand = self.v_net.total_resource_demand / revenue_benchmark
        reward = -weight * wasted_demand * 0.5
        # Typical range: ~[-3.0, -0.5]; median ≈ -1.2
        # Break-even p_min = |R_f| / (R_s + |R_f|) ≈ 1.2 / (2.5 + 1.2) ≈ 0.32

    else:
        # ── Outcome C: Early Rejection ──────────────────────────────────────
        reward = 0.0
        # Optionally: add a small positive bonus for rejecting hard VNRs
        # to encourage exploration of the reject action early in training.
        # reward = +0.05  # uncomment if entropy collapse persists

    # ── Bookkeeping (no baseline subtraction) ───────────────────────────────
    self.actual_cumulative_reward += reward
    self.v_net_reward += reward
    self.global_timestep_count += 1
    self.global_cumulative_reward += reward

    running_mean = self.global_cumulative_reward / max(self.global_timestep_count, 1)
    self.extra_record_info.update({
        'actual_cumulative_reward': self.actual_cumulative_reward,
        'global_cumulative_reward': self.global_cumulative_reward,
        'average_reward_benchmark': running_mean,
        'cumulative_reward': self.cumulative_reward,
        'actual_reward': reward,
    })

    # Return the RAW reward — PPO's GAE computes advantages internally.
    self.cumulative_reward += reward
    return reward
```

> **Key change from the original**: the last line returns `reward` directly, **not**
> `reward - global_mean`. The `average_reward_benchmark` is still logged for monitoring.

---

## 8. Balancing and Scaling Strategies

### 8.1 Verify the Break-Even Point After Tuning

After choosing your penalty coefficient, verify the break-even empirically:

```python
# In a diagnostic script, sweep p and check EV sign change
p_min_target = 0.30
R_s_typical  = 2.5   # from your reward logs
R_f_needed   = (p_min_target * R_s_typical) / (1 - p_min_target)
print(f"Required |R_f| for p_break={p_min_target}: {R_f_needed:.3f}")
# → Required |R_f| for p_break=0.30: 1.071
```

Then cross-check your `total_resource_demand` distribution:

```python
# Log during training:
print(f"avg total_resource_demand / 100: {avg_demand:.2f}")
print(f"avg failure reward = -weight * avg_demand * 0.5 = {-1.5 * avg_demand * 0.5:.2f}")
```

Adjust the multiplier (currently `0.5`) until the median failure reward magnitude is
≈ `R_f_needed`.

### 8.2 Reward Normalisation in the Solver

In `hrl_ac_solver.py`, `self.norm_reward = True` is already set. Confirm that the
`PPOSolver` base class applies reward normalisation **to the raw rewards** stored in the
rollout buffer, not to the already-corrupted baseline-subtracted values. If the base class
uses `RunningMeanStd`, make sure it is applied after environment stepping:

```python
# In PPOSolver.update() or collect_rollouts(), something like:
if self.norm_reward:
    rewards = self.reward_normalizer.normalize(rewards)
```

With the manual baseline removed, this normalisation is now safe and effective.

### 8.3 Clip Extreme Reward Values

Add hard clipping to prevent rare outlier VNRs from dominating gradient updates:

```python
reward = np.clip(reward, -5.0, 5.0)
```

Set the clip bounds to approximately ±2σ of your observed reward distribution.

---

## 9. Exploration-Preserving Techniques

### 9.1 Entropy Regularisation (Primary Fix)

Add an entropy bonus to the PPO objective to prevent the binary distribution from
collapsing. In `hrl_ac_solver.py`, ensure the entropy coefficient is set and non-trivial:

```python
# In PPOSolver.__init__ or HrlAcSolver.__init__:
self.entropy_coef = 0.05   # start here; tune between 0.01 and 0.1
```

Verify the `PPOSolver.update()` base class includes:
```python
actor_loss = -torch.mean(torch.min(surr1, surr2)) - self.entropy_coef * entropy
```

If the base class does not expose this, override `update()` or add the entropy term manually.

### 9.2 Initialise Actor Logits Toward Balanced Policy

At the start of training, the actor should output nearly equal logits for accept and reject.
Ensure the final linear layer of the actor MLP is initialised with small weights:

```python
# In net.py, Actor.__init__, after self.net = MLPNet(...):
# Zero out the final layer bias; small weight init → logits near 0 → π ≈ [0.5, 0.5]
nn.init.orthogonal_(self.net.layers[-1].weight, gain=0.01)
nn.init.constant_(self.net.layers[-1].bias, 0.0)
```

### 9.3 Optional: Warm-Start with Balanced Labels

Before RL training, run a supervised warm-up phase where the agent is trained on labels
derived from the sub-solver's offline acceptance rate per VNR difficulty class. This gives
the actor a non-degenerate starting policy.

### 9.4 Optional: Rejection Bonus for Hard VNRs

Add a small positive reward for early rejection to ensure the reject gradient is never
purely zero. This is especially useful early in training when the actor is close to always-accept:

```python
# In Outcome C block:
# Compute a simple hardness proxy (high demand relative to average = hard VNR)
demand_ratio = self.v_net.total_resource_demand / self.avg_demand_estimate
if demand_ratio > 1.5:   # VNR is significantly harder than average
    reward = +0.1        # small bonus for intelligent rejection
else:
    reward = 0.0
```

---

## 10. PPO-Specific Stabilization Suggestions

### 10.1 Remove the Manual Baseline (Critical)

This is a duplicate of F2's fix but important enough to repeat: **delete lines 66–72 in
`env.py`** that compute `average_reward` and return `reward` directly. PPO already implements
a Critic-based baseline through its GAE advantage computation. Double-baselining corrupts
the advantage estimates and causes the collapse described in Section 3.

### 10.2 Verify GAE Advantage Normalisation

PPO's `update()` should normalise advantages to zero-mean, unit-variance before computing
the surrogate loss. Check that this is enabled in the `PPOSolver` base class:

```python
# In PPOSolver.update():
advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
```

If the base class normalises *rewards* but not *advantages*, ensure advantage normalisation
is also applied.

### 10.3 Tune the Clip Ratio

With the reward rebalanced, the optimal clip ratio `ε` may differ. Start with:

```python
self.clip_range = 0.2   # standard PPO default
```

If the policy still collapses, try `ε = 0.1` to slow policy updates and prevent early
entropy collapse.

### 10.4 Reduce Learning Rate During Early Training

The current LR is divided by 10 in the solver:
```python
{'params': self.policy.actor.parameters(), 'lr': self.lr_actor / 10},
```

This is appropriate. Additionally, consider a learning rate schedule:

```python
# Cosine annealing or linear decay over training
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
    self.optimizer, T_max=total_training_steps, eta_min=1e-6
)
```

### 10.5 Critic Value Clipping

Enable value function clipping in the PPO update to prevent Critic overfitting to the
biased always-accept return estimates accumulated before the fix:

```python
# value_loss with clipping:
v_pred_clipped = v_pred_old + torch.clamp(v_pred - v_pred_old, -clip_range, clip_range)
v_loss = torch.max(F.mse_loss(v_pred, returns), F.mse_loss(v_pred_clipped, returns))
```

### 10.6 Rollout Buffer Size

Ensure the rollout buffer is large enough to contain **both accept and reject samples**. If
the buffer fills up entirely with accept samples (e.g., buffer_size=256 and reject frequency
is < 1%), the gradient update has no reject-action gradients. Use a larger buffer or
implement **stratified sampling** that guarantees at least some reject samples per batch.

---

## 11. Practical Implementation Recommendations

### 11.1 Minimal Patch (apply in this order)

```
Step 1. In env.py compute_reward():
    - Remove the global_cumulative_reward / global_timestep_count subtraction.
    - Change the failure penalty from:
          reward = -0.01 * self.v_net.num_nodes
      to:
          reward = -weight * (self.v_net.total_resource_demand / revenue_benchmark) * 0.5
    - Return reward directly.

Step 2. In hrl_ac_solver.py:
    - Confirm self.entropy_coef is set to 0.05 (or add it if missing).

Step 3. Run a short training sweep (1–2 epochs) and check:
    - reject_count / total_count > 0.05  (agent is exploring rejection)
    - entropy of binary distribution > 0.3  (not collapsed yet)
    - failure_reward median ≈ -1.0 to -1.5  (penalty is substantial)
```

### 11.2 Monitoring Checklist During Training

Add the following metrics to your logging/tensorboard:

```python
self.extra_record_info.update({
    'reject_ratio':    (1 if solution['early_rejection'] else 0),
    'accept_ratio':    (1 if not solution['early_rejection'] else 0),
    'success_ratio':   (1 if solution['result'] else 0),
    'fail_ratio':      (1 if (not solution['result'] and not solution['early_rejection']) else 0),
    'raw_reward':      reward,
    'policy_entropy':  # log from actor in solver.update()
})
```

**Red flags to watch for:**
- `reject_ratio` monotonically decreasing toward 0 → collapse is recurring
- `policy_entropy` < 0.2 → add entropy bonus or increase `entropy_coef`
- `fail_ratio` / `accept_ratio` > 0.7 → sub-solver quality issue, not reward issue

### 11.3 Hyperparameter Search Priority

| Parameter | Current | Recommended Range | Impact |
|-----------|---------|------------------|--------|
| `failure_penalty_coef` | 0.01 (broken) | 0.3 – 0.7 | Critical |
| `entropy_coef` | unknown | 0.01 – 0.10 | High |
| `clip_range` | default 0.2 | 0.1 – 0.2 | Medium |
| `gae_lambda` | 0.98 | 0.95 – 0.99 | Low |
| `gamma` | 1.0 | 0.99 – 1.0 | Low (online setting) |

### 11.4 Regression Test

After applying the fix, the following should hold within 3–5 epochs:

```
assert reject_ratio > 0.10       # agent is not always accepting
assert success_ratio > 0.60      # accepted VNRs are mostly mappable
assert policy_entropy > 0.30     # binary distribution is not degenerate
assert avg_r2c_ratio > 0.45      # embedding quality maintained
```

---

## 12. Expected Behavioral Improvements After the Fixes

| Metric | Before Fix | Expected After Fix |
|--------|-----------|-------------------|
| Early rejection rate | ~0% (collapses to 0) | 15–35% (learns to filter hard VNRs) |
| Sub-solver success rate (given accept) | ~50–60% | 70–85% (only accepts mappable VNRs) |
| Long-term R/C ratio | Degrades over time | Stable or improving |
| Policy entropy | → 0 (collapsed) | Steady-state > 0.3 |
| Critic loss | High variance | Converges smoothly |
| Average reward (raw) | Inflated by always-accept | Initially lower, then improves |

The key insight is that **a lower acceptance ratio paired with a higher per-accepted-VNR
success rate will produce better long-term revenue** than blindly accepting everything. The
fixed reward function makes this trade-off visible to the PPO agent.

---

## Quick Reference: Before vs. After

```python
# ─── BEFORE (broken) ──────────────────────────────────────────────────────────
# Outcome B failure penalty:
reward = -0.01 * self.v_net.num_nodes             # ≈ -0.05  (too small)

# Return to PPO with corrupted baseline:
average_reward = reward - (self.global_cumulative_reward / self.global_timestep_count)
return average_reward                              # makes reject look like -1.5


# ─── AFTER (fixed) ────────────────────────────────────────────────────────────
# Outcome B failure penalty (scaled to wasted demand):
wasted_demand = self.v_net.total_resource_demand / revenue_benchmark
reward = -weight * wasted_demand * 0.5            # ≈ -1.2  (proportional)

# Return raw reward — let PPO's GAE compute the advantage:
return reward
```

These two lines are the minimum viable fix. All other recommendations in this document
improve robustness and training stability but are secondary to eliminating the baseline
corruption and rebalancing the failure penalty.
