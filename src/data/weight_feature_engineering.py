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
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df_poi['cluster'] = kmeans.fit_predict(scaled_features)
    
    # Assign cluster names intuitively (Suggested k=4: Commercial, Residential, Hub, Mixed)
    cluster_names = {0: 'Mixed', 1: 'Residential', 2: 'Commercial Hub', 3: 'Special/Industrial'}
    df_poi['cluster_name'] = df_poi['cluster'].map(cluster_names)

    # Merge with stations master
    print("Merging with stations master...")
    df_stations = pd.read_csv('data/processed/stations_master.csv')
    
    # Drop existing cluster columns if they exist to avoid duplicates
    if 'cluster' in df_stations.columns:
        df_stations = df_stations.drop(columns=['cluster'])
    if 'cluster_name' in df_stations.columns:
        df_stations = df_stations.drop(columns=['cluster_name'])

    df_merged = pd.merge(df_stations, df_poi[['Station Code', 'cluster', 'cluster_name']], on=['Station Code'], how='left')
    
    # Fill any missed stations
    df_merged['cluster'] = df_merged['cluster'].fillna(-1).astype(int)
    df_merged['cluster_name'] = df_merged['cluster_name'].fillna('Unknown')
    
    # Save back to stations_master.csv as requested
    df_merged.to_csv('data/processed/stations_master.csv', index=False)
    # Also save to stations_features.csv for compatibility with other scripts
    df_merged_full = pd.merge(df_stations, df_poi, on=['Station Code'], how='left', suffixes=('', '_poi'))
    df_merged_full.to_csv('data/processed/stations_features.csv', index=False)
    
    print(f"Features engineered. Updated stations_master.csv and saved to data/processed/stations_features.csv")

if __name__ == '__main__':
    process_features()
