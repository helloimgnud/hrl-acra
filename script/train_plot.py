import os
import argparse
import matplotlib.pyplot as plt
import numpy as np

def parse_train_summary(file_path):
    epochs = []
    rewards = []
    acceptance_rates = []
    r2c_ratios = []
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line.startswith('|') or not line.endswith('|'):
            continue
            
        parts = [p.strip().strip('*') for p in line.split('|')]
        # Drop the first and last elements (empty strings from splitting '|' at start/end)
        parts = parts[1:-1]
        
        if not parts:
            continue
            
        # Skip header and separator lines
        if parts[0].lower() == 'epoch' or parts[0].startswith(':---') or parts[0].startswith(':-'):
            continue
            
        try:
            epoch = int(parts[0])
        except ValueError:
            continue
            
        # Helper to parse float or return None
        def parse_float(val):
            val = val.strip()
            if val == 'N/A' or val == '':
                return None
            try:
                if val.endswith('%'):
                    return float(val[:-1]) / 100.0
                return float(val)
            except ValueError:
                return None
                
        # Indices in parts:
        # 0: Epoch
        # 1: Success Count
        # 2: Acceptance Rate
        # 3: Early Rejection Count
        # 4: Route Failure Count
        # 5: R2C Ratio
        # 6: Cumulative Reward
        # 7: Long-Term Avg Revenue
        # 8: Clock Time
        
        ac = parse_float(parts[2])
        r2c = parse_float(parts[5])
        reward = parse_float(parts[6])
        
        epochs.append(epoch)
        acceptance_rates.append(ac)
        r2c_ratios.append(r2c)
        rewards.append(reward)
        
    return epochs, rewards, acceptance_rates, r2c_ratios

def smooth_data(data, weight=0.6):
    """Exponential moving average smoothing."""
    if len(data) == 0:
        return []
    smoothed = []
    last = data[0]
    for point in data:
        if point is None:
            smoothed.append(None)
            continue
        if last is None:
            last = point
        smoothed_val = last * weight + (1 - weight) * point
        smoothed.append(smoothed_val)
        last = smoothed_val
    return smoothed

def filter_valid(x, y):
    valid_x = []
    valid_y = []
    for xi, yi in zip(x, y):
        if yi is not None:
            valid_x.append(xi)
            valid_y.append(yi)
    return np.array(valid_x), np.array(valid_y)

