#!/usr/bin/env python3
"""
Descarga automáticamente la imagen de cada producto del catálogo desde
internet y la guarda en assets/img/products/, actualizando catalog.json.

Busca imágenes en Bing Imágenes (y DuckDuckGo como respaldo) usando el nombre
del producto, descarga la primera imagen válida y la asocia al producto.

Requisitos: solo Python 3 (librería estándar) e internet. Sin instalar nada.

Uso básico (descarga solo los productos que NO tienen imagen):
    python3 scrape-images.py

Opciones:
    --all                Vuelve a descargar aunque el producto ya tenga imagen
    --only "CATEGORÍA"   Solo esa categoría (por nombre, parcial)
    --limit N            Procesa como máximo N productos
    --suffix "texto"     Texto extra en la búsqueda (p.ej. "medicamento caja")
    --source bing|ddg    Fuente principal (por defecto: bing; usa la otra como respaldo)
    --delay 1.5          Segundos de espera entre productos (por defecto 1.5)
    --tries 4            Cuántas imágenes candidatas intentar por producto
    --min-bytes 2500     Tamaño mínimo para aceptar una imagen
    --dry-run            Solo muestra qué buscaría, sin descargar
    --catalog ruta.json  Archivo de catálogo (por defecto catalog.json)

Consejo: primero abre la app con el servidor (python3 server.py) al menos una
vez para que exista catalog.json; si no existe, este script intenta crearlo a
partir de assets/js/seed.js.
"""
import os
import re
import sys
import ssl
import json
import time
import html
import uuid
import argparse
import unicodedata
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "assets", "img", "products")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# firmas de imagen -> extensión (para validar y nombrar el archivo)
MAGIC = [
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF87a", "gif"), (b"GIF89a", "gif"),
    (b"RIFF", "webp"),  # se confirma con 'WEBP' en bytes 8..12
    (b"BM", "bmp"),
]
_ssl_ctx = ssl.create_default_context()


