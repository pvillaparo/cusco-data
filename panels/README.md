# Canon and municipal finance panel, Cusco districts

`canon_spending_district_year.csv` (and the `.dta` version, which has variable labels) is a district-year panel. It covers the 116 districts of Cusco from 2001 to 2026 and puts canon transfers next to municipal revenues and spending. You can rebuild it from the SIRTOD workbooks in `../SIRTOD` with:

```bash
python panels/build_canon_spending_panel.py
```

The build reads the four district workbooks (`04a`–`04d`), the UBIGEO directory in the guide and, for the population splice, the department workbook (`02`), so the panel can always be traced back to the archived SIRTOD download of 22 September 2026.

## What is in it

There is one row per district and year. A district enters the panel in the first year it appears in SIRTOD, which gives 2,877 rows. All money is in **nominal soles**. The municipal accounts (`munfin_*`) come in thousands of soles in SIRTOD and have been multiplied by 1,000. FONCOMUN is labelled "thousands of soles" in SIRTOD, but its values are already in soles (the department total for 2022 is S/ 457.7 million, about S/ 330 per person), so it is left as published.

| Block | Variables | SIRTOD codes | Years |
|---|---|---|---|
| Canon, main series | `canon_total`, `canon_mining`, `canon_gas`, `canon_hydro`, `canon_forest`, `canon_oil`, `canon_fishing`, `sobrecanon_oil` | 407245–407251, 417639 | 2001–2024 |
| Canon, alternative series | `canon_total_alt` | 414080 | 2014–2024 |
| Other transfers | `foncomun` | 414062 | 2009–2025 |
| MEF-SIAF budget cycle | `siaf_pia`, `siaf_pim`, `siaf_commit`, `siaf_accrued` (devengado), `siaf_paid` (girado), `siaf_exec_rate` | 516869–516874 | 2007–2026 |
| Municipal accounts (MEF public accounting, DNCP) | `munfin_rev_total/current/capital/financing/transfers`, `munfin_exp_total/current/capital/debt` | 122042–122050 | revenue 2003–2025, expenditure 2004–2025 |
| Population | `pop_proj` (as published), `pop_spliced` (one consistent series) | 262234 | 2001–2026 |
| Per capita | the main money variables with suffix `_pc`, divided by `pop_spliced` | — | — |

