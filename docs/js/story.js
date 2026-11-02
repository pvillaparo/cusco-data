// "Cusco in six charts": the narrated story above the explorer. Each step is drawn when it
// scrolls into view, from the same data files as the explorer.
/* global d3 */
import { STORY, STORY_LINKS } from "./story-text.js";
import { STRINGS, makeFormatter } from "./i18n.js";
import { drawLineChart } from "./linechart.js";
import { drawMap } from "./map.js";

let ctx = null;            // set by initStory: { lang(), series(v), tooltip, geo (promise of the boundaries), PLACES, cssVar, openExplorer, label(v) }
let firstLang = "en";      // the language buildStory was called with, until initStory
const drawn = new Set();   // steps already drawn (re-drawn on language change or resize)
let observer = null;

const S = () => STORY[ctx ? ctx.lang() : firstLang];
const pts = (json, m, lv = "department", code = "08") =>
  ((json.measures[m] || {})[lv] || {})[code]?.map((p) => ({ year: p[0], value: p[1], n: p[2], N: p[3] })) || [];

// The six sections with their text, before any data has loaded (the Explore buttons wait for initStory).
export function buildStory(lang) {
  firstLang = lang;
  const root = document.getElementById("story-steps");
  root.textContent = "";
  S().steps.forEach((_, i) => {
    const sec = document.createElement("section");
    sec.className = "story-step";
    sec.id = `story-${i + 1}`;
    sec.dataset.step = i;
    sec.innerHTML = `
      <div class="story-text">
        <p class="story-num">${i + 1}</p>
        <h2 class="story-title"></h2>
        <p class="story-body"></p>
        <div class="story-links"></div>
      </div>
      <figure class="story-figure">
        <figcaption class="story-caption"></figcaption>
        <div class="story-chart"></div>
      </figure>`;
    root.append(sec);
  });
  renderStoryText();
}

// Once the data have loaded: Explore buttons, and charts drawn as their step scrolls into view.
export function initStory(context) {
  ctx = context;
  const root = document.getElementById("story-steps");
  if (!root.querySelector(".story-step")) buildStory(ctx.lang());
  renderStoryText();
  observer = new IntersectionObserver((entries) => {
    for (const e of entries) if (e.isIntersecting) drawStep(+e.target.dataset.step);
  }, { rootMargin: "200px 0px" });
  root.querySelectorAll(".story-step").forEach((s) => observer.observe(s));
}

export function renderStoryText() {
  const s = S();
  document.getElementById("story-kicker").textContent = s.kicker;
  document.getElementById("story-title").textContent = s.title;
  document.getElementById("story-intro").textContent = s.intro;
  document.getElementById("story-note").textContent = s.note;
  document.getElementById("story-outro").textContent = s.toExplorer;
  document.getElementById("story-go").textContent = s.goExplorer;
  document.querySelectorAll(".story-step").forEach((sec) => {
    const i = +sec.dataset.step;
    const st = s.steps[i];
    sec.querySelector(".story-title").textContent = st.title;
    sec.querySelector(".story-body").textContent = st.text;
    sec.querySelector(".story-caption").textContent = st.chart;
    const links = sec.querySelector(".story-links");
    links.textContent = "";
    if (!ctx) return;                                          // labels come from the dictionary
    for (const [v, m, real, places] of STORY_LINKS[i]) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "btn-explore";
      b.textContent = `${s.explore}: ${ctx.label(v)}\u00a0→`;   // keep the arrow on the last word's line
      b.addEventListener("click", () => ctx.openExplorer({ v, m, real, places }));
      links.append(b);
    }
  });
}

export function redrawStory() {
  renderStoryText();
  for (const i of [...drawn]) { drawn.delete(i); drawStep(i); }
}

async function drawStep(i) {
  if (drawn.has(i)) return;
  drawn.add(i);
  const sec = document.querySelector(`.story-step[data-step="${i}"]`);
  const box = sec.querySelector(".story-chart");
  try {
    await [step1, step2, step3, step4, step5, step6][i](box, S().steps[i]);
  } catch (e) {
    console.error(e);
    box.textContent = "";
    drawn.delete(i);
  }
}

