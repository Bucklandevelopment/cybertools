import http.server
import socketserver
import sys
import os
import importlib.util

# Get the absolute path to the geo-recon.py script
current_dir = os.path.dirname(os.path.abspath(__file__))
geo_recon_path = os.path.join(current_dir, 'modules', 'geo-recon.py')

# Load the geo_recon module dynamically
spec = importlib.util.spec_from_file_location('geo_recon', geo_recon_path)
geo_recon = importlib.util.module_from_spec(spec)
sys.path.insert(0, os.path.join(current_dir, 'modules')) # Add modules to path for its own imports
spec.loader.exec_module(geo_recon)
get_osint = geo_recon.get_osint


PORT = 8000

# HTML template for the initial page
initial_page_template = """
<!DOCTYPE html>
<html>
<head>
    <title>IP OSINT</title>
</head>
<body>
    <h1>IP OSINT</h1>
    <p>Click the link below to perform an OSINT scan on your IP address.</p>
    <a href="/osint">Scan my IP</a>
</body>
</html>
"""

# HTML template for the results page
results_page_template = """
<!DOCTYPE html>
<html>
<head>
    <title>IP OSINT Results</title>
</head>
<body>
    <h1>IP OSINT Results</h1>
    <pre>{results}</pre>
</body>
</html>
"""

class OSINTHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(initial_page_template.encode('utf-8'))
        elif self.path.startswith('/osint'):
            client_ip = self.client_address[0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Run the geo-recon script and capture the output
            results = get_osint(client_ip)

            # Render the results page
            self.wfile.write(results_page_template.format(results=results).encode('utf-8'))
        else:
            super().do_GET()

def run_server():
    with socketserver.TCPServer(("", PORT), OSINTHandler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()

if __name__ == '__main__':
    run_server()
