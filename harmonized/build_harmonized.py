"""
Build the display-ready ("harmonized") Cusco-stats dataset.

Input : panels/canon_spending_district_year.csv  (built by panels/build_canon_spending_panel.py)
        harmonized/inputs/cpi_annual.csv          (optional; columns year,cpi)
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
    least 95% of the population of the districts that exist that year.
  * Years: each variable has a display window (canon from 2004, SIAF from 2008,
    RENAMU from 2004, without the broken RENAMU year 2023); 2026 is dropped for
    now (partial year). Rows outside the window are kept with display = 0.
  * Money is in current soles. If inputs/cpi_annual.csv exists, real values in
    soles of REAL_BASE_YEAR are added as extra measures.
"""

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent / "panels" / "canon_spending_district_year.csv"
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
    "finance": ("Finanzas municipales (RENAMU)", "Municipal finances (RENAMU)"),
}

SRC = {
    "pop": ("INEI, proyecciones de población (SIRTOD 262234)",
            "INEI population projections (SIRTOD 262234)"),
    "canon": ("MEF, transferencias de canon a municipalidades (SIRTOD)",
              "MEF canon transfers to municipalities (SIRTOD)"),
    "siaf": ("MEF, Consulta Amigable / SIAF, gobiernos locales (SIRTOD)",
             "MEF SIAF budget execution, local governments (SIRTOD)"),
    "renamu": ("INEI, Registro Nacional de Municipalidades - RENAMU (SIRTOD)",
               "INEI National Registry of Municipalities - RENAMU (SIRTOD)"),
}

CAVEAT_CANON = ("Desde 2004: antes de la reforma de 2004 la cobertura y los montos no son comparables. "
                "El canon de 2025 aún no está disponible en SIRTOD.",
                "From 2004: before the 2004 reform coverage and amounts are not comparable. "
                "2025 canon is not yet available in SIRTOD.")
CAVEAT_SIAF = ("Desde 2008: en 2007 SIAF cubre solo 40 de 108 distritos.",
               "From 2008: in 2007 SIAF covers only 40 of 108 districts.")
CAVEAT_RENAMU = ("Se excluye 2023: ese año RENAMU es inconsistente en casi todos los distritos (gasto ~23% sobre SIAF, "
                 "ingresos ~2,4 veces los de 2022 y 2024).",
                 "2023 is excluded: that year RENAMU is inconsistent in almost every district (spending ~23% above SIAF, "
                 "revenue ~2.4 times its 2022 and 2024 levels).")
