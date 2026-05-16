# Comprehensive Analysis of HRL-ACRA Reward System and Policy Collapse

This document provides a detailed mathematical breakdown of the reward system implemented in the Hierarchical Reinforcement Learning Admission Control (HRL-AC) solver. It explains the core reasons behind the agent's policy collapse (learning an "always accept" degenerate policy) and plots out specific directions for fixing the reward shaping.

## 1. The Current Reward Math Breakdown

In `virne/solver/learning/hrl_ac/env.py` under the `compute_reward` method, the environment defines three possible outcomes for an incoming Virtual Network Request (VNR).

### Outcome A: Accept & Map Successfully
When the high-level agent accepts the VNR and the low-level sub-solver successfully maps it:
```python
basic_reward = solution['v_net_revenue'] / 100
weight = 1 + (solution['v_net_lifetime'] / max_lifetime)  # Between 1.0 and 2.0
reward = weight * basic_reward * solution['v_net_r2c_ratio']
```
*   **Typical Values:** Average revenue per VNR is roughly ~350. The `r2c_ratio` averages ~0.48. The `weight` averages ~1.5.
*   **Estimated Base Reward:** $1.5 \times (350 / 100) \times 0.48 \approx \mathbf{+2.52}$

### Outcome B: Accept & Map Fails
When the high-level agent accepts the VNR, but the low-level sub-solver fails to map it (wasting computational resources):
```python
reward = - 0.01 * (self.v_net.num_nodes)
```
*   **Typical Values:** VNRs typically contain between 2 to 10 nodes. Let's assume an average of 5 nodes.
*   **Estimated Base Reward:** $-0.01 \times 5 = \mathbf{-0.05}$

### Outcome C: Early Rejection
When the high-level agent explicitly rejects the VNR upfront:
```python
reward = 0
```
*   **Estimated Base Reward:** $\mathbf{0}$

---

## 2. The Expected Value Problem (Why the agent gambles)

Reinforcement learning agents update their policies to maximize Expected Value ($E$). Let's assume a highly-constrained, difficult VNR arrives, and the sub-solver only has a tiny **5% probability ($p=0.05$)** of successfully mapping it.

If the agent evaluates its options:

*   **Expected Reward of Accepting:** 
    $E[Accept] = (p \times \text{Success Reward}) + ((1-p) \times \text{Failure Penalty})$
    $E[Accept] = (0.05 \times 2.52) + (0.95 \times -0.05) = 0.126 - 0.0475 = \mathbf{+0.0785}$
*   **Expected Reward of Rejecting:** 
    $E[Reject] = \mathbf{0}$

Because $0.0785 > 0$, mathematical logic dictates that **it is always better to accept and gamble on a miracle than to reject**. The penalty for failing ($-0.05$) is so microscopic compared to the massive reward for succeeding ($+2.52$) that the agent learns it has absolutely nothing to lose by accepting every single request. Over time, the neural network weights shift to output `Accept` for every state.

---

## 3. The Fatal Flaw: The Global Average Subtraction

The final trigger for the collapse happens in lines 66-72 of `env.py`, where a baseline subtraction is applied manually before returning the step reward to PPO:
```python
average_reward = reward - (self.global_cumulative_reward / self.global_timestep_count)
```

Assume the agent is doing reasonably well early on, and the global average reward establishes itself at `+1.5`. Look at what this does to the final PPO step reward:

*   **If it Succeeds:** $2.52 - 1.5 = \mathbf{+1.02}$
*   **If it Rejects:** $0 - 1.5 = \mathbf{-1.50}$
*   **If it Fails:** $-0.05 - 1.5 = \mathbf{-1.55}$

**The Collapse Trigger:** To the PPO agent, *Rejecting* guarantees a massive penalty ($-1.50$). Failing a mapping is barely worse ($-1.55$). But *Accepting* gives it a chance at a positive score ($+1.02$). The policy gradient will ruthlessly optimize the network to completely eliminate the `Reject` action to avoid the guaranteed $-1.50$ penalty, locking the model into a degenerate "always accept" state.

---

## 4. Plotting the Direction for a Fix

To fix this collapse and ensure the HRL agent learns a strict, resource-aware admission boundary, the scales must be balanced. Implement the following two architectural changes:

### Direction 1: Punish Failures Severely
Make the penalty for an accepted-but-failed VNR scale proportionally with the potential reward. If success gives $+2.5$, failure should give a heavy penalty (e.g., $-1.5$ to $-3.5$).

```python
# Change this weak penalty:
# reward = - 0.01 * (self.v_net.num_nodes)

# To a strictly punishing penalty:
reward = - (self.v_net.total_resource_demand / 100) 
```
This forces the Expected Value ($E[Accept]$) of bad requests to go negative, teaching the agent that rejecting ($0$) is mathematically better than failing a risky map ($-3.5$).

### Direction 2: Remove the Manual Global Baseline
Subtracting a globally increasing average from a static `0` reject reward destroys the agent's relative baseline. Standard PPO implementations already calculate `Advantage` using their own internal Critic network (via Generalized Advantage Estimation, GAE). 

You do not need to manually subtract `global_cumulative_reward / global_timestep_count` from the step reward. You should return the raw `reward` directly to PPO:

```python
# Change this:
# average_reward = reward - self.global_cumulative_reward / self.global_timestep_count
# return average_reward

# To this:
return reward
```

By applying these two fixes, the high-level PPO agent will become appropriately risk-averse, avoiding mapping failures and learning a precise admission boundary that filters out unmappable requests.