// ---------- shared helpers ----------
function fmts(digits = 1) {
  const { fmt, tickFormat } = makeFormatter(ctx.lang());
  return { f: (v) => fmt(v, digits), tickFormat };
}
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
function legend(items) {
  const lg = el("div", "legend");
  for (const it of items) {
    const i = el("span", "legend-item");
    const k = el("span", "legend-key" + (it.box ? " is-band" : ""));
    k.style.background = it.color;
    i.append(k, el("span", null, it.label));
    lg.append(i);
  }
  return lg;
}
function line(container, series, { digits = 1, unit = "", height = 220, band = null, compact = true, label = null } = {}) {
  const { f, tickFormat } = fmts(digits);
  const year = ctx.lang() === "es" ? "Año" : "Year";
  drawLineChart(container, {
    series, band, unit, fmt: f, tickFormat, tooltip: ctx.tooltip, compact, height,
    coverageText: (n, N) => `${n}/${N}`, intervalText: (a, b) => `${a}–${b}`, yearLabel: year,
    ariaLabel: label || series.map((s) => s.name).join(", "),
    summary: (y) => `${y}: ` + series.map((s) => { const p = s.points.find((q) => q.year === y); return `${s.name} ${p ? f(p.value) : "–"}`; }).join("; "),
  });
}
function multiples(box, panels) {
  box.textContent = "";
  const grid = el("div", "story-multiples");
  box.append(grid);
  // build every cell first: with auto-fit columns a lone first cell would span the whole row
  // and its chart would be drawn too wide, then shrink once the other cells arrive
  const charts = panels.map((p) => {
    const cell = el("div", "story-panel");
    cell.append(el("p", "story-panel-title", p.title));
    if (p.legend) cell.append(legend(p.legend));
    const c = el("div", "chart");
    cell.append(c);
    grid.append(cell);
    return c;
  });
  // name each chart after its panel title (the series names alone can be just "Cusco")
  panels.forEach((p, i) => { p.draw(charts[i]); charts[i].querySelector("svg")?.setAttribute("aria-label", p.title); });
}
const ink = () => ctx.cssVar("--ref-line");
const slot = (i) => ctx.cssVar(`--series-${i}`);

// ---------- 1. canon by type, stacked bars ----------
async function step1(box, st) {
  const [tot, gas, min] = await Promise.all(["canon_total", "canon_gas", "canon_mining"].map(ctx.series));
  const T = new Map(pts(tot, "per_capita_real").map((p) => [p.year, p.value]));
  const G = new Map(pts(gas, "per_capita_real").map((p) => [p.year, p.value]));
  const M = new Map(pts(min, "per_capita_real").map((p) => [p.year, p.value]));
  const years = [...T.keys()].sort((a, b) => a - b);
  const rows = years.map((y) => ({ year: y, gas: G.get(y) || 0, mining: M.get(y) || 0, other: Math.max(0, T.get(y) - (G.get(y) || 0) - (M.get(y) || 0)), total: T.get(y) }));
  const keys = ["gas", "mining", "other"];
  const colors = { gas: slot(1), mining: slot(2), other: ctx.cssVar("--text-muted") };
  box.textContent = "";
  box.append(legend(keys.map((k) => ({ label: st.layers[k], color: colors[k], box: true }))));
  const c = el("div", "chart"); box.append(c);
  const { f, tickFormat } = fmts(0);
  const width = Math.max(260, c.clientWidth || 600), height = 300, m = { top: 10, right: 12, bottom: 28, left: 52 };
  const iw = width - m.left - m.right, ih = height - m.top - m.bottom;
  const x = d3.scaleBand().domain(years).range([0, iw]).padding(0.18);
  const y = d3.scaleLinear().domain([0, d3.max(rows, (r) => r.total) * 1.06]).nice().range([ih, 0]);
  const svg = d3.select(c).append("svg").attr("viewBox", `0 0 ${width} ${height}`).attr("role", "img").attr("aria-label", st.chart);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
  g.append("g").attr("class", "grid").call(d3.axisLeft(y).ticks(5).tickSize(-iw).tickFormat("")).call((s) => s.select(".domain").remove());
  g.append("g").attr("class", "axis").attr("transform", `translate(0,${ih})`)
    .call(d3.axisBottom(x).tickValues(years.filter((yy) => yy % 2 === 0)).tickSizeOuter(0));
  g.append("g").attr("class", "axis").call(d3.axisLeft(y).ticks(5).tickFormat(tickFormat(y.domain()[1])).tickSizeOuter(0)).call((s) => s.select(".domain").remove());
  const stack = d3.stack().keys(keys)(rows);
  g.append("g").selectAll("g").data(stack).join("g").attr("fill", (d) => colors[d.key])
    .selectAll("rect").data((d) => d).join("rect")
    .attr("x", (d) => x(d.data.year)).attr("width", x.bandwidth())
    .attr("y", (d) => y(d[1])).attr("height", (d) => Math.max(0, y(d[0]) - y(d[1])))
    .attr("stroke", "var(--surface-1)").attr("stroke-width", 1);       // surface gap between segments
  // hover: whole column as the target
  g.append("g").selectAll("rect").data(rows).join("rect")
    .attr("x", (d) => x(d.year) - (x.step() - x.bandwidth()) / 2).attr("width", x.step()).attr("y", 0).attr("height", ih)
    .attr("fill", "transparent")
    .on("pointermove pointerdown", (ev, d) => ctx.tooltip.show({
      head: String(d.year),
      rows: [...keys.map((k) => ({ color: colors[k], value: f(d[k]), name: st.layers[k] })),
        { color: null, value: f(d.total), name: ctx.lang() === "es" ? "Total" : "Total" }],
    }, ev.clientX, ev.clientY))
    .on("pointerleave", (ev) => { if (ev.pointerType === "mouse") ctx.tooltip.hide(); });
}

