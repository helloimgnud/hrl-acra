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

def run_eval_heuristic(solver_name, shortest_method, dataset_dir, run_id_suffix, v_sim_setting_aver_arrival_rate=None):
    # 1. Get default config
    config = get_config(args=[])
    
    # 2. Override hyperparameters for heuristic solver
    config.solver_name = solver_name
    config.num_train_epochs = 0
    config.num_epochs = 1
    config.seed = 42
    config.shortest_method = shortest_method
    
    if v_sim_setting_aver_arrival_rate is not None:
        config.v_sim_setting_aver_arrival_rate = v_sim_setting_aver_arrival_rate
        config.v_sim_setting['aver_arrival_rate'] = v_sim_setting_aver_arrival_rate
        if 'arrival_rate' in config.v_sim_setting:
            config.v_sim_setting['arrival_rate']['lam'] = v_sim_setting_aver_arrival_rate
            
    # Point dataset save directories to evaluation dataset
    config.p_net_setting['save_dir'] = os.path.join(dataset_dir, 'p_net')
    config.v_sim_setting['save_dir'] = os.path.join(dataset_dir, 'v_nets')
    
    # 3. Load physical and virtual networks from evaluation dataset
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
    config.run_id = f"eval_{solver_name}_{shortest_method}_{run_id_suffix}"
    
    # 4. Build scenario manually to force loading from the pre-generated datasets
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
    
    print(f"Evaluation of {solver_name} completed successfully!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--solver_name', type=str, default='fast_hpso')
    parser.add_argument('--shortest_method', type=str, default='bfs_shortest')
    parser.add_argument('--dataset_dir', type=str, default='eval_dataset')
    parser.add_argument('--run_id_suffix', type=str, default='default')
    parser.add_argument('--v_sim_setting_aver_arrival_rate', type=float, default=None)
    args = parser.parse_args()
    
    run_eval_heuristic(
        args.solver_name, 
        args.shortest_method, 
        args.dataset_dir, 
        args.run_id_suffix, 
        v_sim_setting_aver_arrival_rate=args.v_sim_setting_aver_arrival_rate
    )
