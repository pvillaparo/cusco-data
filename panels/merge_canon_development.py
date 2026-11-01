"""
Merge the canon and municipal finance panel with the district development
core panel and its time-invariant baselines.

    python panels/merge_canon_development.py

Inputs (all in this folder; rebuild them first if their sources changed):
    canon_spending_district_year.csv / .dta     build_canon_spending_panel.py
    development_core_district_year.csv / .dta   extract_development_indicators.py
    development_core_baseline_district.csv/.dta extract_development_indicators.py

Output:
    canon_development_district_year.csv   UTF-8, one row per district x year
    canon_development_district_year.dta   Stata 118, with variable labels

Choices:
  * The canon panel is the spine (2001-2026; each district from its first
    year in the fiscal data). The development panel covers 2003-2025, so its
    variables are missing in 2001-2002 and 2026. Development rows with no
    canon row are dropped and reported; in the current build these are two
    rows (Villa Kintiarina 2015, Megantoni 2016) that hold only RENIEC DNI
    counts recorded before the districts enter the fiscal data.
  * Population: the canon panel's pop_proj is kept. It equals the development
    panel's copy wherever both exist and adds the 2016-2017 interpolation.
  * Baselines (c07_*, c17_*, pov13_*) are attached to every year of a
    district, so they can be used directly as interactions.
  * Province and district names must agree between the panels; the script
    stops if they do not.
"""

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
CANON = HERE / "canon_spending_district_year"
DEV = HERE / "development_core_district_year"
BASE = HERE / "development_core_baseline_district"
OUT = HERE / "canon_development_district_year"
KEY = ["ubigeo", "year"]
NAMES = ["province", "district"]


def read(stem):
    df = pd.read_csv(f"{stem}.csv", dtype={"ubigeo": str})
    labels = pd.read_stata(f"{stem}.dta", iterator=True).variable_labels()
    return df, labels


def main():
    canon, lab_c = read(CANON)
    dev, lab_d = read(DEV)
    base, lab_b = read(BASE)

    for name, df, key in [("canon", canon, KEY), ("development", dev, KEY), ("baseline", base, ["ubigeo"])]:
        if df.duplicated(key).any():
            raise SystemExit(f"duplicated {key} in the {name} file")

    # population: same series; keep the canon copy (it has the interpolation)
    chk = canon[KEY + ["pop_proj"]].merge(dev[KEY + ["pop_proj"]], on=KEY, suffixes=("", "_dev")).dropna()
    if not np.allclose(chk["pop_proj"], chk["pop_proj_dev"]):
        raise SystemExit("pop_proj differs between the canon and development panels")
    dev = dev.drop(columns="pop_proj")

    m = canon.merge(dev, on=KEY, how="outer", suffixes=("", "_dev"), indicator=True)
    both = m[m["_merge"] == "both"]
    for n in NAMES:
        if (both[n] != both[f"{n}_dev"]).any():
            raise SystemExit(f"{n} names differ between the panels")
    dropped = m[m["_merge"] == "right_only"]
    if len(dropped):
        print("development rows without a canon row (dropped):")
        print(dropped[KEY + ["district_dev"]].to_string(index=False))
    m = m[m["_merge"] != "right_only"].drop(columns=["_merge"] + [f"{n}_dev" for n in NAMES])
    # the outer join widens integer flags to float; restore the canon types
    m = m.astype({c: t for c, t in canon.dtypes.items() if pd.api.types.is_integer_dtype(t)})

    b = base.drop(columns=NAMES)
    m = m.merge(b, on="ubigeo", how="left", validate="many_to_one")
    m = m.sort_values(KEY).reset_index(drop=True)

    labels = {**lab_b, **lab_d, **lab_c}
    labels = {k: v for k, v in labels.items() if k in m}
    m.to_csv(f"{OUT}.csv", index=False, encoding="utf-8")
    m.to_stata(f"{OUT}.dta", write_index=False, version=118, variable_labels=labels)
    print(f"wrote {OUT.name}.csv and .dta: {len(m)} rows, {m['ubigeo'].nunique()} districts, "
          f"{m.shape[1]} columns ({canon.shape[1]} canon, {dev.shape[1] - 2} development, "
          f"{b.shape[1] - 1} baseline)")


if __name__ == "__main__":
    main()
