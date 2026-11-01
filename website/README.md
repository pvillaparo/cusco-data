# Website data for Cusco-stats (/cusco-data/)

This folder turns the harmonized dataset into the files the Cusco-stats app reads. The app itself will live in its own repository (`pvillaparo/cusco-data`), served at `pvillaparo.github.io/cusco-data/`, with a landing page at `/cusco-stats/` on the main site. The full design is in `PLAN.md`; the first draft of the story text is in `story_draft.md`.

Rebuild after any change to the harmonized data:

```bash
python website/build_boundaries.py      # district and province boundaries (interim source by default)
python website/export_site_data.py      # JSON for the app, into website/site_data/
```

## Files

| Path | What it is |
|---|---|
| `place_names.csv` | Display names with accents for the department, 13 provinces and 116 districts. `review_note` marks names with alternative spellings, to be checked by hand |
| `build_boundaries.py` | Writes `site_data/geo/districts.geojson` and `provinces.geojson`. Interim source: `pe-atlas` 0.0.1 (MIT), a redistribution of the geogpsperu.com 2022 edition of INEI's boundaries, cached in `inputs/`. It has 112 districts; the four created in 2021 are still inside their parents. `--source inei` fetches INEI's IDE 2024 layer instead, once `geosmarthosting.undp.org` is allowed |
| `export_site_data.py` | Writes `site_data/meta.json`, `dictionary.json`, `places.json` and `series/<variable>.json` |
| `site_data/` | The output, about 2 MB in total; each indicator is a separate file of at most ~140 KB, loaded only when needed |

## Format of the series files

`series/<variable>.json` holds `measures → level → place code → [[year, value, ...], ...]`. District points are `[year, value]`; department and province points add the number of districts with data and the number of districts that exist, `[year, value, n_reporting, n_districts]`, so the app can say "112 of 116 districts". **Only values with `display = 1` in the harmonized data are exported**: a missing year is a gap and must be drawn as one.
