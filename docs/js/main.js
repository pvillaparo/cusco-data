// Cusco-stats explorer: state, data loading, controls, rendering, URL state.
/* global d3 */
import { STRINGS, makeFormatter } from "./i18n.js";
import { drawLineChart } from "./linechart.js";
import { drawMap, rewind } from "./map.js";
import { initStory, redrawStory } from "./story.js";

const SERIES_VARS = ["--series-1", "--series-2", "--series-3", "--series-4", "--series-5", "--series-6"];
const MAX_PLACES = 6;
const HIDDEN_MEASURES = new Set(["pct_lo", "pct_hi"]);

const state = { lang: "en", v: "canon_total", m: "per_capita", real: true, places: [], year: null, table: false, mapTable: false };
const slots = new Map();      // place code -> colour slot, kept while the place stays selected
const cache = new Map();      // variable -> promise of the series json
let DICT, PLACES, META, GEO_D, GEO_P;
const byId = new Map();
const placeInfo = new Map();  // code -> {name, level, province}
let provinceNames = new Set();
let pendingNotes = [];        // one-off messages (from the link, or after adding/removing a place)
let renderToken = 0;

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
  hide() { if (this.el) this.el.hidden = true; },
};

// ---------- data ----------
async function getJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}
function series(v) {
  if (!cache.has(v)) {
    const p = getJSON(`data/series/${v}.json`).catch((e) => { cache.delete(v); throw e; });
    cache.set(v, p);
  }
  return cache.get(v);
}

// ---------- URL state ----------
function readURL() {
  const q = new URLSearchParams(location.search);
  if (q.get("lang") === "es" || q.get("lang") === "en") state.lang = q.get("lang");
  if (q.get("v")) state.v = q.get("v");
  if (q.get("m")) state.m = q.get("m");
  if (q.get("u")) state.real = q.get("u") !== "nominal";
  if (q.get("p")) state.places = q.get("p").split(",").map((s) => s.trim()).filter(Boolean);
  if (q.get("c")) state.slotHint = q.get("c");
  if (q.get("y")) state.year = +q.get("y");
  state.fromLink = q.has("v") || location.hash === "#explorer";   // a shared view, or a link to #explorer: open at the explorer
}
function writeURL() {
  const q = new URLSearchParams();
  q.set("lang", state.lang); q.set("v", state.v); q.set("m", state.m);
  if (!state.real) q.set("u", "nominal");
  if (state.places.length) {
    q.set("p", state.places.join(","));
    q.set("c", state.places.map((c) => slots.get(c)).join(""));   // colour slots, so a shared link looks the same
  }
  if (state.year) q.set("y", state.year);
  history.replaceState(null, "", `${location.pathname}?${q.toString()}`);
}

