"""
District and province boundaries of Cusco for the Cusco-stats maps.

    python website/build_boundaries.py                       # INEI IDE 2024 layer (cached copy in inputs/)
    python website/build_boundaries.py --refresh             # re-download it (needs geosmarthosting.undp.org)
    python website/build_boundaries.py --source pe-atlas     # older interim source, 112 districts

Output: docs/data/geo/districts.geojson and provinces.geojson
(WGS84, coordinates rounded to 4 decimals, about 10 m).

Sources
  * DEFAULT. INEI district boundaries, IDE 2024 edition ("Distritos_INEI_2025_IDE_2024"),
    as served by UNDP's ArcGIS hosting: all 116 Cusco districts, including the four created
    in 2021. Downloaded on 2026-11-01 and cached in inputs/inei_ide2024_cusco_districts.geojson.
    The full-resolution polygons are simplified locally with shared borders preserved
    (python package topojson), and province outlines are the union of their districts
    (shapely), so the two layers line up exactly. Needs: pip install topojson shapely.
    Laguna Langui-Layo (Canas) is outside every district polygon, so it shows as a gap.
  * pe-atlas 0.0.1 (MIT licence; https://www.npmjs.com/package/pe-atlas), a TopoJSON
    redistribution of the geogpsperu.com 2022 edition of INEI's boundaries. It has 112
    Cusco districts: the four created in 2021 are still inside their parent districts.
"""

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs" / "data" / "geo"
PE_ATLAS_URL = "https://registry.npmjs.org/pe-atlas/-/pe-atlas-0.0.1.tgz"
PE_ATLAS_CACHE = HERE / "inputs" / "pe-atlas-0.0.1"
INEI_LAYER = ("https://geosmarthosting.undp.org/arcgis/rest/services/Hosted/"
              "Distritos_INEI_2025_IDE_2024/FeatureServer/0/query")
INEI_CACHE = HERE / "inputs" / "inei_ide2024_cusco_districts.geojson"
DIGITS = 4
SIMPLIFY = 0.0005    # degrees, about 55 m; topology-preserving


def topo_to_features(topo, obj):
    """Decode one TopoJSON object (quantized, delta-encoded arcs) into GeoJSON features."""
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append([x * sx + tx, y * sy + ty])
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            pts = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(pts if not out else pts[1:])
        return out

    feats = []
    for g in topo["objects"][obj]["geometries"]:
        if g["type"] == "Polygon":
            coords = [ring(r) for r in g["arcs"]]
        elif g["type"] == "MultiPolygon":
            coords = [[ring(r) for r in poly] for poly in g["arcs"]]
        else:
            continue
        feats.append({"type": "Feature", "id": g.get("id"), "properties": dict(g.get("properties", {})),
                      "geometry": {"type": g["type"], "coordinates": coords}})
    return feats


def round_coords(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], DIGITS), round(c[1], DIGITS)]
    return [round_coords(x) for x in c]


def from_pe_atlas():
    import io
    import tarfile
    if not (PE_ATLAS_CACHE / "districts-100k.json").exists():
        PE_ATLAS_CACHE.mkdir(parents=True, exist_ok=True)
        data = urllib.request.urlopen(PE_ATLAS_URL, timeout=120).read()
        with tarfile.open(fileobj=io.BytesIO(data)) as tf:
            for name in ["districts-100k.json", "LICENSE.md", "README.md"]:
                (PE_ATLAS_CACHE / name).write_bytes(tf.extractfile(f"package/{name}").read())
    topo = json.loads((PE_ATLAS_CACHE / "districts-100k.json").read_text())
    districts = [f for f in topo_to_features(topo, "districts") if str(f["id"]).startswith("08")]
    provinces = [f for f in topo_to_features(topo, "provinces") if str(f["id"]).startswith("08")]
    note = ("pe-atlas 0.0.1 (MIT), redistribution of the geogpsperu.com 2022 edition of INEI boundaries; "
            "the four districts created in 2021 are drawn inside their parents")
    return districts, provinces, note


def from_inei(refresh=False):
    if INEI_CACHE.exists() and not refresh:
        return parse_inei(json.loads(INEI_CACHE.read_text(encoding="utf-8")))
    import time
    # full resolution: simplification is done locally, preserving shared borders
    params = {"where": "ubigeo LIKE '08%'", "outFields": "ubigeo,distrito,provincia", "f": "geojson",
              "outSR": "4326", "geometryPrecision": "6"}
    url = INEI_LAYER + "?" + urllib.parse.urlencode(params)
    for wait in (0, 2, 4, 8, 16):          # the connection is occasionally reset; retry with backoff
        time.sleep(wait)
        try:
            gj = json.loads(urllib.request.urlopen(url, timeout=120).read())
            break
        except OSError as e:
            print(f"retrying after error: {e}")
    else:
        raise SystemExit("could not reach the INEI layer")
    if "error" in gj:
        raise SystemExit(f"service error: {gj['error']}")
    INEI_CACHE.parent.mkdir(parents=True, exist_ok=True)
    INEI_CACHE.write_text(json.dumps(gj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return parse_inei(gj)


def parse_inei(gj):
    """Simplify with shared borders preserved (topojson), then dissolve provinces from the result."""
    import topojson as tp
    for f in gj["features"]:
        props = {k.lower(): v for k, v in f["properties"].items()}
        f["properties"] = {"ubigeo": str(props.get("ubigeo")), "name": props.get("distrito") or ""}
    topo = tp.Topology(gj, prequantize=False, topology=True, toposimplify=SIMPLIFY, prevent_oversimplify=True)
    simple = json.loads(topo.to_geojson())
    districts = []
    for f in simple["features"]:
        f["id"] = f["properties"]["ubigeo"]
        districts.append(f)
    provinces = dissolve_provinces(districts)
    note = ("INEI district boundaries, IDE 2024 edition (Distritos_INEI_2025_IDE_2024, UNDP-hosted service, "
            "downloaded 2026-11-01); province outlines dissolved from the districts")
    return districts, provinces, note


def dissolve_provinces(districts):
    """Province outlines as the union of their districts, so both layers share the same edges."""
    from shapely.geometry import mapping, shape
    from shapely.ops import unary_union
    groups = {}
    for f in districts:
        groups.setdefault(str(f["id"])[:4], []).append(shape(f["geometry"]).buffer(0))
    out = []
    for code, geoms in sorted(groups.items()):
        merged = unary_union(geoms)        # borders are shared exactly, so no slivers
        out.append({"type": "Feature", "id": code, "properties": {}, "geometry": mapping(merged)})
    for f in out:
        f["geometry"] = json.loads(json.dumps(f["geometry"]))   # tuples -> lists
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["inei", "pe-atlas"], default="inei")
    ap.add_argument("--refresh", action="store_true", help="re-download the INEI layer instead of using the cache")
    args = ap.parse_args()
    districts, provinces, note = from_pe_atlas() if args.source == "pe-atlas" else from_inei(args.refresh)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, feats in [("districts", districts), ("provinces", provinces)]:
        for f in feats:
            f["geometry"]["coordinates"] = round_coords(f["geometry"]["coordinates"])
            f["properties"] = {"ubigeo": str(f["id"]), "name": f["properties"].get("name", "")}
        fc = {"type": "FeatureCollection", "source": note, "features": sorted(feats, key=lambda f: f["properties"]["ubigeo"])}
        (OUT / f"{name}.geojson").write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"wrote {name}.geojson: {len(feats)} features")
    print("source:", note)


if __name__ == "__main__":
    main()
