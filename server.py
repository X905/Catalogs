#!/usr/bin/env python3
"""
Servidor local para el Catálogo de Productos.

Sirve la app y permite guardar en disco:
  - Imágenes de productos en   assets/img/products/
  - El catálogo en             catalog.json

Y descargar imágenes desde internet (botón "Descargar imágenes" de la app):
  - POST /api/scrape           inicia la descarga en segundo plano
  - GET  /api/scrape/status    progreso
  - POST /api/scrape/stop      detiene

Sin dependencias externas. Solo escucha en localhost (127.0.0.1).

Uso:
    python3 server.py            # puerto 8000
    python3 server.py 8080       # otro puerto
"""
import http.server
import sys
import os
import re
import json
import uuid
import threading
import unicodedata
import webbrowser
from urllib.parse import urlparse, parse_qs, unquote

import scraper_core as core

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "assets", "img", "products")
CATALOG_FILE = os.path.join(ROOT, "catalog.json")
PHARMACIES_FILE = os.path.join(ROOT, "pharmacies.json")
os.makedirs(IMG_DIR, exist_ok=True)


def load_pharmacies():
    if not os.path.exists(PHARMACIES_FILE):
        return {}
    try:
        with open(PHARMACIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except Exception:
        return {}

EXT_BY_MIME = {
    "image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg",
    "image/webp": "webp", "image/gif": "gif", "image/svg+xml": "svg",
    "image/avif": "avif", "image/bmp": "bmp",
}
MAX_UPLOAD = 20 * 1024 * 1024

# ---- estado compartido de la descarga (scraping) ----
LOCK = threading.Lock()
SCRAPE = {"running": False, "stop": False, "state": {}, "log": [], "summary": None}


def slugify(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "img"


def save_catalog_disk(catalog):
    tmp = CATALOG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CATALOG_FILE)


def run_scrape(opts):
    def on_prog(st):
        with LOCK:
            SCRAPE["state"] = st

    def logf(msg):
        with LOCK:
            SCRAPE["log"].append(str(msg))
            del SCRAPE["log"][:-60]

    def should_stop():
        return SCRAPE["stop"]

    try:
        if not os.path.exists(CATALOG_FILE):
            logf("No hay catalog.json; guarda el catálogo primero.")
            return
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            catalog = json.load(f)
        opts["pharmacies"] = load_pharmacies()
        summary = core.scrape_catalog(
            catalog, ROOT, IMG_DIR, opts,
            on_progress=on_prog, should_stop=should_stop,
            save_fn=save_catalog_disk, log=logf,
        )
        with LOCK:
            SCRAPE["summary"] = summary
    except Exception as e:  # noqa: BLE001
        logf("Error: %s" % str(e)[:160])
    finally:
        with LOCK:
            SCRAPE["running"] = False


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

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

    # ----------------------------- GET -----------------------------
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
        if path == "/api/pharmacies":
            ph = load_pharmacies()
            return self._send_json([
                {"key": k, "label": v.get("label", k)} for k, v in ph.items()
            ])
        if path == "/api/scrape/status":
            with LOCK:
                return self._send_json({
                    "running": SCRAPE["running"],
                    "state": SCRAPE["state"],
                    "log": SCRAPE["log"][-12:],
                    "summary": SCRAPE["summary"],
                })
        return super().do_GET()

    # ----------------------------- POST -----------------------------
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
                json.loads(body.decode("utf-8"))
            except Exception as e:  # noqa: BLE001
                return self._send_json({"error": "JSON inválido: " + str(e)}, 400)
            with open(CATALOG_FILE, "wb") as f:
                f.write(body)
            return self._send_json({"ok": True})

        if path == "/api/scrape":
            with LOCK:
                if SCRAPE["running"]:
                    return self._send_json({"error": "ya hay una descarga en curso"}, 409)
            try:
                opts = json.loads(self._read_body().decode("utf-8") or "{}")
            except Exception:  # noqa: BLE001
                opts = {}
            with LOCK:
                SCRAPE.update({"running": True, "stop": False, "state": {},
                               "log": [], "summary": None})
            threading.Thread(target=run_scrape, args=(opts,), daemon=True).start()
            return self._send_json({"started": True})

        if path == "/api/scrape/stop":
            with LOCK:
                SCRAPE["stop"] = True
            return self._send_json({"stopping": True})

        self.send_error(404, "No encontrado")

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


class Server(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


with Server(("127.0.0.1", PORT), Handler) as httpd:
    url = f"http://localhost:{PORT}/index.html"
    print("=" * 56)
    print("  Catálogo de Productos — Hispanic Foods")
    print(f"  Abriendo: {url}")
    print("  Imágenes -> assets/img/products/   Catálogo -> catalog.json")
    print("  Descargar imágenes: botón en la app (o scrape-images.py)")
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
