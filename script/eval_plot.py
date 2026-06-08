import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser(description="Plot evaluation records from HRL-ACRA CSV files.")
    parser.add_argument(
        "files", 
        type=str, 
        help="Comma-separated paths to evaluation CSV files (e.g. path/to/1,path/to/2)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="eval_plot.png", 
        help="Path to save the output plot image (default: eval_plot.png)"
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
    
    # Split files argument by comma and strip whitespaces/quotes
    file_paths = [f.strip().strip("'\"") for f in args.files.split(",") if f.strip()]
    
    if not file_paths:
        print("Error: No valid file paths provided.")
        return

    # Use a clean, modern plot style if available
    try:
        if 'seaborn-v0_8-whitegrid' in plt.style.available:
            plt.style.use('seaborn-v0_8-whitegrid')
        elif 'seaborn-whitegrid' in plt.style.available:
            plt.style.use('seaborn-whitegrid')
        else:
            plt.style.use('default')
    except Exception:
        plt.style.use('default')
    
    # Create the figure with 2 subplots (stacked vertically, sharing x-axis)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    
    # Define a clean color palette (modern, readable colors)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, file_path in enumerate(file_paths):
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            continue
            
        print(f"Processing file: {file_path}")
        try:
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Check required columns
            required_cols = ['success_count', 'v_net_count', 'total_r2c']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                print(f"Error: File {file_path} is missing required columns: {missing}")
                continue

            # Filter to keep only request arrival (Enter) events if 'event_type' is present
            if 'event_type' in df.columns:
                df_arrivals = df[df['event_type'] == 1]
            else:
                df_arrivals = df

            # Calculate RAC = (success_count / v_net_count) * 100
            # Handle division by zero safely
            total_ac = (df_arrivals['success_count'] / df_arrivals['v_net_count'].replace(0, 1)) * 100
            total_ac = total_ac.fillna(0)
            
            total_r2c = df_arrivals['total_r2c'].fillna(0)
            
            # Legend label is the filename (basename)
            label = os.path.basename(file_path)
            color = colors[i % len(colors)]
            
            # X-axis is the arriving requests sequence
            x = range(1, len(df_arrivals) + 1)
            
            # Plot Total AC
            ax1.plot(x, total_ac, label=label, color=color, linewidth=1.8, alpha=0.9)
            
            # Plot Total R2C
            ax2.plot(x, total_r2c, label=label, color=color, linewidth=1.8, alpha=0.9)
            
            # Print basic stats for convenience
            if len(df_arrivals) > 0:
                print(f"  -> File: {label} | Total Arrivals: {len(df_arrivals)}")
                print(f"     Final RAC: {total_ac.iloc[-1]:.2f}% | Max RAC: {total_ac.max():.2f}%")
                print(f"     Final Total R2C: {total_r2c.iloc[-1]:.4f} | Max Total R2C: {total_r2c.max():.4f}")
                
        except Exception as e:
            print(f"Error reading or plotting {file_path}: {e}")
            continue

    # Style Subplot 1: RAC
    ax1.set_ylabel("Request Acceptance Rate (RAC) %", fontsize=11, fontweight='semibold')
    ax1.set_title("Evaluation Results: RAC over Time", fontsize=13, fontweight='bold', pad=10)
    ax1.legend(loc="best", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0')
    ax1.tick_params(labelsize=10)
    
    # Style Subplot 2: Total R2C
    ax2.set_xlabel("Experiment Time (Arrived VNR Count)", fontsize=11, fontweight='semibold')
    ax2.set_ylabel("Total R2C Ratio", fontsize=11, fontweight='semibold')
    ax2.set_title("Evaluation Results: Total R2C over Time", fontsize=13, fontweight='bold', pad=10)
    ax2.legend(loc="best", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0')
    ax2.tick_params(labelsize=10)
    
    # General layout styling
    for ax in (ax1, ax2):
        # Despine for a cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        # Grid settings
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
        
    # If show option is set, display the interactive window
    if args.show:
        plt.show()

if __name__ == "__main__":
    main()
