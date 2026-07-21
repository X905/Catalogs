/* ============================================================
   Catálogo de Productos — Hispanic Foods
   Lógica de la aplicación: estado, editor y previsualización/PDF.
   Sin dependencias externas. Funciona abriendo index.html o con un
   servidor local. Los datos se guardan en localStorage.
   ============================================================ */
(function () {
  "use strict";

  var STORAGE_KEY = "hispanic_catalog_v1";
  // Productos por hoja. La primera hoja de cada categoría lleva el banner,
  // por eso caben menos tarjetas que en las hojas de continuación.
  var FIRST_PAGE = 12;
  var CONT_PAGE = 15;
  var ACCENTS = ["orange", "coral", "gold", "green", "teal", "cyan"];
  var ACCENT_LABEL = {
    orange: "Naranja", coral: "Coral", gold: "Dorado",
    green: "Verde", teal: "Turquesa", cyan: "Celeste"
  };

  var state = null;
  var openCats = {}; // categorías expandidas en el editor

  /* ---------------- utilidades ---------------- */
  function uid(p) { return (p || "id") + "-" + Math.random().toString(36).slice(2, 9); }
  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt != null) n.textContent = txt;
    return n;
  }
  function deepClone(o) { return JSON.parse(JSON.stringify(o)); }

  function normalize(data) {
    // garantiza ids y estructura
    data.settings = data.settings || { showPrices: true, currency: "$" };
    if (typeof data.settings.showPrices !== "boolean") data.settings.showPrices = true;
    data.settings.currency = data.settings.currency || "$";
    (data.categories || []).forEach(function (c) {
      if (!c.id) c.id = uid("cat");
      if (!c.accent) c.accent = "orange";
      c.products = c.products || [];
      c.products.forEach(function (p) { if (!p.id) p.id = uid("p"); if (p.price == null) p.price = ""; });
    });
    return data;
  }

  // ¿Hay un backend (server.py) detrás? Se detecta al arrancar con un "ping".
  // Con servidor: imágenes y catálogo se guardan como archivos en disco.
  // Sin servidor (GitHub Pages, doble-clic): se usa el navegador (localStorage).
  var serverMode = false;
  function hasServer() { return serverMode; }
  function detectServer() {
    if (location.protocol === "file:") return Promise.resolve(false); // nunca hay servidor
    return fetch("/api/ping", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (j) { return !!(j && j.server === "catalog"); })
      .catch(function () { return false; });
  }

  function loadState() {
    // Con servidor: el catálogo vive en disco (catalog.json).
    if (hasServer()) {
      return fetch("/api/catalog", { cache: "no-store" })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (j && !j.empty && j.categories) return normalize(j);
          return normalize(deepClone(window.CATALOG_SEED)); // primera vez
        })
        .catch(function () { return normalize(deepClone(window.CATALOG_SEED)); });
    }
    // Sin servidor (GitHub Pages / file://): usa localStorage, salvo que el
    // catálogo publicado (seed.js) tenga una versión más nueva, en cuyo caso se
    // adopta el nuevo (así las actualizaciones publicadas se ven sin borrar caché).
    var seed = window.CATALOG_SEED;
    var raw = null;
    try { raw = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    if (raw) {
      try {
        var saved = JSON.parse(raw);
        var sameVersion = !seed.version || (saved && saved.version === seed.version);
        if (sameVersion) return Promise.resolve(normalize(saved));
      } catch (e) {}
    }
    // primera visita o versión publicada nueva: cargar el seed y guardarlo
    var fresh = normalize(deepClone(seed));
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh)); } catch (e) {}
    return Promise.resolve(fresh);
  }

  function save() {
    // Copia de respaldo siempre en el navegador (con servidor, las imágenes son
    // rutas, así que el JSON es pequeño y no llena el almacenamiento).
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
    if (hasServer()) saveToDiskSoon();
  }

  var diskTimer = null;
  var scrapingActive = false; // pausa el guardado a disco mientras se descargan imágenes
  function saveToDiskSoon() { clearTimeout(diskTimer); diskTimer = setTimeout(saveToDisk, 500); }
  function saveToDisk() {
    if (scrapingActive) return; // no sobrescribir el catálogo mientras el servidor lo actualiza
    fetch("/api/catalog", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state)
    }).then(function (r) { return r.json(); })
      .then(function (j) { if (j && j.error) flash("No se pudo guardar en disco: " + j.error, true); })
      .catch(function () { flash("No se pudo guardar en disco (¿el servidor sigue encendido?).", true); });
  }

  var saveTimer = null;
  function saveSoon() { clearTimeout(saveTimer); saveTimer = setTimeout(save, 350); }

  /* ---------------- formato de precio ---------------- */
  function formatPrice(price) {
    var s = (price == null ? "" : String(price)).trim();
    if (!s) return { text: "", consult: false };
    if (/^\d+(\.\d+)?$/.test(s)) {
      return { text: state.settings.currency + Number(s).toFixed(2), consult: false };
    }
    return { text: s, consult: true }; // texto libre, p.ej. "Consultar precio"
  }

  /* ============================================================
     PREVISUALIZACIÓN (hojas tamaño carta)
     ============================================================ */
  function paginate(products) {
    var pages = [];
    var arr = products.slice();
    if (arr.length === 0) return [[]]; // al menos la hoja con el banner
    pages.push(arr.splice(0, FIRST_PAGE));
    while (arr.length) pages.push(arr.splice(0, CONT_PAGE));
    return pages;
  }

  function footEl() {
    var b = state.brand;
    var f = el("div", "foot");
    f.appendChild(el("div", "l", b.companyName + " — " + b.address));
    f.appendChild(el("div", "r", "Tel: " + b.phone + " · " + b.email));
    return f;
  }

  function renderCover() {
    var b = state.brand;
    var page = el("div", "page cover");
    var inner = el("div", "page-inner");
    var card = el("div", "cover-card");

    var top = el("div", "cover-bar top");
    var bot = el("div", "cover-bar bottom");
    for (var i = 0; i < 5; i++) { top.appendChild(el("span")); bot.appendChild(el("span")); }
    card.appendChild(top); card.appendChild(bot);

    if (b.logo) {
      var lg = el("div", "cover-logo");
      var img = new Image(); img.src = b.logo; img.alt = b.companyName;
      lg.appendChild(img); card.appendChild(lg);
    }
    var dots = el("div", "cover-dots");
    for (var d = 0; d < 4; d++) dots.appendChild(el("i"));
    card.appendChild(dots);

    card.appendChild(el("div", "cover-title", b.catalogTitle));
    if (b.subtitle) card.appendChild(el("div", "cover-sub", b.subtitle));

    var contact = el("div", "cover-contact");
    contact.appendChild(el("div", "co", b.companyName));
    contact.appendChild(el("div", "ln", b.address));
    contact.appendChild(el("div", "ln", "Tel: " + b.phone));
    contact.appendChild(el("div", "ln", b.email));
    card.appendChild(contact);

    inner.appendChild(card);
    page.appendChild(inner);
    page.appendChild(footEl());
    return page;
  }

  function renderCard(p) {
    var card = el("div", "card");
    var box = el("div", "imgbox");
    if (p.image) {
      var img = new Image(); img.src = p.image; img.alt = p.name || "";
      box.appendChild(img);
    } else {
      box.className = "imgbox empty";
      box.appendChild(el("div", "ic", "🖼")); // 🖼
      box.appendChild(el("div", null, "Foto"));
    }
    card.appendChild(box);
    card.appendChild(el("div", "pn", p.name || ""));
    var pr = formatPrice(p.price);
    var pp = el("div", "pp" + (pr.consult ? " consult" : ""), pr.text);
    card.appendChild(pp);
    return card;
  }

  function renderCategoryPage(cat, products, isFirst, total) {
    var page = el("div", "page category acc-" + cat.accent);
    var inner = el("div", "page-inner");

    if (isFirst) {
      var banner = el("div", "cat-banner");
      banner.appendChild(el("div", "t", cat.name));
      banner.appendChild(el("div", "n", total + (total === 1 ? " producto" : " productos")));
      inner.appendChild(banner);
      // La nota se muestra siempre (con o sin precios).
      if (state.brand.illustrativeNote) {
        inner.appendChild(el("div", "illus-note", state.brand.illustrativeNote));
      }
    }

    var grid = el("div", "grid");
    products.forEach(function (p) { grid.appendChild(renderCard(p)); });
    inner.appendChild(grid);

    page.appendChild(inner);
    page.appendChild(footEl());
    return page;
  }

  function renderPreview() {
    var wrap = document.getElementById("preview");
    wrap.innerHTML = "";
    wrap.className = "preview-scale" + (state.settings.showPrices ? "" : " no-prices");
    wrap.appendChild(renderCover());
    state.categories.forEach(function (cat) {
      var pages = paginate(cat.products);
      pages.forEach(function (prods, idx) {
        wrap.appendChild(renderCategoryPage(cat, prods, idx === 0, cat.products.length));
      });
    });
    applyZoom();
  }

  /* ============================================================
     EDITOR (panel lateral)
     ============================================================ */
  function bindField(input, obj, key, after) {
    input.value = obj[key] || "";
    input.addEventListener("input", function () {
      obj[key] = input.value;
      saveSoon();
      if (after) after();
    });
  }

  function renderBrandEditor() {
    var host = document.getElementById("brandEditor");
    host.innerHTML = "";
    var b = state.brand;
    var fields = [
      ["companyName", "Nombre de la empresa"],
      ["catalogTitle", "Título del catálogo"],
      ["subtitle", "Subtítulo (pastilla)"],
      ["address", "Dirección"],
      ["phone", "Teléfono"],
      ["email", "Correo"],
      ["illustrativeNote", "Nota bajo el banner"]
    ];
    fields.forEach(function (f) {
      var wrap = el("div", "field");
      wrap.appendChild(el("label", null, f[1]));
      var inp = el("input");
      bindField(inp, b, f[0], renderPreview);
      wrap.appendChild(inp);
      host.appendChild(wrap);
    });

    // Logo
    var lf = el("div", "field");
    lf.appendChild(el("label", null, "Logo"));
    var logoRow = el("div", "prod-row");
    var thumb = el("div", "thumb");
    if (b.logo) { var im = new Image(); im.src = b.logo; thumb.appendChild(im); } else thumb.textContent = "+";
    thumb.title = "Cambiar logo";
    thumb.addEventListener("click", function () {
      acquireImage("logo", b.logo, function (src) { b.logo = src; save(); renderBrandEditor(); renderPreview(); });
    });
    logoRow.appendChild(thumb);
    var hint = el("div", "pname"); hint.appendChild(el("span", null, "Clic para cambiar el logo"));
    logoRow.appendChild(hint);
    lf.appendChild(logoRow);
    host.appendChild(lf);
  }

  function renderCatEditor() {
    var host = document.getElementById("catEditor");
    host.innerHTML = "";
    state.categories.forEach(function (cat, ci) {
      var block = el("div", "cat-block" + (openCats[cat.id] ? " open" : ""));

      var head = el("div", "cat-head");
      var dot = el("span", "dot"); dot.style.background = accentColor(cat.accent);
      head.appendChild(dot);
      head.appendChild(el("span", "cat-name", cat.name));
      head.appendChild(el("span", "count", cat.products.length + " prod."));
      head.appendChild(el("span", "chev", "›"));
      head.addEventListener("click", function () {
        openCats[cat.id] = !openCats[cat.id];
        block.classList.toggle("open");
      });
      block.appendChild(head);

      var body = el("div", "cat-body");

      // nombre + acento + eliminar categoría
      var nameField = el("div", "field");
      nameField.appendChild(el("label", null, "Nombre de la categoría"));
      var nameInp = el("input"); nameInp.value = cat.name;
      nameInp.addEventListener("input", function () {
        cat.name = nameInp.value;
        head.querySelector(".cat-name").textContent = nameInp.value;
        saveSoon(); renderPreview();
      });
      nameField.appendChild(nameInp);
      body.appendChild(nameField);

      var accField = el("div", "field");
      accField.appendChild(el("label", null, "Color de acento"));
      var sel = el("select");
      sel.style.cssText = "width:100%;padding:7px 9px;border:1px solid #d3d7db;border-radius:7px;font-size:13px;";
      ACCENTS.forEach(function (a) {
        var o = el("option", null, ACCENT_LABEL[a]); o.value = a;
        if (a === cat.accent) o.selected = true; sel.appendChild(o);
      });
      sel.addEventListener("change", function () {
        cat.accent = sel.value; dot.style.background = accentColor(cat.accent);
        saveSoon(); renderPreview();
      });
      accField.appendChild(sel);
      body.appendChild(accField);

      // productos
      cat.products.forEach(function (p, pi) {
        body.appendChild(renderProductRow(cat, p, pi));
      });

      // acciones
      var actions = el("div", "cat-actions");
      var addBtn = el("button", "btn small", "+ Producto");
      addBtn.addEventListener("click", function () {
        cat.products.push({ id: uid("p"), name: "NUEVO PRODUCTO", price: "" });
        save(); renderCatEditor(); renderPreview();
      });
      var delBtn = el("button", "btn small ghost", "Eliminar categoría");
      delBtn.style.color = "#d0512d";
      delBtn.addEventListener("click", function () {
        if (confirm("¿Eliminar la categoría \"" + cat.name + "\" y todos sus productos?")) {
          state.categories.splice(ci, 1); save(); renderCatEditor(); renderPreview();
        }
      });
      actions.appendChild(addBtn);
      var up = el("button", "btn small", "↑");
      up.title = "Subir categoría";
      up.addEventListener("click", function () {
        if (ci > 0) { var t = state.categories.splice(ci, 1)[0]; state.categories.splice(ci - 1, 0, t); save(); renderCatEditor(); renderPreview(); }
      });
      var down = el("button", "btn small", "↓");
      down.title = "Bajar categoría";
      down.addEventListener("click", function () {
        if (ci < state.categories.length - 1) { var t = state.categories.splice(ci, 1)[0]; state.categories.splice(ci + 1, 0, t); save(); renderCatEditor(); renderPreview(); }
      });
      actions.appendChild(up); actions.appendChild(down);
      actions.appendChild(delBtn);
      body.appendChild(actions);

      block.appendChild(body);
      host.appendChild(block);
    });
  }

  function renderProductRow(cat, p, pi) {
    var row = el("div", "prod-row");
    var thumb = el("div", "thumb");
    if (p.image) { var im = new Image(); im.src = p.image; thumb.appendChild(im); }
    else thumb.textContent = "📷"; // 📷
    thumb.title = "Clic: subir/cambiar imagen";
    thumb.addEventListener("click", function () {
      acquireImage(p.name, p.image, function (src) { p.image = src; save(); renderCatEditor(); renderPreview(); });
    });
    // quitar imagen (clic derecho)
    thumb.addEventListener("contextmenu", function (ev) {
      ev.preventDefault();
      if (p.image && confirm("¿Quitar la imagen de este producto?")) {
        delete p.image; save(); renderCatEditor(); renderPreview();
      }
    });
    row.appendChild(thumb);

    var nameWrap = el("div", "pname");
    var nameInp = el("input"); nameInp.value = p.name || "";
    nameInp.addEventListener("input", function () { p.name = nameInp.value; saveSoon(); renderPreview(); });
    nameWrap.appendChild(nameInp);
    row.appendChild(nameWrap);

    var priceWrap = el("div", "pprice");
    var priceInp = el("input"); priceInp.value = p.price || ""; priceInp.placeholder = "precio";
    priceInp.addEventListener("input", function () { p.price = priceInp.value; saveSoon(); renderPreview(); });
    priceWrap.appendChild(priceInp);
    row.appendChild(priceWrap);

    // mover a otra categoría
    var moveSel = el("select", "movesel");
    moveSel.title = "Mover a otra categoría";
    var ph = el("option", null, "⇄"); ph.value = ""; ph.selected = true; moveSel.appendChild(ph);
    state.categories.forEach(function (tc) {
      if (tc.id === cat.id) return;
      var o = el("option", null, tc.name); o.value = tc.id; moveSel.appendChild(o);
    });
    moveSel.addEventListener("change", function () {
      var target = state.categories.filter(function (c) { return c.id === moveSel.value; })[0];
      if (!target) return;
      cat.products.splice(pi, 1);
      target.products.push(p);
      save(); renderCatEditor(); renderPreview();
    });
    row.appendChild(moveSel);

    var del = el("button", "del", "✕");
    del.title = "Eliminar producto";
    del.addEventListener("click", function () {
      cat.products.splice(pi, 1); save(); renderCatEditor(); renderPreview();
    });
    row.appendChild(del);
    return row;
  }

  function accentColor(a) {
    var map = { orange: "#E4572E", coral: "#E1502B", gold: "#E3A81C", green: "#5BA632", teal: "#2FA9B6", cyan: "#3FB0C9" };
    return map[a] || "#888";
  }

  /* ---------------- imágenes ---------------- */
  var imgInput;
  function pickFile(cb) {
    if (!imgInput) {
      imgInput = el("input"); imgInput.type = "file"; imgInput.accept = "image/*";
      imgInput.style.display = "none"; document.body.appendChild(imgInput);
    }
    imgInput.value = "";
    imgInput.onchange = function () { cb(imgInput.files[0]); };
    imgInput.click();
  }

  function toDataURL(file, cb) {
    var r = new FileReader();
    r.onload = function () { cb(r.result); };
    r.readAsDataURL(file);
  }

  function uploadImage(file, nameHint, oldPath) {
    var qs = "?name=" + encodeURIComponent(nameHint || "img");
    if (oldPath && oldPath.indexOf("assets/img/products/") === 0) {
      qs += "&old=" + encodeURIComponent(oldPath);
    }
    return fetch("/api/upload" + qs, {
      method: "POST",
      headers: { "Content-Type": file.type || "image/png" },
      body: file
    }).then(function (r) { return r.json(); })
      .then(function (j) { if (j && j.path) return j.path; throw new Error("upload"); });
  }

  // Obtiene una imagen: la guarda como archivo (con servidor) o como data URL
  // (sin servidor), y devuelve la ruta/URL para usar en el producto.
  function acquireImage(nameHint, oldPath, cb) {
    pickFile(function (file) {
      if (!file) return;
      if (hasServer()) {
        uploadImage(file, nameHint, oldPath)
          .then(cb)
          .catch(function () { toDataURL(file, cb); }); // respaldo si falla la subida
      } else {
        toDataURL(file, cb);
      }
    });
  }

  /* ---------------- importar / exportar ---------------- */
  function exportJSON() {
    var blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
    var a = el("a"); a.href = URL.createObjectURL(blob);
    a.download = "catalogo-hispanic-foods.json"; a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  }
  var jsonInput;
  function importJSON() {
    if (!jsonInput) {
      jsonInput = el("input"); jsonInput.type = "file"; jsonInput.accept = "application/json,.json";
      jsonInput.style.display = "none"; document.body.appendChild(jsonInput);
    }
    jsonInput.value = "";
    jsonInput.onchange = function () {
      var f = jsonInput.files[0]; if (!f) return;
      var r = new FileReader();
      r.onload = function () {
        try {
          state = normalize(JSON.parse(r.result));
          save(); renderAll(); flash("Catálogo importado.");
        } catch (e) { flash("El archivo no es un catálogo válido.", true); }
      };
      r.readAsText(f);
    };
    jsonInput.click();
  }

  function resetSeed() {
    if (confirm("Restablecer el catálogo a los datos originales. Se perderán tus cambios. ¿Continuar?")) {
      state = normalize(deepClone(window.CATALOG_SEED));
      save(); renderAll(); flash("Catálogo restablecido.");
    }
  }

  function addCategory() {
    state.categories.push({ id: uid("cat"), name: "NUEVA CATEGORÍA", accent: ACCENTS[state.categories.length % ACCENTS.length], products: [] });
    openCats[state.categories[state.categories.length - 1].id] = true;
    save(); renderCatEditor(); renderPreview();
  }

  /* ---------------- zoom ---------------- */
  var zoom = 0.85;
  function applyZoom() {
    var wrap = document.getElementById("preview");
    wrap.style.transform = "scale(" + zoom + ")";
    wrap.style.transformOrigin = "top center";
  }
  function setZoom(z) { zoom = Math.max(0.4, Math.min(1.5, z)); document.getElementById("zoomLbl").textContent = Math.round(zoom * 100) + "%"; applyZoom(); }

  /* ---------------- avisos ---------------- */
  var flashTimer;
  function flash(msg, isErr) {
    var box = document.getElementById("flash");
    box.textContent = msg;
    box.style.background = isErr ? "#e05252" : "#2c9aa6";
    box.classList.add("show");
    clearTimeout(flashTimer);
    flashTimer = setTimeout(function () { box.classList.remove("show"); }, 2600);
  }

  /* ============================================================
     DESCARGA DE IMÁGENES (scraping vía servidor)
     ============================================================ */
  var scrapeModal, scrapePoll;

  function buildScrapeModal() {
    if (scrapeModal) return scrapeModal;
    var overlay = el("div", "modal-overlay");
    var panel = el("div", "modal");
    overlay.appendChild(panel);

    // --- vista de opciones ---
    var opts = el("div", "modal-opts");
    opts.appendChild(el("h3", null, "Descargar imágenes"));
    opts.appendChild(el("p", "modal-desc",
      "Busca en internet la imagen de cada producto por su nombre y la guarda en assets/img/products/. Las imágenes son orientativas: revísalas después."));

    var g1 = el("div", "field");
    g1.appendChild(el("label", null, "¿Qué productos?"));
    var scope = el("select");
    [["missing", "Solo los que no tienen imagen"], ["all", "Todos (reemplaza las actuales)"]]
      .forEach(function (o) { var op = el("option", null, o[1]); op.value = o[0]; scope.appendChild(op); });
    g1.appendChild(scope); opts.appendChild(g1);

    var g2 = el("div", "field");
    g2.appendChild(el("label", null, "Categoría (opcional, vacío = todas)"));
    var only = el("select");
    var anyOpt = el("option", null, "Todas las categorías"); anyOpt.value = ""; only.appendChild(anyOpt);
    g2.appendChild(only); opts.appendChild(g2);

    var g3 = el("div", "field");
    g3.appendChild(el("label", null, "Texto extra de búsqueda"));
    var suffix = el("input"); suffix.value = "medicamento"; g3.appendChild(suffix);
    opts.appendChild(g3);

    var g4 = el("div", "field");
    g4.appendChild(el("label", null, "Fuente"));
    var source = el("select");
    [["bing", "Bing Imágenes"], ["google", "Google Imágenes"], ["ddg", "DuckDuckGo"]].forEach(function (o) {
      var op = el("option", null, o[1]); op.value = o[0]; source.appendChild(op);
    });
    g4.appendChild(source); opts.appendChild(g4);

    var actions = el("div", "modal-actions");
    var cancel = el("button", "btn", "Cancelar");
    var start = el("button", "btn primary", "Iniciar descarga");
    actions.appendChild(cancel); actions.appendChild(start);
    opts.appendChild(actions);
    panel.appendChild(opts);

    // --- vista de progreso ---
    var prog = el("div", "modal-prog"); prog.style.display = "none";
    prog.appendChild(el("h3", null, "Descargando imágenes…"));
    var barWrap = el("div", "bar-wrap"); var bar = el("div", "bar"); barWrap.appendChild(bar);
    prog.appendChild(barWrap);
    var pcount = el("div", "prog-count", ""); prog.appendChild(pcount);
    var pcur = el("div", "prog-cur", ""); prog.appendChild(pcur);
    var logBox = el("div", "prog-log"); prog.appendChild(logBox);
    var pactions = el("div", "modal-actions");
    var stop = el("button", "btn", "Detener");
    var close = el("button", "btn primary", "Cerrar"); close.disabled = true;
    pactions.appendChild(stop); pactions.appendChild(close);
    prog.appendChild(pactions);
    panel.appendChild(prog);

    document.body.appendChild(overlay);

    scrapeModal = {
      overlay: overlay, opts: opts, prog: prog,
      scope: scope, only: only, suffix: suffix, source: source,
      bar: bar, pcount: pcount, pcur: pcur, logBox: logBox,
      start: start, cancel: cancel, stop: stop, close: close
    };

    cancel.addEventListener("click", closeScrape);
    close.addEventListener("click", closeScrape);
    start.addEventListener("click", startScrape);
    stop.addEventListener("click", function () {
      stop.disabled = true; stop.textContent = "Deteniendo…";
      fetch("/api/scrape/stop", { method: "POST" }).catch(function () {});
    });
    return scrapeModal;
  }

  function openScrapeModal() {
    if (!hasServer()) {
      flash("Para descargar imágenes abre la app con «python3 server.py».", true);
      return;
    }
    var m = buildScrapeModal();
    // llena categorías
    m.only.innerHTML = "";
    var any = el("option", null, "Todas las categorías"); any.value = ""; m.only.appendChild(any);
    state.categories.forEach(function (c) {
      var op = el("option", null, c.name + " (" + c.products.length + ")"); op.value = c.name; m.only.appendChild(op);
    });
    // llena fuentes: farmacias configuradas (recomendadas) + buscadores
    fetch("/api/pharmacies").then(function (r) { return r.json(); }).then(function (phs) {
      m.source.innerHTML = "";
      (phs || []).forEach(function (p) {
        var op = el("option", null, "🏥 " + p.label + "  (recomendado)"); op.value = "pharmacy:" + p.key; m.source.appendChild(op);
      });
      [["bing", "Bing Imágenes"], ["google", "Google Imágenes"], ["ddg", "DuckDuckGo"]].forEach(function (o) {
        var op = el("option", null, o[1]); op.value = o[0]; m.source.appendChild(op);
      });
      if (m.source.options.length) m.source.selectedIndex = 0; // farmacia por defecto si hay
    }).catch(function () {});
    m.opts.style.display = ""; m.prog.style.display = "none";
    m.start.disabled = false; m.close.disabled = true;
    m.stop.disabled = false; m.stop.textContent = "Detener";
    m.overlay.classList.add("show");
  }

  function closeScrape() {
    if (!scrapeModal) return;
    clearInterval(scrapePoll);
    scrapeModal.overlay.classList.remove("show");
    if (scrapingActive) {
      // terminó o se cerró: recargar el catálogo desde disco (ya con imágenes)
      scrapingActive = false;
      loadState().then(function (s) { state = s; renderAll(); });
    }
  }

  function startScrape() {
    var m = scrapeModal;
    var opts = {
      all: m.scope.value === "all",
      only: m.only.value,
      suffix: m.suffix.value.trim(),
      source: m.source.value
    };
    m.opts.style.display = "none"; m.prog.style.display = "";
    m.bar.style.width = "0%"; m.pcount.textContent = "Preparando…";
    m.pcur.textContent = ""; m.logBox.textContent = "";
    scrapingActive = true; // pausa el auto-guardado a disco

    // primero asegurar que el catálogo en disco esté al día, luego iniciar
    fetch("/api/catalog", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(state) })
      .then(function () {
        return fetch("/api/scrape", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(opts) });
      })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j && j.error) { flash(j.error, true); scrapingActive = false; m.opts.style.display = ""; m.prog.style.display = "none"; return; }
        scrapePoll = setInterval(pollScrape, 1000);
      })
      .catch(function () { flash("No se pudo iniciar la descarga.", true); scrapingActive = false; });
  }

  function pollScrape() {
    var m = scrapeModal;
    fetch("/api/scrape/status", { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (s) {
      var st = s.state || {};
      var total = st.total || 0, i = st.i || 0;
      var pct = total ? Math.round((i / total) * 100) : 0;
      m.bar.style.width = pct + "%";
      m.pcount.textContent = i + " / " + total + "  ·  ✓ " + (st.ok || 0) + "   ✗ " + (st.fail || 0);
      m.pcur.textContent = st.name ? ("Buscando: " + st.name) : "";
      if (s.log && s.log.length) m.logBox.textContent = s.log.join("\n");
      m.logBox.scrollTop = m.logBox.scrollHeight;
      if (!s.running) {
        clearInterval(scrapePoll);
        var sum = s.summary || {};
        m.pcur.textContent = "Listo. Descargadas: " + (sum.ok || 0) + "  ·  Sin imagen: " + (sum.fail || 0);
        m.stop.disabled = true; m.close.disabled = false;
        // recargar catálogo desde disco para mostrar las imágenes en la vista
        loadState().then(function (data) { state = data; renderAll(); });
      }
    }).catch(function () { /* seguirá intentando en el próximo tick */ });
  }

  /* ---------------- render global + eventos ---------------- */
  function renderAll() { renderBrandEditor(); renderCatEditor(); renderPreview(); syncPriceSwitch(); }

  function syncPriceSwitch() { document.getElementById("priceToggle").checked = state.settings.showPrices; }

  function wireTopbar() {
    document.getElementById("priceToggle").addEventListener("change", function (e) {
      state.settings.showPrices = e.target.checked; save(); renderPreview();
    });
    document.getElementById("btnPrint").addEventListener("click", function () { window.print(); });
    document.getElementById("btnScrape").addEventListener("click", openScrapeModal);
    document.getElementById("btnExport").addEventListener("click", exportJSON);
    document.getElementById("btnImport").addEventListener("click", importJSON);
    document.getElementById("btnReset").addEventListener("click", resetSeed);
    document.getElementById("btnAddCat").addEventListener("click", addCategory);
    document.getElementById("zoomIn").addEventListener("click", function () { setZoom(zoom + 0.1); });
    document.getElementById("zoomOut").addEventListener("click", function () { setZoom(zoom - 0.1); });
  }

  function init() {
    wireTopbar();
    detectServer().then(function (isSrv) {
      serverMode = isSrv;
      if (!serverMode) {
        // Modo estático (GitHub Pages / doble-clic): sin scraping ni disco.
        var b = document.getElementById("btnScrape");
        if (b) b.style.display = "none";
      }
      return loadState();
    }).then(function (s) {
      state = s;
      renderAll();
      setZoom(zoom);
    });
  }

  document.addEventListener("DOMContentLoaded", init);
})();
