"""
Build the display-ready ("harmonized") Cusco-stats dataset.

Input : panels/canon_development_district_year.csv (canon + development + baselines;
                                                   built by panels/merge_canon_development.py)
        SIRTOD/02_SIRTOD_Cusco_anual_departamento.xlsx (official department rates)
        harmonized/inputs/cpi_annual.csv          (optional; built by build_cpi.py)
Output: harmonized/cusco_stats_long.csv           one row per level x place x year x variable x measure
        harmonized/cusco_stats_dictionary.csv     bilingual (ES/EN) labels, units, sources, caveats

Run from the repository root:

    python harmonized/build_harmonized.py

Harmonization rules (see harmonized/README.md):
  * Levels: district, province (13) and department. Province and department
    values are built from the districts, so the three levels always agree
    (except official rates and poverty, whose department line is SIRTOD's
    official series and which have no province level).
  * Measures: for amounts, the total and the per-capita value (total divided by
    the spliced population of the districts that report); for ratios, the ratio
    of sums (e.g. accrued / PIM across districts), never an average of ratios.
  * Coverage: an aggregate is displayed only if the reporting districts hold at
    least 95% of the population AND at least 98% of the money of the districts
    that exist that year. A missing district is sized by the mean of its values
    k years before and after, for the smallest k <= 3 with any value (otherwise
    zero). A district in its first year whose parent still reports, and young
    districts (created 2015 or later, first 3 years), count as covered in the
    population test and stay in per-capita denominators. Where SIRTOD has an
    official department total, the district sum must match it within 2%; a
    mismatch hides the aggregate, and a match lets a year through only when the
    missing districts are young ones.
  * Years: each variable has a display window (canon from 2005, SIAF from 2008,
    municipal accounts from 2004 without the broken year 2023, FONCOMUN without
    the scrambled year 2016); 2026 is dropped for
    now (partial year). Rows outside the window are kept with display = 0.
  * Indicator kinds: sums (money or counts), ratios of sums, yes/no municipal
    services (count or share of reporting municipalities), official rates
    (department line from SIRTOD's department series because the district
    percentages come without denominators; districts as published; no
    province level), the official poverty interval (same treatment) and census
    snapshots (2007, 2017; province and department are ratios of the sums of
    the district counts).
  * Money is in current soles, plus constant-soles measures (total_real,
    per_capita_real) in soles of REAL_BASE_YEAR when inputs/cpi_annual.csv exists
    (built by build_cpi.py from the Cusco city CPI; available from 2010 only).
"""

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent / "panels" / "canon_development_district_year.csv"
DEPT_FILE = HERE.parent / "SIRTOD" / "02_SIRTOD_Cusco_anual_departamento.xlsx"
CPI_FILE = HERE / "inputs" / "cpi_annual.csv"
OUT_LONG = HERE / "cusco_stats_long.csv"
OUT_DICT = HERE / "cusco_stats_dictionary.csv"

LAST_YEAR = 2025          # 2026 is partial; revisit at next update
COVERAGE_MIN = 0.95       # population share of reporting districts
REAL_BASE_YEAR = 2024

CAT = {
    "population": ("Población", "Population"),
    "canon": ("Canon", "Canon transfers"),
    "transfers": ("Transferencias", "Transfers"),
    "budget": ("Presupuesto municipal (MEF-SIAF)", "Municipal budget (MEF-SIAF)"),
    "finance": ("Finanzas municipales (MEF, contabilidad pública)", "Municipal finances (MEF public accounts)"),
    "education": ("Educación", "Education"),
    "registration": ("Registro civil", "Civil registration"),
    "economy": ("Empleo y finanzas", "Jobs and finance"),
    "municipal": ("Capacidad y servicios municipales", "Municipal capacity and services"),
    "social": ("Programas sociales", "Social programmes"),
    "census": ("Censos 2007 y 2017", "2007 and 2017 censuses"),
    "poverty": ("Pobreza", "Poverty"),
}
MONEY_CATS = {"canon", "transfers", "budget", "finance"}

SRC = {
    "pop": ("INEI, estimaciones y proyecciones de población (vía SIRTOD)",
            "INEI population estimates and projections (via SIRTOD)"),
    "canon": ("MEF, transferencias de canon a municipalidades (vía INEI SIRTOD)",
              "MEF canon transfers to municipalities (via INEI SIRTOD)"),
    "foncomun": ("MEF, Dirección Nacional de Contabilidad Pública: FONCOMUN transferido (vía INEI SIRTOD)",
                 "MEF Public Accounting Directorate: FONCOMUN transfers (via INEI SIRTOD)"),
    "canon_siaf": ("MEF: transferencias de canon y ejecución presupuestal SIAF (vía INEI SIRTOD)",
                   "MEF canon transfers and SIAF budget execution (via INEI SIRTOD)"),
    "siaf": ("MEF, Consulta Amigable (SIAF): presupuesto y ejecución de los gobiernos locales (vía INEI SIRTOD)",
             "MEF, Consulta Amigable (SIAF): budgets and execution of local governments (via INEI SIRTOD)"),
    "munfin": ("MEF, Dirección Nacional de Contabilidad Pública: finanzas municipales (vía INEI SIRTOD)",
               "MEF Public Accounting Directorate: municipal finances (via INEI SIRTOD)"),
    "escale": ("MINEDU, Unidad de Estadística Educativa: Censo Escolar, ESCALE (vía INEI SIRTOD)",
               "MINEDU, Educational Statistics Unit: School Census, ESCALE (via INEI SIRTOD)"),
    "umc": ("MINEDU, Oficina de Medición de la Calidad de los Aprendizajes (UMC): Evaluación Censal de Estudiantes, ECE (vía INEI SIRTOD)",
            "MINEDU, Learning Quality Measurement Office (UMC): national census test of pupils, ECE (via INEI SIRTOD)"),
    "reniec": ("RENIEC, registro de nacimientos (vía INEI SIRTOD)", "RENIEC birth registration (via INEI SIRTOD)"),
    "mtpe": ("MTPE, Planilla Electrónica (vía INEI SIRTOD)", "MTPE electronic payroll (via INEI SIRTOD)"),
    "sbs": ("SBS, colocaciones de cajas municipales (vía INEI SIRTOD)", "SBS municipal savings banks' lending (via INEI SIRTOD)"),
    "renamu": ("INEI, Registro Nacional de Municipalidades - RENAMU (vía SIRTOD)",
               "INEI National Registry of Municipalities - RENAMU (via SIRTOD)"),
    "census": ("INEI, Censos Nacionales 2007 y 2017 (vía SIRTOD)", "INEI 2007 and 2017 National Censuses (via SIRTOD)"),
    "povmap": ("INEI: Encuesta Nacional de Hogares (ENAHO), intervalos por grupos de departamentos, para Cusco; "
               "Mapa de pobreza provincial y distrital 2013, para los distritos (vía SIRTOD)",
               "INEI: National Household Survey (ENAHO), intervals for groups of departments, for Cusco; "
               "2013 provincial and district poverty map, for districts (via SIRTOD)"),
}

CAVEAT_CANON = ("Desde 2005: 2004 es un año de arranque con cobertura incompleta, y antes de la reforma de 2004 "
                "los montos no son comparables. El canon de 2025 aún no está disponible en SIRTOD.",
                "From 2005: 2004 is a start-up year with incomplete coverage, and before the 2004 reform amounts "
                "are not comparable. 2025 canon is not yet available in SIRTOD.")
CAVEAT_SIAF = ("Desde 2008: en 2007 SIAF cubre solo 40 de 108 distritos.",
               "From 2008: in 2007 SIAF covers only 40 of 108 districts.")
CAVEAT_MUNFIN = ("Se excluye 2023: ese año los datos distritales son inconsistentes en casi todos los distritos "
                 "(gasto ~23% sobre el devengado de SIAF; ingresos ~2 veces el promedio de 2022 y 2024).",
                 "2023 is excluded: that year the district data are inconsistent in almost every district "
                 "(spending ~23% above SIAF accrued spending; revenue about twice the average of 2022 and 2024).")
MUNFIN_BAD_YEARS = [2023]

