import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
from shapely.geometry import Point
import os

def main():
    # File Paths
    tif_path = 'data/raw/Map_POI/B50K_R200index-geo.tif'
    poi_path = 'data/raw/Map_POI/GeoCom4.1_202512.csv'
    mtr_path = 'data/processed/stations_master.csv'
    output_path = 'data/processed/mtr_poi_clusters_map.png'
    
    # Check if files exist
    for path in [tif_path, poi_path, mtr_path]:
        if not os.path.exists(path):
            print(f"Error: {path} not found.")
            return

    print("Loading Base Map TIFF...")
    raster = rasterio.open(tif_path)
    
    print("Loading POI Data...")
    try:
        # Some special characters might fail standard utf-8 decode
        poi_df = pd.read_csv(poi_path, encoding='utf-8')
    except UnicodeDecodeError:
        poi_df = pd.read_csv(poi_path, encoding='utf-8-sig', on_bad_lines='skip')
        
    # Convert POI coordinates to Geopandas DataFrame (Hong Kong 1980 Grid - EPSG:2326)
    # Filter rows with missing Easting/Northing 
    poi_df = poi_df.dropna(subset=['EASTING', 'NORTHING'])
    geometry_poi = [Point(xy) for xy in zip(pd.to_numeric(poi_df['EASTING'], errors='coerce'), 
                                            pd.to_numeric(poi_df['NORTHING'], errors='coerce'))]
    poi_gdf = gpd.GeoDataFrame(poi_df, geometry=geometry_poi, crs="EPSG:2326")

    print("Loading MTR Station Cluster Data...")
    # Read MTR stations from processed master file (contains cluster)
    mtr_df = pd.read_csv(mtr_path)
    
    # Coordinates are in a different file, merge them
    coords_path = 'data/raw/MTR_Stations_Location/Stations_With_Coords_And_Maps.csv'
    if os.path.exists(coords_path):
        coords_df = pd.read_csv(coords_path)
        # Standardize station names for merging if necessary, but English Name should match station_eng
        mtr_df = pd.merge(mtr_df, coords_df[['station_eng', 'lat', 'long']], 
                         left_on='English Name', right_on='station_eng', how='left')
    
    mtr_df = mtr_df.dropna(subset=['lat', 'long'])
    
    # MTR stations use WGS84 Lat/Long => EPSG:4326
    geometry_mtr = [Point(xy) for xy in zip(pd.to_numeric(mtr_df['long'], errors='coerce'), 
                                            pd.to_numeric(mtr_df['lat'], errors='coerce'))]
    mtr_gdf = gpd.GeoDataFrame(mtr_df, geometry=geometry_mtr, crs="EPSG:4326")
    
    # Convert MTR to the coordinate system of the grid/POIs
    print("Converting MTR Coordinates to HK1980 Grid (EPSG:2326)...")
    mtr_gdf = mtr_gdf.to_crs(epsg=2326)
    
    print("Plotting Data...")
    fig, ax = plt.subplots(figsize=(20, 20))
    
    # 1. Base Map rendering
    show(raster, ax=ax, title="Hong Kong MTR Station POI Clusters")
    
    # 2. POI overlay (faded)
    poi_gdf.plot(ax=ax, color='#D3D3D3', markersize=0.5, alpha=0.1, label='POI Background')

    # 3. MTR Stations overlay colored by cluster
    # Define colors for clusters (k=4)
    cluster_colors = {
        0: 'red',        # Mixed
        1: 'blue',       # Residential
        2: 'green',      # Commercial Hub
        3: 'purple',     # Special/Industrial
        -1: 'black'      # Unknown
    }
    
    for cluster_id, color in cluster_colors.items():
        subset = mtr_gdf[mtr_gdf['cluster'] == cluster_id]
        if not subset.empty:
            label = subset['cluster_name'].iloc[0] if 'cluster_name' in subset.columns else f'Cluster {cluster_id}'
            subset.plot(ax=ax, color=color, markersize=250, edgecolor='white', 
                       linewidth=1.5, marker='o', label=f'{label}')
    
    # Additional styling
    plt.legend(loc='upper left', frameon=True, fontsize=14, markerscale=1.5, title="Station Categories")
    plt.axis('off')
    
    # Output File
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualization completed! Map saved successfully to: {output_path}")

if __name__ == "__main__":
    main()
