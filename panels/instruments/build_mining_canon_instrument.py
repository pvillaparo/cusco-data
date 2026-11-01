"""
Formula-based instrument for canon minero, Cusco districts, built by source.

Run after build_canon_spending_panel.py, from the repository root:

    python panels/instruments/build_mining_canon_instrument.py

Why not the single-pool gas recipe
----------------------------------
Mining canon in Cusco comes from two sources that switch on at different
times: the Espinar mines (Tintaya, Antapaccay), which generate essentially all
local mining canon in the base period, and Constancia in Chumbivilcas, whose
income-tax payments appear in 2013, 2018-2020 and 2022-2024. A single frozen
share times the total pool would send Constancia's money to Espinar. The
instrument therefore freezes the formula shares *by source and tier*.

Formula and evidence
--------------------
Municipalities receive 75% of mining canon: 40% through a department tier
(all municipalities, population/poverty index), 25% through the producing
province's municipalities, 10% to the producing district(s). In the data:
  * Outside La Convencion, Espinar and Chumbivilcas, base-period mining shares
    are proportional to gas shares (corr 0.994) and the group's mining/gas
    share ratio is ~1.0 every year: the department-tier index is common to
    both canons. So a district's department-tier mining receipt in year t is
    its gas share x the mining pool (La Convencion, which gets gas local
    tiers, is assumed to receive only department-tier mining canon).
  * The remaining "local" money is 35/75 of the pool in every year, and
    comes only from Espinar and Chumbivilcas (other provinces ~ 0).

Pools (shifts), each year t:
    D_t   department-tier mining canon to all municipalities
    LE_t  local mining canon in Espinar province (Espinar-mine tiers)
    LC_t  local mining canon in Chumbivilcas province (Constancia tiers)
Frozen shares (exposures):
    w_d   share of D in 2007-2009
    lE_d  share of LE in 2007-2009 (observed directly)
    lC_d  formula share of LC: (25/35) x d's share of Chumbivilcas department
          weights + (10/35) x d's producing split (Livitaca, Chamaca,
          Velille; mean of their excess receipts 2018-2024)
Instrument:
    mining_iv_dt = w_d * D_t + lE_d * LE_t + lC_d * LC_t
"""

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PANEL = HERE.parent / "canon_spending_district_year.csv"
OUT_STEM = HERE / "mining_canon_instrument_district_year"

BASE_YEARS = [2007, 2008, 2009]
REBASE_YEARS = [2021, 2022, 2023]
REINDEX_FIRST_YEAR = 2020
LC_YEARS = [2018, 2019, 2020, 2022, 2023, 2024]  # years with sizable Constancia canon

ESPINAR, CHUMBIVILCAS, LA_CONVENCION = "0808", "0807", "0809"
CONSTANCIA_DISTRICTS = {"080705": "LIVITACA", "080703": "CHAMACA", "080708": "VELILLE"}
BOUNDARY_PARENTS = {"080902": 2016, "080909": 2015, "080907": 2016, "080910": 2016}

PC_OUTCOMES = ["canon_total", "canon_mining", "canon_gas", "siaf_accrued",
               "siaf_pim", "munfin_exp_current", "munfin_exp_capital"]


