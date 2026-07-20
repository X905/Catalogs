/*
 * Renderizador de páginas con navegador (para sitios que cargan su contenido
 * con JavaScript, como Farmacias Batres). Lo usa scrape-images.py / server.py
 * cuando una farmacia tiene "render": true en pharmacies.json.
 *
 * Protocolo (stdin/stdout, una línea por petición):
 *   - Al arrancar imprime:            READY
 *   - Recibe por stdin:               una URL por línea
 *   - Responde por stdout:            OK <html-en-base64>   ó   ERR <mensaje>
 *
 * Requisitos (una sola vez):  npm install  &&  npx playwright install chromium
 */
import pw from "playwright";
import readline from "readline";

const { chromium } = pw;
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

const launchOpts = { headless: true };
if (process.env.CHROMIUM_PATH) launchOpts.executablePath = process.env.CHROMIUM_PATH;
const browser = await chromium.launch(launchOpts);
const ctx = await browser.newContext({ userAgent: UA, locale: "es-GT" });

process.stdout.write("READY\n");

const rl = readline.createInterface({ input: process.stdin });
for await (const line of rl) {
  const url = line.trim();
  if (!url) continue;
  let page;
  try {
    page = await ctx.newPage();
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
    // Espera a que aparezca alguna imagen real (no el placeholder "imagenCarga")
    await page.waitForFunction(() => {
      return [...document.images].some((i) =>
        i.currentSrc &&
        !/imagenCarga|page_media|loading|placeholder/i.test(i.currentSrc) &&
        i.naturalWidth > 40);
    }, { timeout: 15000 }).catch(() => {});
    // pequeño scroll para disparar carga diferida
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)).catch(() => {});
    await page.waitForTimeout(1200);
    const html = await page.content();
    await page.close();
    process.stdout.write("OK " + Buffer.from(html, "utf8").toString("base64") + "\n");
  } catch (e) {
    if (page) { try { await page.close(); } catch (_) {} }
    process.stdout.write("ERR " + String(e && e.message || e).slice(0, 140) + "\n");
  }
}

await browser.close();
