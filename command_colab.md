# Google Colab Execution Guide: Controlled Datasets & Evaluator Runs

This guide provides detailed commands to set up, pre-generate a controlled dataset with a fixed seed, and evaluate both normal (heuristic/learning) and hierarchical 2-agent (`hrl_ac`) solvers in a Google Colab environment.

---

## 1. Colab Environment Setup

Before running the code, you need to install the required libraries. Run the following commands in a Colab notebook cell to install all dependencies (including PyTorch Geometric):

```bash
# 1. Clone the repository and navigate into the root directory
!git clone https://github.com/GeminiLight/hrl-acra.git  # Replace with your repository link if different
%cd hrl-acra

# 2. Install basic dependencies
!pip install numpy pandas matplotlib pyyaml tqdm colorama networkx scipy gym stable_baselines3 sb3_contrib ortools

# 3. Install PyTorch Geometric (pyg) dependencies matching the pre-installed PyTorch version in Colab
!pip install torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric -f https://data.pyg.org/whl/torch-$(python -c "import torch; print(torch.__version__)").html
```

---

## 2. Step 1: Pre-generate and Save a Controlled Dataset

To ensure all algorithms are evaluated on the exact same networks and request arrivals under identical seeds, generate the dataset once and save it to disk. 

The python script [data/generator.py](file:///d:/HUST_file/@research/@hrl-git/hrl-acra/data/generator.py) contains a `Generator` class which saves physical network data to `dataset/p_net` and virtual network requests to `dataset/v_nets`.

Run the following command in Colab to pre-generate and save the dataset with a controlled seed (e.g., `--seed 42`):

```bash
!python -c "from config import get_config; from data.generator import Generator; config = get_config(); Generator.generate_dataset(config, save=True)" \
  --seed 42 \
  --v_sim_setting_num_v_nets 1000 \
  --p_net_setting_path settings/p_net_setting.yaml \
  --v_sim_setting_path settings/v_sim_setting.yaml
```

> [!NOTE]
> - This command parses `--seed 42` (which configures the generation process to be deterministic).
> - The dataset is saved under `dataset/p_net/` and `dataset/v_nets/` directories.
> - Any future run with `--seed 42` and identical network/simulation settings will automatically load this saved dataset rather than generating new requests dynamically.

---

## 3. Step 2: Evaluate Normal (Heuristic/Single-Agent) Solvers

To evaluate a baseline solver (like `nrm_rank`, `grc_rank`, or `pl_rank`) using the saved dataset, run [main.py](file:///d:/HUST_file/@research/@hrl-git/hrl-acra/main.py) with the following parameters:
- `--renew_v_net_simulator False`: Forces loading the saved dataset instead of generating new requests.
- `--num_train_epochs 0`: Skip the training phase and only perform evaluation.

### Run GRC Solver:
```bash
!python main.py \
  --solver_name "grc_rank" \
  --renew_v_net_simulator False \
  --num_train_epochs 0 \
  --seed 42 \
  --summary_file_name "eval_grc_rank.csv"
```

### Run NRM Solver:
```bash
!python main.py \
  --solver_name "nrm_rank" \
  --renew_v_net_simulator False \
  --num_train_epochs 0 \
  --seed 42 \
  --summary_file_name "eval_nrm_rank.csv"
```

---

## 4. Step 3: Evaluate the 2-Agent Solver (`hrl_ac`) with Different Sub-Solvers

The hierarchical solver [hrl_ac](file:///d:/HUST_file/@research/@hrl-git/hrl-acra/solver/learning/hrl_ac/hrl_ac_solver.py) controls **Admission Control** (upper-level agent) and relies on a sub-solver for **Resource Allocation** (lower-level agent). 

To run it for evaluation only, we use `--num_train_epochs 0`, point to the pretrained models using `--pretrained_model_path`, and define the desired `--sub_solver_name`.

### Case A: Evaluating `hrl_ac` with Heuristic Sub-Solvers

You can pair `hrl_ac` with heuristic sub-solvers like `nrm_rank` or `grc_rank`. These do not require a separate pretrained model path for the sub-solver.

#### Using `nrm_rank` as Sub-Solver:
```bash
!python main.py \
  --solver_name "hrl_ac" \
  --sub_solver_name "nrm_rank" \
  --renew_v_net_simulator False \
  --num_train_epochs 0 \
  --pretrained_model_path "/content/drive/MyDrive/models/hrl_ac_pretrained.pth" \
  --seed 42 \
  --summary_file_name "eval_hrl_ac_nrm.csv"
```

#### Using `grc_rank` as Sub-Solver:
```bash
!python main.py \
  --solver_name "hrl_ac" \
  --sub_solver_name "grc_rank" \
  --renew_v_net_simulator False \
  --num_train_epochs 0 \
  --pretrained_model_path "/content/drive/MyDrive/models/hrl_ac_pretrained.pth" \
  --seed 42 \
  --summary_file_name "eval_hrl_ac_grc.csv"
```

### Case B: Evaluating `hrl_ac` with Learning-Based `hrl_ra` Sub-Solver

To evaluate the complete 2-agent RL hierarchy, pair `hrl_ac` with the learning-based resource allocation agent `hrl_ra`. This requires both the upper-level agent model (`--pretrained_model_path`) and the lower-level sub-solver model (`--pretrained_subsolver_model_path`).

```bash
!python main.py \
  --solver_name "hrl_ac" \
  --sub_solver_name "hrl_ra" \
  --renew_v_net_simulator False \
  --num_train_epochs 0 \
  --pretrained_model_path "/content/drive/MyDrive/models/hrl_ac_pretrained.pth" \
  --pretrained_subsolver_model_path "/content/drive/MyDrive/models/hrl_ra_pretrained.pth" \
  --seed 42 \
  --summary_file_name "eval_hrl_acra.csv"
```

---

## 5. Summary of Key CLI Arguments

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `--solver_name` | `nrm_rank` | Name of the primary solver (e.g., `grc_rank`, `nrm_rank`, `hrl_ac`). |
| `--sub_solver_name` | `nrm_rank` | The lower-level solver used by `hrl_ac` (e.g., `nrm_rank`, `grc_rank`, `hrl_ra`, `fast_hpso`). |
| `--renew_v_net_simulator` | `False` | Set to `False` to load the dataset from disk. Set to `True` to regenerate. |
| `--num_train_epochs` | `100` | Number of epochs to train. Set to `0` for evaluation-only mode. |
| `--pretrained_model_path` | `""` | File path of the pretrained model for the primary solver (e.g. `hrl_ac`). |
| `--pretrained_subsolver_model_path` | `""` | File path of the pretrained model for the sub-solver (e.g. `hrl_ra`). |
| `--seed` | `None` | Random seed to control and load the dataset consistently. |
| `--summary_file_name` | `global_summary.csv` | Output file name for evaluation statistics under the `save/` directory. |
