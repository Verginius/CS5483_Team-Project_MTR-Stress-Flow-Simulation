import pandas as pd
import numpy as np
import networkx as nx
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
import os
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ODMiningXGBoost:
    """
    Task T3.1: Demand Generation (OD Mining)
    This module uses XGBoost Regression to learn and predict the potential passenger flow
    between any Origin-Destination (OD) pairs in the MTR network.
    """
    def __init__(self, features_path, topology_path, output_dir='data/processed'):
        self.features_path = features_path
        self.topology_path = topology_path
        self.output_dir = output_dir
        self.stations_df = None
        self.G = None
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def load_data(self):
        logging.info("Loading stations features and network topology...")
        self.stations_df = pd.read_csv(self.features_path)
        self.G = nx.read_gml(self.topology_path)
        logging.info(f"Loaded {len(self.stations_df)} stations and Graph with {len(self.G.nodes)} nodes.")

    def generate_od_features(self):
        logging.info("Generating OD pair features (Cartesian product)...")
        # Start with all combinations of stations
        station_codes = self.stations_df['Station Code'].tolist()
        
        od_records = []
        for origin in station_codes:
            for dest in station_codes:
                if origin == dest:
                    continue
                
                # We need to extract shortest path and transfers from the graph
                # The graph's 'weight' now represents actual travel time in minutes.
                orig_nodes = [n for n in self.G.nodes if n.startswith(origin + '_')]
                dest_nodes = [n for n in self.G.nodes if n.startswith(dest + '_')]
                
                min_len = float('inf')
                best_path = None
                for on in orig_nodes:
                    for dn in dest_nodes:
                        if on == dn:
                            continue
                        try:
                            l = nx.shortest_path_length(self.G, source=on, target=dn, weight='weight')
                            if l < min_len:
                                min_len = l
                                best_path = nx.shortest_path(self.G, source=on, target=dn, weight='weight')
                        except nx.NetworkXNoPath:
                            pass
                            
                if best_path is None:
                    travel_time = 999
                    transfers = 0
                else:
                    travel_time = min_len
                    transfers = self._estimate_transfers(best_path)
                
                orig_data = self.stations_df[self.stations_df['Station Code'] == origin].iloc[0]
                dest_data = self.stations_df[self.stations_df['Station Code'] == dest].iloc[0]
                
                poi_categories = ['GOV', 'CUF', 'TRS', 'RSF', 'CMF', 'UTI', 'BUS', 'MUF', 'SCH', 'AMD', 'TRH', 'REM', 'HNC', 'TRF', 'COM', 'BGD']
                
                record = {
                    'Origin': origin,
                    'Destination': dest,
                    'O_Cluster': orig_data['Cluster_Name'],
                    'D_Cluster': dest_data['Cluster_Name'],
                    'Travel_Time_Min': travel_time,
                    'Transfers': transfers,
                    # Synthetic baseline target: Gravity Model using travel time
                    # Flow = (O_POI * D_POI) / (Travel_Time^2)
                    'Target_Flow_Baseline': (orig_data['Total_POI'] * dest_data['Total_POI']) / ((travel_time + 1)**2)
                }
                
                for c in poi_categories:
                    record[f'O_{c}'] = orig_data[c]
                    record[f'D_{c}'] = dest_data[c]
                    
                od_records.append(record)
        
        self.od_df = pd.DataFrame(od_records)
        logging.info(f"Generated {len(self.od_df)} OD pairs.")

    def _estimate_transfers(self, path):
        # Count line changes based on node suffixes (e.g. ADM_ISL -> ADM_TWL)
        lines = [n.split('_')[1] for n in path if '_' in n]
        if not lines:
            return 0
            
        transfers = 0
        curr = lines[0]
        for line in lines[1:]:
            if line != curr:
                transfers += 1
                curr = line
        return transfers

    def train_xgboost_model(self):
        logging.info("Encoding categorical features and preparing training data...")
        df = self.od_df.copy()
        
        le = LabelEncoder()
        df['O_Cluster_Enc'] = le.fit_transform(df['O_Cluster'])
        df['D_Cluster_Enc'] = le.transform(df['D_Cluster'])
        
        poi_categories = ['GOV', 'CUF', 'TRS', 'RSF', 'CMF', 'UTI', 'BUS', 'MUF', 'SCH', 'AMD', 'TRH', 'REM', 'HNC', 'TRF', 'COM', 'BGD']
        poi_features = [f'O_{c}' for c in poi_categories] + [f'D_{c}' for c in poi_categories]
        
        features = ['O_Cluster_Enc', 'D_Cluster_Enc', 'Travel_Time_Min', 'Transfers'] + poi_features
        X = df[features]
        y = df['Target_Flow_Baseline']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        logging.info("Training XGBoost Regressor...")
        model = xgb.XGBRegressor(
            n_estimators=100, 
            learning_rate=0.1, 
            max_depth=5, 
            random_state=42, 
            objective='reg:squarederror'
        )
        model.fit(X_train, y_train)
        
        score = model.score(X_test, y_test)
        logging.info(f"Model R^2 Score on Test Set: {score:.4f}")
        
        # Predict Flow
        self.od_df['Predicted_Flow'] = model.predict(X)
        
        # Plot Feature Importance (Improved Aesthetics)
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(12, 8))
        xgb.plot_importance(model, ax=ax, max_num_features=20, height=0.6, 
                            color='#4C72B0', edgecolor='none', grid=False)
        ax.set_title('Top 20 Features Importance for OD Flow Prediction', fontsize=16, fontweight='bold', pad=15)
        ax.set_xlabel('F-Score (Importance Weight)', fontsize=13)
        ax.set_ylabel('Features', fontsize=13)
        ax.tick_params(axis='both', labelsize=11)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'xgboost_feature_importance.png'), dpi=300, bbox_inches='tight')
        logging.info("Saved feature importance plot.")
        
        # Save OD Matrix
        output_csv = os.path.join(self.output_dir, 'predicted_od_matrix.csv')
        self.od_df.to_csv(output_csv, index=False)
        logging.info(f"Saved predicted OD matrix to {output_csv}")

if __name__ == "__main__":
    # Ensure current directory is the project root
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    FEATURES_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'stations_features.csv')
    TOPOLOGY_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'mtr_topology.gml')
    
    miner = ODMiningXGBoost(FEATURES_PATH, TOPOLOGY_PATH)
    miner.load_data()
    miner.generate_od_features()
    miner.train_xgboost_model()