# ----------------------------- utilidades -----------------------------
def slugify(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "img"


def http_get(url, headers=None, timeout=25):
    """Devuelve (bytes, content_type). Lanza excepción si falla."""
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as r:
        return r.read(), r.headers.get("Content-Type", "")


def detect_ext(data, content_type=""):
    for sig, ext in MAGIC:
        if data.startswith(sig):
            if ext == "webp" and data[8:12] != b"WEBP":
                continue
            return ext
    ct = (content_type or "").lower()
    if "png" in ct: return "png"
    if "jpeg" in ct or "jpg" in ct: return "jpg"
    if "gif" in ct: return "gif"
    if "webp" in ct: return "webp"
    if "svg" in ct: return "svg"
    return None


# ------------------------- búsqueda de imágenes -------------------------
def search_bing(query, want=12):
    url = ("https://www.bing.com/images/search?q=%s&form=HDRSC2&first=1"
           % urllib.parse.quote(query))
    page, _ = http_get(url, {"User-Agent": UA, "Accept-Language": "es,en;q=0.8"})
    text = html.unescape(page.decode("utf-8", "ignore"))
    urls = re.findall(r'"murl":"(.*?)"', text)
    # descarta miniaturas/base64
    out = []
    for u in urls:
        u = u.replace("\\/", "/")
        if u.startswith("http") and u not in out:
            out.append(u)
        if len(out) >= want:
            break
    return out


def search_ddg(query, want=12):
    # 1) token vqd
    home = ("https://duckduckgo.com/?q=%s&iax=images&ia=images"
            % urllib.parse.quote(query))
    page, _ = http_get(home, {"User-Agent": UA})
    txt = page.decode("utf-8", "ignore")
    m = (re.search(r'vqd=["\']([\d-]+)["\']', txt)
         or re.search(r'vqd=([\d-]+)\&', txt)
         or re.search(r'vqd=([\d-]+)', txt))
    if not m:
        return []
    vqd = m.group(1)
    api = ("https://duckduckgo.com/i.js?l=us-en&o=json&q=%s&vqd=%s&f=,,,&p=1"
           % (urllib.parse.quote(query), vqd))
    data, _ = http_get(api, {"User-Agent": UA, "Referer": "https://duckduckgo.com/"})
    j = json.loads(data.decode("utf-8", "ignore"))
    out = []
    for r in j.get("results", []):
        u = r.get("image", "")
        if u.startswith("http") and u not in out:
            out.append(u)
        if len(out) >= want:
            break
    return out


def search_all(query, primary):
    """Fuente principal + respaldo, sin repetir errores fatales."""
    order = [primary] + [s for s in ("bing", "ddg") if s != primary]
    urls = []
    for src in order:
        try:
            found = (search_bing if src == "bing" else search_ddg)(query)
            for u in found:
                if u not in urls:
                    urls.append(u)
            if urls:
                break
        except (URLError, HTTPError, ValueError, TimeoutError) as e:
            sys.stderr.write("  [%s falló: %s]\n" % (src, str(e)[:80]))
    return urls


# --------------------------- catálogo en disco ---------------------------
def ensure_catalog(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # intentar generarlo desde seed.js con node
    seed = os.path.join(ROOT, "assets", "js", "seed.js")
    if os.path.exists(seed):
        try:
            import subprocess
            subprocess.run(
                ["node", "-e",
                 "global.window={};require('%s');"
                 "require('fs').writeFileSync('%s',JSON.stringify(window.CATALOG_SEED,null,2))"
                 % (seed.replace("\\", "\\\\"), path.replace("\\", "\\\\"))],
                check=True)
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    sys.exit("No existe %s. Abre la app con 'python3 server.py' una vez para "
             "crearlo, o crea el archivo manualmente." % path)


def save_catalog(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# -------------------------------- main --------------------------------
def main():
    ap = argparse.ArgumentParser(add_help=True, description="Descarga imágenes de productos.")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--suffix", default="")
    ap.add_argument("--source", choices=["bing", "ddg"], default="bing")
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--tries", type=int, default=4)
    ap.add_argument("--min-bytes", type=int, default=2500)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--catalog", default=os.path.join(ROOT, "catalog.json"))
    args = ap.parse_args()

    os.makedirs(IMG_DIR, exist_ok=True)
    catalog = ensure_catalog(args.catalog)

    # arma la lista de productos a procesar
    todo = []
    for cat in catalog.get("categories", []):
        if args.only and args.only.lower() not in cat.get("name", "").lower():
            continue
        for p in cat.get("products", []):
            if p.get("image") and not args.all:
                continue
            todo.append((cat, p))
    if args.limit > 0:
        todo = todo[:args.limit]

    if not todo:
        print("No hay productos pendientes. (Usa --all para volver a descargar todo.)")
        return

    print("Productos a procesar: %d  |  fuente: %s%s"
          % (len(todo), args.source, "  (dry-run)" if args.dry_run else ""))
    ok = fail = 0
    failed_names = []

    for i, (cat, p) in enumerate(todo, 1):
        name = p.get("name", "").strip()
        query = (name + " " + args.suffix).strip()
        print("[%d/%d] %s  →  \"%s\"" % (i, len(todo), name, query))
        if args.dry_run:
            continue

        try:
            candidates = search_all(query, args.source)
        except Exception as e:
            candidates = []
            sys.stderr.write("  búsqueda falló: %s\n" % str(e)[:100])

        saved = False
        for url in candidates[:args.tries]:
            try:
                data, ct = http_get(url, {"User-Agent": UA, "Referer": "https://www.bing.com/"})
            except Exception:
                continue
            if len(data) < args.min_bytes:
                continue
            ext = detect_ext(data, ct)
            if not ext:
                continue
            old = p.get("image", "")
            fname = "%s-%s.%s" % (slugify(name), uuid.uuid4().hex[:6], ext)
            with open(os.path.join(IMG_DIR, fname), "wb") as f:
                f.write(data)
            # borra la imagen anterior si estaba en la carpeta de productos
            if old.startswith("assets/img/products/"):
                oa = os.path.abspath(os.path.join(ROOT, old))
                if oa.startswith(IMG_DIR + os.sep) and os.path.exists(oa):
                    try: os.remove(oa)
                    except OSError: pass
            p["image"] = "assets/img/products/" + fname
            print("   ✓ %s (%d KB)" % (fname, len(data) // 1024))
            saved = True
            ok += 1
            break

        if not saved:
            fail += 1
            failed_names.append(name)
            print("   ✗ sin imagen")

        save_catalog(args.catalog, catalog)  # guarda avance tras cada producto
        if i < len(todo):
            time.sleep(args.delay)

    print("\nListo. Descargadas: %d  |  Sin imagen: %d" % (ok, fail))
    if failed_names:
        print("Sin imagen (revísalos a mano): " + ", ".join(failed_names))
    print("Actualizado: %s" % args.catalog)
    print("Abre/recarga la app para ver las imágenes.")


if __name__ == "__main__":
    main()
