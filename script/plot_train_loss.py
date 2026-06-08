import os
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
    parser = argparse.ArgumentParser(description="Plot policy and critic losses across specified run directories.")
    parser.add_argument(
        "run_dirs", 
        type=str, 
        help="Comma-separated paths to run directories (e.g. save/hrl_ac/run1,save/hrl_ac/run2)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="save/train_loss_compare_plot.png",
        help="Path to save the output plot image (default: save/train_loss_compare_plot.png)"
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
        
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), sharex=True)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for idx, run_dir in enumerate(run_directories):
        if not os.path.exists(run_dir):
            print(f"Warning: Directory not found: {run_dir}")
            continue
            
        log_file = os.path.join(run_dir, 'log', 'training_info.csv')
        if not os.path.exists(log_file):
            print(f"Warning: training_info.csv not found under: {os.path.join(run_dir, 'log')}")
            continue
            
        run_name = os.path.basename(run_dir.replace('\\', '/').rstrip('/'))
        print(f"Processing run: {run_name} | Reading: {log_file}")
        
        try:
            df = pd.read_csv(log_file)
            
            # Check required columns
            required_cols = ['update_time', 'loss/actor_loss', 'loss/critic_loss']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                print(f"Warning: Skipping {run_name} due to missing columns: {missing}")
                continue
                
            # Sort by update_time
            df = df.sort_values(by='update_time').reset_index(drop=True)
            
            x = df['update_time'].values
            actor_loss = df['loss/actor_loss'].values
            critic_loss = df['loss/critic_loss'].values
            
            color = colors[idx % len(colors)]
            
            # --- Plot Actor Loss (ax1) ---
            if args.smooth_weight > 0 and len(actor_loss) > 1:
                actor_smooth = smooth_data(actor_loss, args.smooth_weight)
                ax1.plot(x, actor_loss, color=color, alpha=0.15, linewidth=1.0, linestyle='-')
                ax1.plot(x, actor_smooth, label=f"{run_name} (EMA smoothed)", color=color, linewidth=2.0, alpha=0.95)
            else:
                ax1.plot(x, actor_loss, label=run_name, color=color, linewidth=1.5, alpha=0.9)
                
            # --- Plot Critic Loss (ax2) ---
            if args.smooth_weight > 0 and len(critic_loss) > 1:
                critic_smooth = smooth_data(critic_loss, args.smooth_weight)
                ax2.plot(x, critic_loss, color=color, alpha=0.15, linewidth=1.0, linestyle='-')
                ax2.plot(x, critic_smooth, label=f"{run_name} (EMA smoothed)", color=color, linewidth=2.0, alpha=0.95)
            else:
                ax2.plot(x, critic_loss, label=run_name, color=color, linewidth=1.5, alpha=0.9)
                
            print(f"  -> Run: {run_name} | Total updates: {len(x)}")
            print(f"     Final Actor Loss: {actor_loss[-1]:.4f} | Min Actor Loss: {np.min(actor_loss):.4f}")
            print(f"     Final Critic Loss: {critic_loss[-1]:.4f} | Min Critic Loss: {np.min(critic_loss):.4f}")
            
        except Exception as e:
            print(f"Error reading or plotting {log_file}: {e}")
            continue

    # Style Subplot 1: Actor Loss
    ax1.set_ylabel("Actor Loss (Policy)", fontsize=11, fontweight='semibold')
    ax1.set_title("Policy Loss (Actor Loss) over Updates", fontsize=13, fontweight='bold', pad=10)
    ax1.legend(loc="best", frameon=True, shadow=False, facecolor='white', edgecolor='#e0e0e0')
    ax1.tick_params(labelsize=10)
    
    # Style Subplot 2: Critic Loss
    ax2.set_xlabel("Update Step", fontsize=11, fontweight='semibold')
    ax2.set_ylabel("Critic Loss (MSE)", fontsize=11, fontweight='semibold')
    title_suffix = f" (EMA Smooth: {args.smooth_weight})" if args.smooth_weight > 0 else ""
    ax2.set_title(f"Value Function Loss (Critic Loss) over Updates{title_suffix}", fontsize=13, fontweight='bold', pad=10)
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
