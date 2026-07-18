/*
 * Datos semilla del catálogo (Hispanic Foods Corp — Medicina).
 * Transcrito de las notas de inventario (5 páginas).
 *
 * Modelo de datos:
 *   brand:      información de portada y pie de página
 *   settings:   { showPrices, currency }
 *   categories: [ { id, name, accent, products: [ { id, name, price, image } ] } ]
 *
 * price: número ("25", "12.50"), texto libre ("Consultar precio") o vacío.
 * accent: orange, coral, gold, green, teal, cyan.
 *
 * Nota: la categoría de cada producto es una clasificación inicial; puedes
 * mover cualquier producto a otra categoría desde el editor.
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
    {
      id: "cat-panadol",
      name: "PANADOL",
      accent: "teal",
      products: [
        { name: "PANADOL AZUL", price: "35.00" },
        { name: "PANADOL DÍA", price: "23.00" },
        { name: "PANADOL MUJER", price: "23.00" },
        { name: "PANADOL MULTISÍNTOMAS", price: "23.00" },
        { name: "PANADOL NIÑO PASTILLA", price: "37.00" },
        { name: "PANADOL NIÑO JARABE", price: "12.00" },
        { name: "PANADOL NOCHE", price: "23.00" },
        { name: "PANADOL ROJO", price: "35.00" },
        { name: "PANADOL SINUS", price: "23.00" }
      ]
    },
    {
      id: "cat-tabcin",
      name: "TABCIN",
      accent: "green",
      products: [
        { name: "TABCIN AZUL EN GEL", price: "25.00" },
        { name: "TABCIN CELESTE", price: "25.00" },
        { name: "TABCIN FLEMA Y CONGESTIÓN", price: "25.00" },
        { name: "TABCIN MORADO EFERVESCENTE", price: "25.00" },
        { name: "TABCIN MORADO GEL", price: "25.00" },
        { name: "TABCIN NIÑO", price: "25.00" },
        { name: "TABCIN ROJO", price: "25.00" },
        { name: "TABCIN VERDE GEL", price: "25.00" }
      ]
    },
    {
      id: "cat-vick",
      name: "VICK",
      accent: "gold",
      products: [
        { name: "VICK 44 ADULTO FRASCO", price: "10.75" },
        { name: "VICK 44 NIÑO FRASCO", price: "10.75" },
        { name: "VICK DROPS PASTILLAS", price: "3.75" },
        { name: "VICK VAPORUB 50 GRS UNIDADES", price: "5.00" },
        { name: "VICK VAPORUB LATA", price: "4.05" }
      ]
    },
    {
      id: "cat-virogrip",
      name: "VIROGRIP",
      accent: "coral",
      products: [
        { name: "VIROGRIP DÍA GEL", price: "25.00" },
        { name: "VIROGRIP DÍA POLVO", price: "25.00" },
        { name: "VIROGRIP JARABE UNIDADES", price: "12.00" },
        { name: "VIROGRIP NOCHE GEL", price: "25.00" },
        { name: "VIROGRIP NOCHE POLVO", price: "25.00" }
      ]
    },
    {
      id: "cat-sudagrip",
      name: "SUDAGRIP",
      accent: "cyan",
      products: [
        { name: "SUDAGRIP PASTILLA", price: "25.00" },
        { name: "SUDAGRIP POLVO", price: "25.00" },
        { name: "SUDAGRIP JARABE NIÑO", price: "12.00" },
        { name: "SUDAGRIP JARABE ADULTO", price: "12.00" }
      ]
    },
    {
      id: "cat-gripe",
      name: "GRIPE, TOS Y RESFRIADO",
      accent: "green",
      products: [
        { name: "ANTIGRIP", price: "32.00" },
        { name: "ANTIGRIPITO PASTILLA", price: "30.00" },
        { name: "ANTIGRIPITO JARABE", price: "12.00" },
        { name: "CLOROMILAN", price: "60.00" },
        { name: "DESENFRIOL ADULTO", price: "15.00" },
        { name: "DESENFRIOLITO NIÑO", price: "15.00" },
        { name: "FÓRMULA 44 ADULTOS", price: "8.75" },
        { name: "FÓRMULA 44 NIÑOS", price: "8.75" },
        { name: "GRIPON C", price: "35.00" },
        { name: "GRIPONCITO", price: "35.00" },
        { name: "KOLD GRIP GOTERO", price: "12.00" },
        { name: "LORATADINA JARABE", price: "12.00" },
        { name: "NEUMONIL FORTE", price: "45.00" },
        { name: "NEUMONIL VERDE", price: "24.50" },
        { name: "PULMO FEROL", price: "Consultar precio" },
        { name: "VITAPIRENA", price: "40.00" }
      ]
    },
    {
      id: "cat-estomago",
      name: "ESTÓMAGO Y DIGESTIÓN",
      accent: "gold",
      products: [
        { name: "ALKA AD", price: "26.00" },
        { name: "ALKA SELTZER", price: "25.00" },
        { name: "ALKA SELTZER NEGRA", price: "25.00" },
        { name: "BICARBONATO PAQUETES", price: "32.00" },
        { name: "BISMUTO COMPUESTO PAQUETES", price: "30.00" },
        { name: "CITRATO DE MAGNESIA PAQUETES", price: "33.00" },
        { name: "CUAJO MARSHALL", price: "Consultar precio" },
        { name: "DONOFLAT PLUS BLISTER", price: "60.00" },
        { name: "ENTEROGUANIL ADULTO", price: "30.00" },
        { name: "ENTEROGUANIL NIÑO", price: "30.00" },
        { name: "ESTOMICINA EN SOBRE x50", price: "22.00" },
        { name: "ESTOMICINA PASTILLA", price: "22.00" },
        { name: "LANSOPRAZOL", price: "10.00" },
        { name: "MAGNESIA THERFAM", price: "26.00" },
        { name: "MAX FRESH PAQUETES", price: "26.00" },
        { name: "NAUSEOL", price: "0.50" },
        { name: "OMEPRAZOL PASTILLA", price: "45.00" },
        { name: "PEPTO BISMOL UNIDADES", price: "Consultar precio" },
        { name: "SAL ANDREWS", price: "25.00" },
        { name: "SAL DE UVAS PICOT", price: "20.00" },
        { name: "SAL INGLESA PAQUETES", price: "22.00" },
        { name: "SERTAL COMPUESTA BLISTER", price: "7.75" },
        { name: "SUERO ANCALMO COCO", price: "26.00" },
        { name: "SUERO ANCALMO FRESA", price: "26.00" },
        { name: "SUERO ANCALMO NARANJA", price: "26.00" },
        { name: "SUERO ANCALMO VITAMINADO", price: "26.00" },
        { name: "SULFATO DE SODA PAQUETES", price: "22.00" }
      ]
    },
    {
      id: "cat-vitaminas",
      name: "VITAMINAS Y SUPLEMENTOS",
      accent: "coral",
      products: [
        { name: "ARTRIBION", price: "38.00" },
        { name: "BACAOLINA", price: "Consultar precio" },
        { name: "CALCIO + B12", price: "Consultar precio" },
        { name: "CARDIO VITAL 60 PASTILLAS", price: "30.00" },
        { name: "CARDIO VITAL 30 PASTILLAS", price: "15.00" },
        { name: "CENTRUM MUJER", price: "17.00" },
        { name: "CENTRUM NIÑO", price: "17.00" },
        { name: "COLÁGENO + CALCIO", price: "17.00" },
        { name: "FERRIDOCE", price: "18.00" },
        { name: "KOMILON", price: "12.00" },
        { name: "MUJER PLEX", price: "Consultar precio" },
        { name: "NEUROTROPAS", price: "Consultar precio" },
        { name: "NEUROBION 25000", price: "17.00" },
        { name: "NEUROBION 25000 INYECCIÓN", price: "25.00" },
        { name: "NEUROBION 3 EN 1", price: "17.00" },
        { name: "NEUROBION 50 MIL", price: "17.00" },
        { name: "NEUROBION 50 MIL OJITO", price: "Consultar precio" },
        { name: "NEUROFORTÁN", price: "10.75" },
        { name: "SUKROL 4 EN 1", price: "17.00" },
        { name: "SUKROL BEBIBLE", price: "18.00" },
        { name: "SUKROL JARABE", price: "14.00" },
        { name: "SUKROL PASTILLA", price: "11.00" },
        { name: "VITAL 4 EN 1", price: "14.00" },
        { name: "VITAL FUERTE JARABE", price: "14.00" },
        { name: "VITAL FUERTE AMPOLLA", price: "18.00" },
        { name: "VITAL FUERTE BEBIBLE", price: "18.00" },
        { name: "VITAL FUERTE B3", price: "25.00" },
        { name: "VITAL FUERTE VITAMINADO PASTILLAS", price: "15.00" },
        { name: "VITAMINAL TRES TOROS", price: "18.00" },
        { name: "VITAMINAS 10 EN 1", price: "18.00" }
      ]
    },
    {
      id: "cat-antibioticos",
      name: "ANTIBIÓTICOS Y ANTIPARASITARIOS",
      accent: "teal",
      products: [
        { name: "ALBENDAZOL MK", price: "12.00" },
        { name: "AMOXICILINA JARABE", price: "15.00" },
        { name: "CIPROFLOXACINA", price: "Consultar precio" },
        { name: "CLINDAMICINA", price: "Consultar precio" },
        { name: "LEVECILIN 400MG", price: "Consultar precio" },
        { name: "LOMBRINIÑOS", price: "33.00" },
        { name: "MEBENDAZOL JARABE", price: "12.00" },
        { name: "MEBENDAZOL PASTILLA", price: "8.00" },
        { name: "METRONIDAZOL JARABE", price: "Consultar precio" },
        { name: "METRONIDAZOL PASTILLA", price: "Consultar precio" },
        { name: "SALUPRIM", price: "8.75" },
        { name: "SANTEMICINA", price: "35.00" },
        { name: "SULFABAC", price: "9.75" }
      ]
    },
    {
      id: "cat-cremas",
      name: "CREMAS, POMADAS Y UNGÜENTOS",
      accent: "green",
      products: [
        { name: "BARMICIL", price: "10.00" },
        { name: "CANESTEN TRIPLE ACCIÓN", price: "10.00" },
        { name: "CLOTRIPLEX", price: "Consultar precio" },
        { name: "COFAL AZUL 60 GRS UNIDADES", price: "10.00" },
        { name: "COFAL ROJO 60 GRS UNIDADES", price: "10.00" },
        { name: "CREMA BÉSAME", price: "5.75" },
        { name: "CREMA BLANCO DERMA ALOE VERA", price: "8.75" },
        { name: "CREMA BLANCO DERMA ARGÁN", price: "8.75" },
        { name: "CREMA BLANCO DERMA AVENA", price: "8.75" },
        { name: "CREMA BLANCO DERMA CLÁSICA", price: "8.75" },
        { name: "CREMA ROSY ROSADA UNIDADES", price: "4.75" },
        { name: "CREMA ROSY VERDE UNIDADES", price: "4.75" },
        { name: "CURADERMA POMADA", price: "3.05" },
        { name: "GMS AMARILLO BALSÁMICO", price: "3.25" },
        { name: "GMS AZUL POMADA", price: "3.25" },
        { name: "MENTOL DAVIS GRANDE 36 UNIDADES", price: "3.25" },
        { name: "MENTOL DAVIS PEQUEÑO DOCENAS", price: "12.00" },
        { name: "POMADA ALCANFORADA UNIDADES", price: "3.25" },
        { name: "POMADA VALENCIA UNIDADES", price: "3.25" },
        { name: "SANA SANA", price: "3.25" },
        { name: "UNGÜENTO DE LEÓN 90 GRS UNIDADES", price: "Consultar precio" }
      ]
    },
    {
      id: "cat-bebes",
      name: "BEBÉS Y NIÑOS",
      accent: "gold",
      products: [
        { name: "ACEITE BABY CHIC 8 ONZ", price: "8.75" },
        { name: "ACEITE BABY CHIC 4 ONZ", price: "6.00" },
        { name: "ACEITE BABY CHIC 2 ONZ", price: "4.50" },
        { name: "BACAOLINITA", price: "12.00" },
        { name: "BALLENA AZUL", price: "12.00" },
        { name: "BEBETINA JARABE", price: "12.00" },
        { name: "BEBETINA PASTILLA", price: "30.00" }
      ]
    },
    {
      id: "cat-naturales",
      name: "NATURALES Y TRADICIONALES",
      accent: "coral",
      products: [
        { name: "AJO MÁS PEREJIL", price: "6.00" },
        { name: "ACHICORIA JARABE CALIQUIMICA", price: "3.25" },
        { name: "ANARA", price: "25.00" },
        { name: "AGUA FLORIDA DE LA ROSA AMARILLA", price: "3.25" },
        { name: "AGUA FLORIDA DE LA ROSA BLANCA UNIDADES", price: "3.25" },
        { name: "AGUA FLORIDA DE LA ROSA VERDE UNIDADES", price: "3.25" },
        { name: "AZÚCAR DE LECHE PAQUETES", price: "17.00" },
        { name: "TÉ CALMADOL", price: "20.00" },
        { name: "CORDIAL DEL SUSTO", price: "3.25" },
        { name: "CORDIAL DEL SUSTO AMARILLO UNIDADES", price: "3.25" },
        { name: "ESENCIA MARAVILLOSA UNIDADES", price: "3.75" },
        { name: "KURA KURA UNIDADES", price: "3.25" },
        { name: "MIEL ROSADA", price: "3.25" },
        { name: "NERVESA", price: "30.00" },
        { name: "OJO DE ÁGUILA", price: "8.00" },
        { name: "TINTURA RUIBARBO", price: "3.25" },
        { name: "RÁBANO YODADO", price: "17.00" },
        { name: "SIETE MACHOS GRANDE", price: "4.75" },
        { name: "SIETE MACHOS MEDIANO", price: "2.75" },
        { name: "SIETE ESPÍRITUS", price: "3.25" },
        { name: "SIETE ESPÍRITUS CALIQUIMICA", price: "3.25" },
        { name: "TÉ DE NERVIOS VIDA", price: "6.00" },
        { name: "TÉ DE TILO VIDA", price: "6.00" },
        { name: "URIN", price: "60.00" },
        { name: "UROFIN", price: "70.00" }
      ]
    },
    {
      id: "cat-otros",
      name: "OTROS",
      accent: "teal",
      products: [
        { name: "CHAMPIOJO BOTES", price: "20.00" },
        { name: "DROPADEX 10 CÁPSULAS", price: "10.00" },
        { name: "NEOBOL SPRAY", price: "Consultar precio" },
        { name: "OTIK", price: "12.00" },
        { name: "PEINE FINO PEQUEÑO DOCENAS", price: "6.00" },
        { name: "PIOJINA 100 ML", price: "4.10" },
        { name: "VIOLETA GENCIANA 1 ONZ UNIDADES", price: "Consultar precio" },
        { name: "YODOCLORINA", price: "35.00" }
      ]
    }
  ]
};