This panel feeds the display-ready dataset in `../harmonized/`, which the Cusco-stats app ([pvillaparo.github.io/cusco-data](https://pvillaparo.github.io/cusco-data/)) reads. The formula-based instruments built on it for causal work are kept separately in `instruments/`.

## Data choices and caveats

**Which canon series.** The main series (`canon_total`, 407245) runs from 2001 to 2024, and in almost every row it equals the sum of its components. SIRTOD does not store zeros, so a component left blank in a year where the total is observed is set to zero; with oil sobrecanon counted as a component, the components then add up to the total in every row up to 1–2 soles of rounding (`canon_components_incomplete` flags any exception). The main series has one real gap: the four districts created in 2021 have no 407245 values in 2021–2022. The alternative series has them, and it is identical to the main one outside the two capitals discussed next, so those eight rows are filled from it (`canon_filled_from_alt`). Its mining component (414084) is blank there, so mining is taken as the total minus the other components, which matches the department-wide share of mining canon these districts receive. The alternative series 414080 matches the main one everywhere except two capital districts. In **Cusco** it adds the Regional Government's canon (in 2018 the gap equals the GORE transfer to the sol). In **Santa Ana** it adds what looks like the provincial municipality's share. `canon_alt_differs` marks those two districts. Use the main series unless you specifically want money that reaches all entities seated in a district.

**Why there are two spending sources.** SIRTOD files series 122042–122050 under municipal statistics, but its catalogue attributes them to MEF's Public Accounting Directorate (DNCP), not to INEI's RENAMU survey; they are municipal financial statements. Their total spending matches SIAF devengado almost one-for-one: the median ratio is 1.00, and 92% of district-years are within 5%. So the two are not independent measurements. They are complements: SIAF gives the budget cycle (PIA → PIM → devengado) and the execution rate, while the accounts give the split between current and capital spending. `munfin_siaf_gap` flags the district-years where the two sources disagree by more than 5%. They cluster in 2023, which is a broken year in this series: spending is about 23% above SIAF in almost every district, and district revenues are about twice the 2022–2024 average. The harmonized dataset therefore leaves 2023 out of the plots. FONCOMUN has a similar problem in 2016, when SIRTOD's district values are scrambled across districts, so 2016 is left out of the FONCOMUN plots.

**Pre-2004 canon.** Coverage and amounts in 2001–2003 look different (very small transfers, irregular coverage), consistent with the canon distribution rules before the 2004 reform. `canon_pre2004` lets you drop those years easily.

**Population and per-capita variables.** SIRTOD mixes two generations of INEI projections. The older one, built on the 2007 Census, covers 2000–2015. The newer one, built on the 2017 Census, starts in 2018 at district level (2016–2017 are missing) and in 2016 at department level. The two disagree on levels: department population falls 2.8% between 2015 and 2016, and several districts whose borders never changed lose 30–50% between 2015 and 2018 (Coporaque, Mosoc Llacta, Suyckutambo, Llusco…). Dividing by `pop_proj` would therefore create artificial jumps in every per-capita series.

`pop_spliced` fixes this with the standard backward splice. The newer projections are kept exactly as published. The older series is rescaled so that, extended forward at its own 2010–2015 growth rate, it meets the newer series in its first year (2016 for the department, 2018 for districts). This keeps the old series' year-to-year changes and moves only its level. District values for 2016–2017 are interpolated geometrically, and in every year the districts are rescaled to add up to the spliced department total. Because the department meets the new series in 2016 and districts in 2018, this common rescaling factor is 0.98–0.99 before 2018, which adds about 0.8 percentage points to every district's growth in 2016–2017 and again in 2017–2018 (and takes about 0.06 points off 2015–2016). Parents that lost territory before 2018 are spliced together with the districts carved out of them (Echarate with Megantoni, Vilcabamba with Inkawasi and Villa Virgen, and Kimbiri with Villa Kintiarina; only the Megantoni link is documented, the other two are inferred from the data), because the parent's old population covered its children's territory. In 2016–2017 each family's total is interpolated and shared out by 2018 shares, and a child that does not exist yet leaves its share with its parent. After the splice, department growth slows smoothly from about 0.9% a year in the early 2000s to 0.6% in 2015, and then follows the newer projections. Every district change above 9% in a year is a genuine boundary split (Vilcabamba 2016, Kimbiri 2016, Echarate 2017, and Echarate, Kimbiri and Pichari in 2021); the largest change anywhere else is +8.6% (Saylla, 2019). Flags: `pop_backcast` (years ≤ 2015, rescaled old series), `pop_interpolated` (2016–2017), `pop_boundary_mismatch` (split families, 2015–2017, where parent and new-district populations are allocated approximately).

**Boundaries.** Official boundaries are kept as they are. Eight districts in La Convención enter after 2010 (`new_district`): Inkawasi and Villa Virgen in 2015, Villa Kintiarina in 2016, Megantoni in 2017, and Kumpirushiato, Cielo Punco, Manitea and Union Ashaninka in 2021. `boundary_change_parent` marks Echarate, Vilcabamba, Kimbiri and Pichari, whose territory shrank when those districts appeared. Megantoni being carved out of Echarate is documented. The other parent links are inferred from population drops that coincide with the new districts' entry, so check them against the creation laws before building fixed-boundary aggregates. Province and department totals are unaffected by these splits, because a sum does not depend on internal borders.

**Partial years.** In 2026, SIAF figures cover only part of the year (`partial_year`). Canon stops in 2024, and the municipal accounts and FONCOMUN stop in 2025.

**Deflation.** The panel stays in current soles, and `cpi_index` is an empty placeholder. Constant-soles values are added one step later, in `harmonized/`: `harmonized/build_cpi.py` links the two monthly SIRTOD series of the Cusco city CPI (saved in `harmonized/inputs/`) into an annual index, and `harmonized/build_harmonized.py` uses it to express money in constant 2024 soles from 2010 (see `harmonized/inputs/CPI_LINKING_NOTES.md` for why earlier years are not deflated).

## Flags at a glance

`first_year_in_data`, `new_district`, `boundary_change_parent`, `capital_district`, `canon_alt_differs`, `canon_filled_from_alt`, `canon_pre2004`, `canon_components_incomplete`, `partial_year`, `munfin_siaf_gap`, `pop_backcast`, `pop_interpolated`, `pop_boundary_mismatch`.