// ---------- helpers ----------
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
function colorOf(code) {
  if (code === "08") return cssVar("--ref-line");
  return cssVar(SERIES_VARS[slots.get(code) ?? 0]);
}
function assignSlot(code, preferred) {
  if (slots.has(code)) return;
  const used = new Set(slots.values());
  if (preferred != null && preferred >= 0 && preferred < SERIES_VARS.length && !used.has(preferred)) { slots.set(code, preferred); return; }
  for (let i = 0; i < SERIES_VARS.length; i++) if (!used.has(i)) { slots.set(code, i); return; }
}
function levelOf(code) { return code === "08" ? "department" : code.length === 4 ? "province" : "district"; }
function baseName(code) {
  if (code === "08") return T().cusco;
  const p = placeInfo.get(code);
  return p ? p.name : code;
}
// Provinces always carry "(province)"; a district carries "(district)" when a province has the same name.
function placeLabel(code) {
  const lv = levelOf(code);
  const n = baseName(code);
  if (lv === "province") return `${n} ${T().provSuffix}`;
  if (lv === "district" && provinceNames.has(n)) return `${n} ${T().distSuffix}`;
  return n;
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
function digits(em) { return ["total", "total_real", "count"].includes(em) ? 0 : 1; }
function vintageDate() { const m = /(\d{4}-\d{2}-\d{2})/.exec(META.data_vintage || ""); return m ? m[1] : META.data_vintage; }
let lastStatus = "";
function setStatus(msg) { const s = msg || ""; if (s !== lastStatus) { $("status").textContent = s; lastStatus = s; } }

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
  const provName = new Map(PLACES.province.map((p) => [p.code, p.name]));
  for (const p of PLACES.province) {
    const o = document.createElement("option");
    o.value = `${p.name} ${T().provSuffix}`;
    dl.append(o);
  }
  for (const d of PLACES.district) {
    const o = document.createElement("option");
    o.value = `${d.name} · ${provName.get(d.province)}`;
    dl.append(o);
  }
}
function lookupPlace(text) {
  const t = text.trim().toLowerCase();
  if (!t) return {};
  const provName = new Map(PLACES.province.map((p) => [p.code, p.name]));
  for (const p of PLACES.province) {
    if (`${p.name} ${T().provSuffix}`.toLowerCase() === t || `${p.name} (${T().province})`.toLowerCase() === t) return { code: p.code };
  }
  for (const d of PLACES.district) if (`${d.name} · ${provName.get(d.province)}`.toLowerCase() === t) return { code: d.code };
  const norm = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
  const nt = norm(t);
  const d = PLACES.district.find((x) => norm(x.name) === nt);
  const p = PLACES.province.find((x) => norm(x.name) === nt);
  if (d) return { code: d.code, ambiguous: !!p };
  return p ? { code: p.code } : {};
}
function addPlace(code, { ambiguous = false } = {}) {
  if (!code || code === "08" || state.places.includes(code)) return;
  if (state.places.length >= MAX_PLACES) { setStatus(T().tooMany); return; }
  state.places.push(code);
  assignSlot(code);
  pendingNotes.push(ambiguous ? T().ambiguous(baseName(code)) : T().added(placeLabel(code)));
  render();
}
function removePlace(code, { focusNext = false } = {}) {
  const idx = state.places.indexOf(code);
  pendingNotes.push(T().removed(placeLabel(code)));
  state.places = state.places.filter((c) => c !== code);
  slots.delete(code);
  render().then(() => {
    if (!focusNext) return;
    const buttons = [...document.querySelectorAll("#chips button")];
    (buttons[Math.min(idx, buttons.length - 1)] || $("inp-place")).focus();
  });
}

function renderChips(missing) {
  const box = $("chips");
  box.textContent = "";
  const mk = (code) => {
    const c = document.createElement("span");
    c.className = "chip" + (code === "08" ? " is-ref" : "") + (missing.has(code) ? " is-missing" : "");
    const k = document.createElement("span");
    k.className = "chip-key";
    k.style.background = colorOf(code);
    if (code === "08") k.style.height = "3px";
    const t = document.createElement("span");
    t.textContent = code === "08" ? T().cusco : `${baseName(code)} · ${T()[levelOf(code)]}${missing.has(code) ? ` (${T().noData.toLowerCase()})` : ""}`;
    c.append(k, t);
    if (code !== "08") {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", `${T().remove} ${placeLabel(code)}`);
      b.textContent = "×";
      b.addEventListener("click", () => removePlace(code, { focusNext: true }));
      c.append(b);
    }
    return c;
  };
  box.append(mk("08"), ...state.places.map(mk));
}

// ---------- rendering ----------
let lastData = null;

