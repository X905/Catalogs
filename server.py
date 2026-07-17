#!/usr/bin/env python3
"""
Servidor local para el Catálogo de Productos.
Sirve la carpeta actual y abre el navegador. Sin dependencias externas.

Uso:
    python3 server.py            # usa el puerto 8000
    python3 server.py 8080       # usa otro puerto
"""
import http.server
import socketserver
import sys
import webbrowser
import os

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass  # silencioso


with socketserver.TCPServer(("", PORT), Handler) as httpd:
    url = f"http://localhost:{PORT}/index.html"
    print("=" * 52)
    print("  Catálogo de Productos — Hispanic Foods")
    print(f"  Abriendo: {url}")
    print("  Detén el servidor con Ctrl+C")
    print("=" * 52)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
