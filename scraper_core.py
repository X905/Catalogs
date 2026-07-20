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


# ------------------------- relevancia por texto -------------------------
_STOP = set((
    "de la el los las y con para en un una mg ml grs gr grms gramos unidad unidades "
    "caja cajas pastilla pastillas tableta tabletas capsula capsulas jarabe gel gotero "
    "polvo sobre sobres adulto adultos nino ninos frasco frascos botella lata bebible "
    "inyeccion ampolla paquetes medicamento medicina producto farmacia").split())


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s)


def name_tokens(name):
    """Palabras significativas del nombre del producto (para medir relevancia)."""
    toks = [t for t in _norm(name).split() if len(t) >= 4 and t not in _STOP]
    return toks or [t for t in _norm(name).split() if len(t) >= 3]


def title_matches(title, tokens):
    if not tokens:
        return True
    nt = _norm(title)
    return any(tok in nt for tok in tokens)


# ------------------------- búsqueda de imágenes -------------------------
# Cada búsqueda devuelve una lista de (url, titulo). El titulo (cuando existe)
# se usa para filtrar resultados que no correspondan al producto.

def search_bing(query, want=40):
    # Endpoint asíncrono: devuelve SOLO los resultados reales (sin tendencias).
    url = ("https://www.bing.com/images/async?q=%s&first=0&count=%d&adlt=off&mmasync=1"
           % (urllib.parse.quote(query), want))
    page, _ = http_get(url, {"User-Agent": UA, "Accept-Language": "es,en;q=0.8",
                             "Referer": "https://www.bing.com/images/search"})
    raw = page.decode("utf-8", "ignore")
    out = []
    for block in re.findall(r'm="({&quot;.*?})"', raw):
        try:
            obj = json.loads(html.unescape(block))
        except ValueError:
            continue
        u = obj.get("murl") or obj.get("imgurl")
        if u and u.startswith("http"):
            out.append((u, obj.get("t", "") or ""))
        if len(out) >= want:
            break
    return out


def search_google(query, want=40):
    url = ("https://www.google.com/search?q=%s&tbm=isch&hl=es&gl=us&safe=off"
           % urllib.parse.quote(query))
    page, _ = http_get(url, {"User-Agent": UA, "Accept-Language": "es,en;q=0.8",
                             "Cookie": "CONSENT=YES+1"})
    txt = page.decode("utf-8", "ignore")
    out = []
    for u in re.findall(r'\["(https?://[^"\]]+?)",\d+,\d+\]', txt):
        u = (u.replace("\\u003d", "=").replace("\\u0026", "&").replace("\\/", "/"))
        low = u.lower()
        if "gstatic.com" in low or "google.com" in low or low.endswith(".gif"):
            continue
        if u.startswith("http") and (u, "") not in out:
            out.append((u, ""))  # Google no da título fiable
        if len(out) >= want:
            break
    return out


def search_ddg(query, want=40):
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
        if u.startswith("http"):
            out.append((u, r.get("title", "") or ""))
        if len(out) >= want:
            break
    return out


_SEARCHERS = {"bing": search_bing, "google": search_google, "ddg": search_ddg}


def search_all(query, primary="bing", log=None):
    """Combina resultados de varias fuentes (con título cuando esté disponible)."""
    order = [primary] + [s for s in ("bing", "google", "ddg") if s != primary]
    combined = []
    seen = set()
    for src in order:
        try:
            for u, t in _SEARCHERS[src](query):
                if u not in seen:
                    seen.add(u)
                    combined.append((u, t))
        except (URLError, HTTPError, ValueError, TimeoutError, OSError) as e:
            if log:
                log("  [%s falló: %s]" % (src, str(e)[:80]))
        if len(combined) >= 20:
            break
    return combined


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
    tries = int(opts.get("tries", 6) or 6)
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

        # Ordena por relevancia: primero los resultados cuyo título coincide con
        # el nombre del producto; luego los sin título; al final los que no coinciden.
        toks = name_tokens(name)
        matched = [c for c in candidates if c[1] and title_matches(c[1], toks)]
        unknown = [c for c in candidates if not c[1]]
        rest = [c for c in candidates if c[1] and not title_matches(c[1], toks)]
        ordered = (matched + unknown + rest) if toks else candidates
        if matched:
            log("  %d resultado(s) relevante(s)" % len(matched))

        saved = False
        for url, _title in ordered[:tries]:
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
