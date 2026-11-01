"""
Formula-based (shift-share) instrument for canon gasifero, Cusco districts.

Run after build_canon_spending_panel.py, from the repository root:

    python panels/build_gas_canon_instrument.py

Logic
-----
Each year the Camisea gas canon (50% of royalties and income tax paid by the
concession holders) is split by law into tiers: 10% to the producing district,
25% to the municipalities of the producing province (La Convencion), 40% to all
municipalities of the department and 25% to the regional government and
universities. Inside the provincial and departmental tiers, money is allocated
with MEF indices built from population and poverty (NBI / infrastructure gaps).
In the data, the municipal pool is 75% of the total (GORE/municipal = 0.333 in
2007-2011) and the tier shares are flat from 2007 to 2015.

So district d's gas canon is  canon_gas_dt = s_dt * M_t,  where M_t is the pool
going to all Cusco municipalities and s_dt is d's formula share. The share moves
when MEF updates its indices with new population and poverty data, and those
updates can be endogenous (population growth responds to the local economy,
including canon-funded spending). The instrument freezes the share in a base
period and lets only the department-wide pool move:

    gas_iv_dt = s_d,base * M_t

Variants
--------
gas_iv          base shares = mean 2007-2009 (pre-boom, post-2004 formula, pre-splits)
gas_iv_loo      same, but the pool excludes the district's own transfer
gas_iv_rebased  2007-2009 shares up to 2019; 2021-2023 shares from 2020 onward,
                after MEF re-indexed on the 2017 Census (re-indexing happens in
                2020-2021; shares are stable again from 2021)
gas_iv_prod     base shares x Cusco gas production (volume only, no price/tax)

Per-capita versions divide by base-period population (mean 2007-2009), so they
are not hit by the 2018 rebasing of INEI projections.
"""

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SIRTOD = HERE.parent / "SIRTOD"
PANEL = HERE / "canon_spending_district_year.csv"
OUT_STEM = HERE / "gas_canon_instrument_district_year"

BASE_YEARS = [2007, 2008, 2009]
REBASE_YEARS = [2021, 2022, 2023]
REINDEX_FIRST_YEAR = 2020

PRODUCING_BASE = {"080902"}          # Echarate (Camisea lots 56/88) in base years
PRODUCING_PROVINCE = "0809"          # La Convencion
BOUNDARY_PARENTS = {"080902", "080909", "080907", "080910"}
SPLIT_YEAR = {"080902": 2016, "080909": 2015, "080907": 2016, "080910": 2016}

PC_OUTCOMES = ["canon_total", "canon_gas", "canon_mining", "siaf_accrued",
               "siaf_pim", "renamu_exp_current", "renamu_exp_capital"]


def load_gas_production() -> pd.DataFrame:
    dep = pd.read_excel(SIRTOD / "02_SIRTOD_Cusco_anual_departamento.xlsx",
                        sheet_name="Datos", header=5, dtype={"Código indicador": str})
    keep = {"362136": "gas_prod_mcf", "362138": "ngl_prod_bbl"}
    dep = dep[dep["Código indicador"].isin(keep)]
    out = dep.pivot_table(index="Año", columns="Código indicador", values="Valor numérico")
    return out.rename(columns=keep).rename_axis("year").reset_index()


