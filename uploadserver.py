import os
import platform
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
from email.parser import BytesParser
from email.policy import default

# 👇 Automatically set upload directory based on platform
if "Android" in platform.platform():
    UPLOAD_DIR = "/sdcard/Download/uploadserver"
else:
    UPLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "uploadserver")

PORT = 8090
os.makedirs(UPLOAD_DIR, exist_ok=True)

class CustomHandler(BaseHTTPRequestHandler):
    def _send_html_response(self, content):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_GET(self):
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
                filename = disposition.params["filename"]
                filename = os.path.basename(filename)
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(file_data.strip(b"\r\n--"))
                self._send_html_response(f"<p>✅ File '{filename}' uploaded.</p><a href='/'>Go Back</a>")
                return

        self.send_error(400, "No valid file uploaded")

if __name__ == "__main__":
    print(f"📁 Uploads will be saved to: {UPLOAD_DIR}")
    with HTTPServer(("", PORT), CustomHandler) as httpd:
        print(f"✅ Serving at http://0.0.0.0:{PORT}")
        httpd.serve_forever()
