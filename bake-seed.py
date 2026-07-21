#!/usr/bin/env python3
"""
Convierte catalog.json (tu catálogo actual, con imágenes y precios) en
assets/js/seed.js, que son los datos que se cargan por defecto al abrir la app.

Úsalo antes de PUBLICAR (por ejemplo en GitHub Pages) para que quien abra la
página vea el catálogo completo con las fotos ya puestas.

Uso:
    python3 bake-seed.py

Después, sube al repositorio:
    - assets/js/seed.js            (los datos por defecto)
    - assets/img/products/*.jpg    (las imágenes descargadas)
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(ROOT, "catalog.json")
SEED = os.path.join(ROOT, "assets", "js", "seed.js")

if not os.path.exists(CATALOG):
    sys.exit("No existe catalog.json. Abre la app con 'python3 server.py' y edita/"
             "descarga imágenes al menos una vez para generarlo.")

with open(CATALOG, "r", encoding="utf-8") as f:
    catalog = json.load(f)

# Marca de versión: cada vez que horneas, cambia. La app publicada la usa para
# detectar que hay una versión nueva y refrescarse (aunque el visitante tenga
# una copia vieja guardada en su navegador).
catalog["version"] = int(time.time())

# Aviso si hay imágenes incrustadas (base64): pesan mucho en el seed.
inline = sum(1 for c in catalog.get("categories", [])
             for p in c.get("products", [])
             if str(p.get("image", "")).startswith("data:"))

header = ("/* Generado por bake-seed.py desde catalog.json.\n"
          "   Son los datos por defecto del catálogo (portada, categorías,\n"
          "   productos, precios e imágenes). Vuelve a generarlo tras cambios. */\n")
body = "window.CATALOG_SEED = " + json.dumps(catalog, ensure_ascii=False, indent=2) + ";\n"

with open(SEED, "w", encoding="utf-8") as f:
    f.write(header + body)

n_cat = len(catalog.get("categories", []))
n_prod = sum(len(c.get("products", [])) for c in catalog.get("categories", []))
n_img = sum(1 for c in catalog.get("categories", [])
            for p in c.get("products", []) if p.get("image"))
print("seed.js actualizado: %d categorías, %d productos, %d con imagen." % (n_cat, n_prod, n_img))
if inline:
    print("Aviso: %d imágenes están incrustadas (base64) y harán el seed.js muy "
          "grande. Idealmente usa imágenes como archivos en assets/img/products/." % inline)