// ---------- 2. where it lands: map + ranked bars ----------
async function step2(box, st) {
  const [tot, geo] = await Promise.all([ctx.series("canon_total"), ctx.geo.catch(() => null)]);
  const dist = tot.measures.per_capita_real.district;
  const avg = new Map();
  for (const [code, arr] of Object.entries(dist)) {
    const v = arr.filter((p) => p[0] >= 2020 && p[0] <= 2024).map((p) => p[1]);
    if (v.length) avg.set(code, d3.mean(v));
  }
  const names = new Map(ctx.PLACES.district.map((d) => [d.code, d.name]));
  const provName = new Map(ctx.PLACES.province.map((p) => [p.code, p.name]));
  const provinceOf = new Map(ctx.PLACES.district.map((d) => [d.code, provName.get(d.province)]));
  const { f } = fmts(0);
  box.textContent = "";
  const wrap = el("div", "story-split");
  const left = el("div"), right = el("div");
  wrap.append(left, right); box.append(wrap);
  const mapEl = el("div", "map"), legendEl = el("div", "map-legend");
  left.append(mapEl, legendEl, el("p", "story-hint", st.mapHint));
  const strings = { yes: "", no: "", noData: ctx.lang() === "es" ? "Sin datos" : "No data", mapNoDataLegend: ctx.lang() === "es" ? "Sin datos" : "No data",
    interval: () => "", tapAgain: ctx.lang() === "es" ? "toca de nuevo para abrir" : "tap again to open" };
  if (geo) {
    drawMap(mapEl, legendEl, {
      districts: geo.districts, provinces: geo.provinces, values: avg, names, provinceOf, selected: new Map(), fmt: f,
      tooltip: ctx.tooltip, strings, binary: false, intervals: null, ariaLabel: st.chart,
      onToggle: (code) => ctx.openExplorer({ v: "canon_total", m: "per_capita", real: true, places: [code] }),
    });
  } else mapEl.append(el("p", "empty", STRINGS[ctx.lang()].loadError));   // the bars below still show
  // ranked bars, top ten
  const top = [...avg].sort((a, b) => b[1] - a[1]).slice(0, 10);
  const median = d3.median([...avg.values()]);
  const width = Math.max(260, right.clientWidth || 320), rowH = 26, m = { top: 6, right: 64, bottom: 8, left: 112 };
  const height = m.top + m.bottom + rowH * top.length;
  const x = d3.scaleLinear().domain([0, top[0][1]]).range([0, width - m.left - m.right]);
  const svg = d3.select(right).append("svg").attr("viewBox", `0 0 ${width} ${height}`).attr("role", "img").attr("aria-label", st.chart);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
  const rows = g.selectAll("g").data(top).join("g").attr("transform", (_, i) => `translate(0,${i * rowH})`);
  rows.append("text").attr("class", "bar-label").attr("x", -8).attr("y", rowH / 2).attr("dy", "0.35em").attr("text-anchor", "end").text((d) => names.get(d[0]));
  rows.append("rect").attr("x", 0).attr("y", 5).attr("height", rowH - 10).attr("rx", 3)
    .attr("width", (d) => Math.max(2, x(d[1]))).attr("fill", slot(1));
  rows.append("text").attr("class", "bar-value").attr("x", (d) => x(d[1]) + 6).attr("y", rowH / 2).attr("dy", "0.35em").text((d) => f(d[1]));
  right.append(el("p", "story-hint", st.median(f(median))));
}

