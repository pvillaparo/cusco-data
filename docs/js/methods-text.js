// Text of the Methods & data page, in English and Spanish. Edit here.
// Each section has an id (used in links: methods.html#population), a title and a body made of
// paragraphs (strings), lists ({list: [...]}), notes ({note: "..."}), tables ({table: [[header...], [row...]]})
// or a citation box ({cite: "..."}). Inside strings, [text](url) makes a link, **text** is bold
// and `text` is code. The "catalogue" section is generated from data/dictionary.json.

const REPO = "https://github.com/pvillaparo/cusco-data";

export const METHODS = {
  en: {
    title: "Methods & data",
    metaDescription: "How Cusco-stats was built: sources, population splice, coverage rules for provinces and the department, real values with the Cusco city CPI, known breaks, and the full indicator catalogue.",
    lede: "Where every number comes from, how the series were made comparable across districts and years, and what to keep in mind when reading them.",
    tocTitle: "On this page",
    skipMethods: "Skip to the content",
    sections: [
      {
        id: "about", title: "What Cusco-stats is",
        body: [
          "Cusco-stats brings together official statistics on the 116 districts of the department of Cusco, Peru: canon transfers, municipal budgets and accounts, schools, civil registration, municipal services, formal jobs, census indicators and poverty. It harmonizes them into one district-by-year dataset and builds province and department figures from it, so that a district can be compared with its province, with Cusco as a whole and with itself over time.",
          "The data go through three steps, and each one can be traced back to the one before. The raw download from INEI is kept as published; it is then turned into district-year panels with consistent units and a single population series; and finally those panels are aggregated to the 13 provinces and the department, checked against the rules described below and labelled in English and Spanish. The website reads only from this last step, and all the code is [on GitHub](" + REPO + ").",
        ],
      },
      {
        id: "sources", title: "Where the numbers come from",
        body: [
          "Every series comes from INEI's **Regional Information System for Decision Making (SIRTOD)**, in a download of 22 September 2026. SIRTOD does not produce most of these data itself: it republishes, district by district, series produced by several public agencies. The main ones are:",
          { list: [
            "**INEI**: population projections, the 2007 and 2017 National Censuses, monetary poverty from the National Household Survey (ENAHO) and the 2013 district poverty map, and the National Registry of Municipalities (RENAMU), an annual survey of all municipalities.",
            "**Ministry of Economy and Finance (MEF)**: canon and FONCOMUN transfers, budget execution of local governments from the SIAF system, and municipal revenue and expenditure from the Public Accounting Directorate (DNCP).",
            "**Ministry of Education (MINEDU)**: the School Census (ESCALE) and the national census test of second graders (ECE).",
            "**RENIEC** (birth registration), the **Ministry of Labour (MTPE)** electronic payroll (formal private jobs) and the **Superintendency of Banking (SBS)** (lending by municipal savings banks).",
          ] },
          "The [indicator catalogue](#catalogue) at the end of this page gives the original source and the SIRTOD codes of each indicator, so any value can be looked up again in SIRTOD.",
        ],
      },
      {
        id: "geography", title: "Districts, provinces and boundaries",
        body: [
          "Cusco has 13 provinces and, today, 116 districts. Eight of them are recent, all in the province of La Convención: Inkawasi and Villa Virgen (2015), Villa Kintiarina (2016), Megantoni (2017), and Kumpirushiato, Cielo Punco, Manitea and Union Ashaninka (2021). A new district has data only from its creation onwards, and the districts it was carved out of (Echarate, Vilcabamba, Kimbiri and Pichari) cover a larger territory in the years before. The explorer flags both situations whenever one of these districts is selected.",
          "Except for three indicators published only as rates (see [below](#aggregation)), province and department values are built from the district data, never taken from a separate table, so moving from Cusco down to a province or a district never shows a contradiction. Because a sum does not depend on internal borders, the creation of new districts does not by itself change province or department figures, as long as every district reports (see [coverage](#aggregation)).",
          "The maps use INEI's district boundaries, IDE 2024 edition (layer `Distritos_INEI_2025_IDE_2024`), obtained from a map service hosted by UNDP on 1 November 2026. Every year is drawn on these current borders. The shapes are simplified for the web (to about 55 metres, keeping shared borders aligned) and province outlines are the union of each province's districts, so they are fine for maps but should not be used to compute areas; the full-resolution layer is in the repository.",
        ],
      },
      {
        id: "population", title: "Population and values per person",
        body: [
          "Values per person (and per 1,000 people) divide by INEI's population projections. INEI has two vintages of projections, one based on the 2007 Census and one based on the 2017 Census, and they do not meet: switching from one to the other in 2017 or 2018 would create a jump in every per-person line that has nothing to do with the district itself. Cusco-stats therefore joins them with a standard **backward splice**: the newer, 2017-based series is kept exactly as published, and the older series is rescaled so that, extended forward at its own 2010–2015 growth rate, it meets the newer series in the newer series' first year (2016 for the department, 2018 for districts). This keeps the year-to-year changes of the old series and moves only its level. District values for 2016 and 2017 are interpolated geometrically, and in every year the districts are scaled to add up to the spliced department total. Because the department and the districts meet the new series in different years, this common scaling adds about 0.8 percentage points to every district's population growth between 2017 and 2018, and shifts earlier growth rates by only about 0.04 points a year.",
          "Districts that were split need extra care, because the old projections refer to the territory before the split. Each parent district is therefore spliced together with the districts carved out of it (Echarate with Megantoni, Vilcabamba with Inkawasi and Villa Virgen, Kimbiri with Villa Kintiarina), so that its old population is matched to the same territory in 2018. For these seven districts the 2015–2017 populations can only be divided approximately, so their district population and per-person values are not shown for those years; province and department values are not affected.",
        ],
      },
      {
        id: "aggregation", title: "From districts to provinces and Cusco",
        body: [
          "How a province or department value is built depends on the kind of indicator:",
          { list: [
            "**Amounts** (soles, people, workers, equipment) are summed over the districts. Values per person are the sum over the reporting districts divided by the population of those same districts, which is the population-weighted average that readers expect.",
            "**Percentages and ratios** are always a ratio of sums. The department's budget execution rate, for example, is total accrued expenditure over the total modified budget, not an average of 116 district rates, which would give a district of 2,000 people the same weight as the city of Cusco.",
            "**Yes/no municipal services** (such as serenazgo) are shown as the share of municipalities that provide the service, where each municipality counts the same whatever its size, or as a count of districts.",
            "**Census indicators** are ratios of the sums of the district counts, which reproduces SIRTOD's official 2017 department figures.",
            "**Indicators published only as rates** (school electricity, the ECE test and poverty) cannot be rebuilt from the districts, because SIRTOD does not publish the counts behind them. For these, the Cusco line is SIRTOD's official department series, districts are shown as published, and there is no province level. For poverty, the official series is an interval for a group of departments that includes Cusco, and the chart shows it as a band.",
          ] },
          "**Coverage rule.** A province or department value is shown only if the districts with data hold at least **95% of the population** and at least **98% of the money** of the districts that exist that year (yes/no services are tested on population only). The money test matters because population alone can miss a large gap: the four districts created in 2021 hold 1.3% of Cusco's people but 4–5% of its municipal spending. Each missing district is sized by its own values in the nearest years around the gap (the average of its values the same number of years before and after, up to three years away). New districts are treated as covered while their territory is still reported by the district they came from: a district in its first year whose budget its parent still reported, and districts created in 2015 or later during their first three years. They count as covered in the population test and their population stays in the per-person denominator, but the money test still applies.",
          "**Official totals check.** Wherever SIRTOD publishes its own department total, the sum of the districts is compared with it, with a 2% tolerance. A mismatch always hides that year at department and province level (districts stay visible). A match, on the other hand, lets a year through only when the districts without data are young ones, created in 2015 or later and in their first three years, whose territory is still reported under their parent districts.",
          "When a year fails these tests, the charts show a gap rather than a misleading value, and the notes under each chart list the years left out.",
        ],
      },
      {
        id: "money", title: "Money: current and constant soles",
        body: [
          "Every amount is available in **current soles** and, from 2010, in **constant 2024 soles**, computed as the nominal value × (2024 average CPI / the year's average CPI). The deflator is INEI's **consumer price index for the city of Cusco**, with annual values taken as the average of the twelve monthly values. The charts use constant soles by default wherever they exist.",
          "SIRTOD holds the Cusco CPI in two monthly series with different bases: one that runs from 1996 to December 2021 (labelled base 2009, a base that applies from January 2010 onwards) and one that starts in January 2022 (base December 2021 = 100). They are linked by expressing the newer series on the older base (multiplying it by the older series' December 2021 value / 100), so that no month's inflation is lost at the junction.",
          { note: "Two limits are worth keeping in mind. First, applying a city price index to every district, rural ones included, is an analytical assumption, because there are no district price indices. Second, real values start in 2010 because the older CPI series has a rebasing break in January 2010 that could not be linked with an official factor: neither of the simple rescalings reproduces INEI's reported January 2010 inflation for Cusco (+0.45%). Earlier years are therefore shown in current soles only. Real values could be extended back if INEI publishes an official linking factor (*factor de empalme*) for Cusco, or index values on both bases for an overlapping period." },
        ],
      },
      {
        id: "breaks", title: "Known breaks and corrections",
        body: [
          "Each indicator is shown only over the years in which it is comparable, and a few source problems are corrected or hidden. The values outside these windows are kept in the dataset, flagged as not displayed, so nothing is lost.",
          { table: [
            ["Indicator", "Years shown", "Why"],
            ["Canon (total, gas, mining, hydropower)", "2005–2024", "2004 is a start-up year with incomplete coverage, and amounts before the 2004 reform are not comparable; 2025 canon is not yet in SIRTOD."],
            ["FONCOMUN", "2009–2025, without 2016", "The district series starts in 2009. SIRTOD's 2016 district values are scrambled across districts: their correlation with 2015 and 2017 is 0.32, against 0.99 or more for every other pair of years."],
            ["Budget execution (SIAF)", "2008–2025", "In 2007 SIAF covers only 40 of the 108 districts that existed then."],
            ["Municipal accounts (revenue, expenditure, capital share, dependence on transfers)", "2004–2025, without 2023", "2023 is broken at the source: expenditure is about 23% above SIAF and revenue about twice its 2022–2024 average in almost every district."],
            ["Births registered late", "Cusco and provinces without 2021–2022", "In those years the district sums of late births fall 2–7% short of SIRTOD's department total."],
            ["Serenazgo", "2007–2024", "2004–2005 seem to answer a different question (even Cusco reads \"no\"), and 2006 has no data."],
            ["Computers in municipalities", "Cusco and provinces without 2015", "Kimbiri's erroneous 2015 value is left out (see below), but SIRTOD's department total still includes it, so the corrected district sum no longer matches the official total."],
          ] },
          "In addition, seven single district values are left blank because they contradict the neighbouring years by an order of magnitude: Vaso de Leche beneficiaries in 2014 in Cusco, Marcapata, Llusco and Omacha (Cusco reads 32, against 3,785 and 3,411 in the years around it); working dump trucks in 2004 in Cusco and Paucartambo; and municipal computers in 2015 in Kimbiri (1,631, against 190 and 162).",
          "Two definitions also deserve care. Total municipal revenue includes **financing**, that is, balances carried over from previous years and borrowing, so it can exceed what a municipality raised in the year; dependence on transfers therefore divides transfer revenue by total revenue minus financing. And RENAMU records equipment early in the following year, so computers and dump trucks are dated to the year before the survey. 2026 is left out for now because it is a partial year.",
        ],
      },
      { id: "catalogue", title: "Indicator catalogue", body: [] },
      {
        id: "reuse", title: "Downloads, code and how to cite",
        body: [
          "Every view of the [explorer](explorer) can be shared as a link, which keeps the indicator, the measure, the places and the year, and downloaded as a CSV file with one row per place and year for the places in the chart, with values at full stored precision rather than the one decimal shown on screen.",
          "The full harmonized dataset is in the [GitHub repository](" + REPO + "), in the `harmonized` folder: `cusco_stats_long.csv` has one row per level, place, year, indicator and measure, with the number of reporting districts and the coverage shares used by the rules above, and `cusco_stats_dictionary.csv` has the labels, units, descriptions, caveats and sources in English and Spanish. The district-year panels it is built from are in the `panels` folder, also in Stata format.",
          "If you use Cusco-stats, please cite it as:",
          { cite: "Villa Paro, Paola (2026). *Cusco-stats: the 116 districts of Cusco, Peru, in data.* https://pvillaparo.github.io/cusco-data/ (data: INEI SIRTOD, download of 22 September 2026)." },
          "**Licence.** The harmonized data, the site data and the text of these pages are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), so they can be reused for any purpose with credit, and the code under the [MIT licence](" + REPO + "/blob/main/LICENSE). The underlying statistics belong to INEI and the other agencies that produce them and remain subject to their terms.",
          "Corrections and suggestions are very welcome through the repository's [issues page](" + REPO + "/issues).",
        ],
      },
      {
        id: "credits", title: "Credits",
        body: [
          "Cusco-stats is a project by [Paola Villa Paro](https://pvillaparo.github.io/), built with assistance from Claude (Anthropic). The data belong to the institutions that produce them, as listed in the catalogue; any error in the harmonization is mine.",
        ],
      },
    ],
    catalogue: {
      intro: (n) => `The ${n} indicators below are generated from the same dictionary the explorer uses, so they always match the data on the site. For each one: what it measures, the measures and units available (and whether it can be mapped), the years with data at each level, how Cusco and province values are computed, the source and its SIRTOD codes, and what to read with care.`,
      open: "Open in explorer",
      measures: "Measures",
      map: "map",
      interval: "Lower and upper bounds of the interval",
      real: "Constant soles",
      realText: (y) => `Also in constant 2024 soles, from ${y}`,
      years: "Years with data",
      levels: { department: "Cusco", province: "Provinces", district: "Districts" },
      method: "Cusco and provinces",
      source: "Source",
    },
  },

  es: {
    title: "Métodos y datos",
    metaDescription: "Cómo se construyó Cusco-stats: fuentes, empalme de la población, reglas de cobertura para provincias y departamento, valores reales con el IPC de la ciudad de Cusco, rupturas conocidas y el catálogo completo de indicadores.",
    lede: "De dónde viene cada número, cómo se hicieron comparables las series entre distritos y años, y qué conviene tener en cuenta al leerlas.",
    tocTitle: "En esta página",
    skipMethods: "Ir al contenido",
    sections: [
      {
        id: "about", title: "Qué es Cusco-stats",
        body: [
          "Cusco-stats reúne estadísticas oficiales de los 116 distritos del departamento de Cusco, Perú: transferencias de canon, presupuestos y cuentas municipales, escuelas, registro civil, servicios municipales, empleo formal, indicadores censales y pobreza. Las armoniza en una sola base de datos por distrito y año, y a partir de ella construye las cifras de provincias y del departamento, de modo que cada distrito pueda compararse con su provincia, con Cusco en conjunto y consigo mismo a lo largo del tiempo.",
          "Los datos pasan por tres etapas, y cada una puede rastrearse hasta la anterior. La descarga original del INEI se conserva tal como se publicó; luego se transforma en paneles por distrito y año con unidades coherentes y una sola serie de población; y, por último, esos paneles se agregan a las 13 provincias y al departamento, se contrastan con las reglas que se describen abajo y se etiquetan en inglés y en español. El sitio web lee solo de esta última etapa, y todo el código está [en GitHub](" + REPO + ").",
        ],
      },
      {
        id: "sources", title: "De dónde vienen los números",
        body: [
          "Todas las series provienen del **Sistema de Información Regional para la Toma de Decisiones (SIRTOD)** del INEI, en una descarga del 22 de septiembre de 2026. El SIRTOD no produce la mayoría de estos datos: los republica, distrito por distrito, a partir de series elaboradas por varias entidades públicas. Las principales son:",
          { list: [
            "**INEI**: proyecciones de población, los Censos Nacionales de 2007 y 2017, la pobreza monetaria de la Encuesta Nacional de Hogares (ENAHO) y el mapa de pobreza distrital de 2013, y el Registro Nacional de Municipalidades (RENAMU), una encuesta anual a todas las municipalidades.",
            "**Ministerio de Economía y Finanzas (MEF)**: transferencias de canon y FONCOMUN, ejecución presupuestal de los gobiernos locales del sistema SIAF, e ingresos y gastos municipales de la Dirección Nacional de Contabilidad Pública (DNCP).",
            "**Ministerio de Educación (MINEDU)**: el Censo Escolar (ESCALE) y la Evaluación Censal de Estudiantes de segundo grado (ECE).",
            "**RENIEC** (registro de nacimientos), la Planilla Electrónica del **Ministerio de Trabajo (MTPE)** (empleo formal privado) y la **Superintendencia de Banca, Seguros y AFP (SBS)** (colocaciones de las cajas municipales).",
          ] },
          "El [catálogo de indicadores](#catalogue), al final de esta página, indica la fuente original y los códigos SIRTOD de cada indicador, de modo que cualquier valor pueda volver a consultarse en el SIRTOD.",
        ],
      },
      {
        id: "geography", title: "Distritos, provincias y límites",
        body: [
          "Cusco tiene 13 provincias y, hoy, 116 distritos. Ocho de ellos son recientes, todos en la provincia de La Convención: Inkawasi y Villa Virgen (2015), Villa Kintiarina (2016), Megantoni (2017), y Kumpirushiato, Cielo Punco, Manitea y Union Ashaninka (2021). Un distrito nuevo tiene datos solo desde su creación, y los distritos de los que se separó (Echarate, Vilcabamba, Kimbiri y Pichari) abarcan un territorio mayor en los años anteriores. El explorador advierte ambas situaciones cada vez que se selecciona uno de estos distritos.",
          "Salvo tres indicadores publicados solo como tasas (ver [más abajo](#aggregation)), los valores de provincias y del departamento se construyen a partir de los datos distritales, nunca de una tabla aparte, de modo que al pasar de Cusco a una provincia o a un distrito nunca aparece una contradicción. Como una suma no depende de los límites internos, la creación de distritos nuevos no cambia por sí sola las cifras de provincias o del departamento, siempre que todos los distritos reporten (ver [cobertura](#aggregation)).",
          "Los mapas usan los límites distritales del INEI, edición IDE 2024 (capa `Distritos_INEI_2025_IDE_2024`), obtenidos el 1 de noviembre de 2026 de un servicio de mapas alojado por el PNUD. Todos los años se dibujan sobre estos límites actuales. Las formas se simplifican para la web (a unos 55 metros, sin desalinear los límites compartidos) y los contornos de las provincias son la unión de sus distritos, así que sirven para mapas pero no para calcular áreas; la capa a resolución completa está en el repositorio.",
        ],
      },
      {
        id: "population", title: "Población y valores por habitante",
        body: [
          "Los valores por habitante (y por cada 1 000 habitantes) dividen entre las proyecciones de población del INEI. El INEI tiene dos generaciones de proyecciones, una basada en el Censo de 2007 y otra en el de 2017, y no coinciden: pasar de una a otra en 2017 o 2018 crearía un salto en todas las series por habitante que nada tiene que ver con el distrito. Por eso Cusco-stats las une con un **empalme hacia atrás** estándar: la serie más reciente, basada en 2017, se mantiene exactamente como se publicó, y la serie antigua se reescala para que, prolongada con su propia tasa de crecimiento de 2010–2015, coincida con la nueva en el primer año de esta (2016 para el departamento, 2018 para los distritos). Así se conservan las variaciones anuales de la serie antigua y solo cambia su nivel. Los valores distritales de 2016 y 2017 se interpolan geométricamente y, en cada año, los distritos se escalan para que sumen el total departamental empalmado. Como el departamento y los distritos se enlazan con la serie nueva en años distintos, este escalamiento común añade unos 0,8 puntos porcentuales al crecimiento poblacional de cada distrito entre 2017 y 2018, y desplaza las tasas de crecimiento anteriores en apenas unos 0,04 puntos al año.",
          "Los distritos que se dividieron requieren un cuidado adicional, porque las proyecciones antiguas se refieren al territorio previo a la división. Por eso cada distrito de origen se empalma junto con los distritos que se separaron de él (Echarate con Megantoni, Vilcabamba con Inkawasi y Villa Virgen, Kimbiri con Villa Kintiarina), de modo que su población antigua corresponda al mismo territorio en 2018. Para estos siete distritos la población de 2015–2017 solo puede repartirse de forma aproximada, así que su población distrital y sus valores por habitante no se muestran en esos años; los valores de provincias y del departamento no se ven afectados.",
        ],
      },
      {
        id: "aggregation", title: "De los distritos a las provincias y a Cusco",
        body: [
          "La forma de construir el valor de una provincia o del departamento depende del tipo de indicador:",
          { list: [
            "**Montos** (soles, personas, trabajadores, equipos): se suman los distritos. Los valores por habitante son la suma de los distritos que reportan dividida entre la población de esos mismos distritos, es decir, el promedio ponderado por población que el lector espera.",
            "**Porcentajes y razones**: siempre son un cociente de sumas. El avance de ejecución del departamento, por ejemplo, es el gasto devengado total entre el presupuesto modificado total, no un promedio de 116 tasas distritales, que daría a un distrito de 2 000 habitantes el mismo peso que a la ciudad del Cusco.",
            "**Servicios municipales de sí o no** (como el serenazgo): se muestran como el porcentaje de municipalidades que prestan el servicio, donde cada municipalidad cuenta igual sea cual sea su tamaño, o como un número de distritos.",
            "**Indicadores censales**: son cocientes de las sumas de los conteos distritales, lo que reproduce las cifras departamentales oficiales de 2017 del SIRTOD.",
            "**Indicadores publicados solo como tasas** (electricidad en las escuelas, la ECE y la pobreza): no pueden reconstruirse a partir de los distritos, porque el SIRTOD no publica los conteos que los sustentan. En estos casos, la línea de Cusco es la serie departamental oficial del SIRTOD, los distritos se muestran tal como se publican y no hay nivel provincial. Para la pobreza, la serie oficial es un intervalo para un grupo de departamentos que incluye a Cusco, y el gráfico lo muestra como una banda.",
          ] },
          "**Regla de cobertura.** El valor de una provincia o del departamento se muestra solo si los distritos con datos concentran al menos el **95% de la población** y al menos el **98% del dinero** de los distritos que existen ese año (los servicios de sí o no se evalúan solo por población). La prueba del dinero importa porque la población por sí sola puede pasar por alto un vacío grande: los cuatro distritos creados en 2021 tienen el 1,3% de la población de Cusco pero entre el 4% y el 5% de su gasto municipal. Cada distrito faltante se dimensiona con sus propios valores en los años más cercanos al vacío (el promedio de sus valores a la misma distancia antes y después, hasta tres años). Los distritos nuevos se consideran cubiertos mientras su territorio todavía lo reporta el distrito del que se separaron: un distrito en su primer año cuyo presupuesto aún reportaba el distrito de origen, y los distritos creados en 2015 o después durante sus tres primeros años. Cuentan como cubiertos en la prueba de población y su población se mantiene en el denominador por habitante, pero la prueba del dinero sigue aplicándose.",
          "**Contraste con los totales oficiales.** Cuando el SIRTOD publica su propio total departamental, la suma de los distritos se compara con él, con una tolerancia del 2%. Una discrepancia siempre oculta ese año a nivel departamental y provincial (los distritos siguen visibles). Una coincidencia, en cambio, deja pasar un año solo cuando los distritos sin datos son recientes, creados en 2015 o después y en sus tres primeros años, cuyo territorio todavía se reporta bajo sus distritos de origen.",
          "Cuando un año no supera estas pruebas, los gráficos muestran un vacío en lugar de un valor engañoso, y las notas debajo de cada gráfico listan los años omitidos.",
        ],
      },
      {
        id: "money", title: "Dinero: soles corrientes y constantes",
        body: [
          "Todos los montos están disponibles en **soles corrientes** y, desde 2010, en **soles constantes de 2024**, calculados como el valor nominal × (IPC promedio de 2024 / IPC promedio del año). El deflactor es el **índice de precios al consumidor de la ciudad de Cusco** del INEI, con valores anuales calculados como el promedio de los doce valores mensuales. Los gráficos usan soles constantes por defecto siempre que existen.",
          "El SIRTOD guarda el IPC de Cusco en dos series mensuales con bases distintas: una que va de 1996 a diciembre de 2021 (rotulada base 2009, una base que rige desde enero de 2010) y otra que empieza en enero de 2022 (base diciembre de 2021 = 100). Se enlazan expresando la serie más reciente en la base de la antigua (multiplicándola por el valor de diciembre de 2021 de la serie antigua / 100), de modo que no se pierde la inflación de ningún mes en la unión.",
          { note: "Conviene tener en cuenta dos límites. Primero, aplicar un índice de precios de la ciudad a todos los distritos, incluidos los rurales, es un supuesto analítico, porque no existen índices de precios distritales. Segundo, los valores reales empiezan en 2010 porque la serie antigua del IPC tiene un cambio de base en enero de 2010 que no pudo enlazarse con un factor oficial: ninguno de los reescalamientos simples reproduce la inflación de enero de 2010 que el INEI reporta para Cusco (+0,45%). Por eso los años anteriores se muestran solo en soles corrientes. Los valores reales podrían extenderse hacia atrás si el INEI publica un factor de empalme oficial para Cusco, o valores del índice en ambas bases para un periodo común." },
        ],
      },
      {
        id: "breaks", title: "Rupturas conocidas y correcciones",
        body: [
          "Cada indicador se muestra solo en los años en que es comparable, y algunos problemas de la fuente se corrigen u ocultan. Los valores fuera de estas ventanas se conservan en la base de datos, marcados como no mostrados, así que nada se pierde.",
          { table: [
            ["Indicador", "Años mostrados", "Por qué"],
            ["Canon (total, gas, minero, hidroenergético)", "2005–2024", "2004 es un año de arranque con cobertura incompleta, y los montos anteriores a la reforma de 2004 no son comparables; el canon de 2025 aún no está en el SIRTOD."],
            ["FONCOMUN", "2009–2025, sin 2016", "La serie distrital empieza en 2009. Los valores distritales de 2016 del SIRTOD están desordenados entre distritos: su correlación con 2015 y 2017 es 0,32, frente a 0,99 o más para cualquier otro par de años."],
            ["Ejecución presupuestal (SIAF)", "2008–2025", "En 2007 el SIAF cubre solo 40 de los 108 distritos que existían entonces."],
            ["Cuentas municipales (ingresos, gastos, participación del gasto de capital, dependencia de transferencias)", "2004–2025, sin 2023", "2023 está roto en la fuente: el gasto supera al del SIAF en cerca de 23% y los ingresos duplican su promedio de 2022–2024 en casi todos los distritos."],
            ["Nacimientos inscritos tardíamente", "Cusco y provincias sin 2021–2022", "En esos años la suma distrital de inscripciones tardías queda entre 2% y 7% por debajo del total departamental del SIRTOD."],
            ["Serenazgo", "2007–2024", "2004–2005 parecen responder a otra pregunta (incluso Cusco figura con \"no\"), y 2006 no tiene datos."],
            ["Computadoras de las municipalidades", "Cusco y provincias sin 2015", "Se omite el valor erróneo de Kimbiri en 2015 (ver abajo), pero el total departamental del SIRTOD todavía lo incluye, así que la suma distrital corregida ya no coincide con el total oficial."],
          ] },
          "Además, siete valores distritales aislados se dejan en blanco porque contradicen a los años vecinos en un orden de magnitud: beneficiarios del Vaso de Leche en 2014 en Cusco, Marcapata, Llusco y Omacha (Cusco figura con 32, frente a 3 785 y 3 411 en los años de alrededor); volquetes operativos en 2004 en Cusco y Paucartambo; y computadoras municipales en 2015 en Kimbiri (1 631, frente a 190 y 162).",
          "También hay dos definiciones que merecen cuidado. Los ingresos municipales totales incluyen el **financiamiento**, es decir, saldos de años anteriores y endeudamiento, de modo que pueden superar lo que la municipalidad recaudó en el año; por eso la dependencia de transferencias divide los ingresos por transferencias entre los ingresos totales menos el financiamiento. Y el RENAMU registra el equipamiento a inicios del año siguiente, así que las computadoras y los volquetes se fechan en el año anterior a la encuesta. 2026 se deja fuera por ahora porque es un año incompleto.",
        ],
      },
      { id: "catalogue", title: "Catálogo de indicadores", body: [] },
      {
        id: "reuse", title: "Descargas, código y cómo citar",
        body: [
          "Cada vista del [explorador](explorer) puede compartirse como un enlace, que conserva el indicador, la medida, los lugares y el año, y descargarse como un archivo CSV con una fila por lugar y año para los lugares del gráfico, con los valores en su precisión completa y no con el único decimal que se muestra en pantalla.",
          "La base de datos armonizada completa está en el [repositorio de GitHub](" + REPO + "), en la carpeta `harmonized`: `cusco_stats_long.csv` tiene una fila por nivel, lugar, año, indicador y medida, con el número de distritos que reportan y las proporciones de cobertura que usan las reglas anteriores, y `cusco_stats_dictionary.csv` tiene las etiquetas, unidades, descripciones, advertencias y fuentes en inglés y en español. Los paneles por distrito y año de los que se construye están en la carpeta `panels`, también en formato Stata.",
          "Si usas Cusco-stats, por favor cítalo así:",
          { cite: "Villa Paro, Paola (2026). *Cusco-stats: los 116 distritos de Cusco, Perú, en datos.* https://pvillaparo.github.io/cusco-data/ (datos: INEI SIRTOD, descarga del 22 de septiembre de 2026)." },
          "**Licencia.** Los datos armonizados, los datos del sitio y los textos de estas páginas se publican bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es), de modo que pueden reutilizarse con cualquier fin citando la fuente, y el código bajo la [licencia MIT](" + REPO + "/blob/main/LICENSE). Las estadísticas de origen pertenecen al INEI y a las demás entidades que las producen, y siguen sujetas a sus condiciones.",
          "Las correcciones y sugerencias son muy bienvenidas a través de la [página de issues](" + REPO + "/issues) del repositorio.",
        ],
      },
      {
        id: "credits", title: "Créditos",
        body: [
          "Cusco-stats es un proyecto de [Paola Villa Paro](https://pvillaparo.github.io/), elaborado con la asistencia de Claude (Anthropic). Los datos pertenecen a las instituciones que los producen, según se indica en el catálogo; cualquier error en la armonización es mío.",
        ],
      },
    ],
    catalogue: {
      intro: (n) => `Los ${n} indicadores que siguen se generan a partir del mismo diccionario que usa el explorador, así que siempre coinciden con los datos del sitio. Para cada uno: qué mide, las medidas y unidades disponibles (y si puede mapearse), los años con datos en cada nivel, cómo se calculan los valores de Cusco y de las provincias, la fuente con sus códigos SIRTOD y qué leer con cuidado.`,
      open: "Abrir en el explorador",
      measures: "Medidas",
      map: "mapa",
      interval: "Límites inferior y superior del intervalo",
      real: "Soles constantes",
      realText: (y) => `También en soles constantes de 2024, desde ${y}`,
      years: "Años con datos",
      levels: { department: "Cusco", province: "Provincias", district: "Distritos" },
      method: "Cusco y provincias",
      source: "Fuente",
    },
  },
};
