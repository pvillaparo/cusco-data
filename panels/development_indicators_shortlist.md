# District development indicators for Cusco: a shortlist from SIRTOD

This note began as a proposal and now also documents the decision taken on it. It asks which district-level series in the SIRTOD download (22 September 2026) can describe how developed Cusco's 116 districts are and how they change over time, and which of them could serve as outcomes or controls next to the canon and municipal finance panel in `canon_spending_district_year.csv`. In November 2026 the **core set, with SIRTOD data only**, was approved and built. The section "The approved core panel" near the end describes the resulting files. The rest of the note keeps the full shortlist, so that any series can be added later.

The files are as follows. `development_core_district_year` (CSV and Stata) is the core panel, and `development_core_baseline_district` (CSV and Stata) holds its time-invariant baselines. `extract_development_indicators.py` builds both, and with `--set full` it extracts the whole shortlist instead. `development_indicators_coverage.csv` has coverage statistics for all 1,132 annual district indicators, and `development_indicators_coverage.py` rebuilds that table.

## The short version

The main finding has two sides. SIRTOD is strong on **education inputs, municipal capacity (RENAMU), civil registration and identity, and formal employment**, and these come at full district coverage for 10–22 years. By contrast, it is weak, and in some cases empty, on several things a development economist would normally look at first. There is no recurring district series for child stunting or anemia, poverty, household access to water, sanitation or electricity, or agricultural output. Poverty appears only as the 2013 district poverty map, which is a single year published as confidence intervals. Household services appear only in the 2007 and 2017 Censuses. As a result, a SIRTOD-only panel will describe development mostly through the **supply of public services and state capacity** rather than through household welfare. The welfare side will have to come from the two censuses (for levels and long differences) and from outside sources, which I list at the end.

The second finding matters more for identification. Many of the best-covered series are **themselves things canon money buys**: municipal staff, computers, dump trucks, serenazgo, waste collection, Vaso de Leche coverage. They make good outcomes for a "where does canon go" design. However, they are bad controls, because conditioning on them blocks part of the effect you want to estimate. The truly pre-determined or plausibly exogenous variables in this list are few. They are the 2007 Census baseline, the 2013 poverty map, mining production (which is the source of the treatment rather than an outcome) and, to some degree, centrally provided inputs such as public-school teachers.

## How coverage was measured, and three traps in the raw counts

For every indicator I counted the years with any district value, the districts with a value in each year, the longest run of consecutive years, and the number of years with at least 100 districts. Of the 1,132 district indicators, 672 have at least 10 years, but only 179 have at least 10 years in which 100 or more districts report. Taken at face value, that would suggest most long series are too patchy to use. The raw counts are misleading in three ways, however, and correcting for them changes the picture considerably.

**First, RENAMU yes/no items store only the "yes".** Every indicator phrased as "Municipalidades que…" holds the value 1 for municipalities that answered yes and nothing at all for those that answered no. SIRTOD never stores a zero for them. Seen this way, the "district coverage" of such an item is simply its prevalence. "Municipality provides serenazgo" covers 3 districts in 2004 and 109 in 2024 because serenazgo spread, not because reporting improved. The same is true for RENAMU counts of things a municipality may lack, such as dump trucks or serenazgo staff. Because RENAMU is a census of all municipalities, a missing value in a year when the municipality answered the survey is a "no" or a zero. The extraction script fills it that way, but only for municipalities that report staff or computers that year (106–116 a year from 2004) and only in years when the question was asked at all. There are 327 RENAMU indicators with 10 or more years that fail the raw ≥100-district test. Of these, 121 are pure yes-flags, and almost all the others are counts for which SIRTOD never stores a zero. So once they are read this way, most of them have essentially full coverage. The coverage file flags them with `missing_may_mean_zero`.

**Second, some series are published only where the activity exists.** SBS credit and deposits are reported by the district where a bank or *caja* branch sits. MINEM mining production is reported by the district where a producing unit sits. A missing value therefore means "no branch" or "no production recorded", and filling it with zero is reasonable, provided you remember that this is an inference rather than a measurement. Police crime complaints are different, and here a missing value is truly ambiguous. They are recorded by police station, so a district without a *comisaría* is missing even though crimes happen there and get reported in a neighbouring district. I do **not** fill those.

**Third, boundary changes look like missing data.** Before 2015 the full set of districts is 108, not 116, because the eight new districts in La Convención did not exist yet. So "108 districts in 2010" means complete coverage. The parent districts (Echarate, Vilcabamba, Kimbiri, Pichari) lose territory when the new ones appear, so any count variable such as enrolment, staff or births has a mechanical drop in those four districts. Keep the `boundary_change_parent` flag from the canon panel, or aggregate the new districts back into their parents for fixed-boundary work.

Beyond these traps, I also checked each candidate for level breaks, meaning abrupt jumps in the cross-district median that coincide across districts. These usually signal a change in definition rather than a real change. Such breaks are flagged indicator by indicator below.