def main() -> None:
    p = pd.read_csv(PANEL, dtype={"ubigeo": str})
    p = p[["ubigeo", "province", "district", "year", "pop_proj", "new_district",
           "first_year_in_data"] + PC_OUTCOMES].copy()

    # Shift: pool of gas canon to all Cusco municipalities (all districts, incl. new ones)
    pool = p.groupby("year")["canon_gas"].sum(min_count=1).rename("gas_pool_muni")
    p = p.merge(pool, on="year", how="left").merge(load_gas_production(), on="year", how="left")
    p["gas_share_actual"] = p["canon_gas"] / p["gas_pool_muni"]

    # Shares and population in the base period
    def period_mean(col, years):
        return p[p.year.isin(years)].groupby("ubigeo")[col].mean()

    p["gas_share_base"] = p.ubigeo.map(period_mean("gas_share_actual", BASE_YEARS))
    p["gas_share_rebase"] = p.ubigeo.map(period_mean("gas_share_actual", REBASE_YEARS))
    p["pop_base"] = p.ubigeo.map(period_mean("pop_proj", BASE_YEARS))

    # Instruments
    p["gas_iv"] = p.gas_share_base * p.gas_pool_muni
    own = p.canon_gas.fillna(0)
    p["gas_iv_loo"] = p.gas_share_base / (1 - p.gas_share_base) * (p.gas_pool_muni - own)
    p.loc[p.gas_pool_muni.isna(), "gas_iv_loo"] = np.nan
    share_rb = np.where(p.year >= REINDEX_FIRST_YEAR, p.gas_share_rebase, p.gas_share_base)
    p["gas_iv_rebased"] = share_rb * p.gas_pool_muni
    p["gas_iv_prod"] = p.gas_share_base * p.gas_prod_mcf

    for v in ["gas_iv", "gas_iv_loo", "gas_iv_rebased"]:
        p[f"{v}_pc"] = p[v] / p.pop_base
    for v in PC_OUTCOMES:
        p[f"{v}_pcb"] = p[v] / p.pop_base

    # Formula tier in the base period
    p["tier_base"] = np.select(
        [p.ubigeo.isin(PRODUCING_BASE), p.ubigeo.str[:4] == PRODUCING_PROVINCE],
        ["producing_district", "producing_province"], "department")
    p.loc[p.gas_share_base.isna(), "tier_base"] = ""

    # Sample flags
    split = p.ubigeo.map(SPLIT_YEAR)
    boundary_ok = ~(p.ubigeo.isin(BOUNDARY_PARENTS) & (p.year >= split))
    p["iv_sample"] = (p.gas_share_base.notna() & (p.new_district == 0) & boundary_ok
                      & p.canon_gas.notna() & p.year.between(2008, 2024)).astype(int)
    p["reindex_period"] = (p.year >= REINDEX_FIRST_YEAR).astype(int)
    p["base_overlap"] = p.year.isin(BASE_YEARS).astype(int)

    cols = ["ubigeo", "province", "district", "year",
            "gas_pool_muni", "gas_prod_mcf", "ngl_prod_bbl",
            "gas_share_actual", "gas_share_base", "gas_share_rebase", "tier_base", "pop_base",
            "gas_iv", "gas_iv_loo", "gas_iv_rebased", "gas_iv_prod",
            "gas_iv_pc", "gas_iv_loo_pc", "gas_iv_rebased_pc"] + \
           [f"{v}_pcb" for v in PC_OUTCOMES] + \
           ["iv_sample", "reindex_period", "base_overlap"]
    out = p[cols].sort_values(["ubigeo", "year"])
    out.to_csv(OUT_STEM.with_suffix(".csv"), index=False, encoding="utf-8")

    labels = {
        "ubigeo": "INEI UBIGEO district code (text)", "province": "Province",
        "district": "District", "year": "Year",
        "gas_pool_muni": "Gas canon to all Cusco municipalities, year t (S/)",
        "gas_prod_mcf": "Cusco natural gas production (thousand cubic feet)",
        "ngl_prod_bbl": "Cusco natural gas liquids production (barrels)",
        "gas_share_actual": "District share of municipal gas canon pool, year t",
        "gas_share_base": "District share of gas canon pool, mean 2007-2009",
        "gas_share_rebase": "District share of gas canon pool, mean 2021-2023",
        "tier_base": "Formula tier in base period",
        "pop_base": "Projected population, mean 2007-2009",
        "gas_iv": "IV: base share x municipal gas pool (S/)",
        "gas_iv_loo": "IV: base share x pool excluding own transfer (S/)",
        "gas_iv_rebased": "IV: base share to 2019, 2021-23 share from 2020 (S/)",
        "gas_iv_prod": "IV: base share x Cusco gas production",
        "gas_iv_pc": "gas_iv per base-period capita (S/)",
        "gas_iv_loo_pc": "gas_iv_loo per base-period capita (S/)",
        "gas_iv_rebased_pc": "gas_iv_rebased per base-period capita (S/)",
        "iv_sample": "Recommended estimation sample (=1)",
        "reindex_period": "Year >= 2020, after MEF re-indexing (=1)",
        "base_overlap": "Year is in base period 2007-2009 (=1)",
    }
    labels.update({f"{v}_pcb": f"{v} per base-period capita (S/)" for v in PC_OUTCOMES})
    dta = out.copy()
    for c in ["ubigeo", "province", "district", "tier_base"]:
        dta[c] = dta[c].fillna("").astype(object)
    dta.to_stata(OUT_STEM.with_suffix(".dta"), write_index=False, version=118,
                 variable_labels={k: v[:80] for k, v in labels.items()})
    print(f"wrote {len(out):,} rows; iv_sample = {out.iv_sample.sum():,} district-years, "
          f"{out[out.iv_sample == 1].ubigeo.nunique()} districts")


if __name__ == "__main__":
    main()
