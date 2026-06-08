import os
import glob
import re
import argparse
import yaml
import copy
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from config import get_config, save_config
from data.physical_network import PhysicalNetwork
from data.virtual_network_request_simulator import VirtualNetworkRequestSimulator
from base.loader import load_simulator
from base.scenario import BasicScenario
from base.counter import Counter
from base.controller import Controller
from base.recorder import Recorder

def evaluate_checkpoint(config, p_net_base, v_sim_base, checkpoint_path, shortest_method):
    # Get a fresh copy of substrate and virtual network requests
    p_net = copy.deepcopy(p_net_base)
    v_net_simulator = copy.deepcopy(v_sim_base)
    
    # Configure evaluation parameters
    config.num_train_epochs = 0
    config.num_epochs = 1
    config.seed = 42
    config.pretrained_model_path = checkpoint_path
    config.shortest_method = shortest_method
    
    # Build environment and solver fresh to avoid state pollution
    counter = Counter(config.v_sim_setting['node_attrs_setting'], 
                      config.v_sim_setting['link_attrs_setting'], 
                      **vars(config))
    controller = Controller(config.v_sim_setting['node_attrs_setting'], 
                            config.v_sim_setting['link_attrs_setting'], 
                            **vars(config))
    recorder = Recorder(counter, **vars(config))
    
    Env, Solver = load_simulator(config.solver_name)
    env = Env(p_net, v_net_simulator, controller, recorder, counter, **vars(config))
    
    # Patch env.reset to load dataset instead of renewing virtual networks
    original_reset = env.reset
    def patched_reset(seed=None, epoch_id=None):
        return original_reset(seed=seed, epoch_id=None)
    env.reset = patched_reset
    
    solver = Solver(controller, recorder, counter, **vars(config))
    
    # Run the BasicScenario evaluation
    scenario = BasicScenario(env, solver, config)
    scenario.run()
    
    # Retrieve summary records
    summary_info = env.summary_records()
    return summary_info

