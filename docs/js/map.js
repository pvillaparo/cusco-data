// District choropleth: classes on a single-hue ramp (quantile breaks, de-duplicated, labelled with
// the values each class actually holds; discrete classes for small counts; two for yes/no),
// hatched "no data", province outlines, hover/tap tooltip, click (or second tap) to add/remove.
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

// Classes for the values of one year: returns [{color, lo, hi}] and a function value -> color.
export function makeClasses(vals, ramp, binary) {
  const uniq = [...new Set(vals)].sort((a, b) => a - b);
  if (!uniq.length) return { classes: [], color: () => null };
  if (binary || uniq.length <= 2) {
    const cols = uniq.length === 1 ? [ramp[4]] : [ramp[0], ramp[4]];
    const classes = uniq.map((u, i) => ({ color: cols[i], lo: u, hi: u, single: true }));
    return { classes, color: (v) => classes.find((c) => c.lo === v)?.color ?? cols[cols.length - 1] };
  }
  const isInt = uniq.every((v) => Number.isInteger(v));
  let thresholds;
  if (isInt && uniq.length <= 6) {
    thresholds = uniq.slice(1);                                   // one class per value
  } else {
    const q = d3.scaleQuantile().domain(vals).range(d3.range(6));
    thresholds = [...new Set(q.quantiles())].filter((t) => t > uniq[0]);
  }
  const k = thresholds.length + 1;
  const pick = d3.range(k).map((i) => ramp[Math.round((i * (ramp.length - 1)) / Math.max(1, k - 1))]);
  const scale = d3.scaleThreshold().domain(thresholds).range(pick);
  // label each class with the smallest and largest value it actually holds; drop empty classes
  const members = new Map();
  for (const v of vals) {
    const c = scale(v);
    const m = members.get(c) || { lo: Infinity, hi: -Infinity };
    m.lo = Math.min(m.lo, v); m.hi = Math.max(m.hi, v);
    members.set(c, m);
  }
  const classes = pick.filter((c) => members.has(c)).map((c) => ({ color: c, ...members.get(c), single: members.get(c).lo === members.get(c).hi }));
  return { classes, color: (v) => scale(v) };
}

export function drawMap(container, legendEl, opts) {
  const { districts, provinces, values, names, provinceOf, selected, fmt, onToggle, tooltip, ariaLabel,
          strings, binary, intervals } = opts;
  container.textContent = "";
  legendEl.textContent = "";
  const width = Math.max(260, container.clientWidth || 480);
  const height = Math.round(width * 1.12);
  const css = getComputedStyle(document.documentElement);
  const ramp = SEQ.map((v) => css.getPropertyValue(v).trim());
  const nodata = css.getPropertyValue("--nodata").trim();
  const halo = css.getPropertyValue("--text-primary").trim();

  const vals = [...values.values()].filter((v) => v != null);
  const { classes, color } = makeClasses(vals, ramp, binary);
  const label = (v) => (binary ? (v ? strings.yes : strings.no) : fmt(v));

  const projection = d3.geoMercator().fitSize([width, height], { type: "FeatureCollection", features: districts.features });
  const path = d3.geoPath(projection);
  const svg = d3.select(container).append("svg").attr("viewBox", `0 0 ${width} ${height}`)
    .attr("role", "img").attr("aria-label", ariaLabel);

  const defs = svg.append("defs");
  const pat = defs.append("pattern").attr("id", "hatch").attr("width", 6).attr("height", 6)
    .attr("patternUnits", "userSpaceOnUse").attr("patternTransform", "rotate(45)");
  pat.append("rect").attr("width", 6).attr("height", 6).attr("fill", nodata);
  pat.append("line").attr("x1", 0).attr("y1", 0).attr("x2", 0).attr("y2", 6).attr("stroke", "var(--surface-1)").attr("stroke-width", 2);

  let tapped = null;     // touch: first tap shows the value, a second tap on the same district adds it
  const showTip = (ev, d) => {
    const code = d.properties.ubigeo;
    const v = values.get(code);
    const iv = intervals && intervals.get(code);
    tooltip.show({
      head: names.get(code) || code,
      sub: provinceOf.get(code) || "",
      rows: [{ color: null, value: v == null ? strings.noData : label(v), name: "" }],
      note: [iv ? strings.interval(fmt(iv[0]), fmt(iv[1])) : "", ev.pointerType === "touch" ? strings.tapAgain : ""].filter(Boolean).join(" · "),
    }, ev.clientX, ev.clientY);
  };

  svg.append("g").selectAll("path").data(districts.features).join("path")
    .attr("class", "district")
    .attr("d", path)
    .attr("fill", (d) => { const v = values.get(d.properties.ubigeo); return v == null ? "url(#hatch)" : color(v); })
    .on("pointermove", (ev, d) => { if (ev.pointerType === "mouse") showTip(ev, d); })
    .on("pointerleave", (ev) => { if (ev.pointerType === "mouse") tooltip.hide(); })
    .on("pointerup", (ev, d) => {
      const code = d.properties.ubigeo;
      if (ev.pointerType === "mouse") { onToggle(code); return; }
      if (tapped === code) { tapped = null; tooltip.hide(); onToggle(code); return; }
      tapped = code;
      showTip(ev, d);
    });

  svg.append("g").selectAll("path").data(provinces.features).join("path").attr("class", "province").attr("d", path);

  // selected districts: a dark halo under the series colour, so the outline shows on any fill
  const sel = districts.features.filter((d) => selected.has(d.properties.ubigeo));
  const top = svg.append("g").attr("pointer-events", "none");
  top.selectAll("path.halo").data(sel).join("path").attr("class", "halo").attr("d", path)
    .attr("fill", "none").attr("stroke", halo).attr("stroke-width", 4.5).attr("stroke-linejoin", "round");
  top.selectAll("path.sel").data(sel).join("path").attr("class", "sel").attr("d", path)
    .attr("fill", "none").attr("stroke", (d) => selected.get(d.properties.ubigeo)).attr("stroke-width", 2.2).attr("stroke-linejoin", "round");

  for (const c of classes) {
    const lo = label(c.lo), hi = label(c.hi);
    legendEl.append(swatch(c.color, c.single || lo === hi ? lo : `${lo} – ${hi}`));
  }
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