def main():
    parser = argparse.ArgumentParser(description="Plot training progress (Reward, AC, R2C) from a markdown train summary file.")
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=r"d:\HUST_file\@research\@hrl-git\hrl-acra\save\train_summary.csv",
        help="Path to the training summary file (default: save/train_summary.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=r"d:\HUST_file\@research\@hrl-git\hrl-acra\save\train_plot.png",
        help="Path to save the output plot image (default: save/train_plot.png)"
    )
    parser.add_argument(
        "--smooth-weight", "-sw",
        type=float,
        default=0.7,
        help="EMA smoothing weight between 0 and 1 (default: 0.7)"
    )
    parser.add_argument(
        "--dark",
        action="store_true",
        help="Enable modern dark mode style for the plot"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the interactive plot window"
    )
    
    args = parser.parse_args()
    
    try:
        epochs, rewards, acceptance_rates, r2c_ratios = parse_train_summary(args.file)
    except Exception as e:
        print(f"Error parsing file: {e}")
        return
        
    if not epochs:
        print("No training data found in file.")
        return
        
    # Set style
    if args.dark:
        plt.style.use('dark_background')
        bg_color = '#0f172a' # Slate 900
        axes_bg = '#1e293b' # Slate 800
        text_color = '#f8fafc'
        grid_color = '#334155'
        spine_color = '#475569'
        
        color_reward_raw = '#0ea5e9'
        color_reward_smooth = '#38bdf8'
        
        color_ac_raw = '#f43f5e'
        color_ac_smooth = '#fda4af'
        
        color_r2c_raw = '#a855f7'
        color_r2c_smooth = '#c084fc'
    else:
        plt.style.use('default')
        bg_color = '#ffffff'
        axes_bg = '#f8fafc' # Slate 50
        text_color = '#0f172a'
        grid_color = '#e2e8f0'
        spine_color = '#cbd5e1'
        
        color_reward_raw = '#3b82f6'
        color_reward_smooth = '#1d4ed8'
        
        color_ac_raw = '#ef4444'
        color_ac_smooth = '#b91c1c'
        
        color_r2c_raw = '#8b5cf6'
        color_r2c_smooth = '#6d28d9'
        
    # Configure plotting parameters
    plt.rcParams['text.color'] = text_color
    plt.rcParams['axes.labelcolor'] = text_color
    plt.rcParams['xtick.color'] = text_color
    plt.rcParams['ytick.color'] = text_color
    
    # Create subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 10), sharex=True, facecolor=bg_color)
    
    # --- Plot 1: Cumulative Reward ---
    x_rew, y_rew = filter_valid(epochs, rewards)
    if len(y_rew) > 0:
        y_rew_smooth = smooth_data(y_rew, args.smooth_weight)
        # Plot raw values
        ax1.plot(x_rew, y_rew, color=color_reward_raw, alpha=0.3, linewidth=1.5, label='Raw Reward')
        # Plot smoothed values
        ax1.plot(x_rew, y_rew_smooth, color=color_reward_smooth, linewidth=2.5, label='EMA Smoothed')
        # Annotate final/max
        final_val = y_rew[-1]
        max_val = np.max(y_rew)
        ax1.text(0.02, 0.95, f'Final: {final_val:.2f} | Max: {max_val:.2f}', 
                 transform=ax1.transAxes, verticalalignment='top', fontsize=10, fontweight='semibold',
                 bbox=dict(facecolor=axes_bg, alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'))
    ax1.set_ylabel('Cumulative Reward', fontsize=11, fontweight='bold')
    ax1.set_title('Training Progress: Cumulative Reward', fontsize=12, fontweight='bold', pad=8)
    ax1.legend(loc='lower right', frameon=True, facecolor=axes_bg, edgecolor='none')
    
    # --- Plot 2: Acceptance Rate ---
    x_ac, y_ac = filter_valid(epochs, acceptance_rates)
    if len(y_ac) > 0:
        y_ac_smooth = smooth_data(y_ac, args.smooth_weight)
        ax2.plot(x_ac, y_ac, color=color_ac_raw, alpha=0.3, linewidth=1.5, label='Raw AC')
        ax2.plot(x_ac, y_ac_smooth, color=color_ac_smooth, linewidth=2.5, label='EMA Smoothed')
        # Annotate final/max
        final_val = y_ac[-1] * 100.0  # Show as %
        max_val = np.max(y_ac) * 100.0
        ax2.text(0.02, 0.95, f'Final: {final_val:.2f}% | Max: {max_val:.2f}%', 
                 transform=ax2.transAxes, verticalalignment='top', fontsize=10, fontweight='semibold',
                 bbox=dict(facecolor=axes_bg, alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'))
        # Set y-axis to percentage formatting
        import matplotlib.ticker as mtick
        ax2.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax2.set_ylabel('Acceptance Rate', fontsize=11, fontweight='bold')
    ax2.set_title('Training Progress: Acceptance Rate (AC)', fontsize=12, fontweight='bold', pad=8)
    ax2.legend(loc='lower right', frameon=True, facecolor=axes_bg, edgecolor='none')
    
    # --- Plot 3: R2C Ratio ---
    x_r2c, y_r2c = filter_valid(epochs, r2c_ratios)
    if len(y_r2c) > 0:
        y_r2c_smooth = smooth_data(y_r2c, args.smooth_weight)
        ax3.plot(x_r2c, y_r2c, color=color_r2c_raw, alpha=0.3, linewidth=1.5, label='Raw R2C')
        ax3.plot(x_r2c, y_r2c_smooth, color=color_r2c_smooth, linewidth=2.5, label='EMA Smoothed')
        # Annotate final/max
        final_val = y_r2c[-1]
        max_val = np.max(y_r2c)
        ax3.text(0.02, 0.95, f'Final: {final_val:.4f} | Max: {max_val:.4f}', 
                 transform=ax3.transAxes, verticalalignment='top', fontsize=10, fontweight='semibold',
                 bbox=dict(facecolor=axes_bg, alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'))
    ax3.set_xlabel('Epoch', fontsize=11, fontweight='bold')
    ax3.set_ylabel('R2C Ratio', fontsize=11, fontweight='bold')
    ax3.set_title('Training Progress: R2C Ratio', fontsize=12, fontweight='bold', pad=8)
    ax3.legend(loc='lower right', frameon=True, facecolor=axes_bg, edgecolor='none')
    
    # Apply style to all subplots
    for ax in (ax1, ax2, ax3):
        ax.set_facecolor(axes_bg)
        ax.grid(True, linestyle='--', color=grid_color, alpha=0.5)
        # Despine
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color(spine_color)
        ax.spines['bottom'].set_color(spine_color)
        ax.tick_params(colors=text_color)
        
    plt.tight_layout()
    
    # Save file
    try:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        plt.savefig(args.output, dpi=300, bbox_inches='tight', facecolor=bg_color)
        print(f"Plot successfully saved to: {args.output}")
    except Exception as e:
        print(f"Error saving plot to {args.output}: {e}")
        
    if args.show:
        plt.show()

if __name__ == '__main__':
    main()
