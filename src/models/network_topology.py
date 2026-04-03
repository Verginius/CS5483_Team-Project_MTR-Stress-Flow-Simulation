import pandas as pd
import networkx as nx
import os

class MTRNetworkModel:
    def __init__(self, stations_data_path):
        self.stations_df = pd.read_csv(stations_data_path)
        # 填充 NaN 以防缺失
        self.stations_df['Lines'] = self.stations_df['Lines'].fillna('')
        self.graph = nx.DiGraph()
        
    def build_topology(self):
        """建立车站-区间图，包含 Node Splitting (多层图拆分) 转乘逻辑 以及 真实的线路区间"""
        
        # 记录每条线上的节点，方便后续建立同线区间边
        stations_by_line = {}
        
        for _, row in self.stations_df.iterrows():
            station_code = row['Station Code']
            lines = row['Lines'].split(',')
            
            # 1. 节点拆分 (Node Splitting)：一个物理站按线路拆分为多个逻辑站
            logic_nodes = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                node_id = f"{station_code}_{line}"
                logic_nodes.append(node_id)
                
                # 记录该线路的节点，备用
                if line not in stations_by_line:
                    stations_by_line[line] = []
                stations_by_line[line].append(station_code)
                
                # 添加逻辑节点
                self.graph.add_node(
                    node_id, 
                    station_code=station_code,
                    line=line,
                    name=row['English Name'],
                    c_name=row['Chinese Name'],
                    type='platform'
                )
            
            # 2. 如果是换乘站，建立站内换乘边 (Transfer Edges)
            if row['Is_Interchange'] and len(logic_nodes) > 1:
                # 建立所有双向换乘边，可以附加基于经验或设施的换乘代价 weight (转乘时间)
                for i in range(len(logic_nodes)):
                    for j in range(len(logic_nodes)):
                        if i != j:
                            u, v = logic_nodes[i], logic_nodes[j]
                            # 假设默认换乘时间为 3-5 分钟 (这里假设代价为 3 分钟)
                            self.graph.add_edge(u, v, edge_type='transfer', weight=3, capacity=float('inf'))
                            
        # 3. 追加同线区间连线 (Running Edges)
        self._add_hardcoded_running_edges()

    def _add_hardcoded_running_edges(self):
        """
        基于真实港铁线路顺序，将同一条线上的各个站点连接起来。
        这为引力模型和路径分配(T3.1, T3.2)提供物理行驶连接。
        """
        # 港铁各骨干线站点顺序(缩写)
        mtr_sequences = {
            "ISL": ["KET", "HKU", "SYP", "SHW", "CEN", "ADM", "WAC", "CAB", "TIH", "FOH", "NOP", "QUB", "TAK", "SWH", "SKW", "HFC", "CHW"],
            "TWL": ["CEN", "ADM", "TST", "JOR", "YMT", "MOK", "PRE", "SSP", "CSW", "LCK", "MEF", "LAK", "KWF", "KWH", "TWH", "TSW"],
            "KTL": ["WHA", "HOM", "YMT", "MOK", "PRE", "SKM", "KOT", "LOF", "WTS", "DIH", "CHH", "KOB", "NTK", "KWT", "LAT", "YAT", "TIK"],
            "TKL": ["NOP", "QUB", "YAT", "TIK", "TKO", "HAH", "POA"],
            "TKL_BRANCH": ["TKO", "LHP"],
            "TCL": ["HOK", "KOW", "OLY", "NAC", "LAK", "TSY", "SUN", "TUC"],
            "AEL": ["HOK", "KOW", "TSY", "AIR", "AWE"],
            "SIL": ["ADM", "OCP", "WCH", "LET", "SOH"],
            "EAL": ["ADM", "EXC", "HUH", "MKK", "KOT", "TAW", "SHT", "FOT", "UNI", "TAP", "TWO", "FAN", "SHS", "LOW"],
            "EAL_BRANCH": ["SHS", "LMC"],
            "TML": ["WKS", "MOS", "HEO", "TSH", "SHM", "CIO", "STW", "CKT", "TAW", "HIK", "DIH", "KAT", "SUW", "TKW", "HOM", "HUH", "ETS", "AUS", "NAC", "MEF", "TWW", "KSR", "YUL", "LOP", "TIS", "SIH", "TUM"],
            "DRL": ["SUN", "DIS"]
        }

        # 遍历生成的序列构建双向连线
        for line_key, seq in mtr_sequences.items():
            base_line = line_key.split('_')[0] # 处理分支如 TKL_BRANCH -> TKL
            for i in range(len(seq) - 1):
                u_code = seq[i]
                v_code = seq[i+1]
                
                u_node = f"{u_code}_{base_line}"
                v_node = f"{v_code}_{base_line}"
                
                # 只有当两个节点在我们的图(即从csv读取的)中均存在时才连接
                if self.graph.has_node(u_node) and self.graph.has_node(v_node):
                    # 假设站间平均行驶时间 2 分钟，理论载客量 2500 人/分钟
                    self.graph.add_edge(u_node, v_node, edge_type='running', weight=2, capacity=2500)
                    self.graph.add_edge(v_node, u_node, edge_type='running', weight=2, capacity=2500)
                            
    def add_segment_edges(self, edge_list):
        """
        添加同线区间边 (Running Edges)
        edge_list: list of dict {'u': 'ADM_TWL', 'v': 'CEN_TWL', 'time': 2, 'capacity': 2500}
        """
        for edge in edge_list:
            self.graph.add_edge(
                edge['u'], 
                edge['v'], 
                edge_type='running', 
                weight=edge['time'], 
                capacity=edge['capacity']
            )

    def get_graph(self):
        return self.graph
        
    def save_graph_gml(self, filepath):
        nx.write_gml(self.graph, filepath)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../"))
    
    data_path = os.path.join(project_root, "data", "processed", "stations_master.csv")
    model_output_dir = os.path.join(project_root, "data", "processed")
    
    print(f"Reading data from: {data_path}")
    mtr_model = MTRNetworkModel(data_path)
    mtr_model.build_topology()
    
    G = mtr_model.get_graph()
    
    # 统计信息
    print(f"Graph topology built with {G.number_of_nodes()} logical platforms and {G.number_of_edges()} transfer links.")
    
    out_file = os.path.join(model_output_dir, "mtr_topology.gml")
    mtr_model.save_graph_gml(out_file)
    print(f"Saved NetworkX logic graph to {out_file}")
