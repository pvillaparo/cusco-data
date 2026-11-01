# Cusco-stats: display plan

This plan describes how the harmonized data in `../harmonized/` becomes the **Cusco-stats** project on pvillaparo.github.io. Four decisions frame it:

| Decision | Choice |
|---|---|
| Architecture | Like Rimay: a short landing page inside the Jekyll site, linking to a standalone app in its own repository |
| Audience and language | Researchers first; English by default, with a Spanish toggle |
| Experience | A short narrated story, then a free explorer |
| Data link | Compact JSON files exported from this repository |

## 1. Architecture

The site is a Jekyll *academicpages* theme on GitHub Pages. Its "Miscellaneous" tab reads its cards from `_data/miscellaneous.yml`, which already holds a commented-out "Cusco Stats" entry at `/cusco-stats/`. Following the Quechua pattern (landing page `/quechua/` → app `/rimay/`), there are three pieces:

1. **Card and landing page** in `pvillaparo.github.io`: uncomment the card, and add `_pages/cusco-stats.md` with a two-paragraph description, a preview image, the data sources and an "Open the explorer" button.
2. **The app** in this repository's `docs/` folder, published by GitHub Pages at `pvillaparo.github.io/cusco-data/` (the repository is renamed from `data_cusco` to `cusco-data`). It is a static site: plain HTML, CSS and JavaScript, with no build step and no server. The theme cannot constrain its layout, and it cannot break the academic site.
3. **The data** is exported by `website/export_site_data.py` straight into `docs/data/`, so a yearly update is one rebuild with no copying between repositories.