# id, kind, source column(s), category, display window, per-capita?, map?, source, codes, labels, description, caveat
VARS = [
    dict(id="pop", kind="sum", col="pop_spliced", cat="population", years=(2001, LAST_YEAR),
         pc=False, map=False, src="pop", codes="262234",
         label=("Población", "Population"),
         desc=("Población proyectada por INEI, con las proyecciones basadas en los censos de 2007 y 2017 empalmadas en una sola serie.",
               "INEI projected population, with the projections based on the 2007 and 2017 censuses spliced into one series."),
         caveat=("Antes de 2016 (departamento) y 2018 (distritos) la serie antigua está reescalada al nivel de la nueva; "
                 "2016-2017 interpolado a nivel distrital. Para los siete distritos de las familias de Echarate, Vilcabamba y Kimbiri "
                 "(con Megantoni, Inkawasi, Villa Virgen y Villa Kintiarina) la población y los valores por habitante no se muestran en "
                 "2015-2017, porque la población de esos años solo puede repartirse de forma aproximada entre ellos.",
                 "Before 2016 (department) and 2018 (districts) the old series is rescaled to the level of the new one; "
                 "2016-2017 interpolated at district level. For the seven districts of the Echarate, Vilcabamba and Kimbiri families "
                 "(with Megantoni, Inkawasi, Villa Virgen and Villa Kintiarina) population and per-person values are not shown in "
                 "2015-2017, because the population of those years can only be divided between them approximately.")),
    dict(id="canon_total", kind="sum", col="canon_total", cat="canon", years=(2005, 2024),
         pc=True, map=True, src="canon", codes="407245; 414080",
         label=("Canon transferido a municipalidades", "Canon transferred to municipalities"),
         desc=("Suma de todos los tipos de canon transferidos a la municipalidad: minero, gasífero, hidroenergético, forestal, petrolero, pesquero y sobrecanon petrolero. "
               "El canon es la participación de los gobiernos locales y regionales en los ingresos y rentas que el Estado obtiene por la explotación de recursos naturales. "
               "En 2021-2022, los datos de los cuatro distritos creados en 2021 se completan con el código 414080.",
               "Sum of all canon types transferred to the municipality: mining, gas, hydropower, forestry, oil, fishing and the oil surcharge (sobrecanon petrolero). "
               "Canon is the share of the revenue the State obtains from the exploitation of natural resources that is passed on to local and regional governments. "
               "In 2021-2022, the data of the four districts created in 2021 are filled in from code 414080."),
         caveat=CAVEAT_CANON),
    dict(id="canon_gas", kind="sum", col="canon_gas", cat="canon", years=(2005, 2024),
         pc=True, map=True, src="canon", codes="407247",
         label=("Canon gasífero", "Gas canon"),
         desc=("Canon gasífero (Camisea) transferido a la municipalidad.",
               "Gas canon (Camisea) transferred to the municipality."),
         caveat=CAVEAT_CANON),
    dict(id="canon_mining", kind="sum", col="canon_mining", cat="canon", years=(2005, 2024),
         pc=True, map=True, src="canon", codes="407249",
         label=("Canon minero", "Mining canon"),
         desc=("Canon minero transferido a la municipalidad.",
               "Mining canon transferred to the municipality."),
         caveat=CAVEAT_CANON),
    dict(id="canon_hydro", kind="sum", col="canon_hydro", cat="canon", years=(2005, 2024),
         pc=True, map=False, src="canon", codes="407248",
         label=("Canon hidroenergético", "Hydropower canon"),
         desc=("Canon hidroenergético transferido a la municipalidad.",
               "Hydropower canon transferred to the municipality."),
         caveat=CAVEAT_CANON),
    dict(id="foncomun", kind="sum", col="foncomun", cat="transfers", years=(2009, LAST_YEAR),
         pc=True, map=True, src="foncomun", codes="414062", exclude=[2016],
         label=("Fondo de Compensación Municipal (FONCOMUN)", "Municipal Compensation Fund (FONCOMUN)"),
         desc=("Transferencia del FONCOMUN a la municipalidad. El FONCOMUN es un fondo establecido en la Constitución que redistribuye recursos "
               "(principalmente el Impuesto de Promoción Municipal) entre todas las municipalidades del país.",
               "FONCOMUN transfer to the municipality. FONCOMUN is a constitutional fund that redistributes resources "
               "(mainly the Municipal Promotion Tax) across all municipalities in the country."),
         caveat=("Se excluye 2016: en SIRTOD los valores distritales de ese año están desordenados entre distritos. "
                 "SIRTOD lo rotula en miles de soles, pero los valores ya están en soles.",
                 "2016 is excluded: in SIRTOD that year's district values are scrambled across districts. "
                 "SIRTOD labels it in thousands of soles, but the values are already in soles.")),
    dict(id="siaf_pia", kind="sum", col="siaf_pia", cat="budget", years=(2008, LAST_YEAR),
         pc=True, map=False, src="siaf", codes="516869",
         label=("Presupuesto Institucional de Apertura (PIA)", "Opening budget (PIA)"),
         desc=("Presupuesto aprobado al inicio del año.", "Budget approved at the start of the year."),
         caveat=CAVEAT_SIAF),
    dict(id="siaf_pim", kind="sum", col="siaf_pim", cat="budget", years=(2008, LAST_YEAR),
         pc=True, map=False, src="siaf", codes="516870",
         label=("Presupuesto Institucional Modificado (PIM)", "Modified budget (PIM)"),
         desc=("Presupuesto vigente tras las modificaciones del año (incluye saldos y transferencias recibidas).",
               "Budget in force after the year's modifications (includes carry-overs and transfers received)."),
         caveat=CAVEAT_SIAF),
    dict(id="siaf_accrued", kind="sum", col="siaf_accrued", cat="budget", years=(2008, LAST_YEAR),
         pc=True, map=True, src="siaf", codes="516872",
         label=("Gasto ejecutado (devengado)", "Accrued expenditure (devengado)"),
         desc=("Gasto devengado: obligaciones de pago reconocidas en el año.",
               "Accrued expenditure: payment obligations recognised during the year."),
         caveat=CAVEAT_SIAF),
    dict(id="siaf_exec_rate", kind="ratio", num="siaf_accrued", den="siaf_pim", cat="budget",
         years=(2008, LAST_YEAR), pc=False, map=True, src="siaf", codes="516872 / 516870",
         label=("Avance de ejecución presupuestal", "Budget execution rate"),
         desc=("Gasto devengado como porcentaje del PIM. En agregados es devengado total / PIM total.",
               "Accrued expenditure as a percentage of the modified budget (PIM). Aggregates are total accrued / total PIM."),
         caveat=CAVEAT_SIAF),
    dict(id="munfin_rev_total", kind="sum", col="munfin_rev_total", cat="finance", years=(2004, LAST_YEAR),
         pc=True, map=False, src="munfin", codes="122042", exclude=MUNFIN_BAD_YEARS,
         label=("Ingresos totales (incluye saldos de balance y endeudamiento)", "Total revenue (incl. carry-over balances and borrowing)"),
         desc=("Ingreso total registrado por la municipalidad (SIRTOD: ingreso total recaudado): ingresos corrientes, de capital, transferencias y financiamiento "
               "(este último incluye los saldos de balance de años anteriores y el endeudamiento).",
               "Total revenue recorded by the municipality: current revenue, capital revenue, transfers and financing "
               "(the latter includes balances carried over from previous years and borrowing)."),
         caveat=CAVEAT_MUNFIN),
    dict(id="munfin_rev_transfers", kind="sum", col="munfin_rev_transfers", cat="finance", years=(2004, LAST_YEAR),
         pc=True, map=False, src="munfin", codes="122046", exclude=MUNFIN_BAD_YEARS,
         label=("Ingresos por transferencias", "Transfer revenue"),
         desc=("Ingresos de la municipalidad provenientes de transferencias (canon, FONCOMUN, otros).",
               "Municipal revenue from transfers (canon, FONCOMUN, others)."),
         caveat=CAVEAT_MUNFIN),
    dict(id="munfin_exp_current", kind="sum", col="munfin_exp_current", cat="finance", years=(2004, LAST_YEAR),
         pc=True, map=False, src="munfin", codes="122048", exclude=MUNFIN_BAD_YEARS,
         label=("Gasto corriente", "Current expenditure"),
         desc=("Gasto corriente ejecutado: personal, bienes y servicios y otros gastos corrientes.",
               "Current expenditure executed: staff, goods and services, and other current expenditure."),
         caveat=CAVEAT_MUNFIN),
    dict(id="munfin_exp_capital", kind="sum", col="munfin_exp_capital", cat="finance", years=(2004, LAST_YEAR),
         pc=True, map=True, src="munfin", codes="122049", exclude=MUNFIN_BAD_YEARS,
         label=("Gasto de capital", "Capital expenditure"),
         desc=("Gasto de capital ejecutado, principalmente inversión pública (obras).",
               "Capital expenditure executed, mainly public investment (works)."),
         caveat=CAVEAT_MUNFIN),
    dict(id="capital_share", kind="ratio", num="munfin_exp_capital", den="munfin_exp_total", cat="finance",
         years=(2004, LAST_YEAR), pc=False, map=True, src="munfin", codes="122049 / 122047", exclude=MUNFIN_BAD_YEARS,
         label=("Participación del gasto de capital", "Capital share of expenditure"),
         desc=("Gasto de capital como porcentaje del gasto total ejecutado.",
               "Capital expenditure as a percentage of total expenditure executed."),
         caveat=CAVEAT_MUNFIN),
    dict(id="transfers_share", kind="ratio", num="munfin_rev_transfers", den="munfin_rev_nonfin", cat="finance",
         years=(2004, LAST_YEAR), pc=False, map=True, src="munfin", codes="122046 / (122042 - 122045)", exclude=MUNFIN_BAD_YEARS,
         label=("Dependencia de transferencias", "Dependence on transfers"),
         desc=("Ingresos por transferencias como porcentaje de los ingresos del año sin financiamiento "
               "(ingresos totales menos saldos de balance y endeudamiento).",
               "Transfer revenue as a percentage of the year's revenue excluding financing "
               "(total revenue minus carry-over balances and borrowing)."),
         caveat=CAVEAT_MUNFIN),
    dict(id="canon_dependence", kind="ratio", num="canon_total", den="siaf_accrued", cat="canon",
         years=(2008, 2024), pc=False, map=True, src="canon_siaf", codes="407245 / 516872",
         label=("Canon como porcentaje del gasto", "Canon as a share of expenditure"),
         desc=("Canon transferido en el año como porcentaje del gasto devengado del mismo año.",
               "Canon transferred in the year as a percentage of accrued expenditure in the same year."),
         caveat=("Puede superar 100%: el canon de un año suele gastarse en años posteriores.",
                 "Can exceed 100%: canon received in one year is often spent in later years.")),

    # ---- Development indicators (panels/extract_development_indicators.py) ----
    dict(id="edu_ptr_pub", kind="ratio", num="edu_enrol_ebr_pub", den="edu_teach_ebr_pub", scale=1,
         official_check={"num": "413856", "den": "417647"},
         measures=["ratio"], cat="education", years=(2008, LAST_YEAR), map=True, src="escale", codes="413856 / 417647",
         unit=("Alumnos por docente", "Pupils per teacher"),
         label=("Alumnos por docente en la educación básica regular pública", "Pupils per teacher in public regular basic education"),
         desc=("Matrícula pública en educación básica regular (inicial, primaria y secundaria) dividida entre el número de docentes "
               "(incluye personal directivo). En agregados: matrícula total / docentes totales.",
               "Public enrolment in regular basic education (pre-school, primary and secondary) divided by the number of teachers "
               "(including school heads). Aggregates: total enrolment / total teachers."),
         caveat=("Baja tanto por más docentes como por menos alumnos (menos niños y migración). Las plazas docentes se financian con "
                 "recursos del Tesoro Público y las administra el gobierno regional (UGEL), no la municipalidad.",
                 "Falls both with more teachers and with fewer pupils (fewer children and out-migration). Teaching posts are funded "
                 "by the national Treasury and managed by the regional government (UGEL), not by the municipality.")),
    dict(id="sch_electric", kind="official_rate", col="sch_electric", dept_code="261276", cat="education",
         years=(2001, 2022), district_years=(2011, 2022), map=True, src="escale", codes="261276",
         label=("Locales escolares públicos conectados a la red eléctrica", "Public school premises connected to the electricity grid"),
         desc=("Porcentaje de locales escolares públicos con conexión a la red pública de electricidad.",
               "Percentage of public school premises connected to the public electricity grid."),
         caveat=("El valor de Cusco es la serie oficial departamental de SIRTOD; los valores distritales se muestran tal como se publican. "
                 "Las provincias no se calculan a partir de los distritos porque SIRTOD no publica el número de locales; "
                 "las series provinciales oficiales de SIRTOD aún no se incluyen.",
                 "The Cusco value is SIRTOD's official department series; district values are shown as published. "
                 "Provinces are not built from districts because SIRTOD does not publish the number of premises; "
                 "SIRTOD's official province series are not included yet.")),
    dict(id="ece_read", kind="official_rate", col="ece_read_satis", dept_code="420549", cat="education",
         years=(2007, 2016), district_years=(2007, 2016), map=True, src="umc", codes="420549",
         label=("Estudiantes de 2.º grado con nivel satisfactorio en lectura (ECE)", "2nd-grade pupils at the satisfactory level in reading (ECE)"),
         desc=("Porcentaje de los estudiantes de segundo grado de primaria evaluados que alcanzan el nivel satisfactorio en comprensión lectora en la Evaluación Censal de Estudiantes.",
               "Percentage of second-grade primary pupils assessed who reach the satisfactory level in reading comprehension in the national census test (ECE)."),
         caveat=("Se refiere a los estudiantes evaluados: los de escuelas de educación intercultural bilingüe (EIB) y de escuelas muy pequeñas "
                 "no rinden esta prueba, por lo que las cifras describen sobre todo escuelas de enseñanza en castellano y pueden sobrestimar el "
                 "aprendizaje en zonas quechuahablantes. Los porcentajes distritales se basan en pocos alumnos en distritos pequeños (un 0% puede "
                 "reflejar un grupo muy pequeño), y la cobertura distrital es incompleta en algunos años (69 de 108 distritos en 2007, 31 en 2008, 73 en 2009 y 81 en 2012). El valor de Cusco es la serie oficial departamental; "
                 "las provincias no se calculan porque SIRTOD no publica el número de evaluados.",
                 "Refers to pupils assessed: pupils in intercultural bilingual (EIB) schools and in very small schools do not take this test, "
                 "so the figures mainly describe Spanish-instruction schools and may overstate learning in Quechua-speaking areas. District "
                 "percentages rest on few pupils in small districts (a 0% may reflect a very small group), and district coverage is incomplete in "
                 "some years (69 of 108 districts in 2007, 31 in 2008, 73 in 2009 and 81 in 2012). The Cusco value is the official department series; provinces are not built because SIRTOD does not publish the "
                 "number of pupils assessed.")),
    dict(id="ece_math", kind="official_rate", col="ece_math_satis", dept_code="420553", cat="education",
         years=(2007, 2016), district_years=(2007, 2016), map=True, src="umc", codes="420553",
         label=("Estudiantes de 2.º grado con nivel satisfactorio en matemática (ECE)", "2nd-grade pupils at the satisfactory level in mathematics (ECE)"),
         desc=("Porcentaje de los estudiantes de segundo grado de primaria evaluados que alcanzan el nivel satisfactorio en matemática en la Evaluación Censal de Estudiantes.",
               "Percentage of second-grade primary pupils assessed who reach the satisfactory level in mathematics in the national census test (ECE)."),
         caveat=("Se refiere a los estudiantes evaluados: los de escuelas de educación intercultural bilingüe (EIB) y de escuelas muy pequeñas "
                 "no rinden esta prueba, por lo que las cifras describen sobre todo escuelas de enseñanza en castellano y pueden sobrestimar el "
                 "aprendizaje en zonas quechuahablantes. Los porcentajes distritales se basan en pocos alumnos en distritos pequeños (un 0% puede "
                 "reflejar un grupo muy pequeño), y la cobertura distrital es incompleta en algunos años (69 de 108 distritos en 2007, 31 en 2008, 73 en 2009 y 81 en 2012). El valor de Cusco es la serie oficial departamental; "
                 "las provincias no se calculan porque SIRTOD no publica el número de evaluados.",
                 "Refers to pupils assessed: pupils in intercultural bilingual (EIB) schools and in very small schools do not take this test, "
                 "so the figures mainly describe Spanish-instruction schools and may overstate learning in Quechua-speaking areas. District "
                 "percentages rest on few pupils in small districts (a 0% may reflect a very small group), and district coverage is incomplete in "
                 "some years (69 of 108 districts in 2007, 31 in 2008, 73 in 2009 and 81 in 2012). The Cusco value is the official department series; provinces are not built because SIRTOD does not publish the "
                 "number of pupils assessed.")),
    dict(id="late_birth_share", kind="ratio", num="vit_births_late", den="vit_births_reg", cat="registration",
         official_check={"num": "262226", "den": "262211"}, min_den=20, missing_is_zero=True,
         years=(2005, 2024), map=True, src="reniec", codes="262226 / 262211",
         label=("Nacimientos inscritos de forma tardía", "Births registered late"),
         desc=("Porcentaje de los nacimientos inscritos que se registraron por vía extraordinaria, fuera del plazo legal (60 días en general; 90 días en comunidades nativas y municipalidades de centros poblados). En agregados: tardíos / total inscritos.",
               "Percentage of registered births that were registered late, after the legal deadline (60 days in general; 90 days in native communities and populated-centre municipalities). Aggregates: late / all registered births."),
         caveat=("Se cuenta donde se inscribe el nacimiento, no donde vive la madre; cada vez más nacimientos se inscriben en hospitales de las capitales. "
                 "Las campañas nacionales de identidad influyen tanto como el desarrollo local. Los distritos con menos de 20 nacimientos inscritos en el año "
                 "no se muestran, y 2021-2022 no se muestran para Cusco ni sus provincias porque la suma distrital de inscripciones tardías no cuadra "
                 "con el total departamental de SIRTOD.",
                 "Counted where the birth is registered, not where the mother lives; more and more births are registered in hospitals in the main towns. "
                 "National identity campaigns matter as much as local development. Districts with fewer than 20 registered births in the year are not "
                 "shown, and 2021-2022 are not shown for Cusco or its provinces because the district sum of late registrations does not match "
                 "SIRTOD's department total.")),
    dict(id="lab_private_workers", kind="sum", col="lab_private_workers", measures=["total", "per_1000"], money=False,
         official_check={"col": "517303"}, missing_is_zero=True,
         cat="economy", years=(2015, LAST_YEAR), map=True, src="mtpe", codes="517303",
         unit=("Trabajadores", "Workers"),
         label=("Trabajadores formales del sector privado", "Formal private-sector workers"),
         desc=("Trabajadores del sector privado registrados en la Planilla Electrónica (empleo formal).",
               "Private-sector workers registered in the electronic payroll (formal employment)."),
         caveat=("Solo empleo formal, una parte pequeña del empleo en la mayoría de distritos. El lugar asignado parece ser el del empleador o el "
                 "establecimiento declarado: Megantoni (Camisea) registra alrededor de 1 000 trabajadores o menos, por lo que es probable que el empleo del gas se "
                 "registre en otros distritos. Un distrito sin dato tiene cero trabajadores o una cifra no publicada; como la suma de los distritos "
                 "coincide con el total departamental, en provincias y en Cusco se cuentan como cero.",
                 "Formal jobs only, a small share of employment in most districts. The location assigned appears to be the employer's or the declared "
                 "establishment's: Megantoni (Camisea) records about 1,000 workers or fewer, so gas employment is probably recorded in other districts. "
                 "A district without data has zero workers or an unpublished figure; since the district sum matches the department total, they count "
                 "as zero in provinces and in Cusco.")),
    dict(id="fin_cmac_present", kind="binary", col="fin_cmac_present", measures=["count"], cat="economy",
         years=(2003, LAST_YEAR), map=True, src="sbs", codes="389746",
         unit=("Distritos (en el mapa distrital: 1 = sí, 0 = no)", "Districts (on the district map: 1 = yes, 0 = no)"),
         label=("Distritos con colocaciones de una caja municipal", "Districts where a municipal savings bank (caja) lends"),
         desc=("Número de distritos donde al menos una caja municipal de ahorro y crédito registra créditos (es decir, tiene una agencia).",
               "Number of districts where at least one municipal savings and credit bank (caja municipal) books loans (that is, has a branch)."),
         caveat=("Los créditos se registran en la agencia: los vecinos de distritos sin agencia también pueden ser clientes.",
                 "Loans are booked at the branch: residents of districts without a branch may also borrow there.")),
    dict(id="mun_computers", kind="sum", col="mun_computers", measures=["total"], money=False, cat="municipal",
         official_check={"col": "121992", "shift": 1},
         years=(2003, 2024), map=False, src="renamu", codes="121992",
         unit=("Computadoras", "Computers"),
         label=("Computadoras de las municipalidades", "Computers in municipalities"),
         desc=("Número de computadoras (operativas y no operativas) de las municipalidades.",
               "Number of computers (working or not) available to municipalities."),
         caveat=("Se fecha al año anterior al de la encuesta RENAMU, porque el equipamiento se registra al llenarla a inicios del año siguiente "
                 "(supuesto basado en el calendario de RENAMU). En 2015 se omite el valor erróneo de Kimbiri (1 631 frente a 190 y 162), "
                 "y como el total departamental oficial todavía lo incluye, ese año no se muestra para Cusco ni para sus provincias.",
                 "Dated to the year before the RENAMU survey, because equipment is recorded when the survey is filled in early the following year "
                 "(an assumption based on the RENAMU calendar). In 2015 Kimbiri's erroneous value (1,631 against 190 and 162) is left out, "
                 "and because the official department total still includes it, that year is not shown for Cusco or its provinces.")),
    dict(id="mun_dump_trucks", kind="sum", col="mun_dump_trucks", measures=["total"], money=False, cat="municipal",
         official_check={"col": "121981", "shift": 1},
         years=(2003, 2024), map=False, src="renamu", codes="121981",
         unit=("Volquetes", "Dump trucks"),
         label=("Volquetes operativos de las municipalidades", "Working dump trucks available to municipalities"),
         desc=("Número de volquetes operativos de las municipalidades, usados para transportar materiales de construcción y recoger residuos sólidos.",
               "Number of working dump trucks available to municipalities, used to carry construction materials and collect solid waste."),
         caveat=("Sin dato en 2005. Se fecha al año anterior al de la encuesta, como las computadoras (supuesto basado en el calendario de RENAMU). "
                 "En 2004 se omiten los valores erróneos de Cusco y Paucartambo, y como el total departamental oficial todavía los incluye, "
                 "ese año no se muestra para Cusco ni para sus provincias.",
                 "No data for 2005. Dated to the year before the survey, like computers (an assumption based on the RENAMU calendar). "
                 "In 2004 the erroneous values of Cusco and Paucartambo are left out, and because the official department total still "
                 "includes them, that year is not shown for Cusco or its provinces.")),
    dict(id="sec_serenazgo", kind="binary", col="sec_serenazgo", measures=["pct"], cat="municipal",
         years=(2007, 2024), map=True, src="renamu", codes="122093",
         unit=("Porcentaje de municipalidades (en el mapa distrital: 100 = brinda el servicio, 0 = no)",
               "Percent of municipalities (on the district map: 100 = provides the service, 0 = does not)"),
         label=("Municipalidades que brindan serenazgo", "Municipalities providing serenazgo (local security patrols)"),
         desc=("Porcentaje de las municipalidades que respondieron RENAMU que brindan el servicio de serenazgo.",
               "Percentage of municipalities answering RENAMU that provide the serenazgo service (local security patrols)."),
         caveat=("Desde 2007: en 2004-2005 casi ninguna municipalidad registra el servicio (incluso Cusco, que lo brinda desde 2007), lo que sugiere "
                 "un cambio en la pregunta; 2006 no tiene datos. Es un servicio municipal, no una medida de delincuencia.",
                 "From 2007: in 2004-2005 almost no municipality records the service (not even Cusco, which provides it from 2007), which suggests a "
                 "change in the question; 2006 has no data. It is a municipal service, not a measure of crime.")),
    dict(id="vdl_benef_0_6", kind="sum", col="vdl_benef_0_6", measures=["total"], money=False, cat="social",
         official_check={"col": "516485"},
         years=(2010, 2024), map=False, src="renamu", codes="516485",
         unit=("Beneficiarios", "Beneficiaries"),
         label=("Beneficiarios del Vaso de Leche de 0 a 6 años", "Vaso de Leche beneficiaries aged 0-6"),
         desc=("Niñas y niños de 0 a 6 años atendidos por el programa municipal Vaso de Leche.",
               "Children aged 0-6 served by the municipal Vaso de Leche (glass of milk) programme."),
         caveat=("La municipalidad elige a los beneficiarios y el presupuesto nacional del programa está casi congelado en términos nominales, "
                 "por lo que la caída mezcla menor necesidad con menor presupuesto real. En 2014 cuatro distritos (Cusco, Marcapata, Llusco y Omacha) "
                 "tienen valores erróneos en la fuente y se omiten, por lo que ese año no se muestra para Cusco ni para las provincias afectadas.",
                 "The municipality chooses the beneficiaries and the programme's national budget is almost frozen in nominal terms, "
                 "so the decline mixes lower need with a shrinking real budget. In 2014 four districts (Cusco, Marcapata, Llusco and Omacha) have "
                 "erroneous source values and are left out, so that year is not shown for Cusco or the affected provinces.")),
]

