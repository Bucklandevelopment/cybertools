#!/usr/bin/env python3
"""
SCANet CLI - Main command line interface
"""

import click
import os
from pathlib import Path
from .parser import AirodumpParser
from .database import WiFiDatabase
from .visualizer import WiFiVisualizer
from .reporter import HTMLReporter, PDFReporter
from .web_osint import run_server


@click.group()
@click.version_option()
def cli():
    """SCANet - WiFi Security Analysis Network Tool"""
    pass


@cli.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='report', help='Output directory for reports')
@click.option('--format', '-f', type=click.Choice(['html', 'pdf', 'both']), default='both', help='Report format')
@click.option('--db', default=None, help='SQLite database file (auto-generated if not specified)')
def analyze(csv_file, output, format, db):
    """Analyze airodump-ng CSV file and generate reports"""
    
    csv_path = Path(csv_file)
    output_dir = Path(output)
    output_dir.mkdir(exist_ok=True)
    
    if db is None:
        db = output_dir / f"{csv_path.stem}.db"
    
    click.echo(f"📡 Analyzing {csv_file}...")
    
    # Parse CSV and store in database
    parser = AirodumpParser()
    ap_data, station_data = parser.parse(csv_path)
    
    db_manager = WiFiDatabase(str(db))
    db_manager.create_tables()
    db_manager.insert_access_points(ap_data)
    db_manager.insert_stations(station_data)
    
    click.echo(f"✅ Data stored in {db}")
    
    # Generate visualizations
    visualizer = WiFiVisualizer(str(db))
    charts = visualizer.generate_all_charts()
    
    # Generate reports
    if format in ['html', 'both']:
        html_reporter = HTMLReporter(str(db))
        html_file = output_dir / f"{csv_path.stem}_report.html"
        html_reporter.generate(str(html_file), charts)
        click.echo(f"📄 HTML report: {html_file}")
    
    if format in ['pdf', 'both']:
        pdf_reporter = PDFReporter(str(db))
        pdf_file = output_dir / f"{csv_path.stem}_report.pdf"
        html_file = output_dir / f"{csv_path.stem}_report.html"
        pdf_reporter.generate(str(html_file), str(pdf_file))
        click.echo(f"📑 PDF report: {pdf_file}")


@cli.command()
@click.argument('db_file', type=click.Path(exists=True))
@click.option('--query', '-q', help='Custom SQL query')
def query(db_file, query):
    """Execute custom queries on the database"""
    db_manager = WiFiDatabase(db_file)
    
    if query:
        results = db_manager.execute_query(query)
        if results:
            # Print column headers
            if results:
                columns = list(results[0].keys())
                click.echo(" | ".join(columns))
                click.echo("-" * (len(" | ".join(columns))))
                
                # Print data rows
                for row in results:
                    values = [str(row[col]) for col in columns]
                    click.echo(" | ".join(values))
        else:
            click.echo("No results found.")
    else:
        click.echo("Available sample queries:")
        click.echo("1. SELECT CH, COUNT(*) FROM ap GROUP BY CH;")
        click.echo("2. SELECT ESSID, COUNT(DISTINCT station) FROM ap JOIN sta ON ap.BSSID = sta.bssid GROUP BY ESSID;")

@cli.command()
def web_osint():
    """Start the web server for IP OSINT."""
    run_server()

if __name__ == '__main__':
    cli()
