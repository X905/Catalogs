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


def _score(title, tokens):
    nt = _norm(title)
    return sum(1 for tok in tokens if tok in nt)


def rank_candidates(candidates, tokens):
    """Ordena (url,titulo) por relevancia: más palabras coincidentes primero,
    luego los que no tienen título, al final los que no coinciden."""
    if not tokens:
        return list(candidates)
    matched, unknown, rest = [], [], []
    for idx, (u, t) in enumerate(candidates):
        if t:
            s = _score(t, tokens)
            (matched if s > 0 else rest).append((s, idx, u, t))
        else:
            unknown.append((u, t))
    matched.sort(key=lambda x: (-x[0], x[1]))
    return [(u, t) for _, _, u, t in matched] + unknown + [(u, t) for _, _, u, t in rest]


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
    """Combina resultados de varios buscadores de imágenes (con título si lo hay)."""
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


# ------------------------- sitios de farmacia -------------------------
def _abs_url(u, base):
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return base.rstrip("/") + u
    return u


RENDER_WAIT_JS = (
    "() => [...document.images].some(i => i.currentSrc && "
    "!/imagenCarga|page_media|loading|placeholder|sprite|logo/i.test(i.currentSrc) && "
    "i.naturalWidth > 40)")


class Renderer:
    """Navegador headless (Playwright para Python) para sitios que cargan con JS.

    Requisito (una vez):
        python -m pip install playwright
        python -m playwright install chromium
    """

    def __init__(self, root, log=None, wait_ms=15000):
        self.log = log or (lambda *_: None)
        self.wait_ms = wait_ms
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise RuntimeError(
                "Falta Playwright para Python. Instálalo con: "
                "python -m pip install playwright  &&  python -m playwright install chromium")
        self._pw = sync_playwright().start()
        opts = {"headless": True}
        if os.environ.get("CHROMIUM_PATH"):
            opts["executable_path"] = os.environ["CHROMIUM_PATH"]
        self.browser = self._pw.chromium.launch(**opts)
        self.ctx = self.browser.new_context(user_agent=UA, locale="es-GT")

    def render(self, url):
        page = self.ctx.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_function(RENDER_WAIT_JS, timeout=self.wait_ms)
            except Exception:
                pass  # seguimos con lo que haya cargado
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            except Exception:
                pass
            page.wait_for_timeout(1200)
            return page.content()
        except Exception as e:  # noqa: BLE001
            self.log("  render falló: %s" % str(e)[:100])
            return ""
        finally:
            try:
                page.close()
            except Exception:
                pass

    def close(self):
        try:
            self.browser.close()
        except Exception:
            pass
        try:
            self._pw.stop()
        except Exception:
            pass


def vtex_search(domain, query, want=10):
    """Farmacias con plataforma VTEX: API pública de catálogo (JSON, fiable)."""
    url = ("https://%s/api/catalog_system/pub/products/search?ft=%s&_from=0&_to=%d"
           % (domain, urllib.parse.quote(query), max(0, want - 1)))
    data, _ = http_get(url, {"User-Agent": UA, "Accept": "application/json",
                             "Referer": "https://%s/" % domain})
    arr = json.loads(data.decode("utf-8", "ignore"))
    out = []
    for p in arr:
        name = p.get("productName", "") or ""
        img = ""
        for it in p.get("items", []):
            imgs = it.get("images", [])
            if imgs:
                img = imgs[0].get("imageUrl", "") or ""
                break
        if img.startswith("http"):
            out.append((img, name))
        if len(out) >= want:
            break
    return out


_IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
_SKIP_IMG = ("logo", "sprite", "icon", "placeholder", "banner", "loading", "blank",
             "no-image", "noimage", "avatar", "flag")


def _attr(tag, name):
    m = (re.search(r'%s\s*=\s*"([^"]*)"' % name, tag, re.I)
         or re.search(r"%s\s*=\s*'([^']*)'" % name, tag, re.I))
    return m.group(1) if m else ""


def _decode_next_image(u):
    """Next.js sirve imágenes como /_next/image?url=<real-codificada>&w=..&q=..
    Devuelve la imagen real (así se obtiene la de mejor calidad y se deduplica)."""
    m = re.search(r"/_next/image\?[^\"']*?url=([^&\"']+)", u)
    if m:
        return urllib.parse.unquote(m.group(1))
    return u


