/*
 * Exportación de PDF sin abrir el navegador (opcional / para automatizar).
 *
 * Requisitos (una sola vez):
 *     npm install
 *     npx playwright install chromium
 *
 * Uso:
 *     node export-pdf.mjs                       -> catalogo.pdf (con precios, datos actuales)
 *     node export-pdf.mjs --sin-precio          -> versión sin precios
 *     node export-pdf.mjs --data catalogo.json  -> usa un catálogo exportado desde la app
 *     node export-pdf.mjs --out mi-catalogo.pdf -> nombre de salida
 *
 * Nota: la app guarda tus cambios en el navegador (localStorage). Para exportar
 * exactamente lo que editaste, primero pulsa "Exportar JSON" en la app y pásalo
 * aquí con --data.
 */
import { chromium } from "playwright";
import { fileURLToPath } from "url";
import { dirname, resolve } from "path";
import { readFileSync, existsSync } from "fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const has = (f) => args.includes(f);
const val = (f, d) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : d; };

const sinPrecio = has("--sin-precio");
// Por defecto usa catalog.json (lo que guardó el servidor) si existe.
const defaultData = existsSync(resolve(__dirname, "catalog.json")) ? resolve(__dirname, "catalog.json") : null;
const dataFile = val("--data", defaultData);
const outFile = val("--out", sinPrecio ? "catalogo-sin-precio.pdf" : "catalogo.pdf");
const STORAGE_KEY = "hispanic_catalog_v1";

const browser = await chromium.launch();
const page = await browser.newPage();
const indexUrl = "file://" + resolve(__dirname, "index.html");
await page.goto(indexUrl, { waitUntil: "networkidle" });

// Inyectar un catálogo exportado, si se indicó
if (dataFile) {
  const json = readFileSync(resolve(process.cwd(), dataFile), "utf8");
  await page.evaluate(([k, v]) => localStorage.setItem(k, v), [STORAGE_KEY, json]);
  await page.reload({ waitUntil: "networkidle" });
}

// Ajustar con/sin precios
await page.evaluate((sin) => {
  const cb = document.getElementById("priceToggle");
  if (cb && cb.checked === sin) cb.click();
}, sinPrecio);
await page.waitForTimeout(400);

await page.emulateMedia({ media: "print" });
await page.pdf({
  path: resolve(process.cwd(), outFile),
  width: "8.5in",
  height: "11in",
  printBackground: true,
});
console.log("PDF generado: " + outFile);
await browser.close();
