// Cusco-stats explorer: state, data loading, controls, rendering, URL state.
/* global d3 */
import { STRINGS, makeFormatter } from "./i18n.js";
import { drawLineChart } from "./linechart.js";
import { drawMap, rewind } from "./map.js";

const SERIES_VARS = ["--series-1", "--series-2", "--series-3", "--series-4", "--series-5", "--series-6"];
const MAX_PLACES = 6;
const HIDDEN_MEASURES = new Set(["pct_lo", "pct_hi"]);

const state = { lang: "en", v: "canon_total", m: "per_capita", real: true, places: [], year: null, table: false };
const slots = new Map();      // place code -> colour slot, kept for as long as the place stays selected
const cache = new Map();      // variable -> series json
let DICT, PLACES, META, GEO_D, GEO_P;
const byId = new Map();
const placeInfo = new Map();  // code -> {name, level, province}

const $ = (id) => document.getElementById(id);
const T = () => STRINGS[state.lang];

// ---------- tooltip ----------
const tooltip = {
  el: null,
  show(content, cx, cy) {
    const el = this.el;
    el.textContent = "";
    const head = document.createElement("div");
    head.className = "tt-head";
    head.textContent = content.head;
    el.append(head);
    if (content.sub) { const s = document.createElement("div"); s.className = "tt-note"; s.textContent = content.sub; el.append(s); }
    for (const r of content.rows) {
      const row = document.createElement("div");
      row.className = "tt-row";
      const key = document.createElement("span");
      key.className = "tt-key";
      if (r.color) key.style.background = r.color;
      const val = document.createElement("span");
      val.className = "tt-val";
      val.textContent = r.value;
      const name = document.createElement("span");
      name.className = "tt-name";
      name.textContent = r.name + (r.note ? ` · ${r.note}` : "");
      row.append(key, val, name);
      el.append(row);
    }
    if (content.note) { const n = document.createElement("div"); n.className = "tt-note"; n.textContent = content.note; el.append(n); }
    el.hidden = false;
    const w = el.offsetWidth, h = el.offsetHeight;
    let x = cx + 14, y = cy + 14;
    if (x + w > window.innerWidth - 8) x = cx - w - 14;
    if (y + h > window.innerHeight - 8) y = cy - h - 14;
    el.style.left = `${Math.max(8, x)}px`;
    el.style.top = `${Math.max(8, y)}px`;
  },
  hide() { this.el.hidden = true; },
};

// ---------- data ----------
async function getJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}
async function series(v) {
  if (!cache.has(v)) cache.set(v, await getJSON(`data/series/${v}.json`));
  return cache.get(v);
}

// ---------- URL state ----------
function readURL() {
  const q = new URLSearchParams(location.search);
  if (q.get("lang") === "es" || q.get("lang") === "en") state.lang = q.get("lang");
  if (q.get("v")) state.v = q.get("v");
  if (q.get("m")) state.m = q.get("m");
  if (q.get("u")) state.real = q.get("u") !== "nominal";
  if (q.get("p")) state.places = q.get("p").split(",").filter(Boolean).slice(0, MAX_PLACES);
  if (q.get("y")) state.year = +q.get("y");
}
function writeURL() {
  const q = new URLSearchParams();
  q.set("lang", state.lang); q.set("v", state.v); q.set("m", state.m);
  if (!state.real) q.set("u", "nominal");
  if (state.places.length) q.set("p", state.places.join(","));
  if (state.year) q.set("y", state.year);
  history.replaceState(null, "", `${location.pathname}?${q.toString()}${location.hash}`);
}

// ---------- helpers ----------
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
function colorOf(code) {
  if (code === "08") return cssVar("--ref-line");
  return cssVar(SERIES_VARS[slots.get(code) ?? 0]);
}
function assignSlot(code) {
  if (slots.has(code)) return;
  const used = new Set(slots.values());
  for (let i = 0; i < SERIES_VARS.length; i++) if (!used.has(i)) { slots.set(code, i); return; }
}
function levelOf(code) { return code === "08" ? "department" : code.length === 4 ? "province" : "district"; }
function placeName(code) {
  if (code === "08") return T().cusco;
  const p = placeInfo.get(code);
  return p ? p.name : code;
}
function measureInfo(v, m) { return byId.get(v).measures.find((x) => x.id === m); }
function baseMeasures(v) { return byId.get(v).measures.map((x) => x.id).filter((id) => !id.endsWith("_real") && !HIDDEN_MEASURES.has(id)); }
function hasReal(v, m) { return byId.get(v).measures.some((x) => x.id === `${m}_real`); }
function effMeasure() { return state.real && hasReal(state.v, state.m) ? `${state.m}_real` : state.m; }
function aggText(agg) {
  const a = T().aggregation;
  if (agg.startsWith("official")) return a.official;
  if (agg.startsWith("ratio_of_sums of district")) return a.snapshot;
  return a[agg] || agg;
}
function toPoints(arr) { return (arr || []).map((p) => ({ year: p[0], value: p[1], n: p[2], N: p[3] })); }

