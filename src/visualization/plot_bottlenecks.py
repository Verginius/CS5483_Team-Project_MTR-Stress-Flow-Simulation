import pandas as pd
import matplotlib.pyplot as plt
import os
import matplotlib

# 设置支持中文的字体 (用于Windows的MicroSoft YaHei)
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

def identify_and_plot_bottlenecks():
    congested_path = 'data/processed/congested_edges.csv'
    stations_path = 'data/processed/stations_master.csv'
    
    if not os.path.exists(congested_path) or not os.path.exists(stations_path):
        print(f"File not found: {congested_path} or {stations_path}")
        return

    df_congested = pd.read_csv(congested_path)
    df_stations = pd.read_csv(stations_path)
    
    # 建立站点代码到中文名的映射
    station_map = dict(zip(df_stations['Station Code'], df_stations['Chinese Name']))
    
    # 获取最严重拥塞片段 (合并同一连接不同时间的最高值)
    agg_congested = df_congested.groupby(['Source', 'Target', 'Is_Transfer'])['VC_Ratio'].max().reset_index()
    agg_congested = agg_congested.sort_values(by='VC_Ratio', ascending=False)
    
    # 获取前10
    top_10 = agg_congested.head(10).copy()
    
    def get_display_name(node):
        code = node.split('_')[0]
        line = node.split('_')[-1]
        chinese_name = station_map.get(code, code)
        return f"{chinese_name}({line})"
        
    top_10['Src_Name'] = top_10['Source'].apply(get_display_name)
    top_10['Tgt_Name'] = top_10['Target'].apply(get_display_name)
    top_10['Route_Desc'] = top_10['Src_Name'] + " -> " + top_10['Tgt_Name']
    
    # ----------------------
    # 输出记录文件到 data/processed
    # ----------------------
    os.makedirs('data/processed', exist_ok=True)
    report_path = 'data/processed/top_10_bottlenecks.csv'
    top_10[['Route_Desc', 'Is_Transfer', 'VC_Ratio']].to_csv(report_path, index=False)
    print(f"Saved top 10 bottlenecks record to: {report_path}")
    
    # ----------------------
    # 绘制可视化柱状图并保存到 data/processed
    # ----------------------
    plt.figure(figsize=(10, 6))
    bars = plt.barh(top_10['Route_Desc'][::-1], top_10['VC_Ratio'][::-1], color='crimson')
    plt.xlabel('压力指数 (V/C Ratio)')
    plt.title('港铁网络首 10 大最严重拥塞瓶颈 (Top 10 Congested Points)')
    
    # 添加数值标签
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                 f'{width:.2f}', ha='left', va='center')
                 
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    chart_path = 'data/processed/top_10_bottlenecks_chart.png'
    plt.savefig(chart_path, dpi=300)
    print(f"Saved bottlenecks chart to: {chart_path}")
    plt.close()

    # ----------------------
    # 在 TIF 地图上标记这些拥塞路段
    # ----------------------
    tif_path = 'data/raw/Map_POI/B50K_R200index-geo.tif'
    coords_path = 'data/raw/MTR_Stations_Location/Stations_With_Coords_And_Maps.csv'
    
    if os.path.exists(tif_path) and os.path.exists(coords_path):
        try:
            import rasterio
            from rasterio.plot import show
            import geopandas as gpd
            from shapely.geometry import Point, LineString
            
            df_coords = pd.read_csv(coords_path)
            
            top_10['Src_Code'] = top_10['Source'].apply(lambda n: n.split('_')[0])
            top_10['Tgt_Code'] = top_10['Target'].apply(lambda n: n.split('_')[0])
            
            station_eng_map = dict(zip(df_stations['Station Code'], df_stations['English Name']))
            coords_map = dict(zip(df_coords['station_eng'], zip(df_coords['long'], df_coords['lat'])))
            
            # 建立坐标查找的辅助字典（忽略大小写，部分匹配）
            coords_map_lower = {str(k).lower(): v for k, v in coords_map.items()}
            
            def get_coord(eng_name):
                if not eng_name: return None
                coord = coords_map.get(eng_name)
                if coord: return coord
                eng_lower = str(eng_name).lower()
                for k, v in coords_map_lower.items():
                    if k.startswith(eng_lower) or eng_lower.startswith(k):
                        return v
                return None
            
            lines = []
            points = set()
            for _, row in top_10.iterrows():
                src_eng = station_eng_map.get(row['Src_Code'])
                tgt_eng = station_eng_map.get(row['Tgt_Code'])
                
                src_coord = get_coord(src_eng)
                tgt_coord = get_coord(tgt_eng)
                            
                if src_coord and tgt_coord:
                    lines.append(LineString([src_coord, tgt_coord]))
                    points.add(src_coord)
                    points.add(tgt_coord)
            
            if lines:
                # 转换路线到 GeoDataFrame
                edges_gdf = gpd.GeoDataFrame(geometry=lines, crs="EPSG:4326")
                edges_gdf = edges_gdf.to_crs(epsg=2326) # 转换为香港1980网格坐标系
                
                # 转换站点到 GeoDataFrame
                nodes_gdf = gpd.GeoDataFrame(geometry=[Point(c) for c in points], crs="EPSG:4326")
                nodes_gdf = nodes_gdf.to_crs(epsg=2326)
                
                plt.figure(figsize=(15, 15))
                ax = plt.gca()
                
                with rasterio.open(tif_path) as src:
                    # 绘制底图
                    show(src, ax=ax, title=f"港铁网络最严重拥塞瓶颈空间位置 (已绘制 {len(lines)} 条)")
                    
                    # 绘制连接线
                    edges_gdf.plot(ax=ax, color='red', linewidth=4, zorder=2, label='Congested Links')
                    
                    # 绘制相关的站点
                    nodes_gdf.plot(ax=ax, color='#00FF00', markersize=150, edgecolor='black', linewidth=1.2, marker='*', zorder=3, label='Stations')
                    
                plt.legend(loc='lower left', frameon=True, fontsize=12)
                plt.xlabel('Easting')
                plt.ylabel('Northing')
                
                map_out_path = 'data/processed/top_10_bottlenecks_map.png'
                plt.savefig(map_out_path, dpi=300, bbox_inches='tight')
                print(f"Saved bottlenecks map to: {map_out_path}")
                plt.close()
            else:
                print("Failed to map coordinates for the bottlenecks.")
                
        except ImportError as e:
            print(f"Required library missing: {e}. Skip map TIF visualization.")
    else:
        print(f"File not found: {tif_path} or {coords_path}")
        
if __name__ == '__main__':
    identify_and_plot_bottlenecks()
