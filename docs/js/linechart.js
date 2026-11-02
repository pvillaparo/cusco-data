// Line chart: one line per place, gaps for missing years, optional confidence band,
// crosshair + tooltip listing every series at the chosen year (mouse, touch and keyboard).
/* global d3 */

const MARGIN = { top: 26, right: 112, bottom: 30, left: 56 };

export function drawLineChart(container, opts) {
  const { series, band, unit, fmt, tickFormat, ariaLabel, yearLabel, tooltip, coverageText, intervalText, connect, summary } = opts;
  container.textContent = "";
  const width = Math.max(260, container.clientWidth || 640);
  const narrow = width < 520;
  const m = { ...MARGIN, right: narrow ? 16 : MARGIN.right, top: narrow ? 12 : MARGIN.top };
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
  const yfmt = tickFormat(y.domain()[1]);

  const svg = d3.select(container).append("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("role", "group").attr("aria-label", ariaLabel);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);

  // grid + axes (hairlines, recessive)
  g.append("g").attr("class", "grid").attr("aria-hidden", "true")
    .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat(""))
    .call((s) => s.select(".domain").remove());
  const span = y1 - y0;
  const step = span > 16 ? 4 : span > 8 ? 2 : 1;
  let xticks = d3.range(Math.ceil(y0 / step) * step, y1 + 1, step).filter((t) => t >= y0 && t <= y1);
  if (!xticks.includes(y1)) {
    if (xticks.length && y1 - xticks[xticks.length - 1] < step * 0.75) xticks.pop();
    xticks.push(y1);
  }
  if (connect) xticks = years;
  g.append("g").attr("class", "axis").attr("aria-hidden", "true").attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x).tickValues(y0 === y1 ? [y0] : xticks).tickFormat(d3.format("d")).tickSizeOuter(0));
  g.append("g").attr("class", "axis").attr("aria-hidden", "true")
    .call(d3.axisLeft(y).ticks(5).tickFormat(yfmt).tickSizeOuter(0))
    .call((s) => s.select(".domain").remove());
  if (!narrow) g.append("text").attr("class", "axis-title").attr("aria-hidden", "true").attr("x", -m.left + 4).attr("y", -14).text(unit);

  const art = g.append("g").attr("aria-hidden", "true");
  if (band && bandPts.length) {
    const area = d3.area().defined((d) => d.lo != null).x((d) => x(d.year)).y0((d) => y(d.lo)).y1((d) => y(d.hi));
    art.append("path").attr("d", area(fill(bandPts, y0, y1, ["lo", "hi"]))).attr("fill", "var(--band)");
  }

  const line = d3.line().defined((d) => d.value != null).x((d) => x(d.year)).y((d) => y(d.value));
  for (const s of series) {
    const filled = connect ? s.points : fill(s.points, y0, y1, ["value"]);
    art.append("path").attr("d", line(filled)).attr("fill", "none")
      .attr("stroke", s.color).attr("stroke-width", s.isRef ? 2.6 : 2)
      .attr("stroke-linejoin", "round").attr("stroke-linecap", "round");
    const have = new Set(s.points.map((p) => p.year));
    const dots = s.points.filter((p) => !have.has(p.year - 1) || !have.has(p.year + 1) || s.points.length <= 3);
    art.append("g").selectAll("circle").data(dots).join("circle")
      .attr("cx", (d) => x(d.year)).attr("cy", (d) => y(d.value)).attr("r", 4)
      .attr("fill", s.color).attr("stroke", "var(--surface-1)").attr("stroke-width", 2);
  }

  if (!narrow && series.length <= 4) {
    const labels = series.map((s) => {
      const last = s.points[s.points.length - 1];
      return { s, last, x: x(last.year) + 8, y: y(last.value) };
    }).filter((l) => l.last.year === y1).sort((a, b) => a.y - b.y);
    for (let i = 1; i < labels.length; i++) if (labels[i].y - labels[i - 1].y < 14) labels[i].y = labels[i - 1].y + 14;
    const overflow = labels.length ? labels[labels.length - 1].y - (innerH - 4) : 0;
    if (overflow > 0) for (const l of labels) l.y -= overflow;
    art.append("g").selectAll("text").data(labels).join("text").attr("class", "direct-label")
      .attr("x", (d) => d.x).attr("y", (d) => d.y).attr("dy", "0.35em")
      .text((d) => truncate(d.s.short || d.s.name, 18));
  }

  // interaction layer
  const cross = art.append("line").attr("class", "crosshair").attr("y1", 0).attr("y2", innerH).style("display", "none");
  const marks = art.append("g");
  g.append("rect").attr("class", "frame").attr("width", innerW).attr("height", innerH).attr("fill", "none").attr("stroke", "none");
  const overlay = g.append("rect").attr("class", "overlay").attr("width", innerW).attr("height", innerH)
    .attr("tabindex", 0).attr("role", "slider").attr("aria-label", yearLabel)
    .attr("aria-valuemin", y0).attr("aria-valuemax", y1).attr("aria-valuenow", y1)
    .attr("aria-valuetext", summary(y1));
  let current = null;

  const show = (year, clientX, clientY) => {
    current = year;
    overlay.attr("aria-valuenow", year).attr("aria-valuetext", summary(year));
    cross.style("display", null).attr("x1", x(year)).attr("x2", x(year));
    const rows = series.map((s) => ({ s, p: s.points.find((q) => q.year === year) }));
    marks.selectAll("circle").data(rows.filter((r) => r.p)).join("circle")
      .attr("cx", x(year)).attr("cy", (r) => y(r.p.value)).attr("r", 4.5)
      .attr("fill", (r) => r.s.color).attr("stroke", "var(--surface-1)").attr("stroke-width", 2);
    const bp = band && bandPts.find((q) => q.year === year);
    tooltip.show({
      head: String(year),
      rows: rows.map((r) => {
        const notes = [];
        if (r.p && r.p.lo != null && r.p.hi != null) notes.push(intervalText(fmt(r.p.lo), fmt(r.p.hi)));
        if (r.s.isRef && bp) notes.push(intervalText(fmt(bp.lo), fmt(bp.hi)));
        if (r.p && r.p.n != null && r.p.N != null && r.p.n < r.p.N) notes.push(coverageText(r.p.n, r.p.N));
        return { color: r.s.color, value: r.p ? fmt(r.p.value) : "–", name: r.s.name, note: notes.join(" · ") };
      }),
    }, clientX, clientY);
  };
  const hide = () => { cross.style("display", "none"); marks.selectAll("*").remove(); tooltip.hide(); };
  const nearest = (px) => years.reduce((a, b) => (Math.abs(x(b) - px) < Math.abs(x(a) - px) ? b : a), years[0]);
  const showAtPointer = (ev) => { const [px] = d3.pointer(ev); show(nearest(px), ev.clientX, ev.clientY); };

  overlay
    .on("pointermove", showAtPointer)
    .on("pointerdown", showAtPointer)                       // touch: a tap picks the tapped year
    .on("pointerleave", (ev) => { if (ev.pointerType === "mouse") hide(); })
    .on("blur", hide)
    .on("focus", function () {
      if (!this.matches(":focus-visible")) return;          // keyboard focus only
      const r = this.getBoundingClientRect();
      const yr = current ?? y1;
      show(yr, r.left + x(yr) * (r.width / innerW), r.top + 8);
    })
    .on("keydown", function (ev) {
      if (ev.key === "Escape") { hide(); return; }
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(ev.key)) return;
      ev.preventDefault();
      let i = years.indexOf(current ?? y1);
      if (ev.key === "ArrowLeft") i = Math.max(0, i - 1);
      if (ev.key === "ArrowRight") i = Math.min(years.length - 1, i + 1);
      if (ev.key === "Home") i = 0;
      if (ev.key === "End") i = years.length - 1;
      const r = this.getBoundingClientRect();
      show(years[i], r.left + x(years[i]) * (r.width / innerW), r.top + 8);
    });

  return { years, hide };
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
