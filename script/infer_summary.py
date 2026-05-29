import os
import pandas as pd
import numpy as np

def clean_value(val):
    val = str(val).strip().strip('*')
    if val == 'N/A' or val == '':
        return np.nan
    if val.endswith('%'):
        return float(val[:-1]) / 100.0
    if val.endswith('s') or val.startswith('~') and val.endswith('s'):
        val_clean = val.replace('~', '').replace('s', '').strip()
        try:
            return float(val_clean)
        except ValueError:
            return val
    try:
        if '.' in val:
            return float(val)
        return int(val)
    except ValueError:
        return val

def main():
    input_file = r"d:\HUST_file\@research\@hrl-git\hrl-acra\save\train_summary.csv"
    output_file = r"d:\HUST_file\@research\@hrl-git\hrl-acra\save\train_summary_clean.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return
        
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    data = []
    headers = []
    
    for line in lines:
        line = line.strip()
        if not line.startswith('|') or not line.endswith('|'):
            continue
            
        parts = [p.strip() for p in line.split('|')]
        parts = parts[1:-1] # Remove empty parts from split
        
        if not parts:
            continue
            
        # Check header
        if parts[0].lower() == 'epoch':
            headers = [h.lower().replace(' ', '_') for h in parts]
            continue
        elif parts[0].startswith(':---') or parts[0].startswith(':-'):
            continue
            
        cleaned_parts = [clean_value(p) for p in parts]
        data.append(cleaned_parts)
        
    df = pd.DataFrame(data, columns=headers)
    
    # Identify success and rejection columns
    early_reject_col = 'early_rejection_count'
    if early_reject_col not in df.columns:
        for col in df.columns:
            if 'reject' in col:
                early_reject_col = col
                break
                
    success_col = 'success_count'
    if success_col not in df.columns:
        for col in df.columns:
            if 'success' in col:
                success_col = col
                break
                
    # Calculate route_failure_count as 1000 - success_count - early_rejection_count
    df['route_failure_count'] = 1000 - df[success_col].astype(float) - df[early_reject_col].astype(float)
    
    # Save clean CSV
    df.to_csv(output_file, index=False)
    print(f"Successfully processed train_summary.csv and saved to: {output_file}")
    print("\nLast 5 rows of processed data:")
    print(df[['epoch', success_col, early_reject_col, 'route_failure_count']].tail(5))

if __name__ == '__main__':
    main()