def main():
    parser = argparse.ArgumentParser(description="Evaluate checkpoints at regular intervals and plot RAC & R2C.")
    parser.add_argument(
        "--run_dirs", 
        type=str, 
        required=True,
        help="Comma-separated paths to run directories to evaluate (e.g. save/hrl_ac/run1,save/hrl_ac/run2)"
    )
    parser.add_argument(
        "--dataset_dir", 
        type=str, 
        default="eval_dataset", 
        help="Directory of the generated evaluation dataset"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="save/checkpoints_compare_plot.png", 
        help="Path to save the comparison plot (default: save/checkpoints_compare_plot.png)"
    )
    parser.add_argument(
        "--step", 
        type=int, 
        default=2, 
        help="Checkpoint step interval, e.g. 2 evaluates model-0, model-2, model-4..."
    )
    parser.add_argument(
        "--use_existing",
        action="store_true",
        help="Reuse existing checkpoint_eval_summary.csv in the run directory instead of evaluating."
    )
    args = parser.parse_args()
    
    run_directories = [d.strip().strip("'\"") for d in args.run_dirs.split(",") if d.strip()]
    if not run_directories:
        print("Error: No valid run directories provided.")
        return
        
    results_by_run = {}
    
    for run_dir in run_directories:
        if not os.path.exists(run_dir):
            print(f"Warning: Directory not found: {run_dir}")
            continue
            
        run_name = os.path.basename(run_dir.replace('\\', '/').rstrip('/'))
        print(f"\n{'='*20} Processing run: {run_name} {'='*20}")
        
        # Check if we should use existing results
        summary_csv_path = os.path.join(run_dir, 'checkpoint_eval_summary.csv')
        if args.use_existing and os.path.exists(summary_csv_path):
            print(f"Loading existing summary results from: {summary_csv_path}")
            try:
                df_res = pd.read_csv(summary_csv_path)
                results_by_run[run_name] = df_res
                continue
            except Exception as e:
                print(f"Error loading {summary_csv_path}: {e}. Falling back to evaluation.")
        
        # 1. Load config.yaml from run directory
        config_path = os.path.join(run_dir, 'config.yaml')
        if not os.path.exists(config_path):
            print(f"Error: No config.yaml found at {config_path}")
            continue
            
        # Get base default config and overlay loaded values
        config = get_config(args=[])
        with open(config_path, 'r') as f:
            loaded_config_dict = yaml.safe_load(f)
        for k, v in loaded_config_dict.items():
            setattr(config, k, v)
            
        # Override save directories to target evaluation dataset
        config.p_net_setting['save_dir'] = os.path.join(args.dataset_dir, 'p_net')
        config.v_sim_setting['save_dir'] = os.path.join(args.dataset_dir, 'v_nets')
        
        # 2. Load base physical network and virtual networks simulator
        from utils import get_p_net_dataset_dir_from_setting, get_v_nets_dataset_dir_from_setting
        p_net_dir = get_p_net_dataset_dir_from_setting(config.p_net_setting)
        v_net_dir = get_v_nets_dataset_dir_from_setting(config.v_sim_setting)
        
        print(f"Loading Physical Network from: {p_net_dir}")
        p_net_base = PhysicalNetwork.load_dataset(p_net_dir)
        print(f"Loading Virtual Network Simulator from: {v_net_dir}")
        v_sim_base = VirtualNetworkRequestSimulator.load_dataset(v_net_dir)
        
        # 3. Locate and filter checkpoint model files
        model_dir = os.path.join(run_dir, 'model')
        pkl_files = glob.glob(os.path.join(model_dir, 'model-*.pkl'))
        checkpoint_map = {}
        for f in pkl_files:
            match = re.search(r'model-(\d+)\.pkl', os.path.basename(f))
            if match:
                checkpoint_map[int(match.group(1))] = f
                
        sorted_epochs = sorted(checkpoint_map.keys())
        selected_epochs = [e for e in sorted_epochs if e % args.step == 0]
        
        if not selected_epochs:
            print(f"No matching checkpoints found in {model_dir}")
            continue
            
        print(f"Found checkpoints: {sorted_epochs}")
        print(f"Selected for evaluation: {selected_epochs}")
        
        run_results = []
        
        # 4. Evaluate each selected checkpoint
        for epoch in selected_epochs:
            checkpoint_path = checkpoint_map[epoch]
            print(f"\n--- Evaluating Checkpoint: {os.path.basename(checkpoint_path)} ---")
            
            # Temporary change configuration run_id to avoid overwriting summary records
            config.run_id = f"eval_checkpoint_{epoch}_{config.shortest_method}"
            
            try:
                summary = evaluate_checkpoint(config, p_net_base, v_sim_base, checkpoint_path, config.shortest_method)
                rac = summary.get('acceptance_rate', 0.0) * 100.0
                r2c = summary.get('r2c_ratio', 0.0)
                print(f"Result -> RAC: {rac:.2f}%, R2C: {r2c:.4f}")
                
                run_results.append({
                    'checkpoint': epoch,
                    'rac': rac,
                    'r2c': r2c,
                    'fusion': 0.5 * (rac / 100.0) + 0.5 * r2c
                })
            except Exception as e:
                print(f"Error evaluating checkpoint {epoch}: {e}")
                
        if run_results:
            df_res = pd.DataFrame(run_results)
            # Save results to a CSV file inside the run directory for record keeping
            summary_csv_path = os.path.join(run_dir, 'checkpoint_eval_summary.csv')
            df_res.to_csv(summary_csv_path, index=False)
            print(f"Saved run evaluation summary to: {summary_csv_path}")
            
            results_by_run[run_name] = df_res

    # 5. Plotting results
    if not results_by_run:
        print("Error: No evaluation results gathered to plot.")
        return
        
    try:
        if 'seaborn-v0_8-whitegrid' in plt.style.available:
            plt.style.use('seaborn-v0_8-whitegrid')
        elif 'seaborn-whitegrid' in plt.style.available:
            plt.style.use('seaborn-whitegrid')
        else:
            plt.style.use('default')
    except Exception:
        plt.style.use('default')
        
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 13), sharex=True)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for idx, (run_name, df_res) in enumerate(results_by_run.items()):
        color = colors[idx % len(colors)]
        x = df_res['checkpoint']
        
        # Subplot 1: RAC
        ax1.plot(x, df_res['rac'], marker='o', markersize=4, label=run_name, color=color, linewidth=1.8, alpha=0.9)
        
        # Subplot 2: R2C
        ax2.plot(x, df_res['r2c'], marker='s', markersize=4, label=run_name, color=color, linewidth=1.8, alpha=0.9)
        
        # Subplot 3: Fusion Metric
        # Calculate fusion on-the-fly in case it wasn't saved in CSV previously
        if 'fusion' not in df_res.columns:
            df_res['fusion'] = 0.5 * (df_res['rac'] / 100.0) + 0.5 * df_res['r2c']
        ax3.plot(x, df_res['fusion'], marker='^', markersize=4, label=run_name, color=color, linewidth=1.8, alpha=0.9)
        
    # Style Subplot 1: RAC
    ax1.set_ylabel("Request Acceptance Rate (RAC) %", fontsize=11, fontweight='semibold')
    ax1.set_title("RAC across Model Checkpoints", fontsize=13, fontweight='bold', pad=10)
    ax1.legend(loc="best", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0')
    ax1.tick_params(labelsize=10)
    
    # Style Subplot 2: R2C
    ax2.set_ylabel("Request-to-Cost (R2C) Ratio", fontsize=11, fontweight='semibold')
    ax2.set_title("R2C Ratio across Model Checkpoints", fontsize=13, fontweight='bold', pad=10)
    ax2.legend(loc="best", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0')
    ax2.tick_params(labelsize=10)

    # Style Subplot 3: Fusion
    ax3.set_xlabel("Model Checkpoint Index (Epoch)", fontsize=11, fontweight='semibold')
    ax3.set_ylabel("Fusion Metric (0.5*RAC_ratio + 0.5*R2C)", fontsize=11, fontweight='semibold')
    ax3.set_title("Fusion Metric (0.5 * RAC_ratio + 0.5 * R2C) across Model Checkpoints", fontsize=13, fontweight='bold', pad=10)
    ax3.legend(loc="best", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0')
    ax3.tick_params(labelsize=10)
    
    for ax in (ax1, ax2, ax3):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        ax.grid(True, linestyle='--', alpha=0.6, color='#cccccc')
        
    plt.tight_layout()
    
    try:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.savefig(args.output, dpi=300, bbox_inches='tight')
        print(f"\nSuccessfully saved checkpoints comparison plot to: {args.output}")
    except Exception as e:
        print(f"Error saving plot to {args.output}: {e}")

if __name__ == '__main__':
    main()