CENSUS_CAVEAT = ("Instantánea censal. Los valores de provincia y de Cusco se calculan como cociente de las sumas de los conteos distritales. "
                 "Los distritos creados después de 2007 no tienen valor de 2007, y los creados en 2021 tampoco de 2017. Echarate, Vilcabamba y "
                 "Kimbiri perdieron territorio entre ambos censos (Megantoni, Inkawasi, Villa Virgen y Villa Kintiarina), por lo que sus valores "
                 "de 2007 y 2017 no son comparables entre sí. En 2007, los totales provinciales y departamentales que publica SIRTOD para viviendas y "
                 "hogares no coinciden con la suma de sus distritos (a nivel departamental, agua y electricidad 14% por debajo, internet 27%, "
                 "celular 17% y el total de viviendas 9%), y con ellos las provincias de Cusco y Paruro tendrían 5,8 y 6,4 personas por "
                 "vivienda, frente a 3,7-4,3 en todas las provincias con los conteos distritales; por eso aquí se construyen a partir de los "
                 "conteos distritales y difieren de los valores que implican los totales departamentales de SIRTOD hasta en 7 puntos. "
                 "En 2017 la pregunta sobre el combustible para cocinar admite varios combustibles, por lo que la cocina con leña o bosta "
                 "no es comparable entre ambos censos; en 2017, los indicadores de hogares usan como denominador el total de hogares de SIRTOD (516818).",
                 "Census snapshot. Province and Cusco values are ratios of the sums of the district counts. Districts created after 2007 have "
                 "no 2007 value, and those created in 2021 have no 2017 value either. Echarate, Vilcabamba and Kimbiri lost territory between "
                 "the two censuses (to Megantoni, Inkawasi, Villa Virgen and Villa Kintiarina), so their 2007 and 2017 values are not comparable. "
                 "For 2007, SIRTOD's own province and department totals for dwellings and households do not add up to its districts "
                 "(at department level, water and electricity 14% short, internet 27%, mobile phones 17% and total dwellings 9%), and "
                 "with them the provinces of Cusco and Paruro would have 5.8 and 6.4 persons per dwelling, against 3.7-4.3 in every "
                 "province from the district counts; the values here are therefore built from the district counts and differ from those "
                 "implied by SIRTOD's department totals by up to 7 points. In 2017 the cooking-fuel question allows several fuels, so cooking "
                 "with firewood or dung is not comparable between the two censuses; household items in 2017 use SIRTOD's total of households "
                 "(516818) as denominator.")
