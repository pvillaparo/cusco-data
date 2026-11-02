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
  * Spending: MEF-SIAF budget cycle (516869-516874) and MEF public-accounts
    (DNCP) municipal revenues and spending by economic category (122042-122050,
    variables munfin_*). FONCOMUN (414062).
  * Inputs: the district workbooks 04a-04d, the UBIGEO sheet of the guide (01)
    and the department workbook (02, population only).
  * All money in nominal soles. munfin_* is reported in thousands and is
    multiplied by 1,000; FONCOMUN is labelled thousands in SIRTOD but its values
    are already in soles. Per-capita versions divide by `pop_spliced`, which
    joins INEI's 2007-Census and 2017-Census projection vintages (see
    splice_population). No deflator here: money stays in current soles and
    `cpi_index` is left empty; constant 2024 soles are added in harmonized/
    (build_cpi.py + build_harmonized.py, from 2010).
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
    # Alternative-series components, used only to fill gaps in the main series
    "414081": ("_alt_canon_forest", 1, ""),
    "414082": ("_alt_canon_gas", 1, ""),
    "414083": ("_alt_canon_hydro", 1, ""),
    "414084": ("_alt_canon_mining", 1, ""),
    "414085": ("_alt_canon_fishing", 1, ""),
    "414087": ("_alt_canon_oil", 1, ""),
    "414088": ("_alt_sobrecanon_oil", 1, ""),
    # Other transfers
    "414062": ("foncomun", 1, "FONCOMUN transferred (S/)"),  # labelled thousands, values in soles
    # MEF-SIAF budget cycle (soles)
    "516869": ("siaf_pia", 1, "SIAF opening budget PIA (S/)"),
    "516870": ("siaf_pim", 1, "SIAF modified budget PIM (S/)"),
    "516871": ("siaf_commit", 1, "SIAF committed spending (S/)"),
    "516872": ("siaf_accrued", 1, "SIAF accrued spending, devengado (S/)"),
    "516873": ("siaf_paid", 1, "SIAF paid spending, girado (S/)"),
    "516874": ("siaf_exec_rate", 1, "SIAF execution rate, devengado/PIM (%)"),
    # Municipal finances, MEF public accounts (DNCP) (thousands of soles -> soles)
    "122042": ("munfin_rev_total", 1000, "Municipal revenue collected, total (S/)"),
    "122043": ("munfin_rev_current", 1000, "Municipal current revenue (S/)"),
    "122044": ("munfin_rev_capital", 1000, "Municipal capital revenue (S/)"),
    "122045": ("munfin_rev_financing", 1000, "Municipal financing revenue (S/)"),
    "122046": ("munfin_rev_transfers", 1000, "Municipal transfer revenue (S/)"),
    "122047": ("munfin_exp_total", 1000, "Municipal spending executed, total (S/)"),
    "122048": ("munfin_exp_current", 1000, "Municipal current spending (S/)"),
    "122049": ("munfin_exp_capital", 1000, "Municipal capital spending (S/)"),
    "122050": ("munfin_exp_debt", 1000, "Municipal debt service (S/)"),
    # Population
    "262234": ("pop_proj", 1, "INEI projected population (persons)"),
}

CANON_COMPONENTS = [
    "canon_mining", "canon_gas", "canon_hydro", "canon_forest",
    "canon_oil", "canon_fishing",
]

