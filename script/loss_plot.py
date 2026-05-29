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
    parser = argparse.ArgumentParser(description="Plot policy loss and critic value over update time.")
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=r"d:\HUST_file\@research\@hrl-git\hrl-acra\save\training_info_all.csv",
        help="Path to the training info CSV file (default: save/training_info_all.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=r"d:\HUST_file\@research\@hrl-git\hrl-acra\save\loss_plot.png",
        help="Path to save the output plot image (default: save/loss_plot.png)"
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
    
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return
        
    try:
        df = pd.read_csv(args.file)
    except Exception as e:
        print(f"Error reading file: {e}")
        return
        
    required_cols = ['update_time', 'loss/actor_loss', 'value/value', 'value/return']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Error: Missing required columns in CSV: {missing}")
        return
        
    # Sort by update_time to ensure chronological order
    df = df.sort_values(by='update_time').reset_index(drop=True)
    
    x = df['update_time'].values
    policy_loss = df['loss/actor_loss'].values
    critic_value = df['value/value'].values
    target_return = df['value/return'].values
    
    # Set style
    if args.dark:
        plt.style.use('dark_background')
        bg_color = '#0f172a' # Slate 900
        axes_bg = '#1e293b' # Slate 800
        text_color = '#f8fafc'
        grid_color = '#334155'
        spine_color = '#475569'
        
        color_ploss_raw = '#f43f5e'
        color_ploss_smooth = '#fda4af'
        
        color_val_raw = '#38bdf8'
        color_val_smooth = '#0ea5e9'
        
        color_ret_raw = '#c084fc'
        color_ret_smooth = '#a855f7'
    else:
        plt.style.use('default')
        bg_color = '#ffffff'
        axes_bg = '#f8fafc' # Slate 50
        text_color = '#0f172a'
        grid_color = '#e2e8f0'
        spine_color = '#cbd5e1'
        
        color_ploss_raw = '#ef4444'
        color_ploss_smooth = '#b91c1c'
        
        color_val_raw = '#3b82f6'
        color_val_smooth = '#1d4ed8'
        
        color_ret_raw = '#8b5cf6'
        color_ret_smooth = '#6d28d9'
        
    # Configure plotting parameters
    plt.rcParams['text.color'] = text_color
    plt.rcParams['axes.labelcolor'] = text_color
    plt.rcParams['xtick.color'] = text_color
    plt.rcParams['ytick.color'] = text_color
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True, facecolor=bg_color)
    
    # --- Plot 1: Policy Loss ---
    pl_smooth = smooth_data(policy_loss, args.smooth_weight)
    ax1.plot(x, policy_loss, color=color_ploss_raw, alpha=0.3, linewidth=1.5, label='Raw Policy Loss')
    ax1.plot(x, pl_smooth, color=color_ploss_smooth, linewidth=2.5, label='EMA Smoothed')
    
    final_pl = policy_loss[-1]
    min_pl = np.min(policy_loss)
    max_pl = np.max(policy_loss)
    ax1.text(0.02, 0.95, f'Final: {final_pl:.4f} | Min: {min_pl:.4f} | Max: {max_pl:.4f}', 
             transform=ax1.transAxes, verticalalignment='top', fontsize=10, fontweight='semibold',
             bbox=dict(facecolor=axes_bg, alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'))
             
    ax1.set_ylabel('Policy Loss (Actor)', fontsize=11, fontweight='bold')
    ax1.set_title('Policy Loss (Actor Loss) over Updates', fontsize=12, fontweight='bold', pad=8)
    ax1.legend(loc='lower right', frameon=True, facecolor=axes_bg, edgecolor='none')
    
    # --- Plot 2: Critic Value & Return ---
    val_smooth = smooth_data(critic_value, args.smooth_weight)
    ret_smooth = smooth_data(target_return, args.smooth_weight)
    
    ax2.plot(x, critic_value, color=color_val_raw, alpha=0.3, linewidth=1.5, label='Raw Value')
    ax2.plot(x, val_smooth, color=color_val_smooth, linewidth=2.5, label='EMA Smoothed Value')
    
    ax2.plot(x, target_return, color=color_ret_raw, alpha=0.2, linewidth=1.5, label='Raw Return')
    ax2.plot(x, ret_smooth, color=color_ret_smooth, linewidth=2.0, linestyle='--', label='EMA Smoothed Return')
    
    final_val = critic_value[-1]
    final_ret = target_return[-1]
    ax2.text(0.02, 0.95, f'Final Value: {final_val:.4f} | Final Return: {final_ret:.4f}', 
             transform=ax2.transAxes, verticalalignment='top', fontsize=10, fontweight='semibold',
             bbox=dict(facecolor=axes_bg, alpha=0.8, edgecolor='none', boxstyle='round,pad=0.3'))
             
    ax2.set_xlabel('Update Time (Optimization Step)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Critic Value / Return', fontsize=11, fontweight='bold')
    ax2.set_title('Critic Value Prediction vs Target Return', fontsize=12, fontweight='bold', pad=8)
    ax2.legend(loc='lower right', frameon=True, facecolor=axes_bg, edgecolor='none')
    
    # Apply style to both subplots
    for ax in (ax1, ax2):
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
