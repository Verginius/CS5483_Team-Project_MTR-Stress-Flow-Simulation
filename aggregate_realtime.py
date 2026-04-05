import os
import json
import pandas as pd
from glob import glob

def main():
    data_dir = r"E:\CityU_CS\CS 5483\CS5483_Team-Project_MTR-Stress-Flow-Simulation\data\realtime"
    output_dir = r"E:\CityU_CS\CS 5483\CS5483_Team-Project_MTR-Stress-Flow-Simulation\data\processed"
    os.makedirs(output_dir, exist_ok=True)
    
    files = glob(os.path.join(data_dir, "*.json"))
    print(f"Found {len(files)} JSON files. Processing...")
    
    records = []
    error_count = 0
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = json.load(file)
                fetch_timestamp = content.get('timestamp')
                for row in content.get('data', []):
                    line = row.get('line')
                    sta = row.get('sta')
                    schedule = row.get('schedule', {})
                    for k, v in schedule.items():
                        if isinstance(v, dict):
                            for direction in ['UP', 'DOWN']:
                                for train in v.get(direction, []):
                                    if not isinstance(train, dict): continue
                                    r = {
                                        'fetch_timestamp': fetch_timestamp,
                                        'line': line,
                                        'sta': sta,
                                        'direction': direction,
                                        'seq': train.get('seq'),
                                        'dest': train.get('dest'),
                                        'plat': train.get('plat'),
                                        'time': train.get('time'),
                                        'ttnt': train.get('ttnt'),
                                        'valid': train.get('valid'),
                                        'source': train.get('source')
                                    }
                                    records.append(r)
        except Exception as e:
            error_count += 1
    
    if error_count > 0:
        print(f"Encountered errors parsing {error_count} files.")
        
    df = pd.DataFrame(records)
    print(f"Extracted {len(df)} total schedules.")
    
    if len(df) > 0 and 'time' in df.columns:
        df['time'] = df['time'].astype(str)
        # Filter for 2026-04-04 (which implies time starts with 2026-04-04)
        df_filtered = df[df['time'].str.startswith('2026-04-04')]
    else:
        df_filtered = df
        
    out_path = os.path.join(output_dir, "realtime_aggregated_20260404.csv")
    df_filtered.to_csv(out_path, index=False, encoding='utf-8')
    print(f"Filtered down to {len(df_filtered)} records for 2026-04-04.")
    print(f"Saved aggregated data to {out_path}")

if __name__ == '__main__':
    main()
