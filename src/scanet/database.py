"""
Database operations for WiFi analysis data
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Any


class WiFiDatabase:
    """SQLite database manager for WiFi analysis data"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def create_tables(self):
        """Create database tables for AP and Station data"""
        with self.connect() as conn:
            # Access Points table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ap (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    BSSID TEXT NOT NULL UNIQUE,
                    PWR INTEGER,
                    Beacons INTEGER,
                    Data INTEGER,
                    per_s INTEGER,
                    CH INTEGER,
                    MB INTEGER,
                    ENC TEXT,
                    CIPHER TEXT,
                    AUTH TEXT,
                    ESSID TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Stations table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station TEXT NOT NULL,
                    first_seen TEXT,
                    last_seen TEXT,
                    power INTEGER,
                    packets INTEGER,
                    bssid TEXT,
                    probed_essids TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bssid) REFERENCES ap(BSSID)
                )
            ''')
            
            # Probed networks table (normalized)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS probes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    station_id INTEGER,
                    probe TEXT,
                    FOREIGN KEY (station_id) REFERENCES sta(id)
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_ap_bssid ON ap(BSSID)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_ap_channel ON ap(CH)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_ap_essid ON ap(ESSID)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sta_bssid ON sta(bssid)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sta_station ON sta(station)')
            
            conn.commit()
    
    def insert_access_points(self, ap_data: pd.DataFrame):
        """Insert access point data into database"""
        if ap_data.empty:
            return
        
        with self.connect() as conn:
            # Convert DataFrame to list of tuples
            records = []
            for _, row in ap_data.iterrows():
                record = (
                    row.get('BSSID', ''),
                    int(row.get('PWR', 0)) if pd.notna(row.get('PWR')) else None,
                    int(row.get('Beacons', 0)) if pd.notna(row.get('Beacons')) else None,
                    int(row.get('Data', 0)) if pd.notna(row.get('Data')) else None,
                    int(row.get('per_s', 0)) if pd.notna(row.get('per_s')) else None,
                    int(row.get('CH', 0)) if pd.notna(row.get('CH')) else None,
                    int(row.get('MB', 0)) if pd.notna(row.get('MB')) else None,
                    row.get('ENC', ''),
                    row.get('CIPHER', ''),
                    row.get('AUTH', ''),
                    row.get('ESSID', '')
                )
                records.append(record)
            
            # Insert or replace records
            conn.executemany('''
                INSERT OR REPLACE INTO ap 
                (BSSID, PWR, Beacons, Data, per_s, CH, MB, ENC, CIPHER, AUTH, ESSID)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', records)
            
            conn.commit()
    
    def insert_stations(self, station_data: pd.DataFrame):
        """Insert station data into database"""
        if station_data.empty:
            return
        
        with self.connect() as conn:
            for _, row in station_data.iterrows():
                # Insert station record
                cursor = conn.execute('''
                    INSERT OR REPLACE INTO sta 
                    (station, first_seen, last_seen, power, packets, bssid, probed_essids)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('Station_MAC', ''),
                    row.get('First_time_seen', ''),
                    row.get('Last_time_seen', ''),
                    int(row.get('Power', 0)) if pd.notna(row.get('Power')) else None,
                    int(row.get('packets', 0)) if pd.notna(row.get('packets')) else None,
                    row.get('BSSID', ''),
                    row.get('Probed_ESSIDs', '')
                ))
                
                station_id = cursor.lastrowid
                
                # Parse and insert probed ESSIDs
                probed_essids = row.get('Probed_ESSIDs', '')
                if probed_essids and probed_essids.strip():
                    # Split by comma and clean
                    essids = [essid.strip().strip('"') for essid in probed_essids.split(',')]
                    essids = [essid for essid in essids if essid]
                    
                    for essid in essids:
                        conn.execute('''
                            INSERT INTO probes (station_id, probe)
                            VALUES (?, ?)
                        ''', (station_id, essid))
            
            conn.commit()
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Execute a custom SQL query"""
        with self.connect() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def get_ap_stats(self) -> Dict[str, Any]:
        """Get access point statistics"""
        with self.connect() as conn:
            stats = {}
            
            # Total APs
            result = conn.execute('SELECT COUNT(*) FROM ap').fetchone()
            stats['total_aps'] = result[0]
            
            # APs by channel
            results = conn.execute('''
                SELECT CH as channel, COUNT(*) as count 
                FROM ap 
                WHERE CH IS NOT NULL 
                GROUP BY CH 
                ORDER BY CH
            ''').fetchall()
            stats['aps_by_channel'] = [{'channel': r[0], 'count': r[1]} for r in results]
            
            # APs by encryption
            results = conn.execute('''
                SELECT ENC as encryption, COUNT(*) as count 
                FROM ap 
                GROUP BY ENC 
                ORDER BY count DESC
            ''').fetchall()
            stats['aps_by_encryption'] = [{'encryption': r[0], 'count': r[1]} for r in results]
            
            # Top ESSIDs by client count
            results = conn.execute('''
                SELECT ap.ESSID, COUNT(DISTINCT sta.station) as clients
                FROM ap 
                LEFT JOIN sta ON ap.BSSID = sta.bssid
                WHERE ap.ESSID != ''
                GROUP BY ap.ESSID
                ORDER BY clients DESC
                LIMIT 10
            ''').fetchall()
            stats['top_essids_by_clients'] = [{'essid': r[0], 'clients': r[1]} for r in results]
            
            return stats
    
    def get_station_stats(self) -> Dict[str, Any]:
        """Get station statistics"""
        with self.connect() as conn:
            stats = {}
            
            # Total stations
            result = conn.execute('SELECT COUNT(*) FROM sta').fetchone()
            stats['total_stations'] = result[0]
            
            # Stations with multiple probes
            results = conn.execute('''
                SELECT sta.station, COUNT(probes.probe) as probe_count
                FROM sta
                LEFT JOIN probes ON sta.id = probes.station_id
                GROUP BY sta.station
                HAVING probe_count > 1
                ORDER BY probe_count DESC
                LIMIT 10
            ''').fetchall()
            stats['multi_probe_stations'] = [{'station': r[0], 'probes': r[1]} for r in results]
            
            # Most probed networks
            results = conn.execute('''
                SELECT probe, COUNT(*) as count
                FROM probes
                GROUP BY probe
                ORDER BY count DESC
                LIMIT 10
            ''').fetchall()
            stats['most_probed_networks'] = [{'network': r[0], 'count': r[1]} for r in results]
            
            return stats
    
    def get_network_graph_data(self) -> List[Dict[str, str]]:
        """Get data for network graph visualization"""
        with self.connect() as conn:
            results = conn.execute('''
                SELECT ap.BSSID as ap, ap.ESSID as ap_name, sta.station
                FROM ap 
                JOIN sta ON ap.BSSID = sta.bssid
                WHERE sta.station != ''
            ''').fetchall()
            
            return [{'ap': r[0], 'ap_name': r[1], 'station': r[2]} for r in results]