# (id stem in the baseline columns, label es/en, description es/en, codes)
CENSUS_VARS = [
    ("water_in", ("Viviendas con agua de red pública dentro de la vivienda", "Dwellings with piped water inside the dwelling"),
     ("Porcentaje de viviendas con ocupantes presentes que se abastecen de agua por red pública dentro de la vivienda.",
      "Percentage of private dwellings with occupants present supplied with piped water inside the dwelling."), "407209 / (407243 + 407244)"),
    ("sewer_in", ("Viviendas con desagüe de red pública dentro de la vivienda", "Dwellings with a sewer connection inside the dwelling"),
     ("Porcentaje de viviendas con ocupantes presentes conectadas a la red pública de desagüe dentro de la vivienda.",
      "Percentage of private dwellings with occupants present connected to the public sewer inside the dwelling."), "407217 / (407243 + 407244)"),
    ("electric", ("Viviendas con alumbrado eléctrico de red pública", "Dwellings with electricity from the public grid"),
     ("Porcentaje de viviendas con ocupantes presentes con alumbrado eléctrico por red pública.",
      "Percentage of private dwellings with occupants present lit by electricity from the public grid."), "407243 / (407243 + 407244)"),
    ("earth_floor", ("Viviendas con piso de tierra", "Dwellings with earth floors"),
     ("Porcentaje de viviendas con ocupantes presentes cuyo material predominante en el piso es tierra.",
      "Percentage of private dwellings with occupants present whose predominant floor material is earth."), "407201 / (407243 + 407244)"),
    ("cook_biomass", ("Hogares que cocinan con leña o bosta", "Households cooking with firewood or dung"),
     ("2007: porcentaje de hogares cuyo combustible principal para cocinar es leña o bosta (estiércol). "
      "2017: porcentaje de hogares que usan leña o bosta para cocinar; el Censo 2017 permitía declarar varios combustibles por hogar "
      "y un hogar que usa ambos se cuenta dos veces, por lo que la cifra de 2017 es una cota superior y no es comparable con la de 2007.",
      "2007: percentage of households whose main cooking fuel is firewood or dung. "
      "2017: percentage of households that use firewood or dung for cooking; the 2017 Census allowed several fuels per household "
      "and a household using both is counted twice, so the 2017 figure is an upper bound and is not comparable with 2007."),
     "2007: (407239 + 407240) / (407235–407242); 2017: (407239 + 407240) / 516818"),
    ("internet", ("Hogares con conexión a internet", "Households with an internet connection"),
     ("Porcentaje de hogares con conexión a internet.", "Percentage of households with an internet connection."),
     "2007: 516775 / (407235–407242); 2017: 516775 / 516818"),
    ("mobile", ("Hogares con teléfono celular", "Households with a mobile phone"),
     ("Porcentaje de hogares con al menos un teléfono celular.", "Percentage of households with at least one mobile phone."),
     "2007: 516777 / (407235–407242); 2017: 516777 / 516818"),
    ("quechua", ("Población con el quechua como lengua materna", "Population with Quechua as mother tongue"),
     ("Porcentaje de la población de 3 años a más que declara como lengua materna el castellano, el quechua, el aimara u otra lengua, "
      "cuya lengua materna es el quechua.",
      "Percentage of the population aged 3 and over reporting Spanish, Quechua, Aymara or another mother tongue whose mother tongue is Quechua."),
     "516750 / (516749 + 516750 + 516751 + 516752)"),
]
for stem, lab, desc, codes in CENSUS_VARS:
    VARS.append(dict(id=f"census_{stem}", kind="snapshot", cols={2007: f"c07_{stem}", 2017: f"c17_{stem}"},
                     weights={2007: "c07_pop", 2017: "c17_pop"}, measures=["pct"], cat="census", years=(2007, 2017),
                     map=True, src="census", codes=codes, label=lab, desc=desc, caveat=CENSUS_CAVEAT))
