import os
import json
import glob
import pandas as pd

def process_mtr_json_to_csv():
    # 获取项目根目录，定位数据目录
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    JSON_DIR = os.path.join(PROJECT_ROOT, "data", "realtime")
    
    # 查找所有的 json 文件
    json_files = glob.glob(os.path.join(JSON_DIR, "*.json"))
    
    if not json_files:
        print("未在 data/realtime/ 找到任何 JSON 文件。")
        return
        
    records = []
    
    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"无法解析 JSON 文件: {file_path}")
                continue
                
            req_timestamp = data.get("timestamp")
            
            # 解析每一条站点的记录
            for item in data.get("data", []):
                line = item.get("line")
                sta = item.get("sta")
                schedule = item.get("schedule", {})
                
                # MTR API 返回的 schedule 下的 key 通常是 "{line}-{sta}"
                key = f"{line}-{sta}"
                if key in schedule:
                    station_data = schedule[key]
                    curr_time = station_data.get("curr_time")
                    sys_time = station_data.get("sys_time")
                    
                    # 遍历 UP 和 DOWN 两个方向
                    for direction in ["UP", "DOWN"]:
                        if direction in station_data:
                            for train in station_data[direction]:
                                records.append({
                                    "fetch_timestamp": req_timestamp,
                                    "line": line,
                                    "station": sta,
                                    "curr_time": curr_time,
                                    "sys_time": sys_time,
                                    "direction": direction,
                                    "seq": train.get("seq"),
                                    "destination": train.get("dest"),
                                    "platform": train.get("plat"),
                                    "train_time": train.get("time"),
                                    "ttnt": train.get("ttnt"),          # Time to next train (mins)
                                    "valid": train.get("valid"),
                                    "source": train.get("source"),
                                    "source_file": os.path.basename(file_path) # 记录数据来源文件
                                })
                                
    if not records:
        print("没有可用的列车时刻记录。")
        return
        
    # 转换为 DataFrame 并导出为 CSV
    df = pd.DataFrame(records)
    
    # 将 CSV 保存到 data/processed/ 目录下
    PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
        
    output_csv = os.path.join(PROCESSED_DIR, "mtr_realtime_schedule.csv")
    
    df.to_csv(output_csv, index=False, encoding="utf-8-sig") # 使用 utf-8-sig 以兼容 Windows Excel
    print(f"✅ 成功将 {len(json_files)} 个 JSON 文件转换成了 {len(df)} 条记录!")
    print(f"📁 CSV 文件已保存至: {output_csv}")

if __name__ == "__main__":
    process_mtr_json_to_csv()
