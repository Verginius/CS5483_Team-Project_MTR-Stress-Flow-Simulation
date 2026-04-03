# MTR Stress & Flow Simulation

## 📌 Project Overview
This project utilizes Hong Kong MTR's open data (real-time train information + static network and fare data) in combination with POI (Point of Interest) data from the Lands Department to build a dynamic traffic flow model. By simulating passenger distributions at various times of the day, the system identifies congestion bottlenecks within the railway network and analyzes passenger flow redistribution and system vulnerability under special scenarios, such as accessibility facility failures.

## 🎯 Objectives
- **Static & Real-time Data Integration**: Establish an automated data acquisition mechanism by combining MTR static data, the Next Train API, and spatial data from the Lands Department.
- **Network Topology & Feature Construction**: Construct a multi-layer directed graph model with NetworkX to transform heterogeneous spatial data into a computable network.
- **Demand Generation & Flow Simulation**: Use the Gravity Model and Iterative Proportional Fitting (IPF) to generate OD (Origin-Destination) demand matrices, and perform stochastic path assignment using a Multinomial Logit Model (MNL).
- **Congestion Warning & Visualization**: Calculate V/C (Volume/Capacity) ratios for continuous stress analysis and deploy an interactive 3D dynamic heatmap dashboard using Streamlit and Pydeck.

## 🏗️ System Architecture
### Data Flow
1. **Input Layer**: MTR Static Data (CSV), Real-time API (JSON), LandsD POI Data (GeoJSON).
2. **Preprocessing Layer**: Spatial Join (500m buffer zone), multi-layer graph topology splitting, and construction (NetworkX).
3. **Knowledge Discovery Layer**: Station feature clustering (K-Means), Double-Constrained Gravity Model (IPF Algorithm).
4. **Simulation Layer**: Multinomial Logit (MNL) discrete choice path assignment, dynamic capacity decay, and stress computation.
5. **Output Layer**: Interactive Dashboard, validation comparisons, and error analysis reports.

### Directory Structure
```text
MTR_Simulation/
├── data/
│   ├── raw/                # Unprocessed static and POI data (e.g., MTR_Fares, Map_POI)
│   ├── processed/          # Processed graph structures, features (e.g., stations_features.csv, mtr_topology.gml)
│   └── realtime/           # Real-time API cache snapshots (e.g., Next Train JSONs)
├── docs/                   # Project documentation and specifications
├── MTRSim/                 # Local Conda environment (Do not commit)
├── notebooks/              # Exploratory Data Analysis (EDA) & Prototyping
├── src/
│   ├── data/               # Data fetching, extraction, and preprocessing (e.g., weight_feature_engineering.py)
│   ├── models/             # Core algorithms (Gravity Model, Path Planner, Stress Engine)
│   ├── visualization/      # Visualization dashboard (Streamlit+Pydeck)
│   └── utils.py            # Utility functions (e.g., coordinates conversion)
├── tests/                  # Unit tests and baseline validation
├── requirements.txt        # Project dependencies
└── README.md               # Project setup and usage instructions
```

## 🧠 Core Algorithms
- **Spatial Clustering**: Unsupervised **K-Means clustering** extracts station attractiveness factors based on the distribution of building types within a 500m radius of each station.
- **Demand Generation (OD Mining)**: Harnesses **Iterative Proportional Fitting (IPF)** for constrained learning to estimate potential pedestrian flow trends between stations via the Gravity Model.
- **Path Assignment**: Applies the **Multinomial Logit Model (MNL)** for network flow overlay and prediction, based on utility functions encompassing time, fare, and transfer penalties.
- **Stress Analysis**: Computes real-time $V/C$ (Volume/Capacity) indices and identifies abnormal congestion evolutions using **Cascade Failure Models** and **Isolation Forest**.
- **Evaluation & Validation**: Employs **Multiple Linear Regression** and **Ablation Studies** to validate the degree to which POI features enhance the model's explanatory power.

## 🛠️ Tech Stack
- **Programming Language**: Python 3.11+ (Recommended for better performance and package compatibility)
- **Data Processing**: Pandas, NumPy
- **Spatial / Graph Computing**: NetworkX, GeoPandas, Shapely
- **Visualization**: Streamlit (Web UI), Pydeck (3D Map), Plotly (Charts)
- **Data Sources**: Data.gov.hk (MTR API), Lands Department Open Map

## 🚀 Setup & Installation (Recommendation)
Due to the heavy reliance on spatial computation libraries (`geopandas`, `shapely`) which require complex C/C++ extensions, **we highly recommend using Conda** to manage the virtual environment, especially on Windows. This avoids common dependency conflicts and compilation errors during installation.

1. **Create and activate a new Conda environment:**
```bash
conda create -n MTRSim python=3.11
conda activate MTRSim   # If installed locally: conda activate .\MTRSim
```

2. **Install all packages via conda-forge (Highly Recommended):**
```bash
conda install --file requirements.txt -c conda-forge -y
```
*Alternatively, you can install dependencies using pip (may cause C-extension compilation errors on Windows):*
```bash
pip install -r requirements.txt
```

## 👥 Role Assignment
- **Data Engineer (Member A)**: API integration, database management, and graph topology construction.
- **Algorithm Specialist (Member B)**: Data mining, Gravity Model development, Logit path prediction, and stress computation.
- **Analyst & Viz (Member C)**: Spatial data & feature engineering, front-end dashboard visualization, final analysis, and testing.

## 📅 Roadmap 
- **Sprint 1**: Setup data acquisition mechanism, construct network topology, and extract POI spatial features.
- **Sprint 2**: Calculate OD flow matrices, implement the core Gravity Model, and complete the Logit path assignment loop.
- **Sprint 3**: Integrate real-time heatmap visualization, execute baseline testing, run ablation studies, and finalize reports.