## The shortlist, dimension by dimension

The tables give the SIRTOD code, the variable name used by the extraction script, the years, and the number of districts per year after the zero-fill rules described above. "Full" means every district that existed in that year.

### 1. Education

Education is the best-measured dimension, because MINEDU's annual school census (ESCALE) covers every district from 2008 to 2025. The difficulty is that most of it measures **inputs and quantities** rather than learning. Enrolment and teacher counts are clean and complete, so their natural use is in ratios. The pupil–teacher ratio in public basic education is the most informative of these, and its median falls steadily from 24 in 2008 to 11 in 2025. This decline comes partly from falling enrolment (fewer children, plus out-migration) and partly from more teachers. Public-school teachers are paid by the central government through the UGELs, not by municipalities. This makes the ratio less directly endogenous to canon than municipal variables, and it can work as a placebo outcome, because canon should not move it unless municipalities build schools that later attract teachers.

The best long series on learning is the second-grade census test (ECE), 2007–2016. Here the three performance levels add up to 100, so a missing level can be recovered as zero whenever another level is published. Coverage is still uneven: about 70 districts in 2007, only about 31 in 2008, and mostly 98–106 from 2011 onwards (81 in 2012). The ECE also leaves out schools under the intercultural bilingual (EIB) programme, which took a separate fourth-grade test. As a result, the districts missing from the ECE are disproportionately rural and Quechua-speaking, which is selection on exactly the dimension you care about. District percentages also rest on a few dozen pupils in small districts, so they are noisy. The test continued after 2016 with other grades and with sample-based rounds, but SIRTOD does not carry those.

School infrastructure gives a rare repeated measure of network services, but it has a serious break. The median share of public school premises with piped water, sewerage and electricity is about 56% in 2016, 42% in 2018 and 29% in 2019. Its water component falls from a median of 60% to 40% in 2019, and its sewerage component from 65% to 46% in 2021, with both drops hitting almost all districts at once. A real deterioration of that size is implausible, so it is almost certainly a change in the school-census questionnaire. Use 2011–2018 as one series, or include year effects and check robustness by sub-period.

| Code | Variable | What it measures | Source | Years | Districts | Caveats |
|---|---|---|---|---|---|---|
| 411492 | `edu_enrol_ebr` | Enrolment in regular basic education, all sectors | MINEDU–ESCALE | 2008–2025 | full | Count; falls with demography and migration, so use it as a ratio. Parents lose students when new districts split off. |
| 413856 + 417647 | `edu_enrol_ebr_pub`, `edu_teach_ebr_pub` | Public EBR enrolment and teachers, which give the **pupil–teacher ratio** | MINEDU–ESCALE | 2008–2025 | full | Clean. Teachers are a central-government input, so this is a plausible placebo or control. |
| 411495 | `edu_enrol_sec` | Secondary enrolment (divide by primary for a transition proxy) | MINEDU–ESCALE | 2008–2025 | full | Secondary schools are concentrated in district capitals, so pupils may enrol in a neighbouring district. |
| 411521 | `edu_schools_ebr` | Number of EBR educational services (schools and programmes) | MINEDU–ESCALE | 2008–2025 | full | Counts include non-formal early-childhood programmes (PRONOEI), so this is not the number of school buildings. |
| 420006 | `edu_sch_3services` | % of public school premises with water, sewerage and electricity | MINEDU–ESCALE | 2011–2022 | full | **Break in 2019** (questionnaire change). Components are 261186, 261214 and 261276 (see Basic services). |
| 420549 / 420553 (+ 420550, 420552, 420554, 420556) | `ece_read_*`, `ece_math_*` | ECE second grade: % satisfactory / in process / below level, in reading and math | MINEDU–UMC | 2007–2016 | 31 → 106 | Excludes EIB schools (selection on rurality and language); noisy in small districts; weak coverage before 2011. |
| 394676 | `edu_teach_titled_sec` | % of secondary teachers with a teaching degree | MINEDU–ESCALE | 2015–2024 | full | Near ceiling (about 87%) with little variation; low priority. |

### 2. Health, nutrition, vital registration and identity

This is where SIRTOD is weakest. The district file has **no stunting, anemia, health-facility or health-staff series**. The only MINSA district data are the 2021–2022 COVID vaccination counts. What remains are registration and programme variables, which describe the reach of the state more than health itself, so they should be read that way.

Registered births and deaths (RENIEC) run for 20 years. However, they are counted where the event is **registered**, not where the mother or the deceased lived. Births concentrate more and more in hospital registration offices: the district median falls from about 136 to 25 while the regional total falls only from about 28,000 to 17,000. Deaths have an outright failure. The regional total falls from about 6,800 in 2019 to about 2,600 in 2020–2022, in the middle of COVID excess mortality, so those years cannot be used. The more interesting registration variable is the **share of births registered late** (after the legal 60 or 90 days). Its median rises from 21% in 2005 to a peak of 41% in 2011 and then falls to about 7% from 2020. It measures how well civil registration reaches households, but national campaigns and programme conditions (JUNTOS requires DNI) drive it as much as local development does.

