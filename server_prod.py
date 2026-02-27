import http.server
import urllib.request
import urllib.parse
import urllib.error
import json
import os
import ssl
import gzip

PORT = int(os.environ.get("PORT", 8080))
DIR = os.path.dirname(os.path.abspath(__file__))

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith("/proxy?url="):
            raw = self.path[len("/proxy?url="):]
            url = urllib.parse.unquote(raw)
            try:
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
                    data = resp.read()
                    if resp.headers.get("Content-Encoding", "") == "gzip":
                        data = gzip.decompress(data)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(data)
            except urllib.error.HTTPError as e:
                body = json.dumps({"error": f"BLOCKED:{e.code}", "blocked": e.code in (403,503,429)}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = json.dumps({"error": str(e)}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        pass

print(f"Servidor iniciado na porta {PORT}")
with http.server.HTTPServer(("0.0.0.0", PORT), Handler) as srv:
    srv.serve_forever()
