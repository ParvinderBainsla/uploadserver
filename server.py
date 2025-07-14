import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
import cgi

UPLOAD_DIR = "uploads"
PORT = 8090

class CustomHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/upload':
            self.send_error(404, "File not found.")
            return

        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        if ctype != 'multipart/form-data':
            self.send_error(400, "Bad request")
            return

        pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
        pdict['CONTENT-LENGTH'] = int(self.headers.get('content-length'))
        fields = cgi.parse_multipart(self.rfile, pdict)

        upload_file = fields.get('file')
        if not upload_file:
            self.send_error(400, "No file uploaded")
            return

        filename = fields.get('filename', ['uploaded_file'])[0]
        filepath = os.path.join(UPLOAD_DIR, os.path.basename(filename))
        with open(filepath, 'wb') as f:
            f.write(upload_file[0])

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Upload successful.")

    def do_GET(self):
        return super().do_GET()

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

os.chdir(UPLOAD_DIR)

httpd = HTTPServer(('', PORT), CustomHandler)
print(f"Serving on port {PORT}...")
httpd.serve_forever()
