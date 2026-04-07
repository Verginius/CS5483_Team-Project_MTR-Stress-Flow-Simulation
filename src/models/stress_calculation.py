import pandas as pd
import numpy as np
import os
import logging
import sys

# Add current dir to path to import capacity_model
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from capacity_model import LINE_CAPACITY, calculate_dynamic_capacity

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StressCalculator:
    """
    Task T3.3: 压力指数计算
    计算 V/C (Volume/Capacity) 比率，识别拥塞点，生成实时压力时间序列。
    """
    def __init__(self, link_flows_path, realtime_schedule_path=None, output_dir='data/processed'):
        self.link_flows_path = link_flows_path
        self.realtime_schedule_path = realtime_schedule_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.flows_df = pd.read_csv(link_flows_path)
        
        # 定义典型工作日 24 小时客流分布比例 (合计1.0)
        # 假设早高峰 08:00-09:00, 晚高峰 18:00-19:00
        self.hourly_profile = {
            0: 0.005, 1: 0.001, 2: 0.000, 3: 0.000, 4: 0.000, 5: 0.010,
            6: 0.030, 7: 0.080, 8: 0.150, 9: 0.090, 10: 0.050, 11: 0.040,
            12: 0.045, 13: 0.045, 14: 0.040, 15: 0.045, 16: 0.055, 17: 0.080,
            18: 0.130, 19: 0.060, 20: 0.040, 21: 0.035, 22: 0.030, 23: 0.020
        }
        
        # 根据经验值设定常规转乘通道流量限制 (人/分钟)
        self.TRANSFER_CAPACITY_PER_MIN = 350
        self._init_realtime_headways()

    def _init_realtime_headways(self):
        self.realtime_headways = {}
        if not self.realtime_schedule_path or not os.path.exists(self.realtime_schedule_path):
            logging.info("No realtime schedule provided. Using static fallback headways.")
            return

        logging.info(f"Loading realtime schedule from {self.realtime_schedule_path}...")
        df = pd.read_csv(self.realtime_schedule_path)
        
        # 提取小时
        df['fetch_hour'] = pd.to_datetime(df['fetch_timestamp']).dt.hour
        
        # 按数据采集时间、线路、站点、方向排序
        df_sorted = df.sort_values(['fetch_timestamp', 'line', 'sta', 'direction', 'seq'])
        
        # 计算发车间隔，即前后班列的时间差（分钟）
        df_sorted['headway_diff'] = df_sorted.groupby(['fetch_timestamp', 'line', 'sta', 'direction'])['ttnt'].diff()
        
        # 过滤有效的间隔时间
        valid_headways = df_sorted[df_sorted['headway_diff'] > 0].copy()
        
        # 按线路和小时求平均发车间隔
        hw_agg = valid_headways.groupby(['line', 'fetch_hour'])['headway_diff'].mean().reset_index()
        
        for _, row in hw_agg.iterrows():
            self.realtime_headways[(row['line'], int(row['fetch_hour']))] = float(row['headway_diff'])
            
        logging.info(f"Successfully computed {len(self.realtime_headways)} hourly realtime headway definitions.")
        
    def get_line_code(self, node_id):
        return node_id.split('_')[-1] if '_' in node_id else ''

    def get_headway(self, line, hour):
        """动态班次时间 (分钟)"""
        # 优先使用实时数据聚合的发车间隔
        if (line, hour) in self.realtime_headways:
            return max(self.realtime_headways[(line, hour)], 1.0)
            
        # 回退至简单的按小时动态班次时间 (分钟)
        # 早晚高峰 (8, 18) -> 2-3分钟, 平峰 -> 4-6分钟, 深夜 -> 8-10分钟
        if hour in [8, 18]: return 2.5
        elif hour in [7, 9, 17, 19]: return 3.5
        elif 6 <= hour <= 23: return 5.0
        else: return 10.0

    def generate_stress_timeseries(self):
        logging.info("Generating stress time-series from daily flow sums...")
        records = []
        
        for idx, row in self.flows_df.iterrows():
            source = row['Source']
            target = row['Target']
            daily_vol = row['Volume']
            
            src_line = self.get_line_code(source)
            tgt_line = self.get_line_code(target)
            is_transfer = (src_line != tgt_line)
            
            for hour in range(24):
                vol_per_min = (daily_vol * self.hourly_profile[hour]) / 60.0
                
                if is_transfer:
                    cap_per_min = self.TRANSFER_CAPACITY_PER_MIN
                else:
                    headway = self.get_headway(src_line, hour)
                    cap_per_min = calculate_dynamic_capacity(headway, src_line)
                    
                # 计算压力指数 V/C (限制下限防止除零)
                vc_ratio = vol_per_min / max(cap_per_min, 1.0)
                
                records.append({
                    'Time': f"{hour:02d}:00",
                    'Hour': hour,
                    'Source': source,
                    'Target': target,
                    'Volume_per_min': vol_per_min,
                    'Capacity_per_min': cap_per_min,
                    'VC_Ratio': vc_ratio,
                    'Is_Transfer': is_transfer
                })
                
        timeseries_df = pd.DataFrame(records)
        output_path = os.path.join(self.output_dir, 'network_stress_timeseries.csv')
        timeseries_df.to_csv(output_path, index=False)
        logging.info(f"Saved stress time-series to {output_path}")
        return timeseries_df

    def identify_congestion_points(self, timeseries_df, threshold=0.85):
        """识别拥塞的列车区间和换乘点"""
        logging.info(f"Identifying congested points (V/C >= {threshold})...")
        
        congested = timeseries_df[timeseries_df['VC_Ratio'] >= threshold].copy()
        top_congested = congested.sort_values(by='VC_Ratio', ascending=False)
        
        output_path = os.path.join(self.output_dir, 'congested_edges.csv')
        top_congested.to_csv(output_path, index=False)
        logging.info(f"Identified {len(top_congested)} congested intervals. Saved to {output_path}")
        
        agg_congested = top_congested.groupby(['Source', 'Target', 'Is_Transfer'])['VC_Ratio'].max().reset_index()
        agg_congested = agg_congested.sort_values(by='VC_Ratio', ascending=False)
        print("\n--- 首 10 大最严重拥塞瓶颈 (Top 10 Congested Points) ---")
        print(agg_congested.head(10).to_string(index=False))

if __name__ == '__main__':
    calculator = StressCalculator(
        link_flows_path='data/processed/link_flows.csv',
        realtime_schedule_path='data/processed/realtime_aggregated_20260404.csv'
    )
    ts_df = calculator.generate_stress_timeseries()
    calculator.identify_congestion_points(ts_df, threshold=0.8)