async function render() {
  const token = ++renderToken;
  tooltip.hide();
  const v = state.v;
  let data;
  try {
    data = await series(v);
  } catch (e) {
    if (token !== renderToken) return;
    console.error(e);
    setStatus(T().loadError);
    $("chart").textContent = "";
    return;
  }
  if (token !== renderToken) return;           // a newer selection started while this one was loading

  const t = T();
  const { fmt, tickFormat } = makeFormatter(state.lang);
  const entry = byId.get(v);
  const em = effMeasure();
  const mi = measureInfo(v, em);
  const block = data.measures[em] || {};
  const official = entry.kind === "official_rate" || entry.kind === "official_interval";
  const messages = pendingNotes.filter(Boolean);
  pendingNotes = [];
  const fmtv = (x) => fmt(x, digits(em));

  // interval measures (poverty): bounds per place and year
  const bounds = {};
  if (em === "pct" && data.measures.pct_lo && data.measures.pct_hi) {
    for (const lv of ["department", "province", "district"]) {
      const lo = data.measures.pct_lo[lv] || {}, hi = data.measures.pct_hi[lv] || {};
      for (const code of Object.keys(lo)) {
        const h = new Map((hi[code] || []).map((p) => [p[0], p[1]]));
        bounds[code] = new Map(lo[code].filter((p) => h.has(p[0])).map((p) => [p[0], [p[1], h.get(p[0])]]));
      }
    }
  }
  const withBounds = (code, pts) => pts.map((p) => {
    const b = bounds[code]?.get(p.year);
    return b ? { ...p, lo: b[0], hi: b[1] } : p;
  });

  // chart series
  const seriesList = [];
  const missing = new Set();
  const noProv = [];
  const ref = block.department && block.department["08"];
  if (ref) seriesList.push({ code: "08", name: t.cusco, short: t.cuscoShort, color: colorOf("08"), isRef: true, points: toPoints(ref) });
  for (const code of state.places) {
    const lv = levelOf(code);
    const arr = block[lv] && block[lv][code];
    if (!arr || !arr.length) {
      missing.add(code);
      if (lv === "province" && !block.province) noProv.push(baseName(code));
      else messages.push(t.notAvailablePlace(placeLabel(code)));
      continue;
    }
    // end-of-line labels use the plain name unless a same-named province and district are both in the chart
    const clash = state.places.some((c) => c !== code && baseName(c) === baseName(code));
    seriesList.push({ code, name: placeLabel(code), short: clash ? placeLabel(code) : baseName(code), color: colorOf(code),
      points: withBounds(code, toPoints(arr)) });
  }
  if (noProv.length) messages.unshift(t.noProvinceLevel(noProv.join(", ")));
  let band = null;
  if (bounds["08"]) band = { label: t.band, points: [...bounds["08"]].map(([year, [lo, hi]]) => ({ year, lo, hi })) };

  if (em.endsWith("_real")) {
    const nominal = data.measures[state.m]?.department?.["08"] || [];
    if (nominal.some((p) => p[0] < 2010)) messages.push(t.realFrom2010);
  }
  if (official) messages.push(t.officialNote);

  // titles and legend
  $("chart-title").textContent = entry.label[state.lang];
  const sub = $("chart-subtitle");
  sub.textContent = `${mi.unit[state.lang]} · ${t.yearsShown(mi.years[0], mi.years[1])}`;
  if (official) { const tag = document.createElement("span"); tag.className = "tag"; tag.textContent = t.officialTag; sub.append(tag); }
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
      series: seriesList, band, unit: mi.unit[state.lang], fmt: fmtv, tickFormat, tooltip,
      coverageText: t.coverage, intervalText: t.interval, connect: entry.kind === "snapshot",
      yearLabel: t.year,
      ariaLabel: t.chartLabel(entry.label[state.lang], seriesList.map((s) => s.name).join(", ")),
      summary: (year) => `${year}: ` + seriesList.map((s) => {
        const p = s.points.find((q) => q.year === year);
        return `${s.name} ${p ? fmtv(p.value) : t.noData}`;
      }).join("; "),
    });
  } else {
    chartEl.textContent = "";
    const e = document.createElement("p"); e.className = "empty"; e.textContent = t.noData; chartEl.append(e);
  }
  lastData = { seriesList, band, unit: mi.unit[state.lang], em, label: entry.label[state.lang], v };
  renderTable();

  const mapMsg = renderMap(entry, em, mi, data, fmtv, bounds);
  if (mapMsg) messages.push(mapMsg);
  renderChips(missing);
  renderNotes(entry, mi, em, data);
  setStatus([...new Set(messages)].join(" "));
  writeURL();
}

