"""
Extract the shortlisted district development indicators into a wide
district-year file, so the shortlist in development_indicators_shortlist.md
can be turned into data once it is approved.

Source: the SIRTOD district workbooks in ../SIRTOD (04a-04d), downloaded from
INEI SIRTOD on 2026-09-22. Run from the repository root or from this folder:

    python panels/extract_development_indicators.py                 # shortlist only
    python panels/extract_development_indicators.py --out my.csv    # other output path
    python panels/extract_development_indicators.py --extra 516459,122103
    python panels/extract_development_indicators.py --only education,crime
    python panels/extract_development_indicators.py --no-fill       # raw SIRTOD values

Reading the four workbooks takes about two minutes. The output is written next
to this script by default (development_indicators_district_year.csv) and can be
merged one-to-one with canon_spending_district_year.csv on (ubigeo, year).

How missing values are treated (the --no-fill switch turns all of this off):

  * RENAMU yes/no indicators ("Municipalidades que ...") are stored in SIRTOD
    only as 1s; a "no" answer is simply absent. They are set to 0 when the
    municipality answered RENAMU that year, which we take to mean it reports
    total staff (121951) or computers (121992) that year. Districts outside
    that universe stay missing, and so do years in which SIRTOD publishes the
    indicator for no district at all (the question was not asked).
  * RENAMU counts of things the municipality may not have (dump trucks,
    serenazgo staff) are filled the same way, because SIRTOD never stores a 0.
  * ECE test-score levels (satisfactory / in process / below) add up to 100.
    When at least one level is published for a district-year, the missing
    levels are set to 0. Districts with no published level stay missing.
  * Structural zeros: SBS credit and deposits and MINEM mining production are
    published only for districts that have a branch or a producing unit. For
    every district that exists in a year in which the indicator is published
    for some district, a missing value is set to 0. Read these as "no branch /
    no production recorded", not as measured zeros.

Suspect cells are blanked by default (use --keep-suspect to keep them):
MINEM 2025 production (an exact copy of 2024 for every producer), the 2015
MTPE firm count (level break: the median falls from 42 to 6 in 2016) and
RENIEC registered deaths in 2020-2022 (regional totals collapse from about
6,800 to 2,600 during COVID, so registration, not mortality, changed).

For every filled variable a companion flag `<var>_filled` (1 = value was set
by a rule above) is written, so the fill can always be undone.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
SIRTOD = HERE.parent / "SIRTOD"
DEFAULT_OUT = HERE / "development_indicators_district_year.csv"

# fill rules
RENAMU = "renamu"         # 0 if the municipality answered RENAMU that year
ECE = "ece"               # 0 if another ECE level is observed for that subject
STRUCT = "structural"     # 0 for any existing district in a published year
NONE = None

# SIRTOD code -> (variable, dimension, fill rule, label)
SHORTLIST = {
    # --- Education (MINEDU ESCALE, school census; UMC for the ECE) ---------
    "411492": ("edu_enrol_ebr", "education", NONE, "Enrolment, regular basic education (EBR), all sectors"),
    "413856": ("edu_enrol_ebr_pub", "education", NONE, "Enrolment, public EBR"),
    "411495": ("edu_enrol_sec", "education", NONE, "Enrolment, EBR secondary, all sectors"),
    "417647": ("edu_teach_ebr_pub", "education", NONE, "Teachers, public EBR"),
    "411521": ("edu_schools_ebr", "education", NONE, "Educational services (schools/programmes), EBR"),
    "420006": ("edu_sch_3services", "education", NONE, "% public school premises with water, sewer and electricity"),
    "394676": ("edu_teach_titled_sec", "education", NONE, "% secondary teachers with a teaching degree"),
    "420549": ("ece_read_satis", "education", ECE, "ECE 2nd grade: % satisfactory, reading"),
    "420550": ("ece_read_process", "education", ECE, "ECE 2nd grade: % in process, reading"),
    "420552": ("ece_read_below", "education", ECE, "ECE 2nd grade: % below level, reading"),
    "420553": ("ece_math_satis", "education", ECE, "ECE 2nd grade: % satisfactory, math"),
    "420554": ("ece_math_process", "education", ECE, "ECE 2nd grade: % in process, math"),
    "420556": ("ece_math_below", "education", ECE, "ECE 2nd grade: % below level, math"),
    # --- Health, nutrition, vital registration and identity ----------------
    "262211": ("vit_births_reg", "health", NONE, "Births registered (RENIEC)"),
    "262226": ("vit_births_late", "health", NONE, "Births registered late (extraordinary route)"),
    "262239": ("vit_deaths_reg", "health", NONE, "Deaths registered (RENIEC)"),
    "424497": ("id_dni_total", "health", NONE, "Population with DNI, by residence"),
    "424508": ("id_dni_minors", "health", NONE, "Population with DNI aged 0-17, by residence"),
    "516485": ("vdl_benef_0_6", "health", NONE, "Vaso de Leche beneficiaries aged 0-6"),
    "516513": ("mun_cred_program", "health", RENAMU, "Municipality runs child growth-monitoring (CRED) programme (0/1)"),
    # --- Basic services ----------------------------------------------------
    "261186": ("sch_water", "services", NONE, "% public school premises connected to piped water"),
    "261214": ("sch_sewer", "services", NONE, "% public school premises connected to sewerage"),
    "261276": ("sch_electric", "services", NONE, "% public school premises connected to the grid"),
    "122051": ("mun_waste_collect", "services", RENAMU, "Municipality collects solid waste (0/1)"),
    "516459": ("mun_waste_kg_day", "services", NONE, "Solid waste collected, kg per day"),
    "516462": ("mun_cleaning_spend", "services", NONE, "Municipal spending on public cleaning (S/)"),
    # --- Economic activity and labour --------------------------------------
    "517303": ("lab_private_workers", "economy", NONE, "Private-sector workers on the electronic payroll (MTPE)"),
    "517302": ("lab_private_firms", "economy", NONE, "Private firms on the electronic payroll (MTPE)"),
    "517438": ("lab_public_workers", "economy", NONE, "Public-sector workers on the electronic payroll (MTPE)"),
    "389746": ("fin_cmac_credit", "economy", STRUCT, "Direct credit, cajas municipales (S/ thousands)"),
    "389744": ("fin_cmac_deposits", "economy", STRUCT, "Deposits, cajas municipales (S/ thousands)"),
    "261507": ("fin_bank_credit", "economy", STRUCT, "Direct credit, commercial banks (S/ thousands)"),
    "261508": ("fin_bank_deposits", "economy", STRUCT, "Deposits, commercial banks (S/ thousands)"),
    "261461": ("min_gold_kg", "economy", STRUCT, "Gold production (kg fine)"),
    "261580": ("min_copper_t", "economy", STRUCT, "Copper production (t fine)"),
    # --- Poverty-related programme coverage (>=10 years) -------------------
    "516484": ("vdl_benef_total", "poverty", NONE, "Vaso de Leche beneficiaries, total"),
    # --- Crime and security ------------------------------------------------
    "389862": ("crime_complaints", "crime", NONE, "Crime complaints registered by the police (PNP)"),
    "122085": ("sec_prob_burglary", "crime", RENAMU, "Municipality reports home burglary problem (0/1)"),
    "122091": ("sec_prob_rustling", "crime", RENAMU, "Municipality reports cattle rustling problem (0/1)"),
    "122089": ("sec_prob_alcohol", "crime", RENAMU, "Municipality reports alcoholism problem (0/1)"),
    "122093": ("sec_serenazgo", "crime", RENAMU, "Municipality provides serenazgo (0/1)"),
    "122156": ("sec_serenazgo_staff", "crime", RENAMU, "Serenazgo staff (persons)"),
    # --- Municipal capacity (RENAMU) ---------------------------------------
    "121951": ("mun_staff_total", "municipal", NONE, "Municipal staff, total"),
    "121953": ("mun_staff_prof", "municipal", RENAMU, "Municipal staff, professionals"),
    "121992": ("mun_computers", "municipal", NONE, "Computers in the municipality"),
    "121997": ("mun_internet", "municipal", RENAMU, "Municipality has internet (0/1)"),
    "121981": ("mun_dump_trucks", "municipal", RENAMU, "Dump trucks owned by the municipality"),
    "122155": ("mun_has_pdc", "municipal", RENAMU, "Municipality has a Concerted Development Plan (0/1)"),
    "516435": ("mun_has_rof", "municipal", RENAMU, "Municipality has an Organisation and Functions Regulation (0/1)"),
    # --- Environment and shocks --------------------------------------------
    "122136": ("env_pollution_sewage", "environment", RENAMU, "Municipality reports pollution from wastewater (0/1)"),
    "122137": ("env_pollution_burning", "environment", RENAMU, "Municipality reports pollution from garbage burning (0/1)"),
    "122138": ("env_pollution_deforest", "environment", RENAMU, "Municipality reports pollution from deforestation/burning (0/1)"),
    "516382": ("env_mgmt_instruments", "environment", RENAMU, "Municipality has environmental management instruments (0/1)"),
    "516558": ("env_disaster_any", "environment", RENAMU, "Municipality registered natural hazards/disasters (0/1)"),
    "122146": ("env_frost", "environment", RENAMU, "Municipality registered frost (0/1)"),
    "122148": ("env_heavy_rain", "environment", RENAMU, "Municipality registered heavy rain (0/1)"),
    # --- Denominator (same series as in the canon panel) -------------------
    "262234": ("pop_proj", "denominator", NONE, "INEI projected population (rebased on 2017 Census from 2018)"),
}

RENAMU_UNIVERSE_CODES = ["121951", "121992"]

# code -> years blanked by default (see module docstring)
SUSPECT = {
    "261461": [2025],
    "261580": [2025],
    "517302": [2015],
    "262239": [2020, 2021, 2022],
}


def read_sirtod(codes):
    frames = []
    for f in sorted(SIRTOD.glob("04*_SIRTOD_Cusco_anual_distritos.xlsx")):
        print(f"reading {f.name} ...", flush=True)
        df = pd.read_excel(
            f, sheet_name="Datos", header=5,
            dtype={"UBIGEO": str, "Código indicador": str, "Valor original": str},
        )
        frames.append(df[df["Código indicador"].isin(codes)])
    raw = pd.concat(frames, ignore_index=True)
    raw = raw[raw["UBIGEO"] != "080199"]
    return raw


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--extra", default="", help="comma-separated extra SIRTOD codes (named v<code>, no fill)")
    ap.add_argument("--only", default="", help="comma-separated dimensions to keep")
    ap.add_argument("--no-fill", action="store_true", help="keep SIRTOD values exactly as published")
    ap.add_argument("--keep-suspect", action="store_true", help="keep the cells listed in SUSPECT")
    ap.add_argument("--first-year", type=int, default=2003)
    ap.add_argument("--last-year", type=int, default=2025)
    args = ap.parse_args()

    spec = dict(SHORTLIST)
    if args.only:
        keep = set(args.only.split(",")) | {"denominator"}
        spec = {k: v for k, v in spec.items() if v[1] in keep}
    for c in filter(None, args.extra.split(",")):
        spec.setdefault(c.strip(), (f"v{c.strip()}", "extra", NONE, "extra code"))

    raw = read_sirtod(set(spec) | set(RENAMU_UNIVERSE_CODES))
    raw = raw[(raw["Año"] >= args.first_year) & (raw["Año"] <= args.last_year)]
    raw = raw.dropna(subset=["Valor numérico"])
    dup = raw.duplicated(["Código indicador", "UBIGEO", "Año"]).sum()
    if dup:
        raise SystemExit(f"{dup} duplicated code-district-year rows; inspect before pivoting")

    if not args.keep_suspect:
        bad = pd.Series(False, index=raw.index)
        for code, years in SUSPECT.items():
            bad |= (raw["Código indicador"] == code) & raw["Año"].isin(years)
        raw = raw[~bad]

    wide = raw.pivot_table(index=["UBIGEO", "Año"], columns="Código indicador",
                           values="Valor numérico", aggfunc="first")

    # Skeleton: every district from its first year in any pulled series.
    ub = pd.read_excel(SIRTOD / "01_SIRTOD_Cusco_guia.xlsx", sheet_name="UBIGEO",
                       header=4, dtype=str)
    ub = ub[ub["UBIGEO"].str.match(r"^08\d{4}$", na=False) & (ub["UBIGEO"] != "080199")]
    first = raw.groupby("UBIGEO")["Año"].min()
    rows = [(u, y) for u in ub["UBIGEO"] for y in range(args.first_year, args.last_year + 1)
            if u in first.index and y >= first[u]]
    idx = pd.MultiIndex.from_tuples(rows, names=["UBIGEO", "Año"])
    wide = wide.reindex(idx)

    renamu_universe = wide[[c for c in RENAMU_UNIVERSE_CODES if c in wide]].notna().any(axis=1)

    out = pd.DataFrame(index=wide.index)
    ece_codes = [c for c, v in spec.items() if v[2] == ECE]
    for code, (var, _dim, rule, _lab) in spec.items():
        s = wide[code] if code in wide else pd.Series(np.nan, index=wide.index)
        filled = pd.Series(False, index=wide.index)
        if not args.no_fill and rule is not None:
            # years in which SIRTOD publishes this indicator for some district;
            # outside them the question was not asked and nothing is filled
            published = s.notna().groupby(level="Año").transform("any")
            if rule == RENAMU:
                filled = s.isna() & renamu_universe & published
            elif rule == ECE:
                subj = [c for c in ece_codes if spec[c][0].split("_")[1] == var.split("_")[1]]
                any_level = wide.reindex(columns=subj).notna().any(axis=1)
                filled = s.isna() & any_level
            elif rule == STRUCT:
                filled = s.isna() & published
            s = s.where(~filled, 0.0)
            out[var + "_filled"] = filled.astype(int)
        out[var] = s
    # put each value next to its flag
    order = []
    for code, (var, *_r) in spec.items():
        order.append(var)
        if var + "_filled" in out:
            order.append(var + "_filled")
    out = out[order]

    out["renamu_respondent"] = renamu_universe.astype(int)
    out = out.reset_index().rename(columns={"UBIGEO": "ubigeo", "Año": "year"})
    names = ub.set_index("UBIGEO")[["Provincia", "Distrito"]]
    out.insert(1, "province", out["ubigeo"].map(names["Provincia"]))
    out.insert(2, "district", out["ubigeo"].map(names["Distrito"]))
    out.to_csv(args.out, index=False, encoding="utf-8")
    print(f"wrote {args.out}: {len(out)} rows, {out['ubigeo'].nunique()} districts, "
          f"{len(spec)} indicators")


if __name__ == "__main__":
    main()