VARS.append(dict(
    id="poverty", kind="official_interval", district_cols={2013: ("pov13_mid", "pov13_lo", "pov13_hi")}, dept_code="427594",
    measures=["pct", "pct_lo", "pct_hi"], cat="poverty", years=(2007, LAST_YEAR), district_years=(2013, 2013),
    map=True, src="povmap", codes="427594",
    label=("Pobreza monetaria", "Monetary poverty"),
    desc=("Porcentaje de la población en pobreza monetaria. INEI publica intervalos de confianza: se muestran los límites y su punto medio, "
          "que es el promedio de ambos límites calculado para el gráfico (no una estimación puntual del INEI). "
          "Para Cusco, el intervalo anual (ENAHO, 2007-2025) corresponde al grupo de departamentos con niveles de pobreza estadísticamente "
          "semejantes al que pertenece Cusco. Para los distritos, el mapa de pobreza distrital de 2013 (el mismo código 427594 a nivel distrital).",
          "Percentage of the population in monetary poverty. INEI publishes confidence intervals: the bounds are shown with their midpoint, "
          "the average of the two bounds computed for the chart (not an INEI point estimate). "
          "For Cusco, the annual interval (ENAHO, 2007-2025) is that of the group of departments with statistically similar poverty to which "
          "Cusco belongs. For districts, the 2013 district poverty map (the same code 427594 at district level)."),
    caveat=("El intervalo de Cusco es el de su grupo de departamentos, no una estimación exclusiva de Cusco. El mapa distrital es de un solo año y "
            "sus intervalos son amplios: dos distritos cuyos intervalos se superponen no pueden ordenarse con seguridad. No hay nivel provincial. "
            "Inkawasi y Villa Virgen ya figuran en el mapa de 2013, aunque se crearon en 2015.",
            "The Cusco interval is that of its group of departments, not an estimate for Cusco alone. The district map covers a single year and its "
            "intervals are wide: two districts whose intervals overlap cannot be ranked with confidence. There is no province level. Inkawasi and "
            "Villa Virgen already appear in the 2013 map, although they were created in 2015.")))

