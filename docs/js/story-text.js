// "Cusco in six charts": story text in English and Spanish (from website/story_draft.md).
// Figures were computed from docs/data and should be rechecked whenever the data are rebuilt.

export const STORY = {
  en: {
    kicker: "Story",
    title: "Cusco in six charts",
    intro: "Cusco is best known abroad for Machupicchu, but over the last two decades its districts have also lived through one of Peru's largest natural-resource windfalls. These six charts follow that money from the gas and copper fields into municipal budgets, and then look at what changed around it in schools, households and the reach of the state. They describe; they do not, on their own, tell us what caused what.",
    note: "Money in constant 2024 soles (Cusco city CPI) unless stated otherwise.",
    explore: "Explore",
    toExplorer: "Explore any of these indicators, for any province or district, in the explorer below.",
    goExplorer: "Go to the explorer",
    steps: [
      {
        title: "A windfall that comes and goes",
        chart: "Canon per person, Cusco, 2010–2024, by type (constant 2024 soles)",
        text: "In 2012 Cusco's municipalities received about S/ 2,530 of canon per resident, almost twice the S/ 1,389 of 2010, and close to nine soles in ten came from the Camisea gas fields. The windfall then shrank by two thirds, to S/ 859 per person in 2020, before rebounding to S/ 2,444 in 2022. For local governments this is the defining feature of canon: it is large, but it follows gas and metal prices rather than local needs.",
        layers: { gas: "Gas", mining: "Mining", other: "Other canon" },
      },
      {
        title: "Where the money lands",
        chart: "Canon per person by district, average 2020–2024 (constant 2024 soles), and the ten largest recipients",
        text: "The money is very unevenly spread. All ten districts with the most canon per person are in La Convención, the gas province, led by Megantoni, home of Camisea, with about S/ 44,000 per resident a year. The median district receives about S/ 1,300. Mining canon tells a different, smaller story, concentrated in the high-altitude districts of Espinar such as Ocoruro, Condoroma and Suyckutambo.",
        median: (v) => `District median: ${v}`,
        mapHint: "Click a district to open it in the explorer.",
      },
      {
        title: "Budgets that grow faster than spending",
        chart: "Modified budget (PIM) and accrued expenditure per person, 2010–2025 (constant 2024 soles), and the budget execution rate (%)",
        text: "When canon booms, budgets jump: the modified budget rose from S/ 2,661 per person in 2010 to S/ 4,727 in 2013. Spending follows, but with a lag, so the share of the budget actually spent tends to fall in boom years (64% in 2011, 65% in 2023) and recover afterwards (88% in 2024). About seven soles in ten of municipal spending go to capital projects, a share that dipped mainly during the 2020 pandemic (56%).",
        pim: "Modified budget (PIM)", accrued: "Accrued expenditure", exec: "Budget execution rate (%)",
      },
      {
        title: "Schools: more teachers, better results",
        chart: "Pupils per teacher (2008–2025), public school premises on the electricity grid (2001–2022), and 2nd-grade pupils at the satisfactory level (2007–2016)",
        text: "The number of pupils per teacher in public schools fell from 24.8 to 13.8, partly because there are more teachers and partly because there are fewer children. School premises connected to the grid went from 37% to 89%. Among second graders who sat the national test, the share reading at the expected level rose from 11% in 2007 to 49% in 2015, and in mathematics from 5% to 37% by 2016. The test does not cover bilingual schools, so these figures describe mainly Spanish-instruction schools.",
        ptr: "Pupils per teacher", elec: "School premises on the grid (%)", ece: "2nd grade, satisfactory level (%)", read: "Reading", math: "Mathematics",
      },
      {
        title: "Households between two censuses, and poverty",
        chart: "Cusco, 2007 and 2017 censuses (% of dwellings or households), and monetary poverty 2007–2025 with its confidence interval",
        text: "Between the two censuses the share of dwellings with piped water inside rose from 61% to 80%, sewerage from 31% to 47%, and electricity from 64% to 82%. Cooking mainly with firewood or dung fell from 62% to 27% of households, while internet at home, still rare, rose from 2% to 15%. Monetary poverty in the group of departments that includes Cusco fell from about 57% in 2007 to about 24% in 2019, jumped to 33% in the pandemic year and was back near 21% by 2025.",
        rows: { census_water_in: "Piped water inside", census_sewer_in: "Sewer connection inside", census_electric: "Grid electricity", census_cook_biomass: "Cooks mainly with firewood or dung", census_internet: "Internet at home" },
        poverty: "Monetary poverty (%), group of departments including Cusco", band: "Confidence interval",
      },
      {
        title: "The reach of the state",
        chart: "Births registered late, municipalities providing serenazgo, districts where a municipal savings bank lends, and formal private jobs per 1,000 people",
        text: "In 2007 about a third of births were registered late; by 2024 fewer than 3% were. The share of municipalities running a serenazgo (local security) service rose from 32% to 94%, and the number of districts where a caja municipal lends grew from 6 to 26. Formal private jobs rose from about 63,000 in 2015 to 90,000 in 2025, still only 64 per 1,000 residents in a region where most work is informal.",
        late: "Births registered late (%)", seren: "Municipalities with serenazgo (%)", cmac: "Districts where a caja municipal lends", jobs: "Formal private jobs per 1,000 people",
      },
    ],
  },
  es: {
    kicker: "Historia",
    title: "Cusco en seis gráficos",
    intro: "Cusco es conocido en el mundo por Machupicchu, pero en las dos últimas décadas sus distritos también han vivido una de las mayores bonanzas de recursos naturales del Perú. Estos seis gráficos siguen ese dinero desde los yacimientos de gas y cobre hasta los presupuestos municipales, y luego miran qué cambió a su alrededor en las escuelas, los hogares y el alcance del Estado. Describen; por sí solos no dicen qué causó qué.",
    note: "Montos en soles constantes de 2024 (IPC de la ciudad de Cusco), salvo que se indique otra cosa.",
    explore: "Explorar",
    toExplorer: "Explora cualquiera de estos indicadores, para cualquier provincia o distrito, en el explorador de abajo.",
    goExplorer: "Ir al explorador",
    steps: [
      {
        title: "Una bonanza que va y viene",
        chart: "Canon por habitante, Cusco, 2010–2024, por tipo (soles constantes de 2024)",
        text: "En 2012 las municipalidades de Cusco recibieron unos S/ 2 530 de canon por habitante, casi el doble de los S/ 1 389 de 2010, y cerca de nueve de cada diez soles venían de los yacimientos de gas de Camisea. Luego la bonanza se redujo en dos tercios, hasta S/ 859 por persona en 2020, antes de recuperarse a S/ 2 444 en 2022. Para los gobiernos locales este es el rasgo central del canon: es grande, pero sigue los precios del gas y de los metales, no las necesidades locales.",
        layers: { gas: "Gas", mining: "Minería", other: "Otro canon" },
      },
      {
        title: "Dónde cae el dinero",
        chart: "Canon por habitante por distrito, promedio 2020–2024 (soles constantes de 2024), y los diez mayores receptores",
        text: "El dinero está muy desigualmente repartido. Los diez distritos con más canon por habitante están en La Convención, la provincia del gas, encabezados por Megantoni, sede de Camisea, con unos S/ 44 000 por habitante al año. El distrito mediano recibe unos S/ 1 300. El canon minero cuenta una historia distinta y más pequeña, concentrada en los distritos altoandinos de Espinar como Ocoruro, Condoroma y Suyckutambo.",
        median: (v) => `Mediana distrital: ${v}`,
        mapHint: "Haz clic en un distrito para abrirlo en el explorador.",
      },
      {
        title: "Presupuestos que crecen más rápido que el gasto",
        chart: "Presupuesto modificado (PIM) y gasto devengado por habitante, 2010–2025 (soles constantes de 2024), y el avance de ejecución presupuestal (%)",
        text: "Cuando el canon crece, los presupuestos saltan: el PIM pasó de S/ 2 661 por habitante en 2010 a S/ 4 727 en 2013. El gasto lo sigue, pero con rezago, de modo que la parte del presupuesto que realmente se ejecuta tiende a caer en los años de bonanza (64% en 2011, 65% en 2023) y a recuperarse después (88% en 2024). Alrededor de siete de cada diez soles del gasto municipal se destinan a proyectos de inversión, una proporción que bajó sobre todo durante la pandemia de 2020 (56%).",
        pim: "Presupuesto modificado (PIM)", accrued: "Gasto devengado", exec: "Avance de ejecución presupuestal (%)",
      },
      {
        title: "Escuelas: más docentes, mejores resultados",
        chart: "Alumnos por docente (2008–2025), locales escolares públicos conectados a la red eléctrica (2001–2022) y estudiantes de 2.º grado con nivel satisfactorio (2007–2016)",
        text: "El número de alumnos por docente en las escuelas públicas bajó de 24,8 a 13,8, en parte porque hay más docentes y en parte porque hay menos niños. Los locales escolares conectados a la red eléctrica pasaron de 37% a 89%. Entre los estudiantes de segundo grado evaluados, la proporción con nivel satisfactorio en lectura subió de 11% en 2007 a 49% en 2015, y en matemática de 5% a 37% en 2016. La prueba no cubre las escuelas bilingües, por lo que estas cifras describen sobre todo escuelas de enseñanza en castellano.",
        ptr: "Alumnos por docente", elec: "Locales escolares conectados a la red (%)", ece: "2.º grado, nivel satisfactorio (%)", read: "Lectura", math: "Matemática",
      },
      {
        title: "Los hogares entre dos censos, y la pobreza",
        chart: "Cusco, censos de 2007 y 2017 (% de viviendas u hogares), y pobreza monetaria 2007–2025 con su intervalo de confianza",
        text: "Entre ambos censos, las viviendas con agua de red pública dentro de la vivienda pasaron de 61% a 80%, las conectadas al desagüe de 31% a 47% y las con electricidad de 64% a 82%. Los hogares que cocinan principalmente con leña o bosta bajaron de 62% a 27%, mientras que el internet en casa, todavía escaso, subió de 2% a 15%. La pobreza monetaria en el grupo de departamentos que incluye a Cusco bajó de alrededor de 57% en 2007 a cerca de 24% en 2019, saltó a 33% en el año de la pandemia y volvió a cerca de 21% en 2025.",
        rows: { census_water_in: "Agua dentro de la vivienda", census_sewer_in: "Desagüe dentro de la vivienda", census_electric: "Electricidad de red pública", census_cook_biomass: "Cocina principalmente con leña o bosta", census_internet: "Internet en casa" },
        poverty: "Pobreza monetaria (%), grupo de departamentos que incluye a Cusco", band: "Intervalo de confianza",
      },
      {
        title: "El alcance del Estado",
        chart: "Nacimientos inscritos de forma tardía, municipalidades con serenazgo, distritos donde presta una caja municipal y empleo formal privado por 1 000 habitantes",
        text: "En 2007 alrededor de un tercio de los nacimientos se inscribía de forma tardía; en 2024, menos de 3%. La proporción de municipalidades con servicio de serenazgo subió de 32% a 94%, y los distritos donde presta una caja municipal pasaron de 6 a 26. El empleo formal privado creció de unos 63 000 trabajadores en 2015 a 90 000 en 2025, todavía solo 64 por cada 1 000 habitantes en una región donde la mayor parte del trabajo es informal.",
        late: "Nacimientos inscritos tarde (%)", seren: "Municipalidades con serenazgo (%)", cmac: "Distritos donde presta una caja municipal", jobs: "Empleo formal privado por 1 000 habitantes",
      },
    ],
  },
};

// Explorer views opened by each step's "Explore" buttons: [variable, base measure, constant soles?, places]
export const STORY_LINKS = [
  [["canon_total", "per_capita", true, []], ["canon_gas", "per_capita", true, ["0809"]], ["canon_mining", "per_capita", true, ["0808", "0807"]]],
  [["canon_total", "per_capita", true, ["080914", "0809"]], ["canon_mining", "per_capita", true, ["080804", "080802"]]],
  [["siaf_accrued", "per_capita", true, []], ["siaf_exec_rate", "pct", true, []], ["capital_share", "pct", true, []]],
  [["edu_ptr_pub", "ratio", true, []], ["sch_electric", "pct", true, []], ["ece_read", "pct", true, []]],
  [["census_water_in", "pct", true, []], ["poverty", "pct", true, []]],
  [["late_birth_share", "pct", true, []], ["sec_serenazgo", "pct", true, []], ["fin_cmac_present", "count", true, []], ["lab_private_workers", "per_1000", true, []]],
];