PER_CAPITA = [
    "canon_total", "canon_mining", "canon_gas", "canon_hydro", "foncomun",
    "siaf_pim", "siaf_accrued", "munfin_rev_transfers",
    "munfin_exp_total", "munfin_exp_current", "munfin_exp_capital",
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

# Population vintages. INEI's district projections based on the 2007 Census
# run to 2015; those based on the 2017 Census start in 2018 at district level
# (2016-2017 are missing in SIRTOD) and in 2016 at department level.
OLD_LAST, NEW_FIRST_DEPT, NEW_FIRST_DIST, TREND_FROM = 2015, 2016, 2018, 2010
# Districts created in La Convencion before 2018 and the parents whose territory
# they came from. Each parent is spliced together with its children, because
# the old-vintage parent population covered the children's territory too.
# Megantoni <- Echarate is documented (2016 law); the other links are inferred
# from population drops that coincide with each new district's entry.
SPLIT_FAMILIES = {
    "080902": ["080914"],             # Echarate -> Megantoni (2017)
    "080909": ["080911", "080912"],   # Vilcabamba -> Inkawasi, Villa Virgen (2015)
    "080907": ["080913"],             # Kimbiri -> Villa Kintiarina (2016), inferred
}
FAMILY_OF = {u: p for p, kids in SPLIT_FAMILIES.items() for u in [p] + kids}
SPLIT_CHILDREN = {u for kids in SPLIT_FAMILIES.values() for u in kids}


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


def load_dept_population() -> pd.Series:
    dep = pd.read_excel(SIRTOD / "02_SIRTOD_Cusco_anual_departamento.xlsx",
                        sheet_name="Datos", header=5, dtype={"Código indicador": str})
    s = dep.loc[dep["Código indicador"] == "262234"].set_index("Año")["Valor numérico"]
    return s.sort_index()


def splice_population(panel: pd.DataFrame, dept: pd.Series) -> pd.DataFrame:
    """Splice the 2007-Census and 2017-Census projection vintages.

    Standard backward splice: the new vintage is kept as published, and the old
    vintage is rescaled so that, extrapolated forward with its own 2010-2015
    growth rate, it meets the new vintage's first year. Year-to-year changes of
    the old series are preserved; only its level moves.
      1. Department: old 1995-2015 rescaled to meet new 2016.
      2. Districts: old 2001-2015 rescaled to meet new 2018, one factor per
         district; a parent that lost territory to a district created before
         2018 is matched against the 2018 total of parent + children.
      3. 2016-2017 at district level: geometric interpolation between the
         spliced 2015 and published 2018 values. For split families the family
         total is interpolated and allocated by 2018 shares; a child that does
         not exist yet leaves its share with the parent.
      4. Every year, districts are rescaled to add up to the spliced department.
         Because the department is anchored in 2016 and districts in 2018, this
         common factor (0.98-0.99 before 2018) adds ~0.8 pp to district growth
         in 2017-2018.
    """
    years = sorted(panel.year.unique())
    first_year = panel.groupby("ubigeo")["first_year_in_data"].first()

    # 1. Department
    g_dep = (dept[OLD_LAST] / dept[TREND_FROM]) ** (1 / (OLD_LAST - TREND_FROM))
    f_dep = dept[NEW_FIRST_DEPT] / (dept[OLD_LAST] * g_dep ** (NEW_FIRST_DEPT - OLD_LAST))
    dept_sp = dept.copy()
    dept_sp[dept_sp.index <= OLD_LAST] *= f_dep

    # 2. Districts, old vintage
    pop = panel.pivot(index="ubigeo", columns="year", values="pop_proj").reindex(columns=years)
    group = pd.Series([FAMILY_OF.get(u, u) for u in pop.index], index=pop.index)
    gsum = pop.groupby(group).sum(min_count=1)
    g = (gsum[OLD_LAST] / gsum[TREND_FROM]) ** (1 / (OLD_LAST - TREND_FROM))
    f = gsum[NEW_FIRST_DIST] / (gsum[OLD_LAST] * g ** (NEW_FIRST_DIST - OLD_LAST))
    sp = pop.copy()
    old_cols = [y for y in years if y <= OLD_LAST]
    sp[old_cols] = pop[old_cols].mul(group.map(f), axis=0)

    # 3. 2016-2017
    gap_years = [y for y in years if OLD_LAST < y < NEW_FIRST_DIST]
    span = NEW_FIRST_DIST - OLD_LAST
    single = ~pop.index.isin(FAMILY_OF)
    for y in gap_years:
        w = (y - OLD_LAST) / span
        sp.loc[single, y] = sp.loc[single, OLD_LAST] * (
            pop.loc[single, NEW_FIRST_DIST] / sp.loc[single, OLD_LAST]) ** w
        for parent, kids in SPLIT_FAMILIES.items():
            members = [parent] + kids
            t0 = sp.loc[members, OLD_LAST].sum()
            t1 = pop.loc[members, NEW_FIRST_DIST].sum()
            total = t0 * (t1 / t0) ** w
            shares = pop.loc[members, NEW_FIRST_DIST].copy()
            for k in kids:
                if first_year.get(k, 9999) > y:      # child not created yet
                    shares[parent] += shares[k]
                    shares[k] = np.nan
            sp.loc[members, y] = total * shares / shares.sum()

    # 4. Rake to the spliced department total
    for y in years:
        s = sp[y].sum(min_count=1)
        if pd.notna(s) and y in dept_sp.index:
            sp[y] *= dept_sp[y] / s

    out = sp.stack().rename("pop_spliced").reset_index()
    out["pop_spliced"] = out.pop_spliced.round(1)
    has = out.pop_spliced.notna()
    out["pop_backcast"] = ((out.year <= OLD_LAST) & has).astype(int)
    out["pop_interpolated"] = (out.year.isin(gap_years) & has).astype(int)
    out["pop_boundary_mismatch"] = (out.ubigeo.isin(FAMILY_OF)
                                    & out.year.between(OLD_LAST, NEW_FIRST_DIST - 1)).astype(int)
    return out


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

    # Fill gaps in the main canon series from the alternative series, which is
    # identical to it outside the two capitals (e.g. the four districts created
    # in 2021 have no 407245 values in 2021-2022 but do have 414080).
    fill = (panel["canon_total"].isna() & panel["canon_total_alt"].notna()
            & ~panel.ubigeo.isin(CAPITALS_ALT_DIFFERS))
    panel["canon_filled_from_alt"] = fill.astype(int)
    panel.loc[fill, "canon_total"] = panel.loc[fill, "canon_total_alt"]
    for c in CANON_COMPONENTS + ["sobrecanon_oil"]:
        panel.loc[fill, c] = panel.loc[fill, f"_alt_{c}"]
    # 414084 (mining) is blank in those rows; the residual matches the
    # department-tier mining share, so mining is taken as total minus the rest.
    others = [c for c in CANON_COMPONENTS + ["sobrecanon_oil"] if c != "canon_mining"]
    resid = panel["canon_total"] - panel[others].fillna(0).sum(axis=1)
    miss_min = fill & panel["canon_mining"].isna()
    panel.loc[miss_min, "canon_mining"] = resid[miss_min]
    if fill.any():
        print(f"note: canon filled from alternative series in {fill.sum()} rows (flagged)")
    panel = panel.drop(columns=[c for c in panel if c.startswith("_alt_")])
    names = {k: v for k, v in names.items() if not v.startswith("_alt_")}

    # Canon components: total = sum of components exactly, so missing -> 0
    has_total = panel["canon_total"].notna()
    for c in CANON_COMPONENTS + ["sobrecanon_oil"]:
        panel.loc[has_total & panel[c].isna(), c] = 0.0
    gap = panel["canon_total"] - panel[CANON_COMPONENTS + ["sobrecanon_oil"]].sum(axis=1, min_count=1)
    bad = has_total & (gap.abs() > 5)  # tolerance for 1-2 sol rounding
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

    # Public-accounts vs SIAF consistency flag (both measure accrued spending)
    ratio = panel["munfin_exp_total"] / panel["siaf_accrued"]
    panel["munfin_siaf_gap"] = np.where(ratio.notna(), ((ratio - 1).abs() > 0.05).astype(float), np.nan)

    # Population: splice INEI's two projection vintages into one series
    panel = panel.sort_values(["ubigeo", "year"]).reset_index(drop=True)
    spliced = splice_population(panel, load_dept_population())
    panel = panel.merge(spliced, on=["ubigeo", "year"], how="left")

    for v in PER_CAPITA:
        panel[f"{v}_pc"] = panel[v] / panel["pop_spliced"]

    panel["cpi_index"] = np.nan  # placeholder: deflator not available in repo

    id_cols = ["ubigeo", "province", "district", "year"]
    flag_cols = ["first_year_in_data", "new_district", "boundary_change_parent",
                 "capital_district", "canon_alt_differs", "canon_filled_from_alt",
                 "canon_pre2004", "canon_components_incomplete",
                 "partial_year", "munfin_siaf_gap", "pop_backcast",
                 "pop_interpolated", "pop_boundary_mismatch"]
    money = [v for v in names.values() if v != "pop_proj"]
    pc = [f"{v}_pc" for v in PER_CAPITA]
    panel = panel[id_cols + money + ["pop_proj", "pop_spliced"] + pc + ["cpi_index"] + flag_cols]

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
        "canon_filled_from_alt": "Canon taken from alternative series 414080 (=1)",
        "partial_year": "Partial year, 2026 (=1)",
        "munfin_siaf_gap": "munfin total spending differs from SIAF by >5% (=1)",
        "pop_spliced": "Population, INEI vintages spliced (persons)",
        "pop_backcast": "pop_spliced is old vintage rescaled, year<=2015 (=1)",
        "pop_interpolated": "pop_spliced interpolated, 2016-2017 (=1)",
        "pop_boundary_mismatch": "Split family, 2015-2017: population allocated approx. (=1)",
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
