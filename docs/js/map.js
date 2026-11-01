// District choropleth: quantile classes on a single-hue ramp (or two classes for yes/no),
// hatched "no data", province outlines on top, hover tooltip, click to add/remove a district.
/* global d3 */

const SEQ = ["--seq-1", "--seq-2", "--seq-3", "--seq-4", "--seq-5", "--seq-6"];

// GeoJSON (RFC 7946) winds exterior rings counter-clockwise; d3-geo expects clockwise and would
// otherwise read each polygon as "the whole globe except this area". Rewind once, in place.
export function rewind(fc) {
  for (const f of fc.features) {
    if (d3.geoArea(f) > 2 * Math.PI) {
      const g = f.geometry;
      const polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
      for (const p of polys) for (const r of p) r.reverse();
    }
  }
  return fc;
}

export function drawMap(container, legendEl, opts) {
  const { districts, provinces, values, names, provinceOf, selected, fmt, onToggle, tooltip, ariaLabel,
          strings, binary, intervals } = opts;
  container.textContent = "";
  legendEl.textContent = "";
  const width = Math.max(300, container.clientWidth || 480);
  const height = Math.round(width * 1.12);
  const css = getComputedStyle(document.documentElement);
  const ramp = SEQ.map((v) => css.getPropertyValue(v).trim());
  const nodata = css.getPropertyValue("--nodata").trim();

  const vals = [...values.values()].filter((v) => v != null);
  let color, classes = [];
  const uniq = [...new Set(vals)].sort((a, b) => a - b);
  if (binary || uniq.length <= 2) {
    const lo = uniq[0] ?? 0;
    color = (v) => (v === lo && uniq.length > 1 ? ramp[0] : ramp[4]);
    classes = uniq.map((u) => ({ color: color(u), label: binary ? (u ? strings.yes : strings.no) : fmt(u) }));
  } else {
    const k = Math.min(6, uniq.length);
    const q = d3.scaleQuantile().domain(vals).range(ramp.slice(0, k).map((_, i) => ramp[Math.round(i * (ramp.length - 1) / Math.max(1, k - 1))]));
    color = (v) => q(v);
    const breaks = [d3.min(vals), ...q.quantiles(), d3.max(vals)];
    classes = q.range().map((c, i) => ({ color: c, label: `${fmt(breaks[i])} – ${fmt(breaks[i + 1])}` }));
  }

  const projection = d3.geoMercator().fitSize([width, height], { type: "FeatureCollection", features: districts.features });
  const path = d3.geoPath(projection);
  const svg = d3.select(container).append("svg").attr("viewBox", `0 0 ${width} ${height}`)
    .attr("role", "img").attr("aria-label", ariaLabel);

  // hatch pattern for "no data" (texture, not a colour that could be read as a value)
  const defs = svg.append("defs");
  const pat = defs.append("pattern").attr("id", "hatch").attr("width", 6).attr("height", 6)
    .attr("patternUnits", "userSpaceOnUse").attr("patternTransform", "rotate(45)");
  pat.append("rect").attr("width", 6).attr("height", 6).attr("fill", nodata);
  pat.append("line").attr("x1", 0).attr("y1", 0).attr("x2", 0).attr("y2", 6).attr("stroke", "var(--surface-1)").attr("stroke-width", 2);

  svg.append("g").selectAll("path").data(districts.features).join("path")
    .attr("class", (d) => "district" + (selected.has(d.properties.ubigeo) ? " is-selected" : ""))
    .attr("d", path)
    .attr("fill", (d) => { const v = values.get(d.properties.ubigeo); return v == null ? "url(#hatch)" : color(v); })
    .attr("stroke", (d) => selected.get(d.properties.ubigeo) || null)
    .on("pointermove", (ev, d) => {
      const code = d.properties.ubigeo;
      const v = values.get(code);
      const iv = intervals && intervals.get(code);
      tooltip.show({
        head: names.get(code) || code,
        sub: provinceOf.get(code) || "",
        rows: [{ color: null, value: v == null ? strings.noData : (binary ? (v ? strings.yes : strings.no) : fmt(v)), name: "" }],
        note: iv ? strings.interval(fmt(iv[0]), fmt(iv[1])) : "",
      }, ev.clientX, ev.clientY);
    })
    .on("pointerleave", () => tooltip.hide())
    .on("click", (ev, d) => onToggle(d.properties.ubigeo));

  svg.append("g").selectAll("path").data(provinces.features).join("path").attr("class", "province").attr("d", path);

  // selected districts drawn again on top so their outline is not hidden by neighbours
  svg.append("g").selectAll("path").data(districts.features.filter((d) => selected.has(d.properties.ubigeo))).join("path")
    .attr("d", path).attr("fill", "none").attr("stroke", (d) => selected.get(d.properties.ubigeo))
    .attr("stroke-width", 2.6).attr("pointer-events", "none");

  // legend: classes + no data
  for (const c of classes) legendEl.append(swatch(c.color, c.label));
  if (districts.features.some((d) => values.get(d.properties.ubigeo) == null)) {
    const sw = swatch(null, strings.mapNoDataLegend);
    sw.querySelector(".box").style.background = `repeating-linear-gradient(45deg, ${nodata} 0 3px, transparent 3px 6px)`;
    legendEl.append(sw);
  }
}

function swatch(color, label) {
  const s = document.createElement("span");
  s.className = "swatch";
  const b = document.createElement("span");
  b.className = "box";
  if (color) b.style.background = color;
  const t = document.createElement("span");
  t.textContent = label;
  s.append(b, t);
  return s;
}
