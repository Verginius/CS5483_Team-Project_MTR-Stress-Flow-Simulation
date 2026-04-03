import networkx as nx
import plotly.graph_objects as go
import os

def visualize_network(gml_path, output_html):
    print(f"Loading graph from {gml_path}...")
    G = nx.read_gml(gml_path)
    
    print("Generating spring layout (this may take a few seconds)...")
    # Using spring layout for plotting nodes
    pos = nx.spring_layout(G, k=0.3, iterations=100, seed=42)

    # Prepare Edges
    running_edge_x = []
    running_edge_y = []
    transfer_edge_x = []
    transfer_edge_y = []

    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_type = edge[2].get('edge_type', 'unknown')
        
        if edge_type == 'transfer':
            transfer_edge_x.extend([x0, x1, None])
            transfer_edge_y.extend([y0, y1, None])
        else:
            running_edge_x.extend([x0, x1, None])
            running_edge_y.extend([y0, y1, None])

    # 绘制同线区间边 (Running Edges)
    running_edge_trace = go.Scatter(
        x=running_edge_x, y=running_edge_y,
        line=dict(width=2, color='#333'),  # 加粗区间线
        hoverinfo='none',
        mode='lines',
        name='Running Links'
    )

    # 绘制站内换乘边 (Transfer Edges)
    transfer_edge_trace = go.Scatter(
        x=transfer_edge_x, y=transfer_edge_y,
        line=dict(width=1.5, color='#999', dash='dot'), # 虚线和浅色代表换乘
        hoverinfo='none',
        mode='lines',
        name='Transfer Links'
    )

    # Prepare Nodes
    node_x = []
    node_y = []
    node_text = []
    node_hovertext = []
    
    # Official MTR Line Colors
    mtr_colors = {
        'KTL': '#00ab4e', # 观塘线
        'TWL': '#ed1d24', # 荃湾线
        'ISL': '#0071ce', # 港岛线
        'SIL': '#b6bd00', # 南港岛线
        'TKL': '#a35eb5', # 将军澳线
        'TCL': '#f7943f', # 东涌线
        'DRL': '#f173ac', # 迪士尼线
        'AEL': '#00888a', # 机场快线
        'EAL': '#53b7e8', # 东铁线
        'TML': '#8d6019'  # 屯马线
    }
    node_colors = []

    for node in G.nodes():
        node_data = G.nodes[node]
        line = node_data.get('line', 'Unknown')
        
        # Assign official MTR colors
        base_line = line.split('_')[0] if '_' in line else line
        node_colors.append(mtr_colors.get(base_line, '#888888'))
        
        # Position
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Hover info
        c_name = node_data.get('c_name', '')
        e_name = node_data.get('name', '')
        hover_info = f"Node ID: {node}<br>Station: {c_name} ({e_name})<br>Line: {line}"
        node_hovertext.append(hover_info)
        node_text.append(c_name)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="top center",
        hovertext=node_hovertext,
        textfont=dict(size=9, color="#444"),
        marker=dict(
            showscale=False,
            color=node_colors,
            size=12,
            line_width=2
        )
    )

    # Compile the figure
    fig = go.Figure(
        data=[running_edge_trace, transfer_edge_trace, node_trace],
        layout=go.Layout(
            title='MTR Network Topology Diagram (Node Splitting Concept)',
            titlefont_size=18,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            paper_bgcolor="#ffffff",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )

    fig.write_html(output_html)
    print(f"Network visualization saved to {output_html}")
    
    return output_html

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../"))
    
    gml_file = os.path.join(project_root, "data", "processed", "mtr_topology.gml")
    html_output = os.path.join(project_root, "data", "processed", "mtr_topology_viz.html")
    
    if not os.path.exists(gml_file):
        print(f"Error: Could not find GML file at {gml_file}")
    else:
        visualize_network(gml_file, html_output)