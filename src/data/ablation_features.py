import pandas as pd
import json

def create_ablation_dataset():

    with open('data/processed/station_poi_weights.json', 'r', encoding='utf-8') as f:
        poi_data = json.load(f)
    
    # Get a sample station's keys to find all POI feature names
    sample_station = next(iter(poi_data))
    poi_columns_to_remove = list(poi_data[sample_station].keys())
    
    # Also add the cluster columns created from these features
    poi_columns_to_remove.extend(['Cluster', 'Cluster_Name'])
    
    # The merge might create suffixes, let's add those too just in case
    poi_columns_to_remove.extend([col + '_poi' for col in poi_columns_to_remove])

    # Remove keys that might also exist in the master station file to avoid errors
    safe_columns_to_remove = [col for col in poi_columns_to_remove if col not in ['Station Code', 'English Name', 'Station ID']]

    df_full = pd.read_csv('data/processed/stations_features.csv')

    # Use a list of columns that actually exist in the dataframe to avoid errors
    existing_cols_to_drop = [col for col in safe_columns_to_remove if col in df_full.columns]
    df_ablation = df_full.drop(columns=existing_cols_to_drop)

    output_path = 'data/processed/stations_features_no_poi.csv'
    df_ablation.to_csv(output_path, index=False)
    print(f"Ablation feature set saved successfully to {output_path}")


if __name__ == '__main__':
    create_ablation_dataset()