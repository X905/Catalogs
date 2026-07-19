#!/usr/bin/env python3
"""
Lógica reutilizable para descargar imágenes de productos desde internet.
La usan tanto scrape-images.py (línea de comandos) como server.py (botón en la app).

Solo usa la librería estándar de Python.
"""
import os
import re
import ssl
import json
import time
import html
import uuid
import unicodedata
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

MAGIC = [
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpg"),
    (b"GIF87a", "gif"), (b"GIF89a", "gif"),
    (b"RIFF", "webp"),
    (b"BM", "bmp"),
]
_ssl_ctx = ssl.create_default_context()


def slugify(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "img"


def http_get(url, headers=None, timeout=20):
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
    out = []
    for u in re.findall(r'"murl":"(.*?)"', text):
        u = u.replace("\\/", "/")
        if u.startswith("http") and u not in out:
            out.append(u)
        if len(out) >= want:
            break
    return out


def search_ddg(query, want=12):
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


def search_all(query, primary="bing", log=None):
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
        except (URLError, HTTPError, ValueError, TimeoutError, OSError) as e:
            if log:
                log("  [%s falló: %s]" % (src, str(e)[:80]))
    return urls


# --------------------------- proceso principal ---------------------------
def build_todo(catalog, all_=False, only="", limit=0):
    todo = []
    for cat in catalog.get("categories", []):
        if only and only.lower() not in cat.get("name", "").lower():
            continue
        for p in cat.get("products", []):
            if p.get("image") and not all_:
                continue
            todo.append(p)
    if limit and limit > 0:
        todo = todo[:limit]
    return todo


def scrape_catalog(catalog, root, img_dir, opts=None, on_progress=None,
                   should_stop=None, save_fn=None, log=None):
    """
    Descarga imágenes para los productos del catálogo (dict, modificado in situ).

    opts: all, only, limit, suffix, source, delay, tries, min_bytes
    on_progress(state): callback con {i,total,name,ok,fail,status}
    should_stop(): devuelve True para detener
    save_fn(catalog): persiste el catálogo (llamado tras cada producto)
    log(msg): registra una línea de texto
    """
    opts = opts or {}
    all_ = bool(opts.get("all"))
    only = opts.get("only", "") or ""
    limit = int(opts.get("limit", 0) or 0)
    suffix = opts.get("suffix", "") or ""
    source = opts.get("source", "bing") or "bing"
    delay = float(opts.get("delay", 1.2) or 0)
    tries = int(opts.get("tries", 4) or 4)
    min_bytes = int(opts.get("min_bytes", 2500) or 2500)
    log = log or (lambda *_: None)

    os.makedirs(img_dir, exist_ok=True)
    todo = build_todo(catalog, all_, only, limit)
    total = len(todo)
    ok = fail = 0

    if on_progress:
        on_progress({"i": 0, "total": total, "name": "", "ok": 0, "fail": 0, "status": "start"})

    for i, p in enumerate(todo, 1):
        if should_stop and should_stop():
            log("Detenido por el usuario.")
            break
        name = (p.get("name") or "").strip()
        query = (name + " " + suffix).strip()
        log("[%d/%d] %s" % (i, total, name))
        if on_progress:
            on_progress({"i": i, "total": total, "name": name, "ok": ok, "fail": fail, "status": "searching"})

        try:
            candidates = search_all(query, source, log=log)
        except Exception as e:  # noqa: BLE001
            candidates = []
            log("  búsqueda falló: %s" % str(e)[:100])

        saved = False
        for url in candidates[:tries]:
            if should_stop and should_stop():
                break
            try:
                data, ct = http_get(url, {"User-Agent": UA, "Referer": "https://www.bing.com/"})
            except Exception:  # noqa: BLE001
                continue
            if len(data) < min_bytes:
                continue
            ext = detect_ext(data, ct)
            if not ext:
                continue
            old = p.get("image", "")
            fname = "%s-%s.%s" % (slugify(name), uuid.uuid4().hex[:6], ext)
            with open(os.path.join(img_dir, fname), "wb") as f:
                f.write(data)
            if old.startswith("assets/img/products/"):
                oa = os.path.abspath(os.path.join(root, old))
                if oa.startswith(img_dir + os.sep) and os.path.exists(oa):
                    try:
                        os.remove(oa)
                    except OSError:
                        pass
            p["image"] = "assets/img/products/" + fname
            log("   OK %s (%d KB)" % (fname, len(data) // 1024))
            saved = True
            ok += 1
            break

        if not saved:
            fail += 1
            log("   sin imagen")

        if save_fn:
            try:
                save_fn(catalog)
            except Exception as e:  # noqa: BLE001
                log("  no se pudo guardar: %s" % str(e)[:80])

        if on_progress:
            on_progress({"i": i, "total": total, "name": name, "ok": ok, "fail": fail,
                         "status": "saved" if saved else "failed"})
        if delay and i < total:
            time.sleep(delay)

    summary = {"total": total, "ok": ok, "fail": fail, "status": "finished"}
    if on_progress:
        on_progress(dict(summary, i=total, name=""))
    return summary
