"""
Build the district development panel for Cusco from SIRTOD.

By default this writes the approved core panel (CORE below) plus a
time-invariant baseline file; --set full extracts the whole shortlist in
development_indicators_shortlist.md instead.

Source: the SIRTOD district workbooks in ../SIRTOD (04a-04d), downloaded from
INEI SIRTOD on 2026-09-22. Run from the repository root or from this folder:

    python panels/extract_development_indicators.py                 # approved core panel
    python panels/extract_development_indicators.py --set full      # whole shortlist
    python panels/extract_development_indicators.py --set full --only education,crime
    python panels/extract_development_indicators.py --extra 516459,122103
    python panels/extract_development_indicators.py --no-fill --keep-suspect   # as published

Reading the four workbooks takes about two minutes. Outputs, written next to
this script (CSV, plus Stata .dta with variable labels unless --no-dta):

  core:  development_core_district_year       one row per district x year,
                                              2003-2025; merge 1:1 with
                                              canon_spending_district_year on
                                              (ubigeo, year)
         development_core_baseline_district   one row per district: 2007 and
                                              2017 Census shares (c07_*, c17_*)
                                              and the 2013 poverty map (pov13_*)
  full:  development_indicators_district_year

How missing values are treated (the --no-fill switch turns all of this off):

  * RENAMU yes/no indicators ("Municipalidades que ...") are stored in SIRTOD
    only as 1s; a "no" answer is simply absent. They are set to 0 when the
    municipality answered RENAMU for that date: for items about year Y
    ("ref", see RENAMU_TIMING) when it reports staff at 31 December Y
    (121951); for items dated at the survey ("survey") when it reports
    computers (121992) that year; otherwise when it reports either. Districts outside
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
6,800 to 2,600 during COVID, so registration, not mortality, changed), and the
share of school premises with all three services in 2019-2022 (questionnaire
break in 2019; the series is kept as 2011-2018).

RENAMU timing: SIRTOD dates items about year Y as Y and items recorded at the
survey (collected in Y+1) as Y+1. --align-renamu re-dates the survey items to
Y so that all RENAMU variables in a row refer to the same year; by default the
SIRTOD dates are kept.

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

# RENAMU timing (see "When RENAMU variables are dated" in the shortlist note).
# One RENAMU round, collected in the first half of year Y+1, yields two kinds
# of items, and SIRTOD dates each by its own reference date:
#   "ref"    activity during calendar year Y or a stock at 31 December Y
#            (staff, services provided, programmes, waste collected); dated Y.
#   "survey" what the municipality has when it answers in year Y+1
#            (equipment, vehicles, plans, perceived problems); dated Y+1.
# Evidence: in every module, "ref" items end in 2024 and "survey" items in
# 2025, and new districts report staff one year before equipment. Items that
# stop before 2019 cannot be classified this way and are marked "unknown".
RENAMU_TIMING = {
    "121951": "ref", "121953": "ref", "122093": "ref", "122156": "ref",
    "122051": "ref", "516459": "ref", "516462": "ref", "516484": "ref",
    "516485": "ref", "516513": "ref", "121997": "ref",
    "121992": "survey", "121981": "survey", "122155": "survey", "516435": "survey",
    "122136": "survey", "122137": "survey", "122138": "survey", "516382": "survey",
    "122085": "unknown", "122091": "unknown", "122089": "unknown",
    "516558": "unknown", "122146": "unknown", "122148": "unknown",
}
# respondent universe used for the zero-fill, by timing class
TIMING_UNIVERSE = {"ref": ["121951"], "survey": ["121992"], "unknown": RENAMU_UNIVERSE_CODES}

# code -> years blanked by default (see module docstring)
SUSPECT = {
    "261461": [2025],
    "261580": [2025],
    "517302": [2015],
    "262239": [2020, 2021, 2022],
    "420006": [2019, 2020, 2021, 2022],
}

# ---------------------------------------------------------------------------
# Approved core set (decision of November 2026): one or two series per
# dimension, chosen to be informative and not redundant. See the section
# "The approved core panel" in development_indicators_shortlist.md.
# ---------------------------------------------------------------------------
CORE = [
    "413856", "417647",            # public pupil-teacher ratio
    "261276",                      # school premises on the grid
    "420006",                      # school premises with all three services (2011-2018)
    "420549", "420553",            # ECE satisfactory, reading and math
    "262226", "262211",            # late-birth-registration share
    "424497",                      # DNI holders (alternative denominator)
    "516485",                      # Vaso de Leche beneficiaries 0-6
    "517303",                      # formal private employment
    "389746",                      # caja municipal credit (presence)
    "121951", "121953",            # municipal staff and professionals
    "121992",                      # computers
    "121981",                      # dump trucks
    "122093",                      # serenazgo
    "122146", "122148",            # frost, heavy rain
    "262234",                      # projected population (denominator)
]

# Derived ratios added whenever their inputs are in the output:
# variable -> (numerator, denominator, scale, label)
DERIVED = {
    "edu_ptr_pub": ("edu_enrol_ebr_pub", "edu_teach_ebr_pub", 1, "Pupil-teacher ratio, public EBR"),
    "vit_late_birth_share": ("vit_births_late", "vit_births_reg", 100, "% of registered births registered late"),
    "mun_prof_share": ("mun_staff_prof", "mun_staff_total", 100, "% of municipal staff who are professionals"),
}

# Time-invariant baselines from the 2007 and 2017 Censuses and the 2013
# poverty map. Census items are counts; each share is numerator/denominator.
DWELL = ["407243", "407244"]                       # dwellings with occupants present
HH = ["407235", "407236", "407237", "407238", "407239", "407240", "407241", "407242"]  # households (by cooking fuel)
LANG = ["516749", "516750", "516751", "516752"]    # population by mother tongue
BASELINE = {
    # name: (numerator codes, denominator codes, label)
    "water_in": (["407209"], DWELL, "% dwellings with piped water inside"),
    "sewer_in": (["407217"], DWELL, "% dwellings with sewer connection inside"),
    "electric": (["407243"], DWELL, "% dwellings with public electricity"),
    "earth_floor": (["407201"], DWELL, "% dwellings with earthen floor"),
    "cook_biomass": (["407239", "407240"], HH, "% households cooking with firewood or dung"),
    "internet": (["516775"], HH, "% households with internet"),
    "mobile": (["516777"], HH, "% households with a mobile phone"),
    "quechua": (["516750"], LANG, "% population with Quechua mother tongue"),
    "rural": (["262221"], ["262215"], "% population rural"),
}
CENSUS_POP = "262215"
POVERTY_MAP = "427594"


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


def read_ubigeo():
    ub = pd.read_excel(SIRTOD / "01_SIRTOD_Cusco_guia.xlsx", sheet_name="UBIGEO",
                       header=4, dtype=str)
    ub = ub[ub["UBIGEO"].str.match(r"^08\d{4}$", na=False) & (ub["UBIGEO"] != "080199")]
    return ub.set_index("UBIGEO")[["Provincia", "Distrito"]]


def build_panel(raw, spec, names, first_year, last_year, fill=True, keep_suspect=False,
                align_renamu=False):
    """Wide district-year panel for the codes in `spec`, with the fill rules."""
    if align_renamu:
        # "survey" items dated Y+1 describe the municipality at about the end
        # of Y; re-date them to Y so every RENAMU item refers to year Y.
        # The computers series used for the survey universe moves with them.
        raw = raw.copy()
        survey = raw["Código indicador"].map(RENAMU_TIMING).eq("survey")
        raw.loc[survey, "Año"] -= 1
    raw = raw[(raw["Año"] >= first_year) & (raw["Año"] <= last_year)]
    raw = raw.dropna(subset=["Valor numérico"])
    dup = raw.duplicated(["Código indicador", "UBIGEO", "Año"]).sum()
    if dup:
        raise SystemExit(f"{dup} duplicated code-district-year rows; inspect before pivoting")
    if not keep_suspect:
        bad = pd.Series(False, index=raw.index)
        for code, years in SUSPECT.items():
            bad |= (raw["Código indicador"] == code) & raw["Año"].isin(years)
        raw = raw[~bad]

    wide = raw.pivot_table(index=["UBIGEO", "Año"], columns="Código indicador",
                           values="Valor numérico", aggfunc="first")

    # Skeleton: every district from its first year in any pulled series.
    in_spec = raw[raw["Código indicador"].isin(spec)]
    first = in_spec.groupby("UBIGEO")["Año"].min()
    rows = [(u, y) for u in names.index for y in range(first_year, last_year + 1)
            if u in first.index and y >= first[u]]
    wide = wide.reindex(pd.MultiIndex.from_tuples(rows, names=["UBIGEO", "Año"]))

    renamu_universe = wide.reindex(columns=RENAMU_UNIVERSE_CODES).notna().any(axis=1)
    universe = {k: wide.reindex(columns=v).notna().any(axis=1) for k, v in TIMING_UNIVERSE.items()}
    # all ECE levels are used for the fill, even those not in the output
    ece_all = [c for c, v in SHORTLIST.items() if v[2] == ECE]

    out = pd.DataFrame(index=wide.index)
    for code, (var, _dim, rule, _lab) in spec.items():
        s = wide[code] if code in wide else pd.Series(np.nan, index=wide.index)
        if fill and rule is not None:
            # years in which SIRTOD publishes this indicator for some district;
            # outside them the question was not asked and nothing is filled
            published = s.notna().groupby(level="Año").transform("any")
            if rule == RENAMU:
                u = universe[RENAMU_TIMING.get(code, "unknown")]
                filled = s.isna() & u & published
            elif rule == ECE:
                subject = var.split("_")[1]
                subj = [c for c in ece_all if SHORTLIST[c][0].split("_")[1] == subject]
                filled = s.isna() & wide.reindex(columns=subj).notna().any(axis=1)
            else:  # STRUCT
                filled = s.isna() & published
            out[var] = s.where(~filled, 0.0)
            out[var + "_filled"] = filled.astype(int)
        else:
            out[var] = s

    out["renamu_respondent"] = renamu_universe.astype(int)
    out["renamu_resp_ref"] = universe["ref"].astype(int)
    out["renamu_resp_survey"] = universe["survey"].astype(int)
    out = out.reset_index().rename(columns={"UBIGEO": "ubigeo", "Año": "year"})
    out.insert(1, "province", out["ubigeo"].map(names["Provincia"]))
    out.insert(2, "district", out["ubigeo"].map(names["Distrito"]))
    return out


def add_derived(out, labels):
    for var, (num, den, scale, lab) in DERIVED.items():
        if num in out and den in out:
            d = out[den].where(out[den] > 0)
            out[var] = scale * out[num] / d
            labels[var] = lab
    if "fin_cmac_credit" in out:
        out["fin_cmac_present"] = (out["fin_cmac_credit"] > 0).astype(float).where(
            out["fin_cmac_credit"].notna())
        labels["fin_cmac_present"] = "A caja municipal reports credit in the district (0/1)"
    return out


def build_baseline(raw, names):
    """One row per district: 2007 and 2017 Census shares and the 2013 poverty map."""
    v = raw.dropna(subset=["Valor numérico"]).pivot_table(
        index=["UBIGEO", "Año"], columns="Código indicador",
        values="Valor numérico", aggfunc="first")
    base = pd.DataFrame(index=names.index)
    labels = {}
    for year in (2007, 2017):
        if year not in v.index.get_level_values("Año"):
            continue
        vy = v.xs(year, level="Año")
        for name, (num, den, lab) in BASELINE.items():
            n = vy.reindex(columns=num).sum(axis=1, min_count=1)
            d = vy.reindex(columns=den).sum(axis=1, min_count=1)
            # a category absent for a district with a denominator is a zero
            n = n.where(n.notna() | d.isna(), 0.0)
            col = f"c{year % 100:02d}_{name}"
            base[col] = (100 * n / d.where(d > 0)).reindex(base.index)
            labels[col] = f"{lab}, Census {year}"
        col = f"c{year % 100:02d}_pop"
        base[col] = vy.reindex(columns=[CENSUS_POP]).iloc[:, 0].reindex(base.index)
        labels[col] = f"Census population {year}"
    # 2013 poverty map: text intervals such as "43,4 - 57,2"
    pm = raw[raw["Código indicador"] == POVERTY_MAP][["UBIGEO", "Valor original"]].dropna()
    parts = pm["Valor original"].str.replace(",", ".").str.split("-", expand=True)
    lo = pd.to_numeric(parts[0].str.strip(), errors="coerce").set_axis(pm["UBIGEO"])
    hi = pd.to_numeric(parts[1].str.strip(), errors="coerce").set_axis(pm["UBIGEO"])
    base["pov13_lo"], base["pov13_hi"] = lo.reindex(base.index), hi.reindex(base.index)
    base["pov13_mid"] = (base["pov13_lo"] + base["pov13_hi"]) / 2
    labels.update(pov13_lo="Poverty 2013 (% poor), lower bound of interval",
                  pov13_hi="Poverty 2013 (% poor), upper bound of interval",
                  pov13_mid="Poverty 2013 (% poor), interval midpoint")
    base = base.reset_index().rename(columns={"UBIGEO": "ubigeo"})
    base.insert(1, "province", base["ubigeo"].map(names["Provincia"]))
    base.insert(2, "district", base["ubigeo"].map(names["Distrito"]))
    return base, labels


def write(df, stem, labels, dta):
    df.to_csv(f"{stem}.csv", index=False, encoding="utf-8")
    msg = f"wrote {stem}.csv"
    if dta:
        lab = {k: v[:80] for k, v in labels.items() if k in df}
        lab.update({k: "1 = value set by a zero-fill rule" for k in df if k.endswith("_filled")})
        df.to_stata(f"{stem}.dta", write_index=False, version=118, variable_labels=lab)
        msg += " and .dta"
    print(f"{msg}: {len(df)} rows, {df['ubigeo'].nunique()} districts")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--set", choices=["core", "full"], default="core",
                    help="core = approved core panel (default); full = whole shortlist")
    ap.add_argument("--out", default=None, help="output path stem (no extension)")
    ap.add_argument("--extra", default="", help="comma-separated extra SIRTOD codes (named v<code>, no fill)")
    ap.add_argument("--only", default="", help="comma-separated dimensions to keep (full set only)")
    ap.add_argument("--no-fill", action="store_true", help="do not apply the zero-fill rules")
    ap.add_argument("--keep-suspect", action="store_true", help="keep the cells listed in SUSPECT")
    ap.add_argument("--align-renamu", action="store_true",
                    help="re-date RENAMU survey-date stocks from Y+1 to Y (end of year Y)")
    ap.add_argument("--no-dta", action="store_true", help="write CSV only")
    ap.add_argument("--first-year", type=int, default=2003)
    ap.add_argument("--last-year", type=int, default=2025)
    args = ap.parse_args()

    if args.set == "core":
        spec = {c: SHORTLIST[c] for c in CORE}
        stem = Path(args.out) if args.out else HERE / "development_core_district_year"
    else:
        spec = dict(SHORTLIST)
        if args.only:
            keep = set(args.only.split(",")) | {"denominator"}
            spec = {k: v for k, v in spec.items() if v[1] in keep}
        stem = Path(args.out) if args.out else DEFAULT_OUT.with_suffix("")
    for c in filter(None, args.extra.split(",")):
        spec.setdefault(c.strip(), (f"v{c.strip()}", "extra", NONE, f"SIRTOD code {c.strip()}"))

    baseline_codes = {c for num, den, _ in BASELINE.values() for c in num + den}
    baseline_codes |= {CENSUS_POP, POVERTY_MAP}
    ece_all = {c for c, v in SHORTLIST.items() if v[2] == ECE}
    need = set(spec) | set(RENAMU_UNIVERSE_CODES) | ece_all
    if args.set == "core":
        need |= baseline_codes
    raw = read_sirtod(need)
    names = read_ubigeo()

    labels = {v[0]: v[3] for v in spec.values()}
    labels.update(ubigeo="INEI UBIGEO district code (text)", year="Year",
                  province="Province", district="District",
                  renamu_respondent="Municipality answered RENAMU this year (reports staff or computers)",
                  renamu_resp_ref="Reports staff at 31 Dec of this year (universe for year-Y items)",
                  renamu_resp_survey="Reports computers dated this year (universe for survey-date items)")
    out = build_panel(raw, spec, names, args.first_year, args.last_year,
                      fill=not args.no_fill, keep_suspect=args.keep_suspect,
                      align_renamu=args.align_renamu)
    out = add_derived(out, labels)
    write(out, str(stem), labels, dta=not args.no_dta)

    if args.set == "core":
        base, blabels = build_baseline(raw, names)
        blabels.update(ubigeo="INEI UBIGEO district code (text)", province="Province",
                       district="District")
        bstem = stem.parent / "development_core_baseline_district"
        write(base, str(bstem), blabels, dta=not args.no_dta)


if __name__ == "__main__":
    main()
