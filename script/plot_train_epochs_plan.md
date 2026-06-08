# Plan - Plot final RAC and LRC across all training epochs

This document defines the implementation details of a python script to parse training records (CSV files under `records/` directory of specified runs) and plot Request Acceptance Rate (RAC) and Long-term Revenue-to-Cost (LRC) ratio over the course of training epochs.

## Proposed Changes

### Training Plotting Tool

#### [plot_train_epochs.py](file:///d:/HUST_file/@research/@hrl-git/hrl-acra/script/plot_train_epochs.py)

We will create a new Python script `script/plot_train_epochs.py` that:
- Accepts a comma-separated list of run directories (e.g., `save/hrl_ac/avai_shortest-DESKTOP-LJ05KB5-20260603T012937` and `save/hrl_ac/bfs_shortest-DESKTOP-LJ05KB5-20260603T013514`).
- Automatically scans the `records/` directory of each run for non-temp CSV files.
- Sorts these CSV files chronologically to represent the sequence of all epochs.
- Reads `config.yaml` in each run directory to determine the evaluation interval (e.g. `eval_interval: 10`).
- Excludes validation epoch record files (located at indices `k * eval_interval + k - 1`), keeping only the training epoch record files.
- Assigns each training epoch file its training epoch number (0, 1, 2, ...).
- For each training epoch file:
  - Filters to keep only arrival events (`event_type == 1`) if the column is present.
  - Extracts the Request Acceptance Rate (RAC) using the formula specified in [z7874322257018_5437b1486ad5e03b09725b15d6cbbcc1.jpg](file:///d:/HUST_file/@research/@hrl-git/hrl-acra/references/VNE/z7874322257018_5437b1486ad5e03b09725b15d6cbbcc1.jpg):
    $$RAC = \frac{\sum_{t=0}^T |\tilde{\mathcal{I}}(t)|}{\sum_{t=0}^T |\mathcal{I}(t)|} \times 100\%$$
    Which is implemented as `(final_success_count / final_v_net_count) * 100` at the end of the total operational period $T$ (the last row of each training CSV file).
  - Extracts the Long-term Revenue-to-Cost (LRC) ratio using the formula:
    $$LRC = \frac{\sum (\text{revenue(solution)} \times \text{lifetime})}{\sum (\text{cost(solution)} \times \text{lifetime})} = \frac{\text{total\_time\_revenue}}{\text{total\_time\_cost}}$$
    Which is implemented as `(final_total_time_revenue / final_total_time_cost)` at the end of the total operational period (from the last row of the file).
- Creates a vertical stack of 2 plots:
  - **Top Subplot**: Request Acceptance Rate (RAC) % vs. Training Epoch.
  - **Bottom Subplot**: Long-term Revenue-to-Cost (LRC) Ratio vs. Training Epoch.
- Uses clear labels, colors, a clean grid layout, and a legend distinguishing the two runs.
- Saves the output image to a designated path (e.g. `save/train_epochs_compare.png`).

## Verification Plan

### Automated Tests
We will run the script using the `hrl_ac` conda environment to plot the results and save the image:
```bash
conda run -n hrl_ac python script/plot_train_epochs.py save/hrl_ac/avai_shortest-DESKTOP-LJ05KB5-20260603T012937,save/hrl_ac/bfs_shortest-DESKTOP-LJ05KB5-20260603T013514 -o save/train_compare_plot.png
```

### Manual Verification
- Verify that the plot file `save/train_compare_plot.png` is generated successfully.
- Display print outputs of final RAC and LRC for training epochs for verification.
