import os
import platform
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
from email.parser import BytesParser
from email.policy import default
import socket

# 📁 Set upload directory based on OS
if "Android" in platform.platform():
    UPLOAD_DIR = "/sdcard/Download/uploadserver"
else:
    UPLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "uploadserver")

os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🌐 Get local IP
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

PORT = 8090

class SimpleUploader(BaseHTTPRequestHandler):
    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_GET(self):
        path = unquote(self.path[1:])
        full_path = os.path.join(UPLOAD_DIR, path)

        if path and os.path.isfile(full_path):
            self.send_response(200)
            self.send_header("Content-Disposition", f'attachment; filename="{path}"')
            self.end_headers()
            with open(full_path, "rb") as f:
                self.wfile.write(f.read())
            return

        files = os.listdir(UPLOAD_DIR)
        html = "<h1>📂 Uploaded Files</h1><ul>"
        for file in files:
            html += f'<li><a href="/{file}">{file}</a></li>'
        html += "</ul><h2>⬆️ Upload File</h2>"
        html += ("""
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file"/>
            <input type="submit" value="Upload"/>
        </form>
        """)
        self._send_html(html)

    def do_POST(self):
        content_len = int(self.headers['Content-Length'])
        boundary = self.headers.get("Content-Type").split("boundary=")[-1].encode()
        body = self.rfile.read(content_len)
        parts = body.split(b"--" + boundary)

        for part in parts:
            if b"Content-Disposition" in part and b"filename=" in part:
                headers, file_data = part.split(b"\r\n\r\n", 1)
                parsed_headers = BytesParser(policy=default).parsebytes(headers + b"\r\n")
                filename = parsed_headers.get_param("filename", header="Content-Disposition")
                if filename:
                    filename = os.path.basename(filename)
                    filepath = os.path.join(UPLOAD_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(file_data.strip(b"\r\n--"))
                    self._send_html(f"<p>✅ Uploaded: {filename}</p><a href='/'>Go Back</a>")
                    return
        self.send_error(400, "No valid file uploaded")

if __name__ == "__main__":
    ip = get_ip()
    print(f"📁 Upload directory: {UPLOAD_DIR}")
    print(f"✅ Serving at: http://{ip}:{PORT}")
    with HTTPServer(("", PORT), SimpleUploader) as httpd:
        httpd.serve_forever()
