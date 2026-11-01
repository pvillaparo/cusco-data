"""
Coverage statistics for every annual district indicator in the SIRTOD Cusco
download, used to build development_indicators_shortlist.md.

    python panels/development_indicators_coverage.py

Writes panels/development_indicators_coverage.csv (one row per SIRTOD code).
Reading the four district workbooks takes about two minutes.

Column guide
  n_years, first_year, last_year, gaps, max_run   years with any district value
  med_districts, min_districts                    districts with a value, per year
  n_years_ge100, max_run_ge100                    years (and longest run) with >=100 districts
  share_zero, only_ones                           does SIRTOD ever store a 0? is it a 1-only flag?
  source_type                                     census / renamu / administrative
  missing_may_mean_zero                           a RENAMU item for which SIRTOD (almost) never
                                                  stores a 0, or a branch-based (SBS) or
                                                  producer-based (MINEM) series: a missing
                                                  district is probably a "no"/zero, so raw
                                                  district counts understate coverage
  meets_10y, meets_10y_broad                      >=10 years / >=10 years with >=100 districts
  shortlist_var, shortlist_dim                    variable name and dimension if shortlisted
"""

from pathlib import Path
import sys

import pandas as pd

HERE = Path(__file__).resolve().parent
SIRTOD = HERE.parent / "SIRTOD"
OUT = HERE / "development_indicators_coverage.csv"

sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
from extract_development_indicators import SHORTLIST  # noqa: E402


def longest_run(years):
    years = sorted(years)
    if not years:
        return 0
    best = cur = 1
    for a, b in zip(years, years[1:]):
        cur = cur + 1 if b == a + 1 else 1
        best = max(best, cur)
    return best


def main():
    frames = []
    for f in sorted(SIRTOD.glob("04*_SIRTOD_Cusco_anual_distritos.xlsx")):
        print(f"reading {f.name} ...", flush=True)
        frames.append(pd.read_excel(
            f, sheet_name="Datos", header=5,
            usecols=["Código indicador", "UBIGEO", "Año", "Valor numérico"],
            dtype={"UBIGEO": str, "Código indicador": str},
        ))
    df = pd.concat(frames, ignore_index=True)
    df = df[df["UBIGEO"] != "080199"].dropna(subset=["Valor numérico"])
    df = df.rename(columns={"Código indicador": "code", "Año": "year", "Valor numérico": "v"})

    guide = pd.read_excel(SIRTOD / "01_SIRTOD_Cusco_guia.xlsx", sheet_name="Indicadores",
                          header=4, dtype={"Código": str})
    guide = guide.rename(columns={
        "Código": "code", "Indicador": "indicator", "Ruta temática": "theme_path",
        "Unidad de medida": "unit", "Institución fuente": "source", "Definición": "definition"})

    per_year = df.groupby(["code", "year"])["UBIGEO"].nunique().rename("nd").reset_index()
    rows = []
    for code, g in per_year.groupby("code"):
        ys = g["year"].tolist()
        broad = g.loc[g["nd"] >= 100, "year"].tolist()
        vals = df.loc[df["code"] == code, "v"]
        rows.append(dict(
            code=code, n_years=len(ys), first_year=min(ys), last_year=max(ys),
            gaps=max(ys) - min(ys) + 1 - len(ys), max_run=longest_run(ys),
            med_districts=g["nd"].median(), min_districts=g["nd"].min(),
            max_districts=g["nd"].max(),
            n_years_ge100=len(broad), max_run_ge100=longest_run(broad),
            share_zero=round((vals == 0).mean(), 4), only_ones=bool((vals == 1).all()),
            years=" ".join(map(str, ys)),
            districts_by_year=" ".join(f"{y}:{n}" for y, n in zip(g["year"], g["nd"])),
        ))
    cov = pd.DataFrame(rows).merge(
        guide[["code", "indicator", "theme_path", "unit", "source", "definition"]],
        on="code", how="left")

    path = cov["theme_path"].fillna("")
    src = cov["source"].fillna("")
    census_years = cov["years"].apply(lambda s: set(map(int, s.split())) <= {2007, 2017, 2025})
    cov["source_type"] = "administrative"
    cov.loc[path.str.contains("MUNICIPALES") | src.str.contains("Municipalidades"), "source_type"] = "renamu"
    cov.loc[census_years & (path.str.contains("Censo|Censal|Censada") | src.str.contains("Censo")
                            | cov["code"].str.startswith(("4071", "4072", "5166", "5167", "5168"))),
            "source_type"] = "census"
    branch_or_producer = src.str.contains("Superintendencia de Banca|Energía y Minas")
    cov["missing_may_mean_zero"] = (
        ((cov["share_zero"] < 0.01) & (cov["source_type"] == "renamu")) | branch_or_producer)
    cov["meets_10y"] = cov["n_years"] >= 10
    cov["meets_10y_broad"] = cov["n_years_ge100"] >= 10
    cov["shortlist_var"] = cov["code"].map({k: v[0] for k, v in SHORTLIST.items()})
    cov["shortlist_dim"] = cov["code"].map({k: v[1] for k, v in SHORTLIST.items()})

    cols = ["code", "indicator", "unit", "source", "source_type", "theme_path",
            "n_years", "first_year", "last_year", "gaps", "max_run",
            "med_districts", "min_districts", "max_districts", "n_years_ge100", "max_run_ge100",
            "share_zero", "only_ones", "missing_may_mean_zero", "meets_10y", "meets_10y_broad",
            "shortlist_var", "shortlist_dim", "years", "districts_by_year", "definition"]
    cov = cov[cols].sort_values(["meets_10y_broad", "meets_10y", "n_years_ge100", "med_districts"],
                                ascending=False)
    cov.to_csv(OUT, index=False, encoding="utf-8")
    print(f"wrote {OUT}: {len(cov)} indicators, {cov['meets_10y'].sum()} with >=10 years, "
          f"{cov['meets_10y_broad'].sum()} with >=10 years at >=100 districts")


if __name__ == "__main__":
    main()
