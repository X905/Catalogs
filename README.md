# Catálogo de Productos — Hispanic Foods

Aplicación local para **crear y mantener el catálogo de productos** (medicina) y
**exportarlo a PDF** conservando el mismo estilo del catálogo original: portada
con logo y franjas de color, banners de categoría con su color de acento, grilla
de tarjetas en 3 columnas y pie de página en cada hoja.

Incluye dos versiones con un solo clic: **con precios** y **sin precios**.

![vista](assets/img/logo.png)

---

## Cómo levantarlo localmente

No necesita compilar nada. Tienes tres formas, de la más simple a la más completa:

### 1. Abrir directamente (lo más rápido)
Haz doble clic en **`index.html`**. Se abre en tu navegador y funciona.
Los datos se guardan en el propio navegador.

> Si tu navegador bloquea la carga de la fuente al abrir con `file://`,
> usa la opción 2 (servidor local).

### 2. Servidor local con Python (recomendado)
```bash
python3 server.py
```
Abre automáticamente `http://localhost:8000/index.html`.
Para otro puerto: `python3 server.py 8080`.

### 3. Servidor con Node
```bash
npx serve -l 8000 .
```

---

## Cómo se usa

- **Panel izquierdo (editor):**
  - *Portada y contacto:* nombre de empresa, título, subtítulo, dirección,
    teléfono, correo y logo.
  - *Categorías y productos:* despliega una categoría para editar su nombre,
    su color de acento y sus productos. En cada producto puedes cambiar el
    nombre, el precio y la imagen (clic en la miniatura para subirla; clic
    derecho para quitarla).
  - Botones para **añadir categoría**, subir/bajar categorías y **añadir
    productos**.
- **Barra superior:**
  - **Mostrar precios:** alterna entre la versión *con precios* y *sin precios*
    (en la versión sin precios aparece la nota «Imágenes con fines ilustrativos»).
  - **Zoom** de la previsualización.
  - **Importar / Exportar JSON:** guarda o carga todo el catálogo como archivo,
    para respaldarlo o moverlo entre computadoras.
  - **Exportar PDF.**

### Precios
El precio admite un número (`25`, `12.50`, se muestra como `$25.00`) o texto
libre como `Consultar precio`. Si lo dejas vacío, no se muestra precio.

---

## Exportar a PDF

### Opción A — desde la app (recomendada)
1. Pulsa **«Exportar PDF»** en la barra superior.
2. En el diálogo de impresión elige **«Guardar como PDF»** como destino.
3. Ajustes recomendados: **Tamaño Carta (Letter)**, **Márgenes: Ninguno** y
   activa **«Gráficos de fondo»** para que se impriman los colores.

El documento ya viene paginado (portada + una o varias hojas por categoría) con
el pie de página en cada hoja.

### Opción B — sin abrir el navegador (para automatizar)
Requiere Node y, una sola vez:
```bash
npm install
npx playwright install chromium
```
Luego:
```bash
node export-pdf.mjs                        # con precios
node export-pdf.mjs --sin-precio           # sin precios
node export-pdf.mjs --data catalogo.json   # usa un catálogo exportado
node export-pdf.mjs --out final.pdf        # nombre de salida
```
> Para exportar exactamente lo que editaste en la app, primero pulsa
> **«Exportar JSON»** y pásalo con `--data`.

---

## Estructura del proyecto

```
Catalogs/
├── index.html              App (editor + previsualización)
├── server.py               Servidor local en Python (sin dependencias)
├── export-pdf.mjs          Exportador de PDF headless (opcional)
├── package.json
├── assets/
│   ├── css/
│   │   ├── catalog.css      Sistema de diseño (pantalla + impresión)
│   │   └── fonts.css        Fuente Oswald embebida (funciona sin internet)
│   ├── js/
│   │   ├── seed.js          Datos iniciales del catálogo (editable)
│   │   └── app.js           Lógica de la aplicación
│   └── img/
│       └── logo.png         Logo de Hispanic Foods
└── README.md
```

## Datos incluidos

Vienen precargadas las **14 categorías** del catálogo con su color de acento, y
la categoría **«Analgésicos y dolor»** con sus **41 productos y precios** como
ejemplo real. Las demás categorías están listas para que agregues sus productos
desde el editor (o importando un JSON).

Para restablecer todo a los datos originales usa **«Restablecer al catálogo
original»** al final del panel izquierdo.
