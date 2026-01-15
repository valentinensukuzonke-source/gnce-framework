from http.server import BaseHTTPRequestHandler, HTTPServer
import os

OUT_DIR = "received_federation"
os.makedirs(OUT_DIR, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        ct = self.headers.get("Content-Type", "application/octet-stream")
        ext = ".zip" if ct == "application/zip" or body[:2] == b"PK" else ".json"

        path = os.path.join(OUT_DIR, f"payload_{len(os.listdir(OUT_DIR))+1}{ext}")
        with open(path, "wb") as f:
            f.write(body)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK\n")
        print(f"[RECEIVED] {path} ({len(body)} bytes, content-type={ct})")

if __name__ == "__main__":
    host, port = "127.0.0.1", 8787
    print(f"Listening on http://{host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()
