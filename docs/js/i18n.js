// Interface strings and number formatting, English and Spanish.
// Indicator labels, units and notes come from data/dictionary.json, not from here.

export const STRINGS = {
  en: {
    skip: "Skip to the explorer",
    tagline: "The 116 districts of Cusco, Peru, in data",
    navStory: "Story", navExplorer: "Explorer", navMethods: "Methods & data", soon: "(soon)",
    explorerTitle: "Explorer",
    explorerIntro: "Choose an indicator, then add provinces or districts to compare them with Cusco as a whole. Click a district on the map to add it to the chart.",
    indicator: "Indicator", measure: "Measure", units: "Soles", unitsReal: "Constant 2024", unitsNominal: "Current",
    addPlace: "Add a province or district", addPlaceHint: "Type a name…",
    showTable: "Show table", hideTable: "Hide table", downloadCsv: "Download CSV",
    year: "Year", aboutIndicator: "About this indicator",
    footerBy: "Built by", footerRepo: "Data and code on GitHub",
    cusco: "Cusco (department)", cuscoShort: "Cusco dept.", province: "province", district: "district",
    remove: "Remove", noData: "No data", yes: "Yes", no: "No",
    officialTag: "official series",
    officialNote: "The Cusco line is SIRTOD's official department series; it is not built from the districts.",
    noProvinceLevel: "This indicator has no province level.",
    noDistrictLevel: "This indicator is not available by district, so there is no map.",
    tooMany: "Up to six places can be compared at once. Remove one to add another.",
    notFound: "No province or district matches that name.",
    notAvailablePlace: (name) => `${name} has no data for this measure.`,
    realFrom2010: "Constant-soles values start in 2010 (the Cusco price index before 2010 is not yet linked). Switch to current soles to see earlier years.",
    coverage: (n, N) => `${n} of ${N} districts with data`,
    yearsShown: (a, b) => (a === b ? `${a}` : `${a}–${b}`),
    mapTitle: (label) => `${label}, by district`,
    mapSubtitle: (y) => `Year ${y}. Click a district to add it to the chart.`,
    mapNoDataLegend: "No data",
    interval: (lo, hi) => `interval ${lo}–${hi}`,
    band: "Confidence interval",
    description: "What it measures", caveats: "Read with care", source: "Source", method: "How Cusco and provinces are computed",
    placeNotes: "About the places selected",
    created: (name, y) => `${name} was created in ${y}; it has data from that year onwards.`,
    lostTerritory: (name) => `${name} lost territory when new districts were created (2015–2021), so its earlier values cover a larger area.`,
    dataVintage: (v, b) => `Data: INEI SIRTOD, downloaded ${v}. Site data built ${b}.`,
    sirtodCodes: "SIRTOD codes",
    aggregation: {
      sum: "Sum of the districts.",
      sum_over_population: "Sum of the districts divided by their population.",
      sum_over_population_x1000: "Sum of the districts per 1,000 residents.",
      ratio_of_sums: "Ratio of the district sums (not an average of district ratios).",
      count_of_districts: "Number of districts.",
      share_of_reporting_municipalities: "Share of the municipalities that answered the survey.",
      official: "Official department series published by SIRTOD; districts as published; no province level.",
      snapshot: "Ratio of the sums of the district census counts.",
    },
    loading: "Loading…",
    loadError: "The data could not be loaded. Please reload the page.",
    chartLabel: (label, places) => `Line chart of ${label} for ${places}.`,
    mapLabel: (label, y) => `Map of ${label} by district, ${y}.`,
    tableYear: "Year",
  },
  es: {
    skip: "Ir al explorador",
    tagline: "Los 116 distritos de Cusco, Perú, en datos",
    navStory: "Historia", navExplorer: "Explorador", navMethods: "Métodos y datos", soon: "(pronto)",
    explorerTitle: "Explorador",
    explorerIntro: "Elige un indicador y añade provincias o distritos para compararlos con el departamento de Cusco. Haz clic en un distrito del mapa para añadirlo al gráfico.",
    indicator: "Indicador", measure: "Medida", units: "Soles", unitsReal: "Constantes de 2024", unitsNominal: "Corrientes",
    addPlace: "Añadir una provincia o distrito", addPlaceHint: "Escribe un nombre…",
    showTable: "Ver tabla", hideTable: "Ocultar tabla", downloadCsv: "Descargar CSV",
    year: "Año", aboutIndicator: "Sobre este indicador",
    footerBy: "Elaborado por", footerRepo: "Datos y código en GitHub",
    cusco: "Cusco (departamento)", cuscoShort: "Cusco dpto.", province: "provincia", district: "distrito",
    remove: "Quitar", noData: "Sin datos", yes: "Sí", no: "No",
    officialTag: "serie oficial",
    officialNote: "La línea de Cusco es la serie oficial departamental de SIRTOD; no se calcula a partir de los distritos.",
    noProvinceLevel: "Este indicador no tiene nivel provincial.",
    noDistrictLevel: "Este indicador no está disponible por distrito, por eso no hay mapa.",
    tooMany: "Se pueden comparar hasta seis lugares a la vez. Quita uno para añadir otro.",
    notFound: "Ninguna provincia o distrito coincide con ese nombre.",
    notAvailablePlace: (name) => `${name} no tiene datos para esta medida.`,
    realFrom2010: "Los valores en soles constantes empiezan en 2010 (el índice de precios de Cusco anterior a 2010 aún no está empalmado). Cambia a soles corrientes para ver los años anteriores.",
    coverage: (n, N) => `${n} de ${N} distritos con datos`,
    yearsShown: (a, b) => (a === b ? `${a}` : `${a}-${b}`),
    mapTitle: (label) => `${label}, por distrito`,
    mapSubtitle: (y) => `Año ${y}. Haz clic en un distrito para añadirlo al gráfico.`,
    mapNoDataLegend: "Sin datos",
    interval: (lo, hi) => `intervalo ${lo}-${hi}`,
    band: "Intervalo de confianza",
    description: "Qué mide", caveats: "Leer con cuidado", source: "Fuente", method: "Cómo se calculan Cusco y las provincias",
    placeNotes: "Sobre los lugares seleccionados",
    created: (name, y) => `${name} se creó en ${y}; tiene datos desde ese año.`,
    lostTerritory: (name) => `${name} perdió territorio al crearse nuevos distritos (2015-2021), por lo que sus valores anteriores cubren un área mayor.`,
    dataVintage: (v, b) => `Datos: INEI SIRTOD, descargados el ${v}. Datos del sitio generados el ${b}.`,
    sirtodCodes: "Códigos SIRTOD",
    aggregation: {
      sum: "Suma de los distritos.",
      sum_over_population: "Suma de los distritos dividida entre su población.",
      sum_over_population_x1000: "Suma de los distritos por cada 1 000 habitantes.",
      ratio_of_sums: "Cociente de las sumas distritales (no un promedio de los cocientes distritales).",
      count_of_districts: "Número de distritos.",
      share_of_reporting_municipalities: "Porcentaje de las municipalidades que respondieron la encuesta.",
      official: "Serie oficial departamental publicada por SIRTOD; distritos tal como se publican; sin nivel provincial.",
      snapshot: "Cociente de las sumas de los conteos censales distritales.",
    },
    loading: "Cargando…",
    loadError: "No se pudieron cargar los datos. Vuelve a cargar la página.",
    chartLabel: (label, places) => `Gráfico de líneas de ${label} para ${places}.`,
    mapLabel: (label, y) => `Mapa de ${label} por distrito, ${y}.`,
    tableYear: "Año",
  },
};