// ---------- controls ----------
function fillIndicatorSelect() {
  const sel = $("sel-indicator");
  sel.textContent = "";
  const groups = new Map();
  for (const e of DICT) {
    const cat = e.category[state.lang];
    if (!groups.has(cat)) groups.set(cat, []);
    groups.get(cat).push(e);
  }
  for (const [cat, items] of groups) {
    const og = document.createElement("optgroup");
    og.label = cat;
    for (const e of items) {
      const o = document.createElement("option");
      o.value = e.id;
      o.textContent = e.label[state.lang];
      og.append(o);
    }
    sel.append(og);
  }
  sel.value = state.v;
}
function fillMeasureSelect() {
  const sel = $("sel-measure");
  sel.textContent = "";
  for (const id of baseMeasures(state.v)) {
    const mi = measureInfo(state.v, id);
    const o = document.createElement("option");
    o.value = id;
    o.textContent = mi.label[state.lang];
    sel.append(o);
  }
  if (!baseMeasures(state.v).includes(state.m)) state.m = baseMeasures(state.v)[0];
  sel.value = state.m;
  $("ctl-units").hidden = !hasReal(state.v, state.m);
  for (const b of document.querySelectorAll("[data-units]")) b.setAttribute("aria-pressed", String((b.dataset.units === "real") === state.real));
}
function fillPlaceList() {
  const dl = $("place-list");
  dl.textContent = "";
  for (const p of PLACES.province) {
    const o = document.createElement("option");
    o.value = `${p.name} (${T().province})`;
    dl.append(o);
  }
  const provName = new Map(PLACES.province.map((p) => [p.code, p.name]));
  for (const d of PLACES.district) {
    const o = document.createElement("option");
    o.value = `${d.name} · ${provName.get(d.province)}`;
    dl.append(o);
  }
}
function lookupPlace(text) {
  const t = text.trim().toLowerCase();
  if (!t) return null;
  const provName = new Map(PLACES.province.map((p) => [p.code, p.name]));
  for (const p of PLACES.province) if (`${p.name} (${T().province})`.toLowerCase() === t) return p.code;
  for (const d of PLACES.district) if (`${d.name} · ${provName.get(d.province)}`.toLowerCase() === t) return d.code;
  // loose match on the name alone: prefer a district, then a province
  const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const nt = norm(t);
  const d = PLACES.district.find((x) => norm(x.name) === nt);
  if (d) return d.code;
  const p = PLACES.province.find((x) => norm(x.name) === nt);
  return p ? p.code : null;
}
function addPlace(code) {
  if (!code || code === "08" || state.places.includes(code)) return;
  if (state.places.length >= MAX_PLACES) { setStatus(T().tooMany); return; }
  state.places.push(code);
  assignSlot(code);
  render();
}
function removePlace(code) {
  state.places = state.places.filter((c) => c !== code);
  slots.delete(code);
  render();
}
function setStatus(msg) { $("status").textContent = msg || ""; }

function renderChips() {
  const box = $("chips");
  box.textContent = "";
  const mk = (code) => {
    const c = document.createElement("span");
    c.className = "chip" + (code === "08" ? " is-ref" : "");
    const k = document.createElement("span");
    k.className = "chip-key";
    k.style.background = colorOf(code);
    if (code === "08") k.style.height = "3px";
    const t = document.createElement("span");
    t.textContent = placeName(code) + (code !== "08" ? ` · ${T()[levelOf(code)]}` : "");
    c.append(k, t);
    if (code !== "08") {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", `${T().remove} ${placeName(code)}`);
      b.textContent = "×";
      b.addEventListener("click", () => removePlace(code));
      c.append(b);
    }
    return c;
  };
  box.append(mk("08"), ...state.places.map(mk));
}

// ---------- rendering ----------
let lastData = null;

