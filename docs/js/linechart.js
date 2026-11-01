// Line chart: one line per place, gaps for missing years, optional confidence band,
// crosshair + tooltip listing every series at the hovered year, keyboard navigation.
/* global d3 */

const MARGIN = { top: 26, right: 112, bottom: 30, left: 56 };

export function drawLineChart(container, opts) {
  const { series, band, unit, fmt, compact, onYear, ariaLabel, tooltip, coverageText, connect } = opts;
  container.textContent = "";
  const width = Math.max(320, container.clientWidth || 640);
  const narrow = width < 520;
  const m = { ...MARGIN, right: narrow ? 16 : MARGIN.right };
  const height = narrow ? 280 : 340;
  const innerW = width - m.left - m.right;
  const innerH = height - m.top - m.bottom;

  const all = series.flatMap((s) => s.points);
  const bandPts = band ? band.points : [];
  if (!all.length) return null;
  const years = [...new Set(all.map((p) => p.year).concat(bandPts.map((p) => p.year)))].sort((a, b) => a - b);
  const y0 = years[0], y1 = years[years.length - 1];
  const vmax = d3.max(all.map((p) => p.value).concat(bandPts.map((p) => p.hi))) || 1;
  const vmin = Math.min(0, d3.min(all.map((p) => p.value)));

  const x = d3.scaleLinear().domain(y0 === y1 ? [y0 - 1, y1 + 1] : [y0, y1]).range([0, innerW]);
  const y = d3.scaleLinear().domain([vmin, vmax * 1.06]).nice().range([innerH, 0]);

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("role", "img").attr("aria-label", ariaLabel);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  // grid + axes (hairlines, recessive)
  g.append("g").attr("class", "grid")
    .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat(""))
    .call((s) => s.select(".domain").remove());
  const span = y1 - y0;
  const step = span > 16 ? 4 : span > 8 ? 2 : 1;
  let xticks = d3.range(Math.ceil(y0 / step) * step, y1 + 1, step).filter((t) => t >= y0 && t <= y1);
  if (!xticks.includes(y1)) {
    // always label the last year, dropping the previous tick if the two would collide
    if (xticks.length && y1 - xticks[xticks.length - 1] < step * 0.75) xticks.pop();
    xticks.push(y1);
  }
  if (connect) xticks = years;          // snapshots: label only the years observed
  g.append("g").attr("class", "axis").attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x).tickValues(y0 === y1 ? [y0] : xticks).tickFormat(d3.format("d")).tickSizeOuter(0));
  g.append("g").attr("class", "axis")
    .call(d3.axisLeft(y).ticks(5).tickFormat(compact).tickSizeOuter(0))
    .call((s) => s.select(".domain").remove());
  g.append("text").attr("class", "axis-title").attr("x", -m.left + 4).attr("y", -14).text(unit);

  // confidence band (department poverty)
  if (band && bandPts.length) {
    const area = d3.area().defined((d) => d.lo != null).x((d) => x(d.year)).y0((d) => y(d.lo)).y1((d) => y(d.hi));
    g.append("path").attr("d", area(fill(bandPts, y0, y1, ["lo", "hi"]))).attr("fill", "var(--band)");
  }

  // lines: gaps where a year is missing; isolated points drawn as dots
  const line = d3.line().defined((d) => d.value != null).x((d) => x(d.year)).y((d) => y(d.value));
  for (const s of series) {
    const filled = connect ? s.points : fill(s.points, y0, y1, ["value"]);
    g.append("path").attr("d", line(filled)).attr("fill", "none")
      .attr("stroke", s.color).attr("stroke-width", s.isRef ? 2.6 : 2)
      .attr("stroke-linejoin", "round").attr("stroke-linecap", "round");
    const dots = s.points.filter((p) => {
      const prev = s.points.find((q) => q.year === p.year - 1);
      const next = s.points.find((q) => q.year === p.year + 1);
      return !prev || !next || s.points.length <= 3;
    });
    g.append("g").selectAll("circle").data(dots).join("circle")
      .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.value)).attr("r", 4)
      .attr("fill", s.color).attr("stroke", "var(--surface-1)").attr("stroke-width", 2);
  }

  // direct labels at the last point (wide screens, up to 4 series)
  if (!narrow && series.length <= 4) {
    const labels = series.map((s) => {
      const last = s.points[s.points.length - 1];
      return { s, last, x: x(last.year) + 8, y: y(last.value) };
    }).filter((l) => l.last.year === y1)   // only lines that reach the right edge get an end label
      .sort((a, b) => a.y - b.y);
    for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 14) labels[i].y = labels[i - 1].y + 14;
    const overflow = labels.length ? labels[labels.length - 1].y - (innerH - 4) : 0;
    if (overflow > 0) for (const l of labels) l.y -= overflow;       // keep labels above the x axis
    g.append("g").selectAll("text").data(labels).join("text").attr("class", "direct-label")
      .attr("x", (d) => d.x).attr("y", (d) => d.y).attr("dy", "0.35em")
      .text((d) => truncate(d.s.short || d.s.name, 16));
  }

  // crosshair + tooltip
  const cross = g.append("line").attr("class", "crosshair").attr("y1", 0).attr("y2", innerH).style("display", "none");
  const marks = g.append("g");
  const frame = g.append("rect").attr("class", "frame").attr("width", innerW).attr("height", innerH).attr("fill", "none").attr("stroke", "none");
  const overlay = g.append("rect").attr("class", "overlay").attr("width", innerW).attr("height", innerH)
    .attr("tabindex", 0).attr("role", "slider").attr("aria-label", ariaLabel)
    .attr("aria-valuemin", y0).attr("aria-valuemax", y1);
  let current = null;

  const show = (year, clientX, clientY) => {
    current = year;
    overlay.attr("aria-valuenow", year);
    cross.style("display", null).attr("x1", x(year)).attr("x2", x(year));
    const rows = series.map((s) => ({ s, p: s.points.find((q) => q.year === year) }));
    marks.selectAll("circle").data(rows.filter((r) => r.p)).join("circle")
      .attr("cx", (r) => x(year)).attr("cy", (r) => y(r.p.value)).attr("r", 4.5)
      .attr("fill", (r) => r.s.color).attr("stroke", "var(--surface-1)").attr("stroke-width", 2);
    const bp = band && bandPts.find((q) => q.year === year);
    tooltip.show({
      head: String(year),
      rows: rows.map((r) => ({ color: r.s.color, value: r.p ? fmt(r.p.value) : "–", name: r.s.name,
        note: r.p && r.p.n != null && r.p.N != null && r.p.n < r.p.N ? coverageText(r.p.n, r.p.N) : "" })),
      note: bp ? `${band.label}: ${fmt(bp.lo)}–${fmt(bp.hi)}` : "",
    }, clientX, clientY);
    if (onYear) onYear(year);
  };
  const hide = () => { cross.style("display", "none"); marks.selectAll("*").remove(); tooltip.hide(); };
  const nearest = (px) => years.reduce((a, b) => (Math.abs(x(b) - px) < Math.abs(x(a) - px) ? b : a), years[0]);

  overlay.on("pointermove", (ev) => {
    const [px] = d3.pointer(ev);
    show(nearest(px), ev.clientX, ev.clientY);
  }).on("pointerleave", hide).on("blur", hide)
    .on("focus", function () {
      const r = this.getBoundingClientRect();
      const yr = current ?? years[years.length - 1];
      show(yr, r.left + x(yr) * (r.width / innerW), r.top + 8);
    })
    .on("keydown", function (ev) {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(ev.key)) return;
      ev.preventDefault();
      let i = years.indexOf(current ?? years[years.length - 1]);
      if (ev.key === "ArrowLeft") i = Math.max(0, i - 1);
      if (ev.key === "ArrowRight") i = Math.min(years.length - 1, i + 1);
      if (ev.key === "Home") i = 0;
      if (ev.key === "End") i = years.length - 1;
      const r = this.getBoundingClientRect();
      show(years[i], r.left + x(years[i]) * (r.width / innerW), r.top + 8);
    });

  return { years };
}

function fill(points, y0, y1, keys) {
  const byYear = new Map(points.map((p) => [p.year, p]));
  const out = [];
  for (let yr = y0; yr <= y1; yr++) {
    const p = byYear.get(yr);
    if (p) out.push(p);
    else { const blank = { year: yr }; for (const k of keys) blank[k] = null; out.push(blank); }
  }
  return out;
}

function truncate(s, n) { return s.length > n ? s.slice(0, n - 1) + "…" : s; }
