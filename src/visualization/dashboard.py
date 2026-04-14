import streamlit as st
import pandas as pd
import pydeck as pdk
import networkx as nx
import os
import json

# Set Page Config
st.set_page_config(page_title="MTR Stress & Flow Simulation", layout="wide")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    # Load stations
    stations_df = pd.read_csv('data/processed/stations_master.csv')
    
    # Load coordinates (needed for pydeck)
    coords_path = 'data/raw/MTR_Stations_Location/Stations_With_Coords_And_Maps.csv'
    if os.path.exists(coords_path):
        coords_df = pd.read_csv(coords_path)
        stations_df = pd.merge(stations_df, coords_df[['station_eng', 'lat', 'long']], 
                             left_on='English Name', right_on='station_eng', how='left')
    
    # Load stress timeseries
    stress_df = pd.read_csv('data/processed/network_stress_timeseries.csv')
    
    # Load topology to get edges
    G = nx.read_gml('data/processed/mtr_topology.gml')
    edges_data = []
    for u, v, data in G.edges(data=True):
        # Extract station code from node label (e.g., ADM_ISL -> ADM)
        u_code = u.split('_')[0] if '_' in u else u
        v_code = v.split('_')[0] if '_' in v else v
        
        u_info = stations_df[stations_df['Station Code'] == u_code]
        v_info = stations_df[stations_df['Station Code'] == v_code]
        
        if not u_info.empty and not v_info.empty:
            edges_data.append({
                'source_code': u,
                'target_code': v,
                'source_lat': u_info['lat'].values[0],
                'source_long': u_info['long'].values[0],
                'target_lat': v_info['lat'].values[0],
                'target_long': v_info['long'].values[0],
                'edge_id': f"{u}-{v}"
            })
    
    edges_df = pd.DataFrame(edges_data)
    return stations_df, stress_df, edges_df

stations_df, stress_df, edges_df = load_data()

# --- DASHBOARD UI ---
st.title("🚇 MTR Network Stress & Crowd Flow Simulation")
st.markdown("### Real-time Bottleneck Detection & Spatial Analysis")

# Sidebar
st.sidebar.header("Control Panel")
# Use 'Time' instead of 'timestamp'
time_col = 'Time'
stress_val_col = 'VC_Ratio'

time_options = sorted(stress_df[time_col].unique())
time_step = st.sidebar.slider("Simulation Time Step", 0, len(time_options) - 1, 0)
selected_time = time_options[time_step]
st.sidebar.write(f"Current Timestamp: **{selected_time}**")

# Filter stress data for selected time
current_stress = stress_df[stress_df[time_col] == selected_time]

# Merge stress with edges for visualization
# Stress CSV uses Source/Target, edges_df uses source_code/target_code
viz_edges = pd.merge(edges_df, current_stress, left_on=['source_code', 'target_code'], right_on=['Source', 'Target'], how='left')
viz_edges[stress_val_col] = viz_edges[stress_val_col].fillna(0)

# Function to map stress ratio to color [R, G, B, A]
def get_color(ratio):
    # Green (0, 255, 0) to Red (255, 0, 0)
    # Ratio 0 -> [0, 255, 0]
    # Ratio 1.0+ -> [255, 0, 0]
    r = min(int(ratio * 255), 255)
    g = max(int((1 - ratio) * 255), 0)
    return [r, g, 0, 160]

viz_edges['color'] = viz_edges[stress_val_col].apply(get_color)

# --- MAP VISUALIZATION ---
# Layer 1: Station Points
station_layer = pdk.Layer(
    "ScatterplotLayer",
    stations_df,
    get_position=["long", "lat"],
    get_color="[200, 30, 0, 160]",
    get_radius=150,
    pickable=True,
)

# Layer 2: Stress Paths
path_data = []
for _, row in viz_edges.iterrows():
    path_data.append({
        "path": [[row['source_long'], row['source_lat']], [row['target_long'], row['target_lat']]],
        "color": row['color'],
        "stress": row[stress_val_col]
    })

path_layer = pdk.Layer(
    "PathLayer",
    path_data,
    get_path="path",
    get_color="color",
    width_min_pixels=3,
    pickable=True,
)

view_state = pdk.ViewState(latitude=22.3193, longitude=114.1694, zoom=11, pitch=45)

r = pdk.Deck(
    layers=[path_layer, station_layer],
    initial_view_state=view_state,
    tooltip={"text": "Edge Stress (V/C): {stress}"}
)

# Layout: Map + Charts
col1, col2 = st.columns([2, 1])

with col1:
    st.pydeck_chart(r)

with col2:
    st.subheader("Network Metrics")
    avg_stress = current_stress[stress_val_col].mean()
    max_stress = current_stress[stress_val_col].max()
    st.metric("Average Network Stress", f"{avg_stress:.2f}")
    st.metric("Peak Stress Ratio", f"{max_stress:.2f}", delta="Critical" if max_stress > 1.0 else "Stable")
    
    st.subheader("Top Bottlenecks")
    top_10 = current_stress.sort_values(by=stress_val_col, ascending=False).head(10)
    # Extract codes for merging
    top_10['source_code_clean'] = top_10['Source'].apply(lambda x: x.split('_')[0])
    top_10['target_code_clean'] = top_10['Target'].apply(lambda x: x.split('_')[0])
    
    # Merge with station names for readability
    top_10 = pd.merge(top_10, stations_df[['Station Code', 'English Name']], left_on='source_code_clean', right_on='Station Code')
    top_10 = pd.merge(top_10, stations_df[['Station Code', 'English Name']], left_on='target_code_clean', right_on='Station Code', suffixes=('_src', '_dest'))
    
    st.table(top_10[['English Name_src', 'English Name_dest', stress_val_col]])

# --- CLUSTER ANALYSIS ---
st.divider()
st.subheader("Station POI Cluster Distribution")
cluster_counts = stations_df['cluster_name'].value_counts()
st.bar_chart(cluster_counts)

st.write("Dashboard developed by Member C (Analyst & Viz). Data powered by XGBoost & MNL models.")
