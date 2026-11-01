"""
District and province boundaries of Cusco for the Cusco-stats maps.

    python website/build_boundaries.py                 # interim source (pe-atlas)
    python website/build_boundaries.py --source inei   # official INEI IDE 2024 layer (needs network access)

Output: website/site_data/geo/districts.geojson and provinces.geojson
(WGS84, coordinates rounded to 4 decimals, about 10 m).

Sources
  * pe-atlas 0.0.1 (MIT licence; https://www.npmjs.com/package/pe-atlas), a TopoJSON
    redistribution of the geogpsperu.com 2022 edition of INEI's boundaries. It has 112
    Cusco districts: the four created in 2021 (Kumpirushiato, Cielo Punco, Manitea,
    Unión Asháninka) are still inside their parent districts. INTERIM.
  * INEI district boundaries, IDE 2024 edition ("Distritos_INEI_2025_IDE_2024"), as
    served by UNDP's ArcGIS hosting. Includes the 2021 districts. Requires
    geosmarthosting.undp.org to be allowed in the session's network settings.
"""

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "site_data" / "geo"
PE_ATLAS_URL = "https://registry.npmjs.org/pe-atlas/-/pe-atlas-0.0.1.tgz"
PE_ATLAS_CACHE = HERE / "inputs" / "pe-atlas-0.0.1"
INEI_LAYER = ("https://geosmarthosting.undp.org/arcgis/rest/services/Hosted/"
              "Distritos_INEI_2025_IDE_2024/FeatureServer/0/query")
DIGITS = 4


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


def from_inei():
    params = {"where": "ubigeo LIKE '08%'", "outFields": "*", "f": "geojson", "outSR": "4326",
              "geometryPrecision": str(DIGITS), "maxAllowableOffset": "0.0005"}
    url = INEI_LAYER + "?" + urllib.parse.urlencode(params)
    gj = json.loads(urllib.request.urlopen(url, timeout=120).read())
    districts = []
    for f in gj["features"]:
        props = {k.lower(): v for k, v in f["properties"].items()}
        f["id"] = str(props.get("ubigeo"))
        f["properties"] = {"name": props.get("nombdist") or props.get("distrito") or ""}
        districts.append(f)
    # Province outlines did not change with the 2021 districts; take them from pe-atlas.
    _, provinces, _ = from_pe_atlas()
    note = "INEI district boundaries, IDE 2024 edition (Distritos_INEI_2025_IDE_2024, UNDP-hosted service)"
    return districts, provinces, note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["pe-atlas", "inei"], default="pe-atlas")
    args = ap.parse_args()
    districts, provinces, note = from_pe_atlas() if args.source == "pe-atlas" else from_inei()
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
