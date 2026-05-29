import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Plot training request outcomes (Success, Rejection, Failure) over epochs.")
    parser.add_argument(
        "--file", "-f",
        type=str,
        default=r"d:\HUST_file\@research\@hrl-git\hrl-acra\save\train_summary_clean.csv",
        help="Path to the clean summary CSV file (default: save/train_summary_clean.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=r"d:\HUST_file\@research\@hrl-git\hrl-acra\save\train_breakdown_plot.png",
        help="Path to save the output plot image (default: save/train_breakdown_plot.png)"
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
        
    # Drop rows where any of the key counts are missing (e.g. the in-progress epoch)
    df_clean = df.dropna(subset=['success_count', 'early_rejection_count', 'route_failure_count']).reset_index(drop=True)
    
    if len(df_clean) == 0:
        print("Error: No complete rows found to plot.")
        return
        
    epochs = df_clean['epoch'].values
    successes = df_clean['success_count'].values
    rejections = df_clean['early_rejection_count'].values
    failures = df_clean['route_failure_count'].values
    
    # Set style
    if args.dark:
        plt.style.use('dark_background')
        bg_color = '#0f172a' # Slate 900
        axes_bg = '#1e293b' # Slate 800
        text_color = '#f8fafc'
        grid_color = '#334155'
        spine_color = '#475569'
        
        color_success = '#10b981'   # Emerald
        color_rejection = '#f59e0b' # Amber
        color_failure = '#ef4444'   # Rose/Red
    else:
        plt.style.use('default')
        bg_color = '#ffffff'
        axes_bg = '#f8fafc' # Slate 50
        text_color = '#0f172a'
        grid_color = '#e2e8f0'
        spine_color = '#cbd5e1'
        
        color_success = '#059669'   # Darker Emerald
        color_rejection = '#d97706' # Darker Amber
        color_failure = '#dc2626'   # Darker Red
        
    plt.rcParams['text.color'] = text_color
    plt.rcParams['axes.labelcolor'] = text_color
    plt.rcParams['xtick.color'] = text_color
    plt.rcParams['ytick.color'] = text_color
    
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=bg_color)
    ax.set_facecolor(axes_bg)
    
    # Stacked Area Plot
    # Success at the bottom, Rejection in the middle, and Failure at the top
    y = np.vstack((successes, rejections, failures))
    
    labels = ['Successes', 'Early Rejections', 'Route Failures']
    colors = [color_success, color_rejection, color_failure]
    
    ax.stackplot(epochs, y, labels=labels, colors=colors, alpha=0.85)
    
    # Configure axes
    ax.set_xlim(epochs.min(), epochs.max())
    ax.set_ylim(0, 1000)
    
    ax.set_xlabel('Epoch', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel('Request Outcome Count (Total: 1000)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_title('Training Request Outcomes Breakdown over Epochs', fontsize=14, fontweight='bold', pad=15)
    
    # Legend
    ax.legend(loc='upper right', frameon=True, facecolor=axes_bg, edgecolor='none', fontsize=10)
    
    # Custom Grid
    ax.grid(True, linestyle='--', color=grid_color, alpha=0.5)
    
    # Despine
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(spine_color)
    ax.spines['bottom'].set_color(spine_color)
    
    # Add text annotations for final epoch values
    final_success = successes[-1]
    final_rejection = rejections[-1]
    final_failure = failures[-1]
    
    stats_text = (
        f"Final Epoch ({int(epochs[-1])}) Breakdown:\n"
        f"• Successes: {int(final_success)} ({final_success/10:.1f}%)\n"
        f"• Rejections: {int(final_rejection)} ({final_rejection/10:.1f}%)\n"
        f"• Failures: {int(final_failure)} ({final_failure/10:.1f}%)"
    )
    
    # Position text box in the upper left
    ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, 
            verticalalignment='top', fontsize=11, fontweight='semibold',
            bbox=dict(facecolor=axes_bg, alpha=0.9, edgecolor='none', boxstyle='round,pad=0.5'))
            
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
