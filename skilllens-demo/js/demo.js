/* SkillLens research demo (coding domain). Reads PAPER (paper tables), CASE_DATA (saved per-task results)
 * and TRAJ_DATA (recorded seaborn-2848 runs). UI state only is kept under skl-demo-v1; the private
 * prep page keeps its own key and nothing here reads it. */
(function () {
"use strict";
var P = window.PAPER, D = window.CASE_DATA, T = window.TRAJ_DATA;
var KEY = "skl-demo-v1", root = document.documentElement;
var S = (function () { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } })();
function def(k, v) { if (S[k] === undefined) S[k] = v; }
def("tab", "overview"); def("theme", "auto"); def("motion", "auto"); def("model", "all"); def("cat", "all"); def("pair", "m");
def("q", ""); def("task", null); def("haiku", false); def("phase", null); def("fork", 0); def("code", "gold"); def("scroll", {}); def("back", null);
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
function tag(k, t) { return '<span class="tag ' + k + '">' + (t || { paper: "Paper", rec: "Recorded run", saved: "Saved results", log: "Log summary", post: "Post-paper", ed: "Editor's summary", teach: "Teaching layout", unk: "Not recorded" }[k]) + "</span>"; }
function $(id) { return document.getElementById(id); }
// the condensed logs mark omissions in Chinese; show them in English
function clean(s) { return String(s || "").replace(/…（省略 (\d+) 行）/g, "… ($1 lines omitted)").replace(/…\[截断\]/g, "… [truncated]"); }
function reduce() { return root.classList.contains("reduce-motion"); }
function fmt(n) { return n.toLocaleString("en-US"); }

/* ---------------- prefs, tabs, back ---------------- */
function applyPrefs() {
  if (S.theme === "auto") root.removeAttribute("data-theme"); else root.dataset.theme = S.theme;
  var r = S.motion === "reduce" || (S.motion === "auto" && matchMedia("(prefers-reduced-motion: reduce)").matches);
  root.classList.toggle("reduce-motion", r);
  document.querySelectorAll("#themeSeg button").forEach(function (b) { b.classList.toggle("on", b.dataset.themeSet === S.theme); });
  $("motionToggle").checked = r;
}
$("themeSeg").addEventListener("click", function (e) { var b = e.target.closest("button"); if (!b) return; S.theme = b.dataset.themeSet; save(); applyPrefs(); });
$("motionToggle").addEventListener("change", function (e) { S.motion = e.target.checked ? "reduce" : "full"; save(); applyPrefs(); });
document.addEventListener("click", function (e) { var m = $("more"); if (m.open && !m.contains(e.target)) m.open = false; });

function topH() { return $("topbar").offsetHeight; }
function setTopVar() { root.style.setProperty("--top", topH() + "px"); }
function scrollToEl(el) { if (!el) return; var y = el.getBoundingClientRect().top + window.scrollY - topH() - 12; window.scrollTo({ top: Math.max(0, y), behavior: reduce() ? "auto" : "smooth" }); }
var TABS = ["overview", "results", "case", "method", "evidence"];
function setTab(t, opts) {
  opts = opts || {};
  if (TABS.indexOf(t) < 0) t = "overview";
  if (S.tab !== t) { S.scroll[S.tab] = window.scrollY; }
  S.tab = t; save();
  document.querySelectorAll("[data-panel]").forEach(function (p) { p.hidden = p.dataset.panel !== t; });
  document.querySelectorAll("#nav a").forEach(function (a) { if (a.dataset.tab === t) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  if (t === "case") renderCase();
  renderBack();
  if (!opts.keepScroll) window.scrollTo(0, opts.restore && S.scroll[t] ? S.scroll[t] : 0);
}
// "← Back" returns to the place a cross-section link was clicked, with its selection and scroll position
function go(t, opts) {
  opts = opts || {};
  if (opts.back) S.back = { tab: S.tab, y: window.scrollY, label: opts.back, to: t };
  setTab(t, opts);
}
function renderBack() {
  var b = $("backbar");
  if (S.back && S.back.to === S.tab) { b.innerHTML = '<button type="button" id="backBtn">← Back to ' + esc(S.back.label) + "</button>"; b.hidden = false; }
  else { b.hidden = true; b.innerHTML = ""; }
}
$("backbar").addEventListener("click", function (e) {
  if (!e.target.closest("#backBtn") || !S.back) return;
  var bk = S.back; S.back = null; setTab(bk.tab, { keepScroll: true }); location.hash = bk.tab;
  window.scrollTo(0, bk.y);
});
$("nav").addEventListener("click", function (e) { var a = e.target.closest("a[data-tab]"); if (!a) return; e.preventDefault(); S.back = null; history.replaceState(null, "", "#" + a.dataset.tab); setTab(a.dataset.tab, { restore: true }); });
// in-page links of the form #tab or #tab/anchor
document.addEventListener("click", function (e) {
  var a = e.target.closest("a[href^='#'], [data-go]"); if (!a || a.closest("#nav")) return;
  var h = (a.dataset.go || a.getAttribute("href")).replace(/^#/, ""); if (!h) return;
  e.preventDefault();
  var parts = h.split("/"), t = parts[0];
  if (TABS.indexOf(t) < 0) return;
  // same section: just move to the anchor, keep the current scroll context
  if (t === S.tab && parts[1]) { jump(t, parts.slice(1)); return; }
  go(t, { back: a.dataset.back });
  history.replaceState(null, "", "#" + t);
  if (parts[1]) setTimeout(function () { jump(t, parts.slice(1)); }, 30);
});
function jump(t, rest) {
  if (t === "results" && rest[0] === "task") { selectTask(rest[1]); return; }
  if (t === "case" && rest[0] === "fork") { scrollToEl($("c-fork")); return; }
  var el = $(rest[0]); if (el) scrollToEl(el);
}

/* ---------------- models with per-task data ---------------- */
var DM = P.MODELS.filter(function (m) { return m.data; });
var TIDX = {}; D.tasks.forEach(function (t, i) { TIDX[t] = i; });
var CAT = {}; P.CATS.forEach(function (c) { CAT[c.skill] = c; });
var CASE_TASK = "seaborn__seaborn-2848";

/* ---------------- overview ---------------- */
function renderOverview() {
  $("citeLine").textContent = P.cite;
  var up = P.MODELS.filter(function (m) { return m.M[1] > m.B[1]; }).length, flat = P.MODELS.filter(function (m) { return m.M[1] === m.B[1]; }).length, down = P.MODELS.length - up - flat;
  $("kpis").innerHTML =
    '<div class="card kpi"><h4>Matched skill vs no skill</h4><div class="big">' + up + " up · " + flat + " flat · " + down + ' down <small>of 8 models</small></div><p class="small">Pass-rate change from N to M ranges from +12.3 (Haiku 4.5) to −5.3 points (Qwen3-8B).</p><p class="src">' + tag("paper") + 'Table 1 · 57 tasks per model · <a href="#results/r-table1">see chart</a></p></div>' +
    '<div class="card kpi"><h4>A net gain hides flips</h4><div class="big">+7 <small>= 10 repairs − 3 regressions</small></div><p class="small">Claude Haiku 4.5 under M. Qwen3-8B: 2 repairs, 5 regressions.</p><p class="src">' + tag("paper") + 'Table 3 · <a href="#results/r-ctrl">see chart</a></p></div>' +
    '<div class="card kpi"><h4>Matched vs mismatched skill</h4><div class="big">+17.5 <small>pts M − X, Gemma-4-26B</small></div><p class="small">Gemma\'s mismatched-skill score (52.6%) falls below no skill (59.6%); for Qwen3-8B, M, X and B all fall below N.</p><p class="src">' + tag("paper") + 'Table 2 · <a href="#results/r-ctrl">see chart</a></p></div>';
  var g0 = run("g_c0"), g1 = run("g_c1");
  $("casePreview").innerHTML = '<p class="kicker">Recorded runs · open case</p><h3>seaborn-2848: solved without the skill, looped with it</h3>' +
    '<p class="small">Same SWE-bench Lite task, same model (Gemma-4-26B). Without the skill the agent fixed the bug and submitted at step ' + last(g0) + '. With the skill prepended it hit <b>IndentationError ' + countIE(g1) + " times</b> and stopped at the 5,400 s limit.</p>" +
    '<div class="mini-lanes">' + lanes(["g_c0", "g_c1"], { mini: true }) + "</div>" +
    '<p><a class="btn primary" href="#case" data-back="Overview">Open the case →</a> <a class="btn" href="#case/fork" data-back="Overview">Jump to the key fork</a></p>' +
    '<p class="src">' + tag("rec") + "Trajectories from sbench trial directories; one task, one pair of runs.</p>";
  $("varLine").textContent = P.VAR.map(function (v) { return v[0] + " " + v[1] + "%"; }).join(", ");
}

/* ---------------- results charts ---------------- */
function pos(v, lo, hi) { return ((v - lo) / (hi - lo) * 100).toFixed(2) + "%"; }
function axis(lo, hi, step, cls) { var s = ""; for (var v = lo; v <= hi; v += step) s += '<span style="left:' + pos(v, lo, hi) + '">' + v + "%</span>"; return '<div class="' + (cls || "db-axis") + '"><span></span><div class="ticks">' + s + "</div><span></span></div>"; }
function renderT1() {
  var lo = 20, hi = 100;
  $("chartT1").innerHTML = P.MODELS.map(function (m) {
    var a = m.B[0], b = m.M[0], up = b >= a;
    return '<div class="db-row' + (m.data ? "" : " dim") + '"><span class="db-name">' + (m.data ? '<button type="button" class="linkish" data-model="' + m.data + '" style="border:0;background:none;padding:0;color:var(--accent);cursor:pointer;text-align:left;font:inherit">' + esc(m.name) + "</button>" : esc(m.name) + ' <span class="muted small">(paper only)</span>') + "</span>" +
      '<div class="db-track" role="img" aria-label="' + esc(m.name) + ": N " + a + "%, M " + b + "%, R " + m.R[0] + '%">' +
      '<span class="db-seg ' + (up ? "up" : "down") + '" style="left:' + pos(Math.min(a, b), lo, hi) + ";width:calc(" + pos(Math.max(a, b), lo, hi) + " - " + pos(Math.min(a, b), lo, hi) + ')"></span>' +
      '<i class="mk r" style="left:' + pos(m.R[0], lo, hi) + '"></i><i class="mk n" style="left:' + pos(a, lo, hi) + '"></i><i class="mk m" style="left:' + pos(b, lo, hi) + '"></i></div>' +
      '<span class="db-val">' + m.B[1] + " → " + m.M[1] + " · R " + m.R[1] + " /57</span></div>";
  }).join("") + axis(lo, hi, 20);
}
function renderCats() {
  $("chartCats").innerHTML = P.CATS.map(function (c) {
    var w = Math.abs(c.u) / 25 * 50;
    return '<div class="br' + (S.cat === c.skill ? " on" : "") + '"><button type="button" data-cat="' + c.skill + '">' + esc(c.name) + '</button><div class="div-track"><span class="div-bar ' + (c.u >= 0 ? "pos" : "neg") + '" style="' + (c.u >= 0 ? "left:50%" : "left:" + (50 - w) + "%") + ";width:" + w + '%"></span></div>' +
      '<span class="db-val">' + (c.u > 0 ? "+" : "") + c.u.toFixed(1) + "% · ▲" + c.r + " ▼" + c.g + " · n=" + c.n + "</span></div>";
  }).join("") + '<div class="br"><span></span><div class="div-track" style="height:14px;font-size:.68rem;color:var(--ink-3)"><span style="position:absolute;left:0">−25%</span><span style="position:absolute;left:50%;transform:translateX(-50%)">0</span><span style="position:absolute;right:0">+25%</span></div><span></span></div>';
}
function renderCtrl() {
  var lo = 20, hi = 100;
  $("chartCtrl").innerHTML = P.CTRL.map(function (c) {
    var mx = ((c.M[1] - c.X[1]) / 57 * 100).toFixed(1);
    return '<div class="db-row"><span class="db-name">' + esc(c.name) + '</span><div class="db-track" role="img" aria-label="' + esc(c.name) + ": N " + c.N[0] + ", M " + c.M[0] + ", X " + c.X[0] + ", B " + c.B[0] + '">' +
      ["B", "X", "N", "M"].map(function (k) { return '<i class="mk ' + k.toLowerCase() + '" style="left:' + pos(c[k][0], lo, hi) + '" title="' + k + " " + c[k][0] + "% (" + c[k][1] + '/57)"></i>'; }).join("") +
      '</div><span class="db-val">M−X ' + (mx > 0 ? "+" : "") + mx + "</span></div>";
  }).join("") + axis(lo, hi, 20);
  $("chartUptake").innerHTML = '<div class="bars">' + P.UPTAKE.map(function (u) {
    return '<div class="br"><span>' + esc(u.name) + '</span><div style="display:grid;gap:2px"><span style="display:block;height:9px;border-radius:3px;background:var(--ok);width:' + (u.r * 10) + '%"></span><span style="display:block;height:9px;border-radius:3px;background:var(--bad);width:' + (u.g * 10) + '%"></span></div><span class="db-val">▲' + u.r + " ▼" + u.g + " · " + (u.u > 0 ? "+" : "") + u.u + "%</span></div>";
  }).join("") + '<div class="br"><span></span><span class="small muted">bar length = number of tasks (0–10); green repairs, red regressions</span><span></span></div></div>';
}

/* ---------------- task grid ---------------- */
function cellOf(mi, ti) {
  var r = D.res[DM[mi].data], n = r.n[ti], c = S.pair === "r" ? r.r[ti] : r.m[ti];
  return n === 0 && c === 1 ? "rep" : n === 1 && c === 0 ? "reg" : n === 1 ? "pp" : "ff";
}
var SYM = { rep: "▲", reg: "▼", pp: "●", ff: "○" };
function renderFilters() {
  $("filters").innerHTML =
    '<label>Model <select id="fModel"><option value="all">All 7 models with per-task data</option>' + DM.map(function (m) { return '<option value="' + m.data + '">' + esc(m.name) + "</option>"; }).join("") + "</select></label>" +
    '<label>Category <select id="fCat"><option value="all">All 10 categories</option>' + P.CATS.map(function (c) { return '<option value="' + c.skill + '">' + esc(c.name) + " (" + c.n + ")</option>"; }).join("") + "</select></label>" +
    '<span>Compare <span class="seg" id="fPair"><button type="button" data-pair="m">M vs N</button><button type="button" data-pair="r">R vs N</button></span></span>' +
    '<label>Task <input id="fQ" type="search" placeholder="task id contains…" size="16"></label>';
  $("fModel").value = S.model; $("fCat").value = S.cat; $("fQ").value = S.q;
  $("fModel").addEventListener("change", function (e) { S.model = e.target.value; save(); renderGrid(); });
  $("fCat").addEventListener("change", function (e) { S.cat = e.target.value; save(); renderGrid(); renderCats(); });
  $("fQ").addEventListener("input", function (e) { S.q = e.target.value.trim(); save(); renderGrid(); });
  $("fPair").addEventListener("click", function (e) { var b = e.target.closest("button"); if (!b) return; S.pair = b.dataset.pair; save(); renderGrid(); if (S.task) renderTask(); });
}
function renderGrid() {
  document.querySelectorAll("#fPair button").forEach(function (b) { b.classList.toggle("on", b.dataset.pair === S.pair); });
  if ($("fModel")) { $("fModel").value = S.model; $("fCat").value = S.cat; }
  var models = DM.map(function (m, i) { return i; }).filter(function (i) { return S.model === "all" || DM[i].data === S.model; });
  var tasks = D.tasks.map(function (t, i) { return i; }).filter(function (i) { return (S.cat === "all" || D.cat[i] === S.cat) && (!S.q || D.tasks[i].toLowerCase().indexOf(S.q.toLowerCase()) >= 0); });
  var cnt = { rep: 0, reg: 0, pp: 0, ff: 0 };
  tasks.forEach(function (ti) { models.forEach(function (mi) { cnt[cellOf(mi, ti)]++; }); });
  var pairs = tasks.length * models.length, cname = S.pair === "r" ? "R (routed) vs N" : "M (matched) vs N";
  $("scope").innerHTML = "<b>Scope:</b> " + (models.length === 1 ? esc(DM[models[0]].name) : models.length + " models") + " × " + tasks.length + " task" + (tasks.length === 1 ? "" : "s") + " = <b>" + pairs + "</b> model–task pairs · " + cname +
    (S.cat !== "all" ? " · category " + esc(CAT[S.cat].name) + " (" + esc(CAT[S.cat].bench) + ")" : "") + " · " + tag("saved") + "per-task file, commit 3afdc03. GPT-5.6-Sol: no per-task data.";
  $("counts").innerHTML = '<span class="count"><b class="ok">' + cnt.rep + "</b>repairs</span>" + '<span class="count"><b class="bad">' + cnt.reg + "</b>regressions</span>" +
    '<span class="count"><b>' + cnt.pp + "</b>pass in both</span>" + '<span class="count"><b>' + cnt.ff + "</b>fail in both</span>" +
    '<span class="count">net ' + (pairs ? ((cnt.rep - cnt.reg) / pairs * 100).toFixed(1) : "0.0") + " points over " + pairs + " pairs</span>" +
    (S.model !== "all" || S.cat !== "all" || S.q ? '<button type="button" class="btn small" id="fClear">Clear filters</button>' : "");
  var cols = models.length, head = '<div class="tg-head" style="--cols:' + cols + '"><span>task</span>' + models.map(function (mi) { return '<span class="v">' + esc(DM[mi].name) + "</span>"; }).join("") + '<span class="hs">recorded runs</span></div>';
  var body = "";
  P.CATS.forEach(function (c) {
    var ts = tasks.filter(function (ti) { return D.cat[ti] === c.skill; }); if (!ts.length) return;
    body += '<div class="tg-cat">' + esc(c.name) + " · " + esc(c.bench) + "</div>";
    ts.forEach(function (ti) {
      body += '<button type="button" class="tg-row' + (S.task === D.tasks[ti] ? " sel" : "") + '" style="--cols:' + cols + '" data-task="' + esc(D.tasks[ti]) + '"><span class="tid" title="' + esc(D.tasks[ti]) + '">' + esc(D.tasks[ti]) + "</span>" +
        models.map(function (mi) { var k = cellOf(mi, ti); return '<span class="cell ' + k + '" title="' + esc(DM[mi].name) + ": " + { rep: "repair", reg: "regression", pp: "pass in both", ff: "fail in both" }[k] + '">' + SYM[k] + "</span>"; }).join("") +
        '<span class="has">' + (D.tasks[ti] === CASE_TASK ? "3 runs ›" : "") + "</span></button>";
    });
  });
  $("taskGrid").innerHTML = tasks.length ? head + body : '<p class="note">No task matches the current filters.</p>';
}
$("taskGrid") && document.addEventListener("click", function (e) {
  var r = e.target.closest(".tg-row"); if (r) { selectTask(r.dataset.task); return; }
  var m = e.target.closest("[data-model]"); if (m) { S.model = m.dataset.model; save(); renderGrid(); scrollToEl($("r-grid")); return; }
  var c = e.target.closest("[data-cat]"); if (c) { S.cat = S.cat === c.dataset.cat ? "all" : c.dataset.cat; save(); renderGrid(); renderCats(); scrollToEl($("r-grid")); return; }
  if (e.target.closest("#fClear")) { S.model = "all"; S.cat = "all"; S.q = ""; save(); $("fQ").value = ""; renderGrid(); renderCats(); return; }
  if (e.target.closest("#tdClose")) { S.task = null; save(); renderTask(); renderGrid(); }
});
function selectTask(id) {
  if (TIDX[id] === undefined) return;
  S.task = id; save(); renderTask(); renderGrid();
  scrollToEl($("taskDetail"));
}
var SEL = { c: "the matched skill", w: "another skill", n: "no skill", u: "not recorded" };
function renderTask() {
  var box = $("taskDetail"); if (!S.task) { box.innerHTML = ""; return; }
  var ti = TIDX[S.task], c = CAT[D.cat[ti]], isCase = S.task === CASE_TASK;
  box.innerHTML = '<div class="card task-detail anchor" id="td"><div style="display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;justify-content:space-between"><h3 style="margin:0"><code>' + esc(S.task) + '</code></h3><button type="button" class="btn small" id="tdClose">Close</button></div>' +
    '<p class="small">' + esc(c.name) + " · benchmark " + esc(c.bench) + " · verifier: " + esc(c.verifier) + "</p>" +
    '<div class="tbl-wrap"><table><thead><tr><th>Model</th><th>N</th><th>M</th><th>R</th><th>Router picked</th><th>M vs N</th></tr></thead><tbody>' +
    DM.map(function (m) { var r = D.res[m.data], n = r.n[ti], mm = r.m[ti], rr = r.r[ti], k = n === 0 && mm === 1 ? "repair" : n === 1 && mm === 0 ? "regression" : n === 1 ? "pass in both" : "fail in both";
      function yn(v) { return v === 1 ? '<span class="ok">pass</span>' : '<span class="bad">fail</span>'; }
      return "<tr><td>" + esc(m.name) + "</td><td>" + yn(n) + "</td><td>" + yn(mm) + "</td><td>" + yn(rr) + "</td><td>" + SEL[r.sel[ti]] + "</td><td>" + k + "</td></tr>"; }).join("") +
    "</tbody></table></div>" +
    (isCase ? '<p>' + tag("rec") + 'Three recorded runs exist for this task: Gemma-4-26B under N and M, and Claude Haiku 4.5 under M. <a class="btn small primary" href="#case" data-back="Results · ' + esc(S.task) + '">Open the case →</a></p>'
      : '<p class="small muted">' + tag("unk", "No trajectory in this demo") + "Only the per-task results are shown here; this demo extracts trajectories for seaborn-2848 only.</p>") +
    '<p class="src">' + tag("saved") + "per-task file, commit 3afdc03 · router choice from the R-condition results</p></div>";
}

/* ---------------- case: recorded runs of seaborn-2848 ---------------- */
function run(k) { return T.runs.filter(function (r) { return r.key === k; })[0]; }
function last(r) { return r.steps[r.steps.length - 1].id; }
function countIE(r) { return r.steps.filter(function (s) { return s.out.indexOf("IndentationError") >= 0; }).length; }
function stepOf(r, id) { return r.steps.filter(function (s) { return s.id === id; })[0]; }
var RUNS = {
  g_c0: { label: "Gemma-4-26B · N", sub: "no skill · rerun", cls: "n", end: "✓ submitted", secs: 215, tin: 353432, tout: 6950,
    phases: [["k-env", "Missing dependencies", "The reproduction script first fails with ModuleNotFoundError: matplotlib; after installing current versions, register_cmap is missing."],
      ["k-env", "Environment compatibility", "Edits seaborn/cm.py for newer matplotlib, then downgrades pandas and numpy. None of this is the issue itself."],
      ["k-repro", "Reproduce the issue", "Step 24 finally shows the TypeError from the issue: ufunc 'isnan' not supported."],
      ["k-fix", "Locate and fix", "Finds _lookup_single in _oldcore.py; meets 'NoneType' object is not callable and one IndentationError; rewrites the whole function at step 33."],
      ["k-done", "Verify and submit", "The reproduction script prints 'Successfully ran pairplot!'; a few extra cases pass; the agent submits."]] },
  g_c1: { label: "Gemma-4-26B · M", sub: "+ python-traceback-reading v3.0", cls: "m", end: "✕ timeout 5,400 s", secs: 5443, tin: 40464364, tout: 125436,
    phases: [["k-env", "Missing dependencies", "Same dependency problems as under N: installs matplotlib and pandas, then downgrades to compatible versions."],
      ["k-repro", "Reproduce the issue", "Reproduces the isnan TypeError at step 15, earlier than step 24 under N."],
      ["k-read", "Read the source", "Reads lines 140–170 of _oldcore.py and settles on the same location as under N."],
      ["k-loop", "Patch loop", "Replaces the code block with Python scripts again and again; each attempt leaves an indentation error. IndentationError appears 91 times between steps 25 and 347, until the 5,400 s limit; nothing is submitted."]] },
  h_c1: { label: "Claude Haiku 4.5 · M", sub: "+ skill · pass via upstream commit", cls: "h", end: "✓ submitted", secs: 370, tin: 2044826, tout: 14734,
    phases: [["k-env", "Missing dependencies", "Also starts without matplotlib; installs and downgrades dependencies."],
      ["k-read", "Search the code", "Searches axisgrid.py and _oldcore.py for hue_order, categorical_order and isnan."],
      ["k-leak", "Find the upstream fix in git history", "git log --all lists 7b3e4dfd 'Fix hue_order as a subset in scatterplot (#2848)'; git show prints the full diff, including the test change."],
      ["k-fix", "Write the patch from the commit", "Writes a patch identical to the upstream commit (same comment text), then handles the isnan branch."],
      ["k-fix", "Fix compatibility and indentation", "Fixes a pandas option incompatibility and an indentation error it introduced."],
      ["k-done", "Verify and submit", "The reproduction script passes; it also runs the verifier's test by name, a name it saw in the git show output at step 35."]] }
};
var XMAX = 350;
function lanes(keys, o) {
  o = o || {};
  var html = keys.map(function (k) {
    var r = run(k), L = RUNS[k], end = last(r);
    return '<div class="lane"><div class="lane-name"><b>' + esc(L.label) + "</b><small>" + esc(L.sub) + "</small></div>" +
      '<div class="lane-track" role="group" aria-label="' + esc(L.label) + ' phases by step index">' + r.phases.map(function (p, i) {
        var x0 = p.r[0], x1 = p.r[1] + 1, id = k + ":" + i;
        return '<button type="button" class="ph ' + L.phases[i][0] + (S.phase === id && !o.mini ? " on" : "") + '"' + (o.mini ? ' tabindex="-1"' : "") + ' data-ph="' + id + '" style="left:' + pos(x0, 0, XMAX) + ";width:" + pos(x1 - x0, 0, XMAX) + '" title="' + esc(L.phases[i][1]) + " · steps " + p.r[0] + "–" + p.r[1] + '"></button>';
      }).join("") + '<span class="lane-end ' + (L.end[0] === "✓" ? "ok" : "bad") + (end > 250 ? " in" : "") + '" style="left:' + pos(end + 1, 0, XMAX) + '">' + esc(L.end) + "</span></div></div>" +
      (o.mini ? "" : '<div class="phase-list">' + r.phases.map(function (p, i) { var id = k + ":" + i; return '<button type="button" data-ph="' + id + '" class="' + (S.phase === id ? "on" : "") + '">' + esc(L.phases[i][1]) + " · " + p.r[0] + "–" + p.r[1] + "</button>"; }).join("") + "</div>");
  }).join("");
  var ticks = ""; for (var v = 0; v <= XMAX; v += 50) ticks += '<span style="left:' + pos(v, 0, XMAX) + '">' + v + "</span>";
  return html + '<div class="lane-axis"><span class="lab0">step index</span><div class="ticks">' + ticks + "</div></div>";
}
function stepCard(r, id, opts) {
  var s = stepOf(r, id); if (!s) return "";
  opts = opts || {};
  var rc = s.rc === 0 ? "ok" : s.rc === -1 ? "na" : "bad";
  return '<li class="step"><div class="step-h"><b>step ' + s.id + '</b><span class="rc ' + rc + '">exit ' + s.rc + "</span>" + (s.out.indexOf("IndentationError") >= 0 ? '<span class="rc bad">IndentationError</span>' : "") + "</div>" +
    "<pre>$ " + esc(clean(s.cmd).split("\n").slice(0, opts.cmdLines || 8).join("\n")) + "</pre>" + (s.out ? "<pre>" + esc(clean(s.out).split("\n").slice(-(opts.outLines || 8)).join("\n")) + "</pre>" : "") + "</li>";
}
function renderPhase() {
  var box = $("phaseDetail"); if (!box) return;
  if (!S.phase) { box.innerHTML = '<p class="small muted">Click a phase above to see its recorded commands and outputs.</p>'; return; }
  var k = S.phase.split(":")[0], i = +S.phase.split(":")[1], r = run(k), p = r.phases[i], L = RUNS[k];
  box.innerHTML = '<div class="card"><h4 style="margin:0 0 4px">' + esc(L.label) + " · " + esc(L.phases[i][1]) + ' <span class="muted small">steps ' + p.r[0] + "–" + p.r[1] + "</span></h4>" +
    '<p class="small">' + tag("ed") + esc(L.phases[i][2]) + "</p>" +
    '<p class="small">' + tag("rec") + "Key steps, command and the tail of its output (condensed log):</p><ul class=\"steps\">" + p.k.map(function (id) { return stepCard(r, id); }).join("") + "</ul></div>";
}
// the key fork: both Gemma runs hit an IndentationError after a scripted block replacement
var FORK = {
  n: [[30, "write", "Write patch", "Python script replaces the function"], [31, "err", "Run the reproduction script", "IndentationError: expected an indented block after function definition"],
    [32, "read", "Inspect lines 140–175", "reads the file it just edited"], [33, "write", "Diagnose and rewrite", "comment: \"I added two def _lookup_single\"; rewrites the whole function"],
    [34, "okk", "Run the reproduction script", "Successfully ran pairplot!"], [36, "end", "Submit", "after extra checks at step 35"]],
  m: [[346, "restore", "Restore the file", "git checkout seaborn/_oldcore.py → \"Updated 1 path from the index\""], [346, "write", "Write patch", "same command: Python script replaces the block → \"Successfully replaced the block.\""],
    [347, "err", "Run the reproduction script", "IndentationError: expected an indented block after 'try' statement"], [348, "read", "Inspect lines 145–175", "reads the file again"],
    [349, "restore", "Restore and patch again", "\"Updated 1 path from the index\" · \"Successfully replaced the block.\""], [null, "end", "Time limit reached", "AgentTimeoutError at 5,400 s; nothing submitted"]]
};
var KD = { write: "write", err: "error", read: "read", restore: "restore", okk: "ok", end: "end" };
function forkCol(side) {
  var r = run(side === "n" ? "g_c0" : "g_c1");
  return FORK[side].map(function (f, i) {
    var s = f[0] ? stepOf(r, f[0]) : null, st = i < S.fork ? "seen" : i === S.fork ? "cur" : "";
    var ex = "";
    if (s) {
      if (f[1] === "err" || f[1] === "okk") ex = clean(s.out).split("\n").slice(-3).join("\n");
      else if (f[1] === "restore" || (f[1] === "write" && side === "m")) ex = (f[1] === "restore" ? clean(s.cmd).split("\n")[0] + "\n" : "") + clean(s.out).split("\n").slice(0, 2).join("\n");
      else if (f[1] === "read") ex = "$ " + clean(s.cmd).split("\n")[0];
      else ex = clean(s.cmd).split("\n").slice(0, 3).join("\n");
    }
    // order interleaves N and M station by station when the two columns stack on narrow screens
    return '<div class="fstep ' + st + '" data-fi="' + i + '" style="order:' + (10 + i * 2 + (side === "m" ? 1 : 0)) + '"><div class="act"><span class="side s-' + side + '">' + (side === "n" ? "N" : "M") + '</span><span class="kd ' + f[1] + '">' + KD[f[1]] + "</span>" + esc(f[2]) + ' <span class="muted small">' + (f[0] ? "step " + f[0] : "—") + "</span></div>" +
      '<div class="small">' + esc(f[3]) + "</div>" + (ex ? "<pre>" + esc(ex) + "</pre>" : "") + "</div>";
  }).join("");
}
var playT = null;
function renderFork() {
  var n = FORK.n.length;
  $("forkRail").innerHTML = FORK.n.map(function (f, i) { return '<button type="button" data-fk="' + i + '" class="' + (i === S.fork ? "on" : i < S.fork ? "done" : "") + '">' + (i + 1) + "</button>"; }).join("");
  $("forkN").innerHTML = forkCol("n"); $("forkM").innerHTML = forkCol("m");
  $("forkPlay").textContent = playT ? "❚❚ Pause" : S.fork >= n - 1 ? "↺ Replay" : S.fork > 0 ? "▶ Continue" : "▶ Replay the fork";
}
function follow() {
  // keep the current pair on screen while it plays
  var cur = document.querySelectorAll("#caseBody .fstep.cur"), lastCur = cur[cur.length - 1]; if (!lastCur) return;
  var r = lastCur.getBoundingClientRect(); if (r.bottom > window.innerHeight - 8) window.scrollBy({ top: r.bottom - window.innerHeight + 16, behavior: reduce() ? "auto" : "smooth" });
}
function tick() { if (S.fork >= FORK.n.length - 1) { playT = null; renderFork(); return; } S.fork++; save(); renderFork(); follow(); playT = setTimeout(tick, 1500); }
function forkPlay() {
  if (playT) { clearTimeout(playT); playT = null; renderFork(); return; }
  if (S.fork >= FORK.n.length - 1) S.fork = 0;
  if (reduce()) { S.fork = FORK.n.length - 1; save(); renderFork(); return; }
  save(); playT = setTimeout(tick, 900); renderFork();
}
function diffHtml(txt) {
  return clean(txt).split("\n").map(function (l) { var c = /^\+(?!\+\+)/.test(l) ? "add" : /^-(?!--)/.test(l) ? "del" : /^@@/.test(l) ? "hunk" : ""; return c ? '<span class="' + c + '">' + esc(l) + "</span>" : esc(l); }).join("\n");
}
function renderCode() {
  var C = { gold: ["Upstream fix (gold patch)", diffHtml(D.gold), "harbor task <code>seaborn__seaborn-2848_wo/solution/solve.sh</code>"],
    n: ["N: function after step 33", esc(D.n_fn.join("\n")), "reconstructed from the command text of step 33 (Gemma · N)"],
    m: ["M: block written at step 24", esc(D.m_blk.join("\n")), "taken from the command text of step 24 (Gemma · M); later attempts vary"] };
  $("codeTabs").innerHTML = Object.keys(C).map(function (k) { return '<button type="button" data-code="' + k + '" class="' + (S.code === k ? "on" : "") + '">' + C[k][0] + "</button>"; }).join("");
  $("codeBox").innerHTML = C[S.code][1];
  $("codeSrc").innerHTML = tag("rec") + C[S.code][2];
}
function renderFacts() {
  var keys = ["g_c0", "g_c1", "h_c1"], rows = [
    ["Last step index", "trajectory step id", function (k) { return last(run(k)); }],
    ["Commands recorded", "shell commands in the log", function (k) { return run(k).steps.length; }],
    ["IndentationError outputs", "outputs containing the error", function (k) { return countIE(run(k)); }],
    ["Wall-clock time (s)", "from the results CSV", function (k) { return RUNS[k].secs; }],
    ["Input tokens", "from the results CSV", function (k) { return RUNS[k].tin; }]];
  $("factsChart").innerHTML = rows.map(function (row) {
    var vals = keys.map(row[2]), mx = Math.max.apply(null, vals) || 1;
    return '<div class="fr"><div><b>' + row[0] + '</b><div class="small muted">' + row[1] + ' · own scale</div></div><div class="fr-bars">' + keys.map(function (k, i) {
      return '<div class="fb"><span>' + esc(RUNS[k].label.replace("Claude ", "").replace("Gemma-4-26B", "Gemma")) + '</span><span class="t ' + RUNS[k].cls + '" style="width:' + Math.max(1, vals[i] / mx * 100) + '%"></span><span class="v">' + fmt(vals[i]) + "</span></div>";
    }).join("") + "</div></div>";
  }).join("");
}
var built = false;
function renderCase() {
  if (built) { renderPhase(); renderFork(); return; }
  built = true;
  var ti = TIDX[CASE_TASK], g0 = run("g_c0"), g1 = run("g_c1"), h1 = run("h_c1");
  var nPass = DM.filter(function (m) { return D.res[m.data].n[ti] === 1; }).length, mPass = DM.filter(function (m) { return D.res[m.data].m[ti] === 1; }).length;
  var issueFirst = T.task.issue.split("\n").slice(0, 6).join("\n");
  $("caseBody").innerHTML =
  '<nav class="jumps" aria-label="Case sections"><a href="#case/c-input">1 Input</a><a href="#case/c-path">2 Execution path</a><a class="key" href="#case/c-fork">3 Key fork</a><a href="#case/c-code">4 Code</a><a href="#case/c-facts">5 Run facts</a><a href="#case/c-verdict">6 Verifier</a><a href="#case/c-limits">Limits</a></nav>' +
  '<div class="case-head"><div>' +
    '<p class="lead">In seaborn 0.11.1, calling <code>pairplot</code> with a <code>hue_order</code> that lists only some of the hue values raises <code>TypeError: ufunc \'isnan\' not supported</code>. The agent works inside a container holding the seaborn repository and must change the code so that the task\'s tests pass. The two Gemma runs below receive the same instruction, except that the M run has the category skill <code>python-traceback-reading</code> prepended.</p>' +
    '<dl class="card facts"><dt>Task</dt><dd><code>' + CASE_TASK + '</code> · SWE-bench Lite · category Python traceback reading (9 tasks)</dd><dt>Verifier</dt><dd>FAIL_TO_PASS <code>' + esc(T.task.f2p) + '</code> + 50 PASS_TO_PASS tests (pytest)</dd><dt>Agent</dt><dd>mini-swe-agent in a Docker container; one shell command per step</dd><dt>Runs shown</dt><dd>Gemma-4-26B under N and under M; Claude Haiku 4.5 under M (optional lane)</dd></dl></div>' +
    '<div class="card"><h3 style="margin-top:0">This task across models</h3><p class="small">Pass under N and M, 7 paper models:</p><div class="strip">' +
      DM.map(function (m) { var r = D.res[m.data]; function s(v) { return v === 1 ? '<b class="ok">✓</b>' : '<b class="bad">✕</b>'; } return '<span class="sm">' + esc(m.name.replace("Claude ", "")) + " N" + s(r.n[ti]) + " M" + s(r.m[ti]) + "</span>"; }).join("") +
    '</div><p class="small"><b>N ' + nPass + "/7 → M " + mPass + '/7.</b> Regressions: Sonnet 4.6, Gemma-4-26B, GLM-5.1. Repair: Haiku 4.5, whose M run read the upstream fix from git history (see verdicts).</p>' +
    '<p class="src">' + tag("saved") + 'per-task file · <a href="#results/task/' + CASE_TASK + '">this task in the grid</a></p></div></div>' +

  '<h2 class="anchor" id="c-input">1 · What differs in the input</h2>' +
    '<div class="prompt-bar"><span><b>N</b></span><div class="pb"><span class="lab">task instruction (identical in both runs)</span></div></div>' +
    '<div class="prompt-bar"><span><b>M</b></span><div class="pb"><span class="ins" style="left:2%;width:46%">skill · 7,856 characters, inserted at character 25</span><span class="lab">rest identical</span></div></div>' +
    '<p class="src">' + tag("rec") + "The two prompts were compared verbatim: the only difference is the inserted skill (<code>python-traceback-reading</code> v3.0). " + tag("teach") + "bar widths are not to scale.</p>" +
    '<details><summary>Show the injected skill text</summary><div class="scrollbox wrapit">' + esc(T.skill.text) + "</div></details>" +
    '<details><summary>Show the task issue text</summary><div class="scrollbox wrapit">' + esc(T.task.issue) + "</div></details>" +

  '<h2 class="anchor" id="c-path">2 · Execution path</h2>' +
    '<p class="small">Each bar is one run on a shared axis of trajectory step index; colored segments are phases. Click a phase to inspect its commands. <label style="margin-left:6px"><input type="checkbox" id="haikuToggle"' + (S.haiku ? " checked" : "") + "> show Claude Haiku 4.5 · M</label></p>" +
    '<div class="lanes" id="lanes"></div>' +
    '<div class="legend"><span><i class="mk" style="background:color-mix(in srgb,var(--teach) 55%,transparent)"></i>environment</span><span><i class="mk" style="background:color-mix(in srgb,var(--n) 55%,transparent)"></i>reproduce</span><span><i class="mk" style="background:color-mix(in srgb,var(--accent) 35%,transparent)"></i>read code</span><span><i class="mk" style="background:color-mix(in srgb,var(--ok) 60%,transparent)"></i>fix</span><span><i class="mk" style="background:var(--bad)"></i>patch loop</span><span><i class="mk" style="background:var(--warn)"></i>upstream fix read</span></div>' +
    '<p class="src">' + tag("rec") + "step ids and commands from the trajectories · " + tag("ed") + "phase boundaries and names are the editor's grouping</p>" +
    '<div class="phase-detail anchor" id="phaseDetail"></div>' +

  '<h2 class="anchor" id="c-fork">3 · The key fork: the same IndentationError, two recoveries</h2>' +
    '<p class="small">Both Gemma runs replace a code block with a Python script and break the indentation. Under N the agent reads the file, names the cause and rewrites the function once. Under M the same cycle repeats until the time limit.</p>' +
    '<div class="fork-ctl"><button type="button" class="btn primary" id="forkPlay"></button><span class="fork-rail" id="forkRail" aria-label="Replay stage"></span><a class="btn small" href="#case/c-path" id="forkLog">Inspect the full patch-loop log ↓</a></div>' +
    '<div class="fork-cols"><div class="fork-col"><h4>Gemma-4-26B · N <small>steps 30–36</small></h4><div id="forkN"></div></div>' +
    '<div class="fork-col"><h4>Gemma-4-26B · M <small>last cycle, steps 346–349</small></h4><div class="loopnote"><b>×' + countIE(g1) + '</b><span>IndentationError outputs between steps 25 and 347. The first cycle starts with the patch at step 24; one shell command can restore and re-patch in the same step.</span></div><div id="forkM"></div></div></div>' +
    '<p class="src">' + tag("rec") + "commands and outputs from the trajectories (condensed) · " + tag("ed") + "action labels</p>" +

  '<h2 class="anchor" id="c-code">4 · Code</h2><div class="tabs" id="codeTabs"></div><div class="scrollbox diff" id="codeBox"></div><p class="src" id="codeSrc"></p>' +

  '<h2 class="anchor" id="c-facts">5 · Run facts</h2><p class="small muted">Different quantities, each with its own scale. Step index, commands, error count and time are not interchangeable.</p><div class="facts-chart" id="factsChart"></div>' +
    '<p class="src">' + tag("rec") + "trajectories · " + tag("saved") + "time and tokens from the results CSV. Output tokens: N " + fmt(RUNS.g_c0.tout) + ", M " + fmt(RUNS.g_c1.tout) + ", Haiku M " + fmt(RUNS.h_c1.tout) + ".</p>" +

  '<h2 class="anchor" id="c-verdict">6 · Verifier results and conditions</h2><div class="verdicts">' +
    '<div class="card verdict"><h4>Gemma-4-26B · N</h4><p class="st ok">pass (reward 1.0)</p><p class="small">This is a rerun: the first attempt ended with NonZeroAgentExitCodeError after 0 tokens (reward 0). The rerun\'s verifier output directory was not saved, so test-level results cannot be inspected.</p><p class="src">' + tag("rec") + "<code>wo_trials/full_gemma_wo_rerun_11/…</code> result.json</p></div>" +
    '<div class="card verdict"><h4>Gemma-4-26B · M</h4><p class="st bad">fail (reward 0) · AgentTimeoutError, 5,400 s</p><p class="small">The source is left with an IndentationError, so test collection fails: test_hue_order fails and 0 of 50 PASS_TO_PASS tests pass. The timeout was scored 0 and not rerun. Skill keywords (bottom-up, producer, root cause) do not appear in the trajectory, which does not settle whether the model used the skill.</p><p class="src">' + tag("rec") + "<code>ws_trials/full_gemma_ws_55/…</code> verifier/report.json</p></div>" +
    '<div class="card verdict"><h4>Claude Haiku 4.5 · M</h4><p class="st ok">pass (resolved) · F2P pass, P2P 50/50</p><p class="small">At steps 34–35 the agent ran <code>git log --all</code> and <code>git show 7b3e4dfd</code>, the upstream fix for this issue; its patch at step 43 matches that commit line for line. This pass cannot be attributed to the skill. Its N run is ' + tag("unk") + "the CSV scores it 0 (491 s), but that trial directory is not in the repository.</p><p class=\"src\">" + tag("rec") + "<code>ws_trials/full_haiku_ws_55/…</code></p></div></div>" +

  '<h2 class="anchor" id="c-limits">What this case can and cannot show</h2><ul class="bounds">' +
    "<li>One pair of runs illustrates a failure mode: a scripted edit loop that never re-reads the cause. It does not show that the skill caused the loop; a single run cannot separate the skill from run-to-run variation.</li>" +
    "<li>The N run is a rerun after a crashed first attempt; the M run timed out and was not rerun. Rerun policy: crashes with zero tokens were rerun, timeouts scored 0.</li>" +
    "<li>All three runs began in a container without matplotlib and spent their first 11–21 steps on dependencies and environment fixes, unrelated to the issue.</li>" +
    "<li>The task image keeps future git history, which let Haiku read the upstream fix. That repair is counted in the paper's Table 3 and Table 6.</li>" +
    '<li>For the population picture see the <a href="#results/r-grid">task grid</a> and <a href="#evidence">evidence &amp; limits</a>; for this category, Table 6 reports +11.1% utility (▲4 ▼1 over three models).</li></ul>';
  $("haikuToggle").addEventListener("change", function (e) { S.haiku = e.target.checked; if (!S.haiku && S.phase && S.phase.indexOf("h_c1") === 0) S.phase = null; save(); renderLanes(); renderPhase(); });
  $("forkPlay").addEventListener("click", forkPlay);
  $("forkRail").addEventListener("click", function (e) { var b = e.target.closest("[data-fk]"); if (!b) return; if (playT) { clearTimeout(playT); playT = null; } S.fork = +b.dataset.fk; save(); renderFork(); });
  $("forkLog").addEventListener("click", function (e) { e.preventDefault(); e.stopPropagation(); S.phase = "g_c1:3"; save(); renderLanes(); renderPhase(); scrollToEl($("phaseDetail")); });
  $("codeTabs").addEventListener("click", function (e) { var b = e.target.closest("[data-code]"); if (!b) return; S.code = b.dataset.code; save(); renderCode(); });
  $("caseBody").addEventListener("click", function (e) { var b = e.target.closest("[data-ph]"); if (!b || b.closest(".mini-lanes")) return; S.phase = S.phase === b.dataset.ph ? null : b.dataset.ph; save(); renderLanes(); renderPhase(); if (S.phase) scrollToEl($("phaseDetail")); });
  renderLanes(); renderPhase(); renderFork(); renderCode(); renderFacts();
}
function renderLanes() { $("lanes").innerHTML = lanes(S.haiku ? ["g_c0", "g_c1", "h_c1"] : ["g_c0", "g_c1"]); }

/* ---------------- boot ---------------- */
applyPrefs(); setTopVar();
renderOverview(); renderT1(); renderCats(); renderCtrl(); renderFilters(); renderGrid(); renderTask();
window.addEventListener("resize", setTopVar);
if (window.ResizeObserver) new ResizeObserver(setTopVar).observe($("topbar"));
window.addEventListener("beforeunload", function () { S.scroll[S.tab] = window.scrollY; save(); });
(function route() {
  var h = (location.hash || "").replace(/^#/, "").split("/");
  if (h[0] && TABS.indexOf(h[0]) >= 0) { setTab(h[0]); if (h[1]) setTimeout(function () { jump(h[0], h.slice(1)); }, 60); }
  else setTab(S.tab || "overview", { restore: true });
})();
window.addEventListener("hashchange", function () { var h = location.hash.replace(/^#/, "").split("/"); if (TABS.indexOf(h[0]) >= 0 && h[0] !== S.tab) setTab(h[0]); if (h[1]) jump(h[0], h.slice(1)); });
window.DEMO = { S: S, go: go, setTab: setTab };
})();
