import os
import platform
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
from email.parser import BytesParser
from email.policy import default

# 👇 Automatically set base directory based on platform
if "Android" in platform.platform():
    BASE_DIR = "/sdcard/Download"
else:
    BASE_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

UPLOAD_DIR = os.path.join(BASE_DIR, "uploadserver")
os.makedirs(UPLOAD_DIR, exist_ok=True)
PORT = 8090

# 🧠 Get device IP address (Termux compatible)
def get_device_ip():
    try:
        result = os.popen("ifconfig | grep 'inet ' | grep -v 127 | awk '{print $2}'").read().strip()
        return result.split('\n')[0] if result else "127.0.0.1"
    except:
        return "127.0.0.1"

class CustomHandler(BaseHTTPRequestHandler):
    def _send_html_response(self, content):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_GET(self):
        rel_path = unquote(self.path.lstrip("/"))
        abs_path = os.path.join(BASE_DIR, rel_path)

        if os.path.isdir(abs_path):
            try:
                items = os.listdir(abs_path)
            except PermissionError:
                self.send_error(403, "Permission Denied")
                return
            body = f"<h1>📁 Directory: /{rel_path}</h1><ul>"
            if rel_path:
                parent = os.path.dirname(rel_path)
                body += f'<li><a href="/{parent}">⬅️ Back</a></li>'
            for item in items:
                safe_item = item.replace('"', '&quot;')
                link = os.path.join(rel_path, safe_item)
                body += f'<li><a href="/{link}">{safe_item}</a></li>'
            body += "</ul><h2>⬆️ Upload File</h2>"
            body += (f"<form enctype='multipart/form-data' method='POST'>"
                     f"<input name='file' type='file'/><input type='submit' value='Upload'/>")
            body += f"<input type='hidden' name='path' value='/{rel_path}'/></form>"
            self._send_html_response(body)
            return

        if os.path.isfile(abs_path):
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.end_headers()
            with open(abs_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "File not found")

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

                path_field = body.split(b"name=\"path\" value=\"")
                rel_upload_path = ""
                if len(path_field) > 1:
                    rel_upload_path = path_field[1].split(b"\"", 1)[0].decode()
                abs_upload_dir = os.path.join(BASE_DIR, rel_upload_path.strip("/"))
                os.makedirs(abs_upload_dir, exist_ok=True)

                filepath = os.path.join(abs_upload_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(file_data.strip(b"\r\n--"))

                self._send_html_response(f"<p>✅ File '{filename}' uploaded to /{rel_upload_path}'</p><a href='/{rel_upload_path}'>Go Back</a>")
                return

        self.send_error(400, "No valid file uploaded")

if __name__ == "__main__":
    device_ip = get_device_ip()
    print(f"📁 File browser starting at: {BASE_DIR}")
    print(f"✅ Serving at http://{device_ip}:{PORT}")
    with HTTPServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()
