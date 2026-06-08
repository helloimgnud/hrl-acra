import os
import glob
import yaml
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Plot final RAC and R2C across all evaluation epochs.")
    parser.add_argument(
        "run_dirs", 
        type=str, 
        help="Comma-separated paths to run directories (e.g. save/hrl_ac/run1,save/hrl_ac/run2)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="save/eval_compare_plot.png",
        help="Path to save the output plot image (default: save/eval_compare_plot.png)"
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
        
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), sharex=False)
    
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
        
        # Filter only validation/evaluation epochs
        eval_files = []
        eval_epochs = []
        k = 1
        while True:
            val_idx = k * eval_interval + k - 1
            if val_idx < len(csv_files):
                eval_files.append(csv_files[val_idx])
                eval_epochs.append(k * eval_interval)
                k += 1
            else:
                break
                
        if not eval_files:
            print(f"Warning: No evaluation epoch files found based on eval_interval {eval_interval}.")
            continue
            
        print(f"  -> Selecting {len(eval_files)} evaluation epochs: {eval_epochs}")
        
        epochs = []
        rac_values = []
        r2c_values = []
        
        for ep_idx, file_path in enumerate(eval_files):
            try:
                df = pd.read_csv(file_path)
                
                # Check for required columns
                required_cols = ['success_count', 'v_net_count', 'total_r2c']
                missing = [col for col in required_cols if col not in df.columns]
                if missing:
                    print(f"Warning: Skipping file {os.path.basename(file_path)} due to missing columns: {missing}")
                    continue
                    
                # Filter to enter events (event_type == 1) if event_type is present
                if 'event_type' in df.columns:
                    df_arr = df[df['event_type'] == 1]
                else:
                    df_arr = df
                    
                if len(df_arr) == 0:
                    print(f"Warning: File {os.path.basename(file_path)} has no arrival events.")
                    continue
                    
                final_success = df_arr['success_count'].iloc[-1]
                final_v_net = df_arr['v_net_count'].replace(0, 1).iloc[-1]
                
                rac = (final_success / final_v_net) * 100
                r2c = df_arr['total_r2c'].iloc[-1]
                
                epoch_num = eval_epochs[ep_idx]
                
                epochs.append(epoch_num)
                rac_values.append(rac)
                r2c_values.append(r2c)
                
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                continue
                
        if not epochs:
            print(f"Warning: No valid epoch data compiled for {run_dir}")
            continue
            
        color = colors[idx % len(colors)]
        
        # Plot RAC on Subplot 1
        ax1.plot(epochs, rac_values, marker='o', markersize=4, label=run_name, color=color, linewidth=1.8, alpha=0.9)
        # Plot R2C on Subplot 2
        ax2.plot(epochs, r2c_values, marker='s', markersize=4, label=run_name, color=color, linewidth=1.8, alpha=0.9)
        
        print(f"  -> Run: {run_name} | Total Eval Epochs: {len(epochs)}")
        print(f"     Final RAC: {rac_values[-1]:.2f}% | Max RAC: {max(rac_values):.2f}%")
        print(f"     Final R2C: {r2c_values[-1]:.4f} | Max R2C: {max(r2c_values):.4f}")

    # Style Subplot 1: RAC
    ax1.set_ylabel("Request Acceptance Rate (RAC) %", fontsize=11, fontweight='semibold')
    ax1.set_title("Request Acceptance Rate (RAC) over Training Epochs", fontsize=13, fontweight='bold', pad=10)
    ax1.legend(loc="best", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0')
    ax1.tick_params(labelsize=10)
    
    # Style Subplot 2: R2C
    ax2.set_xlabel("Training Epochs", fontsize=11, fontweight='semibold')
    ax2.set_ylabel("Revenue-to-Cost (R2C) Ratio", fontsize=11, fontweight='semibold')
    ax2.set_title("Revenue-to-Cost (R2C) Ratio over Training Epochs", fontsize=13, fontweight='bold', pad=10)
    ax2.legend(loc="best", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0')
    ax2.tick_params(labelsize=10)
    
    # General layout styling
    for ax in (ax1, ax2):
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
