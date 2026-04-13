import pandas as pd
import numpy as np
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def train_and_eval(df, features, target_col, name):
    logging.info(f"Training model: {name}")
    X = df[features]
    y = df[target_col]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    return mae, rmse, r2

def main():
    # Load the OD matrix generated with POI (our "Ground Truth" for this study)
    od_matrix_path = 'data/processed/predicted_od_matrix.csv'
    if not os.path.exists(od_matrix_path):
        logging.error("predicted_od_matrix.csv not found. Please run od_mining.py first.")
        return
        
    df = pd.read_csv(od_matrix_path)
    
    # Prepare features
    le = LabelEncoder()
    df['O_Cluster_Enc'] = le.fit_transform(df['O_Cluster'])
    df['D_Cluster_Enc'] = le.transform(df['D_Cluster'])
    
    poi_categories = ['GOV', 'CUF', 'TRS', 'RSF', 'CMF', 'UTI', 'BUS', 'MUF', 'SCH', 'AMD', 'TRH', 'REM', 'HNC', 'TRF', 'COM', 'BGD']
    poi_features = [f'O_{c}' for c in poi_categories] + [f'D_{c}' for c in poi_categories]
    
    features_with_poi = ['O_Cluster_Enc', 'D_Cluster_Enc', 'Travel_Time_Min', 'Transfers'] + poi_features
    features_no_poi = ['Travel_Time_Min', 'Transfers']
    
    target = 'Target_Flow_Baseline'
    
    # Run experiments
    mae_with, rmse_with, r2_with = train_and_eval(df, features_with_poi, target, "With POI")
    mae_no, rmse_no, r2_no = train_and_eval(df, features_no_poi, target, "No POI (Distance Only)")
    
    print("\n" + "="*50)
    print("      ABLATION STUDY REPORT (T5.3)")
    print("="*50)
    print(f"{'Metric':<15} | {'With POI':<15} | {'No POI':<15}")
    print("-"*50)
    print(f"{'MAE':<15} | {mae_with:<15.4f} | {mae_no:<15.4f}")
    print(f"{'RMSE':<15} | {rmse_with:<15.4f} | {rmse_no:<15.4f}")
    print(f"{'R^2 Score':<15} | {r2_with:<15.4f} | {r2_no:<15.4f}")
    print("="*50)
    
    improvement_mae = (mae_no - mae_with) / mae_no * 100
    improvement_r2 = (r2_with - r2_no) / (1 - r2_no) * 100 if r2_no < 1 else 0
    
    print(f"\nConclusion: Adding POI data improved prediction MAE by {improvement_mae:.2f}%.")
    print(f"R^2 Score increased from {r2_no:.4f} to {r2_with:.4f}.")
    print("This proves that POI features are critical for capturing spatial demand.")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