function renderMap(entry, em, mi, data, fmtv, bounds) {
  const t = T();
  const dist = data.measures[em]?.district;
  $("map-title").textContent = t.mapTitle(entry.label[state.lang]);
  const noMap = (msg) => {
    $("map-subtitle").textContent = msg;
    $("map-year-wrap").hidden = true;
    $("map").textContent = "";
    $("map-legend").textContent = "";
    $("btn-map-table").hidden = true;
    $("map-table").hidden = true;
    return null;
  };
  if (!dist) return noMap(t.noDistrictLevel);
  if (!mi.map) return noMap(t.noMapForMeasure);
  $("map-year-wrap").hidden = false;
  $("btn-map-table").hidden = false;
  const years = [...new Set(Object.values(dist).flatMap((a) => a.map((p) => p[0])))].sort((a, b) => a - b);
  let note = null;
  if (!state.year || !years.includes(state.year)) {
    const shown = years[years.length - 1];
    if (state.year && state.askedYear) note = t.yearReplaced(state.year, shown);
    state.year = shown;
  }
  state.askedYear = false;
  const rng = $("rng-year");
  rng.min = 0; rng.max = years.length - 1; rng.value = years.indexOf(state.year);   // an index, so arrows step over gaps
  rng.disabled = years.length === 1;
  rng.setAttribute("aria-valuetext", String(state.year));
  rng.dataset.years = years.join(",");
  $("out-year").textContent = state.year;
  const values = new Map();
  for (const [code, arr] of Object.entries(dist)) {
    const p = arr.find((q) => q[0] === state.year);
    if (p) values.set(code, p[1]);
  }
  const intervals = new Map();
  for (const code of values.keys()) { const b = bounds[code]?.get(state.year); if (b) intervals.set(code, b); }
  $("map-subtitle").textContent = t.mapSubtitle(state.year);
  const selected = new Map(state.places.filter((c) => c.length === 6).map((c) => [c, colorOf(c)]));
  const names = new Map(PLACES.district.map((d) => [d.code, d.name]));
  const provName = new Map(PLACES.province.map((p) => [p.code, p.name]));
  const provinceOf = new Map(PLACES.district.map((d) => [d.code, provName.get(d.province)]));
  drawMap($("map"), $("map-legend"), {
    districts: GEO_D, provinces: GEO_P, values, names, provinceOf, selected, intervals: intervals.size ? intervals : null,
    fmt: fmtv, tooltip, strings: t, binary: entry.kind === "binary",
    ariaLabel: t.mapLabel(entry.label[state.lang], state.year),
    onToggle: (code) => (state.places.includes(code) ? removePlace(code) : addPlace(code)),
  });
  renderMapTable(entry, values, intervals, names, provinceOf, fmtv);
  return note;
}

function renderMapTable(entry, values, intervals, names, provinceOf, fmtv) {
  const t = T();
  const btn = $("btn-map-table");
  btn.textContent = state.mapTable ? t.hideMapData : t.showMapData;
  btn.setAttribute("aria-expanded", String(state.mapTable));
  const wrap = $("map-table");
  wrap.hidden = !state.mapTable;
  if (!state.mapTable) return;
  const binary = entry.kind === "binary";
  const rows = PLACES.district.map((d) => ({ code: d.code, name: names.get(d.code), prov: provinceOf.get(d.code), v: values.get(d.code) }))
    .sort((a, b) => (b.v ?? -Infinity) - (a.v ?? -Infinity) || a.name.localeCompare(b.name));
  const table = document.createElement("table");
  const cap = table.createCaption(); cap.textContent = t.mapTableCaption(entry.label[state.lang], state.year);
  const head = table.createTHead().insertRow();
  const cols = [t.tableDistrict, t.tableProvince, t.tableValue].concat(intervals.size ? [t.tableInterval] : []);
  for (const c of cols) { const th = document.createElement("th"); th.scope = "col"; th.textContent = c; head.append(th); }
  const tb = table.createTBody();
  for (const r of rows) {
    const tr = tb.insertRow();
    const th = document.createElement("th"); th.scope = "row"; th.textContent = r.name; tr.append(th);
    tr.insertCell().textContent = r.prov;
    tr.insertCell().textContent = r.v == null ? t.noData : binary ? (r.v ? t.yes : t.no) : fmtv(r.v);
    if (intervals.size) { const b = intervals.get(r.code); tr.insertCell().textContent = b ? `${fmtv(b[0])}–${fmtv(b[1])}` : "–"; }
  }
  wrap.textContent = "";
  wrap.append(table);
}

