// Methods & data page: prose sections (methods-text.js) plus an indicator catalogue built from
// dictionary.json, so the catalogue always matches the data the explorer shows.
import { STRINGS } from "./i18n.js";
import { METHODS } from "./methods-text.js";

const $ = (id) => document.getElementById(id);
const state = { lang: new URLSearchParams(location.search).get("lang") === "es" ? "es" : "en" };
let META = null, DICT = null;

const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
};

// "2005–2024", "2007, 2017", "2013", or "2001–2014, 2016–2022" when a range has holes
function yearText(list) {
  if (!list || !list.length) return "–";
  const runs = [];
  let a = list[0], b = list[0];
  for (const y of list.slice(1)) {
    if (y === b + 1) { b = y; continue; }
    runs.push([a, b]); a = b = y;
  }
  runs.push([a, b]);
  if (runs.length > 3 && list.length <= 4) return list.join(", ");
  return runs.map(([x, y]) => (x === y ? String(x) : y === x + 1 ? `${x}, ${y}` : `${x}–${y}`)).join(", ");
}

function aggText(agg, m) {
  const a = m.aggregation;
  if (agg.startsWith("official")) return a.official;
  if (agg.startsWith("ratio_of_sums of district")) return a.snapshot;
  return a[agg] || agg;
}

function vintageDate() { const m = /(\d{4}-\d{2}-\d{2})/.exec(META.data_vintage || ""); return m ? m[1] : META.data_vintage; }

function langHref(href) {
  const [path, hash] = href.split("#");
  const base = path.split("?")[0] || "./";
  return `${base}?lang=${state.lang}${hash ? "#" + hash : ""}`;
}

function applyChrome() {
  const t = STRINGS[state.lang], M = METHODS[state.lang];
  document.documentElement.lang = state.lang;
  for (const e of document.querySelectorAll("[data-i18n]")) {
    const v = M[e.dataset.i18n] ?? t[e.dataset.i18n];
    if (typeof v === "string") e.textContent = v;
  }
  for (const e of document.querySelectorAll("[data-i18n-aria]")) e.setAttribute("aria-label", t[e.dataset.i18nAria]);
  for (const b of document.querySelectorAll("[data-lang]")) b.setAttribute("aria-pressed", String(b.dataset.lang === state.lang));
  for (const a of document.querySelectorAll("[data-lang-link]")) a.setAttribute("href", langHref(a.getAttribute("href")));
  document.title = `${M.title} · Cusco-stats`;
  document.querySelector("meta[name=description]")?.setAttribute("content", M.metaDescription);
  $("methods-title").textContent = M.title;
  $("methods-lede").textContent = M.lede;
  $("toc-title").textContent = M.tocTitle;
  if (META) $("footer-data").textContent = t.dataVintage(vintageDate(), META.built);
}

// Prose comes from methods-text.js (static, written by the author): paragraphs and lists are given
// as plain strings, with links and emphasis as [text](url), **bold**, *italics* and `code`, converted here safely.
function inline(parent, text) {
  const re = /\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`|\*([^*]+)\*/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) parent.append(text.slice(last, m.index));
    if (m[1]) {
      const a = el("a", null, m[1]);
      let href = m[2];
      if (href === "explorer") href = `./?lang=${state.lang}#explorer`;
      a.href = href;
      parent.append(a);
    } else if (m[3]) parent.append(el("strong", null, m[3]));
    else if (m[4]) parent.append(el("code", null, m[4]));
    else parent.append(el("em", null, m[5]));
    last = re.lastIndex;
  }
  if (last < text.length) parent.append(text.slice(last));
  return parent;
}

function block(item) {
  if (typeof item === "string") return inline(el("p"), item);
  if (item.list) {
    const ul = el(item.ordered ? "ol" : "ul");
    for (const li of item.list) ul.append(inline(el("li"), li));
    return ul;
  }
  if (item.note) return inline(el("p", "methods-note"), item.note);
  if (item.cite) {
    const f = el("figure", "methods-cite");
    f.append(inline(el("blockquote"), item.cite));
    return f;
  }
  if (item.table) {
    const wrap = el("div", "table-wrap");
    const tb = el("table", "methods-table");
    if (item.caption) tb.createCaption().textContent = item.caption;
    const thead = tb.createTHead().insertRow();
    for (const h of item.table[0]) { const th = el("th", null, h); th.scope = "col"; thead.append(th); }
    const body = tb.createTBody();
    for (const row of item.table.slice(1)) {
      const tr = body.insertRow();
      row.forEach((c, i) => { const td = i === 0 ? el("th") : el("td"); if (i === 0) td.scope = "row"; inline(td, String(c)); tr.append(td); });
    }
    wrap.append(tb);
    return wrap;
  }
  return el("p", null, "");
}

