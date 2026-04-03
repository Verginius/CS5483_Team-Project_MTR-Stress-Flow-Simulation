import os
import time
import json
import requests
from datetime import datetime

# API接口地址
API_URL = "https://rt.data.gov.hk/v1/transport/mtr/getSchedule.php"

# 测试/目标线路和站点 (需要根据你的静态网络数据进行扩展)
# 参考代码含义: line = 线路代码, sta = 站点代码
# 如 TWL: 荃湾线, ADM: 金钟
TARGETS = [
    {"line": "TWL", "sta": "ADM"},
    {"line": "ISL", "sta": "CEN"},
    {"line": "TCL", "sta": "KOW"},
]

# 获取当前脚本所在目录的上上级目录，定位到 data/realtime/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SAVE_DIR = os.path.join(PROJECT_ROOT, "data", "realtime")

def fetch_mtr_data():
    """
    抓取给定的MTR线路和车站的实时列车数据
    """
    # 确保保存目录存在
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    
    all_data = {
        "timestamp": timestamp.isoformat(),
        "data": []
    }

    for target in TARGETS:
        line = target["line"]
        sta = target["sta"]
        
        try:
            response = requests.get(f"{API_URL}?line={line}&sta={sta}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 若API成功返回有效状态(1 indicates success usually)
                if data.get("status") == 1:
                    all_data["data"].append({
                        "line": line,
                        "sta": sta,
                        "schedule": data.get("data", {})
                    })
                    print(f"[{timestamp_str}] 成功获取数据: {line} - {sta}")
                else:
                    print(f"[{timestamp_str}] API返回异常状态 ({line} - {sta}): {data.get('message', '未知错误')}")
            else:
                print(f"[{timestamp_str}] 获取数据失败: {line} - {sta}. HTTP状态码: {response.status_code}")
        except Exception as e:
            print(f"[{timestamp_str}] 请求发生错误 ({line} - {sta}): {e}")
            
        # 增加极短睡眠避免频繁触发API的速率限制
        time.sleep(0.5)
        
    # 保存数据到 JSON 文件
    if all_data["data"]:
        file_path = os.path.join(SAVE_DIR, f"mtr_schedule_{timestamp_str}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            print(f"[{timestamp_str}] 所有数据已保存至 {file_path}")
        except Exception as e:
            print(f"[{timestamp_str}] 写入文件时出错: {e}")
    else:
         print(f"[{timestamp_str}] 未获取到有效数据，跳过保存。")

def main():
    print("🚀 启动港铁实时数据获取脚本...")
    print(f"📁 数据将保存在: {SAVE_DIR}")
    print("⏲️  抓取频率: 每 2 分钟")
    print("🛑 按下 Ctrl+C 可停止运行。")
    print("-" * 50)
    
    try:
        while True:
            fetch_mtr_data()
            target_sleep = 120 # 120秒 = 2分钟
            print(f"等待 {target_sleep} 秒后进行下一次抓取...\n")
            time.sleep(target_sleep)
    except KeyboardInterrupt:
        print("\n⏹️ 已由用户停止数据抓取。")

if __name__ == "__main__":
    main()
