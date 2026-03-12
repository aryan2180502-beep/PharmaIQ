import http.server
import socketserver
import os
import sys
import json

# Ensure project root is in path so imports work correctly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PORT = 8080
DIRECTORY = os.path.join(PROJECT_ROOT, "frontend")


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serves static files AND handles API POST calls."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path.startswith("/api/resolve/"):
            try:
                alert_id = int(self.path.rstrip("/").split("/")[-1])
                from frontend.dashboard_api import resolve_alert
                resolve_alert(alert_id)
                body = json.dumps({"status": "success", "alert_id": alert_id}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                print(f"SERVER_ERROR in do_POST: {e}")
                import traceback; traceback.print_exc()
                body = json.dumps({"error": str(e)}).encode()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        # Only log API calls, suppress static file noise
        if "api" in str(args):
            print(f"[SERVER] {args[0]} {args[1]}")


def start_server():
    os.makedirs(DIRECTORY, exist_ok=True)
    # Allow address reuse so restart doesn't fail on 'already in use'
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"=== PHARMAIQ LIVE DASHBOARD SERVER ===")
        print(f"Dashboard: http://localhost:{PORT}/dashboard.html")
        print(f"Resolve API: POST http://localhost:{PORT}/api/resolve/<alert_id>")
        print(f"Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    start_server()