Identity documentation (DNI by place of residence) is complete and smooth for 2012–2025. It has a second use that may matter for your per-capita work. In districts whose projected population drops 35–40% between 2015 and 2018 because of the Census rebase, DNI holders hardly move: Coporaque has 15,181 in 2015 and 14,867 in 2018, while projected population goes from 17,846 to 10,632. So DNI counts can serve as a **robustness denominator** free of the 2018 break. Their caveats are that they exceed projected population by 2–19% on average (RENIEC addresses are not updated when people migrate, and deaths are removed with a lag), and that a few districts show reassignment jumps. Mosoc Llacta, for example, goes from 1,209 to 8,778 DNI holders between 2015 and 2018.

| Code | Variable | What it measures | Source | Years | Districts | Caveats |
|---|---|---|---|---|---|---|
| 262226 / 262211 | `vit_births_late`, `vit_births_reg` | Share of births registered late | RENIEC | 2005–2024 | 96–112 | Measures registration reach; driven by policy; counted by place of registration. |
| 262239 | `vit_deaths_reg` | Registered deaths (crude death rate with population) | RENIEC | 2005–2024 | 97–112 | **2020–2022 unusable** (totals collapse during COVID). By place of registration. |
| 424497 / 424508 | `id_dni_total`, `id_dni_minors` | Population with DNI, total and aged 0–17, by residence | RENIEC | 2012–2025 | full | Exceeds projected population; useful as an alternative denominator; occasional reassignment jumps. |
| 516485 | `vdl_benef_0_6` | Vaso de Leche beneficiaries aged 0–6 | RENAMU (municipal report) | 2010–2024 | full | A municipal programme, so it reflects local management as much as need; funded by a formula-based MEF transfer, not by canon. |
| 516513 | `mun_cred_program` | Municipality runs a child growth-monitoring (CRED) programme (0/1) | RENAMU | 2010–2024 | full (after zero-fill) | Prevalence drops from 0.97 to 0.56, with a fall in 2018 that looks like a questionnaire change. Weak. |

### 3. Basic services (water, sanitation, electricity, waste)

No repeated household measure exists here. The 2007 and 2017 Censuses are the only household sources, and they are listed in the last section. The recurring proxies are the network connections of public **school premises** and the municipal waste service. School connections are a fair proxy for whether the public network reaches the district's populated centres. Electricity (median 86% in 2011, 94% in 2022) is the cleanest of the three. Water and sewerage share the questionnaire break described under education. The municipal waste variables are self-reported by the municipality. The daily kilograms collected are visibly rounded (1,000, 1,200, 1,500…), so they are estimates, not measurements.

| Code | Variable | What it measures | Source | Years | Districts | Caveats |
|---|---|---|---|---|---|---|
| 261276 | `sch_electric` | % of public school premises on the electricity grid | MINEDU–ESCALE | 2011–2022 | full | Cleanest of the three; nearly saturated by 2020. |
| 261186 | `sch_water` | % of public school premises on piped water | MINEDU–ESCALE | 2011–2022 | full | **Break in 2019.** |
| 261214 | `sch_sewer` | % of public school premises on sewerage | MINEDU–ESCALE | 2011–2022 | full | **Break in 2021.** |
| 516459 | `mun_waste_kg_day` | Solid waste collected per day (kg); divide by population | RENAMU | 2015–2024 | full | Rounded estimates; the per-capita version inherits the 2018 population break. |
| 122051 | `mun_waste_collect` | Municipality collects solid waste (0/1) | RENAMU | 2004–2024 (no 2010) | full (after zero-fill) | Saturates (0.80 → 0.97); informative only before about 2012. |
| 516462 | `mun_cleaning_spend` | Municipal spending on public cleaning (S/) | RENAMU | 2008–2019 | 76–112 | A fiscal variable close to SIAF's functional classification; keep it only if you want a service-specific spending outcome. |

### 4. Economic activity and labour

Formal employment from the electronic payroll (MTPE, *Planilla Electrónica*) is the only recurring measure of local economic activity with broad coverage, from 2015 to 2025. It covers only **formal** jobs, which are a small share of employment in most Cusco districts, and that is why 10–30 districts report nothing in a given year. A missing value there is probably a zero or a cell too small to publish, and the two cannot be told apart. Where a job is located also needs care. Espinar's private employment grows from about 3,800 to 7,600, which tracks the Antapaccay mine. Megantoni, home of Camisea, shows only about 250–1,000 workers, which suggests that contractors and operators registered elsewhere absorb most of the gas workforce. The firm count has a level break: the median falls from 42 in 2015 to 6 in 2016, so drop 2015. Public-sector employment jumps in 2019 and again in 2021 (median 26 → 70 → 108 → 144), which points to coverage changes in the payroll. It is also partly municipal hiring, so it is an outcome of canon by construction.

