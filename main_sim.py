"""
SWMM batch simulation script
1. Read chaohu.inp
2. Load raindata.npy (1000 rainfall events)
3. Insert each rainfall event into inp and simulate
4. Save results to results/, one folder per rainfall event
"""

import os
import datetime
import numpy as np
from pyswmm import Simulation, Links, Nodes
from swmm_api.input_file import read_inp_file
from swmm_api.input_file.sections.others import TimeseriesData
from swmm_api.input_file.section_labels import TIMESERIES

# ============================================================
# Path configuration
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INP_PATH = os.path.join(BASE_DIR, 'chaohu.inp')
RAIN_PATH = os.path.join(BASE_DIR, 'raindata.npy')
TEMP_DIR = os.path.join(BASE_DIR, '_temp_inp')

RAINFALL_TIMESTEP_MIN = 1  # Rainfall timestep (minutes), consistent with RAINGAGES interval
EXTRA_MIN_BEFORE = 60      # Minutes to simulate before rainfall starts
EXTRA_MIN_AFTER = 60       # Minutes to simulate after rainfall ends


# ============================================================
# 1. Load rainfall data
# ============================================================
print("Loading rainfall data...")
rain_data = np.load(RAIN_PATH, allow_pickle=True)
num_rains = rain_data.shape[0]
num_steps = rain_data.shape[1]
print(f"  {num_rains} rainfall events, {num_steps} timesteps each")


# ============================================================
# 2. Helper functions
# ============================================================
def parse_rain_start_time(rain_2d):
    """Parse rainfall start time from the first row of rainfall data"""
    time_str = str(rain_2d[0, 0])
    return datetime.datetime.strptime(time_str, '%m/%d/%Y %H:%M:%S')


def build_rainfall_timeseries(rain_2d):
    """Convert a (120, 2) rainfall array from raindata to TimeseriesData"""
    data_list = []
    for row in rain_2d:
        time_str = str(row[0])
        value = float(row[1])
        dt = datetime.datetime.strptime(time_str, '%m/%d/%Y %H:%M:%S')
        data_list.append((dt, value))
    return TimeseriesData('rainfall', data_list)


def modify_inp_for_rain(inp_path, rain_2d, temp_inp_path):
    """
    Modify inp file for a given rainfall event:
    - Replace TIMESERIES rainfall
    - Adjust simulation start/end times (with buffer before and after rainfall)
    Write to a temporary inp file and return its path
    """
    inp = read_inp_file(inp_path)

    # Parse rainfall start/end times
    rain_start = parse_rain_start_time(rain_2d)
    rain_end = rain_start + datetime.timedelta(minutes=RAINFALL_TIMESTEP_MIN * num_steps)

    # Simulation start = rainfall start - buffer
    sim_start = rain_start - datetime.timedelta(minutes=EXTRA_MIN_BEFORE)
    # Simulation end = rainfall end + buffer
    sim_end = rain_end + datetime.timedelta(minutes=EXTRA_MIN_AFTER)

    # Update time settings in OPTIONS
    inp.OPTIONS['START_DATE'] = sim_start.strftime('%m/%d/%Y')
    inp.OPTIONS['START_TIME'] = sim_start.strftime('%H:%M:%S')
    inp.OPTIONS['REPORT_START_DATE'] = sim_start.strftime('%m/%d/%Y')
    inp.OPTIONS['REPORT_START_TIME'] = sim_start.strftime('%H:%M:%S')
    inp.OPTIONS['END_DATE'] = sim_end.strftime('%m/%d/%Y')
    inp.OPTIONS['END_TIME'] = sim_end.strftime('%H:%M:%S')

    # Replace rainfall timeseries
    inp[TIMESERIES]['rainfall'] = build_rainfall_timeseries(rain_2d)

    # Write to temporary file
    inp.write_file(temp_inp_path)
    return temp_inp_path


def run_simulation(inp_path, rain_2d):
    """
    Run SWMM simulation and save node/link results
    """
    with Simulation(inp_path) as sim:

        # Step through simulation
        for step in sim:
            pass


# ============================================================
# 3. Batch simulation
# ============================================================
os.makedirs(TEMP_DIR, exist_ok=True)

print(f"\nStarting batch simulation, {num_rains} rainfall events...")

for i in range(num_rains):
    rain_2d = rain_data[i]
    folder_name = f"rain_{i:04d}"

    print(f"  [{i+1}/{num_rains}] Simulating {folder_name} ...", end='', flush=True)

    try:
        # Generate temporary inp file
        temp_inp_path = os.path.join(TEMP_DIR, f'chaohu_{i:04d}.inp')
        modify_inp_for_rain(INP_PATH, rain_2d, temp_inp_path)

        # Run simulation and save results
        run_simulation(temp_inp_path, rain_2d)

    except Exception as e:
        print(f" Failed: {e}")
        # Save error info
        with open('error.txt', 'w') as f:
            f.write(str(e))

    finally:
        pass

