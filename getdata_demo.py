"""
Extract node depth and link flow time series from SWMM .out file
Usage:
    python getdata_demo.py <rainfall_index> <node_name> <link_name>
Example:
    python getdata_demo.py 0 CC-storage CC-R1
"""

import os
import sys
import numpy as np
from swmm_api import read_out_file
from swmm_api.output_file import VARIABLES, OBJECTS

# ============================================================
# Path configuration
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'results')


def get_node_depth(out_path, node_name):
    """Extract depth time series for a specified node from .out file"""
    out = read_out_file(out_path)
    series = out.get_part(OBJECTS.NODE, node_name, VARIABLES.NODE.DEPTH)
    out.close()
    # series is a pandas Series, index is time, values are depth
    times = series.index.strftime('%Y-%m-%d %H:%M:%S').to_numpy()
    depths = series.values
    return times, depths


def get_link_flow(out_path, link_name):
    """Extract flow time series for a specified link from .out file"""
    out = read_out_file(out_path)
    series = out.get_part(OBJECTS.LINK, link_name, VARIABLES.LINK.FLOW)
    out.close()
    times = series.index.strftime('%Y-%m-%d %H:%M:%S').to_numpy()
    flows = series.values
    return times, flows


def main():
    if len(sys.argv) < 4:
        print("Usage: python getdata_demo.py <rainfall_index> <node_name> <link_name>")
        print("Example: python getdata_demo.py 0 CC-storage CC-R1")
        sys.exit(1)

    rain_idx = int(sys.argv[1])
    node_name = sys.argv[2]
    link_name = sys.argv[3]

    # Locate .out file: results/rain_XXXX/rain_XXXX.out
    folder_name = f"rain_{rain_idx:04d}"
    out_path = os.path.join(RESULTS_DIR, folder_name, f"{folder_name}.out")

    if not os.path.exists(out_path):
        print(f"Error: Cannot find out file {out_path}")
        print("Please run main_sim.py first to generate simulation results")
        sys.exit(1)

    # Save directory
    save_dir = os.path.join(RESULTS_DIR, folder_name)
    os.makedirs(save_dir, exist_ok=True)

    # Extract node depth
    print(f"Extracting depth data for node '{node_name}'...")
    times, depths = get_node_depth(out_path, node_name)
    depth_data = np.column_stack([times, depths.astype(str)])
    depth_save_path = os.path.join(save_dir, f"node_{node_name}_depth.npy")
    np.save(depth_save_path, depth_data)
    print(f"  Saved to: {depth_save_path}  (shape: {depth_data.shape})")

    # Extract link flow
    print(f"Extracting flow data for link '{link_name}'...")
    times, flows = get_link_flow(out_path, link_name)
    flow_data = np.column_stack([times, flows.astype(str)])
    flow_save_path = os.path.join(save_dir, f"link_{link_name}_flow.npy")
    np.save(flow_save_path, flow_data)
    print(f"  Saved to: {flow_save_path}  (shape: {flow_data.shape})")

    print("Done!")


if __name__ == '__main__':
    main()
