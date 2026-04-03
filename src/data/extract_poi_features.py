import os
import json
import pandas as pd
import numpy as np
from pyproj import Transformer

def main():
    print("Loading stations...")
    stations_df = pd.read_csv('data/processed/stations_master.csv')
    coords_df = pd.read_csv('data/raw/MTR_Stations_Location/Stations_With_Coords_And_Maps.csv')
    
    stations_df['key'] = stations_df['English Name'].str.lower().str.replace('[^a-z0-9]', '', regex=True)
    coords_df['key'] = coords_df['station_eng'].str.lower().str.replace('[^a-z0-9]', '', regex=True)
    
    merged_stations = pd.merge(
        stations_df, 
        coords_df[['key', 'lat', 'long']].drop_duplicates('key'), 
        on='key', 
        how='left'
    )
    
    # Check for missing coords
    missing = merged_stations[merged_stations['lat'].isna()]
    if not missing.empty:
        print(f"Warning: Missing coordinates for {missing['English Name'].tolist()}")
        
    print("Transforming coordinates to HK1980 (EPSG:2326)...")
    # Convert lat/long (EPSG:4326) to Easting/Northing (EPSG:2326)
    # Note: pyproj expects (lat, lon) or (lon, lat) based on the exact transformer settings.
    # by default for 4326 it is usually (lat, lon) in newer pyproj but always_xy=True is safer.
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2326", always_xy=True)
    
    # always_xy=True means input is (lon, lat), output is (x, y) -> (Easting, Northing)
    x, y = transformer.transform(merged_stations['long'].values, merged_stations['lat'].values)
    merged_stations['easting'] = x
    merged_stations['northing'] = y
    
    print("Loading POI data...")
    # Read POI data. It can be large, so we only read needed columns
    poi_df = pd.read_csv('data/raw/Map_POI/GeoCom4.1_202512.csv', usecols=['CLASS', 'TYPE', 'EASTING', 'NORTHING'])
    
    # Drop rows without coordinates
    poi_df = poi_df.dropna(subset=['EASTING', 'NORTHING'])
    poi_easting = poi_df['EASTING'].values
    poi_northing = poi_df['NORTHING'].values
    poi_class = poi_df['CLASS'].values
    
    print("Calculating POI weights within 500m for each station...")
    results = {}
    total_stations = len(merged_stations)
    
    for idx, row in merged_stations.iterrows():
        station_code = row['Station Code']
        st_e = row['easting']
        st_n = row['northing']
        
        # Compute euclidean distance using numpy (vectorized)
        distances = np.sqrt((poi_easting - st_e)**2 + (poi_northing - st_n)**2)
        
        # Filter within 500m
        within_500 = poi_df[distances <= 500]
        
        # Count by CLASS
        class_counts = within_500['CLASS'].value_counts().to_dict()
        
        # Output format
        res_dict = {
            "Station ID": row['Station ID'],
            "English Name": row['English Name'],
            "Total_POI": int(within_500.shape[0])
        }
        # Add class counts and make sure they are standard ints
        for k, v in class_counts.items():
            res_dict[k] = int(v)
            
        results[station_code] = res_dict
        
        if (idx+1) % 20 == 0:
            print(f"Processed {idx+1}/{total_stations} stations...")
            
    out_path = 'data/processed/station_poi_weights.json'
    print(f"Saving results to {out_path}...")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print("Done!")

if __name__ == "__main__":
    main()