function renderTable() {
  const t = T();
  const wrap = $("chart-table");
  const btn = $("btn-table");
  btn.textContent = state.table ? t.hideTable : t.showTable;
  btn.setAttribute("aria-expanded", String(state.table));
  wrap.hidden = !state.table;
  if (!state.table || !lastData) return;
  const { fmt } = makeFormatter(state.lang);
  const fmtv = (x) => fmt(x, digits(lastData.em));
  const { seriesList, band } = lastData;
  const years = [...new Set(seriesList.flatMap((s) => s.points.map((p) => p.year)))].sort((a, b) => b - a);
  const table = document.createElement("table");
  const cap = table.createCaption(); cap.textContent = t.tableCaption(lastData.label, lastData.unit);
  const thead = table.createTHead().insertRow();
  const th0 = document.createElement("th"); th0.scope = "col"; th0.textContent = t.tableYear; thead.append(th0);
  for (const s of seriesList) { const th = document.createElement("th"); th.scope = "col"; th.textContent = s.name; thead.append(th); }
  if (band) { const th = document.createElement("th"); th.scope = "col"; th.textContent = band.label; thead.append(th); }
  const tb = table.createTBody();
  for (const y of years) {
    const tr = tb.insertRow();
    const th = document.createElement("th"); th.scope = "row"; th.textContent = y; tr.append(th);
    for (const s of seriesList) {
      const p = s.points.find((q) => q.year === y);
      tr.insertCell().textContent = p ? fmtv(p.value) + (p.lo != null ? ` (${fmtv(p.lo)}–${fmtv(p.hi)})` : "") : "–";
    }
    if (band) { const b = band.points.find((q) => q.year === y); tr.insertCell().textContent = b ? `${fmtv(b.lo)}–${fmtv(b.hi)}` : "–"; }
  }
  wrap.textContent = "";
  wrap.append(table);
}

