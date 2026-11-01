"""
Build a district-year panel of canon transfers and municipal finances for Cusco.

Source: the SIRTOD district workbooks in ../SIRTOD (04a-04d), downloaded from
INEI SIRTOD on 2026-09-22. Run from the repository root or from this folder:

    python panels/build_canon_spending_panel.py

Outputs (written next to this script):
    canon_spending_district_year.csv   UTF-8, one row per district x year
    canon_spending_district_year.dta   Stata 14+ with variable labels

Design choices (see panels/README.md for the reasoning):
  * Canon, main series: SIRTOD 407245 (total) and its components 407246-407251,
    2001-2024. The total equals the sum of components exactly, so a component
    that is missing in a year where the total is observed is set to 0.
  * Canon, check series: 414080 (2014-2024). It matches 407245 everywhere except
    Cusco district (adds the Regional Government's canon) and Santa Ana
    (adds what looks like the provincial-municipality share). Kept as
    canon_total_alt with a flag.
  * Spending: MEF-SIAF budget cycle (516869-516874) and RENAMU revenues and
    spending by economic category (122042-122050). FONCOMUN (414062).
  * All money in nominal soles (RENAMU and FONCOMUN are reported in thousands
    and are multiplied by 1,000). Per-capita versions use INEI projected
    population (262234). No deflator: the CPI in SIRTOD is monthly and the
    monthly files are not in the repository; `cpi_index` is left empty.
  * Boundaries are kept as official; new districts and their parents are flagged.
"""

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SIRTOD = HERE.parent / "SIRTOD"
OUT_STEM = HERE / "canon_spending_district_year"

YEARS = range(2001, 2027)

# SIRTOD code -> (variable name, multiplier to soles, label)
SERIES = {
    # Canon, main series (soles)
    "407245": ("canon_total", 1, "Canon transferred to municipality, total (S/)"),
    "407249": ("canon_mining", 1, "Canon minero transferred (S/)"),
    "407247": ("canon_gas", 1, "Canon gasifero transferred (S/)"),
    "407248": ("canon_hydro", 1, "Canon hidroenergetico transferred (S/)"),
    "407246": ("canon_forest", 1, "Canon forestal transferred (S/)"),
    "407251": ("canon_oil", 1, "Canon petrolero transferred (S/)"),
    "407250": ("canon_fishing", 1, "Canon pesquero transferred (S/)"),
    "417639": ("sobrecanon_oil", 1, "Sobrecanon petrolero transferred (S/)"),
    # Canon, alternative series (soles)
    "414080": ("canon_total_alt", 1, "Canon total, alt. series 414080 (S/)"),
    # Other transfers
    "414062": ("foncomun", 1000, "FONCOMUN transferred (S/)"),
    # MEF-SIAF budget cycle (soles)
    "516869": ("siaf_pia", 1, "SIAF opening budget PIA (S/)"),
    "516870": ("siaf_pim", 1, "SIAF modified budget PIM (S/)"),
    "516871": ("siaf_commit", 1, "SIAF committed spending (S/)"),
    "516872": ("siaf_accrued", 1, "SIAF accrued spending, devengado (S/)"),
    "516873": ("siaf_paid", 1, "SIAF paid spending, girado (S/)"),
    "516874": ("siaf_exec_rate", 1, "SIAF execution rate, devengado/PIM (%)"),
    # RENAMU municipal finances (thousands of soles -> soles)
    "122042": ("renamu_rev_total", 1000, "RENAMU revenue collected, total (S/)"),
    "122043": ("renamu_rev_current", 1000, "RENAMU current revenue (S/)"),
    "122044": ("renamu_rev_capital", 1000, "RENAMU capital revenue (S/)"),
    "122045": ("renamu_rev_financing", 1000, "RENAMU financing revenue (S/)"),
    "122046": ("renamu_rev_transfers", 1000, "RENAMU transfer revenue (S/)"),
    "122047": ("renamu_exp_total", 1000, "RENAMU spending executed, total (S/)"),
    "122048": ("renamu_exp_current", 1000, "RENAMU current spending (S/)"),
    "122049": ("renamu_exp_capital", 1000, "RENAMU capital spending (S/)"),
    "122050": ("renamu_exp_debt", 1000, "RENAMU debt service (S/)"),
    # Population
    "262234": ("pop_proj", 1, "INEI projected population (persons)"),
}

