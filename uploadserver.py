import os
from http.server import SimpleHTTPRequestHandler, HTTPServer

PORT = 8080
UPLOAD_DIR = "/sdcard/Download"

class CustomHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        rel_path = os.path.relpath(super().translate_path(path), os.getcwd())
        return os.path.join(UPLOAD_DIR, rel_path)

os.makedirs(UPLOAD_DIR, exist_ok=True)

with HTTPServer(("", PORT), CustomHandler) as httpd:
    print(f"✅ Serving at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
