#!/usr/bin/env python3
"""
Servidor local para el Catálogo de Productos.

Sirve la app y además permite guardar en disco:
  - Las imágenes de los productos en  assets/img/products/
  - El catálogo completo en           catalog.json

Sin dependencias externas (solo la librería estándar de Python).

Uso:
    python3 server.py            # puerto 8000
    python3 server.py 8080       # otro puerto

Solo escucha en localhost (127.0.0.1).
"""
import http.server
import socketserver
import sys
import os
import re
import json
import uuid
import unicodedata
import webbrowser
from urllib.parse import urlparse, parse_qs, unquote

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "assets", "img", "products")
CATALOG_FILE = os.path.join(ROOT, "catalog.json")
os.makedirs(IMG_DIR, exist_ok=True)

EXT_BY_MIME = {
    "image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg",
    "image/webp": "webp", "image/gif": "gif", "image/svg+xml": "svg",
    "image/avif": "avif", "image/bmp": "bmp",
}
MAX_UPLOAD = 20 * 1024 * 1024  # 20 MB por imagen


def slugify(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "img"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    # --- helpers ---
    def _send_json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        return self.rfile.read(length) if length else b""

    # --- rutas ---
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/catalog":
            if os.path.exists(CATALOG_FILE):
                with open(CATALOG_FILE, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self._send_json({"empty": True})
            return
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/upload":
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length <= 0 or length > MAX_UPLOAD:
                return self._send_json({"error": "tamaño inválido"}, 400)
            data = self.rfile.read(length)
            mime = self.headers.get("Content-Type", "image/png").split(";")[0].strip()
            ext = EXT_BY_MIME.get(mime, "png")
            name = unquote(query.get("name", ["img"])[0])
            old = unquote(query.get("old", [""])[0])
            filename = slugify(name) + "-" + uuid.uuid4().hex[:6] + "." + ext
            with open(os.path.join(IMG_DIR, filename), "wb") as f:
                f.write(data)
            # borra la imagen anterior si estaba en la carpeta de productos
            if old.startswith("assets/img/products/"):
                old_abs = os.path.abspath(os.path.join(ROOT, old))
                if old_abs.startswith(IMG_DIR + os.sep) and os.path.exists(old_abs):
                    try:
                        os.remove(old_abs)
                    except OSError:
                        pass
            return self._send_json({"path": "assets/img/products/" + filename})

        if path == "/api/catalog":
            body = self._read_body()
            try:
                json.loads(body.decode("utf-8"))  # validar que sea JSON
            except Exception as e:
                return self._send_json({"error": "JSON inválido: " + str(e)}, 400)
            with open(CATALOG_FILE, "wb") as f:
                f.write(body)
            return self._send_json({"ok": True})

        self.send_error(404, "No encontrado")

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass  # silencioso


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    url = f"http://localhost:{PORT}/index.html"
    print("=" * 56)
    print("  Catálogo de Productos — Hispanic Foods")
    print(f"  Abriendo: {url}")
    print(f"  Imágenes -> assets/img/products/")
    print(f"  Catálogo -> catalog.json")
    print("  Detén el servidor con Ctrl+C")
    print("=" * 56)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