MONEY_UNITS = {
    "total": ("Soles corrientes", "Current soles"),
    "per_capita": ("Soles corrientes por habitante", "Current soles per person"),
    "total_real": (f"Soles constantes de {REAL_BASE_YEAR} (IPC de la ciudad de Cusco)",
                   f"Constant {REAL_BASE_YEAR} soles (Cusco city CPI)"),
    "per_capita_real": (f"Soles constantes de {REAL_BASE_YEAR} por habitante (IPC de la ciudad de Cusco)",
                        f"Constant {REAL_BASE_YEAR} soles per person (Cusco city CPI)"),
}
MEASURE_LABEL = {
    "total": ("Total", "Total"),
    "per_capita": ("Por habitante", "Per person"),
    "per_1000": ("Por 1 000 habitantes", "Per 1,000 people"),
    "total_real": ("Total, en soles constantes", "Total, constant soles"),
    "per_capita_real": ("Por habitante, en soles constantes", "Per person, constant soles"),
    "pct": ("Porcentaje", "Percent"),
    "pct_lo": ("Límite inferior del intervalo", "Lower bound of the interval"),
    "pct_hi": ("Límite superior del intervalo", "Upper bound of the interval"),
    "ratio": ("Razón", "Ratio"),
    "count": ("Número", "Number"),
}
PCT_UNIT = ("Porcentaje (%)", "Percent (%)")


def is_money(v):
    return v.get("money", v["kind"] == "sum" and v["cat"] in MONEY_CATS)


def measures_for(v, deflator=None):
    if "measures" in v:
        ms = list(v["measures"])
    elif v["kind"] in ("ratio", "official_rate", "snapshot", "official_interval"):
        ms = ["pct"]
    else:
        ms = ["total", "per_capita"] if v.get("pc") else ["total"]
    if deflator is not None and is_money(v):
        ms += [m + "_real" for m in ms if m in ("total", "per_capita")]
    return ms


def unit_for(v, m):
    if is_money(v):
        return MONEY_UNITS[m]
    if m in ("pct", "pct_lo", "pct_hi"):
        # a yes/no service may carry its own unit, to explain the 0/100 district values
        return v["unit"] if v["kind"] == "binary" and "unit" in v else PCT_UNIT
    if v["id"] == "pop":
        return ("Personas", "People")
    u = v["unit"]
    if m == "per_1000":
        return (f"{u[0]} por 1 000 habitantes", f"{u[1]} per 1,000 people")
    return u


def aggregation_for(v, m):
    k = v["kind"]
    if k == "ratio":
        return "ratio_of_sums"
    if k == "binary":
        return "count_of_districts" if m == "count" else "share_of_reporting_municipalities"
    if k == "official_rate":
        return "official_department_series; districts as published; no province level"
    if k == "snapshot":
        return "ratio_of_sums of district counts"
    if k == "official_interval":
        return "official department interval (group of departments); districts as published; no province level"
    if m.startswith("per_capita"):
        return "sum_over_population"
    if m == "per_1000":
        return "sum_over_population_x1000"
    return "sum"


REAL_NOTE = {
    "es": (f"Valores reales = valor nominal × (IPC promedio de {REAL_BASE_YEAR} / IPC promedio del año), con el IPC de la "
           "ciudad de Cusco (INEI). Aplicar un índice de precios de la ciudad a todos los distritos es un supuesto "
           "analítico: no hay índices de precios distritales. Disponible desde 2010: el empalme del IPC de Cusco "
           "anterior a 2010 aún no está validado."),
    "en": (f"Real values = nominal value × ({REAL_BASE_YEAR} average CPI / the year's average CPI), using INEI's Cusco "
           "city CPI. Applying a city price index to all districts is an analytical assumption: there are no "
           "district price indices. Available from 2010: the link of the Cusco CPI before 2010 is not yet validated."),
}


def load_cpi():
    """Deflator to soles of REAL_BASE_YEAR from inputs/cpi_annual.csv (built by build_cpi.py).

    Partial years (fewer than 12 months) are not used. Years without a CPI
    (before 2010, where the Cusco CPI rebasing break is unresolved) get no real values.
    """
    if not CPI_FILE.exists():
        return None
    cpi = pd.read_csv(CPI_FILE)
    cpi = cpi[cpi.partial == 0].set_index("year")["cpi"] if "partial" in cpi else cpi.set_index("year")["cpi"]
    return cpi[REAL_BASE_YEAR] / cpi


# Districts created before 2018 and their parents (see panels/build_canon_spending_panel.py).
SPLIT_PARENT = {"080914": "080902", "080911": "080909", "080912": "080909", "080913": "080907"}
VALUE_COVERAGE_MIN = 0.98   # share of the money held by reporting districts
OFFICIAL_TOLERANCE = 0.02   # district sum vs SIRTOD's official department total
YOUNG_DISTRICT_YEARS = 3    # a district created in 2015+ counts as "young" in its first 3 years
# Single district values that are errors at the source (verified against neighbouring years); blanked.
SOURCE_ERRORS = [
    ("vdl_benef_0_6", "080101", 2014),    # Cusco: 32 vs 3,785 (2013) and 3,411 (2015)
    ("vdl_benef_0_6", "081209", 2014),    # Marcapata: 25 vs 632 / 515
    ("vdl_benef_0_6", "080706", 2014),    # Llusco: 42 vs 494 / 507
    ("vdl_benef_0_6", "081006", 2014),    # Omacha: 110 vs 734 / 703
    ("mun_dump_trucks", "080101", 2004),  # Cusco: zero-filled, but 22 (2003) and 15 (2006)
    ("mun_dump_trucks", "081101", 2004),  # Paucartambo: 32 vs 2-6 in neighbouring rounds
    ("mun_computers", "080907", 2015),    # Kimbiri: 1,631 vs 190 (2014) and 162 (2016)
]
PROXY_WINDOW = 3            # years searched for a missing district's size proxy


def coverage_inputs(df, col):
    """Per district-year: does it report `col`, is it covered by its parent, and its size proxy.

    A district in its first year whose own value is missing while its parent
    reports is 'covered by parent': its budget was still part of the parent's.
    The size proxy is the district's own value, or for a missing year its value
    the average of its values in the nearest observed years before and after
    (up to PROXY_WINDOW years away).
    """
    val = df.set_index(["ubigeo", "year"])[col]
    rep = df["exists"] & df[col].notna()
    parent = df.ubigeo.map(SPLIT_PARENT)
    parent_val = pd.Series([val.get((pu, y), np.nan) if isinstance(pu, str) else np.nan
                            for pu, y in zip(parent, df.year)], index=df.index)
    cbp = (df["exists"] & df[col].isna() & parent.notna()
           & (df.year == df.first_year_in_data) & parent_val.notna())
    w = df.pivot(index="ubigeo", columns="year", values=col)
    prox = w.copy()
    for k in range(1, PROXY_WINDOW + 1):
        # average of the observed values k years before and after (either one if only one exists)
        around = pd.concat([w.shift(k, axis=1), w.shift(-k, axis=1)]).groupby(level=0).mean()
        prox = prox.fillna(around)
    proxy = pd.Series([prox.at[u, y] if y in prox.columns else np.nan for u, y in zip(df.ubigeo, df.year)],
                      index=df.index)
    return rep, cbp, proxy.abs()


