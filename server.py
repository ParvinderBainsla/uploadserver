from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

os.chdir("uploads")  # Serve files from uploads directory

server_address = ('', 8090)  # Change port if needed
httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
print("Serving on port 8090...")
httpd.serve_forever()
