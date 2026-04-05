import pandas as pd
import numpy as np

# 港铁各线路列车设计载客量（预估值用于模拟）
LINE_CAPACITY = {
    'EAL': 3200,  # 东铁线 (9卡)
    'TWL': 2500,  # 荃湾线 (8卡)
    'ISL': 2500,  # 港岛线 (8卡)
    'KTL': 2500,  # 观塘线 (8卡)
    'TKL': 2500,  # 将军澳线 (8卡)
    'TCL': 2500,  # 东涌线 (8卡)
    'TML': 2500,  # 屯马线 (8卡)
    'SIL': 1000,  # 南港岛线 (3卡)
    'DRL': 1000,  # 迪士尼线 (4卡)
    'AEL': 1200,  # 机场快线 (8卡，立座较少)
}

DEFAULT_CAPACITY = 2500

def calculate_dynamic_capacity(headway_minutes: float, line_code: str, decay_factor: float = 1.0) -> float:
    """
    计算动态每分钟载客容量 (C_max)
    
    Args:
        headway_minutes: 实时班次间隔 (分钟)，即 Headway
        line_code: 港铁线路代码 (如 'EAL', 'TWL')
        decay_factor: 运力衰减系数 (如因特殊情况、设备故障导致的车厢不可用，默认 1.0)
        
    Returns:
        float: 每分钟的最大可用运力 C_max
    """
    if pd.isna(headway_minutes) or headway_minutes <= 0.0:
        return 0.0
        
    train_capacity = LINE_CAPACITY.get(line_code, DEFAULT_CAPACITY)
    
    # 动态运力模型：C_max = (每列车载客量 / 班次间隔) * 衰减系数
    c_max = (train_capacity / headway_minutes) * decay_factor
    
    return c_max

def apply_capacity_model(df: pd.DataFrame, headway_col: str = 'headway_min', line_col: str = 'line') -> pd.DataFrame:
    """
    批量计算数据集中的动态运力参数
    
    Args:
        df: 包含实时班次间隔的 DataFrame
        headway_col: 间隔时间(分钟)的列名
        line_col: 线路代码的列名
        
    Returns:
        pd.DataFrame: 新增 'capacity_per_min' 运力列后的 DataFrame
    """
    df_out = df.copy()
    
    if headway_col not in df_out.columns or line_col not in df_out.columns:
        raise ValueError(f"DataFrame 必须包含 '{headway_col}' 和 '{line_col}' 列")
        
    df_out['capacity_per_min'] = df_out.apply(
        lambda row: calculate_dynamic_capacity(row[headway_col], row[line_col]), 
        axis=1
    )
    
    return df_out