Credit and deposits (SBS) run for more than two decades, but they exist only where a branch exists. *Cajas municipales* are present in 5 districts in 2002 and 28 in 2025, and commercial banks in 4 and 20. The most useful version for a district panel is therefore probably the **extensive margin**, that is, whether a district has a branch. Amounts are booked at the branch, so neighbouring districts show zero even if their residents borrow there. Amounts are in nominal thousands of soles.

Mining production (MINEM) is not a development outcome. It is the **source** of canon, and it is useful as a first stage or for defining producing districts. Two details matter. First, Constancia's copper is attributed to Velille in 2015–2017 and 2020–2025 but to Livitaca in 2018–2019, so aggregate the two for any producer definition. Second, the 2025 values are identical to 2024 for every producer, so they are a carry-forward placeholder and should be dropped. Informal and artisanal gold does not appear.

| Code | Variable | What it measures | Source | Years | Districts | Caveats |
|---|---|---|---|---|---|---|
| 517303 | `lab_private_workers` | Private-sector workers on the electronic payroll | MTPE | 2015–2025 | 83–107 | Formal jobs only; workers assigned by employer registration, so the gas workforce is undercounted; missing likely means zero but is ambiguous. |
| 517302 | `lab_private_firms` | Private firms on the electronic payroll | MTPE | 2016–2025 (drop 2015) | 77–103 | **Break in 2015/16.** |
| 517438 | `lab_public_workers` | Public-sector workers on the electronic payroll | MTPE | 2016–2025 | 103–113 | Jumps in 2019 and 2021; includes municipal staff, so endogenous to canon. |
| 389746 / 389744 | `fin_cmac_credit`, `fin_cmac_deposits` | Credit and deposits of *cajas municipales* | SBS | 2002–2025 | 5 → 28 with presence; full after zero-fill | Structural zeros; booked at the branch; nominal. |
| 261507 / 261508 | `fin_bank_credit`, `fin_bank_deposits` | Credit and deposits of commercial banks | SBS | 2002–2025 | 4 → 20 with presence; full after zero-fill | Same caveats; concentrated in the districts of Cusco province, Espinar, Santa Ana (Quillabamba) and Sicuani. |
| 261461 / 261580 | `min_gold_kg`, `min_copper_t` | Gold and copper production | MINEM | 2001–2024 (drop 2025) | 1–7 producers | Treatment side, not an outcome; attribution moves between districts (Constancia). |

### 5. Poverty

No recurring district poverty measure exists in SIRTOD. Indicator 427594 is the INEI 2013 district poverty map: 110 districts, published as text intervals such as "43,4 - 57,2", with the misleading title "por grupos de departamentos". It is a single cross-section, so it belongs with the baselines below. Among series with ten years or more, the closest proxy is **Vaso de Leche coverage**. Its total beneficiaries fall from a mean of about 1,250 per district in 2010–2012 to about 650 in 2022–2024. However, the municipality chooses the beneficiaries, and the programme's national budget has stayed roughly flat in nominal terms for years, so the decline mixes falling need with a shrinking real budget. JUNTOS households (2015–2023) and Pensión 65 users (2012–2018) are better poverty proxies, because they are targeted through the national household targeting system (SISFOH), but both fall short of ten years. They are listed in the last section.

| Code | Variable | What it measures | Source | Years | Districts | Caveats |
|---|---|---|---|---|---|---|
| 516484 | `vdl_benef_total` | Vaso de Leche beneficiaries, total | RENAMU (municipal report) | 2010–2024 | full | A municipal programme with a nominally fixed budget; reflects management and budget as much as need. |

### 6. Crime and security

The police series is long but patchy, and it is a good example of a variable that measures supply as much as outcomes. Complaints are recorded by the station that receives them, so only 55–76 districts appear in a given year. Where a station exists, more policing and more serenazgo patrols raise *reported* crime. So if canon-funded serenazgo increases complaints, that is not evidence that canon raises crime. The RENAMU security module (2004–2015) records whether the municipal official perceives home burglary, cattle rustling or alcoholism as a local problem. Cattle rustling (*abigeato*) is the one most specific to rural Cusco. These are perceptions with very high base rates (65–90%), so they move slowly. Serenazgo itself, which spreads from 3 municipalities in 2004 to 109 in 2024, is a clean **municipal spending outcome**.

