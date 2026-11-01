# Canon and municipal finance panel, Cusco districts

`canon_spending_district_year.csv` (and the `.dta` version, which has variable labels) is a district-year panel. It covers the 116 districts of Cusco from 2001 to 2026 and puts canon transfers next to municipal revenues and spending. You can rebuild it from the SIRTOD workbooks in `../SIRTOD` with:

```bash
python panels/build_canon_spending_panel.py
```

The build reads only the four district workbooks (`04a`–`04d`) and the UBIGEO directory in the guide, so the panel can always be traced back to the archived SIRTOD download of 22 September 2026.

## What is in it

There is one row per district and year. A district enters the panel in the first year it appears in SIRTOD, which gives 2,877 rows. All money is in **nominal soles**. RENAMU and FONCOMUN come in thousands of soles in SIRTOD and have been multiplied by 1,000.

| Block | Variables | SIRTOD codes | Years |
|---|---|---|---|
| Canon, main series | `canon_total`, `canon_mining`, `canon_gas`, `canon_hydro`, `canon_forest`, `canon_oil`, `canon_fishing`, `sobrecanon_oil` | 407245–407251, 417639 | 2001–2024 |
| Canon, alternative series | `canon_total_alt` | 414080 | 2014–2024 |
| Other transfers | `foncomun` | 414062 | 2009–2025 |
| MEF-SIAF budget cycle | `siaf_pia`, `siaf_pim`, `siaf_commit`, `siaf_accrued` (devengado), `siaf_paid` (girado), `siaf_exec_rate` | 516869–516874 | 2007–2026 |
| RENAMU finances | `renamu_rev_total/current/capital/financing/transfers`, `renamu_exp_total/current/capital/debt` | 122042–122050 | 2003–2025 |
| Population | `pop_proj` | 262234 | 2001–2026 |
| Per capita | the main money variables with suffix `_pc` | — | — |

## Choices that matter for identification

**Which canon series.** The main series (`canon_total`, 407245) runs from 2001 to 2024, and in almost every row it equals the sum of its components. A component that SIRTOD leaves blank in a year where the total is observed is therefore set to zero. The exceptions are five rows where the components fall short of the total by at most 2.2%, which suggests a component is genuinely missing; these are flagged with `canon_components_incomplete`. The alternative series 414080 matches the main one everywhere except two capital districts. In **Cusco** it adds the Regional Government's canon (in 2018 the gap equals the GORE transfer to the sol). In **Santa Ana** it adds what looks like the provincial municipality's share. `canon_alt_differs` marks those two districts. Use the main series unless you specifically want money that reaches all entities seated in a district.

**Why there are two spending sources.** RENAMU total spending matches SIAF devengado almost one-for-one: the median ratio is 1.00, and 92% of district-years are within 5%. So the two are not independent measurements. They are complements: SIAF gives the budget cycle (PIA → PIM → devengado) and the execution rate, while RENAMU gives the split between current and capital spending, which you need for flypaper or "canon goes to concrete" designs. `renamu_siaf_gap` flags the district-years where the two sources disagree by more than 5%. These cluster in 2023, so treat that year's RENAMU split with care.

**Pre-2004 canon.** Coverage and amounts in 2001–2003 look different (very small transfers, irregular coverage), consistent with the canon distribution rules before the 2004 reform. `canon_pre2004` lets you drop those years easily.

**Population and per-capita variables.** SIRTOD has no population values for 2016–2017. For districts whose boundaries did not change, these are filled by geometric interpolation and flagged with `pop_interpolated`. More importantly, the projections are **rebased on the 2017 Census from 2018 onward** (`pop_vintage_2017census`). Several districts that never changed boundaries lose 30–50% of their projected population between 2015 and 2018 (Mosoc Llacta, Coporaque, Suyckutambo, Llusco…). Per-capita series therefore have a level break in 2018 that comes from the denominator, not from fiscal behaviour. District fixed effects do not absorb it, so consider year effects, a 2018 break dummy interacted with district, or per-capita measures built on a fixed-year population.

**Boundaries.** Official boundaries are kept as they are. Eight districts in La Convención enter after 2010 (`new_district`): Inkawasi and Villa Virgen in 2015, Villa Kintiarina in 2016, Megantoni in 2017, and Kumpirushiato, Cielo Punco, Manitea and Unión Asháninka in 2021. `boundary_change_parent` marks Echarate, Vilcabamba, Kimbiri and Pichari, whose territory shrank when those districts appeared. Megantoni being carved out of Echarate is documented. The other parent links are inferred from population drops that coincide with the new districts' entry, so check them against the creation laws before building fixed-boundary aggregates. Interpolated population is deliberately left missing for the parent districts.

**Partial years.** In 2026, SIAF figures cover only part of the year (`partial_year`). Canon stops in 2024, and RENAMU and FONCOMUN stop in 2025.

**Deflation.** The only CPI in SIRTOD is monthly, and the monthly files (`05`–`08` in the guide) are not in this repository. `cpi_index` is an empty placeholder: fill it with an annual Cusco CPI (base year of your choice) and divide.

## Flags at a glance

`first_year_in_data`, `new_district`, `boundary_change_parent`, `capital_district`, `canon_alt_differs`, `canon_pre2004`, `canon_components_incomplete`, `partial_year`, `renamu_siaf_gap`, `pop_interpolated`, `pop_vintage_2017census`.
