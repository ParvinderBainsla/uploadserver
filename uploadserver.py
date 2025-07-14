import os
import platform
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, quote
from email.parser import BytesParser
from email.policy import default

# 👇 Automatically set root directory based on platform
if "Android" in platform.platform():
    ROOT_DIR = "/sdcard"
else:
    ROOT_DIR = os.path.expanduser("~")

PORT = 8090

class FileExplorerHandler(BaseHTTPRequestHandler):
    def _send_html_response(self, content):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_GET(self):
        path = unquote(self.path)
        fs_path = os.path.join(ROOT_DIR, path.lstrip("/"))

        if os.path.isfile(fs_path):
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.end_headers()
            with open(fs_path, "rb") as f:
                self.wfile.write(f.read())
            return

        if not os.path.exists(fs_path):
            self.send_error(404, "File or directory not found")
            return

        entries = os.listdir(fs_path)
        entries.sort()

        body = f"<h1>📁 Index of {path}</h1><ul>"
        if path != "/":
            parent = os.path.dirname(path.rstrip("/"))
            body += f'<li><a href="/{quote(parent)}">⬅️ Parent Directory</a></li>'

        for entry in entries:
            full_path = os.path.join(fs_path, entry)
            display_name = entry + ("/" if os.path.isdir(full_path) else "")
            href = quote(os.path.join(path, entry))
            body += f'<li><a href="/{href}">{display_name}</a></li>'

        body += "</ul><h2>⬆️ Upload File</h2>"
        body += ("""
        <form enctype="multipart/form-data" method="POST">
            <input name="file" type="file"/>
            <input type="submit" value="Upload"/>
        </form>""")

        self._send_html_response(body)

    def do_POST(self):
        path = unquote(self.path)
        save_path = os.path.join(ROOT_DIR, path.lstrip("/"))

        if not os.path.isdir(save_path):
            self.send_error(400, "Uploads allowed only to folders")
            return

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
                filename = disposition.params.get("filename") if disposition else None
                if filename:
                    filename = os.path.basename(filename)
                    filepath = os.path.join(save_path, filename)
                    with open(filepath, "wb") as f:
                        f.write(file_data.strip(b"\r\n--"))
                    self._send_html_response(f"<p>✅ File '{filename}' uploaded.</p><a href='/'>Go Back</a>")
                    return

        self.send_error(400, "No valid file uploaded")

if __name__ == "__main__":
    print(f"📁 Browsing from: {ROOT_DIR}")
    print(f"✅ Serving at http://0.0.0.0:{PORT}")
    with HTTPServer(("0.0.0.0", PORT), FileExplorerHandler) as httpd:
        httpd.serve_forever()