| Code | Variable | What it measures | Source | Years | Districts | Caveats |
|---|---|---|---|---|---|---|
| 389862 | `crime_complaints` | Crime complaints registered by the police | PNP | 2011–2023 | 55–76 | Recorded by station location; missing is ambiguous (not filled); reporting rises with policing. |
| 122091 | `sec_prob_rustling` | Municipality reports cattle rustling as a problem (0/1) | RENAMU | 2004–2015 | full (after zero-fill) | Perception of one official; high base rate. |
| 122085 | `sec_prob_burglary` | Municipality reports home burglary as a problem (0/1) | RENAMU | 2004–2015 | full (after zero-fill) | Same. |
| 122089 | `sec_prob_alcohol` | Municipality reports alcoholism as a problem (0/1) | RENAMU | 2004–2015 | full (after zero-fill) | Same; nearly saturated by 2015. |
| 122093 / 122156 | `sec_serenazgo`, `sec_serenazgo_staff` | Municipality provides serenazgo; number of serenazgo staff | RENAMU | 2004–2024 | full (after zero-fill) | A spending outcome, not a crime measure. |

### 7. Municipal capacity and services (RENAMU)

RENAMU gives the richest set of long series, and these are the natural outcomes for "what does canon buy". Staff, professionals, computers and dump trucks are counts with full coverage over roughly two decades. Dump trucks are particularly interesting for a "canon goes to concrete" story, because they are capital goods tied to public works. The binary planning instruments (Concerted Development Plan, ROF) say something about institutional quality, but their prevalence moves in strange ways. Having a Development Plan falls from 0.70 to 0.36, which probably reflects plans that expired and were not renewed rather than lost capacity.

Two cautions apply to all of RENAMU. First, total staff has visible breaks. The median jumps from 26 to 61 in 2011, falls from 76 to 32 in 2019 and rises to 98 in 2023. Each of these years is the first year of a new municipal term, so part of this is real political turnover. Still, part of it is almost certainly a change in how contract modalities (CAS, *locación de servicios*) are counted. Look at the components by labour regime before using the total. Second, RENAMU items are not all dated the same way. Items about activity during the year are dated by that year, while items recorded at the survey are dated by the survey year, one year later. This matters for leads and lags relative to canon, and the section "When RENAMU variables are dated" below explains it.

| Code | Variable | What it measures | Source | Years | Districts | Caveats |
|---|---|---|---|---|---|---|
| 121951 | `mun_staff_total` | Total municipal staff | RENAMU | 2004–2024 | full | **Breaks in 2011, 2019 and 2023** (term starts and changes in contract modality). |
| 121953 | `mun_staff_prof` | Professional staff (divide by total for a skill share) | RENAMU | 2004–2024 | full (after zero-fill) | Same breaks, especially 2019. |
| 121992 | `mun_computers` | Computers in the municipality | RENAMU | 2004–2025 | full | Clean, steady growth (mean 12 → 89); a capacity outcome. |
| 121981 | `mun_dump_trucks` | Dump trucks owned | RENAMU | 2003–2025 | full (after zero-fill) | Capital good tied to public works; 2003 not filled (no RENAMU universe that year). |
| 121997 | `mun_internet` | Municipality has internet (0/1) | RENAMU | 2004–2024 | full (after zero-fill) | Saturated by about 2014; useful for 2004–2013 only. |
| 122155 / 516435 | `mun_has_pdc`, `mun_has_rof` | Has a Concerted Development Plan; has an Organisation and Functions Regulation | RENAMU | 2004–2025; 2012–2025 | full (after zero-fill) | Prevalence moves in ways that suggest plan expiry and reporting changes. |

### 8. Environment and natural shocks

All the environmental series in SIRTOD at district level come from RENAMU and are **reported by the municipality**. This creates a specific bias: more capable or better-funded municipalities are more likely to notice and report pollution, so a canon effect on "pollution reported" could be pure measurement. The shock variables (frost, heavy rain, any disaster recorded, 2005–2018) are more useful as controls, because frost and heavy rain matter for agriculture and for emergency spending. They are still self-reports, and satellite or station climate data would be better (see below).

| Code | Variable | What it measures | Source | Years | Districts | Caveats |
|---|---|---|---|---|---|---|
| 122146 / 122148 | `env_frost`, `env_heavy_rain` | Municipality recorded frost / heavy rain (0/1) | RENAMU | 2005–2018; 2004–2018 | full (after zero-fill) | Self-reported shocks; prefer climate data for exogeneity. |
| 516558 | `env_disaster_any` | Municipality recorded any natural hazard or disaster (0/1) | RENAMU | 2005–2018 | full (after zero-fill) | Nearly saturated (≥0.95); little variation. |
| 122138 | `env_pollution_deforest` | Reports pollution from deforestation and burning (0/1) | RENAMU | 2004–2025 | full (after zero-fill) | Perception; rises 0.26 → 0.51; reporting rises with capacity. |
| 122136 / 122137 | `env_pollution_sewage`, `env_pollution_burning` | Reports pollution from wastewater / garbage burning (0/1) | RENAMU | 2004–2025 | full (after zero-fill) | Same. |
| 516382 | `env_mgmt_instruments` | Has environmental management instruments (0/1) | RENAMU | 2006–2025 | full (after zero-fill) | A capacity variable (0.40 → 0.87) more than an environmental outcome. |

## Valuable indicators with fewer than ten years

These do not meet the ten-year rule, but several of them are exactly what you would want for baseline heterogeneity or long-difference designs.

