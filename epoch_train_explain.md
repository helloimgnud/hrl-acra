# Single Epoch Training & Evaluation Output Explanation

This document provides a line-by-line explanation of a single evaluation step and epoch summary logged during the training of the `hrl_ac` model.

## 1. Environment Initialization

```text
*** Generate virtual networks with seed 0
```
*   **What this means:** The environment is preparing for an evaluation episode. To ensure fair and comparable testing across different epochs, the virtual network requests (VNRs) are generated or sampled from the dataset using a fixed random seed (`0`). This guarantees the model is evaluated on the exact same sequence of requests every time, allowing you to accurately measure learning progress.

## 2. Evaluation Metrics Dictionary

During the evaluation phase, the agent is tested on the generated dataset. The dictionary logged represents the performance of the model's current weights (at epoch 9).

### 2.1. Admission & Mapping Outcomes
```python
 'success_count': 694,
 'early_rejection_count': 235,
 'place_failure_count': 0,
 'route_failure_count': 71,
 'acceptance_rate': 0.694,
```
*   **Total Requests:** If we sum `success_count + early_rejection_count + place_failure_count + route_failure_count`, we get exactly **1000** requests. This perfectly matches the `dataset/v_nets/1000-...` path.
*   **Agent's Decision:** The PPO admission controller explicitly **rejected 235** requests, preventing them from consuming computation time. It **accepted 765** requests.
*   **Sub-Solver's Performance:** Out of the 765 accepted requests, the low-level mapping solver (`nrm_rank`) successfully embedded **694**. It failed to find a valid shortest-path link mapping for **71** requests (`route_failure`), but had zero node placement failures (`place_failure`).
*   **Acceptance Rate:** `694 / 1000 = 0.694` (or 69.4%). This is a solid mid-training performance.

### 2.2. Cost, Revenue, and Efficiency
```python
 'r2c_ratio': 0.4793275828461958,
 'total_revenue': 243450,
 'total_cost': 507899,
 'long_term_aver_revenue': 10.147978324301793,
 'long_term_aver_cost': 21.171279699874948,
```
*   **Revenue vs. Cost:** The successful embeddings generated `243,450` in revenue but consumed `507,899` in physical network resources (cost). 
*   **Efficiency (`r2c_ratio`):** Revenue divided by cost is ~0.479. This implies that on average, embedding 1 unit of requested virtual resource required about 2.08 physical resource units (due to multi-hop routing paths).
*   **Long-Term Averages:** These are simply the totals divided by the `total_simulation_time` (23990.0).

### 2.3. Reinforcement Learning State
```python
 'cumulative_reward': 221.1011110206692,
```
*   **Reward:** The agent accumulated a positive net reward of `221.1`. This means the shaped rewards for successful mappings outweighed the shaped penalties for the 71 route failures and 235 rejections.

## 3. Saving Artifacts

```text
save records to save/hrl_ac/d0fe23168cc4-20260516T161053/records/hrl_ac-d0fe23168cc4-20260516T161053-20260516T162342.csv
save summary to save/exp-wx_100-hrl_ac-training.csv
```
*   **What this means:** After finishing the evaluation episode, the framework saves two files:
    1.  **Detailed Record:** A step-by-step history of all 1000 requests processed in this specific evaluation run.
    2.  **Summary:** It appends the logged dictionary (the row with `acceptance_rate=0.694`) to the main `exp-wx_100-hrl_ac-training.csv` tracking file.

## 4. Policy Network Update (PPO Metrics)

```text
Update time: 000399 | +0.2624 & -0.0039 & +0.5446 & +0.6016 & -0.5437 & -0.5042 & +0.0073
```
*   **What this means:** This line is printed directly by the Proximal Policy Optimization (PPO) updating routine after the agent has collected enough trajectory data from interacting with the environment.
*   **Update Time:** The PPO gradient descent optimization steps took `399` iterations or milliseconds (depending on framework implementation).
*   **The numerical vector (`+0.2624 & ...`):** These represent the internal loss and debugging metrics of the PPO algorithm during the neural network update. While the exact order depends on the specific logger in the Virne framework, a typical PPO implementation logs the following in sequence:
    1.  **Total Loss** (`+0.2624`)
    2.  **Actor (Policy) Loss** (`-0.0039`): Measures policy improvement. A negative value indicates the optimizer pushed the policy to increase the probability of actions that resulted in high advantages.
    3.  **Critic (Value) Loss** (`+0.5446`): Mean Squared Error of the value function's predictions. Indicates how accurately the critic is guessing the expected reward.
    4.  **Entropy** (`+0.6016`): A measure of exploration. Higher entropy means the agent is still unsure and exploring; lower entropy means it is becoming confident in its decisions.
    5.  **KL Divergence / Clip Fraction / Explained Variance** (Remaining values): Internal PPO metrics measuring how much the policy changed during this update step to ensure stability within the trust region.

## 5. Epoch Summary Logging

```text
epoch    9, success_count     0, r2c 0.4793
```
*   **What this means:** This is a short, terminal-friendly printout concluding the training loop for Epoch 9.
*   **`epoch 9`:** Identifies the current step in the `num_train_epochs=50` parameter.
*   **`r2c 0.4793`:** Mirrors the `r2c_ratio` found in the evaluation dictionary, confirming the evaluation score for this epoch.
*   **Why is `success_count 0`?** 
    *   This is typically a logging artifact or quirk in the framework. The evaluation phase clearly had a success count of `694`.
    *   However, during the *training* phase (collecting PPO trajectories), the agent might reset the environment multiple times in partial episodes (mini-batches). The `success_count` printed here is likely fetching the variable from an incomplete training environment thread or the final empty batch of the epoch, rather than the true evaluation environment state. It does not mean the agent failed; the evaluation dictionary holds the true performance.
