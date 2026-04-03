import json
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def process_features():
    print("Loading POI data...")
    with open('data/processed/station_poi_weights.json', 'r', encoding='utf-8') as f:
        poi_data = json.load(f)

    # Flatten JSON to DataFrame
    rows = []
    for station_code, attrs in poi_data.items():
        row = {'Station Code': station_code}
        row.update(attrs)
        rows.append(row)

    df_poi = pd.DataFrame(rows)
    df_poi = df_poi.fillna(0)
    
    # Select feature columns (exclude IDs and Names)
    feature_cols = [col for col in df_poi.columns if col not in ['Station Code', 'Station ID', 'English Name', 'Total_POI']]
    
    # Normalize features
    print("Normalizing features...")
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_poi[feature_cols])
    
    # K-Means Clustering
    print("Applying K-Means clustering...")
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df_poi['Cluster'] = kmeans.fit_predict(scaled_features)
    
    # Assign cluster names intuitively (Optional, generic for now)
    cluster_names = {0: 'Mixed', 1: 'Residential', 2: 'Commercial'}
    # (A proper assignment would analyze cluster centers, but this serves as a baseline)
    df_poi['Cluster_Name'] = df_poi['Cluster'].map(cluster_names)

    # Merge with stations master
    print("Merging with stations master...")
    df_stations = pd.read_csv('data/processed/stations_master.csv')
    df_merged = pd.merge(df_stations, df_poi, on=['Station Code'], how='left', suffixes=('', '_poi'))
    
    # Fill any missed stations
    df_merged['Cluster'] = df_merged['Cluster'].fillna(-1)
    df_merged['Cluster_Name'] = df_merged['Cluster_Name'].fillna('Unknown')
    
    # Save the updated dataset
    output_path = 'data/processed/stations_features.csv'
    df_merged.to_csv(output_path, index=False)
    print(f"Features engineered and saved to {output_path}")

if __name__ == '__main__':
    process_features()
