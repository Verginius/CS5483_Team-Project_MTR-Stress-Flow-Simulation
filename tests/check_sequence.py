import pandas as pd
import importlib.util
import os
import sys

# Get project root based on current file location
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Read CSV
csv_path = os.path.join(project_root, 'data', 'raw', 'MTR_Stations_Facilities', '20231122-1027-mtr_lines_and_stations.csv')
df = pd.read_csv(csv_path)

# Load fetch_realtime_data.py
sys.path.append(os.path.join(project_root, 'src', 'data'))
import fetch_realtime_data

print("Checking fetch_realtime_data.py STATIONS_DATA:")
for line, stations in fetch_realtime_data.STATIONS_DATA:
    if line not in df['Line Code'].values:
        print(f"Line {line} not found in CSV.")
        continue
        
    line_df_dt = df[(df['Line Code'] == line) & (df['Direction'] == 'DT')].sort_values('Sequence')
    line_df_ut = df[(df['Line Code'] == line) & (df['Direction'] == 'UT')].sort_values('Sequence')
    
    dt_seq = line_df_dt['Station Code'].tolist()
    ut_seq = line_df_ut['Station Code'].tolist()
    
    if stations != dt_seq and stations != ut_seq and stations != dt_seq[::-1] and stations != ut_seq[::-1]:
        print(f"\nLine {line} mismatch in fetch_realtime_data:")
        print(f"Current: {stations}")
        print(f"CSV DT: {dt_seq}")
        print(f"CSV UT: {ut_seq}")
    else:
        pass # print(f"Line {line} matches OK.")

print("\n----------------\nChecking network_topology.py mtr_sequences:")
sys.path.append(os.path.join(project_root, 'src', 'models'))
import network_topology

# Mock check on the hardcoded dict
topology_path = os.path.join(project_root, 'src', 'models', 'network_topology.py')
with open(topology_path, 'r', encoding='utf-8') as f:
    eval_text = ""
    in_dict = False
    for line in f:
        if "mtr_sequences =" in line:
            in_dict = True
        if in_dict:
            eval_text += line
            if "}" in line:
                break

loc = {}
exec(eval_text.strip(), globals(), loc)
mtr_seqs = loc['mtr_sequences']

for line, stations in mtr_seqs.items():
    base_line = line.split('_')[0]
    if base_line not in df['Line Code'].values:
        print(f"Line {base_line} not found in CSV.")
        continue
        
    # some lines are branched, the CSV handles them with different Directions or we must ignore branch checking if complex
    # Let's do simple list inclusion check for branches, or direct match for mainlines.
    if '_BRANCH' in line:
        continue
        
    line_df_dt = df[(df['Line Code'] == base_line) & (df['Direction'] == 'DT')].sort_values('Sequence')
    line_df_ut = df[(df['Line Code'] == base_line) & (df['Direction'] == 'UT')].sort_values('Sequence')
    
    dt_seq = line_df_dt['Station Code'].tolist()
    ut_seq = line_df_ut['Station Code'].tolist()
    
    if stations != dt_seq and stations != ut_seq and stations != dt_seq[::-1] and stations != ut_seq[::-1]:
        print(f"\nLine {line} mismatch in network_topology:")
        print(f"Current: {stations}")
        print(f"CSV DT: {dt_seq}")
        print(f"CSV UT: {ut_seq}")

