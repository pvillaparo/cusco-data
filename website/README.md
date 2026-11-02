# Website data for Cusco-stats (/cusco-data/)

This folder turns the harmonized dataset into the files the Cusco-stats app reads. The app lives in this same repository, in `docs/`, and GitHub Pages publishes that folder at `pvillaparo.github.io/cusco-data/`; the landing page is at `/cusco-stats/` on the main site. The Methods & data page is `docs/methods.html`, with its text in `docs/js/methods-text.js`. The data files go to `docs/data/`. The full design is in `PLAN.md`; the editing draft of the story text is in `story_draft.md`, and the text the page actually shows is in `docs/js/story-text.js`.

Rebuild after any change to the harmonized data:

```bash
python website/build_boundaries.py      # district and province boundaries (INEI IDE 2024, from the cached download)
python website/export_site_data.py      # JSON for the app, into docs/data/
```

## Files

| Path | What it is |
|---|---|
| `place_names.csv` | Display names with accents for the department, 13 provinces and 116 districts. `review_note` marks names with alternative spellings, to be checked by hand |
| `build_boundaries.py` | Writes `docs/data/geo/districts.geojson` (116 districts) and `provinces.geojson` (13). Source: **INEI's district boundaries, IDE 2024 edition** (`Distritos_INEI_2025_IDE_2024`, served by UNDP), downloaded on 2026-11-01 at full resolution and cached in `inputs/inei_ide2024_cusco_districts.geojson`. The polygons are simplified locally to about 55 m with shared borders preserved (python package `topojson`), and province outlines are the union of their districts (`shapely`), so the two layers line up exactly. Laguna Langui-Layo (Canas) is outside every district and shows as a gap. `--refresh` re-downloads the layer; `--source pe-atlas` rebuilds the older interim version (112 districts). Rebuilding needs `pip install topojson shapely` |
| `export_site_data.py` | Writes `docs/data/meta.json`, `dictionary.json`, `places.json` and `series/<variable>.json` |
| `../docs/data/` | The output, about 3 MB in total (series about 2 MB, boundaries about 0.65 MB); each indicator is a separate file of at most ~140 KB, loaded only when needed |

## Format of the series files

`series/<variable>.json` holds `measures → level → place code → [[year, value, ...], ...]`. District points are `[year, value]`; department and province points add the number of districts with data and the number of districts that exist, `[year, value, n_reporting, n_districts]`, so the app can say "112 of 116 districts". **Only values with `display = 1` in the harmonized data are exported**: a missing year is a gap and must be drawn as one.