async function render() {
  tooltip.hide();
  const t = T();
  const { fmt, compact } = makeFormatter(state.lang);
  const entry = byId.get(state.v);
  const em = effMeasure();
  const mi = measureInfo(state.v, em);
  const data = await series(state.v);
  const block = data.measures[em] || {};
  const official = entry.kind === "official_rate" || entry.kind === "official_interval";
  const messages = [];

  // chart series
  const seriesList = [];
  const ref = block.department && block.department["08"];
  if (ref) seriesList.push({ code: "08", name: t.cusco, short: t.cuscoShort, color: colorOf("08"), isRef: true, points: toPoints(ref) });
  for (const code of state.places) {
    const lv = levelOf(code);
    const arr = block[lv] && block[lv][code];
    if (!arr || !arr.length) {
      messages.push(lv === "province" && !block.province ? t.noProvinceLevel : t.notAvailablePlace(placeName(code)));
      continue;
    }
    seriesList.push({ code, name: placeName(code), color: colorOf(code), points: toPoints(arr) });
  }

  // confidence band for interval indicators (department)
  let band = null;
  if (em === "pct" && data.measures.pct_lo && data.measures.pct_hi) {
    const lo = new Map((data.measures.pct_lo.department?.["08"] || []).map((p) => [p[0], p[1]]));
    const hi = new Map((data.measures.pct_hi.department?.["08"] || []).map((p) => [p[0], p[1]]));
    const pts = [...lo.keys()].filter((y) => hi.has(y)).map((y) => ({ year: y, lo: lo.get(y), hi: hi.get(y) }));
    if (pts.length) band = { label: t.band, points: pts };
  }

  // constant soles start in 2010
  if (em.endsWith("_real")) {
    const nominal = data.measures[state.m]?.department?.["08"] || [];
    if (nominal.some((p) => p[0] < 2010)) messages.push(t.realFrom2010);
  }
  if (official) messages.push(t.officialNote);
  setStatus(messages.join(" "));

  // titles
  $("chart-title").textContent = entry.label[state.lang];
  const sub = $("chart-subtitle");
  sub.textContent = `${mi.unit[state.lang]} · ${t.yearsShown(mi.years[0], mi.years[1])}`;
  if (official) { const tag = document.createElement("span"); tag.className = "tag"; tag.textContent = t.officialTag; sub.append(tag); }

  // legend (always present for 2 or more series; band key when shown)
  const legend = $("chart-legend");
  legend.textContent = "";
  if (seriesList.length >= 2 || band) {
    for (const s of seriesList) {
      const it = document.createElement("span"); it.className = "legend-item";
      const k = document.createElement("span"); k.className = "legend-key" + (s.isRef ? " is-ref" : ""); k.style.background = s.color;
      const l = document.createElement("span"); l.textContent = s.name;
      it.append(k, l); legend.append(it);
    }
    if (band) {
      const it = document.createElement("span"); it.className = "legend-item";
      const k = document.createElement("span"); k.className = "legend-key is-band"; k.style.background = "var(--band)";
      const l = document.createElement("span"); l.textContent = band.label;
      it.append(k, l); legend.append(it);
    }
  }

  const chartEl = $("chart");
  if (seriesList.length) {
    drawLineChart(chartEl, {
      series: seriesList, band, unit: mi.unit[state.lang], fmt: (v) => fmt(v, digits(em)), compact, tooltip,
      connect: entry.kind === "snapshot",
      coverageText: t.coverage,
      ariaLabel: t.chartLabel(entry.label[state.lang], seriesList.map((s) => s.name).join(", ")),
    });
  } else {
    chartEl.textContent = "";
    const e = document.createElement("p"); e.className = "empty"; e.textContent = t.noData; chartEl.append(e);
  }
  lastData = { seriesList, band, unit: mi.unit[state.lang], em };
  renderTable();

  // map
  await renderMap(entry, em, mi, data, fmt);

  renderChips();
  renderNotes(entry, mi, official);
  writeURL();
}

function vintageDate() {
  const m = /(\d{4}-\d{2}-\d{2})/.exec(META.data_vintage || "");
  return m ? m[1] : META.data_vintage;
}

function digits(em) {
  if (["total", "total_real", "count"].includes(em)) return 0;
  return em === "ratio" ? 1 : 1;
}

