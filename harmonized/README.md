# Cusco-stats: harmonized dataset for plots

This folder holds the display-ready data behind the planned **Cusco-stats** pages. The pipeline has three steps, and each one can be traced back to the one before:

1. `SIRTOD/` keeps the raw INEI SIRTOD download (22 September 2026), as published.
2. `panels/` turns it into district-year panels with consistent units, flags and a spliced population series: canon and municipal finance (`canon_spending_district_year`), development indicators and census baselines (`development_core_*`), and the merged file the website data is built from (`canon_development_district_year`).
3. `harmonized/` (this folder) aggregates that panel to province and department level, applies the display rules below, and adds bilingual labels. The plots should read only from here.

Rebuild everything with:

```bash
python panels/build_canon_spending_panel.py
python panels/extract_development_indicators.py
python panels/merge_canon_development.py
python harmonized/build_cpi.py
python harmonized/build_harmonized.py
```

## Files

**`cusco_stats_long.csv`** has one row per level × place × year × variable × measure:

| Column | Meaning |
|---|---|
| `level` | `department`, `province` or `district` |
| `geo_code` | UBIGEO code: `08` (department), 4 digits (province), 6 digits (district). Keep it as text. |
| `geo_name`, `province` | Place name and, for districts, the province they belong to |
| `year` | 2001–2025. For census snapshots, the census year (2007, 2017) or 2013 for the poverty map |
| `variable`, `measure` | What is measured (see the dictionary) and how: `total`, `per_capita`, `per_1000`, `pct`, `ratio`, `count` (and `total_real`, `per_capita_real` for money; `pct_lo`, `pct_hi` for the poverty interval) |
| `value` | The number |
| `n_reporting`, `n_districts` | For aggregates: districts with data, and districts that exist that year |
| `pop_coverage` | For aggregates: share of the population living in the reporting districts |
| `value_coverage` | For aggregates: estimated share of the money held by the reporting districts (each missing district is sized by its values in the nearest years before and after) |
| `display` | `1` if the value should be plotted, `0` if it falls outside the variable's display window, is an excluded year (FONCOMUN 2016, municipal accounts 2023), fails the coverage rule or fails the official totals check |

**`cusco_stats_dictionary.csv`** has one row per variable × measure, with labels, units, descriptions, caveats and sources **in Spanish and English** (`*_es`, `*_en`). It also gives the aggregation rule, the first and last year displayed at department level, and `map_recommended`, which marks a curated subset of per-capita and percentage series that work well on a district map (totals do not, because they mostly reflect district size).

## Harmonization rules

**Three levels that always agree.** Province and department values are built from the district data, never taken from a separate source (the exceptions are the three indicators SIRTOD publishes only as district rates, school electricity, the ECE and poverty, described below). Clicking from the department down to a province or a district therefore never shows a contradiction, and province and department figures are unaffected by the new districts created in La Convención, because a sum does not depend on internal borders, as long as every district reports (see Coverage).

**Two measures for amounts.** Each amount has a total and a per-capita value. At province and department level, per capita is the sum over reporting districts divided by the spliced population of those same districts. That is the population-weighted average, which is the number readers expect ("soles per person in Cusco"). Percentages are always a ratio of sums: the department's execution rate is total accrued expenditure over the total modified budget, not an average of 116 district rates, which would give a 2,000-person district the same weight as Cusco city.

**One population series.** Per-capita values use `pop_spliced` from the panel. INEI's projections based on the 2007 and 2017 censuses are joined with a standard backward splice, so per-capita lines do not jump in 2016–2018 just because the population source changed. Each parent district that lost territory before 2018 is spliced together with the districts carved out of it (Echarate with Megantoni, Vilcabamba with Inkawasi and Villa Virgen, Kimbiri with Villa Kintiarina), so each one's old population is matched to the same territory in 2018. For these seven districts the 2015–2017 populations can only be allocated approximately, so their district-level population and per-capita values are not displayed for those years. Province and department values are not affected.

**Coverage.** An aggregate is shown only if the reporting districts hold at least 95% of the population **and** at least 98% of the money of the districts that exist that year. The money test matters because population alone can miss a large gap: the four districts created in 2021 hold 1.3% of Cusco's people but 4–5% of its municipal spending. Each missing district is sized by the mean of its own values k years before and after, for the smallest k ≤ 3 with any value (zero if there is none). Young districts (created in 2015 or later, in their first three years) count as covered in the population test, and their population stays in the per-capita denominator; the money test still applies to them. A new district in its first year whose budget was still reported by its parent (Megantoni in 2017, for example) counts as covered by the parent, and its population is kept in the per-capita denominator. In practice this hides, at department level, PIA in 2021–2022 (the 2021 districts have no opening budget in those years), municipal current and capital expenditure in 2022, capital expenditure in 2007 and the capital share in 2022 (canon 2004 also fails, but it is outside the canon window anyway). The `display` column is the authoritative record.

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