// CSV with English column names (place names and units follow the page language), one row per place and year.
function downloadCSV() {
  if (!lastData) return;
  const rows = [["indicator", "measure", "year", "place", "code", "level", "value", "lower_bound", "upper_bound", "unit", "districts_with_data", "districts"]];
  const bandAt = new Map((lastData.band?.points || []).map((p) => [p.year, p]));
  for (const s of lastData.seriesList) {
    for (const p of s.points) {
      const b = s.isRef ? bandAt.get(p.year) : null;
      rows.push([lastData.v, lastData.em, p.year, s.name, s.code, levelOf(s.code), p.value,
        p.lo ?? b?.lo ?? "", p.hi ?? b?.hi ?? "", lastData.unit, p.n ?? "", p.N ?? ""]);
    }
  }
  const esc = (v) => { const s = String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  const blob = new Blob(["﻿" + rows.map((r) => r.map(esc).join(",")).join("\n")], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `cusco-stats_${lastData.v}_${lastData.em}.csv`;
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

function renderNotes(entry, mi, em, data) {
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
  const perPerson = em.startsWith("per_capita") || em === "per_1000";
  section(t.method, [aggText(mi.aggregation), perPerson ? t.splicedNote : ""]);
  if (!["official_rate", "official_interval", "snapshot"].includes(entry.kind)) {
    const dep = data.measures[em]?.department?.["08"] || [];
    const have = new Set(dep.map((p) => p[0]));
    const gaps = [];
    if (dep.length) for (let y = mi.years[0]; y <= mi.years[1]; y++) if (!have.has(y)) gaps.push(y);
    section(t.gaps, [gaps.length ? t.missingYears(gaps.join(", ")) : "", t.coverageRule]);
  }
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
  for (const el of document.querySelectorAll("[data-i18n-aria]")) el.setAttribute("aria-label", t[el.dataset.i18nAria]);
  const ml = document.querySelector('[data-nav="methods"]');
  if (ml) ml.setAttribute("href", `methods.html?lang=${state.lang}`);
  const head = document.querySelector("#story-kicker");
  if (head) document.querySelector("meta[name=description]")?.setAttribute("content", t.metaDescription || "");
  for (const b of document.querySelectorAll("[data-lang]")) b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang));
  $("footer-data").textContent = t.dataVintage(vintageDate(), META.built);
  document.title = state.lang === "es" ? "Cusco-stats · Los distritos de Cusco en datos" : "Cusco-stats · Districts of Cusco in data";
}

// ---------- story -> explorer ----------
function openExplorer({ v, m, real, places }) {
  state.v = v; state.m = m; state.real = real; state.year = null;
  state.places = []; slots.clear();
  for (const c of places) { state.places.push(c); assignSlot(c); }
  fillIndicatorSelect(); fillMeasureSelect();
  render();
  const ex = $("explorer");
  ex.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  ex.focus({ preventScroll: true });
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
  provinceNames = new Set(PLACES.province.map((p) => p.name));
  if (!byId.has(state.v)) state.v = DICT[0].id;

  // places from the link: keep known codes, de-duplicate, then apply the limit; restore colour slots
  const asked = state.places;
  const valid = [...new Set(asked.filter((c) => placeInfo.has(c)))];
  state.places = valid.slice(0, MAX_PLACES);
  if (valid.length > MAX_PLACES) pendingNotes.push(STRINGS[state.lang].linkTrimmed);
  const hint = state.slotHint || "";
  state.places.forEach((c) => {
    const i = asked.indexOf(c);
    assignSlot(c, hint.length === asked.length && i >= 0 ? +hint[i] : null);
  });
  state.askedYear = !!state.year;

  applyLanguage();
  fillIndicatorSelect();
  fillMeasureSelect();
  fillPlaceList();
  initStory({
    lang: () => state.lang, series, tooltip, GEO_D, GEO_P, PLACES, cssVar, openExplorer,
    label: (v) => byId.get(v)?.label[state.lang] || v,
  });

  $("sel-indicator").addEventListener("change", (e) => { state.v = e.target.value; state.year = null; fillMeasureSelect(); render(); });
  $("sel-measure").addEventListener("change", (e) => { state.m = e.target.value; fillMeasureSelect(); render(); });
  for (const b of document.querySelectorAll("[data-units]")) {
    b.addEventListener("click", () => { state.real = b.dataset.units === "real"; fillMeasureSelect(); render(); });
  }
  const inp = $("inp-place");
  const tryAdd = () => {
    if (!inp.value.trim()) return;
    const { code, ambiguous } = lookupPlace(inp.value);
    if (code) { addPlace(code, { ambiguous }); inp.value = ""; } else setStatus(T().notFound);
  };
  inp.addEventListener("change", tryAdd);
  inp.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); tryAdd(); } });
  const rng = $("rng-year");
  rng.addEventListener("input", () => {
    const years = rng.dataset.years.split(",").map(Number);
    state.year = years[Math.max(0, Math.min(years.length - 1, +rng.value))];
    render();
  });
  $("btn-table").addEventListener("click", () => { state.table = !state.table; renderTable(); });
  $("btn-map-table").addEventListener("click", () => { state.mapTable = !state.mapTable; render(); });
  $("btn-csv").addEventListener("click", downloadCSV);
  for (const b of document.querySelectorAll("[data-lang]")) {
    b.addEventListener("click", () => {
      state.lang = b.dataset.lang;
      applyLanguage(); fillIndicatorSelect(); fillMeasureSelect(); fillPlaceList(); render(); redrawStory();
    });
  }
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") tooltip.hide(); });
  document.addEventListener("pointerdown", (e) => {
    const inside = e.target.closest && (e.target.closest(".chart") || e.target.closest(".map"));
    if (!inside) tooltip.hide();
  });
  let timer;
  let lastWidth = window.innerWidth;
  window.addEventListener("resize", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (window.innerWidth === lastWidth) return;      // ignore height-only resizes (mobile address bar)
      lastWidth = window.innerWidth;
      render(); redrawStory();
    }, 150);
  });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { render(); redrawStory(); });

  await render();
  if (state.fromLink) pinExplorer();
}

// A shared explorer link opens at the explorer. Story charts above it draw lazily and can grow the
// page after the jump, so keep the explorer in place until those settle or the reader takes over.
function pinExplorer() {
  const ex = $("explorer");
  ex.scrollIntoView({ block: "start" });
  const ro = new ResizeObserver(() => ex.scrollIntoView({ block: "start" }));
  ro.observe($("story"));
  const events = ["wheel", "touchstart", "keydown", "pointerdown"];
  const stop = () => { ro.disconnect(); for (const e of events) window.removeEventListener(e, stop); };
  for (const e of events) window.addEventListener(e, stop, { passive: true });
  setTimeout(stop, 4000);
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