async function renderMap(entry, em, mi, data, fmt) {
  const t = T();
  const card = $("map-card");
  const dist = data.measures[em]?.district;
  if (!dist) {
    card.hidden = false;
    $("map-title").textContent = t.mapTitle(entry.label[state.lang]);
    $("map-subtitle").textContent = t.noDistrictLevel;
    $("map-year-wrap").hidden = true;
    $("map").textContent = "";
    $("map-legend").textContent = "";
    return;
  }
  card.hidden = false;
  $("map-year-wrap").hidden = false;
  const years = [...new Set(Object.values(dist).flatMap((a) => a.map((p) => p[0])))].sort((a, b) => a - b);
  if (!state.year || !years.includes(state.year)) state.year = years[years.length - 1];
  const rng = $("rng-year");
  rng.min = years[0]; rng.max = years[years.length - 1]; rng.value = state.year;
  rng.disabled = years.length === 1;
  rng.dataset.years = years.join(",");
  $("out-year").textContent = state.year;
  const values = new Map();
  for (const [code, arr] of Object.entries(dist)) {
    const p = arr.find((q) => q[0] === state.year);
    if (p) values.set(code, p[1]);
  }
  let intervals = null;
  if (em === "pct" && data.measures.pct_lo?.district && data.measures.pct_hi?.district) {
    intervals = new Map();
    for (const code of Object.keys(data.measures.pct_lo.district)) {
      const lo = data.measures.pct_lo.district[code].find((q) => q[0] === state.year);
      const hi = data.measures.pct_hi.district[code]?.find((q) => q[0] === state.year);
      if (lo && hi) intervals.set(code, [lo[1], hi[1]]);
    }
  }
  $("map-title").textContent = t.mapTitle(entry.label[state.lang]);
  $("map-subtitle").textContent = t.mapSubtitle(state.year);
  const selected = new Map(state.places.filter((c) => c.length === 6).map((c) => [c, colorOf(c)]));
  const names = new Map(PLACES.district.map((d) => [d.code, d.name]));
  const provName = new Map(PLACES.province.map((p) => [p.code, p.name]));
  const provinceOf = new Map(PLACES.district.map((d) => [d.code, provName.get(d.province)]));
  drawMap($("map"), $("map-legend"), {
    districts: GEO_D, provinces: GEO_P, values, names, provinceOf, selected, intervals,
    fmt: (v) => fmt(v, digits(em)), tooltip, strings: t, binary: entry.kind === "binary",
    ariaLabel: t.mapLabel(entry.label[state.lang], state.year),
    onToggle: (code) => (state.places.includes(code) ? removePlace(code) : addPlace(code)),
  });
}

function renderTable() {
  const wrap = $("chart-table");
  const btn = $("btn-table");
  btn.textContent = state.table ? T().hideTable : T().showTable;
  btn.setAttribute("aria-expanded", String(state.table));
  wrap.hidden = !state.table;
  if (!state.table || !lastData) return;
  const { fmt } = makeFormatter(state.lang);
  const { seriesList, band } = lastData;
  const years = [...new Set(seriesList.flatMap((s) => s.points.map((p) => p.year)))].sort((a, b) => b - a);
  const table = document.createElement("table");
  const thead = table.createTHead().insertRow();
  const th0 = document.createElement("th"); th0.textContent = T().tableYear; thead.append(th0);
  for (const s of seriesList) { const th = document.createElement("th"); th.textContent = s.name; thead.append(th); }
  if (band) { const th = document.createElement("th"); th.textContent = band.label; thead.append(th); }
  const tb = table.createTBody();
  for (const y of years) {
    const tr = tb.insertRow();
    tr.insertCell().textContent = y;
    for (const s of seriesList) { const p = s.points.find((q) => q.year === y); tr.insertCell().textContent = p ? fmt(p.value, digits(lastData.em)) : "–"; }
    if (band) { const b = band.points.find((q) => q.year === y); tr.insertCell().textContent = b ? `${fmt(b.lo)}–${fmt(b.hi)}` : "–"; }
  }
  wrap.textContent = "";
  wrap.append(table);
}