RENAMU_BAD_YEARS = [2023]

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
    dict(id="canon_total", kind="sum", col="canon_total", cat="canon", years=(2004, 2024),
         pc=True, map=True, src="canon", codes="407245",
         label=("Canon transferido a municipalidades", "Canon transferred to municipalities"),
         desc=("Suma de todos los tipos de canon (minero, gasífero, hidroenergético, forestal, petrolero, pesquero) transferidos a la municipalidad.",
               "Sum of all canon types (mining, gas, hydropower, forestry, oil, fishing) transferred to the municipality."),
         caveat=CAVEAT_CANON),
    dict(id="canon_gas", kind="sum", col="canon_gas", cat="canon", years=(2004, 2024),
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
         caveat=("Desde 2005: en 2003-2004 casi ningún distrito registra canon minero. "
                 "El canon de 2025 aún no está disponible en SIRTOD.",
                 "From 2005: in 2003-2004 almost no district records mining canon. "
                 "2025 canon is not yet available in SIRTOD.")),
    dict(id="canon_hydro", kind="sum", col="canon_hydro", cat="canon", years=(2005, 2024),
         pc=True, map=False, src="canon", codes="407248",
         label=("Canon hidroenergético", "Hydropower canon"),
         desc=("Canon hidroenergético transferido a la municipalidad.",
               "Hydropower canon transferred to the municipality."),
         caveat=CAVEAT_CANON),
    dict(id="canon_forest", kind="sum", col="canon_forest", cat="canon", years=(2004, 2024),
         pc=True, map=False, src="canon", codes="407246",
         label=("Canon forestal", "Forestry canon"),
         desc=("Canon forestal transferido a la municipalidad. Montos muy pequeños.",
               "Forestry canon transferred to the municipality. Very small amounts."),
         caveat=CAVEAT_CANON),
    dict(id="foncomun", kind="sum", col="foncomun", cat="transfers", years=(2009, LAST_YEAR),
         pc=True, map=True, src="canon", codes="414062",
         label=("Fondo de Compensación Municipal (FONCOMUN)", "Municipal Compensation Fund (FONCOMUN)"),
         desc=("Transferencia del FONCOMUN a la municipalidad.",
               "FONCOMUN transfer to the municipality."),
         caveat=("SIRTOD lo rotula en miles de soles, pero los valores ya están en soles.",
                 "SIRTOD labels it in thousands of soles, but the values are already in soles.")),
    dict(id="siaf_pia", kind="sum", col="siaf_pia", cat="budget", years=(2008, LAST_YEAR),
         pc=True, map=False, src="siaf", codes="516869",
         label=("Presupuesto Institucional de Apertura (PIA)", "Initial approved budget (PIA)"),
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
         label=("Gasto ejecutado (devengado)", "Spending executed (accrued)"),
         desc=("Gasto devengado: obligaciones de pago reconocidas en el año.",
               "Accrued spending: payment obligations recognised during the year."),
         caveat=CAVEAT_SIAF),
    dict(id="siaf_exec_rate", kind="ratio", num="siaf_accrued", den="siaf_pim", cat="budget",
         years=(2008, LAST_YEAR), pc=False, map=True, src="siaf", codes="516872 / 516870",
         label=("Avance de ejecución presupuestal", "Budget execution rate"),
         desc=("Gasto devengado como porcentaje del PIM. En agregados es devengado total / PIM total.",
               "Accrued spending as a percentage of the modified budget (PIM). Aggregates are total accrued / total PIM."),
         caveat=CAVEAT_SIAF),
    dict(id="renamu_rev_total", kind="sum", col="renamu_rev_total", cat="finance", years=(2004, LAST_YEAR),
         pc=True, map=False, src="renamu", codes="122042", exclude=RENAMU_BAD_YEARS,
         label=("Ingresos recaudados", "Revenue collected"),
         desc=("Ingreso total recaudado por la municipalidad (corrientes, de capital, financiamiento y transferencias).",
               "Total revenue collected by the municipality (current, capital, financing and transfers)."),
         caveat=CAVEAT_RENAMU),
    dict(id="renamu_rev_transfers", kind="sum", col="renamu_rev_transfers", cat="finance", years=(2004, LAST_YEAR),
         pc=True, map=False, src="renamu", codes="122046", exclude=RENAMU_BAD_YEARS,
         label=("Ingresos por transferencias", "Transfer revenue"),
         desc=("Ingresos de la municipalidad provenientes de transferencias (canon, FONCOMUN, otros).",
               "Municipal revenue from transfers (canon, FONCOMUN, others)."),
         caveat=CAVEAT_RENAMU),
    dict(id="renamu_exp_current", kind="sum", col="renamu_exp_current", cat="finance", years=(2004, LAST_YEAR),
         pc=True, map=False, src="renamu", codes="122048", exclude=RENAMU_BAD_YEARS,
         label=("Gasto corriente", "Current spending"),
         desc=("Gasto corriente ejecutado: personal, bienes y servicios, otros gastos corrientes.",
               "Current spending executed: staff, goods and services, other current spending."),
         caveat=CAVEAT_RENAMU),
    dict(id="renamu_exp_capital", kind="sum", col="renamu_exp_capital", cat="finance", years=(2004, LAST_YEAR),
         pc=True, map=True, src="renamu", codes="122049", exclude=RENAMU_BAD_YEARS,
         label=("Gasto de capital", "Capital spending"),
         desc=("Gasto de capital ejecutado, principalmente inversión pública (obras).",
               "Capital spending executed, mainly public investment (works)."),
         caveat=CAVEAT_RENAMU),
    dict(id="capital_share", kind="ratio", num="renamu_exp_capital", den="renamu_exp_total", cat="finance",
         years=(2004, LAST_YEAR), pc=False, map=True, src="renamu", codes="122049 / 122047", exclude=RENAMU_BAD_YEARS,
         label=("Participación del gasto de capital", "Capital share of spending"),
         desc=("Gasto de capital como porcentaje del gasto total ejecutado.",
               "Capital spending as a percentage of total spending executed."),
         caveat=CAVEAT_RENAMU),
    dict(id="transfers_share", kind="ratio", num="renamu_rev_transfers", den="renamu_rev_total", cat="finance",
         years=(2004, LAST_YEAR), pc=False, map=True, src="renamu", codes="122046 / 122042", exclude=RENAMU_BAD_YEARS,
         label=("Dependencia de transferencias", "Dependence on transfers"),
         desc=("Ingresos por transferencias como porcentaje del ingreso total recaudado.",
               "Transfer revenue as a percentage of total revenue collected."),
         caveat=CAVEAT_RENAMU),
    dict(id="canon_dependence", kind="ratio", num="canon_total", den="siaf_accrued", cat="canon",
         years=(2008, 2024), pc=False, map=True, src="canon", codes="407245 / 516872",
         label=("Canon como porcentaje del gasto", "Canon as a share of spending"),
         desc=("Canon transferido en el año como porcentaje del gasto devengado del mismo año.",
               "Canon transferred in the year as a percentage of accrued spending in the same year."),
         caveat=("Puede superar 100%: el canon de un año suele gastarse en años posteriores.",
                 "Can exceed 100%: canon received in one year is often spent in later years.")),
]

