# MTR Simulation Project Architecture & Detailed Specification

## 1. Project Overview
A dynamic crowd flow and line stress simulation system for the Hong Kong MTR network, leveraging real-time train data and official POI datasets.

---

## 2. Directory Structure (Implementation Layout)

```text
MTR_Simulation/
├── data/
│   ├── raw/                # Unprocessed MTR static/POI data
│   ├── processed/          # Cleaned stations, graph, and POI weights
│   └── realtime/           # Cached Next Train API responses
├── docs/                   # Project documentation and specifications
├── notebooks/              # Exploratory Data Analysis (EDA) & Prototyping
├── src/
│   ├── data/               # Data fetching and preprocessing scripts
│   │   ├── mtr_api.py      # Next Train API wrapper
│   │   ├── poi_processor.py # LandsD POI spatial analysis
│   │   └── graph_builder.py # NetworkX graph construction
│   ├── models/             # Core algorithms
│   │   ├── xgboost_model.py # OD matrix generation (XGBoost regression)
│   │   ├── path_planner.py  # Logit-based path assignment
│   │   └── stress_engine.py # V/C ratio & cascade failure logic
│   ├── visualization/      # UI components
│   │   └── dashboard.py    # Streamlit & Pydeck implementation
│   └── utils.py            # Coordinate conversion (EPSG:2326 to 4326)
├── tests/                  # Unit tests for graph and algorithms
├── .env                    # API keys (if needed)
├── requirements.txt        # Project dependencies
└── README.md               # Setup and usage instructions
```

---

## 3. System Architecture (Data Flow)

1.  **Input Layer**: 
    *   `MTR Static Data`: CSVs for fares, station locations.
    *   `MTR Real-time API`: JSON stream of Next Train info.
    *   `LandsD Geocom`: GeoJSON/Shapefiles of building polygons.
2.  **Preprocessing Layer**:
    *   **Spatial Join**: Maps buildings to the nearest MTR station (500m buffer).
    *   **Graph Engine**: Constructs a directed multi-layer graph using `NetworkX`.
3.  **Knowledge Discovery Layer (Mining)**:
    *   **Feature Engineering**: K-Means clustering of stations based on POI density.
    *   **Demand Predictor**: Executes the XGBoost regression model using engineered spatial and network features to generate the OD Matrix.
4.  **Simulation Layer**:
    *   **Path Assignment**: Distributes OD flow across the graph using the Multinomial Logit Model.
    *   **Dynamic Loading**: Overlays flow on edges based on real-time capacity ($C_{max}$).
5.  **Output Layer**:
    *   **Dashboard**: Real-time stress heatmap.
    *   **Validation**: RMSE/MAE reports comparing results to historical throughput.

---

## 4. Key Module Specifications

### Module: `graph_builder.py`
*   **Input**: `stations.csv`, `lines.csv`, `fares.json`.
*   **Logic**: Splits nodes by line (e.g., ADM_ISL, ADM_TWL). Connects them with "Transfer Edges" (weighted by walk time) and "Travel Edges" (weighted by distance/fare).

### Module: `xgboost_model.py`
*   **Algorithm**: Extreme Gradient Boosting (XGBoost) Regression.
*   **Process**: 
    1. Extract features (Origin POI clusters, Destination POI clusters, fare, total travel time, transfers).
    2. Train model / generate inferences for OD pair demand flow.
    3. Output Feature Importance for ablation study and validation report.

### Module: `dashboard.py`
*   **Engine**: Streamlit.
*   **Viz**: `pydeck.Layer("ArcLayer")` for crowd flow and `pydeck.Layer("PathLayer")` for line stress (color scale: Green [0.0] to Red [1.2+]).

---

## 5. Development Roadmap (Next Steps)
1.  **Sprint 1**: Setup `mtr_api.py` and `graph_builder.py`. (A)
2.  **Sprint 2**: Implement `poi_processor.py` and cluster stations. (C)
3.  **Sprint 3**: Build the `xgboost_model.py` and `path_planner.py`. (B)
4.  **Sprint 4**: Integrate everything into the `dashboard.py` and run validation. (All)