**Money in current and constant soles.** Every amount comes in current soles (`total`, `per_capita`) and, from 2010, in **constant 2024 soles** (`total_real`, `per_capita_real`): nominal value × (2024 average CPI / the year's average CPI). The deflator is INEI's **Cusco city CPI**, built by `build_cpi.py` from the two SIRTOD series in `inputs/` and saved as `inputs/cpi_annual.csv`. Two limits are worth stating wherever real values are shown. First, applying a city price index to every district is an analytical assumption, because there are no district price indices. Second, real values start in 2010, because the Cusco CPI has a rebasing break in January 2010 that is not yet resolved: neither simple rescaling reproduces INEI's reported January 2010 inflation for Cusco (+0.45%). Earlier years therefore stay in current soles only. The plots should use constant soles wherever they are available. Details and open questions are in `inputs/CPI_LINKING_NOTES.md`.

## Variables currently included

**Canon and municipal finance.** Population; canon total, gas, mining and hydropower; FONCOMUN; SIAF opening budget (PIA), modified budget (PIM), accrued expenditure and execution rate; municipal accounts (MEF's Public Accounting Directorate, DNCP, via SIRTOD) for total revenue, transfer revenue, current expenditure and capital expenditure; and three derived percentages: capital share of expenditure, dependence on transfers, and canon as a share of expenditure. Forestry, oil and fishing canon are left out of the plots because they are negligible in Cusco, but they still count in canon total.

Two definitions deserve care. Total revenue includes **financing**, that is, balances carried over from previous years and borrowing, so it can exceed what a municipality actually raised in the year. Dependence on transfers therefore divides transfer revenue by total revenue *minus* financing. A blank financing value in SIRTOD is read as zero, because SIRTOD does not store zeros.

**Development indicators** (chosen from the shortlist in `panels/development_indicators_shortlist.md`):

| Variable | Measure | Years shown (Cusco) | How the Cusco and province values are built |
|---|---|---|---|
| Pupils per teacher, public regular basic education | ratio | 2008–2025 | Total enrolment / total teachers |
| Public school premises on the electricity grid | % | 2001–2022 (districts 2011–2022) | **Official department series**; districts as published; no province level |
| 2nd-grade pupils at the satisfactory level, reading and maths (ECE) | % | 2007–2016 | **Official department series**; districts as published; no province level |
| Births registered late | % | 2005–2020, 2023–2024 | Late / all registered births (a blank is a zero, because SIRTOD stores no zeros). In 2021–2022 the district sums of late births fall 2–7% short of SIRTOD's department total, so those years are hidden for Cusco and every province. District values need at least 20 registered births |
| Formal private-sector workers | total, per 1,000 people | 2015–2025 | Sum; districts without data count as zero (the district sum matches SIRTOD's department total), so per 1,000 people divides by the whole population |
| Districts where a *caja municipal* lends | count | 2003–2025 | Number of districts |
| Computers in municipalities (working or not); working dump trucks | total | computers 2006–2014 and 2016–2024 (2015 is hidden because SIRTOD's department total still includes Kimbiri's erroneous value, blanked below); trucks 2003 and 2006–2024 | Sum, dated to the year before the RENAMU survey (equipment is recorded early the following year). Earlier years fail coverage |
| Municipalities providing serenazgo | % | 2007–2024 | Share of municipalities answering RENAMU. 2004–2005 look like a different question (even Cusco reads "no"), and 2006 has no data |
| Vaso de Leche beneficiaries aged 0–6 | total | 2010–2011, 2013, 2015–2024 | Sum. 2012 fails coverage (7 districts missing) and 2014 has source errors in four districts |
| Monetary poverty | interval midpoint and bounds | Cusco 2007–2025; districts 2013 | **Official department series** (ENAHO interval for the group of departments that includes Cusco); districts from the 2013 poverty map; no province level |

Municipal staff, the three-services school share, DNI holders and the frost and rain shocks were left out on purpose: staff has counting breaks in 2011, 2015, 2019 and 2023; the school share has only 8 usable years; DNI holders are a denominator rather than an indicator; and the weather shocks are municipal self-reports that end in 2018.

**Census snapshots** (2007 and 2017) for district maps: dwellings with piped water inside, with a sewer connection inside, with grid electricity and with earth floors (predominant material); households whose main cooking fuel is firewood or dung, with internet and with a mobile phone; and the population with Quechua as mother tongue. Province and Cusco values are ratios of the sums of the district counts, which reproduces SIRTOD's official 2017 department figures. Echarate, Vilcabamba and Kimbiri lost territory between the two censuses, so their own 2007 and 2017 values are not comparable. The rural share was left out because the two censuses define it differently.

**Source errors.** Seven single district values are blanked because they contradict the neighbouring years by an order of magnitude: Vaso de Leche 2014 in Cusco, Marcapata, Llusco and Omacha (Cusco reads 32 against 3,785 and 3,411); dump trucks 2004 in Cusco (a zero fill against 22 and 15) and Paucartambo (32 against 2–6); and computers 2015 in Kimbiri (1,631 against 190 and 162). The list is `SOURCE_ERRORS` in `build_harmonized.py`.

**Two new rules came with these indicators.** First, SIRTOD publishes school electricity, the ECE and poverty only as district percentages or intervals, without the counts behind them, so a Cusco value cannot be built from the districts. For these the Cusco line is SIRTOD's official department series, the districts are shown as published, and there is no province level. Second, wherever SIRTOD has its own department total, the district sum is compared with it (tolerance 2%). That total turns out to be the sum of the published districts, so a match proves little on its own: it lets a year through only when the districts without data are young ones (created in 2015 or later, in their first three years), whose territory is still reported under the parent districts, as with the four districts created in 2021. In all other cases the population and money tests still apply. A mismatch, on the other hand, always hides the year, at department and province level. Yes/no municipal services are tested on population coverage only.

## Adding more variables

Any other series from the shortlist can be added the same way: extract it into the district panel with `panels/extract_development_indicators.py --extra <codes>` (or by adding it to the `CORE` list), rebuild the merged panel, and give it an entry in `VARS` in `build_harmonized.py` with its kind (`sum`, `ratio`, `binary`, `official_rate`, `official_interval` or `snapshot`), its display window, an official department code for the coverage check if SIRTOD has one, and bilingual labels.