UNITS = {
    ("money", "total"): ("Soles corrientes", "Current soles"),
    ("money", "per_capita"): ("Soles corrientes por habitante", "Current soles per person"),
    ("money", "total_real"): (f"Soles de {REAL_BASE_YEAR}", f"{REAL_BASE_YEAR} soles"),
    ("money", "per_capita_real"): (f"Soles de {REAL_BASE_YEAR} por habitante", f"{REAL_BASE_YEAR} soles per person"),
    ("people", "total"): ("Personas", "People"),
    ("ratio", "pct"): ("Porcentaje (%)", "Percent (%)"),
}
MEASURE_LABEL = {
    "total": ("Total", "Total"),
    "per_capita": ("Por habitante", "Per person"),
    "total_real": ("Total, en términos reales", "Total, real terms"),
    "per_capita_real": ("Por habitante, en términos reales", "Per person, real terms"),
    "pct": ("Porcentaje", "Percent"),
}


def load_cpi():
    if not CPI_FILE.exists():
        return None
    cpi = pd.read_csv(CPI_FILE).set_index("year")["cpi"]
    return cpi[REAL_BASE_YEAR] / cpi


def aggregate(df, keys, v):
    """Aggregate one variable from districts to the groups in `keys`."""
    pop = df["pop_spliced"].fillna(0)
    exists = df["exists"]
    if v["kind"] == "sum":
        rep = exists & df[v["col"]].notna()
        g = df.assign(_v=df[v["col"]].where(rep), _rep=rep, _ex=exists,
                      _prep=pop.where(rep, 0), _pex=pop.where(exists, 0))
        out = g.groupby(keys).agg(total=("_v", lambda s: s.sum(min_count=1)), n_reporting=("_rep", "sum"),
                                  n_districts=("_ex", "sum"), pop_rep=("_prep", "sum"), pop_ex=("_pex", "sum"))
        out["per_capita"] = out.total / out.pop_rep.replace(0, np.nan)
    else:
        rep = exists & df[v["num"]].notna() & df[v["den"]].notna()
        g = df.assign(_n=df[v["num"]].where(rep), _d=df[v["den"]].where(rep), _rep=rep, _ex=exists,
                      _prep=pop.where(rep, 0), _pex=pop.where(exists, 0))
        out = g.groupby(keys).agg(num=("_n", lambda s: s.sum(min_count=1)), den=("_d", lambda s: s.sum(min_count=1)),
                                  n_reporting=("_rep", "sum"), n_districts=("_ex", "sum"),
                                  pop_rep=("_prep", "sum"), pop_ex=("_pex", "sum"))
        out["pct"] = 100 * out.num / out.den.replace(0, np.nan)
    out["pop_coverage"] = out.pop_rep / out.pop_ex.replace(0, np.nan)
    return out.reset_index()


