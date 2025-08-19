"""
CSV Parser for airodump-ng files
"""

import pandas as pd
import re
from pathlib import Path
from typing import Tuple, List, Dict


class AirodumpParser:
    """Parse airodump-ng CSV files into structured data"""
    
    def __init__(self):
        self.ap_columns = [
            'BSSID', 'PWR', 'Beacons', 'Data', 'per_s', 'CH', 'MB', 
            'ENC', 'CIPHER', 'AUTH', 'ESSID'
        ]
        self.station_columns = [
            'Station_MAC', 'First_time_seen', 'Last_time_seen', 
            'Power', 'packets', 'BSSID', 'Probed_ESSIDs'
        ]
    
    def parse(self, csv_file: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Parse airodump CSV file and return AP and Station dataframes"""
        
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Split the file content into AP and Station sections
        sections = content.split('\n\n')
        
        ap_section = None
        station_section = None
        
        for section in sections:
            if section.strip().startswith('BSSID'):
                ap_section = section
            elif section.strip().startswith('Station MAC'):
                station_section = section
        
        ap_data = self._parse_ap_section(ap_section) if ap_section else pd.DataFrame()
        station_data = self._parse_station_section(station_section) if station_section else pd.DataFrame()
        
        return ap_data, station_data
    
    def _parse_ap_section(self, section: str) -> pd.DataFrame:
        """Parse Access Points section"""
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        
        if not lines:
            return pd.DataFrame()
        
        # Clean header line
        header = lines[0].replace(' ', '').split(',')
        data_lines = lines[1:]
        
        parsed_data = []
        for line in data_lines:
            if not line:
                continue
            
            # Handle quoted ESSID values
            parts = self._parse_csv_line(line)
            if len(parts) >= len(self.ap_columns):
                # Take only the expected number of columns
                row_data = parts[:len(self.ap_columns)]
                parsed_data.append(row_data)
        
        if not parsed_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(parsed_data, columns=self.ap_columns)
        
        # Clean and convert data types
        df = self._clean_ap_data(df)
        
        return df
    
    def _parse_station_section(self, section: str) -> pd.DataFrame:
        """Parse Stations section"""
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        
        if not lines:
            return pd.DataFrame()
        
        data_lines = lines[1:]  # Skip header
        
        parsed_data = []
        for line in data_lines:
            if not line:
                continue
            
            parts = self._parse_csv_line(line)
            if len(parts) >= len(self.station_columns):
                row_data = parts[:len(self.station_columns)]
                parsed_data.append(row_data)
        
        if not parsed_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(parsed_data, columns=self.station_columns)
        
        # Clean and convert data types
        df = self._clean_station_data(df)
        
        return df
    
    def _parse_csv_line(self, line: str) -> List[str]:
        """Parse a CSV line handling quoted fields"""
        # Simple CSV parser that handles quoted fields
        parts = []
        current = ""
        in_quotes = False
        
        i = 0
        while i < len(line):
            char = line[i]
            
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                parts.append(current.strip())
                current = ""
                i += 1
                continue
            else:
                current += char
            
            i += 1
        
        parts.append(current.strip())
        return parts
    
    def _clean_ap_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert AP data types"""
        if df.empty:
            return df
        
        # Remove quotes from ESSID
        if 'ESSID' in df.columns:
            df['ESSID'] = df['ESSID'].str.replace('"', '').str.strip()
        
        # Convert numeric columns
        numeric_cols = ['PWR', 'Beacons', 'Data', 'per_s', 'CH', 'MB']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean string columns
        string_cols = ['BSSID', 'ENC', 'CIPHER', 'AUTH', 'ESSID']
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        return df
    
    def _clean_station_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert Station data types"""
        if df.empty:
            return df
        
        # Convert numeric columns
        numeric_cols = ['Power', 'packets']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean string columns
        string_cols = ['Station_MAC', 'BSSID']
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Parse Probed ESSIDs
        if 'Probed_ESSIDs' in df.columns:
            df['Probed_ESSIDs'] = df['Probed_ESSIDs'].str.replace('"', '').str.strip()
        
        return df