**The 2007 and 2017 Censuses (and a 2025 census count).** For about 110 districts, the censuses give household access to piped water inside the dwelling (407209), sewerage inside the dwelling (407217), public electricity (407243), earthen floors (407201), cooking with firewood (407239) and dung (407240), internet and mobile phones (516775, 516777), and Quechua as mother tongue (516749–516750). They also give rural and urban population (262218–262223). With two waves, these support a **2007–2017 long difference**, which lines up neatly with the canon boom. The 2007 values also give a pre-determined baseline you can interact with canon. Both waves are counts, so divide by occupied dwellings (407184) or households. The 2017 Census adds a block with no 2007 counterpart: unmet basic needs (inadequate dwelling 516824, overcrowding 516825, no toilet 516826, children out of school 516827, high economic dependency 516828), household assets (516818–516823) and fertility (516835). Population counts for 2025 (262215, 516654) appear for most districts, but they look preliminary.

**Poverty.** The 2013 district poverty map (427594) covers 110 districts as an interval. Parsing the text into lower and upper bounds gives a mean lower bound of about 28%. JUNTOS beneficiary households (398450, 2015–2023, 89–116 districts, falling from a median of 618 to 277) and Pensión 65 users (426742, 2012–2018, full coverage) are SISFOH-targeted programme counts and are good recurring proxies for the poor population, though they also reflect programme roll-out. The JUNTOS gaps before 2021 are probably districts outside the programme, that is, zeros.

**Education outcomes.** Grade repetition in primary and secondary (394664, 394669; 2015–2022), over-age enrolment (517181, 517182; 2016–2022) and dropout (517185, 517186; 2016–2021) are MINEDU rates with near-full coverage (primary dropout is thinner, at about 76 districts). They are the closest thing to an education *outcome* after the ECE ends.

**Firms.** INEI firm counts (517005, total firms; 516841, firms located at their declared address, "habidas"; 2019–2024; full coverage) are a broader measure of local business activity than the MTPE payroll, because they include small taxpayers without formal employees. Payroll firms by size (517511–517514, 2017–2025) are also available.

**Environment.** Forest loss in hectares (427592, MINAM, 2014–2021) covers only the 22 or so districts with forest, mostly in La Convención, plus Lares and Yanatile (Calca), Kosñipata and Paucartambo, and Camanti and Marcapata (Quispicanchi). That is precisely where the gas canon goes, so it may be worth extending from the original source.

## What to bring in from outside SIRTOD

Since the welfare side is thin, it is worth naming the sources that fill the main gaps. I have not downloaded or checked any of them here. Child stunting and anemia by district can be built from INS-CENAN's nutritional surveillance system (SIEN/HIS, children attended in MINSA facilities), though it is subject to selection into facility use. District poverty exists for other years in the INEI poverty maps (2007, 2009, 2013 and 2018). Annual school-level learning results after 2016 come from MINEDU-UMC. Health facilities and staff come from MINSA's RENIPRESS and INFORHUS registries. Forest loss for all years comes from MINAM's Geobosque. Exogenous weather shocks can come from SENAMHI's PISCO gridded data or from ERA5. Finally, project-level public investment comes from MEF's investment bank (*Banco de Inversiones*) and INFOBRAS. These would let you see what canon builds rather than only what it costs, which seems central to your question.

## Cross-cutting cautions for the canon design

A few issues cut across all dimensions and are worth keeping in view when you choose. **Per-capita variables** inherit the 2018 population rebase. DNI holders give a denominator free of that break that you can use as a robustness check, and fixed-year (2017 Census) population is the other option. **Counts in the four parent districts** fall mechanically when the new districts split off. **Many RENAMU and MTPE series have breaks** at municipal term starts (2011, 2015, 2019, 2023), which coincide with political turnover and with questionnaire revisions, and which year effects only partly absorb if the change interacts with municipal size. And **most of the long, well-covered series are outcomes of municipal spending**, so they belong on the left-hand side. For controls, prefer the 2007 Census baseline, the 2013 poverty map, centrally provided inputs (public-school teachers) and exogenous shocks.

## The approved core panel

The core set keeps one or two series per dimension, chosen to be informative without much redundancy, and it uses SIRTOD only. It is built by

```bash
python panels/extract_development_indicators.py
```

which reads the four district workbooks (about two minutes) and writes two pairs of files, each as CSV and as Stata `.dta` with variable labels.

**`development_core_district_year`** has one row per district and year from 2003 to 2025, which makes 2,547 rows for 116 districts. Each district enters in its first year in the data. It merges one-to-one with the canon panel on `ubigeo` and `year`. The canon panel also covers 2001–2002 and 2026, which the core panel does not. In the other direction, two core rows (Villa Kintiarina 2015 and Megantoni 2016) precede the canon panel because RENIEC reports DNI holders there one year before the districts enter the fiscal data. All other values in those two rows are empty or filled zeros. The panel contains the following variables.