def html_search(cfg, query, want=12, fetch_page=None):
    """Descarga la página de resultados del sitio y extrae (imagen, nombre).

    Por defecto lee las etiquetas <img> (soporta carga diferida y usa el texto
    alternativo como nombre). Se puede afinar con 'image_regex' en la config.
    Si se pasa fetch_page (navegador headless), obtiene el HTML ya renderizado.
    """
    base = cfg.get("base", "")
    url = cfg["search_url"].replace("{q}", urllib.parse.quote(query))
    if fetch_page is not None:
        txt = fetch_page(url)
    else:
        page, _ = http_get(url, {"User-Agent": UA, "Accept-Language": "es,en;q=0.8",
                                 "Referer": base + "/" if base else ""})
        txt = page.decode("utf-8", "ignore")
    if not txt:
        return []

    # Modo avanzado: regex a medida (captura la URL de imagen).
    if cfg.get("image_regex"):
        out, seen = [], set()
        for u in re.findall(cfg["image_regex"], txt):
            u = _abs_url(html.unescape(u), base)
            if u.startswith("http") and u not in seen:
                seen.add(u)
                out.append((u, ""))
            if len(out) >= want:
                break
        return out

    must = [s.lower() for s in cfg.get("must_contain", []) if s]
    skip_extra = [s.lower() for s in cfg.get("skip_contains", []) if s]

    # 1) pares (url, nombre) desde las etiquetas <img> (con carga diferida)
    lazy_attrs = ("data-src", "data-original", "data-lazy", "data-lazy-src",
                  "data-echo", "data-image", "data-img", "data-thumb", "src")
    pairs, seen = [], set()
    for tag in _IMG_TAG.findall(txt):
        alt = _attr(tag, "alt")
        if any(x in alt.lower() for x in _SKIP_IMG):  # p.ej. alt="logo"
            continue
        src = ""
        for a in lazy_attrs:
            v = _attr(tag, a)
            if v and not v.startswith("data:"):
                src = v
                break
        if not src:
            ss = _attr(tag, "srcset") or _attr(tag, "data-srcset")
            if ss:
                src = ss.split(",")[0].strip().split(" ")[0]
        if src:
            u = _decode_next_image(_abs_url(html.unescape(src), base))
            if u.startswith("http") and u not in seen:
                seen.add(u)
                pairs.append((u, alt))
    # 2) además, URLs de imagen embebidas en JSON/scripts (incluye /_next/image)
    raw_urls = re.findall(
        r'https?:\\?/\\?/[^\s"\'<>()\\]+?\.(?:jpg|jpeg|png|webp)(?:\?[^\s"\'<>()\\]*)?', txt, re.I)
    raw_urls += re.findall(r'/_next/image\?[^\s"\'<>()\\]+', txt)
    for u in raw_urls:
        u = _decode_next_image(u.replace("\\/", "/"))
        if u.startswith("http") and u not in seen:
            seen.add(u)
            pairs.append((u, ""))

    # 3) frecuencia (una imagen repetida en muchas tarjetas = logo/mascota)
    freq = {}
    for u, _ in pairs:
        freq[u] = freq.get(u, 0) + 1

    out = []
    for u, alt in pairs:
        low = u.lower()
        if any(x in low for x in _SKIP_IMG) or any(x in low for x in skip_extra):
            continue
        if not re.search(r"\.(jpg|jpeg|png|webp)", low):
            continue
        if freq.get(u, 1) > 4:            # se repite mucho -> placeholder/logo
            continue
        if must and not any(x in low for x in must):  # filtro opcional por ruta
            continue
        out.append((u, alt))
        if len(out) >= want:
            break
    return out


def site_search(cfg, query, log=None, fetch_page=None):
    try:
        if cfg.get("type") == "vtex":
            return vtex_search(cfg["domain"], query)
        return html_search(cfg, query, fetch_page=fetch_page)
    except (URLError, HTTPError, ValueError, TimeoutError, OSError, KeyError) as e:
        if log:
            log("  [%s falló: %s]" % (cfg.get("label", "sitio"), str(e)[:80]))
        return []


def find_images(source, query, pharmacies=None, log=None, fetch_page=None):
    """Punto de entrada único: buscador de imágenes o sitio de farmacia.

    source: 'bing' | 'google' | 'ddg'  ó  'pharmacy:CLAVE'
    """
    pharmacies = pharmacies or {}
    if source and source.startswith("pharmacy:"):
        key = source.split(":", 1)[1]
        cfg = pharmacies.get(key)
        if not cfg:
            if log:
                log("  farmacia no configurada: %s" % key)
            return []
        return site_search(cfg, query, log=log, fetch_page=fetch_page)
    return search_all(query, source or "bing", log=log)


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
    pharmacies = opts.get("pharmacies") or {}
    is_site = bool(source) and source.startswith("pharmacy:")
    log = log or (lambda *_: None)

    # Navegador headless (una sola vez) si la farmacia carga su contenido con JS.
    site_cfg = pharmacies.get(source.split(":", 1)[1]) if is_site else None
    renderer = None
    fetch_page = None
    if site_cfg and site_cfg.get("render"):
        try:
            log("Iniciando navegador (Chromium)…")
            renderer = Renderer(root, log=log)
            fetch_page = renderer.render
        except Exception as e:  # noqa: BLE001
            log("No se pudo iniciar el navegador: %s" % str(e)[:120])
            log("Instálalo: python -m pip install playwright && python -m playwright install chromium")

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
        # En sitios de farmacia se busca el nombre normalizado (sin el sufijo);
        # en buscadores de imágenes se añade el sufijo para afinar.
        query = _norm(name) if is_site else (name + " " + suffix).strip()
        log("[%d/%d] %s" % (i, total, name))
        if on_progress:
            on_progress({"i": i, "total": total, "name": name, "ok": ok, "fail": fail, "status": "searching"})

        try:
            candidates = find_images(source, query, pharmacies, log=log, fetch_page=fetch_page)
        except Exception as e:  # noqa: BLE001
            candidates = []
            log("  búsqueda falló: %s" % str(e)[:100])

        # Ordena por relevancia: primero los que más palabras del nombre comparten
        # con el título; luego los sin título; al final los que no coinciden.
        toks = name_tokens(name)
        ordered = rank_candidates(candidates, toks)

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

    if renderer:
        renderer.close()

    summary = {"total": total, "ok": ok, "fail": fail, "status": "finished"}
    if on_progress:
        on_progress(dict(summary, i=total, name=""))
    return summary
