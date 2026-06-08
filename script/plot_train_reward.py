import os
import glob
import yaml
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def smooth_data(data, weight=0.6):
    """Exponential moving average smoothing."""
    if len(data) == 0:
        return []
    smoothed = []
    last = data[0]
    for point in data:
        if pd.isna(point):
            smoothed.append(None)
            continue
        if last is None or pd.isna(last):
            last = point
        smoothed_val = last * weight + (1 - weight) * point
        smoothed.append(smoothed_val)
        last = smoothed_val
    return smoothed

def main():
    parser = argparse.ArgumentParser(description="Plot final cumulative reward across all training epochs.")
    parser.add_argument(
        "run_dirs", 
        type=str, 
        help="Comma-separated paths to run directories (e.g. save/hrl_ac/run1,save/hrl_ac/run2)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="save/train_reward_compare_plot.png",
        help="Path to save the output plot image (default: save/train_reward_compare_plot.png)"
    )
    parser.add_argument(
        "--metric", "-m",
        type=str,
        default="cumulative_reward",
        choices=["cumulative_reward", "actual_cumulative_reward", "global_cumulative_reward"],
        help="The reward metric to plot (default: cumulative_reward)"
    )
    parser.add_argument(
        "--smooth-weight", "-sw",
        type=float,
        default=0.6,
        help="EMA smoothing weight between 0 and 1 (default: 0.6). Set to 0 to disable smoothing."
    )
    parser.add_argument(
        "--grid", 
        action="store_true", 
        default=True, 
        help="Show grid on the plots (default: True)"
    )
    parser.add_argument(
        "--show", 
        action="store_true", 
        help="Display the plot window interactively"
    )
    
    args = parser.parse_args()
    
    run_directories = [d.strip().strip("'\"") for d in args.run_dirs.split(",") if d.strip()]
    
    if not run_directories:
        print("Error: No valid run directories provided.")
        return

    # Set up clean plotting style
    try:
        if 'seaborn-v0_8-whitegrid' in plt.style.available:
            plt.style.use('seaborn-v0_8-whitegrid')
        elif 'seaborn-whitegrid' in plt.style.available:
            plt.style.use('seaborn-whitegrid')
        else:
            plt.style.use('default')
    except Exception:
        plt.style.use('default')
        
    fig, ax = plt.subplots(figsize=(11, 7))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for idx, run_dir in enumerate(run_directories):
        if not os.path.exists(run_dir):
            print(f"Warning: Directory not found: {run_dir}")
            continue
            
        records_dir = os.path.join(run_dir, 'records')
        if not os.path.exists(records_dir):
            print(f"Warning: records directory not found under: {run_dir}")
            continue
            
        # Find all CSV files except temp files
        csv_files = glob.glob(os.path.join(records_dir, "*.csv"))
        csv_files = [f for f in csv_files if "temp-" not in os.path.basename(f)]
        
        if not csv_files:
            print(f"Warning: No record CSV files found in {records_dir}")
            continue
            
        # Sort files alphabetically to ensure chronological order by timestamp
        csv_files.sort()
        
        run_name = os.path.basename(run_dir.replace('\\', '/').rstrip('/'))
        
        # Load eval_interval from config.yaml if available
        eval_interval = 10
        config_path = os.path.join(run_dir, 'config.yaml')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config and 'eval_interval' in config:
                        eval_interval = config['eval_interval']
            except Exception as e:
                print(f"Warning: Could not read config.yaml for eval_interval: {e}")
                
        print(f"Processing run: {run_name} | Found {len(csv_files)} total epoch files | eval_interval: {eval_interval}")
        
        # Exclude validation indices
        val_indices = set()
        k = 1
        while True:
            val_idx = k * eval_interval + k - 1
            if val_idx < len(csv_files):
                val_indices.add(val_idx)
                k += 1
            else:
                break
                
        train_files = []
        train_epochs = []
        train_epoch_num = 0
        for i, file_path in enumerate(csv_files):
            if i in val_indices:
                continue
            train_files.append(file_path)
            train_epochs.append(train_epoch_num)
            train_epoch_num += 1
            
        if not train_files:
            print(f"Warning: No training epoch files found for {run_dir}")
            continue
            
        print(f"  -> Selecting {len(train_files)} training epochs: {train_epochs[0]} to {train_epochs[-1]}")
        
        epochs = []
        reward_values = []
        
        for ep_idx, file_path in enumerate(train_files):
            try:
                df = pd.read_csv(file_path)
                
                # Check for required columns
                if args.metric not in df.columns:
                    print(f"Warning: Skipping file {os.path.basename(file_path)} due to missing column: {args.metric}")
                    continue
                    
                if len(df) == 0:
                    print(f"Warning: File {os.path.basename(file_path)} is empty.")
                    continue
                    
                final_reward = df[args.metric].iloc[-1]
                
                epoch_num = train_epochs[ep_idx]
                
                epochs.append(epoch_num)
                reward_values.append(final_reward)
                
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue
                
        if not epochs:
            print(f"Warning: No valid training epoch data compiled for {run_dir}")
            continue
            
        color = colors[idx % len(colors)]
        
        # Plot reward vs epoch (smoothed and raw)
        if args.smooth_weight > 0 and len(reward_values) > 1:
            smoothed_values = smooth_data(reward_values, args.smooth_weight)
            # Plot raw with high transparency
            ax.plot(epochs, reward_values, color=color, alpha=0.25, linewidth=1.0, linestyle='-')
            # Plot smoothed with thicker line
            ax.plot(epochs, smoothed_values, marker='o', markersize=3, label=f"{run_name} (EMA smoothed)", color=color, linewidth=2.0, alpha=0.95)
        else:
            ax.plot(epochs, reward_values, marker='o', markersize=3, label=run_name, color=color, linewidth=1.5, alpha=0.9)
        
        print(f"  -> Run: {run_name} | Total Train Epochs: {len(epochs)}")
        print(f"     Final Reward: {reward_values[-1]:.2f} | Max Reward: {max(reward_values):.2f} (at epoch {epochs[np.argmax(reward_values)]})")

    # Style Plot
    metric_label = args.metric.replace('_', ' ').title()
    ax.set_xlabel("Training Epoch", fontsize=11, fontweight='semibold')
    ax.set_ylabel(f"Final {metric_label}", fontsize=11, fontweight='semibold')
    title_suffix = f" (EMA Smooth: {args.smooth_weight})" if args.smooth_weight > 0 else ""
    ax.set_title(f"Training Epoch vs Final {metric_label}{title_suffix}", fontsize=13, fontweight='bold', pad=10)
    ax.legend(loc="best", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0')
    ax.tick_params(labelsize=10)
    
    # Despine
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    if args.grid:
        ax.grid(True, linestyle='--', alpha=0.6, color='#cccccc')
        
    plt.tight_layout()
    
    # Save the figure
    try:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.savefig(args.output, dpi=300, bbox_inches='tight')
        print(f"\nSuccessfully saved comparison plot to: {args.output}")
    except Exception as e:
        print(f"Error saving plot to {args.output}: {e}")
        
    if args.show:
        plt.show()

if __name__ == "__main__":
    main()
