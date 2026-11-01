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

---

# Formula-based instrument for mining canon

`mining_canon_instrument_district_year.csv` / `.dta` has one row per `ubigeo` × `year` and merges one-to-one with the panel and the gas instrument. Rebuild it with `python panels/build_mining_canon_instrument.py`.

## Why it is built by source

Gas canon has a single source, so one frozen share times one pool is enough. Mining canon has two sources that switch on at different times. The Espinar mines (Tintaya, then Antapaccay) generate all the local-tier mining money in the base period. Constancia in Chumbivilcas starts generating canon in 2013 and, above all, in 2018–2020 and 2022–2024, when Chumbivilcas's share of the pool jumps from about 5% to 13–21%. A single frozen 2007–09 share would hand Constancia's money to Espinar. The instrument therefore freezes the formula shares *separately for each source and tier* and lets each source's pool move on its own.

## What the data says about the formula

Municipalities receive 75% of mining canon: 40% through a department tier shared by every municipality according to a population and poverty index, 25% through the producing province's municipalities, and 10% to the producing district(s). Three facts make it possible to split each year's money by source:

1. **The department index is the same for gas and mining.** Outside La Convención, Espinar and Chumbivilcas, base-period mining shares are proportional to gas shares (correlation 0.994), and that group's mining-to-gas share ratio is ≈1.0 every year from 2005 to 2024. So a district's department-tier mining receipt is its gas share times the mining pool. La Convención, which gets gas local tiers, is assumed to receive only department-tier mining money.
2. **The local money is always 35/75 of the pool**, as the 10% + 25% tiers predict (0.45–0.48 every year), and it shows up only in Espinar and Chumbivilcas. The residual for other provinces is at most 2.7% of the pool (`pool_local_other`).
3. **Constancia's 10% producing share goes to Velille, Livitaca and Chamaca.** These are the only Chumbivilcas districts whose receipts clearly exceed what the 25% provincial tier predicts. The other districts receive close to (25/35) × their department weight, which supports using department weights for the provincial tier.

## Construction

Shifts (yearly pools): `pool_dept` (department tier), `pool_local_espinar`, `pool_local_chumbivilcas`.
Exposures (frozen shares):

- `w_dept_base`: the district's share of the department tier in 2007–09.
- `l_espinar_base`: its share of Espinar's local money in 2007–09, observed directly.
- `l_chumb_base`: its formula share of Constancia's local money, (25/35) × its share of Chumbivilcas's department weights + (10/35) × its producing split. The split is Velille 0.56, Livitaca 0.23, Chamaca 0.22, the average excess receipts over 2018–2024.

`mining_iv = w_dept_base × pool_dept + l_espinar_base × pool_local_espinar + l_chumb_base × pool_local_chumbivilcas`

`mining_iv_rebased` uses the same construction with 2021–23 shares from 2020 onward, the analogue of the gas version. `mining_iv_naive` (single base share × total pool) is included only for comparison. Per-capita versions (`_pc`) and outcomes (`_pcb`) use 2007–09 population. `source_exposure` labels each district `espinar`, `chumbivilcas`, `constancia_producing` or `department_only`. `iv_sample` is defined as for gas.

## First stage

`canon_mining_pcb` regressed on each instrument, with district and year fixed effects, standard errors clustered by district, `iv_sample == 1`, and base years dropped:

| Sample | Naive single pool | By source (`mining_iv_pc`) | Rebased |
|---|---|---|---|
| 2010–19, all (108) | 0.89 (0.04), F = 608 | 1.00 (0.05), F = 332 | same |
| 2010–19, excluding Espinar province (100) | 1.00 (0.13), F = 56 | 1.00 (0.09), F = 128 | same |
| 2010–24, all | 0.76 (0.10), F = 63 | 0.92 (0.11), F = 73 | 0.98 (0.03), F = 1,404 |
| 2010–24, department-only districts (92) | 0.49 (0.17), F = 8 | 0.32 (0.16), F = 4 | 0.90 (0.03), F = 829 |
| 2010–24, Chumbivilcas (8) | 1.48 (4.51), F ≈ 0 | 0.62 (0.17), F = 13 | 1.00 (0.31), F = 10 |

Up to 2019 the source-based instrument has a coefficient of exactly 1.00, as the formula predicts, while the naive one is attenuated (0.89) because it misplaces Constancia's money. Within Chumbivilcas the naive instrument has no power at all, while the source-based one does. After 2019 the same MEF re-indexing seen for gas weakens the frozen department weights, and the rebased version restores the first stage, under the same stronger assumption explained in the gas section.

## Using both instruments together

After removing district and year effects, `gas_iv_pc` and `mining_iv_pc` are almost uncorrelated (−0.003 for 2010–19; 0.07 for the rebased versions over 2010–24). In a joint first stage, each instrument predicts its own canon with a coefficient ≈ 1 and the other's with ≈ 0. Gas and mining canon can therefore enter the same 2SLS as separate endogenous variables. That is useful if you suspect that different revenue sources have different effects, for instance because canon from a mine inside the district comes with conflict, migration or company-financed projects that gas money from far away does not.

## Caveats

- **Espinar and Coporaque dominate the Espinar pool**, and Espinar district alone receives about half of it. Results should survive dropping Espinar province (row 2 of the table).
- **The Constancia producing split is estimated from post-2017 receipts.** It reflects where the mine sits, not anything the districts chose, but it is the one exposure not fixed in the base period. Replacing it with an equal three-way split is an easy robustness check.
- **Chumbivilcas has only 8 districts**, so inference on Constancia-specific effects rests on very few clusters. Wild-cluster bootstrap or randomization inference is advisable.
- **The 2013 Chumbivilcas money is small (S/ 2M) and lands mostly in Llusco and Quiñota**, not in the Constancia districts, probably from smaller operations. It is absorbed into the Chumbivilcas pool.
- **Mining data before 2005 is unusable** (eight districts in 2004), so the pools are set to missing before 2005.