CANON_COMPONENTS = [
    "canon_mining", "canon_gas", "canon_hydro", "canon_forest",
    "canon_oil", "canon_fishing",
]

PER_CAPITA = [
    "canon_total", "canon_mining", "canon_gas", "canon_hydro", "foncomun",
    "siaf_pim", "siaf_accrued", "renamu_rev_transfers",
    "renamu_exp_total", "renamu_exp_current", "renamu_exp_capital",
]

# Districts whose territory shrank when new districts were created. Inferred
# from (i) the year the new districts enter the data and (ii) a contemporaneous
# population drop in the parent that is far larger than the 2017-Census rebasing
# seen elsewhere. Megantoni <- Echarate (2016 law) is documented; the others
# should be verified against the creation laws before relying on them.
BOUNDARY_PARENTS = {
    "080902": "ECHARATE: lost Megantoni (enters 2017) and territory again in 2021",
    "080909": "VILCABAMBA: lost territory when Inkawasi/Villa Virgen enter (2015)",
    "080907": "KIMBIRI: lost territory when 2021 districts enter",
    "080910": "PICHARI: lost territory when 2021 districts enter",
}

CAPITALS_ALT_DIFFERS = {"080101", "080901"}  # Cusco, Santa Ana


def load_district_data() -> pd.DataFrame:
    files = sorted(SIRTOD.glob("04*_SIRTOD_Cusco_anual_distritos.xlsx"))
    if len(files) != 4:
        raise FileNotFoundError(f"Expected 4 district workbooks in {SIRTOD}, found {len(files)}")
    frames = []
    for f in files:
        print(f"reading {f.name} ...", flush=True)
        df = pd.read_excel(
            f, sheet_name="Datos", header=5,
            dtype={"UBIGEO": str, "Código indicador": str, "Valor original": str},
        )
        frames.append(df[df["Código indicador"].isin(SERIES)])
    return pd.concat(frames, ignore_index=True)


def load_ubigeo() -> pd.DataFrame:
    ub = pd.read_excel(SIRTOD / "01_SIRTOD_Cusco_guia.xlsx", sheet_name="UBIGEO",
                       header=4, dtype=str)
    ub = ub[["UBIGEO", "Provincia", "Distrito"]].rename(
        columns={"UBIGEO": "ubigeo", "Provincia": "province", "Distrito": "district"})
    return ub[~ub.ubigeo.str.endswith("99")]  # 080199 is not a real district


