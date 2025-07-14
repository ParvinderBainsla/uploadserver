import http.server
import socketserver
import os
import io
from email.parser import BytesParser
from urllib.parse import parse_qs

PORT = 8080
UPLOAD_DIR = "./uploads"

class UploadHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_type = self.headers.get('Content-Type')
        if not content_type or "multipart/form-data" not in content_type:
            self.send_error(400, "Invalid Content-Type")
            return

        boundary = content_type.split("boundary=")[1].encode()
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        parts = body.split(b"--" + boundary)
        for part in parts:
            if b"Content-Disposition" in part:
                headers, file_data = part.split(b"\r\n\r\n", 1)
                headers = BytesParser().parsebytes(headers + b"\r\n")
                content_disp = headers.get("Content-Disposition", "")
                if "filename=" in content_disp:
                    filename = content_disp.split("filename=")[-1].strip('"')
                    filepath = os.path.join(UPLOAD_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(file_data.rstrip(b"\r\n--"))

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Upload complete.")

    def list_directory(self, path):
        return super().list_directory(UPLOAD_DIR)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.chdir(UPLOAD_DIR)
Handler = UploadHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
