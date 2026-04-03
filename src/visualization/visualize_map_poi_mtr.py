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
    mtr_path = 'data/raw/MTR_Stations_Location/Stations_With_Coords_And_Maps.csv'
    output_path = 'data/processed/poi_mtr_map_visualization.png'
    
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
        poi_df = pd.read_csv(poi_path, encoding='utf-8-sig')
        
    # Convert POI coordinates to Geopandas DataFrame (Hong Kong 1980 Grid - EPSG:2326)
    # Filter rows with missing Easting/Northing 
    poi_df = poi_df.dropna(subset=['EASTING', 'NORTHING'])
    geometry_poi = [Point(xy) for xy in zip(pd.to_numeric(poi_df['EASTING'], errors='coerce'), 
                                            pd.to_numeric(poi_df['NORTHING'], errors='coerce'))]
    poi_gdf = gpd.GeoDataFrame(poi_df, geometry=geometry_poi, crs="EPSG:2326")

    print("Loading MTR Station Data...")
    # Read MTR stations (ignoring cantonise encoding issues via errors='replace' if needed)
    mtr_df = pd.read_csv(mtr_path, encoding='utf-8', on_bad_lines='skip')
    mtr_df = mtr_df.dropna(subset=['lat', 'long'])
    
    # MTR stations use WGS84 Lat/Long => EPSG:4326
    geometry_mtr = [Point(xy) for xy in zip(pd.to_numeric(mtr_df['long'], errors='coerce'), 
                                            pd.to_numeric(mtr_df['lat'], errors='coerce'))]
    mtr_gdf = gpd.GeoDataFrame(mtr_df, geometry=geometry_mtr, crs="EPSG:4326")
    
    # Convert MTR to the coordinate system of the grid/POIs
    print("Converting MTR Coordinates to HK1980 Grid (EPSG:2326)...")
    mtr_gdf = mtr_gdf.to_crs(epsg=2326)
    
    print("Plotting Data...")
    fig, ax = plt.subplots(figsize=(15, 15))
    
    # 1. Base Map rendering
    show(raster, ax=ax, title="Hong Kong POI and MTR Stations")
    
    # 2. POI overlay
    poi_gdf.plot(ax=ax, color='#FF8C00', markersize=1.5, alpha=0.3, label='POI (All Categories)')

    # 3. MTR Stations overlay
    mtr_gdf.plot(ax=ax, color='#00FF00', markersize=150, edgecolor='black', linewidth=1.2, marker='*', label='MTR Stations')
    # Additional styling
    plt.legend(loc='lower left', frameon=True, fontsize=12, markerscale=2)
    
    # Output File
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Visualization completed! Map saved successfully to: {output_path}")

if __name__ == "__main__":
    main()
