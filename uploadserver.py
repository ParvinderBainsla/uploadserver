import os
import platform
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
from email.parser import BytesParser
from email.policy import default

# 📁 Automatically choose upload directory
if "Android" in platform.platform():
    UPLOAD_DIR = "/sdcard/Download/uploadserver"
else:
    UPLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "uploadserver")

PORT = 8090
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🌐 Detect local IP address
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

class CustomHandler(BaseHTTPRequestHandler):
    def _send_html_response(self, content):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_GET(self):
        path = unquote(self.path.lstrip("/"))
        if path:
            filepath = os.path.join(UPLOAD_DIR, path)
            if os.path.isfile(filepath):
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "File not found")
                return

        files = os.listdir(UPLOAD_DIR)
        body = "<h1>📁 Uploaded Files</h1><ul>"
        for file in files:
            safe_file = file.replace('"', '&quot;')
            body += f'<li><a href="/{safe_file}">{safe_file}</a></li>'
        body += "</ul><h2>⬆️ Upload File</h2>"
        body += ("""
        <form enctype="multipart/form-data" method="POST">
            <input name="file" type="file"/>
            <input type="submit" value="Upload"/>
        </form>""")
        self._send_html_response(body)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        content_type = self.headers.get('Content-Type', '')
        boundary = content_type.split("boundary=")[-1].encode()
        body = self.rfile.read(content_length)

        parts = body.split(b"--" + boundary)
        for part in parts:
            if b"Content-Disposition" in part and b"filename=" in part:
                headers, file_data = part.split(b"\r\n\r\n", 1)
                headers = BytesParser(policy=default).parsebytes(headers + b"\r\n")
                disposition = headers.get("Content-Disposition")
                if not disposition or not disposition.params.get("filename"):
                    continue
                filename = os.path.basename(disposition.params["filename"])
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(file_data.strip(b"\r\n--"))
                self._send_html_response(f"<p>✅ File '{filename}' uploaded.</p><a href='/'>Go Back</a>")
                return

        self.send_error(400, "No valid file uploaded")

if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"📁 Uploads will be saved to: {UPLOAD_DIR}")
    print(f"✅ Serving at http://{local_ip}:{PORT}")
    with HTTPServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()