def main() -> None:
    raw = load_district_data()

    key = ["Código indicador", "UBIGEO", "Año"]
    if raw.duplicated(key).any():
        raise ValueError("Duplicate indicator x district x year rows in source")
    if raw["Valor numérico"].isna().any():
        raise ValueError("Non-numeric values in selected series")

    names = {c: v[0] for c, v in SERIES.items()}
    mult = {c: v[1] for c, v in SERIES.items()}
    raw["value"] = raw["Valor numérico"] * raw["Código indicador"].map(mult)
    raw["var"] = raw["Código indicador"].map(names)
    long = raw.rename(columns={"UBIGEO": "ubigeo", "Año": "year"})
    wide = long.pivot(index=["ubigeo", "year"], columns="var", values="value")

    # Full district x year frame, restricted to districts that appear in the data
    ub = load_ubigeo()
    ub = ub[ub.ubigeo.isin(long.ubigeo.unique())]
    frame = ub.merge(pd.DataFrame({"year": list(YEARS)}), how="cross")
    panel = frame.merge(wide.reset_index(), on=["ubigeo", "year"], how="left")
    for v in names.values():
        if v not in panel:
            panel[v] = np.nan

    # Canon components: total = sum of components exactly, so missing -> 0
    has_total = panel["canon_total"].notna()
    for c in CANON_COMPONENTS + ["sobrecanon_oil"]:
        panel.loc[has_total & panel[c].isna(), c] = 0.0
    gap = panel["canon_total"] - panel[CANON_COMPONENTS].sum(axis=1, min_count=1)
    bad = has_total & (gap.abs() > 1)
    panel["canon_components_incomplete"] = np.where(has_total, bad.astype(float), np.nan)
    if bad.any():
        print(f"note: canon total != sum of components in {bad.sum()} rows (flagged)")

    # Flags
    first_year = long.groupby("ubigeo")["year"].min()
    panel["first_year_in_data"] = panel.ubigeo.map(first_year)
    panel["new_district"] = (panel.first_year_in_data >= 2011).astype(int)
    panel["boundary_change_parent"] = panel.ubigeo.isin(BOUNDARY_PARENTS).astype(int)
    panel["capital_district"] = panel.ubigeo.str.endswith("01").astype(int)
    panel["canon_alt_differs"] = panel.ubigeo.isin(CAPITALS_ALT_DIFFERS).astype(int)
    panel["canon_pre2004"] = (panel.year < 2004).astype(int)
    panel["partial_year"] = (panel.year >= 2026).astype(int)

    # RENAMU vs SIAF consistency flag (both measure accrued spending)
    ratio = panel["renamu_exp_total"] / panel["siaf_accrued"]
    panel["renamu_siaf_gap"] = np.where(ratio.notna(), ((ratio - 1).abs() > 0.05).astype(float), np.nan)

    # Population: SIRTOD has no 2016-2017 values. Fill interior gaps by
    # geometric interpolation, except for boundary-change parents, and flag.
    panel = panel.sort_values(["ubigeo", "year"]).reset_index(drop=True)
    panel["pop_interpolated"] = 0
    logpop = np.log(panel["pop_proj"])
    filled = logpop.groupby(panel.ubigeo).transform(
        lambda s: s.interpolate(method="linear", limit_area="inside"))
    fill_mask = panel.pop_proj.isna() & filled.notna() & (panel.boundary_change_parent == 0)
    panel.loc[fill_mask, "pop_proj"] = np.exp(filled[fill_mask]).round()
    panel.loc[fill_mask, "pop_interpolated"] = 1
    panel["pop_vintage_2017census"] = (panel.year >= 2018).astype(int)

    for v in PER_CAPITA:
        panel[f"{v}_pc"] = panel[v] / panel["pop_proj"]

    panel["cpi_index"] = np.nan  # placeholder: deflator not available in repo

    id_cols = ["ubigeo", "province", "district", "year"]
    flag_cols = ["first_year_in_data", "new_district", "boundary_change_parent",
                 "capital_district", "canon_alt_differs", "canon_pre2004",
                 "canon_components_incomplete",
                 "partial_year", "renamu_siaf_gap", "pop_interpolated",
                 "pop_vintage_2017census"]
    money = [v for v in names.values() if v != "pop_proj"]
    pc = [f"{v}_pc" for v in PER_CAPITA]
    panel = panel[id_cols + money + ["pop_proj"] + pc + ["cpi_index"] + flag_cols]

    # Drop district-years outside each district's existence and with no data
    allna = panel[money + ["pop_proj"]].isna().all(axis=1)
    panel = panel[~(allna & (panel.year < panel.first_year_in_data))]

    panel.to_csv(OUT_STEM.with_suffix(".csv"), index=False, encoding="utf-8")

    labels = {v[0]: v[2] for v in SERIES.values()}
    labels.update({f"{v}_pc": (labels[v].replace("(S/)", "") + " per capita")[:80] for v in PER_CAPITA})
    labels.update({
        "ubigeo": "INEI UBIGEO district code (text)",
        "province": "Province", "district": "District", "year": "Year",
        "cpi_index": "Deflator placeholder (empty)",
        "first_year_in_data": "First year district appears in SIRTOD",
        "new_district": "District created after 2010 (=1)",
        "boundary_change_parent": "Lost territory to a new district (=1)",
        "capital_district": "Provincial capital district (=1)",
        "canon_alt_differs": "canon_total_alt includes other entities (=1)",
        "canon_pre2004": "Year before 2004 canon regime (=1)",
        "canon_components_incomplete": "Canon components do not sum to total (=1)",
        "partial_year": "Partial year, 2026 (=1)",
        "renamu_siaf_gap": "RENAMU total spending differs from SIAF by >5% (=1)",
        "pop_interpolated": "Population interpolated, 2016-2017 (=1)",
        "pop_vintage_2017census": "Population projection based on 2017 Census (=1)",
    })
    dta = panel.copy()
    for c in ["ubigeo", "province", "district"]:
        dta[c] = dta[c].astype(object)
    dta.to_stata(OUT_STEM.with_suffix(".dta"), write_index=False, version=118,
                 variable_labels={k: v[:80] for k, v in labels.items() if k in dta})

    print(f"wrote {len(panel):,} rows x {panel.shape[1]} columns, "
          f"{panel.ubigeo.nunique()} districts, {panel.year.min()}-{panel.year.max()}")


if __name__ == "__main__":
    main()