def aggregate(df, keys, v):
    """Aggregate one sum, ratio or binary variable from districts to the groups in `keys`."""
    if v.get("missing_is_zero"):        # SIRTOD stores no zeros: in a published year, a blank is a zero
        for c in ([v["col"]] if "col" in v else [v["num"], v["den"]]):
            published = df.groupby("year")[c].transform(lambda x: x.notna().any())
            df = df.assign(**{c: df[c].where(~(df.exists & published), df[c].fillna(0))})
    pop = df["pop_spliced"].fillna(0)
    exists = df["exists"]
    if v["kind"] in ("sum", "binary"):
        rep, cbp, proxy = coverage_inputs(df, v["col"])
        g = df.assign(_v=df[v["col"]].where(rep))
    else:
        rep_n = exists & df[v["num"]].notna()
        rep, cbp, proxy = coverage_inputs(df, v["den"])
        rep = rep & rep_n
        g = df.assign(_n=df[v["num"]].where(rep), _d=df[v["den"]].where(rep))
    if v["kind"] == "binary":           # a 0/1 service: coverage is about who answered, not money
        proxy = pd.Series(1.0, index=df.index)
    counted = exists & ~cbp
    # young districts (created 2015+, first years) that do not report: their territory may still be reported by parents
    young = (df.first_year_in_data >= 2015) & (df.year < df.first_year_in_data + YOUNG_DISTRICT_YEARS)
    young_miss = exists & ~rep & ~cbp & young
    other_miss = exists & ~rep & ~cbp & ~young
    g = g.assign(_rep=rep, _ex=exists, _om=other_miss,
                 _prep=pop.where(rep | cbp | young_miss, 0), _pex=pop.where(exists, 0),
                 _xrep=proxy.where(rep, 0).fillna(0), _xex=proxy.where(counted, 0).fillna(0))
    spec = dict(n_reporting=("_rep", "sum"), n_districts=("_ex", "sum"), pop_rep=("_prep", "sum"),
                pop_ex=("_pex", "sum"), x_rep=("_xrep", "sum"), x_ex=("_xex", "sum"), other_missing=("_om", "sum"))
    if v["kind"] == "sum":
        out = g.groupby(keys).agg(total=("_v", lambda s: s.sum(min_count=1)), **spec)
        out["per_capita"] = out.total / out.pop_rep.replace(0, np.nan)
        out["per_1000"] = 1000 * out.per_capita
    elif v["kind"] == "binary":
        out = g.groupby(keys).agg(count=("_v", lambda s: s.sum(min_count=1)),
                                  mean=("_v", "mean"), **spec)
        out["pct"] = 100 * out["mean"]
    else:
        out = g.groupby(keys).agg(num=("_n", lambda s: s.sum(min_count=1)),
                                  den=("_d", lambda s: s.sum(min_count=1)), **spec)
        r = out.num / out.den.replace(0, np.nan)
        out["pct"] = 100 * r
        out["ratio"] = v.get("scale", 100) * r
    out["pop_coverage"] = out.pop_rep / out.pop_ex.replace(0, np.nan)
    out["value_coverage"] = (out.x_rep / out.x_ex.replace(0, np.nan)).fillna(1.0)
    if v["kind"] == "binary":
        out["value_coverage"] = 1.0
    return out.reset_index()


def district_frame(p, v):
    """District-level values for sum, ratio, binary and official-rate variables."""
    d = p[p.exists].copy()
    k = v["kind"]
    if k == "sum":
        d["total"] = d[v["col"]]
        d["per_capita"] = d[v["col"]] / d["pop_spliced"]
        # split families in 2015-2017: population is allocated only approximately
        d.loc[d.pop_boundary_mismatch == 1, "per_capita"] = np.nan
        d["per_1000"] = 1000 * d["per_capita"]
        if v["id"] == "pop":
            d.loc[d.pop_boundary_mismatch == 1, "total"] = np.nan
        ok = d[v["col"]].notna()
    elif k == "binary":
        d["count"] = d[v["col"]]
        d["pct"] = 100 * d[v["col"]]
        ok = d[v["col"]].notna()
    elif k == "official_rate":
        d["pct"] = d[v["col"]]
        ok = d["pct"].notna()
    else:
        r = d[v["num"]] / d[v["den"]].replace(0, np.nan)
        if v.get("min_den"):
            r = r.where(d[v["den"]] >= v["min_den"])
        d["pct"] = 100 * r
        d["ratio"] = v.get("scale", 100) * r
        ok = r.notna()
    d = d[ok]
    return d.assign(level="district", geo_code=d.ubigeo, geo_name=d.district,
                    n_reporting=1, n_districts=1, pop_coverage=1.0, value_coverage=1.0)


def snapshot_frames(p, v):
    """District values and province/department values (ratio of the sums of district counts) for one census-type variable."""
    first = p.sort_values("year").groupby("ubigeo").first().reset_index()
    frames = []
    for year, col in v["cols"].items():
        wcol = v["weights"][year]
        if wcol == "pop_spliced":
            w = p[p.year == year].set_index("ubigeo")["pop_spliced"]
        else:
            w = first.set_index("ubigeo")[wcol]
        d = first[["ubigeo", "province", "district", "prov_code", "dept_code", col]].copy()
        d["w"] = d.ubigeo.map(w)
        d["pct"] = d[col]
        if "bounds" in v:
            lo, hi = v["bounds"][year]
            d["pct_lo"], d["pct_hi"] = first[lo].values, first[hi].values
        exists = p[(p.year == year) & p.exists].ubigeo
        d["exists"] = d.ubigeo.isin(exists)
        d["year"] = year
        dist = d[d.pct.notna()].assign(level="district", geo_code=lambda x: x.ubigeo, geo_name=lambda x: x.district,
                                       n_reporting=1, n_districts=1, pop_coverage=1.0, value_coverage=1.0)
        frames.append(dist)
        for level, code_col, name_map in [
            ("province", "prov_code", first.groupby("prov_code").province.first()),
            ("department", "dept_code", pd.Series({"08": "CUSCO"})),
        ]:
            rep = d.pct.notna() & d.w.notna()
            g = d.assign(_rep=rep & d.exists, _ex=d.exists, _w=d.w.where(rep, 0).fillna(0),
                         _wex=d.w.where(d.exists, 0).fillna(0))
            for c in ["pct", "pct_lo", "pct_hi"]:
                if c in d:
                    g[f"_wx_{c}"] = (d[c] * d.w).where(rep, 0).fillna(0)
            ratio_of_sums = f"{col}_n" in first.columns
            if ratio_of_sums:
                g["_num"] = first[f"{col}_n"].where(rep, 0).fillna(0).values
                g["_den"] = first[f"{col}_d"].where(rep, 0).fillna(0).values
            agg = g.groupby(code_col).agg(n_reporting=("_rep", "sum"), n_districts=("_ex", "sum"),
                                          wsum=("_w", "sum"), wex=("_wex", "sum"),
                                          **{f"s_{c}": (f"_wx_{c}", "sum") for c in ["pct", "pct_lo", "pct_hi"] if c in d})
            for c in ["pct", "pct_lo", "pct_hi"]:
                if c in d:
                    agg[c] = agg[f"s_{c}"] / agg.wsum.replace(0, np.nan)
            if ratio_of_sums:
                nd = g.groupby(code_col)[["_num", "_den"]].sum()
                agg["pct"] = 100 * nd["_num"] / nd["_den"].replace(0, np.nan)
            agg["pop_coverage"] = (agg.wsum / agg.wex.replace(0, np.nan)).clip(upper=1.0)
            agg["value_coverage"] = 1.0
            agg = agg.reset_index().rename(columns={code_col: "geo_code"})
            agg["level"], agg["year"] = level, year
            agg["geo_name"] = agg.geo_code.map(name_map)
            agg["province"] = agg.geo_name if level == "province" else ""
            frames.append(agg)
    return frames


def official_check(a, v, official):
    """1 if the district sum matches SIRTOD's official department total within tolerance, 0 if not, NaN if no total."""
    chk = v["official_check"]
    shift = chk.get("shift", 0)          # RENAMU survey-date items: official dated Y+1 describes Y
    def match(col_sum, code):
        s = official.get(code)
        if s is None:
            return pd.Series(np.nan, index=a.index)
        off = a.year.map(lambda y: s.get(y + shift, np.nan))
        ok = ((col_sum / off) - 1).abs() <= OFFICIAL_TOLERANCE
        return ok.astype(float).where(off.notna() & col_sum.notna())
    if v["kind"] == "sum":
        return match(a["total"], chk["col"]).values
    m1, m2 = match(a["num"], chk["num"]), match(a["den"], chk["den"])
    both = (m1 == 1) & (m2 == 1)
    return both.astype(float).where(m1.notna() & m2.notna()).values


def load_official_interval(code):
    """SIRTOD department series published as text intervals such as '19,5 - 23,4'."""
    dep = pd.read_excel(DEPT_FILE, sheet_name="Datos", header=5, dtype={"Código indicador": str, "Valor original": str})
    dep = dep[dep["Código indicador"] == code]
    parts = dep["Valor original"].str.replace(",", ".").str.split("-", expand=True)
    lo = pd.to_numeric(parts[0].str.strip(), errors="coerce")
    hi = pd.to_numeric(parts[1].str.strip(), errors="coerce")
    return pd.DataFrame({"year": dep["Año"].astype(int).values, "pct_lo": lo.values, "pct_hi": hi.values}).assign(
        pct=lambda x: (x.pct_lo + x.pct_hi) / 2)


def load_official_department(codes):
    dep = pd.read_excel(DEPT_FILE, sheet_name="Datos", header=5, dtype={"Código indicador": str})
    dep = dep[dep["Código indicador"].isin(codes)]
    return {c: g.set_index("Año")["Valor numérico"] for c, g in dep.groupby("Código indicador")}


