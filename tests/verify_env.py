import sys
import os
import warnings

# Suppress OpenMP and KMeans warnings
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="threadpoolctl")

def verify_environment():
    print(f"🐍 Python Version: {sys.version.split(' ')[0]}\n")
    print("⏳ Verifying library installations and C-extension bindings...\n")
    
    errors = 0

    # 1. Base Data Science
    try:
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({'test': [1, 2, 3]})
        _ = np.mean(df['test'])
        print(f"✅ pandas (v{pd.__version__}) and numpy (v{np.__version__}) are working.")
    except Exception as e:
        print(f"❌ Error with pandas/numpy: {e}")
        errors += 1

    # 2. Spatial Libraries (Most prone to C-extension errors)
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        # Test C-extensions (GEOS/GDAL)
        p1 = Point(114.1694, 22.3193) # HK Coordinates
        p2 = Point(114.1700, 22.3200)
        gs = gpd.GeoSeries([p1, p2])
        _ = gs.distance(p1)
        print(f"✅ geopandas (v{gpd.__version__}) and shapely are working. C-extensions loaded successfully.")
    except Exception as e:
        print(f"❌ Error with geopandas/shapely: {e}")
        errors += 1

    # 3. Graph Computing
    try:
        import networkx as nx
        G = nx.DiGraph()
        G.add_edge("Admiralty", "Central", weight=2)
        _ = nx.shortest_path(G, "Admiralty", "Central")
        print(f"✅ networkx (v{nx.__version__}) is working.")
    except Exception as e:
        print(f"❌ Error with networkx: {e}")
        errors += 1

    # 4. Machine Learning
    try:
        import sklearn
        from sklearn.cluster import KMeans
        X = np.array([[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]])
        kmeans = KMeans(n_clusters=2, random_state=0, n_init="auto").fit(X)
        print(f"✅ scikit-learn (v{sklearn.__version__}) is working.")
    except Exception as e:
        print(f"❌ Error with scikit-learn: {e}")
        errors += 1

    # 5. Visualization & Network
    try:
        import streamlit as st
        import pydeck as pdk
        import plotly
        import requests
        import dotenv
        print(f"✅ streamlit (v{st.__version__}), pydeck, plotly, requests, and python-dotenv are installed.")
    except Exception as e:
        print(f"❌ Error with visualization/network libraries: {e}")
        errors += 1

    print("\n" + "="*50)
    if errors == 0:
        print("🎉 All tests passed! Your MTRSim environment is stable and ready to use.")
    else:
        print(f"⚠️ Verification finished with {errors} error(s). Please check the logs above.")

if __name__ == "__main__":
    verify_environment()
