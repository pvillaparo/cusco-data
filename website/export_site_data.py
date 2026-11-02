"""
Export the harmonized Cusco-stats data as compact JSON for the website app (/cusco-data/).

    python website/export_site_data.py

Inputs : harmonized/cusco_stats_long.csv, harmonized/cusco_stats_dictionary.csv,
         website/place_names.csv, panels/canon_spending_district_year.csv (district flags),
         docs/data/geo/*.geojson (from build_boundaries.py)
Output : docs/data/  (served with the app by GitHub Pages)
           meta.json          data vintage, build date, data_cusco commit, CPI base year
           dictionary.json    every variable x measure, labels/units/caveats in en and es
           places.json        department, provinces and districts with display names and flags
           series/<var>.json  displayable values only, by measure, level and place
           geo/               district and province boundaries (copied in place by build_boundaries.py)

Only rows with display = 1 are exported: the app must never show a value the
harmonized data hides, and a missing year is a gap.
"""

import datetime as dt
import json
from decimal import ROUND_HALF_UP, Decimal
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "docs" / "data"   # published by GitHub Pages with the app in docs/
LONG = ROOT / "harmonized" / "cusco_stats_long.csv"
DICT = ROOT / "harmonized" / "cusco_stats_dictionary.csv"
PLACES = HERE / "place_names.csv"
PANEL = ROOT / "panels" / "canon_spending_district_year.csv"
GEO = OUT / "geo" / "districts.geojson"

LEVELS = ["department", "province", "district"]


def digits(variable, measure):
    """Export precision. Percentages and ratios keep 4 decimals so that the app's own
    rounding to 1 decimal is the only rounding (no double rounding)."""
    if measure in ("total", "total_real", "count"):
        return 0
    if measure in ("per_capita", "per_capita_real", "per_1000"):
        return 1
    return 4


def round_half_up(v, nd):
    """Round half away from zero, as the app's number formatting does (Python's round() is half-to-even)."""
    q = Decimal(1).scaleb(-nd)
    return float(Decimal(repr(float(v))).quantize(q, rounding=ROUND_HALF_UP))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return path.stat().st_size


def clean(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return int(v) if float(v).is_integer() else float(v)
    return v


def main():
    long = pd.read_csv(LONG, dtype={"geo_code": str})
    shown = long[long.display == 1].copy()
    dic = pd.read_csv(DICT)
    names = pd.read_csv(PLACES, dtype={"ubigeo": str, "province_code": str}).fillna("")
    name_of = dict(zip(names.ubigeo, names.name))

    # ---- places ----
    panel = pd.read_csv(PANEL, dtype={"ubigeo": str})
    flags = panel.groupby("ubigeo").agg(first_year=("first_year_in_data", "first"),
                                        new_district=("new_district", "first"),
                                        boundary_change_parent=("boundary_change_parent", "first"),
                                        capital_district=("capital_district", "first"))
    with_geometry = set()
    if GEO.exists():
        with_geometry = {f["properties"]["ubigeo"] for f in json.loads(GEO.read_text())["features"]}
    places = {"department": [{"code": "08", "name": "Cusco"}], "province": [], "district": []}
    for _, r in names[names.level == "province"].iterrows():
        places["province"].append({"code": r.ubigeo, "name": r["name"]})
    for _, r in names[names.level == "district"].iterrows():
        fl = flags.loc[r.ubigeo]
        places["district"].append({
            "code": r.ubigeo, "name": r["name"], "province": r.province_code,
            "first_year": int(fl.first_year), "new_district": int(fl.new_district),
            "lost_territory": int(fl.boundary_change_parent), "provincial_capital": int(fl.capital_district),
            "on_map": int(r.ubigeo in with_geometry),
        })
    write_json(OUT / "places.json", places)

    # ---- dictionary ----
    entries = {}
    for _, r in dic.sort_values(["sort_order", "measure"]).iterrows():
        v = r.variable
        if v not in entries:
            entries[v] = {
                "id": v, "order": int(r.sort_order), "kind": r.kind,
                "category": {"en": r.category_en, "es": r.category_es},
                "label": {"en": r.label_en, "es": r.label_es},
                "description": {"en": r.description_en, "es": r.description_es},
                "source": {"en": r.source_en, "es": r.source_es},
                "sirtod_codes": str(r.sirtod_codes),
                "measures": [],
            }
        sub = shown[(shown.variable == v) & (shown.measure == r.measure)]
        if sub.empty:
            continue
        entries[v]["measures"].append({
            "id": r.measure,
            "label": {"en": r.measure_en, "es": r.measure_es},
            "unit": {"en": r.unit_en, "es": r.unit_es},
            "caveat": {"en": clean(r.caveat_en) or "", "es": clean(r.caveat_es) or ""},
            "aggregation": r.aggregation,
            "levels": [lv for lv in LEVELS if (sub.level == lv).any()],
            "years": [int(sub.year.min()), int(sub.year.max())],
            "map": int(r.map_recommended),
        })
    dictionary = [e for e in entries.values() if e["measures"]]
    write_json(OUT / "dictionary.json", dictionary)

    # ---- series ----
    sizes = {}
    for e in dictionary:
        v = e["id"]
        out = {"id": v, "measures": {}}
        for m in e["measures"]:
            mid = m["id"]
            sub = shown[(shown.variable == v) & (shown.measure == mid)]
            nd = digits(v, mid)
            block = {}
            for lv in LEVELS:
                s = sub[sub.level == lv]
                if s.empty:
                    continue
                places_lv = {}
                for code, g in s.sort_values("year").groupby("geo_code"):
                    pts = []
                    for _, row in g.iterrows():
                        val = round_half_up(row.value, nd)
                        val = int(val) if nd == 0 else val
                        if lv == "district":
                            pts.append([int(row.year), val])
                        else:   # aggregates carry their coverage: districts with data / districts
                            pts.append([int(row.year), val, clean(row.n_reporting), clean(row.n_districts)])
                    places_lv[code] = pts
                block[lv] = places_lv
            out["measures"][mid] = block
        sizes[v] = write_json(OUT / "series" / f"{v}.json", out)

    # ---- meta ----
    try:
        commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit = ""
    geo_source = json.loads(GEO.read_text()).get("source", "") if GEO.exists() else ""
    meta = {
        "title": {"en": "Cusco-stats", "es": "Cusco-stats"},
        "data_vintage": "INEI SIRTOD download of 2026-09-22",
        "built": dt.date.today().isoformat(),
        "data_repository": "https://github.com/pvillaparo/cusco-data",
        "data_commit": commit,
        "real_base_year": 2024,
        "deflator": {"en": "Cusco city CPI (INEI), annual average", "es": "IPC de la ciudad de Cusco (INEI), promedio anual"},
        "boundaries": geo_source,
        "n_variables": len(dictionary),
        "n_series": sum(len(e["measures"]) for e in dictionary),
    }
    write_json(OUT / "meta.json", meta)

    total = sum(sizes.values())
    print(f"wrote {len(dictionary)} variables, {meta['n_series']} series; series files {total/1024:.0f} KB "
          f"(largest {max(sizes, key=sizes.get)} {max(sizes.values())/1024:.0f} KB); "
          f"{sum(p['on_map'] for p in places['district'])}/{len(places['district'])} districts on the map")


if __name__ == "__main__":
    main()
