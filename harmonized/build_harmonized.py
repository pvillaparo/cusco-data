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
    values are built from the districts, so the three levels always agree.
  * Measures: for amounts, the total and the per-capita value (total divided by
    the spliced population of the districts that report); for ratios, the ratio
    of sums (e.g. accrued / PIM across districts), never an average of ratios.
  * Coverage: an aggregate is displayed only if the reporting districts hold at
    least 95% of the population AND at least 98% of the money (estimated from
    each missing district's nearest observed year) of the districts that exist
    that year. A district in its first year whose parent still reports is
    treated as covered by the parent (its budget was still the parent's).
  * Years: each variable has a display window (canon from 2005, SIAF from 2008,
    municipal accounts from 2004 without the broken year 2023, FONCOMUN without
    the scrambled year 2016); 2026 is dropped for
    now (partial year). Rows outside the window are kept with display = 0.
  * Indicator kinds: sums (money or counts), ratios of sums, yes/no municipal
    services (count or share of reporting municipalities), official rates
    (department line from SIRTOD's department series because the district
    percentages come without denominators; districts as published; no
    province level) and census snapshots (2007, 2017 and the 2013 poverty map;
    province and department are population-weighted means, an approximation).
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
    "pop": ("INEI, proyecciones de población (SIRTOD 262234)",
            "INEI population projections (SIRTOD 262234)"),
    "canon": ("MEF, transferencias de canon a municipalidades (vía INEI SIRTOD)",
              "MEF canon transfers to municipalities (via INEI SIRTOD)"),
    "foncomun": ("MEF, Dirección Nacional de Contabilidad Pública: FONCOMUN transferido (vía INEI SIRTOD)",
                 "MEF Public Accounting Directorate: FONCOMUN transfers (via INEI SIRTOD)"),
    "canon_siaf": ("MEF: transferencias de canon y ejecución presupuestal SIAF (vía INEI SIRTOD)",
                   "MEF canon transfers and SIAF budget execution (via INEI SIRTOD)"),
    "siaf": ("MEF, Consulta Amigable / SIAF, gobiernos locales (vía INEI SIRTOD)",
             "MEF SIAF budget execution, local governments (via INEI SIRTOD)"),
    "munfin": ("MEF, Dirección Nacional de Contabilidad Pública: finanzas municipales (vía INEI SIRTOD)",
               "MEF Public Accounting Directorate: municipal finances (via INEI SIRTOD)"),
    "escale": ("MINEDU, Censo Escolar - ESCALE (vía INEI SIRTOD)", "MINEDU School Census - ESCALE (via INEI SIRTOD)"),
    "umc": ("MINEDU, Oficina de Medición de la Calidad de los Aprendizajes - ECE (vía INEI SIRTOD)",
            "MINEDU Learning Assessment Office - ECE census test (via INEI SIRTOD)"),
    "reniec": ("RENIEC, registro de nacimientos (vía INEI SIRTOD)", "RENIEC birth registration (via INEI SIRTOD)"),
    "mtpe": ("MTPE, Planilla Electrónica (vía INEI SIRTOD)", "MTPE electronic payroll (via INEI SIRTOD)"),
    "sbs": ("SBS, colocaciones de cajas municipales (vía INEI SIRTOD)", "SBS municipal savings banks' lending (via INEI SIRTOD)"),
    "renamu": ("INEI, Registro Nacional de Municipalidades - RENAMU (vía SIRTOD)",
               "INEI National Registry of Municipalities - RENAMU (via SIRTOD)"),
    "census": ("INEI, Censos Nacionales 2007 y 2017 (vía SIRTOD)", "INEI 2007 and 2017 National Censuses (via SIRTOD)"),
    "povmap": ("INEI, Mapa de pobreza provincial y distrital 2013 (vía SIRTOD)",
               "INEI 2013 provincial and district poverty map (via SIRTOD)"),
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
                 "(spending ~23% above SIAF accrued spending; revenue about twice the 2022-2024 average).")
MUNFIN_BAD_YEARS = [2023]

# id, kind, source column(s), category, display window, per-capita?, map?, source, codes, labels, description, caveat
VARS = [
    dict(id="pop", kind="sum", col="pop_spliced", cat="population", years=(2001, LAST_YEAR),
         pc=False, map=False, src="pop", codes="262234",
         label=("Población", "Population"),
         desc=("Población proyectada por INEI, con las proyecciones basadas en los censos de 2007 y 2017 empalmadas en una sola serie.",
               "INEI projected population, with the projections based on the 2007 and 2017 censuses spliced into one series."),
         caveat=("Antes de 2016 (departamento) y 2018 (distritos) la serie antigua está reescalada al nivel de la nueva; "
                 "2016-2017 interpolado a nivel distrital.",
                 "Before 2016 (department) and 2018 (districts) the old series is rescaled to the level of the new one; "
                 "2016-2017 interpolated at district level.")),
    dict(id="canon_total", kind="sum", col="canon_total", cat="canon", years=(2005, 2024),
         pc=True, map=True, src="canon", codes="407245",
         label=("Canon transferido a municipalidades", "Canon transferred to municipalities"),
         desc=("Suma de todos los tipos de canon transferidos a la municipalidad: minero, gasífero, hidroenergético, forestal, petrolero, pesquero y sobrecanon petrolero. "
               "El canon es la participación de los gobiernos locales y regionales en los ingresos y rentas que el Estado obtiene por la explotación de recursos naturales.",
               "Sum of all canon types transferred to the municipality: mining, gas, hydropower, forestry, oil, fishing and oil sobrecanon. "
               "Canon is the share of the revenue the State obtains from the exploitation of natural resources that is passed on to local and regional governments."),
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
         label=("Presupuesto Institucional de Apertura (PIA)", "Initial budget (PIA)"),
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
         desc=("Ingreso total recaudado por la municipalidad: ingresos corrientes, de capital, transferencias y financiamiento "
               "(este último incluye los saldos de balance de años anteriores y el endeudamiento).",
               "Total revenue collected by the municipality: current revenue, capital revenue, transfers and financing "
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
         desc=("Matrícula pública en educación básica regular (inicial, primaria y secundaria) dividida entre el número de docentes. "
               "En agregados: matrícula total / docentes totales.",
               "Public enrolment in regular basic education (pre-school, primary and secondary) divided by the number of teachers. "
               "Aggregates: total enrolment / total teachers."),
         caveat=("Baja tanto por más docentes como por menos alumnos (menos niños y migración). Los docentes los paga el gobierno central.",
                 "Falls both with more teachers and with fewer pupils (fewer children and out-migration). Teachers are paid by the central government.")),
    dict(id="sch_electric", kind="official_rate", col="sch_electric", dept_code="261276", cat="education",
         years=(2001, 2022), district_years=(2011, 2022), map=True, src="escale", codes="261276",
         label=("Locales escolares públicos conectados a la red eléctrica", "Public school premises connected to the electricity grid"),
         desc=("Porcentaje de locales escolares públicos con conexión a la red pública de electricidad.",
               "Percentage of public school premises connected to the public electricity grid."),
         caveat=("El valor de Cusco es la serie oficial departamental de SIRTOD; los valores distritales se muestran tal como se publican. "
                 "No hay nivel provincial porque SIRTOD no publica el número de locales para agregar los distritos.",
                 "The Cusco value is SIRTOD's official department series; district values are shown as published. "
                 "There is no province level because SIRTOD does not publish the number of premises needed to aggregate districts.")),
    dict(id="ece_read", kind="official_rate", col="ece_read_satis", dept_code="420549", cat="education",
         years=(2007, 2016), district_years=(2007, 2016), map=True, src="umc", codes="420549",
         label=("Estudiantes de 2.º grado con nivel satisfactorio en lectura (ECE)", "2nd-grade pupils at the satisfactory level in reading (ECE)"),
         desc=("Porcentaje de estudiantes de segundo grado de primaria que alcanzan el nivel satisfactorio en comprensión lectora en la Evaluación Censal de Estudiantes.",
               "Percentage of second-grade primary pupils reaching the satisfactory level in reading comprehension in the national census test (ECE)."),
         caveat=("La ECE excluye las escuelas de educación intercultural bilingüe, por lo que faltan sobre todo distritos rurales quechuahablantes. "
                 "Los porcentajes distritales se basan en pocos alumnos en distritos pequeños. El valor de Cusco es la serie oficial departamental; no hay nivel provincial.",
                 "The ECE excludes intercultural bilingual schools, so mostly rural Quechua-speaking districts are missing. "
                 "District percentages rest on few pupils in small districts. The Cusco value is the official department series; there is no province level.")),
    dict(id="ece_math", kind="official_rate", col="ece_math_satis", dept_code="420553", cat="education",
         years=(2007, 2016), district_years=(2007, 2016), map=True, src="umc", codes="420553",
         label=("Estudiantes de 2.º grado con nivel satisfactorio en matemática (ECE)", "2nd-grade pupils at the satisfactory level in mathematics (ECE)"),
         desc=("Porcentaje de estudiantes de segundo grado de primaria que alcanzan el nivel satisfactorio en matemática en la Evaluación Censal de Estudiantes.",
               "Percentage of second-grade primary pupils reaching the satisfactory level in mathematics in the national census test (ECE)."),
         caveat=("La ECE excluye las escuelas de educación intercultural bilingüe, por lo que faltan sobre todo distritos rurales quechuahablantes. "
                 "Los porcentajes distritales se basan en pocos alumnos en distritos pequeños. El valor de Cusco es la serie oficial departamental; no hay nivel provincial.",
                 "The ECE excludes intercultural bilingual schools, so mostly rural Quechua-speaking districts are missing. "
                 "District percentages rest on few pupils in small districts. The Cusco value is the official department series; there is no province level.")),
    dict(id="late_birth_share", kind="ratio", num="vit_births_late", den="vit_births_reg", cat="registration",
         official_check={"num": "262226", "den": "262211"},
         years=(2005, 2024), map=True, src="reniec", codes="262226 / 262211",
         label=("Nacimientos inscritos de forma tardía", "Births registered late"),
         desc=("Porcentaje de los nacimientos inscritos que se registraron por vía extraordinaria (fuera del plazo legal). En agregados: tardíos / total inscritos.",
               "Percentage of registered births that were registered late (after the legal deadline). Aggregates: late / all registered births."),
         caveat=("Se cuenta donde se inscribe el nacimiento, no donde vive la madre; cada vez más nacimientos se inscriben en hospitales de las capitales. "
                 "Las campañas nacionales de identidad influyen tanto como el desarrollo local.",
                 "Counted where the birth is registered, not where the mother lives; more and more births are registered in hospitals in the main towns. "
                 "National identity campaigns matter as much as local development.")),
    dict(id="lab_private_workers", kind="sum", col="lab_private_workers", measures=["total", "per_1000"], money=False,
         official_check={"col": "517303"},
         cat="economy", years=(2015, LAST_YEAR), map=True, src="mtpe", codes="517303",
         unit=("Trabajadores", "Workers"),
         label=("Trabajadores formales del sector privado", "Formal private-sector workers"),
         desc=("Trabajadores del sector privado registrados en la Planilla Electrónica (empleo formal).",
               "Private-sector workers registered in the electronic payroll (formal employment)."),
         caveat=("Solo empleo formal, una parte pequeña del empleo en la mayoría de distritos. Se asigna según el registro del empleador, "
                 "por lo que subestima a los trabajadores del gas de Camisea. Un distrito sin dato puede tener cero trabajadores o una cifra no publicada.",
                 "Formal jobs only, a small share of employment in most districts. Workers are assigned by the employer's registration, "
                 "so Camisea gas workers are undercounted. A district without data may have zero workers or an unpublished figure.")),
    dict(id="fin_cmac_present", kind="binary", col="fin_cmac_present", measures=["count"], cat="economy",
         years=(2003, LAST_YEAR), map=True, src="sbs", codes="389746",
         unit=("Distritos", "Districts"),
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
         desc=("Número de computadoras operativas de las municipalidades, fechado al año que describe (fin de año).",
               "Number of working computers in the municipalities, dated to the year it describes (end of year)."),
         caveat=("RENAMU registra el equipamiento al llenar la encuesta, a inicios del año siguiente; aquí se fecha al año anterior para alinearlo con el gasto.",
                 "RENAMU records equipment when the survey is filled in, early the following year; here it is dated to the previous year to line up with spending.")),
    dict(id="mun_dump_trucks", kind="sum", col="mun_dump_trucks", measures=["total"], money=False, cat="municipal",
         official_check={"col": "121981", "shift": 1},
         years=(2003, 2024), map=False, src="renamu", codes="121981",
         unit=("Volquetes", "Dump trucks"),
         label=("Volquetes de propiedad municipal", "Dump trucks owned by municipalities"),
         desc=("Número de volquetes de propiedad de las municipalidades, un bien de capital ligado a las obras públicas.",
               "Number of dump trucks owned by the municipalities, a capital good tied to public works."),
         caveat=("Sin dato en 2005. Fechado al año que describe, como las computadoras.",
                 "No data for 2005. Dated to the year it describes, like computers.")),
    dict(id="sec_serenazgo", kind="binary", col="sec_serenazgo", measures=["pct"], cat="municipal",
         years=(2004, 2024), map=True, src="renamu", codes="122093",
         label=("Municipalidades que brindan serenazgo", "Municipalities providing serenazgo (local security patrols)"),
         desc=("Porcentaje de las municipalidades que respondieron RENAMU que brindan el servicio de serenazgo.",
               "Percentage of municipalities answering RENAMU that provide the serenazgo service (municipal security patrols)."),
         caveat=("Sin dato en 2006. Es un servicio municipal, no una medida de delincuencia.",
                 "No data for 2006. It is a municipal service, not a measure of crime.")),
    dict(id="vdl_benef_0_6", kind="sum", col="vdl_benef_0_6", measures=["total"], money=False, cat="social",
         official_check={"col": "516485"},
         years=(2010, 2024), map=False, src="renamu", codes="516485",
         unit=("Beneficiarios", "Beneficiaries"),
         label=("Beneficiarios del Vaso de Leche de 0 a 6 años", "Vaso de Leche beneficiaries aged 0-6"),
         desc=("Niñas y niños de 0 a 6 años atendidos por el programa municipal Vaso de Leche.",
               "Children aged 0-6 served by the municipal Vaso de Leche (glass of milk) programme."),
         caveat=("La municipalidad elige a los beneficiarios y el presupuesto nacional del programa está casi congelado en términos nominales, "
                 "por lo que la caída mezcla menor necesidad con menor presupuesto real.",
                 "The municipality chooses the beneficiaries and the programme's national budget is almost frozen in nominal terms, "
                 "so the decline mixes lower need with a shrinking real budget.")),
]

CENSUS_CAVEAT = ("Instantánea censal. Los valores de provincia y de Cusco son promedios ponderados por la población censal, una aproximación. "
                 "Los distritos creados después de 2007 no tienen valor de 2007, y los creados en 2021 tampoco de 2017.",
                 "Census snapshot. Province and Cusco values are averages weighted by census population, an approximation. "
                 "Districts created after 2007 have no 2007 value, and those created in 2021 have no 2017 value either.")
# (id stem in the baseline columns, label es/en, description es/en, codes)
CENSUS_VARS = [
    ("water_in", ("Viviendas con agua de red pública dentro de la vivienda", "Dwellings with piped water inside the dwelling"),
     ("Porcentaje de viviendas con ocupantes presentes que se abastecen de agua por red pública dentro de la vivienda.",
      "Percentage of occupied dwellings supplied with piped water inside the dwelling."), "407209"),
    ("sewer_in", ("Viviendas con desagüe de red pública dentro de la vivienda", "Dwellings with a sewer connection inside the dwelling"),
     ("Porcentaje de viviendas con ocupantes presentes conectadas a la red pública de desagüe dentro de la vivienda.",
      "Percentage of occupied dwellings connected to the public sewer inside the dwelling."), "407217"),
    ("electric", ("Viviendas con alumbrado eléctrico de red pública", "Dwellings with electricity from the public grid"),
     ("Porcentaje de viviendas con ocupantes presentes con alumbrado eléctrico por red pública.",
      "Percentage of occupied dwellings lit by electricity from the public grid."), "407243"),
    ("earth_floor", ("Viviendas con piso de tierra", "Dwellings with earth floors"),
     ("Porcentaje de viviendas con ocupantes presentes cuyo piso es de tierra.",
      "Percentage of occupied dwellings with earth floors."), "407201"),
    ("cook_biomass", ("Hogares que cocinan con leña o bosta", "Households cooking with firewood or dung"),
     ("Porcentaje de hogares que usan leña o bosta (estiércol) para cocinar.",
      "Percentage of households cooking with firewood or dung."), "407239 / 407240"),
    ("internet", ("Hogares con conexión a internet", "Households with an internet connection"),
     ("Porcentaje de hogares con conexión a internet.", "Percentage of households with an internet connection."), "516775"),
    ("mobile", ("Hogares con teléfono celular", "Households with a mobile phone"),
     ("Porcentaje de hogares con al menos un teléfono celular.", "Percentage of households with at least one mobile phone."), "516777"),
    ("quechua", ("Población con el quechua como lengua materna", "Population with Quechua as mother tongue"),
     ("Porcentaje de la población de 3 años a más cuya lengua materna es el quechua.",
      "Percentage of the population aged 3 and over whose mother tongue is Quechua."), "516749 / 516750"),
]
for stem, lab, desc, codes in CENSUS_VARS:
    VARS.append(dict(id=f"census_{stem}", kind="snapshot", cols={2007: f"c07_{stem}", 2017: f"c17_{stem}"},
                     weights={2007: "c07_pop", 2017: "c17_pop"}, measures=["pct"], cat="census", years=(2007, 2017),
                     map=True, src="census", codes=codes, label=lab, desc=desc, caveat=CENSUS_CAVEAT))
VARS.append(dict(
    id="poverty_2013", kind="snapshot", cols={2013: "pov13_mid"}, bounds={2013: ("pov13_lo", "pov13_hi")},
    weights={2013: "pop_spliced"}, measures=["pct", "pct_lo", "pct_hi"], cat="poverty", years=(2013, 2013),
    map=True, src="povmap", codes="427594",
    label=("Pobreza monetaria (mapa de pobreza 2013)", "Monetary poverty (2013 poverty map)"),
    desc=("Porcentaje de la población en pobreza monetaria. INEI publica un intervalo por distrito; se muestra el punto medio "
          "y los límites inferior y superior.",
          "Percentage of the population in monetary poverty. INEI publishes an interval for each district; the midpoint "
          "and the lower and upper bounds are shown."),
    caveat=("Es una estimación de un solo año, publicada como intervalo amplio: dos distritos cuyos intervalos se superponen no pueden "
            "ordenarse con seguridad. Los valores de provincia y de Cusco son promedios de los puntos medios ponderados por población, una aproximación.",
            "A single-year estimate published as a wide interval: two districts whose intervals overlap cannot be ranked with confidence. "
            "Province and Cusco values are population-weighted averages of the midpoints, an approximation.")))

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
    "per_1000": ("Por 1 000 habitantes", "Per 1,000 people"),
    "total_real": ("Total, en soles constantes", "Total, constant soles"),
    "per_capita_real": ("Por habitante, en soles constantes", "Per person, constant soles"),
    "pct": ("Porcentaje", "Percent"),
    "pct_lo": ("Límite inferior", "Lower bound"),
    "pct_hi": ("Límite superior", "Upper bound"),
    "ratio": ("Razón", "Ratio"),
    "count": ("Número", "Number"),
}
PCT_UNIT = ("Porcentaje (%)", "Percent (%)")


def is_money(v):
    return v.get("money", v["kind"] == "sum" and v["cat"] in MONEY_CATS)


def measures_for(v, deflator=None):
    if "measures" in v:
        ms = list(v["measures"])
    elif v["kind"] in ("ratio", "official_rate", "snapshot"):
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
        return PCT_UNIT
    if v["id"] == "pop":
        return ("Personas", "People")
    u = v["unit"]
    if m == "per_1000":
        return (f"{u[0]} por 1 000 habitantes", f"{u[1]} per 1,000 people")
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
        return "population_weighted_mean (approximate)"
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
    g = g.assign(_rep=rep, _ex=exists,
                 _prep=pop.where(rep | cbp, 0), _pex=pop.where(exists, 0),
                 _xrep=proxy.where(rep, 0).fillna(0), _xex=proxy.where(counted, 0).fillna(0))
    spec = dict(n_reporting=("_rep", "sum"), n_districts=("_ex", "sum"), pop_rep=("_prep", "sum"),
                pop_ex=("_pex", "sum"), x_rep=("_xrep", "sum"), x_ex=("_xex", "sum"))
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
        d["pct"] = 100 * r
        d["ratio"] = v.get("scale", 100) * r
        ok = r.notna()
    d = d[ok]
    return d.assign(level="district", geo_code=d.ubigeo, geo_name=d.district,
                    n_reporting=1, n_districts=1, pop_coverage=1.0, value_coverage=1.0)


def snapshot_frames(p, v):
    """District values and population-weighted province/department means for one census-type variable."""
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
            agg = g.groupby(code_col).agg(n_reporting=("_rep", "sum"), n_districts=("_ex", "sum"),
                                          wsum=("_w", "sum"), wex=("_wex", "sum"),
                                          **{f"s_{c}": (f"_wx_{c}", "sum") for c in ["pct", "pct_lo", "pct_hi"] if c in d})
            for c in ["pct", "pct_lo", "pct_hi"]:
                if c in d:
                    agg[c] = agg[f"s_{c}"] / agg.wsum.replace(0, np.nan)
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
    deflator = load_cpi()
    codes = [v["dept_code"] for v in VARS if v["kind"] == "official_rate"]
    codes += [c for v in VARS for k, c in v.get("official_check", {}).items() if k != "shift"]
    official = load_official_department(codes)

    rows = []
    for v in VARS:
        y0, y1 = v["years"]
        measures = measures_for(v)
        if v["kind"] == "snapshot":
            frames = snapshot_frames(p, v)
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
                    ("province", "prov_code", p.groupby("prov_code").province.first()),
                    ("department", "dept_code", pd.Series({"08": "CUSCO"})),
                ]:
                    a = aggregate(p, [code_col, "year"], v).rename(columns={code_col: "geo_code"})
                    a["official_ok"] = np.nan
                    if level == "department" and "official_check" in v:
                        a["official_ok"] = official_check(a, v, official)
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
                part["variable"], part["measure"], part["value"] = v["id"], m, f[m].values
                part = part[part.value.notna()]
                win0, win1 = (v.get("district_years", (y0, y1)) if v["kind"] == "official_rate" else (y0, y1))
                in_window = np.where(part.level == "district", part.year.between(win0, win1), part.year.between(y0, y1))
                in_window = pd.Series(in_window, index=part.index) & ~part.year.isin(v.get("exclude", []))
                if v["kind"] == "official_rate":
                    covered = pd.Series(True, index=part.index)
                else:
                    covered = (((part.pop_coverage >= COVERAGE_MIN) & (part.value_coverage >= VALUE_COVERAGE_MIN))
                               | (part.level == "district"))
                    # where SIRTOD has an official department total, it decides
                    has_off = part.official_ok.notna()
                    covered = covered.where(~has_off, part.official_ok == 1)
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
                "measure_es": MEASURE_LABEL[m][0], "measure_en": MEASURE_LABEL[m][1],
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