function renderCatalogue(sec) {
  const M = METHODS[state.lang], t = STRINGS[state.lang];
  const intro = el("p");
  inline(intro, M.catalogue.intro(DICT.length));
  sec.append(intro);
  const cats = [];
  for (const e of [...DICT].sort((a, b) => a.order - b.order)) {
    const c = e.category[state.lang];
    let g = cats.find((x) => x.name === c);
    if (!g) { g = { name: c, items: [] }; cats.push(g); }
    g.items.push(e);
  }
  for (const g of cats) {
    sec.append(el("h3", "catalogue-cat", g.name));
    const list = el("div", "catalogue");
    for (const e of g.items) {
      const card = el("article", "cat-item");
      card.id = `var-${e.id}`;
      const head = el("div", "cat-head");
      head.append(el("h4", null, e.label[state.lang]));
      const first = e.measures.find((m) => !m.id.endsWith("_real") && !["pct_lo", "pct_hi"].includes(m.id)) || e.measures[0];
      const open = el("a", "cat-open", `${M.catalogue.open} →`);
      open.href = `./?lang=${state.lang}&v=${encodeURIComponent(e.id)}&m=${encodeURIComponent(first.id.replace(/_real$/, ""))}`;
      open.setAttribute("aria-label", `${M.catalogue.open}: ${e.label[state.lang]}`);
      head.append(open);
      card.append(head);
      card.append(el("p", "cat-desc", e.description[state.lang]));

      const dl = el("dl", "cat-facts");
      const row = (k, v) => { if (!v) return; dl.append(el("dt", null, k)); const dd = el("dd"); if (v instanceof Node) dd.append(v); else dd.textContent = v; dl.append(dd); };
      // measures: base measures with their units; note when constant-soles versions exist
      const base = e.measures.filter((m) => !m.id.endsWith("_real") && !["pct_lo", "pct_hi"].includes(m.id));
      const hasReal = e.measures.some((m) => m.id.endsWith("_real"));
      const ul = el("ul", "cat-measures");
      for (const m of base) {
        const li = el("li");
        const lab = m.label[state.lang], unit = m.unit[state.lang];
        // "Percent (%)" rather than "Percent (Percent (%))"; otherwise "Per person: current soles per person"
        if (unit.toLowerCase().startsWith(lab.toLowerCase())) li.append(el("span", "cat-m", unit));
        else li.append(el("span", "cat-m", lab), `: ${unit.charAt(0).toLowerCase()}${unit.slice(1)}`);
        if (m.map) li.append(" · ", el("span", "cat-map", M.catalogue.map));
        ul.append(li);
      }
      if (e.measures.some((m) => m.id === "pct_lo")) ul.append(el("li", null, M.catalogue.interval));
      row(M.catalogue.measures, ul);
      if (hasReal) row(M.catalogue.real, M.catalogue.realText(Math.min(...e.measures.filter((m) => m.id.endsWith("_real")).map((m) => m.years[0]))));
      // years by level (from the first base measure)
      const ybl = first.years_by_level || {};
      const yl = el("ul", "cat-years");
      for (const lv of ["department", "province", "district"]) {
        if (!ybl[lv]) continue;
        const li = el("li");
        li.append(el("span", "cat-m", M.catalogue.levels[lv]), ` ${yearText(ybl[lv])}`);
        yl.append(li);
      }
      row(M.catalogue.years, yl);
      row(M.catalogue.method, aggText(first.aggregation, t));
      const src = el("span");
      src.append(e.source[state.lang]);
      if (e.sirtod_codes && e.sirtod_codes !== "nan") src.append(el("span", "cat-codes", ` · ${t.sirtodCodes}: ${e.sirtod_codes.replace(/;\s*/g, ", ")}`));
      row(M.catalogue.source, src);
      const cav = [...new Set(e.measures.map((m) => m.caveat[state.lang]).filter(Boolean))];
      if (cav.length) {
        const cl = el("ul", "cat-caveats");
        for (const c of cav) cl.append(el("li", null, c));
        row(t.caveats, cl);
      }
      card.append(dl);
      list.append(card);
    }
    sec.append(list);
  }
}

function render() {
  applyChrome();
  const M = METHODS[state.lang];
  const body = $("methods-body"), toc = $("methods-toc");
  body.textContent = ""; toc.textContent = "";
  for (const s of M.sections) {
    const sec = el("section", "methods-section");
    sec.id = s.id;
    sec.setAttribute("aria-labelledby", `${s.id}-h`);
    const h = el("h2", null, s.title); h.id = `${s.id}-h`;
    sec.append(h);
    if (s.id === "catalogue") renderCatalogue(sec);
    else for (const item of s.body) sec.append(block(item));
    body.append(sec);
    const li = el("li"); const a = el("a", null, s.title); a.href = `#${s.id}`; li.append(a); toc.append(li);
  }
  // keep a deep link (#section or #var-id) in view after a re-render
  if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView({ block: "start" });
}

async function init() {
  try {
    [META, DICT] = await Promise.all(["data/meta.json", "data/dictionary.json"].map((u) => fetch(u).then((r) => { if (!r.ok) throw new Error(u); return r.json(); })));
  } catch (err) {
    applyChrome();
    $("methods-status").textContent = STRINGS[state.lang].loadError;
    return;
  }
  render();
  for (const b of document.querySelectorAll("[data-lang]")) {
    b.addEventListener("click", () => {
      if (b.dataset.lang === state.lang) return;
      state.lang = b.dataset.lang;
      const q = new URLSearchParams(location.search); q.set("lang", state.lang);
      history.replaceState(null, "", `${location.pathname}?${q.toString()}${location.hash}`);
      const y = window.scrollY;
      render();
      window.scrollTo(0, y);
    });
  }
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
else init();