| Dimension | Variable | SIRTOD code | Years | Notes |
|---|---|---|---|---|
| Education | `edu_ptr_pub` (from `edu_enrol_ebr_pub`, `edu_teach_ebr_pub`) | 413856 / 417647 | 2008–2025 | Median 24.3 → 10.7. |
| Education | `sch_electric` | 261276 | 2011–2022 | % public school premises on the grid. |
| Education | `edu_sch_3services` | 420006 | 2011–2018 | 2019–2022 blanked (questionnaire break). |
| Education | `ece_read_satis`, `ece_math_satis` | 420549, 420553 | 2007–2016 | Zero filled when another level is published; 31–107 districts. |
| Health / registration | `vit_late_birth_share` (from `vit_births_late`, `vit_births_reg`) | 262226 / 262211 | 2005–2024 | % of registered births registered late. |
| Health / registration | `id_dni_total` | 424497 | 2012–2025 | Alternative denominator without the 2018 break. |
| Health / nutrition | `vdl_benef_0_6` | 516485 | 2010–2024 | Vaso de Leche beneficiaries aged 0–6. |
| Economy | `lab_private_workers` | 517303 | 2015–2025 | Formal private jobs; missing likely zero but not filled. |
| Economy | `fin_cmac_present` (from `fin_cmac_credit`) | 389746 | 2003–2025 | 1 if a *caja municipal* books credit in the district. |
| Municipal capacity | `mun_staff_total`, `mun_staff_prof`, `mun_prof_share` | 121951, 121953 | 2004–2024 | Breaks at the term starts of 2011, 2019 and 2023. |
| Municipal capacity | `mun_computers` | 121992 | 2004–2025 | |
| Municipal capacity | `mun_dump_trucks` | 121981 | 2003–2025 | Zero filled for RENAMU respondents from 2004. |
| Municipal services | `sec_serenazgo` | 122093 | 2004–2024 | 0/1, zero filled. |
| Shocks | `env_frost`, `env_heavy_rain` | 122146, 122148 | 2005–2018; 2004–2018 | 0/1, zero filled; self-reported. |
| Denominator | `pop_proj` | 262234 | 2003–2025 | Same series as the canon panel, without its 2016–2017 interpolation. |

Every zero-filled variable has a companion `<variable>_filled` flag, and `renamu_respondent` marks municipalities that answered RENAMU in a year, so any fill can be undone. The input counts behind each ratio are kept, so you can rebuild the ratios with other conventions. For example, `edu_ptr_pub`, `vit_late_birth_share` and `mun_prof_share` are left missing when their denominator is zero or missing.

**`development_core_baseline_district`** has one row per district. It holds 2007 and 2017 Census shares, with prefixes `c07_` and `c17_`, for piped water inside the dwelling, sewer connection inside the dwelling, public electricity, earthen floor, cooking with firewood or dung, household internet and mobile phone, Quechua mother tongue and rural population, plus census population (`c07_pop`, `c17_pop`). It also holds the 2013 poverty map as interval bounds and midpoint (`pov13_lo`, `pov13_hi`, `pov13_mid`). Dwelling shares are taken over dwellings with occupants present, because the electricity categories add up exactly to that total. Household shares are taken over the sum of the cooking-fuel categories. Language shares are taken over the sum of the four mother-tongue categories, which is about 94% of the census population because children under three are not asked. Three caveats matter here. First, the eight new districts have no 2007 values, and the four created in 2021 have no 2017 values either. Second, kerosene cooking is not reported in 2017, so the 2017 household total is slightly smaller. Third, and most important, **the rural share is not comparable between the two censuses**. No district is fully rural in 2007, but 64 are in 2017, because the 2007 Census classified every district capital as urban regardless of its size. The aggregate rural share falls (from 45% to 39%) while the unweighted district mean rises (from 63% to 74%). So use `c07_rural` or `c17_rural` as a level, but do not difference them.

**Zero-fill.** The zero-fill rules described above are applied by default, and `--no-fill` turns them off. Each RENAMU item is filled using the respondent universe that matches its timing (next section). `renamu_resp_ref` and `renamu_resp_survey` record those universes, and `renamu_respondent` is either of the two.

## When RENAMU variables are dated

I could not open the RENAMU questionnaires (*cédulas*) themselves, because INEI's website is outside this session's allowed network. So what follows rests on how the data are dated in SIRTOD, together with INEI's description of the survey as summarised in search results, rather than on the questionnaire text. Treat it as well supported but not confirmed by the source documents.

**How the survey works.** According to INEI's 2022 resolution on RENAMU (as summarised in a web search; I could not open the document), municipalities send their information in the first quarter of each year, and it covers January–December of the previous year. INEI's publications report staff "al 31 de diciembre" of that year. So one survey round, collected early in year *Y*+1, produces two kinds of answers: what happened during *Y* (or the stock at 31 December *Y*), and what the municipality has when it fills in the form in *Y*+1.

