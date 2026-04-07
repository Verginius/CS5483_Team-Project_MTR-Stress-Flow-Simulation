import pandas as pd
import networkx as nx
import numpy as np
import os
import logging
from itertools import islice

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LogitPathAssignment:
    """
    Task T3.2: Path Assignment Algorithm (Multinomial Logit Model)
    Distributes predicted OD flows onto the network edges based on path time costs.
    """
    def __init__(self, od_matrix_path, topology_path, output_dir='data/processed'):
        self.od_matrix_path = od_matrix_path
        self.topology_path = topology_path
        self.output_dir = output_dir
        self.G = None
        self.od_df = None
        self.edge_flows = {} # {(u, v): flow}

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def load_data(self):
        logging.info("Loading OD matrix and topology...")
        self.od_df = pd.read_csv(self.od_matrix_path)
        self.G = nx.read_gml(self.topology_path)
        # Initialize edge flows
        for u, v in self.G.edges():
            self.edge_flows[(u, v)] = 0.0

    def get_k_shortest_paths(self, origin, dest, k=3):
        orig_nodes = [n for n in self.G.nodes if n.startswith(origin + '_')]
        dest_nodes = [n for n in self.G.nodes if n.startswith(dest + '_')]

        candidate_paths = []
        for on in orig_nodes:
            for dn in dest_nodes:
                if on == dn:
                    continue
                try:
                    # Yen's algorithm to find top k shortest simple paths
                    paths_gen = nx.shortest_simple_paths(self.G, source=on, target=dn, weight='weight')
                    paths = list(islice(paths_gen, k))
                    for p in paths:
                        # Calculate path cost (travel time)
                        length = sum(self.G[u][v].get('weight', 2.0) for u, v in zip(p[:-1], p[1:]))
                        candidate_paths.append({'path': p, 'cost': length})
                except nx.NetworkXNoPath:
                    continue

        # Sort all paths by cost and pick the top k fastest routes overall
        candidate_paths = sorted(candidate_paths, key=lambda x: x['cost'])
        return candidate_paths[:k]

    def allocate_flow(self, theta=0.15):
        """
        theta: sensitivity parameter for the Logit model.
        Higher theta means passengers are strictly preferring the fastest route.
        Lower theta means passengers are more likely to explore alternative routes.
        """
        logging.info(f"Starting Logit Path Assignment (theta={theta})...")
        
        count = 0
        total_od = len(self.od_df)
        
        for idx, row in self.od_df.iterrows():
            origin = row['Origin']
            dest = row['Destination']
            flow = row['Predicted_Flow']
            
            if flow <= 0 or origin == dest:
                continue
                
            paths = self.get_k_shortest_paths(origin, dest, k=3)
            
            if not paths:
                continue
            
            # Apply Multinomial Logit Model (MNL)
            # P(i) = exp(-theta * cost_i) / sum(exp(-theta * cost_j))
            costs = np.array([p['cost'] for p in paths])
            
            # To prevent overflow during exp, subtract min cost
            min_cost = np.min(costs)
            utilities = np.exp(-theta * (costs - min_cost))
            probabilities = utilities / np.sum(utilities)
            
            for i, p_dict in enumerate(paths):
                path_nodes = p_dict['path']
                allocated_flow = flow * probabilities[i]
                
                # Accumulate volume on each edge of the path
                for u, v in zip(path_nodes[:-1], path_nodes[1:]):
                    if (u, v) in self.edge_flows:
                        self.edge_flows[(u, v)] += allocated_flow
                    elif (v, u) in self.edge_flows: # For undirected graph resilience
                        self.edge_flows[(v, u)] += allocated_flow
                        
            count += 1
            if count % 500 == 0:
                logging.info(f"Processed {count}/{total_od} OD pairs...")

    def save_results(self):
        logging.info("Saving link flows...")
        flow_records = []
        for (u, v), flow in self.edge_flows.items():
            flow_records.append({
                'Source': u,
                'Target': v,
                'Volume': round(flow, 2)
            })
            
        flow_df = pd.DataFrame(flow_records)
        output_csv = os.path.join(self.output_dir, 'link_flows.csv')
        flow_df.to_csv(output_csv, index=False)
        
        # Attach flow volume to the network topology attributes
        for u, v in self.G.edges():
            # Update edge data with calculated volume
            self.G[u][v]['volume'] = round(self.edge_flows.get((u, v), 0.0), 2)
        
        out_gml = os.path.join(self.output_dir, 'mtr_topology_with_flow.gml')
        nx.write_gml(self.G, out_gml)
        logging.info(f"Successfully saved flow allocations to {output_csv}")
        logging.info(f"Saved flow-embedded topology to {out_gml}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    OD_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'predicted_od_matrix.csv')
    TOPOLOGY_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'mtr_topology.gml')
    
    assigner = LogitPathAssignment(OD_PATH, TOPOLOGY_PATH)
    assigner.load_data()
    # Execute logit model allocation
    assigner.allocate_flow(theta=0.20)
    assigner.save_results()
