import os
from config import get_config
from data.generator import Generator

def main():
    # Load config with defaults
    config = get_config(args=[])
    
    # Force seed to be 42 (matching training seed)
    config.seed = 42
    
    # Change save directories to eval_dataset
    config.p_net_setting['save_dir'] = 'eval_dataset/p_net'
    config.v_sim_setting['save_dir'] = 'eval_dataset/v_nets'
    
    # Create target directories
    os.makedirs('eval_dataset/p_net', exist_ok=True)
    os.makedirs('eval_dataset/v_nets', exist_ok=True)
    
    print("Generating evaluation dataset...")
    # Generate and save
    Generator.generate_dataset(config, save=True)
    print("Evaluation dataset generated successfully!")

if __name__ == '__main__':
    main()