**Libraries.** I recommend [Observable Plot](https://observablehq.com/plot/), which builds on d3, for both line charts and maps. Its defaults are clean, it handles missing years as true gaps, and it draws maps from GeoJSON without tile servers. That suits 116 districts, works offline, and avoids the usage terms of commercial map tiles. Everything else is plain JavaScript.

## 2. Data for the site

`export_site_data.py` reads `harmonized/cusco_stats_long.csv` and `cusco_stats_dictionary.csv` and writes:

| File | Content | Approximate size |
|---|---|---|
| `data/dictionary.json` | Every variable × measure: labels, units, descriptions, caveats and sources in English and Spanish, category, kind, levels, display years, map flag | ~60 KB |
| `data/series/<variable>.json` | Department, province and district values for that variable, **rows with `display = 1` only**, grouped by measure and place | 5–60 KB each |
| `data/places.json` | UBIGEO, display name with accents, province, level, first year in the data, flags for districts created or split | ~15 KB |
| `data/geo/districts.json`, `provinces.json` | Simplified boundaries (TopoJSON), with provinces dissolved from districts | ~150 KB |
| `data/meta.json` | Data vintage (SIRTOD 22 Sep 2026), build date, and the link to the commit of `data_cusco` used | <1 KB |

**Two inputs are still missing.**

- **Accented place names.** SIRTOD writes names in capitals without accents ("SAN JERONIMO"). The export needs a small hand-checked table of display names for the 116 districts and 13 provinces (San Jerónimo, Unión Asháninka, Quiñota and so on).
- **District boundaries that include the districts created in 2021.** Resolved: INEI's IDE 2024 district layer (served by UNDP), with all 116 districts, simplified with shared borders preserved; see `README.md`.

## 3. What the visitor sees

### 3.1 Story: "Cusco in six charts"

A vertical, scroll-through page. Each step has one chart, two or three sentences of text, and a "Explore this indicator" link that opens the explorer with that view preselected. The draft sequence follows one thread: a resource windfall arrives, municipalities spend it, and we look at what changes around it. It describes; it does not claim causation.

1. **The windfall.** Canon per person in constant 2024 soles, 2010–2024, stacked by gas and mining. It shows the Camisea boom to 2012, the bust to 2020 and the second boom in 2021–2022. Before 2010, nominal values only, marked as such.
2. **Where it lands.** A district map of canon per person (average 2020–2024) next to a bar chart of the ten largest recipients. All ten are in La Convención, the gas province, and Megantoni alone receives about S/ 40,900 per person, against a district median of about S/ 1,240 (current soles). Mining canon matters mostly in Espinar and Chumbivilcas, which a gas/mining toggle on the map makes visible.
3. **What municipalities do with it.** Modified budget and accrued expenditure per person in constant soles, with the execution rate (accrued / modified budget) underneath, 2008–2025. Execution shows no steady trend, but it dips in the boom years, when budgets jump (64% in 2011, 65% in 2023), and recovers afterwards (88% in 2024). The capital share of expenditure stays around 65–74%, except during the 2020 pandemic (56%).
4. **Schools.** Pupils per teacher (24.8 → 13.8), school premises on the grid (46% → 89%), and 2nd-grade reading at the satisfactory level (11% → 49%, 2007–2016), each as a small multiple.
5. **Households.** The 2007 → 2017 census change in piped water, sewerage, internet and firewood cooking, as a dumbbell chart by province, plus the department poverty interval 2007–2025 drawn as a band.
6. **The state's reach.** Late birth registration (34.5% → 2.7%), municipalities providing serenazgo (32% → 94%), districts with a *caja municipal* (6 → 26) and formal private jobs per 1,000 people.

### 3.2 Explorer

A two-column layout on wide screens, which stacks on phones.

- **Left panel.** An indicator picker grouped by category (Canon and transfers · Municipal budget · Municipal finances · Education · Civil registration · Jobs and finance · Municipal services · Social programmes · Census · Poverty). Below it the measure (total, per person, %, ratio), and where available a switch between **constant 2024 soles** (the default from 2010) and current soles.
- **Main panel, top.** A line chart for Cusco, with any provinces or districts the visitor adds by search or by clicking the map. Missing years are drawn as gaps, never bridged. Hovering shows the value, unit and coverage for aggregates ("112 of 116 districts").
- **Main panel, bottom.** For series marked `map_recommended`, a district choropleth with a year slider and a province outline. It uses a single-hue sequential scale, with a diverging scale only where a reference point makes sense. Districts without data are hatched and labelled "no data", never coloured as zero.
- **Beneath both.** A notes box with the indicator's description, caveats and source, taken from the dictionary, and a "Download this view (CSV)" button.

### 3.3 Methods and data

A plain page for researchers. It covers the pipeline (SIRTOD → panels → harmonized → site), the display rules (coverage tests, display windows, excluded years and why), the population splice, the deflator and its open issues, the boundary changes, a suggested citation, links to the `data_cusco` repository and its READMEs, and an update log.

## 4. Display rules the app must enforce

These rules come from the harmonized data. The app should never work around them.

1. **Only rows with `display = 1` are drawn.** Hidden years appear as gaps, and the notes say why ("2023 excluded: inconsistent source data").
2. **Each measure is labelled with its unit on the axis**, and official department series carry a small "official series" tag. For school electricity, the ECE and poverty, the Cusco line does not come from the districts, and there is no province level.
3. **Uncertainty is shown where the data have it.** Poverty appears as an interval band (department) or as a value with interval in the tooltip (districts). Wherever the visitor compares districts, a note says that overlapping intervals cannot be ranked.
4. **Breaks and boundary changes are marked.** A small marker on the axis shows the 2016–2018 change of population source in per-capita series and the La Convención splits (2015–2017, 2021). For Echarate, Vilcabamba and Kimbiri, the census 2007 → 2017 view says the territories differ.
5. **Defaults favour comparability.** Per-person rather than totals, constant soles from 2010, and the full display window.

## 5. Language and accessibility

- All indicator text comes from the dictionary's `*_en` and `*_es` fields. A separate `i18n.json` holds the interface strings (buttons, menus, story text). The language choice is kept in the address (`?lang=es`), so shared links open in the right language.
- Numbers are formatted per language: `1,234.5` in English and `1 234,5` in Spanish.
- Colours meet WCAG AA contrast and are safe for colour blindness. Every chart has a text alternative (a short summary plus the data table), and the whole explorer works with the keyboard.
- **Shareable views.** Indicator, measure, places, year and language are encoded in the address, so a researcher can cite or send an exact view.

## 6. Build phases

| Phase | Work | Result |
|---|---|---|
| 1. Data export | `export_site_data.py`; accented names; boundary source checked and simplified | The `data/` folder |
| 2. Explorer | Indicator picker, line chart, district map, notes, CSV download, language toggle, shareable addresses | A usable explorer, reviewed by you |
| 3. Story | The six steps, with text in both languages | The front page of the app |
| 4. Methods page, landing page and card | Jekyll landing page and card in `pvillaparo.github.io`, preview image | Public launch |
| 5. Yearly update | Rerun the pipeline when SIRTOD adds a year (and revisit 2026), re-export, copy, bump the update log | A one-command refresh |

Each phase ends with a check on desktop and phone before moving on.

## 7. Open decisions

1. **App name and address**, for example `cusco-data` (`/cusco-data/`), with the landing page at `/cusco-stats/`.
2. **Visual identity.** Reuse the academic site's colours and fonts, or give the app its own palette, as Rimay has.
3. **Story text.** I can draft it, but the framing is yours, especially how much to say about canon and municipal spending.
4. **Boundary source** for the maps, and its licence (see section 2).
5. **Official province series** for school electricity and the ECE. SIRTOD has them in the province workbook, so they could be added later.
