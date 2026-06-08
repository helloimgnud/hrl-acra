import os
import argparse
import copy
import yaml
from config import get_config, save_config
from data.physical_network import PhysicalNetwork
from data.virtual_network_request_simulator import VirtualNetworkRequestSimulator
from base.loader import load_simulator
from base.scenario import BasicScenario
from base.counter import Counter
from base.controller import Controller
from base.recorder import Recorder

def run_eval(model_path, shortest_method, dataset_dir, run_id_suffix):
    # 1. Get default config
    config = get_config(args=[])
    
    # 2. Find and load config.yaml from model's run directory to replicate all training hyperparameters
    run_dir = os.path.dirname(os.path.dirname(model_path))
    config_path = os.path.join(run_dir, 'config.yaml')
    if os.path.exists(config_path):
        print(f"Loading hyperparameters from: {config_path}")
        with open(config_path, 'r') as f:
            loaded_config_dict = yaml.safe_load(f)
        for k, v in loaded_config_dict.items():
            setattr(config, k, v)
    else:
        print(f"Warning: No config.yaml found at {config_path}. Using default settings.")
        config.solver_name = 'hrl_ac'
        config.sub_solver_name = 'fast_hpso'
        config.shortest_method = shortest_method

    # 3. Override evaluation-specific settings
    config.num_train_epochs = 0
    config.num_epochs = 1
    config.seed = 42
    config.pretrained_model_path = model_path
    config.shortest_method = shortest_method
    
    # Point dataset save directories to evaluation dataset
    config.p_net_setting['save_dir'] = os.path.join(dataset_dir, 'p_net')
    config.v_sim_setting['save_dir'] = os.path.join(dataset_dir, 'v_nets')
    
    # 4. Load physical and virtual networks from evaluation dataset
    from utils import get_p_net_dataset_dir_from_setting, get_v_nets_dataset_dir_from_setting
    p_net_dir = get_p_net_dataset_dir_from_setting(config.p_net_setting)
    v_net_dir = get_v_nets_dataset_dir_from_setting(config.v_sim_setting)
    
    # Automatically detect actual directory if it exists to be robust to config parameter differences
    if not os.path.exists(p_net_dir) and os.path.exists(config.p_net_setting['save_dir']):
        subdirs = [os.path.join(config.p_net_setting['save_dir'], d) for d in os.listdir(config.p_net_setting['save_dir']) if os.path.isdir(os.path.join(config.p_net_setting['save_dir'], d))]
        if subdirs:
            p_net_dir = subdirs[0]

    if not os.path.exists(v_net_dir) and os.path.exists(config.v_sim_setting['save_dir']):
        subdirs = [os.path.join(config.v_sim_setting['save_dir'], d) for d in os.listdir(config.v_sim_setting['save_dir']) if os.path.isdir(os.path.join(config.v_sim_setting['save_dir'], d))]
        if subdirs:
            v_net_dir = subdirs[0]

    print(f"Loading Physical Network from: {p_net_dir}")
    p_net = PhysicalNetwork.load_dataset(p_net_dir)
    
    print(f"Loading Virtual Network Request Simulator from: {v_net_dir}")
    v_net_simulator = VirtualNetworkRequestSimulator.load_dataset(v_net_dir)
    
    # Define custom run ID to organize evaluation records
    config.run_id = f"eval_{shortest_method}_{run_id_suffix}"
    
    # 5. Build scenario manually to force loading from the pre-generated datasets
    counter = Counter(config.v_sim_setting['node_attrs_setting'], 
                      config.v_sim_setting['link_attrs_setting'], 
                      **vars(config))
    controller = Controller(config.v_sim_setting['node_attrs_setting'], 
                            config.v_sim_setting['link_attrs_setting'], 
                            **vars(config))
    recorder = Recorder(counter, **vars(config))
    
    Env, Solver = load_simulator(config.solver_name)
    
    # Create environment
    env = Env(p_net, v_net_simulator, controller, recorder, counter, **vars(config))
    
    # Patch env.reset to call original reset with epoch_id=None so it loads the dataset instead of renewing
    original_reset = env.reset
    def patched_reset(seed=None, epoch_id=None):
        return original_reset(seed=seed, epoch_id=None)
    env.reset = patched_reset
    
    # Create solver
    solver = Solver(controller, recorder, counter, **vars(config))
    
    # Save current config to the run directory
    if config.if_save_config:
        save_config(config)
        
    # Instantiate and run BasicScenario
    scenario = BasicScenario(env, solver, config)
    scenario.run()
    
    print(f"Evaluation of {model_path} completed successfully!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type=str, required=True)
    parser.add_argument('--shortest_method', type=str, required=True)
    parser.add_argument('--dataset_dir', type=str, default='eval_dataset')
    parser.add_argument('--run_id_suffix', type=str, required=True)
    args = parser.parse_args()
    
    run_eval(args.model_path, args.shortest_method, args.dataset_dir, args.run_id_suffix)
