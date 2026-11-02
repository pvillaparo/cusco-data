# Cusco CPI: verification before linking

`cusco_cpi_monthly_sirtod.xlsx` is the export of the two monthly SIRTOD CPI series for Cusco, with original values and no linking or averaging (exported 2026-11-01). This note records what the data itself shows, the decisions confirmed by the project owner, and what remains open. The linked annual CPI is built by `../build_cpi.py` and saved as `cpi_annual.csv`.

## What the data confirms

**Same geography and concept, as far as SIRTOD can tell.** Both series carry the department code 08 (CUSCO), the same source (INEI, Dirección Técnica de Indicadores Económicos) and the same definition text ("Índice general de precios al consumidor ... que consume habitualmente un grupo representativo de familias"). Neither has missing or duplicated months: 262483 runs from January 1996 to December 2021 (312 months) and 516913 from January 2022 to August 2026 (56 months). Two things SIRTOD does not document: whether INEI's index refers to the city of Cusco (the usual practice for regional CPIs, which would make it an urban price index applied to rural districts too), and whether the 2022 methodology changed the basket or the urban area covered.

**The older series contains a rebasing break.** Series 262483 drops 56.3% in January 2010 (December 2009 = 231.43, January 2010 = 101.08). The catalogue label "Base 2009" therefore applies only from January 2010. The 1996–2009 values are on an earlier base, and their 2009 annual average is 228.36. Apart from that month, the largest monthly change in 1996–2021 is 2.33%, so there are no other breaks.

**The newer series is consistent with December 2021 = 100.** January 2022 is 100.41, which would be a January change of +0.41% if December 2021 equals 100. That is plausible next to the older series' last monthly change (+0.52% in December 2021).

## Links considered (see the decisions below: only the 2021–2022 link is applied)

| Break | Proposed method | Factor | Implied change across the break | Plausibility check |
|---|---|---|---|---|
| Within 262483, Dec 2009 → Jan 2010 | If "base 2009" means the 2009 annual average = 100, rescale 1996–2009 by 100 / (2009 average on the old base) | 100 / 228.3583 = 0.437908 | January 2010: −0.26% | January changes in other years range from −1.29% to +0.49%, and 8 of 24 are negative |
| 262483 → 516913, Dec 2021 → Jan 2022 | If "base diciembre 2021" means December 2021 = 100, express the new series on the old base by multiplying it by the old December 2021 value / 100 | 153.96 / 100 = 1.5396 | January 2022: +0.41%; December 2021 keeps its own +0.52% | December-to-December 2022 would be +9.89% (2021: +6.95%) |

Neither link assumes that January equals December, so no month's inflation is erased. Both, however, rest on what the base labels mean, and that needs confirmation from INEI's methodology. Specifically:

1. For base 2009: that the reference is the 2009 annual average (and not, for example, December 2009), and whether INEI publishes an official link factor (*factor de empalme*) for Cusco.
2. For base December 2021: that December 2021 = 100 in the new series for Cusco (and not only for Lima), and whether INEI publishes an official link factor or a linked historical series.
3. Whether the Cusco index covers the same urban area under both methodologies.

## Annual averages

Annual deflators should be the average of the 12 monthly values. 2026 has only January–August, so any 2026 average must be labelled partial (the harmonized dataset drops 2026 for now anyway).

## Decisions confirmed by the project owner (2026-11-01)

| Question | Answer | Consequence |
|---|---|---|
| Does 516913 have December 2021 = 100 for the Cusco index? | **Yes** | Link applied: 516913 × 1.5396 (= 262483's December 2021 value / 100). January 2022 shows +0.41%, and December 2021 keeps its own +0.52%. |
| How should 1996–2009 be linked to base 2009? | **Unresolved.** INEI reports January 2010 inflation for Cusco of **+0.45%**, which neither candidate reproduces (2009-average rescaling gives −0.26%, December-2009 rescaling gives +1.08%). | Months before January 2010 are left out. Constant-soles values start in 2010. |
| Same urban area under both methodologies? | **Unresolved.** INEI identifies it as a Cusco **city** CPI, but whether the footprint is identical in both periods is not documented. | Documented as an open caveat. Applying the city index to all districts is stated as an analytical assumption. |
| Reporting year for real values | **Constant 2024 soles**, using annual-average CPI | Real value = nominal × (2024 average CPI / year's average CPI), labelled "Cusco city CPI". |

For reference only, not applied: a factor of 101.08 / (231.43 × 1.0045) = 0.434807 would reproduce INEI's reported +0.45% for January 2010. It is backed out of a single reported monthly change, though, not an official link factor or overlapping index values, so it does not meet the validation standard set for this project.

## Still needed to extend real values before 2010

An official INEI link factor (*factor de empalme*) for Cusco between the old base and base 2009, or Cusco index values on both bases for at least one overlapping period, plus documentation of the urban area covered in each period.
