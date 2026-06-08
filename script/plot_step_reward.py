import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser(description="Plot step-by-step reward (cumulative or individual) over an evaluation episode.")
    parser.add_argument(
        "files", 
        type=str, 
        help="Comma-separated paths to record CSV files (e.g. path/to/1.csv,path/to/2.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="step_reward_plot.png",
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
        "--filter-arrivals",
        action="store_true",
        default=True,
        help="Plot only request arrival events (event_type == 1) (default: True)"
    )
    parser.add_argument(
        "--no-filter",
        action="store_false",
        dest="filter_arrivals",
        help="Disable request arrival filtering and plot all raw events (Enter & Leave)"
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
    
    file_paths = [f.strip().strip("'\"") for f in args.files.split(",") if f.strip()]
    
    if not file_paths:
        print("Error: No valid file paths provided.")
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
    
    for i, file_path in enumerate(file_paths):
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            continue
            
        print(f"Processing file: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            
            if args.metric not in df.columns:
                print(f"Error: Metric '{args.metric}' not found in CSV. Available columns: {list(df.columns)}")
                continue
                
            # Filter events if specified
            if args.filter_arrivals and 'event_type' in df.columns:
                df_plot = df[df['event_type'] == 1]
            else:
                df_plot = df
                
            y = df_plot[args.metric].values
            x = range(1, len(df_plot) + 1)
            
            label = os.path.basename(file_path)
            color = colors[i % len(colors)]
            
            ax.plot(x, y, label=label, color=color, linewidth=1.5, alpha=0.85)
            
            print(f"  -> File: {label} | Plotted steps: {len(df_plot)} | Final {args.metric}: {y[-1]:.4f}")
            
        except Exception as e:
            print(f"Error plotting {file_path}: {e}")
            continue
            
    ax.set_ylabel(args.metric.replace('_', ' ').title(), fontsize=12, fontweight='semibold')
    xlabel = "Arrived VNR Count (Steps)" if args.filter_arrivals else "Event Count (Steps)"
    ax.set_xlabel(xlabel, fontsize=12, fontweight='semibold')
    ax.set_title(f"Step-by-Step {args.metric.replace('_', ' ').title()} over Evaluation Episode", fontsize=14, fontweight='bold', pad=15)
    
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
