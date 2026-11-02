# Formula-based instruments for canon (research extension)

> Note: the first-stage tables below were computed before canon for the four districts created in 2021 was filled in for 2021–2022 (see `../README.md`). The instruments have been rebuilt since; rerun the first stages before using the numbers.

These files are **not needed for the descriptive panel or the Cusco-stats plots**. They build shift-share instruments for gas and mining canon, for anyone who later wants to estimate causal effects of canon on municipal outcomes. Both merge one-to-one on `ubigeo` × `year` with `../canon_spending_district_year.csv`, and both scripts must be run after `../build_canon_spending_panel.py`:

```bash
python panels/instruments/build_gas_canon_instrument.py
python panels/instruments/build_mining_canon_instrument.py
```

## Formula-based instrument for gas canon

`gas_canon_instrument_district_year.csv` / `.dta` has one row per `ubigeo` × `year` and merges one-to-one with `../canon_spending_district_year.csv`. Rebuild it with `python panels/instruments/build_gas_canon_instrument.py`.

### The idea

The Camisea gas canon is half of the royalties and income tax paid by the concession holders, and the law splits it into fixed tiers: 10% to the producing district, 25% to the municipalities of the producing province (La Convención), 40% to all municipalities of the department, and 25% to the Regional Government and universities. Within the provincial and departmental tiers, MEF allocates money with indices built from population and poverty. The data reproduces this structure closely. The Regional Government receives exactly 25/75 of the municipal total in 2007–2011 (20/75 from 2012, consistent with 5% going to universities). The producing district, the rest of La Convención and the rest of the department keep almost constant shares of the municipal pool (≈26%, 31% and 43%) from 2007 to 2015.

So a district's gas canon is its formula share times a department-wide pool, `canon_gas_dt = s_dt × M_t`. The pool moves with Camisea's production, prices and tax payments, which a district cannot influence. The share moves whenever MEF updates its indices with new population and poverty data, and that part may well be endogenous, because population growth responds to the local economy and to canon-funded spending. The instrument therefore freezes the share in a base period and lets only the pool vary:

`gas_iv_dt = s_d,2007–09 × M_t`

With district and year fixed effects, this is a single-shift shift-share design. Identification comes entirely from the cross-section of base shares (Goldsmith-Pinkham, Sorkin & Swift 2020): districts with a larger formula share get more money precisely when the pool booms (2010–2014 and 2021–2024) and less when it busts (2015–2020). The exclusion restriction is that nothing else that varies with `s_d × M_t` affects the outcome. Because the shares are built partly from population and poverty, the natural threats are differential trends by size or poverty. Two checks follow naturally: controls such as `gas_share_base × year` or base characteristics × year fixed effects, and showing that results don't depend on the producing district. The pool's non-monotone path (boom, bust, boom) helps separate the instrument from smooth trends.

### Variables

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

### First stage

`canon_gas_pcb` regressed on the instrument, with district and year fixed effects, standard errors clustered by district, `iv_sample == 1`, and base years dropped:

| Sample | `gas_iv_pc` | `gas_iv_rebased_pc` |
|---|---|---|
| 2010–2019, all (108 districts) | 0.98 (0.04), F = 620 | identical |
| 2010–2019, excluding Echarate | 0.98 (0.06), F = 290 | identical |
| 2010–2019, department tier only (98) | 0.78 (0.05), F = 212 | identical |
| 2010–2024, all | 0.55 (0.13), F = 19 | 0.93 (0.03), F = 838 |
| 2010–2024, department tier only | 0.08 (0.20), F = 0.1 | 0.88 (0.02), F = 1,364 |

Up to 2019 the fixed-share instrument is very strong, and its coefficient is close to one, as the formula predicts. **It breaks down after 2019** because MEF re-indexed the shares on the 2017 Census and the new poverty map. This happened in two steps, in 2020 and 2021, after which shares are stable again (year-to-year correlation 0.999). The re-indexing moved money substantially toward fast-growing urban districts: Saylla's share rose about fourfold, and Kosñipata and San Jeronimo gained about 50–100%, while Colcha and other shrinking rural districts lost about 75%. This is the endogenous channel the instrument is meant to remove, so the choice is between two designs:

- **Clean but shorter:** `gas_iv` on 2008–2019. Shares are predetermined, from 2007–09, and the first stage is strong.
- **Longer but with a stronger assumption:** `gas_iv_rebased` on 2008–2024. From 2020 it uses indices built from 2017-Census population and the 2018 poverty map. These are predetermined for outcomes in 2020–2024, but they partly reflect growth during 2007–2017, which earlier canon may itself have caused.

Running both and showing that they agree over the common period is the natural robustness exercise.

### Caveats

- The base period (2007–09) overlaps the start of the SIAF series (2008). Estimating from 2010 onward keeps the base period out of the sample (`base_overlap`).
- Echarate is the producing district, and its canon per capita is an order of magnitude above everyone else's. It sits in its own tier and leaves the sample in 2016, when Megantoni is carved out. Megantoni has no base share and is not in `iv_sample`. Results should not hinge on Echarate.
- `gas_iv_prod` uses production volumes only, so it has no price or tax variation. Its year-on-year growth correlates 0.76 with the pool's. With year fixed effects it identifies off the same base shares, so it differs from `gas_iv` only in how the years are weighted.
- Gas canon is not the only canon. Mining canon is large in Espinar and Chumbivilcas and follows a similar formula, so consider controlling for it or instrumenting it the same way.

---

## Formula-based instrument for mining canon

`mining_canon_instrument_district_year.csv` / `.dta` has one row per `ubigeo` × `year` and merges one-to-one with the main panel and the gas instrument. Rebuild it with `python panels/instruments/build_mining_canon_instrument.py`.