def main() -> None:
    p = pd.read_csv(PANEL, dtype={"ubigeo": str})
    p = p[p.year <= LAST_YEAR].copy()
    p["prov_code"] = p.ubigeo.str[:4]
    p["dept_code"] = "08"
    p["exists"] = p.year >= p.first_year_in_data
    # SIRTOD stores no zeros, so missing financing with total revenue reported means zero financing
    p["munfin_rev_nonfin"] = p.munfin_rev_total - p.munfin_rev_financing.fillna(0)
    # likewise, no late registrations recorded where births were registered means zero late registrations
    p["vit_births_late"] = p.vit_births_late.where(p.vit_births_reg.isna(), p.vit_births_late.fillna(0))
    for col, ubigeo, year in SOURCE_ERRORS:
        p.loc[(p.ubigeo == ubigeo) & (p.year == year), col] = np.nan
    deflator = load_cpi()
    codes = [v["dept_code"] for v in VARS if v["kind"] == "official_rate"]
    codes += [c for v in VARS for k, c in v.get("official_check", {}).items() if k != "shift"]
    official = load_official_department(codes)

    rows = []
    dept_verdict = {}
    for v in VARS:
        y0, y1 = v["years"]
        measures = measures_for(v)
        if v["kind"] == "snapshot":
            frames = snapshot_frames(p, v)
        elif v["kind"] == "official_interval":
            first = p.sort_values("year").groupby("ubigeo").first().reset_index()
            frames = []
            for year, (cm, cl, ch) in v["district_cols"].items():
                d = first[["ubigeo", "province", "district", cm, cl, ch]].rename(columns={cm: "pct", cl: "pct_lo", ch: "pct_hi"})
                d = d[d.pct.notna()].assign(level="district", geo_code=lambda x: x.ubigeo, geo_name=lambda x: x.district,
                                            year=year, n_reporting=1, n_districts=1, pop_coverage=1.0, value_coverage=1.0)
                frames.append(d)
            o = load_official_interval(v["dept_code"])
            frames.append(o.assign(level="department", geo_code="08", geo_name="CUSCO", province="",
                                   n_reporting=np.nan, n_districts=np.nan, pop_coverage=np.nan, value_coverage=np.nan))
        else:
            frames = [district_frame(p, v)]
            if v["kind"] == "official_rate":
                s = official[v["dept_code"]]
                frames.append(pd.DataFrame({
                    "level": "department", "geo_code": "08", "geo_name": "CUSCO", "province": "",
                    "year": s.index.astype(int), "pct": s.values, "n_reporting": np.nan, "n_districts": np.nan,
                    "pop_coverage": np.nan, "value_coverage": np.nan}))
            else:
                for level, code_col, name_map in [
                    ("department", "dept_code", pd.Series({"08": "CUSCO"})),
                    ("province", "prov_code", p.groupby("prov_code").province.first()),
                ]:
                    a = aggregate(p, [code_col, "year"], v).rename(columns={code_col: "geo_code"})
                    a["official_ok"] = np.nan
                    if level == "department" and "official_check" in v:
                        a["official_ok"] = official_check(a, v, official)
                        dept_verdict[v["id"]] = dict(zip(a.year, a.official_ok))
                    a["level"] = level
                    a["geo_name"] = a.geo_code.map(name_map)
                    a["province"] = a.geo_name if level == "province" else ""
                    frames.append(a)

        for f in frames:
            for m in measures:
                if m not in f:
                    continue
                part = f[["level", "geo_code", "geo_name", "province", "year",
                          "n_reporting", "n_districts", "pop_coverage", "value_coverage"]].copy()
                part["official_ok"] = f["official_ok"].values if "official_ok" in f else np.nan
                part["other_missing"] = f["other_missing"].values if "other_missing" in f else np.nan
                part["variable"], part["measure"], part["value"] = v["id"], m, f[m].values
                part = part[part.value.notna()]
                win0, win1 = (v.get("district_years", (y0, y1)) if v["kind"] in ("official_rate", "official_interval") else (y0, y1))
                in_window = np.where(part.level == "district", part.year.between(win0, win1), part.year.between(y0, y1))
                in_window = pd.Series(in_window, index=part.index) & ~part.year.isin(v.get("exclude", []))
                if v["kind"] in ("official_rate", "official_interval"):
                    covered = pd.Series(True, index=part.index)
                else:
                    covered = (((part.pop_coverage >= COVERAGE_MIN) & (part.value_coverage >= VALUE_COVERAGE_MIN))
                               | (part.level == "district"))
                    # SIRTOD's department total is the sum of the published districts, so a match is informative only
                    # about districts that are absent because they are young (their territory reported by parents).
                    # A mismatch always hides the year, at department and province level; a match lets the year through
                    # when the only non-reporting districts are young ones.
                    if "official_check" in v:
                        verdict = dept_verdict.get(v["id"], {})
                        ok_year = part.year.map(lambda y: verdict.get(y, np.nan))
                        young_only = part.other_missing == 0
                        agg_level = part.level != "district"      # districts are shown as published
                        covered = (covered | ((ok_year == 1) & young_only)) & ((ok_year != 0) | ~agg_level)
                part["display"] = (in_window & covered).astype(int)
                rows.append(part)
                if deflator is not None and is_money(v) and m in ("total", "per_capita"):
                    real = part.copy()
                    real["measure"] = m + "_real"
                    real["value"] = real.value * real.year.map(deflator)
                    rows.append(real[real.value.notna()])

    long = pd.concat(rows, ignore_index=True)
    level_order = {"department": 0, "province": 1, "district": 2}
    var_order = {v["id"]: i for i, v in enumerate(VARS)}
    long = long.sort_values(["variable", "measure", "level", "geo_code", "year"],
                            key=lambda s: s.map(var_order) if s.name == "variable"
                            else s.map(level_order) if s.name == "level" else s)
    long["pop_coverage"] = long.pop_coverage.round(4)
    long["value_coverage"] = long.value_coverage.round(4)
    money_ids = {v["id"] for v in VARS if is_money(v)}
    long["value"] = np.where(long.measure.isin(["total", "total_real"]) & long.variable.isin(money_ids),
                             long.value.round(0), long.value.round(4))
    for c in ["n_reporting", "n_districts"]:
        long[c] = long[c].astype("Int64")
    cols = ["level", "geo_code", "geo_name", "province", "year", "variable", "measure",
            "value", "n_reporting", "n_districts", "pop_coverage", "value_coverage", "display"]
    long[cols].to_csv(OUT_LONG, index=False, encoding="utf-8")

    # Dictionary: one row per variable x measure
    drows = []
    for i, v in enumerate(VARS):
        for m in measures_for(v, deflator):
            sub = long[(long.variable == v["id"]) & (long.measure == m) & (long.display == 1)]
            dep = sub[sub.level == "department"]
            levels = [lv for lv in ["department", "province", "district"] if (sub.level == lv).any()]
            drows.append({
                "variable": v["id"], "measure": m, "sort_order": i,
                "category_es": CAT[v["cat"]][0], "category_en": CAT[v["cat"]][1],
                "label_es": v["label"][0], "label_en": v["label"][1],
                "measure_es": ("Punto medio del intervalo" if v["kind"] == "official_interval" and m == "pct" else MEASURE_LABEL[m][0]),
                "measure_en": ("Interval midpoint" if v["kind"] == "official_interval" and m == "pct" else MEASURE_LABEL[m][1]),
                "unit_es": unit_for(v, m)[0], "unit_en": unit_for(v, m)[1],
                "description_es": v["desc"][0], "description_en": v["desc"][1],
                "caveat_es": " ".join(x for x in [v["caveat"][0], REAL_NOTE["es"] if m.endswith("_real") else ""] if x),
                "caveat_en": " ".join(x for x in [v["caveat"][1], REAL_NOTE["en"] if m.endswith("_real") else ""] if x),
                "source_es": SRC[v["src"]][0], "source_en": SRC[v["src"]][1],
                "sirtod_codes": v["codes"],
                "kind": v["kind"], "aggregation": aggregation_for(v, m),
                "levels": ",".join(levels),
                "display_from": int(dep.year.min()) if len(dep) else None,
                "display_to": int(dep.year.max()) if len(dep) else None,
                "map_recommended": int(v["map"] and m in ("per_capita", "per_capita_real", "per_1000", "pct", "ratio", "count")),
            })
    pd.DataFrame(drows).to_csv(OUT_DICT, index=False, encoding="utf-8")

    shown = long[long.display == 1]
    print(f"wrote {len(long):,} rows ({len(shown):,} displayable), "
          f"{long.variable.nunique()} variables, {len(drows)} variable x measure series; "
          f"real values: {'yes' if deflator is not None else 'no (no CPI file)'}")


if __name__ == "__main__":
    main()
