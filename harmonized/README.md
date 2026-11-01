# Cusco-stats: harmonized dataset for plots

This folder holds the display-ready data behind the planned **Cusco-stats** pages. The pipeline has three steps, and each one can be traced back to the one before:

1. `SIRTOD/` keeps the raw INEI SIRTOD download (22 September 2026), as published.
2. `panels/` turns it into a district-year panel with consistent units, flags and a spliced population series (`panels/canon_spending_district_year.csv`).
3. `harmonized/` (this folder) aggregates that panel to province and department level, applies the display rules below, and adds bilingual labels. The plots should read only from here.

Rebuild everything with:

```bash
python panels/build_canon_spending_panel.py
python harmonized/build_harmonized.py
```

## Files

**`cusco_stats_long.csv`** has one row per level × place × year × variable × measure:

| Column | Meaning |
|---|---|
| `level` | `department`, `province` or `district` |
| `geo_code` | UBIGEO code: `08` (department), 4 digits (province), 6 digits (district). Keep it as text. |
| `geo_name`, `province` | Place name and, for districts, the province they belong to |
| `year` | 2001–2025 |
| `variable`, `measure` | What is measured (see the dictionary) and how: `total`, `per_capita` or `pct` |
| `value` | The number |
| `n_reporting`, `n_districts` | For aggregates: districts with data, and districts that exist that year |
| `pop_coverage` | For aggregates: share of the population living in the reporting districts |
| `display` | `1` if the value should be plotted, `0` if it falls outside the variable's display window or fails the coverage rule |

**`cusco_stats_dictionary.csv`** has one row per variable × measure, with labels, units, descriptions, caveats and sources **in Spanish and English** (`*_es`, `*_en`). It also gives the aggregation rule, the first and last year displayed at department level, and `map_recommended`, which marks the series that make sense on a district map (per-capita amounts and percentages, not totals).

## Harmonization rules

**Three levels that always agree.** Province and department values are built from the district data, never taken from a separate source. Clicking from the department down to a province or a district therefore never shows a contradiction, and province and department figures are unaffected by the new districts created in La Convención, because a sum does not depend on internal borders.

**Two measures for amounts.** Each amount has a total and a per-capita value. At province and department level, per capita is the sum over reporting districts divided by the spliced population of those same districts. That is the population-weighted average, which is the number readers expect ("soles per person in Cusco"). Percentages are always a ratio of sums: the department's execution rate is total accrued spending over the total modified budget, not an average of 116 district rates, which would give a 2,000-person district the same weight as Cusco city.

**One population series.** Per-capita values use `pop_spliced` from the panel. INEI's projections based on the 2007 and 2017 censuses are joined with a standard backward splice, so per-capita lines do not jump in 2016–2018 just because the population source changed. District per-capita values for the 12 La Convención districts involved in the 2015–2021 splits are left out for 2015–2017, when their populations can only be allocated approximately.

**Coverage.** An aggregate is shown only if the reporting districts hold at least 95% of the population of the districts that exist that year. This hides years when a missing district would pull a total down artificially.

**Display windows.** Each variable is plotted only over the years it is comparable:

| Variables | Years shown | Why |
|---|---|---|
| Population | 2001–2025 | |
| Canon (total, gas, forestry) | 2004–2024 | Before the 2004 reform amounts and coverage are not comparable; 2025 canon is not in SIRTOD yet |
| Mining and hydropower canon | 2005–2024 | Almost no district records them in 2003–2004 |
| FONCOMUN | 2009–2025 | District series starts in 2009 |
| SIAF budget (PIA, PIM, accrued, execution) | 2008–2025 | In 2007 SIAF covers only 40 of 108 districts |
| Canon as % of spending | 2008–2024 | Needs both canon and SIAF |
| RENAMU revenues and spending, capital share, transfer dependence | 2004–2025, **without 2023** | RENAMU 2023 is broken at the source: spending ~23% above SIAF and revenue ~2.4× its neighbouring years in almost every district |

2026 is dropped for now, because it is a partial year; revisit this at the next update. Values outside the windows stay in the file with `display = 0`, so nothing is lost.

**Money is in current soles for now.** Twenty years of inflation make nominal lines rise even when real resources do not, so real values should replace them in the plots as soon as a price index is available. The build script is ready for that: put an annual CPI in `harmonized/inputs/cpi_annual.csv` (columns `year,cpi`) and rerun it. It then adds `total_real` and `per_capita_real` measures in soles of 2024 (`REAL_BASE_YEAR` in the script), with matching dictionary entries.

## Variables currently included

Population; canon total, gas, mining, hydropower and forestry; FONCOMUN; SIAF opening budget (PIA), modified budget (PIM), accrued spending and execution rate; RENAMU revenue collected, transfer revenue, current spending and capital spending; and three derived percentages: capital share of spending, dependence on transfers, and canon as a share of spending. Oil and fishing canon are left out because they are negligible in Cusco (a handful of district-years).

## Adding more variables

The development indicators being shortlisted in a separate session (on the branch `claude/district-development-indicators`) will be added the same way. Each one is mapped into the district panel with consistent units, then given an entry in `VARS` in `build_harmonized.py` with its kind (an amount to sum, or a ratio with a numerator and denominator), its display window and its bilingual labels. Indicators that are themselves rates, such as stunting or school enrolment, will need their numerator and denominator (or a population weight) so that province and department values remain proper weighted averages.