def main() -> None:
    p = pd.read_csv(PANEL, dtype={"ubigeo": str})
    p = p[["ubigeo", "province", "district", "year", "pop_proj", "new_district"]
          + PC_OUTCOMES].copy()
    p["prov"] = p.ubigeo.str[:4]

    pool_min = p.groupby("year")["canon_mining"].transform("sum")
    pool_gas = p.groupby("year")["canon_gas"].transform("sum")
    p["mining_pool_muni"] = p.groupby("year")["canon_mining"].transform(
        lambda s: s.sum(min_count=1))

    # Department-tier receipt via the common index; local = remainder
    gas_share = p.canon_gas / pool_gas
    p["mining_dept"] = np.where(p.prov == LA_CONVENCION, p.canon_mining, gas_share * pool_min)
    p["mining_local"] = p.canon_mining - p.mining_dept

    pools = p.groupby("year").apply(lambda g: pd.Series({
        "pool_dept": g.mining_dept.sum(min_count=1),
        "pool_local_espinar": g.loc[g.prov == ESPINAR, "mining_local"].sum(min_count=1),
        "pool_local_chumbivilcas": g.loc[g.prov == CHUMBIVILCAS, "mining_local"].sum(min_count=1),
        "pool_local_other": g.loc[~g.prov.isin([ESPINAR, CHUMBIVILCAS]), "mining_local"].sum(min_count=1),
    }), include_groups=False).reset_index()
    pools.loc[pools.year < 2005, pools.columns[1:]] = np.nan  # pre-2005 data unusable
    p = p.merge(pools, on="year", how="left")

    def shares(years):
        g = p[p.year.isin(years)].groupby("ubigeo")
        dept = g.mining_dept.sum()
        w = dept / dept.sum()
        loc_e = p[p.year.isin(years) & (p.prov == ESPINAR)].groupby("ubigeo").mining_local.sum()
        l_e = (loc_e / loc_e.sum()).reindex(w.index, fill_value=0.0)
        # Constancia: provincial tier proportional to department weights
        chumb = w[w.index.str[:4] == CHUMBIVILCAS]
        prov_part = chumb / chumb.sum()
        l_c = (25 / 35) * prov_part.reindex(w.index, fill_value=0.0) \
            + (10 / 35) * producing_split().reindex(w.index, fill_value=0.0)
        return w, l_e, l_c

    def producing_split():
        c = p[(p.prov == CHUMBIVILCAS) & p.year.isin(LC_YEARS)].copy()
        c["lsh"] = c.mining_local / c.groupby("year").mining_local.transform("sum")
        c["wsh"] = c.mining_dept / c.groupby("year").mining_dept.transform("sum")
        excess = (c.lsh - (25 / 35) * c.wsh).groupby(c.ubigeo).mean()
        excess = excess[excess.index.isin(CONSTANCIA_DISTRICTS)].clip(lower=0)
        return excess / excess.sum()

    w0, le0, lc0 = shares(BASE_YEARS)
    w1, le1, lc1 = shares(REBASE_YEARS)
    p["w_dept_base"], p["l_espinar_base"], p["l_chumb_base"] = (
        p.ubigeo.map(w0), p.ubigeo.map(le0), p.ubigeo.map(lc0))
    p["w_dept_rebase"], p["l_espinar_rebase"], p["l_chumb_rebase"] = (
        p.ubigeo.map(w1), p.ubigeo.map(le1), p.ubigeo.map(lc1))
    p["mining_share_base"] = p.ubigeo.map(
        p[p.year.isin(BASE_YEARS)].assign(s=p.canon_mining / pool_min).groupby("ubigeo").s.mean())

    def iv(w, le, lc):
        return w * p.pool_dept + le * p.pool_local_espinar + lc * p.pool_local_chumbivilcas

    p["mining_iv"] = iv(p.w_dept_base, p.l_espinar_base, p.l_chumb_base)
    post = p.year >= REINDEX_FIRST_YEAR
    p["mining_iv_rebased"] = np.where(
        post, iv(p.w_dept_rebase, p.l_espinar_rebase, p.l_chumb_rebase), p.mining_iv)
    p["mining_iv_naive"] = p.mining_share_base * p.mining_pool_muni
    p.loc[p.year < 2005, "mining_iv_naive"] = np.nan

    p["pop_base"] = p.ubigeo.map(p[p.year.isin(BASE_YEARS)].groupby("ubigeo").pop_proj.mean())
    for v in ["mining_iv", "mining_iv_rebased", "mining_iv_naive"]:
        p[f"{v}_pc"] = p[v] / p.pop_base
    for v in PC_OUTCOMES:
        p[f"{v}_pcb"] = p[v] / p.pop_base

    p["source_exposure"] = np.select(
        [p.ubigeo.isin(CONSTANCIA_DISTRICTS), p.prov == CHUMBIVILCAS, p.prov == ESPINAR],
        ["constancia_producing", "chumbivilcas", "espinar"], "department_only")
    split = p.ubigeo.map(BOUNDARY_PARENTS)
    boundary_ok = ~(p.ubigeo.isin(BOUNDARY_PARENTS) & (p.year >= split))
    p["iv_sample"] = (p.w_dept_base.notna() & (p.new_district == 0) & boundary_ok
                      & p.canon_mining.notna() & p.year.between(2008, 2024)).astype(int)
    p["reindex_period"] = post.astype(int)
    p["base_overlap"] = p.year.isin(BASE_YEARS).astype(int)

    cols = ["ubigeo", "province", "district", "year", "mining_pool_muni", "pool_dept",
            "pool_local_espinar", "pool_local_chumbivilcas", "pool_local_other",
            "mining_dept", "mining_local", "mining_share_base",
            "w_dept_base", "l_espinar_base", "l_chumb_base",
            "w_dept_rebase", "l_espinar_rebase", "l_chumb_rebase",
            "source_exposure", "pop_base",
            "mining_iv", "mining_iv_rebased", "mining_iv_naive",
            "mining_iv_pc", "mining_iv_rebased_pc", "mining_iv_naive_pc"] + \
           [f"{v}_pcb" for v in PC_OUTCOMES] + ["iv_sample", "reindex_period", "base_overlap"]
    out = p[cols].sort_values(["ubigeo", "year"])
    out.to_csv(OUT_STEM.with_suffix(".csv"), index=False, encoding="utf-8")

    labels = {
        "ubigeo": "INEI UBIGEO district code (text)", "province": "Province",
        "district": "District", "year": "Year",
        "mining_pool_muni": "Mining canon to all Cusco municipalities (S/)",
        "pool_dept": "Shift: department-tier mining canon pool (S/)",
        "pool_local_espinar": "Shift: local-tier mining canon in Espinar (S/)",
        "pool_local_chumbivilcas": "Shift: local-tier mining canon in Chumbivilcas (S/)",
        "pool_local_other": "Local-tier residual, other provinces (check, ~0)",
        "mining_dept": "District department-tier mining receipt, year t (S/)",
        "mining_local": "District local-tier mining receipt, year t (S/)",
        "mining_share_base": "District share of mining pool, mean 2007-2009",
        "w_dept_base": "Share of department tier, 2007-2009",
        "l_espinar_base": "Share of Espinar local tier, 2007-2009",
        "l_chumb_base": "Formula share of Chumbivilcas local tier (base weights)",
        "w_dept_rebase": "Share of department tier, 2021-2023",
        "l_espinar_rebase": "Share of Espinar local tier, 2021-2023",
        "l_chumb_rebase": "Formula share of Chumbivilcas local tier (2021-23 weights)",
        "source_exposure": "Which mining sources reach the district beyond dept tier",
        "pop_base": "Projected population, mean 2007-2009",
        "mining_iv": "IV: frozen source-tier shares x source pools (S/)",
        "mining_iv_rebased": "IV: base shares to 2019, 2021-23 shares from 2020 (S/)",
        "mining_iv_naive": "IV: single base share x total pool (comparison) (S/)",
        "mining_iv_pc": "mining_iv per base-period capita (S/)",
        "mining_iv_rebased_pc": "mining_iv_rebased per base-period capita (S/)",
        "mining_iv_naive_pc": "mining_iv_naive per base-period capita (S/)",
        "iv_sample": "Recommended estimation sample (=1)",
        "reindex_period": "Year >= 2020, after MEF re-indexing (=1)",
        "base_overlap": "Year is in base period 2007-2009 (=1)",
    }
    labels.update({f"{v}_pcb": f"{v} per base-period capita (S/)" for v in PC_OUTCOMES})
    dta = out.copy()
    for c in ["ubigeo", "province", "district", "source_exposure"]:
        dta[c] = dta[c].fillna("").astype(object)
    dta.to_stata(OUT_STEM.with_suffix(".dta"), write_index=False, version=118,
                 variable_labels={k: v[:80] for k, v in labels.items()})

    split_c = producing_split()
    print("Constancia producing split:",
          {CONSTANCIA_DISTRICTS[k]: round(v, 3) for k, v in split_c.items()})
    print(f"wrote {len(out):,} rows; iv_sample = {out.iv_sample.sum():,} district-years, "
          f"{out[out.iv_sample == 1].ubigeo.nunique()} districts")


if __name__ == "__main__":
    main()
