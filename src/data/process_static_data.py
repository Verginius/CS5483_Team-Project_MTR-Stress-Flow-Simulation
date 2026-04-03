import os
import pandas as pd

# 项目根目录与数据路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

def process_stations_master():
    """
    任务 T1.1: 静态数据集成
    解析 MTR 线路、车站基础数据，生成唯一的 stations_master.csv
    """
    # 1. 加载所有 MTR 站点和线路的数据
    lines_csv_path = os.path.join(RAW_DIR, "MTR_Stations_Facilities", "20231122-1027-mtr_lines_and_stations.csv")
    
    if not os.path.exists(lines_csv_path):
        print(f"❌ 找不到静态车站文件: {lines_csv_path}")
        return

    print("⏳ 开始解析静态车站数据...")
    df_stations = pd.read_csv(lines_csv_path)
    
    # 2. 数据清洗与集成：多条线路的换乘站应该被整合成唯一的基准节点
    # 提取需要的字段
    relevant_cols = ["Line Code", "Station Code", "Station ID", "Chinese Name", "English Name"]
    df_subset = df_stations[relevant_cols].dropna().drop_duplicates()
    
    # 按照站点代码 (Station Code) 分组，汇总此站涵盖的所有线路
    grouped = df_subset.groupby("Station Code").agg({
        "Station ID": "first",             # 保留第一个找到的数字 ID
        "Chinese Name": "first",           # 站名
        "English Name": "first",
        "Line Code": lambda x: ",".join(sorted(set(x)))  # 聚合所有包含该站的线路
    }).reset_index()
    
    # 重命名列以遵循规范
    grouped.rename(columns={
        "Line Code": "Lines"
    }, inplace=True)
    
    # 计算这个站是不是换乘站 (Lines里面包含逗号)
    grouped["Is_Interchange"] = grouped["Lines"].apply(lambda x: "," in x)
    
    # 3. 整合无障碍设施数据 (Barrier-Free Facilities)
    facilities_csv_path = os.path.join(RAW_DIR, "MTR_Stations_Facilities", "20230625-1002-barrier_free_facilities.csv")
    category_csv_path = os.path.join(RAW_DIR, "MTR_Stations_Facilities", "20230625-1007-barrier_free_facility_category.csv")
    if os.path.exists(facilities_csv_path) and os.path.exists(category_csv_path):
        print("⏳ 开始整合无障碍设施数据(附带类别特征)...")
        df_facilities = pd.read_csv(facilities_csv_path)
        df_cat = pd.read_csv(category_csv_path)
        
        # 只统计有效设施 (Value == 'Y' 意思是支持该设施)
        df_valid_facilities = df_facilities[df_facilities['Value'] == 'Y'].copy()
        
        # 关联分类获取分类 ID (Category_Id如 VJ, MJ, HJ, AJ)
        df_valid_facilities = df_valid_facilities.merge(
            df_cat[['Item_Code', 'Category_Id']], 
            left_on='Key', 
            right_on='Item_Code', 
            how='left'
        )
        
        # 为了兼容，我们保留之前的总数，同时增加不同类别的统计
        total_count = df_valid_facilities.groupby('Station_No').size().reset_index(name='Barrier_Free_Facilities_Count')
        
        # 按类型展开 (Pivot via Crosstab)
        cat_count = pd.crosstab(df_valid_facilities['Station_No'], df_valid_facilities['Category_Id']).reset_index()
        # 列名可能为 VJ, MJ, HJ, AJ。我们给它加上前缀或后缀清晰语义
        cat_count.columns = ['Station_No'] + [f"Facilities_{col}_Count" for col in cat_count.columns if col != 'Station_No']
        
        fac_merged = pd.merge(total_count, cat_count, on='Station_No', how='outer')
        fac_merged['Station_No'] = fac_merged['Station_No'].astype(float)
        
        # 将设施数据合并 (left join) 到主站表
        grouped['Station ID'] = grouped['Station ID'].astype(float)
        grouped = pd.merge(grouped, fac_merged, left_on='Station ID', right_on='Station_No', how='left')
        
        # 对于所有新加的统计列，将 NaN 填充为 0
        fill_cols = [c for c in grouped.columns if 'Facilities' in c]
        for c in fill_cols:
            grouped[c] = grouped[c].fillna(0).astype(int)
        
        if 'Station_No' in grouped.columns:
            grouped.drop(columns=['Station_No'], inplace=True)
    else:
        print(f"⚠️ 找不到无障碍设施数据或分类文件，跳过此步骤。")
    
    # 4. 保存至 processed 目录生成 T1.1 的交付物
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
        
    output_path = os.path.join(PROCESSED_DIR, "stations_master.csv")
    grouped.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"✅ 成功生成港铁车站主表！共整合了 {len(grouped)} 个独立车站。")
    print(f"📁 文件保存至: {output_path}")
    
    # 打印前几个记录作为预览
    print("\n--- 车站预览 ---")
    print(grouped.head())

if __name__ == "__main__":
    process_stations_master()
