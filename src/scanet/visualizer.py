"""
Data visualization module for WiFi analysis
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import pandas as pd
import networkx as nx
import io
import base64
from typing import Dict, List, Any
from .database import WiFiDatabase


class WiFiVisualizer:
    """Generate charts and visualizations for WiFi data"""
    
    def __init__(self, db_path: str):
        self.db = WiFiDatabase(db_path)
        
    def generate_all_charts(self) -> Dict[str, str]:
        """Generate all charts and return as base64 encoded images"""
        charts = {}
        
        charts['aps_by_channel'] = self.chart_aps_by_channel()
        charts['aps_by_encryption'] = self.chart_aps_by_encryption()
        charts['top_aps_by_clients'] = self.chart_top_aps_by_clients()
        charts['network_graph'] = self.chart_network_graph()
        
        return charts
    
    def chart_aps_by_channel(self) -> str:
        """Generate bar chart of APs by channel"""
        stats = self.db.get_ap_stats()
        channel_data = stats['aps_by_channel']
        
        if not channel_data:
            return self._empty_chart("No channel data available")
        
        channels = [item['channel'] for item in channel_data]
        counts = [item['count'] for item in channel_data]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(channels, counts, color='skyblue', edgecolor='navy', alpha=0.7)
        
        ax.set_xlabel('Channel', fontsize=12)
        ax.set_ylabel('Number of Access Points', fontsize=12)
        ax.set_title('Access Points Distribution by Channel', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def chart_aps_by_encryption(self) -> str:
        """Generate pie chart of APs by encryption type"""
        stats = self.db.get_ap_stats()
        encryption_data = stats['aps_by_encryption']
        
        if not encryption_data:
            return self._empty_chart("No encryption data available")
        
        labels = [item['encryption'] for item in encryption_data]
        sizes = [item['count'] for item in encryption_data]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Define colors for common encryption types
        colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                         colors=colors[:len(labels)], startangle=90)
        
        ax.set_title('Access Points by Encryption Type', fontsize=14, fontweight='bold')
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def chart_top_aps_by_clients(self) -> str:
        """Generate horizontal bar chart of top APs by client count"""
        stats = self.db.get_ap_stats()
        top_aps = stats['top_essids_by_clients']
        
        if not top_aps:
            return self._empty_chart("No client data available")
        
        # Take top 10 and reverse for better display
        top_aps = top_aps[:10][::-1]
        
        essids = [item['essid'] for item in top_aps]
        clients = [item['clients'] for item in top_aps]
        
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(essids, clients, color='lightgreen', edgecolor='darkgreen')
        
        ax.set_xlabel('Number of Connected Clients', fontsize=12)
        ax.set_ylabel('Network Name (ESSID)', fontsize=12)
        ax.set_title('Top Networks by Client Count', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                   f'{int(width)}', ha='left', va='center')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def chart_network_graph(self) -> str:
        """Generate network graph showing AP-Client relationships"""
        graph_data = self.db.get_network_graph_data()
        
        if not graph_data:
            return self._empty_chart("No network relationship data available")
        
        # Create NetworkX graph
        G = nx.Graph()
        
        # Create unique node names to avoid conflicts
        ap_nodes_set = set()
        station_nodes_set = set()
        
        for item in graph_data:
            ap = item['ap']
            station = item['station']
            ap_name = item['ap_name'] or f"AP_{ap[:8]}"  # Use ESSID or truncated BSSID
            station_name = f"STA_{station[:8]}"  # Prefix station names
            
            ap_nodes_set.add(ap_name)
            station_nodes_set.add(station_name)
            G.add_edge(station_name, ap_name)
        
        if len(G.nodes()) == 0:
            return self._empty_chart("No network connections to display")
        
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Create layout
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # Convert sets to lists for drawing
        ap_nodes = list(ap_nodes_set)
        station_nodes = list(station_nodes_set)
        
        # Draw nodes
        if ap_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=ap_nodes, 
                                 node_color='orange', node_size=800, 
                                 alpha=0.8, ax=ax, label='Access Points')
        
        if station_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=station_nodes,
                                 node_color='lightblue', node_size=400,
                                 alpha=0.8, ax=ax, label='Stations')
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, alpha=0.5, ax=ax)
        
        # Draw labels for APs only (stations would be too cluttered)
        try:
            if ap_nodes:
                ap_pos = {node: pos[node] for node in ap_nodes if node in pos and node in G.nodes()}
                if ap_pos:
                    nx.draw_networkx_labels(G, ap_pos, font_size=8, ax=ax)
        except KeyError:
            # Skip labels if there's an issue with positioning
            pass
        
        ax.set_title('WiFi Network Topology: Access Points ↔ Stations', 
                    fontsize=14, fontweight='bold')
        ax.legend()
        ax.axis('off')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        
        img_base64 = base64.b64encode(buf.getvalue()).decode('ascii')
        plt.close(fig)  # Free memory
        
        return img_base64
    
    def _empty_chart(self, message: str) -> str:
        """Generate an empty chart with a message"""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, message, transform=ax.transAxes,
                ha='center', va='center', fontsize=14, 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return self._fig_to_base64(fig)