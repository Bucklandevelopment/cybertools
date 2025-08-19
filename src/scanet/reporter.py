"""
Report generation module for HTML and PDF outputs
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from jinja2 import Template
import pdfkit
from .database import WiFiDatabase


class HTMLReporter:
    """Generate HTML reports from WiFi analysis data"""
    
    def __init__(self, db_path: str):
        self.db = WiFiDatabase(db_path)
        self.template = self._get_html_template()
    
    def generate(self, output_path: str, charts: Dict[str, str]):
        """Generate HTML report with embedded charts"""
        
        # Get statistics
        ap_stats = self.db.get_ap_stats()
        station_stats = self.db.get_station_stats()
        
        # Get raw data for tables
        ap_data = self._get_ap_table_data()
        station_data = self._get_station_table_data()
        
        # Prepare template context
        context = {
            'title': 'WiFi Security Analysis Report',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ap_stats': ap_stats,
            'station_stats': station_stats,
            'ap_data': ap_data,
            'station_data': station_data,
            'charts': charts
        }
        
        # Render template
        html_content = self.template.render(**context)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _get_ap_table_data(self) -> list:
        """Get access point data for table display"""
        results = self.db.execute_query('''
            SELECT BSSID, ESSID, CH, ENC, CIPHER, AUTH, PWR, Beacons, Data
            FROM ap
            ORDER BY PWR DESC
            LIMIT 50
        ''')
        
        return [dict(row) for row in results]
    
    def _get_station_table_data(self) -> list:
        """Get station data for table display"""
        results = self.db.execute_query('''
            SELECT sta.station, sta.power, sta.packets, sta.bssid, 
                   ap.ESSID, sta.probed_essids
            FROM sta
            LEFT JOIN ap ON sta.bssid = ap.BSSID
            ORDER BY sta.power DESC
            LIMIT 50
        ''')
        
        return [dict(row) for row in results]
    
    def _get_html_template(self) -> Template:
        """Return HTML template for the report"""
        template_str = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        
        .meta-info {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #666;
            font-size: 1.1em;
        }
        
        .section {
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .section h2 {
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background-color: #667eea;
            color: white;
            font-weight: bold;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
        
        .encryption-open {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .encryption-wpa {
            color: #f39c12;
            font-weight: bold;
        }
        
        .encryption-wpa2 {
            color: #27ae60;
            font-weight: bold;
        }
        
        .power-strong {
            color: #27ae60;
            font-weight: bold;
        }
        
        .power-medium {
            color: #f39c12;
            font-weight: bold;
        }
        
        .power-weak {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .footer {
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding: 20px;
        }
        
        @media print {
            body { background-color: white; }
            .section { box-shadow: none; border: 1px solid #ddd; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📡 {{ title }}</h1>
        <p>Generated on {{ generated_at }}</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{{ ap_stats.total_aps }}</div>
            <div class="stat-label">Access Points</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ station_stats.total_stations }}</div>
            <div class="stat-label">Stations</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ ap_stats.aps_by_channel|length }}</div>
            <div class="stat-label">Channels in Use</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ ap_stats.aps_by_encryption|length }}</div>
            <div class="stat-label">Encryption Types</div>
        </div>
    </div>
    
    <div class="section">
        <h2>📊 Access Points by Channel</h2>
        <div class="chart-container">
            <img src="data:image/png;base64,{{ charts.aps_by_channel }}" alt="APs by Channel">
        </div>
    </div>
    
    <div class="section">
        <h2>🔒 Encryption Distribution</h2>
        <div class="chart-container">
            <img src="data:image/png;base64,{{ charts.aps_by_encryption }}" alt="APs by Encryption">
        </div>
    </div>
    
    <div class="section">
        <h2>👥 Top Networks by Client Count</h2>
        <div class="chart-container">
            <img src="data:image/png;base64,{{ charts.top_aps_by_clients }}" alt="Top APs by Clients">
        </div>
    </div>
    
    <div class="section">
        <h2>🕸️ Network Topology</h2>
        <div class="chart-container">
            <img src="data:image/png;base64,{{ charts.network_graph }}" alt="Network Graph">
        </div>
    </div>
    
    <div class="section">
        <h2>📋 Access Points Details</h2>
        <table>
            <thead>
                <tr>
                    <th>BSSID</th>
                    <th>ESSID</th>
                    <th>Channel</th>
                    <th>Encryption</th>
                    <th>Cipher</th>
                    <th>Auth</th>
                    <th>Power</th>
                    <th>Beacons</th>
                    <th>Data</th>
                </tr>
            </thead>
            <tbody>
                {% for ap in ap_data %}
                <tr>
                    <td><code>{{ ap.BSSID }}</code></td>
                    <td>{{ ap.ESSID or '(hidden)' }}</td>
                    <td>{{ ap.CH or 'N/A' }}</td>
                    <td class="{% if ap.ENC == 'OPN' %}encryption-open{% elif 'WPA2' in ap.ENC %}encryption-wpa2{% elif 'WPA' in ap.ENC %}encryption-wpa{% endif %}">
                        {{ ap.ENC or 'N/A' }}
                    </td>
                    <td>{{ ap.CIPHER or 'N/A' }}</td>
                    <td>{{ ap.AUTH or 'N/A' }}</td>
                    <td class="{% if ap.PWR and ap.PWR > -50 %}power-strong{% elif ap.PWR and ap.PWR > -70 %}power-medium{% else %}power-weak{% endif %}">
                        {{ ap.PWR or 'N/A' }} dBm
                    </td>
                    <td>{{ ap.Beacons or '0' }}</td>
                    <td>{{ ap.Data or '0' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2>📱 Station Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Station MAC</th>
                    <th>Connected to BSSID</th>
                    <th>Network Name</th>
                    <th>Power</th>
                    <th>Packets</th>
                    <th>Probed Networks</th>
                </tr>
            </thead>
            <tbody>
                {% for station in station_data %}
                <tr>
                    <td><code>{{ station.station }}</code></td>
                    <td><code>{{ station.bssid or 'N/A' }}</code></td>
                    <td>{{ station.ESSID or 'N/A' }}</td>
                    <td class="{% if station.power and station.power > -50 %}power-strong{% elif station.power and station.power > -70 %}power-medium{% else %}power-weak{% endif %}">
                        {{ station.power or 'N/A' }} dBm
                    </td>
                    <td>{{ station.packets or '0' }}</td>
                    <td>{{ station.probed_essids or 'None' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>Report generated by SCANet - WiFi Security Analysis Network Tool</p>
        <p>🛡️ UTOP.IA SECos Project</p>
    </div>
</body>
</html>
        '''
        
        return Template(template_str)


class PDFReporter:
    """Generate PDF reports from HTML reports"""
    
    def __init__(self, db_path: str):
        self.db = WiFiDatabase(db_path)
    
    def generate(self, html_file: str, output_path: str):
        """Convert HTML report to PDF"""
        
        # Check if wkhtmltopdf is available
        try:
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            pdfkit.from_file(html_file, output_path, options=options)
            
        except Exception as e:
            # Fallback: create a simple text-based PDF info
            self._create_fallback_pdf(output_path, str(e))
    
    def _create_fallback_pdf(self, output_path: str, error_msg: str):
        """Create a fallback PDF when wkhtmltopdf is not available"""
        fallback_content = f"""
PDF Generation Error
===================

Error: {error_msg}

To generate PDF reports, please install wkhtmltopdf:

Ubuntu/Debian:
sudo apt-get install wkhtmltopdf

macOS:
brew install wkhtmltopdf

Windows:
Download from: https://wkhtmltopdf.org/downloads.html

Alternative: Use the HTML report which contains all the same information.
        """
        
        # Create a simple text file as fallback
        txt_path = output_path.replace('.pdf', '_info.txt')
        with open(txt_path, 'w') as f:
            f.write(fallback_content)
        
        print(f"PDF generation failed. Info saved to: {txt_path}")