// English: 1,234.5   Spanish (INEI style): 1 234,5  (narrow no-break space, decimal comma)
export function makeFormatter(lang) {
  const nf = (digits, fixed = false) => new Intl.NumberFormat("en-US", { maximumFractionDigits: digits, minimumFractionDigits: fixed ? digits : 0 });
  const toEs = (s) => s.replace(/,/g, " ").replace(/\./g, ",");
  const fmt = (v, digits = 1) => {
    if (v === null || v === undefined || Number.isNaN(v)) return "–";
    const s = nf(digits, true).format(v);      // values keep a fixed number of decimals
    return lang === "es" ? toEs(s) : s;
  };
  const compact = (v) => {
    if (v === null || v === undefined || Number.isNaN(v)) return "–";
    const a = Math.abs(v);
    let s;
    if (a >= 1e9) s = nf(1).format(v / 1e9) + (lang === "es" ? " mil M" : "B");
    else if (a >= 1e6) s = nf(1).format(v / 1e6) + "M";
    else if (a >= 1e4) s = nf(0).format(v / 1e3) + "k";
    else s = nf(a < 10 ? 1 : 0).format(v);
    return lang === "es" ? toEs(s) : s;
  };
  return { fmt, compact };
}

export function digitsFor(measure) {
  if (["total", "total_real", "count"].includes(measure)) return 0;
  if (["per_capita", "per_capita_real", "per_1000"].includes(measure)) return 1;
  return 1;
}
