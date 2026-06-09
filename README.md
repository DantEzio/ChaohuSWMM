# Chaohu SWMM Batch Simulation Project Documentation

## Project Overview

This project is based on EPA SWMM (Storm Water Management Model) to perform batch rainfall simulations on the Chaohu Basin drainage network. The core functionality is: feeding 1000 different rainfall events sequentially into the same network model (`chaohu.inp`), running the simulations, saving the results, and supporting extraction of time-series data for specified nodes/conduits from the simulation output files.

---

## File Structure

```
chaohuSWMM/
├── chaohu.inp          # SWMM network model input file (template)
├── raindata.npy        # Rainfall data (1000 events)
├── main_sim.py         # Batch simulation main script
├── getdata_demo.py     # Result extraction demo script
├── _temp_inp/          # Temporary inp file directory (auto-generated at runtime)
└── results/            # Simulation results root directory
    └── rain_XXXX/      # Result folder for each rainfall event
```

---

## Data File Description

### `chaohu.inp` — SWMM Network Model

This is the standard SWMM input file that defines the Chaohu Basin drainage network model, containing the following main sections:

| Model Element | Description |
|---------|------|
| **SUBCATCHMENTS** | Divides the basin into several sub-catchments, each corresponding to a rainfall inflow unit |
| **JUNCTIONS** | Connection nodes in the network, representing pipe intersections or manholes |
| **OUTFALLS** | Outlet at the end of the network, the boundary condition where water discharges |
| **STORAGE** | Storage nodes with storage capacity (e.g., detention basins), represented by `CC-storage` |
| **CONDUITS** | Pipes or channels connecting two nodes, serving as water flow transmission channels |
| **PUMPS** | Pumps simulating pump station drainage |
| **RAINGAGES** | Rainfall input devices, named `RG`, referencing `TIMESERIES rainfall`, with a 1-minute time interval |
| **TIMESERIES** | Rainfall time series named `rainfall`, which will be replaced with actual rainfall data before simulation |
| **OPTIONS** | Simulation options including start/end times, which will be dynamically adjusted before simulation |

### `raindata.npy` — Rainfall Data

- **Data type**: NumPy array (load with `allow_pickle=True`)
- **Array shape**: `(1000, 120, 2)`
  - **Dimension 1 (1000)**: 1000 different rainfall events
  - **Dimension 2 (120)**: 120 time steps per event (1 minute/step, i.e., each rainfall event lasts 120 minutes = 2 hours)
  - **Dimension 3 (2)**: Two values per step
    - `[:, :, 0]` — Time string in format `MM/DD/YYYY HH:MM:SS` (e.g., `08/28/2015 08:00:00`)
    - `[:, :, 1]` — Rainfall intensity value (unit: inches/hour or mm/hour, depending on the inp file settings)

**Example**: First 3 time steps of rainfall event #1:
```
[['08/28/2015 08:00:00', 0.5],
 ['08/28/2015 08:01:00', 1.2],
 ['08/28/2015 08:02:00', 0.8]]
```

---

## Script Description

### `main_sim.py` — Batch Simulation Main Script

#### Functionality

Reads the network model and rainfall data, injects 1000 rainfall events one by one into the model for SWMM simulation, and saves each event's simulation results to an independent folder.

#### Usage

```bash
python main_sim.py
```

#### Workflow

1. **Load rainfall data**: Read 1000 rainfall events from `raindata.npy`
2. **Process each event**: For event `i` (`i = 0, 1, ..., 999`):
   - **Modify inp file**:
     - Replace `TIMESERIES rainfall` with the current event's rainfall series
     - Adjust simulation start/end times:
       - Simulation start = rainfall start time - 60 minutes (warm-up period to let the network reach initial state)
       - Simulation end = rainfall end time + 60 minutes (extended simulation to observe recession)
   - **Write temporary inp**: Save to `_temp_inp/chaohu_XXXX.inp`
   - **Run SWMM simulation**: Execute simulation using pyswmm
3. **Save results**: Simulation output files (`.out`, `.rpt`) are saved in the `results/rain_XXXX/` directory

#### Key Parameters

