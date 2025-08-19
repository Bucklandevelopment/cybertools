# SCANet - WiFi Security Analysis Network Tool

A comprehensive tool for analyzing airodump-ng CSV files and generating detailed security reports with visualizations.

## Features

- 📊 **Data Analysis**: Parse and analyze airodump-ng CSV files
- 🗃️ **Database Storage**: Store data in SQLite for efficient querying
- 📈 **Visualizations**: Generate charts showing:
  - Access Points distribution by channel
  - Encryption type distribution
  - Top networks by client count
  - Network topology graphs
- 📄 **Report Generation**: Create HTML and PDF reports
- 🔍 **Custom Queries**: Execute custom SQL queries on the data

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd scanet
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install the package:
```bash
pip install -e .
```

### PDF Generation Requirements

For PDF report generation, install wkhtmltopdf:

**Ubuntu/Debian:**
```bash
sudo apt-get install wkhtmltopdf
```

**macOS:**
```bash
brew install wkhtmltopdf
```

**Windows:**
Download from: https://wkhtmltopdf.org/downloads.html

## Usage

### Basic Analysis

Analyze an airodump-ng CSV file and generate reports:

```bash
scanet analyze examples/sample_airodump.csv
```

### Custom Output Directory

Specify a custom output directory:

```bash
scanet analyze examples/sample_airodump.csv --output ./my_reports
```

### Report Format Selection

Generate only HTML or PDF reports:

```bash
# HTML only
scanet analyze examples/sample_airodump.csv --format html

# PDF only
scanet analyze examples/sample_airodump.csv --format pdf

# Both (default)
scanet analyze examples/sample_airodump.csv --format both
```

### Custom Database

Use a specific database file:

```bash
scanet analyze examples/sample_airodump.csv --db ./my_analysis.db
```

### Custom Queries

Execute custom SQL queries on the database:

```bash
# Interactive query prompt
scanet query ./report/sample_airodump.db

# Execute specific query
scanet query ./report/sample_airodump.db --query "SELECT CH, COUNT(*) FROM ap GROUP BY CH"
```

## Example Queries

Here are some useful SQL queries you can run:

### Access Points by Channel
```sql
SELECT CH AS channel, COUNT(DISTINCT BSSID) AS num_aps
FROM ap
GROUP BY CH
ORDER BY CH;
```

### Top Networks by Client Count
```sql
SELECT ESSID, COUNT(DISTINCT station) AS clients
FROM ap JOIN sta ON ap.BSSID = sta.bssid
GROUP BY ESSID 
ORDER BY clients DESC 
LIMIT 10;
```

### Stations Probing Multiple Networks
```sql
SELECT station, COUNT(DISTINCT probe) AS num_probes
FROM sta s
JOIN probes p ON s.id = p.station_id
GROUP BY station 
HAVING num_probes > 1
ORDER BY num_probes DESC;
```

### Security Analysis - Open Networks
```sql
SELECT BSSID, ESSID, CH, PWR
FROM ap
WHERE ENC = 'OPN'
ORDER BY PWR DESC;
```

### Weak Encryption Detection
```sql
SELECT BSSID, ESSID, ENC, CIPHER
FROM ap
WHERE ENC IN ('WEP', 'OPN')
ORDER BY ESSID;
```

### Future Plans

1. Make a dynamic host AP clone and deauth to hijack users and get the password
2. Ensure to research a method to get in the net and scan the hosts with NMAP like a HTB lab
3. Automate the basic PWN process for windows and android, linuxiphonemacos should be less?? Important?

## Project Structure

```
scanet/
├── src/scanet/
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Command line interface
│   ├── parser.py            # CSV parsing logic
│   ├── database.py          # Database operations
│   ├── visualizer.py        # Chart generation
│   └── reporter.py          # Report generation
├── examples/
│   └── sample_airodump.csv  # Example data file
├── tests/                   # Test files
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── setup.py                # Package setup
└── README.md               # This file
```

## Database Schema

### Access Points Table (ap)
- BSSID, PWR, Beacons, Data, CH, MB, ENC, CIPHER, AUTH, ESSID

### Stations Table (sta)
- station, first_seen, last_seen, power, packets, bssid, probed_essids

### Probes Table (probes)
- station_id, probe (normalized probed networks)

## Sample Output

The tool generates:

1. **HTML Report**: Interactive report with embedded charts
2. **PDF Report**: Printable version of the HTML report
3. **SQLite Database**: Structured data for custom analysis

## Security Considerations

This tool is designed for defensive security analysis only:

- ✅ Analyze your own network security
- ✅ Authorized penetration testing
- ✅ Security auditing and compliance
- ❌ Unauthorized network reconnaissance
- ❌ Malicious activities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- UTOP.IA SECos Team

## Disclaimer

This tool is intended for educational and authorized security testing purposes only. Users are responsible for complying with applicable laws and regulations.