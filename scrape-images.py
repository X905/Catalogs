#!/usr/bin/env python3
"""
Descarga automáticamente la imagen de cada producto del catálogo desde
internet y la guarda en assets/img/products/, actualizando catalog.json.

Busca en Bing Imágenes (y DuckDuckGo como respaldo) usando el nombre del
producto, descarga la primera imagen válida y la asocia al producto.

Requisitos: solo Python 3 (librería estándar) e internet. Sin instalar nada.

Uso básico (descarga solo los productos que NO tienen imagen):
    python3 scrape-images.py

Opciones:
    --all                Vuelve a descargar aunque el producto ya tenga imagen
    --only "CATEGORÍA"   Solo esa categoría (por nombre, parcial)
    --limit N            Procesa como máximo N productos
    --suffix "texto"     Texto extra en la búsqueda (p.ej. "medicamento caja")
    --source bing|ddg    Fuente principal (por defecto bing; usa la otra de respaldo)
    --delay 1.5          Segundos de espera entre productos
    --tries 4            Cuántas imágenes candidatas intentar por producto
    --min-bytes 2500     Tamaño mínimo para aceptar una imagen
    --dry-run            Solo muestra qué buscaría, sin descargar
    --catalog ruta.json  Archivo de catálogo (por defecto catalog.json)

Consejo: abre la app con 'python3 server.py' una vez para crear catalog.json;
si no existe, este script intenta generarlo desde assets/js/seed.js.
"""
import os
import sys
import json
import argparse

import scraper_core as core

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(ROOT, "assets", "img", "products")


def ensure_catalog(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
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


def main():
    ap = argparse.ArgumentParser(description="Descarga imágenes de productos desde internet.")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--suffix", default="")
    ap.add_argument("--source", choices=["bing", "google", "ddg"], default="bing")
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--tries", type=int, default=6)
    ap.add_argument("--min-bytes", type=int, default=2500)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--catalog", default=os.path.join(ROOT, "catalog.json"))
    args = ap.parse_args()

    catalog = ensure_catalog(args.catalog)

    if args.dry_run:
        todo = core.build_todo(catalog, args.all, args.only, args.limit)
        print("Productos a procesar: %d (dry-run)" % len(todo))
        for i, p in enumerate(todo, 1):
            q = (p.get("name", "") + " " + args.suffix).strip()
            print("[%d/%d] %s  →  \"%s\"" % (i, len(todo), p.get("name", ""), q))
        return

    opts = {
        "all": args.all, "only": args.only, "limit": args.limit,
        "suffix": args.suffix, "source": args.source, "delay": args.delay,
        "tries": args.tries, "min_bytes": args.min_bytes,
    }
    summary = core.scrape_catalog(
        catalog, ROOT, IMG_DIR, opts,
        save_fn=lambda c: save_catalog(args.catalog, c),
        log=lambda msg: print(msg),
    )
    print("\nListo. Descargadas: %d  |  Sin imagen: %d" % (summary["ok"], summary["fail"]))
    print("Actualizado: %s" % args.catalog)
    print("Abre/recarga la app para ver las imágenes.")


if __name__ == "__main__":
    main()
