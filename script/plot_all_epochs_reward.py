import os
import glob
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Plot continuous step-by-step reward across all training epochs.")
    parser.add_argument(
        "run_dirs", 
        type=str, 
        help="Comma-separated paths to run directories (e.g. save/hrl_ac/run1,save/hrl_ac/run2)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="all_epochs_reward_plot.png",
        help="Path to save the output plot image"
    )
    parser.add_argument(
        "--metric", "-m",
        type=str,
        default="cumulative_reward",
        choices=["cumulative_reward", "actual_reward", "actual_cumulative_reward", "v_net_reward"],
        help="The reward metric to plot (default: cumulative_reward)"
    )
    parser.add_argument(
        "--cumsum",
        action="store_true",
        help="Calculate the continuous cumulative sum of the selected metric"
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
        
    fig, ax = plt.subplots(figsize=(12, 7))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, run_dir in enumerate(run_directories):
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
        print(f"Processing run: {run_name} | Found {len(csv_files)} epoch files")
        
        all_rewards = []
        
        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                
                # Check metric column
                if args.metric not in df.columns:
                    print(f"Warning: Skipping file {os.path.basename(file_path)} due to missing column {args.metric}.")
                    continue
                
                # Filter events if event_type exists
                if 'event_type' in df.columns:
                    df_arr = df[df['event_type'] == 1]
                else:
                    df_arr = df
                
                rewards = df_arr[args.metric].values
                all_rewards.extend(rewards)
                
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue
                
        if not all_rewards:
            print(f"Warning: No data compiled for {run_dir} with metric {args.metric}")
            continue
            
        # Convert to numpy array and calculate continuous cumulative sum if requested
        all_rewards = np.array(all_rewards)
        if args.cumsum:
            plot_values = np.cumsum(all_rewards)
            y_label = f"Continuous Cumulative {args.metric.replace('_', ' ').title()}"
        else:
            plot_values = all_rewards
            y_label = args.metric.replace('_', ' ').title()
        
        x = range(1, len(plot_values) + 1)
        label = run_name
        color = colors[i % len(colors)]
        
        ax.plot(x, plot_values, label=label, color=color, linewidth=1.2, alpha=0.9)
        
        print(f"  -> Run: {label} | Total VNR Steps: {len(plot_values)} | Final Value: {plot_values[-1]:.2f}")
        
    ax.set_ylabel(y_label, fontsize=12, fontweight='semibold')
    ax.set_xlabel("Total Arrived VNR Count (All Epochs Combined)", fontsize=12, fontweight='semibold')
    ax.set_title(f"Step-by-Step {args.metric.replace('_', ' ').title()} over All Epochs", fontsize=14, fontweight='bold', pad=15)
    
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
        print(f"\nSuccessfully saved plot to: {args.output}")
    except Exception as e:
        print(f"Error saving plot to {args.output}: {e}")
        
    if args.show:
        plt.show()

if __name__ == "__main__":
    main()
