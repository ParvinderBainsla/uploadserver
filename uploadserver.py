import os
import platform
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
from email.parser import BytesParser
from email.policy import default

# 📁 Set correct upload directory
if "Android" in platform.platform():
    ROOT_DIR = "/sdcard/Download"
else:
    ROOT_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

PORT = 8090

class CustomHandler(BaseHTTPRequestHandler):
    def _send_html_response(self, content):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _list_dir(self, dir_path, rel_path=""):
        try:
            items = os.listdir(dir_path)
        except Exception as e:
            self.send_error(404, str(e))
            return

        body = f"<h1>📂 Index of /{rel_path}</h1><ul>"
        if rel_path:
            parent = os.path.dirname(rel_path)
            body += f'<li><a href="/{parent}">🔙 Parent</a></li>'

        for item in sorted(items):
            full_path = os.path.join(dir_path, item)
            link_path = os.path.join(rel_path, item).replace("\\", "/")
            if os.path.isdir(full_path):
                body += f'<li>📁 <a href="/{link_path}">{item}/</a></li>'
            else:
                body += f'<li>📄 <a href="/{link_path}">{item}</a></li>'
        body += "</ul>"

        # Upload form
        body += ("""
        <h2>⬆️ Upload File</h2>
        <form enctype="multipart/form-data" method="POST">
            <input name="file" type="file"/>
            <input type="submit" value="Upload"/>
        </form>""")
        self._send_html_response(body)

    def do_GET(self):
        path = unquote(self.path.strip("/"))
        full_path = os.path.join(ROOT_DIR, path)

        if os.path.isdir(full_path):
            self._list_dir(full_path, path)
        elif os.path.isfile(full_path):
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.end_headers()
            with open(full_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "File or folder not found")

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
                if disposition is None or "filename" not in disposition.params:
                    continue
                filename = os.path.basename(disposition.params["filename"])
                url_path = unquote(self.path.strip("/"))
                upload_path = os.path.join(ROOT_DIR, url_path)
                if not os.path.isdir(upload_path):
                    upload_path = ROOT_DIR
                os.makedirs(upload_path, exist_ok=True)
                filepath = os.path.join(upload_path, filename)
                with open(filepath, "wb") as f:
                    f.write(file_data.strip(b"\r\n--"))
                self._send_html_response(f"<p>✅ File '{filename}' uploaded.</p><a href='/{url_path}'>Go Back</a>")
                return

        self.send_error(400, "No valid file uploaded")

if __name__ == "__main__":
    print(f"📁 File browser starting at: {ROOT_DIR}")
    local_ip = os.popen("ip addr show wlan0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1").read().strip() or "127.0.0.1"
    print(f"✅ Serving at http://{local_ip}:{PORT}")
    os.makedirs(ROOT_DIR, exist_ok=True)
    with HTTPServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()
