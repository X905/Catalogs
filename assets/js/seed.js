/*
 * Datos semilla del catálogo (Hispanic Foods Corp — Medicina).
 * Se cargan la primera vez que abres la app. Después puedes editar todo desde
 * la interfaz; los cambios se guardan en el navegador (localStorage) y puedes
 * exportar/importar el catálogo completo como JSON.
 *
 * Modelo de datos:
 *   brand:      información de portada y pie de página
 *   settings:   { showPrices, currency }
 *   categories: [ { id, name, accent, products: [ { id, name, price, image } ] } ]
 *
 * price: puede ser un número ("25", "12.50"), texto libre ("Consultar precio")
 *        o vacío. accent: uno de los colores definidos en catalog.css
 *        (orange, coral, gold, green, teal, cyan).
 */
window.CATALOG_SEED = {
  brand: {
    companyName: "Hispanic Foods Corp",
    catalogTitle: "CATÁLOGO DE PRODUCTOS",
    subtitle: "MEDICINA",
    address: "194 E Jefferson Blvd, Los Angeles, CA 90011",
    phone: "(213) 389-7506",
    email: "chapinfoods@gmail.com",
    logo: "assets/img/logo.png",
    illustrativeNote: "Imágenes con fines ilustrativos"
  },
  settings: {
    showPrices: true,
    currency: "$"
  },
  categories: [
    {
      id: "cat-analgesicos",
      name: "ANALGÉSICOS Y DOLOR",
      accent: "orange",
      products: [
        { name: "ACCIÓN PLUS", price: "25.00" },
        { name: "ACETAMINOFÉN BAYER", price: "30.00" },
        { name: "ACETAMINOFÉN GOTERO", price: "12.00" },
        { name: "ACETAMINOFÉN JARABE MK", price: "12.00" },
        { name: "ASPIRINA ADULTO", price: "28.00" },
        { name: "ASPIRINA FORTE", price: "32.00" },
        { name: "ASPIRINA NIÑO", price: "25.00" },
        { name: "BARALGINA", price: "16.00" },
        { name: "CALMANTE CALMADOL PAQUETES", price: "40.00" },
        { name: "CALMANTE SANTÉ PAQUETES", price: "40.00" },
        { name: "CARDIO ASPIRINA", price: "22.00" },
        { name: "CEREBREX", price: "18.00" },
        { name: "CEREBREX MICRO BOTELLA", price: "17.00" },
        { name: "DICLOFENACO + NEUROTROPAS", price: "50.00" },
        { name: "DICLOFENACO POTÁSICO", price: "18.00" },
        { name: "DICLOFENACO POTÁSICO GOTERO", price: "12.50" },
        { name: "DICLO ROJO", price: "20.00" },
        { name: "DICLOFENACO SÓDICO", price: "47.00" },
        { name: "DKC ADULTO AMPOLLA", price: "15.00" },
        { name: "DKC NIÑO AMPOLLA", price: "15.00" },
        { name: "DOLO ULTRA ESTRÉS", price: "18.00" },
        { name: "DOLO ULTRA ESTRÉS PASTILLA", price: "32.00" },
        { name: "DOLOFIN", price: "45.00" },
        { name: "DOLONEUROBIÓN INYECCIÓN", price: "25.00" },
        { name: "DOLONEUROBIÓN N", price: "25.00" },
        { name: "DOLONEUROBIÓN PASTILLAS", price: "55.00" },
        { name: "DOLONEUROTROPAS", price: "45.00" },
        { name: "DORIVAL GEL", price: "23.00" },
        { name: "IBUPROFÉN GOTERO", price: "12.00" },
        { name: "IBUPROFENO JARABE", price: "12.00" },
        { name: "IBUPROFÉN 600", price: "28.00" },
        { name: "IBUPROFÉN 800", price: "35.00" },
        { name: "IBUWIN 600", price: "35.00" },
        { name: "IBUWIN 800", price: "35.00" },
        { name: "KETEROLACO", price: "12.00" },
        { name: "NEOMELUBRINA JARABE", price: "Consultar precio" },
        { name: "NEOMELUBRINA PASTILLA", price: "40.00" },
        { name: "SEDALGINA", price: "9.00" },
        { name: "TRAMADOL", price: "Consultar precio" },
        { name: "VITAFLENACO", price: "14.00" },
        { name: "VITAFLENACO EN GEL", price: "10.00" }
      ]
    },
    { id: "cat-panadol",       name: "PANADOL",                        accent: "teal",   products: [] },
    { id: "cat-tabcin",        name: "TABCIN",                         accent: "green",  products: [] },
    { id: "cat-vick",          name: "VICK",                           accent: "gold",   products: [] },
    { id: "cat-virogrip",      name: "VIROGRIP",                       accent: "coral",  products: [] },
    { id: "cat-sudagrip",      name: "SUDAGRIP",                       accent: "cyan",   products: [] },
    { id: "cat-gripe",         name: "GRIPE, TOS Y RESFRIADO",         accent: "green",  products: [] },
    { id: "cat-estomago",      name: "ESTÓMAGO Y DIGESTIÓN",           accent: "gold",   products: [] },
    { id: "cat-vitaminas",     name: "VITAMINAS Y SUPLEMENTOS",        accent: "coral",  products: [] },
    { id: "cat-antibioticos",  name: "ANTIBIÓTICOS Y ANTIPARASITARIOS", accent: "teal",  products: [] },
    { id: "cat-cremas",        name: "CREMAS, POMADAS Y UNGÜENTOS",    accent: "green",  products: [] },
    { id: "cat-bebes",         name: "BEBÉS Y NIÑOS",                  accent: "gold",   products: [] },
    { id: "cat-naturales",     name: "NATURALES Y TRADICIONALES",      accent: "coral",  products: [] },
    { id: "cat-otros",         name: "OTROS",                          accent: "teal",   products: [] }
  ]
};