**How SIRTOD dates them.** SIRTOD appears to date each item by its own reference date, not by the survey round. The clearest evidence is where the series end. The latest round in the download is RENAMU 2025, collected in 2025 about 2024. In every module, items about activity during the year end in **2024**: staff counts (all 45 staff series), serenazgo service and staff, programmes implemented, waste collected, Vaso de Leche beneficiaries, DEMUNA cases, licences granted and council membership. By contrast, items about what the municipality has end in **2025**: computers and other equipment (35 of the 36 equipment series still running after 2017; the exception is internet access), vehicles, the sports infrastructure and health facilities it administers, planning instruments, technical-assistance needs and perceived environmental problems. The entry years of the new districts point the same way. Megantoni, Villa Kintiarina and Inkawasi first report staff one year before they first report computers, which is what you would expect if their first survey round dated staff at 31 December *Y* and equipment at *Y*+1.

**What this means for the core panel.** In SIRTOD's own dating, used by default:

- **Year-*Y* items** describe calendar year *Y*, or 31 December *Y*: `mun_staff_total`, `mun_staff_prof`, `sec_serenazgo`, `vdl_benef_0_6` (and, in the full set, waste, internet, the CRED programme and serenazgo staff).
- **Survey-date items** are recorded early in the year they carry, so the value dated *Y* describes the municipality at about the end of *Y*−1: `mun_computers`, `mun_dump_trucks` (and, in the full set, planning instruments, environmental-management instruments and perceived pollution).
- **Unclassified items** stop before 2019, so the end-year test cannot place them: frost, heavy rain and any disaster recorded (2005–2018), and the security-problem perceptions (2004–2015). Their wording ("registraron" frost or rain) suggests events during the year, but I have not changed their dating.

So for canon transferred and spent in fiscal year *t*, a purchase of trucks or computers made during *t* first appears in the value dated *t*+1, while staff hired during *t* appear in the value dated *t*. To put every RENAMU variable on an end-of-year-*t* basis, build with

```bash
python panels/extract_development_indicators.py --align-renamu
```

which re-dates the survey-date items from *Y*+1 to *Y*. The SIRTOD dates are kept by default, so the panel you approved does not change silently. Computers and dump trucks then run to 2024 instead of 2025.

**A behavioural check, which is inconclusive.** If equipment is recorded at the survey, then municipal capital spending in *t* should predict the change in the series from *t* to *t*+1 rather than from *t*−1 to *t*. With district and year effects (2005–2022), computers behave as expected: the coefficient on log capital spending is 16.3 (t = 2.4) for the forward change and 11.8 (t = 1.8) for the backward change. Dump trucks go the other way, at 0.02 (t = 0.2) forward and 0.18 (t = 1.9) backward. These regressions are too noisy to overturn the evidence from the end years, but they are also a reminder to check that results hold under both datings.

**A related correction.** In SIRTOD, the RENAMU finance series (122042–122050) are sourced to the Ministry of Economy and Finance, not to the RENAMU survey, and they are dated by fiscal year. RENAMU spending matches SIAF accrued spending in the same year in 2008–2022 and 2024, with medians of 1.000–1.003 and 95–100% of districts within 5%, while one-year leads and lags do not match. That is why they agree so closely with SIAF. They should be read as a second view of the same MEF accounts, not as an independent survey measure. In 2023 they match no SIAF year or stage of the budget cycle, and revenue jumps to 2.4 times spending, so that year looks like a data problem rather than a timing shift.

**To confirm.** Once `www.inei.gob.pe` is allowed in the session's network settings, the questionnaires (for example the annex to the RENAMU 2022 resolution and the RENAMU 2025 documents) can be checked item by item for the core variables.

## How to extract the shortlist or other variables

```bash
python panels/extract_development_indicators.py                        # approved core panel + baseline
python panels/extract_development_indicators.py --set full             # whole shortlist above
python panels/extract_development_indicators.py --set full --only education,economy
python panels/extract_development_indicators.py --extra 398450,426742  # add any SIRTOD codes
python panels/extract_development_indicators.py --no-fill              # no zero-fill
python panels/extract_development_indicators.py --keep-suspect         # keep the cells blanked below
python panels/extract_development_indicators.py --align-renamu         # RENAMU survey-date items re-dated to year Y
```

By default the script blanks four groups of cells that this note judges unusable: MINEM production in 2025 (a copy of 2024), the 2015 MTPE firm count, RENIEC registered deaths in 2020–2022, and the three-services school share in 2019–2022. To get the values exactly as SIRTOD publishes them, use both `--no-fill` and `--keep-suspect`.

With `--set full`, the script writes `panels/development_indicators_district_year` with the same structure as the core panel, but with all 57 shortlisted series. To change either set, edit the `CORE` list or the `SHORTLIST` dictionary at the top of the script. Each `SHORTLIST` entry is a SIRTOD code with a variable name, a dimension, a fill rule and a label.
