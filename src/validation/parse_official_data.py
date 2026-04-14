import pandas as pd
import io

def parse_patronage_data(csv_path):
    """
    修正版：解析官方乘客量CSV文件，能更好地处理不规则格式。
    """
    # 1. 先读取文件内容，手动处理一下标题行
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 2. 找到真正的表头和数据开始的位置
    # 我们知道数据从包含“二零二六年”的行开始
    data_start_index = -1
    for i, line in enumerate(lines):
        if '二零二六年' in line:
            data_start_index = i
            break
    
    if data_start_index == -1:
        raise ValueError("在文件中未找到有效的数据行。")

    # 3. 定义列名，因为CSV的表头跨越多行且不规范
    column_names = [
        '月份', '本地服务_月总量', '本地服务_周日均', 
        '机场快线_月总量', '机场快线_日均',
        '过境线_月总量', '过境线_日均',
        '其他_月总量', '其他_日均',
        '高铁_月总量', '高铁_日均'
    ]
    
    # 4. 使用io.StringIO将处理过的行读入Pandas，并指定列名
    # 我们只读取从数据开始的行
    csv_data_string = "".join(lines[data_start_index:])
    df = pd.read_csv(io.StringIO(csv_data_string), header=None, names=column_names)

    # 5. 选择"二零二六年二月"的数据
    # 现在筛选应该能正常工作了
    feb_2026_data = df[df['月份'] == '二零二六年二月'].iloc[0]
    
    # 6. 提取关键列数据，注意单位是“千人次”
    official_monthly_total = float(str(feb_2026_data['本地服务_月总量']).replace(',', '')) * 1000
    official_weekday_avg = float(str(feb_2026_data['本地服务_周日均']).replace(',', '')) * 1000
    
    # 7. 计算周末/假日平均客流与工作日平均客流的比率
    num_weekdays = 20  # 假设2026年2月有20个工作日
    num_weekends = 8   # 和8个周末/假日
    
    total_weekday_traffic = official_weekday_avg * num_weekdays
    total_weekend_traffic = official_monthly_total - total_weekday_traffic
    
    # 增加一个保护，防止周末天数为0导致除零错误
    if num_weekends > 0:
        official_weekend_avg = total_weekend_traffic / num_weekends
    else:
        official_weekend_avg = 0

    # 增加保护，防止工作日平均为0导致除零错误
    if official_weekday_avg > 0:
        weekend_to_weekday_ratio = official_weekend_avg / official_weekday_avg
    else:
        weekend_to_weekday_ratio = 0
    
    return {
        "month": "2026年2月",
        "official_monthly_total": official_monthly_total,
        "official_weekday_avg": official_weekday_avg,
        "weekend_to_weekday_ratio": weekend_to_weekday_ratio,
        "num_weekdays": num_weekdays,
        "num_weekends": num_weekends
    }

def calculate_simulated_daily_total(od_matrix_path):
    """
    计算模拟的OD矩阵的总客流量。
    """
    od_df = pd.read_csv(od_matrix_path)
    simulated_total = od_df['Predicted_Flow'].sum()
    return simulated_total

# --- 主验证流程 ---
# 1. 从官方数据获取验证参数
patronage_file = 'data/raw/Patronage_20260412.csv'
params = parse_patronage_data(patronage_file)

# 2. 计算模拟的单日总流量
od_matrix_file = "data/processed/predicted_od_matrix.csv"
simulated_daily_flow = calculate_simulated_daily_total(od_matrix_file)

# 3. 使用官方比率进行尺度放大，推算模拟月度总量
simulated_monthly_total = (simulated_daily_flow * params['num_weekdays']) + \
                          (simulated_daily_flow * params['weekend_to_weekday_ratio'] * params['num_weekends'])

# 4. 计算与官方数据的相对误差
official_monthly_total = params['official_monthly_total']
relative_error = (simulated_monthly_total - official_monthly_total) / official_monthly_total

# 5. 输出最终验证结果
print("\n--- 宏观总量验证结果 ---")
print(f"验证月份: {params['month']}")
print(f"官方月度总客运量: {official_monthly_total:,.0f} 人次")
print("-" * 25)
print(f"模拟的典型日总客流: {simulated_daily_flow:,.0f} 人次")
print(f"使用的周末/工作日客流比: {params['weekend_to_weekday_ratio']:.2f}")
print(f"推算出的模拟月度总客运量: {simulated_monthly_total:,.0f} 人次")
print("-" * 25)
print(f"模型相对误差: {relative_error:.2%}")