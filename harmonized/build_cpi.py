"""
Annual Cusco city CPI for deflating the harmonized money series.

Input : harmonized/inputs/cusco_cpi_monthly_sirtod.xlsx (SIRTOD 262483 and 516913, as exported)
Output: harmonized/inputs/cpi_annual.csv  (year, cpi, n_months, partial, segment)

Run from the repository root:

    python harmonized/build_cpi.py

Linking decisions (confirmed by the project owner; see inputs/CPI_LINKING_NOTES.md):
  * 516913 (Jan 2022 onward) has December 2021 = 100 for the Cusco index. It is
    expressed on the scale of 262483 (base 2009) by multiplying it by
    262483's December 2021 value / 100. January 2022 therefore shows the change
    from December 2021, and December 2021 keeps its own monthly change.
  * The break inside 262483 in January 2010 (Dec 2009 = 231.43 on an older base,
    Jan 2010 = 101.08 on base 2009) is NOT resolved: neither the 2009-average
    nor the December-2009 rescaling reproduces INEI's reported January 2010
    inflation for Cusco (+0.45%). Months before January 2010 are therefore left
    out until an official Cusco link factor or overlapping values are verified.
  * Annual values are averages of the 12 monthly values; a year with fewer
    months is flagged partial (2026: January-August).
"""

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SRC = HERE / "inputs" / "cusco_cpi_monthly_sirtod.xlsx"
OUT = HERE / "inputs" / "cpi_annual.csv"
FIRST_LINKED_MONTH = "2010-01-01"   # earlier months: unresolved rebasing break


def main() -> None:
    old = pd.read_excel(SRC, sheet_name="Cusco_262483").set_index("periodo")["valor_indice"].sort_index()
    new = pd.read_excel(SRC, sheet_name="Cusco_516913").set_index("periodo")["valor_indice"].sort_index()

    bridge = old.loc["2021-12-01"] / 100.0          # December 2021 = 100 in the new series
    linked = pd.concat([
        old.loc[FIRST_LINKED_MONTH:"2021-12-01"].rename("cpi").to_frame().assign(segment="262483 base 2009"),
        (new * bridge).rename("cpi").to_frame().assign(segment="516913 base Dec2021, rescaled"),
    ])
    if linked.index.duplicated().any() or (linked.index.to_series().diff().dt.days > 31).any():
        raise ValueError("Linked monthly CPI has duplicated or missing months")

    linked["year"] = linked.index.year
    annual = linked.groupby("year").agg(cpi=("cpi", "mean"), n_months=("cpi", "size"),
                                        segment=("segment", lambda s: " + ".join(sorted(set(s)))))
    annual["partial"] = (annual.n_months < 12).astype(int)
    annual["cpi"] = annual.cpi.round(4)
    annual.reset_index()[["year", "cpi", "n_months", "partial", "segment"]].to_csv(OUT, index=False)

    jan22 = (new.iloc[0] / 100 - 1) * 100
    print(f"bridge factor {bridge:.4f}; implied Jan 2022 change {jan22:+.2f}%; "
          f"years {annual.index.min()}-{annual.index.max()} "
          f"(partial: {annual.index[annual.partial == 1].tolist()})")


if __name__ == "__main__":
    main()
