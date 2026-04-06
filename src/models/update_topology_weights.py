import pandas as pd
import networkx as nx
import os
import logging
from datetime import datetime

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_topology_weights(aggregated_csv_path, topology_in_path, topology_out_path):
    """
    Reads the real-time aggregated schedule CSV and updates the graph edge weights 
    with the estimated travel time (in minutes) between adjacent stations.
    """
    logging.info("Loading topology and aggregated schedule...")
    try:
        G = nx.read_gml(topology_in_path)
        df = pd.read_csv(aggregated_csv_path)
    except Exception as e:
        logging.error(f"Error loading files: {e}")
        return

    # Convert 'time' column to datetime objects for calculation
    # Example format: '2026-04-03 22:31:53+08:00'
    df['time'] = pd.to_datetime(df['time'], utc=True)
    
    # Sort dataframe by line, direction, and time
    df = df.sort_values(by=['line', 'direction', 'time'])
    
    edge_weights = {}

    logging.info("Calculating travel times between stations...")
    grouped = df.groupby(['line', 'direction'])
    
    for (line, direction), group in grouped:
        # Sort stations chronologically by arrival time
        sorted_group = group.sort_values('time')
        
        # Iterate through adjacent rows to calculate travel times
        for i in range(len(sorted_group) - 1):
            row1 = sorted_group.iloc[i]
            row2 = sorted_group.iloc[i+1]
            
            # Construct node identifiers (e.g. 'ADM_ISL')
            node1 = f"{row1['sta']}_{line}"
            node2 = f"{row2['sta']}_{line}"
            
            # Calculate time difference in minutes
            time_diff = (row2['time'] - row1['time']).total_seconds() / 60.0
            
            # Only consider reasonable bounds (e.g., > 0 and < 30 mins)
            # Extremely large gaps might mean a structural break or missing data
            if 0 < time_diff < 30:
                # We save it into our dictionary. If there are multiple observations for the same edge,
                # we maintain a list to calculate the average later.
                if G.has_edge(node1, node2):
                    edge = (node1, node2)
                elif G.has_edge(node2, node1):
                    # Graph might be undirected or bidirectional
                    edge = (node2, node1)
                else:
                    continue
                    
                if edge not in edge_weights:
                    edge_weights[edge] = []
                edge_weights[edge].append(time_diff)

    # Calculate average time for each edge and update Graph
    logging.info("Updating graph edge weights...")
    update_count = 0
    for edge, times in edge_weights.items():
        avg_time = sum(times) / len(times)
        G[edge[0]][edge[1]]['weight'] = round(avg_time, 2)
        update_count += 1
        
    # Give a default weight (e.g., 2 mins) for edges without real-time data
    missing_count = 0
    for u, v, data in G.edges(data=True):
        if 'weight' not in data or pd.isna(data.get('weight')):
            # It might be a transfer edge or simply missing data. 
            # If it's a transfer (same station, different line), assign an artificial transfer penalty (e.g. 3 mins)
            u_station = u.split('_')[0]
            v_station = v.split('_')[0]
            if u_station == v_station:
                G[u][v]['weight'] = 3.0  # Transfer penalty
            else:
                G[u][v]['weight'] = 2.0  # Default travel time
            missing_count += 1
            
    logging.info(f"Updated weights for {update_count} edges based on real-time data.")
    logging.info(f"Set default weights for {missing_count} edges (transfers or missing data).")
    
    # Add out-of-station interchange between Central (CEN) and Hong Kong (HOK)
    cen_nodes = [n for n in G.nodes if n.startswith('CEN_')]
    hok_nodes = [n for n in G.nodes if n.startswith('HOK_')]
    
    interchange_count = 0
    for cn in cen_nodes:
        for hn in hok_nodes:
            # Assuming a walking transfer time of 5.0 minutes
            if not G.has_edge(cn, hn):
                G.add_edge(cn, hn, weight=5.0)
            if not G.has_edge(hn, cn):
                G.add_edge(hn, cn, weight=5.0)
            else:
                G[cn][hn]['weight'] = 5.0
                G[hn][cn]['weight'] = 5.0
            interchange_count += 2
            
    if interchange_count > 0:
        logging.info(f"Added/Updated {interchange_count} out-of-station interchange edges (weight=5.0) between Central (CEN) and Hong Kong (HOK).")
    
    # Save the updated graph
    nx.write_gml(G, topology_out_path)
    logging.info(f"Successfully saved updated topology to {topology_out_path}.")

if __name__ == "__main__":
    # Ensure BASE_DIR points to the project root (going up 3 levels from src/models/update_topology_weights.py)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    AGG_CSV = os.path.join(BASE_DIR, 'data', 'processed', 'realtime_aggregated_20260404.csv')
    GML_IN = os.path.join(BASE_DIR, 'data', 'processed', 'mtr_topology.gml')
    GML_OUT = os.path.join(BASE_DIR, 'data', 'processed', 'mtr_topology.gml') # Overwrite the file
    
    update_topology_weights(AGG_CSV, GML_IN, GML_OUT)