import os
import shutil
import numpy as np
import sys

# Ensure root path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.virtual_network_request_simulator import VirtualNetworkRequestSimulator
from data.utils import generate_data_with_distribution
from utils import get_v_nets_dataset_dir_from_setting

def main():
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../eval_dataset_ar_006'))
    dst_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../eval_dataset_ar_004'))

    print(f"Source directory: {src_dir}")
    print(f"Target directory: {dst_dir}")

    # 1. Copy physical network
    src_p_net = os.path.join(src_dir, 'p_net')
    dst_p_net = os.path.join(dst_dir, 'p_net')
    if os.path.exists(dst_p_net):
        shutil.rmtree(dst_p_net)
    shutil.copytree(src_p_net, dst_p_net)
    print("Copied physical network dataset.")

    # 2. Load the virtual network simulator from the source dataset
    src_v_nets_dir = os.path.join(src_dir, 'v_nets', '1000-[2-10]-random-1000-0.06-cpu_[5-50]-bw_[5-50]')
    print(f"Loading virtual network simulator from: {src_v_nets_dir}")
    v_net_simulator = VirtualNetworkRequestSimulator.load_dataset(src_v_nets_dir)

    # 3. Update arrival rate config and save path
    v_net_simulator.v_sim_setting['arrival_rate']['lam'] = 0.04
    v_net_simulator.v_sim_setting['save_dir'] = os.path.join(dst_dir, 'v_nets')

    # 4. Generate new arrival times using the same random seed (42) to keep RNG stream aligned
    # We consume the exact same number of random draws for v_net_size and lifetime
    # to guarantee the arrival times align perfectly with what the generator produces.
    np.random.seed(42)
    _ = generate_data_with_distribution(size=v_net_simulator.num_v_nets, **v_net_simulator.v_sim_setting['v_net_size'])
    _ = generate_data_with_distribution(size=v_net_simulator.num_v_nets, **v_net_simulator.v_sim_setting['lifetime'])
    
    arrival_time_interval = generate_data_with_distribution(
        size=v_net_simulator.num_v_nets,
        **v_net_simulator.v_sim_setting['arrival_rate']
    )
    v_nets_arrival_time = np.cumsum(arrival_time_interval)

    # 5. Overwrite the arrival_time of each v_net to keep graphs, sizes, and lifetimes identical
    for i, v_net in enumerate(v_net_simulator.v_nets):
        v_net.arrival_time = float(v_nets_arrival_time[i])

    # 6. Rebuild events based on the new arrival times
    v_net_simulator.renew_events()

    # 7. Save the new dataset
    os.makedirs(os.path.join(dst_dir, 'v_nets'), exist_ok=True)
    dst_v_nets_dir = get_v_nets_dataset_dir_from_setting(v_net_simulator.v_sim_setting)
    v_net_simulator.save_dataset(dst_v_nets_dir)

    print("Successfully generated and saved new virtual network request dataset!")
    print(f"New dataset path: {dst_v_nets_dir}")

if __name__ == '__main__':
    main()
