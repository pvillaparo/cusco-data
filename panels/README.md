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

---

# Formula-based instrument for gas canon

`gas_canon_instrument_district_year.csv` / `.dta` has one row per `ubigeo` × `year` and merges one-to-one with the panel above. Rebuild it with `python panels/build_gas_canon_instrument.py`, after building the main panel.

## The idea

The Camisea gas canon is half of the royalties and income tax paid by the concession holders, and the law splits it into fixed tiers: 10% to the producing district, 25% to the municipalities of the producing province (La Convención), 40% to all municipalities of the department, and 25% to the Regional Government and universities. Within the provincial and departmental tiers, MEF allocates money with indices built from population and poverty. The data reproduces this structure closely. The Regional Government receives exactly 25/75 of the municipal total in 2007–2011 (20/75 from 2012, consistent with 5% going to universities). The producing district, the rest of La Convención and the rest of the department keep almost constant shares of the municipal pool (≈26%, 31% and 43%) from 2007 to 2015.

So a district's gas canon is its formula share times a department-wide pool, `canon_gas_dt = s_dt × M_t`. The pool moves with Camisea's production, prices and tax payments, which a district cannot influence. The share moves whenever MEF updates its indices with new population and poverty data, and that part may well be endogenous, because population growth responds to the local economy and to canon-funded spending. The instrument therefore freezes the share in a base period and lets only the pool vary:

`gas_iv_dt = s_d,2007–09 × M_t`

With district and year fixed effects, this is a single-shift shift-share design. Identification comes entirely from the cross-section of base shares (Goldsmith-Pinkham, Sorkin & Swift 2020): districts with a larger formula share get more money precisely when the pool booms (2010–2014 and 2021–2024) and less when it busts (2015–2020). The exclusion restriction is that nothing else that varies with `s_d × M_t` affects the outcome. Because the shares are built partly from population and poverty, the natural threats are differential trends by size or poverty. Two checks follow naturally: controls such as `gas_share_base × year` or base characteristics × year fixed effects, and showing that results don't depend on the producing district. The pool's non-monotone path (boom, bust, boom) helps separate the instrument from smooth trends.

## Variables

| Variable | Meaning |
|---|---|
| `gas_pool_muni` | Gas canon to all Cusco municipalities in year t (the shift) |
| `gas_prod_mcf`, `ngl_prod_bbl` | Cusco gas and NGL production (alternative, volume-only shift) |
| `gas_share_actual`, `gas_share_base`, `gas_share_rebase` | District share of the pool: in year t, mean 2007–09, mean 2021–23 |
| `tier_base` | Formula tier in the base period: producing district (Echarate), producing province (rest of La Convención), department |
| `gas_iv` | Main instrument, base share × pool |
| `gas_iv_loo` | Leave-one-out: the pool excludes the district's own transfer |
| `gas_iv_rebased` | Base share until 2019, 2021–23 share from 2020 onward |
| `gas_iv_prod` | Base share × gas production |
| `*_pc`, `*_pcb` | Instruments and outcomes divided by **base-period population** (`pop_base`, mean 2007–09), which avoids the 2018 rebasing break |
| `iv_sample` | Recommended sample: the 108 original districts, 2008–2024, dropping boundary-change parents from the year they split and the new districts (which have no base share) |
| `reindex_period`, `base_overlap` | Year ≥ 2020; year inside the 2007–09 base period |

## First stage

`canon_gas_pcb` regressed on the instrument, with district and year fixed effects, standard errors clustered by district, `iv_sample == 1`, and base years dropped:

| Sample | `gas_iv_pc` | `gas_iv_rebased_pc` |
|---|---|---|
| 2010–2019, all (108 districts) | 0.98 (0.04), F = 620 | identical |
| 2010–2019, excluding Echarate | 0.98 (0.06), F = 290 | identical |
| 2010–2019, department tier only (98) | 0.78 (0.05), F = 212 | identical |
| 2010–2024, all | 0.55 (0.13), F = 19 | 0.93 (0.03), F = 838 |
| 2010–2024, department tier only | 0.08 (0.20), F = 0.1 | 0.88 (0.02), F = 1,364 |

Up to 2019 the fixed-share instrument is very strong, and its coefficient is close to one, as the formula predicts. **It breaks down after 2019** because MEF re-indexed the shares on the 2017 Census and the new poverty map. This happened in two steps, in 2020 and 2021, after which shares are stable again (year-to-year correlation 0.999). The re-indexing moved money substantially toward fast-growing urban districts: Saylla's share rose about fourfold, and Kosñipata and San Jerónimo gained about 50–100%, while Colcha and other shrinking rural districts lost about 75%. This is the endogenous channel the instrument is meant to remove, so the choice is between two designs:

- **Clean but shorter:** `gas_iv` on 2008–2019. Shares are predetermined, from 2007–09, and the first stage is strong.
- **Longer but with a stronger assumption:** `gas_iv_rebased` on 2008–2024. From 2020 it uses indices built from 2017-Census population and the 2018 poverty map. These are predetermined for outcomes in 2020–2024, but they partly reflect growth during 2007–2017, which earlier canon may itself have caused.

Running both and showing that they agree over the common period is the natural robustness exercise.

## Caveats

- The base period (2007–09) overlaps the start of the SIAF series (2008). Estimating from 2010 onward keeps the base period out of the sample (`base_overlap`).
- Echarate is the producing district, and its canon per capita is an order of magnitude above everyone else's. It sits in its own tier and leaves the sample in 2016, when Megantoni is carved out. Megantoni has no base share and is not in `iv_sample`. Results should not hinge on Echarate.
- `gas_iv_prod` uses production volumes only, so it has no price or tax variation. Its year-on-year growth correlates 0.76 with the pool's. With year fixed effects it identifies off the same base shares, so it differs from `gas_iv` only in how the years are weighted.
- Gas canon is not the only canon. Mining canon is large in Espinar and Chumbivilcas and follows a similar formula, so consider controlling for it or instrumenting it the same way.