// ---------- 3. budgets and spending ----------
async function step3(box, st) {
  const [pim, acc, ex] = await Promise.all(["siaf_pim", "siaf_accrued", "siaf_exec_rate"].map(ctx.series));
  multiples(box, [
    { title: `${st.pim} / ${st.accrued}`, legend: [{ label: st.pim, color: slot(1) }, { label: st.accrued, color: slot(2) }],
      draw: (c) => line(c, [
        { code: "pim", name: st.pim, short: "PIM", color: slot(1), points: pts(pim, "per_capita_real") },
        { code: "acc", name: st.accrued, color: slot(2), points: pts(acc, "per_capita_real") },
      ], { digits: 0, height: 240 }) },
    { title: st.exec, draw: (c) => line(c, [{ code: "ex", name: st.exec, color: ink(), isRef: true, points: pts(ex, "pct") }], { height: 240 }) },
  ]);
}

// ---------- 4. schools ----------
async function step4(box, st) {
  const [ptr, el_, er, em] = await Promise.all(["edu_ptr_pub", "sch_electric", "ece_read", "ece_math"].map(ctx.series));
  multiples(box, [
    { title: st.ptr, draw: (c) => line(c, [{ code: "p", name: st.ptr, color: ink(), isRef: true, points: pts(ptr, "ratio") }]) },
    { title: st.elec, draw: (c) => line(c, [{ code: "e", name: st.elec, color: ink(), isRef: true, points: pts(el_, "pct") }]) },
    { title: st.ece, legend: [{ label: st.read, color: slot(1) }, { label: st.math, color: slot(2) }],
      draw: (c) => line(c, [
        { code: "r", name: st.read, color: slot(1), points: pts(er, "pct") },
        { code: "m", name: st.math, color: slot(2), points: pts(em, "pct") },
      ]) },
  ]);
}

