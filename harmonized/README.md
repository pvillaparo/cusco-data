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
| `value_coverage` | For aggregates: estimated share of the money held by the reporting districts (each missing district is sized by its values in the nearest years before and after) |
| `display` | `1` if the value should be plotted, `0` if it falls outside the variable's display window or fails the coverage rule |

**`cusco_stats_dictionary.csv`** has one row per variable × measure, with labels, units, descriptions, caveats and sources **in Spanish and English** (`*_es`, `*_en`). It also gives the aggregation rule, the first and last year displayed at department level, and `map_recommended`, which marks a curated subset of per-capita and percentage series that work well on a district map (totals do not, because they mostly reflect district size).

## Harmonization rules

**Three levels that always agree.** Province and department values are built from the district data, never taken from a separate source. Clicking from the department down to a province or a district therefore never shows a contradiction, and province and department figures are unaffected by the new districts created in La Convención, because a sum does not depend on internal borders, as long as every district reports (see Coverage).

**Two measures for amounts.** Each amount has a total and a per-capita value. At province and department level, per capita is the sum over reporting districts divided by the spliced population of those same districts. That is the population-weighted average, which is the number readers expect ("soles per person in Cusco"). Percentages are always a ratio of sums: the department's execution rate is total accrued expenditure over the total modified budget, not an average of 116 district rates, which would give a 2,000-person district the same weight as Cusco city.

**One population series.** Per-capita values use `pop_spliced` from the panel. INEI's projections based on the 2007 and 2017 censuses are joined with a standard backward splice, so per-capita lines do not jump in 2016–2018 just because the population source changed. Each parent district that lost territory before 2018 is spliced together with the districts carved out of it (Echarate with Megantoni, Vilcabamba with Inkawasi and Villa Virgen, Kimbiri with Villa Kintiarina), so each one's old population is matched to the same territory in 2018. For these seven districts the 2015–2017 populations can only be allocated approximately, so their district-level population and per-capita values are not displayed for those years. Province and department values are not affected.

**Coverage.** An aggregate is shown only if the reporting districts hold at least 95% of the population **and** at least 98% of the money of the districts that exist that year. The money test matters because population alone can miss a large gap: the four districts created in 2021 hold 1.3% of Cusco's people but 4–5% of its municipal spending. Each missing district is sized by its own values in the nearest years before and after. A new district in its first year whose budget was still reported by its parent (Megantoni in 2017, for example) counts as covered by the parent, and its population is kept in the per-capita denominator. In practice this hides, at department level, canon in 2004, PIA in 2021–2022 (the 2021 districts have no opening budget in those years) and municipal current and capital expenditure in 2022.

**Display windows.** Each variable is plotted only over the years it is comparable:

| Variables | Years shown | Why |
|---|---|---|
| Population | 2001–2025 | |
| Canon (total, gas, mining, hydropower) | 2005–2024 | 2004 is a start-up year with incomplete coverage, and before the 2004 reform amounts are not comparable; 2025 canon is not in SIRTOD yet |
| FONCOMUN | 2009–2025, **without 2016** | District series starts in 2009; SIRTOD's 2016 district values are scrambled across districts (their correlation with 2015 and 2017 is 0.32, against 0.99 or more for every other pair of years) |
| SIAF budget (PIA, PIM, accrued, execution) | 2008–2025 | In 2007 SIAF covers only 40 of 108 districts |
| Canon as % of expenditure | 2008–2024 | Needs both canon and SIAF |
| Municipal accounts: revenue, expenditure, capital share, transfer dependence | 2004–2025, **without 2023** | 2023 is broken at the source: expenditure ~23% above SIAF and revenue about twice the 2022–2024 average in almost every district |

2026 is dropped for now, because it is a partial year; revisit this at the next update. Values outside the windows stay in the file with `display = 0`, so nothing is lost.

**Money is in current soles for now.** Twenty years of inflation make nominal lines rise even when real resources do not, so real values should replace them in the plots as soon as a price index is available. The build script is ready for that: put an annual CPI in `harmonized/inputs/cpi_annual.csv` (columns `year,cpi`) and rerun it. It then adds `total_real` and `per_capita_real` measures in soles of 2024 (`REAL_BASE_YEAR` in the script), with matching dictionary entries.

## Variables currently included

Population; canon total, gas, mining and hydropower; FONCOMUN; SIAF opening budget (PIA), modified budget (PIM), accrued expenditure and execution rate; municipal accounts (MEF's Public Accounting Directorate, DNCP, via SIRTOD) for total revenue, transfer revenue, current expenditure and capital expenditure; and three derived percentages: capital share of expenditure, dependence on transfers, and canon as a share of expenditure. Forestry, oil and fishing canon are left out of the plots because they are negligible in Cusco, but they still count in canon total.

Two definitions deserve care. Total revenue includes **financing**, that is, balances carried over from previous years and borrowing, so it can exceed what a municipality actually raised in the year. Dependence on transfers therefore divides transfer revenue by total revenue *minus* financing. A blank financing value in SIRTOD is read as zero, because SIRTOD does not store zeros.

## Adding more variables

The development indicators being shortlisted in a separate session (on the branch `claude/district-development-indicators`) will be added the same way. Each one is mapped into the district panel with consistent units, then given an entry in `VARS` in `build_harmonized.py` with its kind (an amount to sum, or a ratio with a numerator and denominator), its display window and its bilingual labels. Indicators that are themselves rates, such as stunting or school enrolment, will need their numerator and denominator (or a population weight) so that province and department values remain proper weighted averages.
