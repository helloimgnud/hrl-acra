import pandas as pd
import numpy as np

path = "save/nrm_rank/eval_nrm_rank_bfs_shortest_manual/records/nrm_rank-eval_nrm_rank_bfs_shortest_manual-20260605T164011.csv"
try:
    df = pd.read_csv(path)
    last_row = df.iloc[-1]
    success_count = last_row['success_count']
    v_net_count = last_row['v_net_count']
    rac = (success_count / v_net_count) * 100
    
    # Calculate R2C
    total_revenue = last_row['total_revenue']
    total_cost = last_row['total_cost']
    r2c = total_revenue / total_cost if total_cost > 0 else last_row.get('r2c_ratio', 0.0)
    
    fusion = 0.5 * (rac / 100.0) + 0.5 * r2c
    
    print(f"Success Count: {success_count} / {v_net_count}")
    print(f"RAC: {rac:.2f}%")
    print(f"R2C: {r2c:.4f}")
    print(f"Fusion: {fusion:.4f}")
except Exception as e:
    print("Error:", e)