// ---------- 5. census dumbbells + poverty band ----------
async function step5(box, st) {
  const ids = Object.keys(st.rows);
  const data = await Promise.all(ids.map(ctx.series));
  const pov = await ctx.series("poverty");
  const rows = ids.map((id, i) => {
    const p = new Map(pts(data[i], "pct").map((q) => [q.year, q.value]));
    return { id, label: st.rows[id], a: p.get(2007), b: p.get(2017) };
  });
  const { f } = fmts(0);
  box.textContent = "";
  const wrap = el("div", "story-split");
  const left = el("div"), right = el("div");
  wrap.append(left, right); box.append(wrap);
  left.append(legend([{ label: "2007", color: ctx.cssVar("--text-muted") }, { label: "2017", color: slot(1) }]));
  const width = Math.max(260, left.clientWidth || 320), rowH = 44, m = { top: 18, right: 20, bottom: 26, left: 12 };
  const height = m.top + m.bottom + rowH * rows.length;
  const x = d3.scaleLinear().domain([0, 100]).range([0, width - m.left - m.right]);
  const svg = d3.select(left).append("svg").attr("viewBox", `0 0 ${width} ${height}`).attr("role", "img").attr("aria-label", st.chart);
  const g = svg.append("g").attr("transform", `translate(${m.left},${m.top})`);
  g.append("g").attr("class", "grid").attr("transform", `translate(0,${rowH * rows.length})`)
    .call(d3.axisBottom(x).ticks(5).tickSize(-rowH * rows.length).tickFormat("")).call((s) => s.select(".domain").remove());
  g.append("g").attr("class", "axis").attr("transform", `translate(0,${rowH * rows.length})`)
    .call(d3.axisBottom(x).ticks(5).tickFormat((v) => `${v}%`).tickSizeOuter(0));
  const r = g.selectAll("g.row").data(rows).join("g").attr("class", "row").attr("transform", (_, i) => `translate(0,${i * rowH})`);
  r.append("text").attr("class", "bar-label").attr("x", 0).attr("y", 4).text((d) => d.label);
  r.append("line").attr("x1", (d) => x(d.a)).attr("x2", (d) => x(d.b)).attr("y1", 24).attr("y2", 24).attr("stroke", ctx.cssVar("--hairline")).attr("stroke-width", 3);
  r.append("circle").attr("cx", (d) => x(d.a)).attr("cy", 24).attr("r", 6).attr("fill", ctx.cssVar("--text-muted")).attr("stroke", "var(--surface-1)").attr("stroke-width", 2);
  r.append("circle").attr("cx", (d) => x(d.b)).attr("cy", 24).attr("r", 6).attr("fill", slot(1)).attr("stroke", "var(--surface-1)").attr("stroke-width", 2);
  r.append("text").attr("class", "bar-value").attr("x", (d) => x(d.a) + (d.a < d.b ? -10 : 10)).attr("y", 24).attr("dy", "0.35em")
    .attr("text-anchor", (d) => (d.a < d.b ? "end" : "start")).text((d) => f(d.a));
  r.append("text").attr("class", "bar-value is-strong").attr("x", (d) => x(d.b) + (d.a < d.b ? 10 : -10)).attr("y", 24).attr("dy", "0.35em")
    .attr("text-anchor", (d) => (d.a < d.b ? "start" : "end")).text((d) => f(d.b));
  // poverty with its confidence band
  right.append(el("p", "story-panel-title", st.poverty));
  const lo = new Map(pts(pov, "pct_lo").map((p) => [p.year, p.value]));
  const hi = new Map(pts(pov, "pct_hi").map((p) => [p.year, p.value]));
  right.append(legend([{ label: "Cusco", color: ink() }, { label: st.band, color: "var(--band)", box: true }]));
  const c = el("div", "chart"); right.append(c);
  line(c, [{ code: "pov", name: "Cusco", color: ink(), isRef: true, points: pts(pov, "pct") }],
    { height: 250, label: st.poverty, band: { label: st.band, points: [...lo.keys()].filter((y) => hi.has(y)).map((y) => ({ year: y, lo: lo.get(y), hi: hi.get(y) })) } });
}

// ---------- 6. the reach of the state ----------
async function step6(box, st) {
  const [lb, se, cm, jb] = await Promise.all(["late_birth_share", "sec_serenazgo", "fin_cmac_present", "lab_private_workers"].map(ctx.series));
  multiples(box, [
    { title: st.late, draw: (c) => line(c, [{ code: "a", name: st.late, color: ink(), isRef: true, points: pts(lb, "pct") }], { height: 190 }) },
    { title: st.seren, draw: (c) => line(c, [{ code: "b", name: st.seren, color: ink(), isRef: true, points: pts(se, "pct") }], { height: 190 }) },
    { title: st.cmac, draw: (c) => line(c, [{ code: "c", name: st.cmac, color: ink(), isRef: true, points: pts(cm, "count") }], { digits: 0, height: 190 }) },
    { title: st.jobs, draw: (c) => line(c, [{ code: "d", name: st.jobs, color: ink(), isRef: true, points: pts(jb, "per_1000") }], { height: 190 }) },
  ]);
}