def main() -> None:
    p = pd.read_csv(PANEL, dtype={"ubigeo": str})
    p = p[p.year <= LAST_YEAR].copy()
    p["prov_code"] = p.ubigeo.str[:4]
    p["dept_code"] = "08"
    p["exists"] = p.year >= p.first_year_in_data
    deflator = load_cpi()

    rows = []
    for v in VARS:
        y0, y1 = v["years"]
        measures = ["pct"] if v["kind"] == "ratio" else (["total", "per_capita"] if v["pc"] else ["total"])

        # District level
        d = p[p.exists].copy()
        if v["kind"] == "sum":
            d["total"] = d[v["col"]]
            d["per_capita"] = d[v["col"]] / d["pop_spliced"]
            # per-capita values for the La Convencion split block in 2015-2017 are unreliable
            d.loc[d.pop_boundary_mismatch == 1, "per_capita"] = np.nan
            ok = d[v["col"]].notna()
        else:
            d["pct"] = 100 * d[v["num"]] / d[v["den"]].replace(0, np.nan)
            ok = d["pct"].notna()
        d = d[ok]
        d = d.assign(level="district", geo_code=d.ubigeo, geo_name=d.district,
                     n_reporting=1, n_districts=1, pop_coverage=1.0)
        frames = [d]

        # Province and department levels
        for level, code_col, name_map in [
            ("province", "prov_code", p.groupby("prov_code").province.first()),
            ("department", "dept_code", pd.Series({"08": "CUSCO"})),
        ]:
            a = aggregate(p, [code_col, "year"], v).rename(columns={code_col: "geo_code"})
            a["level"] = level
            a["geo_name"] = a.geo_code.map(name_map)
            a["province"] = a.geo_name if level == "province" else ""
            frames.append(a)

        for f in frames:
            for m in measures:
                if m not in f:
                    continue
                part = f[["level", "geo_code", "geo_name", "province", "year",
                          "n_reporting", "n_districts", "pop_coverage"]].copy()
                part["variable"], part["measure"], part["value"] = v["id"], m, f[m].values
                part = part[part.value.notna()]
                in_window = part.year.between(y0, y1) & ~part.year.isin(v.get("exclude", []))
                covered = (part.pop_coverage >= COVERAGE_MIN) | (part.level == "district")
                part["display"] = (in_window & covered).astype(int)
                rows.append(part)
                if deflator is not None and v["kind"] == "sum" and v["id"] != "pop":
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
    long["value"] = np.where(long.measure.isin(["total", "total_real"]) & (long.variable != "pop"),
                             long.value.round(0), long.value.round(4))
    cols = ["level", "geo_code", "geo_name", "province", "year", "variable", "measure",
            "value", "n_reporting", "n_districts", "pop_coverage", "display"]
    long[cols].to_csv(OUT_LONG, index=False, encoding="utf-8")

    # Dictionary: one row per variable x measure
    drows = []
    for i, v in enumerate(VARS):
        kind = "ratio" if v["kind"] == "ratio" else ("people" if v["id"] == "pop" else "money")
        measures = ["pct"] if kind == "ratio" else (["total", "per_capita"] if v["pc"] else ["total"])
        if deflator is not None and kind == "money":
            measures += [m + "_real" for m in measures]
        for m in measures:
            sub = long[(long.variable == v["id"]) & (long.measure == m) & (long.display == 1)]
            dep = sub[sub.level == "department"]
            drows.append({
                "variable": v["id"], "measure": m, "sort_order": i,
                "category_es": CAT[v["cat"]][0], "category_en": CAT[v["cat"]][1],
                "label_es": v["label"][0], "label_en": v["label"][1],
                "measure_es": MEASURE_LABEL[m][0], "measure_en": MEASURE_LABEL[m][1],
                "unit_es": UNITS[(kind, m)][0], "unit_en": UNITS[(kind, m)][1],
                "description_es": v["desc"][0], "description_en": v["desc"][1],
                "caveat_es": v["caveat"][0], "caveat_en": v["caveat"][1],
                "source_es": SRC[v["src"]][0], "source_en": SRC[v["src"]][1],
                "sirtod_codes": v["codes"],
                "aggregation": "ratio_of_sums" if kind == "ratio" else ("sum_over_population" if m.startswith("per_capita") else "sum"),
                "display_from": int(dep.year.min()) if len(dep) else None,
                "display_to": int(dep.year.max()) if len(dep) else None,
                "map_recommended": int(v["map"] and m in ("per_capita", "pct", "per_capita_real")),
            })
    pd.DataFrame(drows).to_csv(OUT_DICT, index=False, encoding="utf-8")

    shown = long[long.display == 1]
    print(f"wrote {len(long):,} rows ({len(shown):,} displayable), "
          f"{long.variable.nunique()} variables, {len(drows)} variable x measure series; "
          f"real values: {'yes' if deflator is not None else 'no (no CPI file)'}")


if __name__ == "__main__":
    main()