| Parameter | Default Value | Description |
|------|--------|------|
| `RAINFALL_TIMESTEP_MIN` | 1 | Rainfall time step (minutes), consistent with the RAINGAGES interval in the inp file |
| `EXTRA_MIN_BEFORE` | 60 | Minutes to simulate before rainfall start (warm-up period) |
| `EXTRA_MIN_AFTER` | 60 | Minutes to continue simulating after rainfall end (recession period) |

#### Helper Functions

| Function Name | Description |
|--------|--------|
| `parse_rain_start_time(rain_2d)` | Parse rainfall start time (datetime object) from the first row of rainfall data |
| `build_rainfall_timeseries(rain_2d)` | Convert a single event's `(120, 2)` array into a `TimeseriesData` object for swmm_api |
| `modify_inp_for_rain(inp_path, rain_2d, temp_inp_path)` | Modify the inp file (replace rainfall series + adjust simulation times) and write to a temporary file |
| `run_simulation(inp_path, rain_2d)` | Run the SWMM simulation using pyswmm |

---

### `getdata_demo.py` — Result Extraction Demo Script

#### Functionality

Extracts the water depth time series of a specified node and the flow rate time series of a specified conduit from the `.out` binary output file generated by SWMM simulation, and saves them as `.npy` files.

#### Usage

```bash
python getdata_demo.py <rainfall_index> <node_name> <link_name>
```

**Parameter Description**:

| Parameter | Description | Example |
|------|------|------|
| `rainfall_index` | Index of the rainfall event (0–999), corresponding to the `rain_XXXX` folder | `0` |
| `node_name` | Name of the node to extract water depth (must match the node name in the inp file) | `CC-storage` |
| `link_name` | Name of the conduit to extract flow rate (must match the conduit name in the inp file) | `CC-R1` |

**Example**:

```bash
python getdata_demo.py 0 CC-storage CC-R1
```

This command extracts the water depth of node `CC-storage` and the flow rate of conduit `CC-R1` from `results/rain_0000/rain_0000.out`.

#### Output Files

| File Name | Shape | Description |
|--------|------|------|
| `node_{node_name}_depth.npy` | `(T, 2)` | Node water depth time series. Each row has two columns: `[time string, depth value]` |
| `link_{link_name}_flow.npy` | `(T, 2)` | Conduit flow rate time series. Each row has two columns: `[time string, flow value]` |

- `T` is the number of simulation time steps
- Time string format: `YYYY-MM-DD HH:MM:SS`
- Water depth unit: feet (ft), depending on the unit settings in the inp file
- Flow rate unit: cubic feet per second (CFS), depending on the unit settings in the inp file

#### Helper Functions

| Function Name | Description |
|--------|--------|
| `get_node_depth(out_path, node_name)` | Extract the water depth pandas Series of a specified node from the `.out` file |
| `get_link_flow(out_path, link_name)` | Extract the flow rate pandas Series of a specified conduit from the `.out` file |

---

## Simulation Results Directory Structure

```
results/
└── rain_0000/                          # Results for rainfall event #1
    ├── rain_0000.out                   # SWMM binary output file (complete time series of all variables)
    ├── rain_0000.rpt                   # SWMM text report file
    ├── node_CC-storage_depth.npy       # Extracted node depth time series (generated by getdata_demo.py)
    └── link_CC-R1_flow.npy             # Extracted conduit flow time series (generated by getdata_demo.py)
└── rain_0001/                          # Results for rainfall event #2
    └── ...
└── rain_0999/                          # Results for rainfall event #1000
    └── ...
```

---

## Dependencies

| Library | Purpose |
|------|------|
| `numpy` | Array read/write and numerical computation |
| `pyswmm` | Invoke the SWMM engine to run simulations |
| `swmm_api` | Read/write inp files and read out binary files |

Install dependencies:

```bash
pip install numpy pyswmm swmm_api
```

---

## Typical Workflow

```
1. Prepare the network model    → chaohu.inp
2. Prepare rainfall data        → raindata.npy
3. Run batch simulations        → python main_sim.py
4. Extract result data          → python getdata_demo.py 0 CC-storage CC-R1
5. Analyze & visualize          → Load .npy files for further processing
```