function downloadCSV() {
  if (!lastData) return;
  const rows = [["year", "place", "code", "level", "value", "unit", "districts_with_data", "districts"]];
  for (const s of lastData.seriesList) {
    for (const p of s.points) rows.push([p.year, s.name, s.code, levelOf(s.code), p.value, lastData.unit, p.n ?? "", p.N ?? ""]);
  }
  const esc = (v) => { const s = String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  const blob = new Blob(["﻿" + rows.map((r) => r.map(esc).join(",")).join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `cusco-stats_${state.v}_${lastData.em}.csv`;
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function renderNotes(entry, mi, official) {
  const t = T();
  const box = $("notes");
  box.textContent = "";
  const section = (title, paras) => {
    const d = document.createElement("div");
    const h = document.createElement("h3"); h.textContent = title; d.append(h);
    for (const p of paras.filter(Boolean)) { const el = document.createElement("p"); el.textContent = p; d.append(el); }
    box.append(d);
  };
  section(t.description, [entry.description[state.lang]]);
  if (mi.caveat[state.lang]) section(t.caveats, [mi.caveat[state.lang]]);
  section(t.method, [aggText(mi.aggregation)]);
  const src = document.createElement("div");
  const h = document.createElement("h3"); h.textContent = t.source; src.append(h);
  const p1 = document.createElement("p"); p1.textContent = entry.source[state.lang]; src.append(p1);
  const p2 = document.createElement("p"); p2.className = "muted"; p2.textContent = `${t.sirtodCodes}: ${entry.sirtod_codes}`; src.append(p2);
  const p3 = document.createElement("p"); p3.className = "muted"; p3.textContent = t.dataVintage(vintageDate(), META.built); src.append(p3);
  box.append(src);
  const placeNotes = [];
  for (const code of state.places) {
    const d = PLACES.district.find((x) => x.code === code);
    if (!d) continue;
    if (d.new_district) placeNotes.push(t.created(d.name, d.first_year));
    if (d.lost_territory) placeNotes.push(t.lostTerritory(d.name));
  }
  if (placeNotes.length) section(t.placeNotes, placeNotes);
}

// ---------- language ----------
function applyLanguage() {
  const t = T();
  document.documentElement.lang = state.lang;
  for (const el of document.querySelectorAll("[data-i18n]")) {
    const v = t[el.dataset.i18n];
    if (typeof v === "string") el.textContent = v;
  }
  for (const el of document.querySelectorAll("[data-i18n-placeholder]")) el.placeholder = t[el.dataset.i18nPlaceholder];
  for (const el of document.querySelectorAll(".nav-link.is-soon")) el.dataset.soon = t.soon;
  for (const b of document.querySelectorAll("[data-lang]")) b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang));
  $("footer-data").textContent = t.dataVintage(vintageDate(), META.built);
  document.title = state.lang === "es" ? "Cusco-stats · Los distritos de Cusco en datos" : "Cusco-stats · Districts of Cusco in data";
}

// ---------- init ----------
async function init() {
  tooltip.el = $("tooltip");
  readURL();
  setStatus(STRINGS[state.lang].loading);
  try {
    [META, DICT, PLACES, GEO_D, GEO_P] = await Promise.all([
      getJSON("data/meta.json"), getJSON("data/dictionary.json"), getJSON("data/places.json"),
      getJSON("data/geo/districts.geojson"), getJSON("data/geo/provinces.geojson"),
    ]);
  } catch (e) {
    setStatus(STRINGS[state.lang].loadError);
    console.error(e);
    return;
  }
  rewind(GEO_D); rewind(GEO_P);
  for (const e of DICT) byId.set(e.id, e);
  for (const p of PLACES.province) placeInfo.set(p.code, { name: p.name, level: "province" });
  for (const d of PLACES.district) placeInfo.set(d.code, { name: d.name, level: "district", province: d.province });
  if (!byId.has(state.v)) state.v = DICT[0].id;
  state.places = state.places.filter((c) => placeInfo.has(c));
  state.places.forEach(assignSlot);

  applyLanguage();
  fillIndicatorSelect();
  fillMeasureSelect();
  fillPlaceList();

  $("sel-indicator").addEventListener("change", (e) => { state.v = e.target.value; state.year = null; fillMeasureSelect(); render(); });
  $("sel-measure").addEventListener("change", (e) => { state.m = e.target.value; fillMeasureSelect(); render(); });
  for (const b of document.querySelectorAll("[data-units]")) {
    b.addEventListener("click", () => { state.real = b.dataset.units === "real"; fillMeasureSelect(); render(); });
  }
  const inp = $("inp-place");
  const tryAdd = () => {
    if (!inp.value.trim()) return;
    const code = lookupPlace(inp.value);
    if (code) { addPlace(code); inp.value = ""; } else setStatus(T().notFound);
  };
  inp.addEventListener("change", tryAdd);
  inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); tryAdd(); } });
  const rng = $("rng-year");
  rng.addEventListener("input", () => {
    const years = rng.dataset.years.split(",").map(Number);
    const v = +rng.value;
    state.year = years.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a), years[0]);
    render();
  });
  $("btn-table").addEventListener("click", () => { state.table = !state.table; renderTable(); });
  $("btn-csv").addEventListener("click", downloadCSV);
  for (const b of document.querySelectorAll("[data-lang]")) {
    b.addEventListener("click", () => {
      state.lang = b.dataset.lang;
      applyLanguage(); fillIndicatorSelect(); fillMeasureSelect(); fillPlaceList(); render();
    });
  }
  let timer;
  window.addEventListener("resize", () => { clearTimeout(timer); timer = setTimeout(render, 150); });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);

  await render();
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
