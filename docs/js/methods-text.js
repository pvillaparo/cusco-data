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
          "The data go through three steps, and each one can be traced back to the one before. The raw download from INEI is kept as published; it is then turned into district-year panels with consistent units and a single population series; and finally those panels are aggregated to the 13 provinces and the department, checked against the rules described below and labelled in English and Spanish. All the numbers on the website come from this last step (the export only adds place names, the flags for new districts and the map boundaries), and all the code is [on GitHub](" + REPO + ").",
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
          "The [indicator catalogue](#catalogue) further down this page gives the original source and the SIRTOD codes of each indicator, so any value can be looked up again in SIRTOD.",
        ],
      },
      {
        id: "geography", title: "Districts, provinces and boundaries",
        body: [
          "Cusco has 13 provinces and, today, 116 districts. Eight of them are recent, all in the province of La Convención, and appear in SIRTOD's data from these years: Inkawasi and Villa Virgen (2015), Villa Kintiarina (2016), Megantoni (2017; created by a 2016 law) and Kumpirushiato, Cielo Punco, Manitea and Union Ashaninka (2021). A new district has data only from that year onwards (the 2013 poverty map, which already includes Inkawasi and Villa Virgen, is the exception), and the districts it was carved out of (Echarate, Vilcabamba, Kimbiri and Pichari) cover a larger territory in the years before. The explorer flags both situations whenever one of these districts is selected.",
          "Except for four indicators published only as rates (school electricity, the two ECE scores and poverty; see [below](#aggregation)), province and department values are built from the district data, never taken from a separate table, so moving from Cusco down to a province or a district never shows a contradiction. Because a sum does not depend on internal borders, the creation of new districts does not by itself change province or department figures, as long as every district reports (see [coverage](#aggregation)).",
          "The maps use INEI's district boundaries, IDE 2024 edition (layer `Distritos_INEI_2025_IDE_2024`), obtained from a map service hosted by UNDP on 1 November 2026. Every year is drawn on these current borders. The shapes are simplified for the web (to about 55 metres, keeping shared borders aligned) and province outlines are the union of each province's districts, so they are fine for maps but should not be used to compute areas; the full-resolution layer is in the repository.",
        ],
      },
      {
        id: "population", title: "Population and values per person",
        body: [
          "Values per person (and per 1,000 people) divide by INEI's population projections. INEI has two vintages of projections, one based on the 2007 Census and one based on the 2017 Census, and they do not meet: switching from one to the other would create a jump in every per-person line that has nothing to do with the district itself. Cusco-stats therefore joins them with a standard **backward splice**: the newer, 2017-based series is kept exactly as published, and the older series is rescaled so that, extended forward at its own 2010–2015 growth rate, it meets the newer series in the newer series' first year (2016 for the department, 2018 for districts). This keeps the year-to-year changes of the old series and moves only its level. District values for 2016 and 2017 are interpolated geometrically, and in every year the districts are scaled to add up to the spliced department total. Because the department and the districts meet the new series in different years, this common scaling adds about 0.8 percentage points to every district's population growth in both 2016–2017 and 2017–2018 (about 1.6 points over the two years), takes about 0.06 points off 2015–2016, and shifts growth rates up to 2015 by only about 0.04 points a year.",
          "Districts that were split need extra care, because the old projections refer to the territory before the split. Each parent district is therefore spliced together with the districts carved out of it (Echarate with Megantoni, Vilcabamba with Inkawasi and Villa Virgen, Kimbiri with Villa Kintiarina; the Megantoni–Echarate split is documented, and the other links are inferred from population changes when the new districts appear), so that its old population is matched to the same territory in 2018. For these seven districts the 2015–2017 populations can only be divided approximately, so their district population and per-person values are not shown for those years; province and department values are not affected.",
          "The download already includes first counts from the 2025 Census. For Cusco as a whole they are about 8% below the projection, a gap similar to 2017's, but in 24 of the 116 districts the count differs from the projection by more than 20% (Megantoni: 16,333 counted against 7,335 projected). Per-person values for recent years in those districts should therefore be read with care until INEI publishes projections based on the 2025 Census.",
        ],
      },
      {
        id: "aggregation", title: "From districts to provinces and Cusco",
        body: [
          "How a province or department value is built depends on the kind of indicator:",
          { list: [
            "**Amounts** (soles, people, workers, equipment) are summed over the districts. Values per person are the sum over the reporting districts divided by the population of the territory they cover (including new districts still reported by their parent; see the coverage rule), which is the population-weighted average that readers expect.",
            "**Percentages and ratios** are always a ratio of sums. The department's budget execution rate, for example, is total accrued expenditure over the total modified budget, not an average of 116 district rates, which would give a district of 2,000 people the same weight as Cusco district (about 120,000 people).",
            "**Yes/no indicators** are shown either as the share of municipalities that provide a service (serenazgo), where each municipality counts the same whatever its size, or as a count of districts (districts where a municipal savings bank lends).",
            "**Census indicators** are ratios of the sums of the district counts. For 2017 this reproduces SIRTOD's official department figures (except one evident error in its mobile-phone total). For 2007 it does not, because SIRTOD's own 2007 province and department totals for several items are wrong (see [known breaks](#breaks)).",
            "**Indicators published only as rates** (school electricity, the ECE test and poverty) cannot be rebuilt from the districts, because SIRTOD does not publish the counts behind them. For these, the Cusco line is SIRTOD's official department series, districts are shown as published, and there is no province level. For poverty, the official series is an interval for a group of departments that includes Cusco, and the chart shows it as a band.",
          ] },
          "**Coverage rule.** A province or department value is shown only if the districts with data hold at least **95% of the population** and at least **98% of the money** (or, for counts such as computers or beneficiaries, of the quantity being added up) of the districts that exist that year (yes/no indicators are tested on population only). The money test matters because population alone can miss a large gap: the four districts created in 2021 hold 1.3% of Cusco's people but 4–5% of its municipal spending. Each missing district is sized by its own values in the nearest years around the gap (the average of its values the same number of years before and after, up to three years away). New districts are treated as covered while their territory is still reported by the district they came from: a district in its first year whose budget its parent still reported, and districts created in 2015 or later during their first three years. Both count as covered in the population test and keep their population in the per-person denominator. The money test still applies to young districts; a district whose budget its parent still reported is left out of it, because its money is already in the parent's figure.",
          "**Official totals check.** For six indicators (pupils per teacher, births registered late, formal private workers, municipal computers, dump trucks and Vaso de Leche beneficiaries), the sum of the districts is also compared with SIRTOD's own department total, with a 2% tolerance. A mismatch always hides that year at department and province level (districts stay visible). A match, on the other hand, lets a year through only when the districts without data are young ones, created in 2015 or later and in their first three years, whose territory is still reported under their parent districts.",
          "When a year fails these tests, the charts show a gap rather than a misleading value, and the notes under each chart list the years left out for Cusco.",
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
          "Each indicator is shown only over the years in which it is comparable, and a few source problems are corrected or hidden. The values outside these windows are kept in the dataset, flagged as not displayed; the seven source errors listed below are removed from the harmonized file but remain in the panels and the raw download.",
          { table: [
            ["Indicator", "Years shown", "Why"],
            ["Canon (total, gas, mining, hydropower)", "2005–2024", "2004 is a start-up year with incomplete coverage, and amounts before the 2004 reform are not comparable; 2025 canon is not yet in SIRTOD."],
            ["FONCOMUN", "2009–2025, without 2016", "The district series starts in 2009. SIRTOD's 2016 district values are scrambled across districts: their correlation with 2015 and 2017 is about 0.32–0.33, against 0.99 or more for every other pair of consecutive years."],
            ["Budget execution (SIAF)", "2008–2025", "In 2007 SIAF covers only 40 of the 108 districts that existed then."],
            ["Municipal accounts (revenue, expenditure, capital share, dependence on transfers)", "2004–2025, without 2023", "2023 is broken at the source: expenditure is about 23% above SIAF and revenue about twice the average of 2022 and 2024 in almost every district."],
            ["Births registered late", "Cusco and provinces without 2021–2022", "In those years the district sums of late births fall 2–7% short of SIRTOD's department total."],
            ["Serenazgo", "2007–2024", "2004–2005 seem to answer a different question (even Cusco reads \"no\"), and 2006 has no data."],
            ["2007 Census (dwelling and household items: water, sewer, electricity, floors, cooking fuel, internet, mobile phones)", "Built from the districts", "SIRTOD's own 2007 province and department totals do not add up to its district counts. At department level, dwellings with piped water and with electricity are 14% below the district sums, internet 27% and mobile phones 17%, and the dwellings counted by electricity and the households counted by cooking fuel are 9% short. Province totals miss in both directions, most in Cusco, Paruro, Acomayo and La Convención, and for internet and mobile phones in almost every province. With SIRTOD's dwelling totals, the provinces of Cusco and Paruro would have 5.8 and 6.4 persons per dwelling, against 3.7–4.3 in every province from the district counts. The district counts are taken as correct, so the 2007 Cusco values differ from those implied by SIRTOD's department totals by up to 7 points (earth floors: 66.5% against 73.2%)."],
            ["2017 Census (households: internet, mobile phones, cooking fuel)", "Built from the districts", "In 2017 a household could report several cooking fuels, so the fuel categories add up to about 15% more than the number of households. Household shares therefore divide by SIRTOD's own total of households (code 516818), and the 2017 cooking figure counts any use of firewood or dung, not the main fuel as in 2007: it is an upper bound for the 2007 concept, and the two censuses are not strictly comparable on cooking."],
            ["Computers in municipalities", "Cusco and provinces without 2015", "Kimbiri's erroneous 2015 value is left out (see below), but SIRTOD's department total still includes it, so the corrected district sum no longer matches the official total."],
            ["Working dump trucks", "Cusco and provinces without 2004 (no data for 2005)", "Cusco's and Paucartambo's 2004 values are left out (see below), but SIRTOD's department total still includes them, so the corrected district sum no longer matches the official total."],
          ] },
          "In addition, seven single district values are left blank because they contradict the neighbouring years by a factor of five or more: Vaso de Leche beneficiaries in 2014 in the districts of Cusco, Marcapata, Llusco and Omacha (Cusco district reads 32, against 3,785 and 3,411 in the years around it); working dump trucks in 2004 in Cusco and Paucartambo; and municipal computers in 2015 in Kimbiri (1,631, against 190 and 162).",
          "Two definitions also deserve care. Total municipal revenue includes **financing**, that is, balances carried over from previous years and borrowing, so it can exceed what a municipality raised in the year; dependence on transfers therefore divides transfer revenue by total revenue minus financing. And RENAMU appears to record equipment early in the following year (an assumption based on its survey calendar), so computers and dump trucks are dated to the year before the survey. 2026 is left out for now because it is a partial year.",
        ],
      },
      { id: "catalogue", title: "Indicator catalogue", body: [] },
      {
        id: "reuse", title: "Downloads, code and how to cite",
        body: [
          "Every view of the [explorer](explorer) can be shared as a link, which keeps the indicator, the measure, the places and the year, and downloaded as a CSV file with one row per place and year for the places in the chart, with percentages and ratios at four decimals rather than the one decimal shown on screen. Read the code column as text: UBIGEO codes keep their leading zero (08, 0809, 080902).",
          "The full harmonized dataset is in the [GitHub repository](" + REPO + "), in the `harmonized` folder: `cusco_stats_long.csv` has one row per level, place, year, indicator and measure, with the number of reporting districts and the coverage shares used by the rules above, and `cusco_stats_dictionary.csv` has the labels, units, descriptions, caveats and sources in English and Spanish. The district-year panels it is built from are in the `panels` folder, also in Stata format.",
          "If you use Cusco-stats, please cite it as:",
          { cite: "Villa Paro, Paola (2026). *Cusco-stats: the 116 districts of Cusco, Peru, in data.* https://pvillaparo.github.io/cusco-data/ (data: INEI SIRTOD, download of 22 September 2026)." },
          "**Licence.** The harmonized data, the district-year panels, the site data, the documentation and the text of these pages are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (see [LICENSE-DATA.md](" + REPO + "/blob/main/LICENSE-DATA.md)), so they can be reused for any purpose with credit, and the code under the [MIT licence](" + REPO + "/blob/main/LICENSE). The underlying statistics belong to INEI and the other agencies that produce them and remain subject to their terms.",
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
      intro: (n) => `The ${n} indicators below are generated from the same dictionary the explorer uses, so they always match the data on the site. For each one: what it measures, the measures and units available (and whether it can be mapped), the years with data at each level, how Cusco and province values are computed, the source and its SIRTOD codes, and what to read with care. A year is listed for provinces or districts when at least one of them has data that year, so in some listed years the coverage rule hides a few provinces.`,
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
          "Los datos pasan por tres etapas, y cada una puede rastrearse hasta la anterior. La descarga original del INEI se conserva tal como se publicó; luego se transforma en paneles por distrito y año con unidades coherentes y una sola serie de población; y, por último, esos paneles se agregan a las 13 provincias y al departamento, se contrastan con las reglas que se describen abajo y se etiquetan en inglés y en español. Todas las cifras del sitio web provienen de esta última etapa (la exportación solo añade los nombres de los lugares, las marcas de distritos nuevos y los límites del mapa), y todo el código está [en GitHub](" + REPO + ").",
        ],
      },
      {
        id: "sources", title: "De dónde vienen los números",
        body: [
          "Todas las series provienen del **Sistema de Información Regional para la Toma de Decisiones (SIRTOD)** del INEI, en una descarga del 22 de septiembre de 2026. El SIRTOD no produce la mayoría de estos datos: los difunde, distrito por distrito, a partir de series elaboradas por varias entidades públicas. Las principales son:",
          { list: [
            "**INEI**: proyecciones de población, los Censos Nacionales de 2007 y 2017, la pobreza monetaria de la Encuesta Nacional de Hogares (ENAHO) y el mapa de pobreza distrital de 2013, y el Registro Nacional de Municipalidades (RENAMU), una encuesta anual a todas las municipalidades.",
            "**Ministerio de Economía y Finanzas (MEF)**: transferencias de canon y FONCOMUN, ejecución presupuestal de los gobiernos locales del sistema SIAF, e ingresos y gastos municipales de la Dirección Nacional de Contabilidad Pública (DNCP).",
            "**Ministerio de Educación (MINEDU)**: el Censo Escolar (ESCALE) y la Evaluación Censal de Estudiantes de segundo grado (ECE).",
            "**RENIEC** (registro de nacimientos), la Planilla Electrónica del **Ministerio de Trabajo y Promoción del Empleo (MTPE)** (empleo formal privado) y la **Superintendencia de Banca, Seguros y AFP (SBS)** (colocaciones de las cajas municipales).",
          ] },
          "El [catálogo de indicadores](#catalogue), más abajo en esta página, indica la fuente original y los códigos SIRTOD de cada indicador, de modo que cualquier valor pueda volver a consultarse en el SIRTOD.",
        ],
      },
      {
        id: "geography", title: "Distritos, provincias y límites",
        body: [
          "Cusco tiene 13 provincias y, hoy, 116 distritos. Ocho de ellos son recientes, todos en la provincia de La Convención, y aparecen en los datos del SIRTOD desde estos años: Inkawasi y Villa Virgen (2015), Villa Kintiarina (2016), Megantoni (2017; creado por una ley de 2016) y Kumpirushiato, Cielo Punco, Manitea y Union Ashaninka (2021). Un distrito nuevo tiene datos solo desde ese año (la excepción es el mapa de pobreza de 2013, que ya incluye a Inkawasi y Villa Virgen), y los distritos de los que se separó (Echarate, Vilcabamba, Kimbiri y Pichari) abarcan un territorio mayor en los años anteriores. El explorador advierte ambas situaciones cada vez que se selecciona uno de estos distritos.",
          "Salvo cuatro indicadores publicados solo como tasas (electricidad escolar, los dos resultados de la ECE y la pobreza; ver [más abajo](#aggregation)), los valores de provincias y del departamento se construyen a partir de los datos distritales, nunca de una tabla aparte, de modo que al pasar de Cusco a una provincia o a un distrito nunca aparece una contradicción. Como una suma no depende de los límites internos, la creación de distritos nuevos no cambia por sí sola las cifras de provincias o del departamento, siempre que todos los distritos reporten (ver [cobertura](#aggregation)).",
          "Los mapas usan los límites distritales del INEI, edición IDE 2024 (capa `Distritos_INEI_2025_IDE_2024`), obtenidos el 1 de noviembre de 2026 de un servicio de mapas alojado por el PNUD. Todos los años se dibujan sobre estos límites actuales. Las formas se simplifican para la web (con una tolerancia de unos 55 metros, sin desalinear los límites compartidos) y los contornos de las provincias son la unión de sus distritos, así que sirven para mapas pero no para calcular áreas; la capa a resolución completa está en el repositorio.",
        ],
      },
      {
        id: "population", title: "Población y valores por habitante",
        body: [
          "Los valores por habitante (y por cada 1 000 habitantes) se obtienen dividiendo entre las proyecciones de población del INEI. El INEI tiene dos series de proyecciones, una basada en el Censo de 2007 y otra en el de 2017, y no coinciden: pasar de una a otra crearía un salto en todas las series por habitante que nada tiene que ver con el distrito. Por eso Cusco-stats las une con un **empalme hacia atrás** estándar: la serie más reciente, basada en el Censo de 2017, se mantiene exactamente como se publicó, y la serie antigua se reescala para que, prolongada con su propia tasa de crecimiento de 2010–2015, coincida con la nueva en el primer año de esta (2016 para el departamento, 2018 para los distritos). Así se conservan las variaciones anuales de la serie antigua y solo cambia su nivel. Los valores distritales de 2016 y 2017 se interpolan geométricamente y, en cada año, los distritos se escalan para que sumen el total departamental empalmado. Como el departamento y los distritos se enlazan con la serie nueva en años distintos, este escalamiento común añade unos 0,8 puntos porcentuales al crecimiento poblacional de cada distrito tanto en 2016–2017 como en 2017–2018 (unos 1,6 puntos en los dos años), resta unos 0,06 puntos en 2015–2016 y desplaza las tasas de crecimiento hasta 2015 en apenas unos 0,04 puntos al año.",
          "Los distritos que se dividieron requieren un cuidado adicional, porque las proyecciones antiguas se refieren al territorio previo a la división. Por eso cada distrito de origen se empalma junto con los distritos que se separaron de él (Echarate con Megantoni, Vilcabamba con Inkawasi y Villa Virgen, Kimbiri con Villa Kintiarina; la separación de Megantoni de Echarate está documentada, y los demás vínculos se infieren de los cambios de población cuando aparecen los distritos nuevos), de modo que su población antigua corresponda al mismo territorio en 2018. Para estos siete distritos la población de 2015–2017 solo puede repartirse de forma aproximada, así que su población distrital y sus valores por habitante no se muestran en esos años; los valores de provincias y del departamento no se ven afectados.",
          "La descarga ya incluye los primeros conteos del Censo de 2025. Para el conjunto de Cusco están cerca de 8% por debajo de la proyección, una brecha similar a la de 2017, pero en 24 de los 116 distritos el conteo difiere de la proyección en más de 20% (Megantoni: 16 333 censados frente a 7 335 proyectados). Por eso, los valores por habitante recientes de esos distritos deben leerse con cautela hasta que el INEI publique proyecciones basadas en el Censo de 2025.",
        ],
      },
      {
        id: "aggregation", title: "De los distritos a las provincias y a Cusco",
        body: [
          "La forma de construir el valor de una provincia o del departamento depende del tipo de indicador:",
          { list: [
            "**Montos** (soles, personas, trabajadores, equipos): se suman los distritos. Los valores por habitante son la suma de los distritos que reportan dividida entre la población del territorio que cubren (incluidos los distritos nuevos que aún reporta su distrito de origen; ver la regla de cobertura), es decir, el promedio ponderado por población que el lector espera.",
            "**Porcentajes y razones**: siempre son un cociente de sumas. El avance de ejecución del departamento, por ejemplo, es el gasto devengado total entre el Presupuesto Institucional Modificado (PIM) total, no un promedio de 116 tasas distritales, que daría a un distrito de 2 000 habitantes el mismo peso que al distrito de Cusco (unos 120 000 habitantes).",
            "**Indicadores de sí o no** (sí/no): se muestran como el porcentaje de municipalidades que prestan un servicio (serenazgo), en el que cada municipalidad cuenta igual, sea cual sea su tamaño, o como un número de distritos (distritos con colocaciones de alguna caja municipal).",
            "**Indicadores censales**: son cocientes de las sumas de los conteos distritales. Para 2017 esto reproduce las cifras departamentales oficiales del SIRTOD (salvo un error evidente en su total de celulares). Para 2007 no, porque los propios totales provinciales y departamentales de 2007 del SIRTOD son erróneos en varios rubros (ver [rupturas conocidas](#breaks)).",
            "**Indicadores publicados solo como tasas** (electricidad en las escuelas, la ECE y la pobreza): no pueden reconstruirse a partir de los distritos, porque el SIRTOD no publica los conteos que los sustentan. En estos casos, la línea de Cusco es la serie departamental oficial del SIRTOD, los distritos se muestran tal como se publican y no hay nivel provincial. Para la pobreza, la serie oficial es un intervalo para un grupo de departamentos que incluye a Cusco, y el gráfico lo muestra como una banda.",
          ] },
          "**Regla de cobertura.** El valor de una provincia o del departamento se muestra solo si los distritos con datos concentran al menos el **95% de la población** y al menos el **98% del dinero** (o, en los conteos como computadoras o beneficiarios, de la cantidad que se suma) de los distritos que existen ese año (los indicadores de sí o no se evalúan solo por población). La prueba del dinero importa porque la población por sí sola puede pasar por alto un vacío grande: los cuatro distritos creados en 2021 tienen el 1,3% de la población de Cusco, pero entre el 4% y el 5% de su gasto municipal. El tamaño de cada distrito faltante se estima con sus propios valores en los años más cercanos al vacío (el promedio de sus valores a igual distancia antes y después, hasta un máximo de tres años). Los distritos nuevos se consideran cubiertos mientras su territorio todavía lo reporta el distrito del que se separaron: un distrito en su primer año cuyo presupuesto aún reportaba el distrito de origen, y los distritos creados en 2015 o después durante sus tres primeros años. Ambos cuentan como cubiertos en la prueba de población y su población se mantiene en el denominador de los valores por habitante. La prueba del dinero sigue aplicándose a los distritos recientes; un distrito cuyo presupuesto aún reportaba su distrito de origen queda fuera de ella, porque su dinero ya está en la cifra de ese distrito.",
          "**Contraste con los totales oficiales.** Para seis indicadores (alumnos por docente, nacimientos inscritos de forma tardía, trabajadores formales del sector privado, computadoras municipales, volquetes y beneficiarios del Vaso de Leche), la suma de los distritos se compara además con el total departamental propio del SIRTOD, con una tolerancia del 2%. Una discrepancia siempre oculta ese año a nivel departamental y provincial (los distritos siguen visibles). Una coincidencia, en cambio, deja pasar un año solo cuando los distritos sin datos son recientes, creados en 2015 o después y en sus tres primeros años, cuyo territorio todavía se reporta bajo sus distritos de origen.",
          "Cuando un año no supera estas pruebas, los gráficos muestran un vacío en lugar de un valor engañoso, y las notas debajo de cada gráfico listan los años omitidos para Cusco.",
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
          "Cada indicador se muestra solo en los años en que es comparable, y algunos problemas de la fuente se corrigen u ocultan. Los valores fuera de estas ventanas se conservan en la base de datos, marcados como no mostrados; los siete errores de la fuente que se listan abajo se eliminan del archivo armonizado, pero se conservan en los paneles y en la descarga original.",
          { table: [
            ["Indicador", "Años mostrados", "Por qué"],
            ["Canon (total, gasífero, minero, hidroenergético)", "2005–2024", "En 2004, año de arranque, la cobertura es incompleta, y los montos anteriores a la reforma de 2004 no son comparables; el canon de 2025 aún no está en el SIRTOD."],
            ["FONCOMUN", "2009–2025, sin 2016", "La serie distrital empieza en 2009. Los valores distritales de 2016 del SIRTOD aparecen intercambiados entre distritos: su correlación con 2015 y 2017 es de 0,32–0,33, frente a 0,99 o más para cualquier otro par de años consecutivos."],
            ["Ejecución presupuestal (SIAF)", "2008–2025", "En 2007 el SIAF cubría solo 40 de los 108 distritos que existían entonces."],
            ["Cuentas municipales (ingresos, gastos, participación del gasto de capital, dependencia de transferencias)", "2004–2025, sin 2023", "Los datos de 2023 tienen errores en la fuente: en casi todos los distritos, el gasto supera en cerca de 23% al registrado en el SIAF y los ingresos duplican el promedio de 2022 y 2024."],
            ["Nacimientos inscritos de forma tardía", "Cusco y provincias sin 2021–2022", "En esos años la suma distrital de inscripciones tardías queda entre 2% y 7% por debajo del total departamental del SIRTOD."],
            ["Serenazgo", "2007–2024", "Las respuestas de 2004–2005 parecen corresponder a otra pregunta (incluso Cusco figura con \"no\"), y 2006 no tiene datos."],
            ["Censo de 2007 (viviendas y hogares: agua, desagüe, electricidad, pisos, combustible para cocinar, internet, celular)", "Construido desde los distritos", "Los propios totales provinciales y departamentales de 2007 del SIRTOD no coinciden con la suma de sus conteos distritales. A nivel departamental, las viviendas con agua por red pública y con electricidad quedan 14% por debajo de la suma distrital, internet 27% y celular 17%, y las viviendas contadas por electricidad y los hogares contados por combustible quedan 9% por debajo. Los totales provinciales fallan en ambos sentidos, sobre todo en Cusco, Paruro, Acomayo y La Convención, y en internet y celular en casi todas las provincias. Con los totales de viviendas del SIRTOD, las provincias de Cusco y Paruro tendrían 5,8 y 6,4 personas por vivienda, frente a 3,7–4,3 en todas las provincias con los conteos distritales. Se toman como correctos los conteos distritales, así que los valores de Cusco de 2007 difieren de los que implican los totales departamentales del SIRTOD hasta en 7 puntos (pisos de tierra: 66,5% frente a 73,2%)."],
            ["Censo de 2017 (hogares: internet, celular, combustible para cocinar)", "Construido desde los distritos", "En 2017 un hogar podía declarar varios combustibles para cocinar, así que las categorías de combustible suman cerca de 15% más que el número de hogares. Por eso, las proporciones de hogares dividen entre el total de hogares del propio SIRTOD (código 516818), y la cifra de 2017 sobre cocina cuenta cualquier uso de leña o bosta, no el combustible principal como en 2007: es una cota superior para el concepto de 2007, y ambos censos no son estrictamente comparables en cuanto a la cocina."],
            ["Computadoras de las municipalidades", "Cusco y provincias sin 2015", "Se omite el valor erróneo de Kimbiri en 2015 (ver abajo), pero el total departamental del SIRTOD todavía lo incluye, así que la suma distrital corregida ya no coincide con el total oficial."],
            ["Volquetes operativos", "Cusco y provincias sin 2004 (no hay datos de 2005)", "Se omiten los valores de 2004 de Cusco y Paucartambo (ver abajo), pero el total departamental del SIRTOD todavía los incluye, así que la suma distrital corregida ya no coincide con el total oficial."],
          ] },
          "Además, siete valores distritales aislados se dejan en blanco porque difieren por un factor de cinco o más de los valores de los años vecinos: beneficiarios del Vaso de Leche en 2014 en los distritos de Cusco, Marcapata, Llusco y Omacha (el distrito de Cusco figura con 32, frente a 3 785 y 3 411 en los años de alrededor); volquetes operativos en 2004 en Cusco y Paucartambo; y computadoras municipales en 2015 en Kimbiri (1 631, frente a 190 y 162).",
          "También hay dos definiciones que merecen cuidado. Los ingresos municipales totales incluyen el **financiamiento**, es decir, saldos de balance de años anteriores y endeudamiento, de modo que pueden superar lo que la municipalidad recaudó en el año; por eso la dependencia de transferencias divide los ingresos por transferencias entre los ingresos totales menos el financiamiento. Y el RENAMU parece registrar el equipamiento a inicios del año siguiente (un supuesto basado en su calendario de encuesta), así que las computadoras y los volquetes se fechan en el año anterior a la encuesta. El año 2026 se deja fuera por ahora porque está incompleto.",
        ],
      },
      { id: "catalogue", title: "Catálogo de indicadores", body: [] },
      {
        id: "reuse", title: "Descargas, código y cómo citar",
        body: [
          "Cada vista del [explorador](explorer) puede compartirse como un enlace, que conserva el indicador, la medida, los lugares y el año, y descargarse como un archivo CSV con una fila por lugar y año para los lugares del gráfico, con los porcentajes y las razones a cuatro decimales, sin redondear al único decimal que se muestra en pantalla. Lee la columna code como texto: los códigos UBIGEO conservan el cero inicial (08, 0809, 080902).",
          "La base de datos armonizada completa está en el [repositorio de GitHub](" + REPO + "), en la carpeta `harmonized`: `cusco_stats_long.csv` tiene una fila por nivel, lugar, año, indicador y medida, con el número de distritos que reportan y las proporciones de cobertura que usan las reglas anteriores, y `cusco_stats_dictionary.csv` tiene las etiquetas, unidades, descripciones, advertencias y fuentes en inglés y en español. Los paneles por distrito y año de los que se construye están en la carpeta `panels`, también en formato Stata.",
          "Si usas Cusco-stats, por favor cítalo así:",
          { cite: "Villa Paro, Paola (2026). *Cusco-stats: los 116 distritos de Cusco, Perú, en datos.* https://pvillaparo.github.io/cusco-data/ (datos: INEI SIRTOD, descarga del 22 de septiembre de 2026)." },
          "**Licencia.** Los datos armonizados, los paneles por distrito y año, los datos del sitio, la documentación y los textos de estas páginas se publican bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es) (ver [LICENSE-DATA.md](" + REPO + "/blob/main/LICENSE-DATA.md)), que permite reutilizarlos con cualquier fin siempre que se cite la fuente; el código se publica bajo la [licencia MIT](" + REPO + "/blob/main/LICENSE). Las estadísticas de origen pertenecen al INEI y a las demás entidades que las producen, y siguen sujetas a sus condiciones.",
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
      intro: (n) => `Los ${n} indicadores que siguen se generan a partir del mismo diccionario que usa el explorador, así que siempre coinciden con los datos del sitio. Para cada uno: qué mide, las medidas y unidades disponibles (y si puede mapearse), los años con datos en cada nivel, cómo se calculan los valores de Cusco y de las provincias, la fuente con sus códigos SIRTOD y qué leer con cuidado. Un año figura para provincias o distritos cuando al menos uno de ellos tiene datos ese año, de modo que en algunos de esos años la regla de cobertura oculta algunas provincias.`,
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