### Why it is built by source

Gas canon has a single source, so one frozen share times one pool is enough. Mining canon has two sources that switch on at different times. The Espinar mines (Tintaya, then Antapaccay) generate all the local-tier mining money in the base period. Constancia in Chumbivilcas starts generating canon in 2013 and, above all, in 2018–2020 and 2022–2024, when Chumbivilcas's share of the pool jumps from about 5% to 13–21%. A single frozen 2007–09 share would hand Constancia's money to Espinar. The instrument therefore freezes the formula shares *separately for each source and tier* and lets each source's pool move on its own.

### What the data says about the formula

Municipalities receive 75% of mining canon: 40% through a department tier shared by every municipality according to a population and poverty index, 25% through the producing province's municipalities, and 10% to the producing district(s). Three facts make it possible to split each year's money by source:

1. **The department index is the same for gas and mining.** Outside La Convención, Espinar and Chumbivilcas, base-period mining shares are proportional to gas shares (correlation 0.994), and that group's mining-to-gas share ratio is ≈1.0 every year from 2005 to 2024. So a district's department-tier mining receipt is its gas share times the mining pool. La Convención, which gets gas local tiers, is assumed to receive only department-tier mining money.
2. **The local money is always 35/75 of the pool**, as the 10% + 25% tiers predict (0.45–0.48 every year), and it shows up only in Espinar and Chumbivilcas. The residual for other provinces is at most 2.7% of the pool (`pool_local_other`).
3. **Constancia's 10% producing share goes to Velille, Livitaca and Chamaca.** These are the only Chumbivilcas districts whose receipts clearly exceed what the 25% provincial tier predicts. The other districts receive close to (25/35) × their department weight, which supports using department weights for the provincial tier.

### Construction

Shifts (yearly pools): `pool_dept` (department tier), `pool_local_espinar`, `pool_local_chumbivilcas`.
Exposures (frozen shares):

- `w_dept_base`: the district's share of the department tier in 2007–09.
- `l_espinar_base`: its share of Espinar's local money in 2007–09, observed directly.
- `l_chumb_base`: its formula share of Constancia's local money, (25/35) × its share of Chumbivilcas's department weights + (10/35) × its producing split. The split is Velille 0.56, Livitaca 0.23, Chamaca 0.21, the average excess receipts over 2018–2024.

`mining_iv = w_dept_base × pool_dept + l_espinar_base × pool_local_espinar + l_chumb_base × pool_local_chumbivilcas`

`mining_iv_rebased` uses the same construction with 2021–23 shares from 2020 onward, the analogue of the gas version. `mining_iv_naive` (single base share × total pool) is included only for comparison. Per-capita versions (`_pc`) and outcomes (`_pcb`) use 2007–09 population. `source_exposure` labels each district `espinar`, `chumbivilcas`, `constancia_producing` or `department_only`. `iv_sample` is defined as for gas.

### First stage

`canon_mining_pcb` regressed on each instrument, with district and year fixed effects, standard errors clustered by district, `iv_sample == 1`, and base years dropped:

| Sample | Naive single pool | By source (`mining_iv_pc`) | Rebased |
|---|---|---|---|
| 2010–19, all (108) | 0.89 (0.04), F = 608 | 1.00 (0.05), F = 332 | same |
| 2010–19, excluding Espinar province (100) | 1.00 (0.13), F = 56 | 1.00 (0.09), F = 128 | same |
| 2010–24, all | 0.76 (0.10), F = 63 | 0.92 (0.11), F = 73 | 0.98 (0.03), F = 1,404 |
| 2010–24, department-only districts (92) | 0.49 (0.17), F = 8 | 0.32 (0.16), F = 4 | 0.90 (0.03), F = 829 |
| 2010–24, Chumbivilcas (8) | 1.48 (4.51), F ≈ 0 | 0.62 (0.17), F = 13 | 1.00 (0.31), F = 10 |

Up to 2019 the source-based instrument has a coefficient of exactly 1.00, as the formula predicts, while the naive one is attenuated (0.89) because it misplaces Constancia's money. Within Chumbivilcas the naive instrument has no power at all, while the source-based one does. After 2019 the same MEF re-indexing seen for gas weakens the frozen department weights, and the rebased version restores the first stage, under the same stronger assumption explained in the gas section.

### Using both instruments together

After removing district and year effects, `gas_iv_pc` and `mining_iv_pc` are almost uncorrelated (−0.003 for 2010–19; 0.07 for the rebased versions over 2010–24). In a joint first stage, each instrument predicts its own canon with a coefficient ≈ 1 and the other's with ≈ 0. Gas and mining canon can therefore enter the same 2SLS as separate endogenous variables. That is useful if you suspect that different revenue sources have different effects, for instance because canon from a mine inside the district comes with conflict, migration or company-financed projects that gas money from far away does not.

### Caveats

- **Espinar and Coporaque dominate the Espinar pool**, and Espinar district alone receives about half of it. Results should survive dropping Espinar province (row 2 of the table).
- **The Constancia producing split is estimated from post-2017 receipts.** It reflects where the mine sits, not anything the districts chose, but it is the one exposure not fixed in the base period. Replacing it with an equal three-way split is an easy robustness check.
- **Chumbivilcas has only 8 districts**, so inference on Constancia-specific effects rests on very few clusters. Wild-cluster bootstrap or randomization inference is advisable.
- **The 2013 Chumbivilcas money is small (S/ 2M) and lands mostly in Llusco and Quiñota**, not in the Constancia districts, probably from smaller operations. It is absorbed into the Chumbivilcas pool.
- **Mining data before 2005 is unusable** (eight districts in 2004), so the pools are set to missing before 2005.
