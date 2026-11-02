/* SkillLens demo diagrams: the five-condition experiment structure with linked contrasts (Method) and the
 * two-route state diagram of the seaborn-2848 runs (Case). Inline SVG for relations, HTML for details.
 * Every count shown on the routes is computed from TRAJ_DATA; nothing is typed in by hand.
 * Loaded before demo.js, which calls SKVIS.method(S, save) and SKVIS.fork(el, S, save).
 */
(function () {
"use strict";
var P = window.PAPER, D = window.CASE_DATA, T = window.TRAJ_DATA;
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
function tag(k, t) { return '<span class="tag ' + k + '">' + (t || { paper: "Paper", rec: "Recorded run", saved: "Saved results", log: "Log summary", post: "Post-paper", ed: "Editor's summary", teach: "Teaching layout", unk: "Not recorded" }[k]) + "</span>"; }
function clean(s) { return String(s || "").replace(/…（省略 (\d+) 行）/g, "… ($1 lines omitted)").replace(/…\[截断\]/g, "… [truncated in the saved log]"); }
function reduce() { return document.documentElement.classList.contains("reduce-motion"); }
function $(id) { return document.getElementById(id); }
function T_(x, y, s, cls, anchor) { return '<text x="' + x + '" y="' + y + '"' + (cls ? ' class="' + cls + '"' : "") + (anchor ? ' text-anchor="' + anchor + '"' : "") + ">" + esc(s) + "</text>"; }
// keyboard: Enter or Space activates any focusable diagram object
function keys(root, fn) { root.addEventListener("keydown", function (e) { if ((e.key === "Enter" || e.key === " ") && e.target.closest("[data-v]")) { e.preventDefault(); fn(e.target.closest("[data-v]")); } }); }

/* ======================= Method: five conditions ======================= */
var ROWS = [
  { k: "N", y: 56, obj: "none", l1: "nothing added", l2: "task only", cov: "8 models" },
  { k: "M", y: 136, obj: "skill", l1: "matched skill", l2: "same category ✓", cov: "8 models" },
  { k: "X", y: 216, obj: "skill", l1: "mismatched skill", l2: "other code category ≠", cov: "3 models" },
  { k: "B", y: 296, obj: "text", l1: "background text", l2: "general domain text", cov: "3 models" },
  { k: "R", y: 392, obj: "route", l1: "", l2: "", cov: "8 models" }
];
var CMP = {
  mn: { a: "M", b: "N", t: "M vs N", q: "Total effect: does adding the matched skill change the pass rate on the same tasks?", chg: "the matched skill is present or absent", res: "r-table1" },
  mx: { a: "M", b: "X", t: "M vs X", q: "Does the matched procedure do better than procedural text written for another category of the same domain?", chg: "which skill is attached: the task's own category or another one", res: "r-ctrl" },
  xb: { a: "X", b: "B", t: "X vs B", q: "Does procedural text do better than general background text from the same domain?", chg: "procedural skill text versus general domain text", res: "r-ctrl" },
  bn: { a: "B", b: "N", t: "B vs N", q: "Does domain background, or simply a longer prompt, change the pass rate on its own?", chg: "background text is present or absent", res: "r-ctrl" }
};
function badge(k, x, y) {
  var c = "var(--" + k.toLowerCase() + ")", s = "";
  // the same marker shapes as the result charts: N hollow circle, M filled circle, X square, B triangle, R diamond
  if (k === "N") s = '<circle cx="' + x + '" cy="' + y + '" r="15" fill="var(--surface)" stroke="' + c + '" stroke-width="2.5"/>';
  if (k === "M") s = '<circle cx="' + x + '" cy="' + y + '" r="15" fill="' + c + '"/>';
  if (k === "X") s = '<rect x="' + (x - 14) + '" y="' + (y - 14) + '" width="28" height="28" rx="3" fill="' + c + '"/>';
  if (k === "B") s = '<path d="M' + x + "," + (y - 17) + " L" + (x + 16) + "," + (y + 12) + " L" + (x - 16) + "," + (y + 12) + 'Z" fill="' + c + '"/>';
  if (k === "R") s = '<path d="M' + x + "," + (y - 17) + " L" + (x + 17) + "," + y + " L" + x + "," + (y + 17) + " L" + (x - 17) + "," + y + 'Z" fill="var(--ink-2)"/>';
  return s + '<text x="' + x + '" y="' + (y + (k === "B" ? 8 : 5)) + '" text-anchor="middle" class="vb-l ' + (k === "N" ? "on-light" : "on-dark") + '">' + k + "</text>";
}
function skillCard(x, y, k, l1, l2) {
  // a skill is a card with a coloured spine labelled "skill"
  return '<g class="vobj"><rect x="' + x + '" y="' + (y - 23) + '" width="210" height="46" rx="6" class="vo-card"/>' +
    '<rect x="' + x + '" y="' + (y - 23) + '" width="40" height="46" rx="6" fill="var(--' + k.toLowerCase() + ')"/><rect x="' + (x + 30) + '" y="' + (y - 23) + '" width="10" height="46" fill="var(--' + k.toLowerCase() + ')"/>' +
    '<text x="' + (x + 20) + '" y="' + (y + 4) + '" text-anchor="middle" class="vo-spine">skill</text>' +
    T_(x + 52, y - 3, l1, "vo-l1") + T_(x + 52, y + 14, l2, "vo-l2") + "</g>";
}
function methodSVG() {
  var s = '<svg class="vsvg" id="vmSvg" viewBox="0 0 1000 452" role="group" aria-labelledby="vmTitle vmDesc"><title id="vmTitle">Five experimental conditions</title>' +
    '<desc id="vmDesc">One task instruction feeds five branches. N adds nothing, M adds the matched skill, X adds a skill from another category, B adds general background text, R lets the model pick a skill or none from ten skill descriptions. All branches go to the same agent run and the same verifier.</desc>' +
    '<defs><marker id="vmArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-3)"/></marker></defs>';
  // shared input, drawn once
  s += '<g class="vshared" data-shared="task"><path class="vo-doc" d="M16,196 h128 l18,18 v54 h-146 z"/><path class="vo-fold" d="M144,196 v18 h18"/>' + T_(30, 224, "Task", "vo-l1") + T_(30, 242, "same instruction", "vo-l2") + T_(30, 258, "57 coding tasks", "vo-l2") +
    '<text x="88" y="186" text-anchor="middle" class="vsame">same in both</text></g>';
  s += '<path d="M162,232 H196" class="ve"/>';
  // branches
  ROWS.forEach(function (r) {
    var y = r.y, g = '<g class="vrow" data-v="row" data-row="' + r.k + '" tabindex="0" role="button" aria-label="Condition ' + r.k + ": " + (r.k === "R" ? "model routes to a skill or none" : r.l1) + '. Show definition, input and coverage.">';
    g += '<rect class="vrow-hit" x="200" y="' + (y - (r.k === "R" ? 50 : 34)) + '" width="380" height="' + (r.k === "R" ? 100 : 68) + '" rx="10"/>';
    g += '<path d="M196,232 C214,232 214,' + y + " 232," + y + '" class="ve"/>' + badge(r.k, 252, y);
    if (r.obj === "none") g += '<g class="vobj"><rect x="290" y="' + (y - 21) + '" width="210" height="42" rx="6" class="vo-empty"/>' + T_(395, y + 5, "nothing added", "vo-l2", "middle") + "</g>";
    if (r.obj === "skill") g += skillCard(290, y, r.k, r.l1, r.l2);
    if (r.obj === "text") g += '<g class="vobj"><rect x="290" y="' + (y - 23) + '" width="210" height="46" rx="6" class="vo-card"/>' +
      [0, 1, 2].map(function (i) { return '<line x1="302" y1="' + (y - 12 + i * 11) + '" x2="' + (i === 2 ? 322 : 330) + '" y2="' + (y - 12 + i * 11) + '" stroke="var(--b)" stroke-width="3" stroke-linecap="round"/>'; }).join("") +
      T_(342, y - 3, r.l1, "vo-l1") + T_(342, y + 14, r.l2, "vo-l2") + "</g>";
    if (r.obj === "route") {
      // R: candidate cards → the model decides → one skill or none
      g += '<g class="vobj">' + [2, 1, 0].map(function (i) { return '<rect x="' + (290 + i * 6) + '" y="' + (y - 30 + i * 6) + '" width="56" height="40" rx="4" class="vo-card"/><rect x="' + (290 + i * 6) + '" y="' + (y - 30 + i * 6) + '" width="12" height="40" rx="3" fill="var(--ink-3)"/>'; }).join("") +
        T_(319, y + 36, "10 skill cards", "vo-l2", "middle") +
        '<path d="M360,' + (y - 6) + ' H378" class="ve" marker-end="url(#vmArr)"/>' +
        '<path d="M410,' + (y - 32) + " L438," + (y - 6) + " L410," + (y + 20) + " L382," + (y - 6) + 'Z" class="vo-dia"/>' + T_(410, y - 2, "model", "vo-l2", "middle") + T_(410, y + 9, "picks", "vo-l2", "middle") +
        '<path d="M438,' + (y - 6) + " C450," + (y - 6) + " 450," + (y - 22) + " 462," + (y - 22) + '" class="ve" marker-end="url(#vmArr)"/>' + T_(446, y - 40, "one skill", "vel", "middle") +
        '<rect x="464" y="' + (y - 36) + '" width="66" height="28" rx="4" class="vo-card"/><rect x="464" y="' + (y - 36) + '" width="10" height="28" rx="3" fill="var(--ink-2)"/>' + T_(500, y - 18, "chosen", "vo-l2", "middle") +
        '<path d="M410,' + (y + 20) + " V" + (y + 32) + ' H530" class="ve dashed"/>' + T_(478, y + 46, "none: task only", "vel", "middle") + "</g>";
    }
    g += T_(252, y + (r.k === "R" ? 34 : 32), r.cov, "vcov", "middle");
    // into the shared agent run
    var y0 = r.k === "R" ? y - 22 : y, x0 = r.k === "R" ? 530 : 500;
    g += '<path d="M' + x0 + "," + y0 + " C" + (x0 + 50) + "," + y0 + " 560,232 606,232" + '" class="ve to-run"/>' + (r.k === "R" ? '<path d="M530,' + (y + 32) + " C580," + (y + 32) + ' 570,232 606,232" class="ve dashed to-run"/>' : "");
    g += '<text class="vdelta" x="279" y="' + (y + 6) + '" text-anchor="middle">Δ</text></g>';
    s += g;
  });
  // shared run and verifier, drawn once
  s += '<g class="vshared" data-shared="run"><rect x="610" y="198" width="160" height="68" rx="10" class="vo-run"/>' + T_(690, 228, "Agent run", "vo-l1", "middle") + T_(690, 246, "mini-swe-agent · Docker", "vo-l2", "middle") +
    '<text x="690" y="188" text-anchor="middle" class="vsame">same in both</text></g>';
  s += '<path d="M770,232 H808" class="ve" marker-end="url(#vmArr)"/>' + T_(789, 222, "repo", "vel", "middle");
  s += '<g class="vshared" data-shared="ver"><rect x="812" y="198" width="172" height="68" rx="10" class="vo-ver"/>' + T_(898, 226, "Verifier", "vo-l1", "middle") + T_(898, 244, "task tests → y ∈ {0, 1}", "vo-l2", "middle") + T_(898, 284, "no LLM judge", "vo-l2", "middle") +
    '<text x="898" y="188" text-anchor="middle" class="vsame">same in both</text></g>';
  s += '<path d="M606,232 H610" class="ve" marker-end="url(#vmArr)"/>';
  return s + "</svg>";
}
// what each branch shows when opened
function rowDetail(k) {
  var issue = T.task.issue.split("\n").slice(0, 5).join("\n"), skill = T.skill.text.split("\n").slice(0, 14).join("\n");
  var picks = { c: 0, w: 0, n: 0, u: 0 }, dm = P.MODELS.filter(function (m) { return m.data; });
  dm.forEach(function (m) { D.res[m.data].sel.forEach(function (v) { picks[v]++; }); });
  var total = picks.c + picks.w + picks.n + picks.u;
  var H = {
    N: ["N · task only", "The agent receives the task instruction and nothing else.",
      '<p class="small">' + tag("rec") + "Example task text (seaborn-2848, first lines of the issue):</p><pre class=\"vx\">" + esc(issue) + "</pre>",
      "All 8 models in Table 1 (column “Base”); per-task results saved for 7.", "§3.3 L336–337; Table 1"],
    M: ["M · task + matched skill", "The expert-written skill for the task's own category is inserted into the instruction; the task text is unchanged.",
      '<p class="small">' + tag("rec") + "Real inserted text for seaborn-2848: <code>" + esc(T.skill.name) + "</code> v" + esc(T.skill.version) + ", " + T.skill.chars.toLocaleString("en-US") + " characters, at character " + T.skill.insert_at + " of the prompt. First lines:</p><pre class=\"vx\">" + esc(skill) + "</pre>",
      "All 8 models in Table 1; per-task results saved for 7.", "§3.3 L336–337; §4.3 L514–528; Table 1; trajectory prompt of the M run"],
    X: ["X · task + mismatched skill", "A skill written for another category of the same (coding) domain is attached instead of the matched one.",
      '<div class="vph"><span class="vph-t">task instruction</span><span class="vph-s">+ skill from another code category</span></div><p class="small">' + tag("unk") + "The X inputs for coding tasks are not saved in the repositories this demo reads, so no text is shown. The boxes are a structural sketch, not an input.</p>",
      "Claude Haiku 4.5, Gemma-4-26B and Qwen3-8B only (Table 2). The paper counts 792 scheduled X/B trials for code and chemistry together.", "§3.3 L336–349; §5.2 L565–567; Table 2"],
    B: ["B · task + background text", "General same-domain background text is attached, without a procedure for the task category.",
      '<div class="vph"><span class="vph-t">task instruction</span><span class="vph-s b">+ general domain text</span></div><p class="small">' + tag("unk") + "The B inputs for coding tasks are not saved in the repositories this demo reads, so no text is shown. The boxes are a structural sketch, not an input.</p>",
      "Claude Haiku 4.5, Gemma-4-26B and Qwen3-8B only (Table 2).", "§3.3 L336–349; §5.2 L565–567; Table 2"],
    R: ["R · model routes", "The model sees the names and descriptions of the domain's skills and picks one to load, or none. A wrong pick is scored by the run with the skill it picked; router correctness is reported separately.",
      '<p class="small">' + tag("saved") + "Router input for seaborn-2848: " + D.routing.skills.length + " skill cards (name + description), e.g.</p><pre class=\"vx\">" + esc(D.routing.skills.slice(0, 2).map(function (x) { return x.name + ": " + x.description; }).join("\n\n")) + "</pre>" +
      '<p class="small">' + tag("saved") + "Picks over 57 tasks × 7 models (" + total + "): matched skill " + picks.c + " · another skill " + picks.w + " · none " + picks.n + " · not recorded " + picks.u + ".</p>",
      "All 8 models in Table 1 (column “Routed”); per-task picks saved for 7.", "§3.4 L363–379; §5.1 L554–555; Table 1; routed results file"]
  }[k];
  return '<div class="vdet-h"><h3>' + esc(H[0]) + '</h3><button type="button" class="btn small" data-vclose>Close</button></div><p>' + tag("paper") + esc(H[1]) + "</p>" + H[2] +
    '<p class="small"><b>Coverage.</b> ' + esc(H[3]) + '</p><p class="src">' + tag("paper") + esc(H[4]) + (k === "X" || k === "B" || k === "R" ? " · " + tag("unk") + "The SkillLens-clean runner accepts only c0/c1 (no skill / one skill); which script ran X, B and R is not recorded here." : "") + "</p>";
}
function cmpBox(id) {
  if (!id) return '<p class="small muted">Pick a contrast to see which two branches it compares and what differs between them.</p>';
  var c = CMP[id], vals = "";
  if (id === "mn") {
    var up = P.MODELS.filter(function (m) { return m.M[1] > m.B[1]; }).length, flat = P.MODELS.filter(function (m) { return m.M[1] === m.B[1]; }).length;
    vals = "Table 1, 57 tasks per model: M above N for " + up + " of 8 models, equal for " + flat + ", below for " + (8 - up - flat) + ".";
  } else vals = "Table 2, 57 tasks per model: " + P.CTRL.map(function (r) { var d = (r[c.a][1] - r[c.b][1]) / 57 * 100; return r.name.replace("Claude ", "") + " " + (d > 0 ? "+" : d < 0 ? "−" : "±") + Math.abs(d).toFixed(1); }).join(" · ") + " points.";
  return '<p class="vq"><b>' + esc(c.t) + "</b> " + esc(c.q) + '</p><p class="small"><b>Same:</b> task, agent, limits and verifier. <b>Differs:</b> ' + esc(c.chg) + ".</p>" +
    '<p class="small">' + tag("paper") + esc(vals) + ' <a href="#results/' + c.res + '" data-back="Method · ' + esc(c.t) + '">See the results →</a></p>' +
    '<p class="small muted">A difference in pass rate between two conditions on the same tasks; it does not show how the added text acted.</p>';
}
function method(S, save) {
  var host = $("vMethod"); if (!host) return;
  host.innerHTML = '<div class="vcmp" role="group" aria-label="Compare two conditions"><span class="small muted">Compare</span>' +
    Object.keys(CMP).map(function (k) { return '<button type="button" data-cmp="' + k + '" aria-pressed="false">' + CMP[k].t + "</button>"; }).join("") + '<button type="button" data-cmp="" class="vclear">Clear</button></div>' +
    '<div class="vcmp-box" id="vmCmp" aria-live="polite"></div>' +
    '<p class="vhint">The diagram scrolls sideways inside its box.</p><div class="vscroll" id="vmScroll"><div class="vfig">' + methodSVG() + "</div></div>" +
    '<p class="vlegend small"><span><i class="lg-skill"></i>skill card</span><span><i class="lg-text"></i>background text</span><span><i class="lg-dia"></i>model decision</span><span><i class="lg-empty"></i>nothing added</span><span>Δ part that differs in a contrast</span><span>' + tag("teach") + "layout; definitions from the paper</span></p>" +
    '<div class="vdet" id="vmDet" aria-live="polite"></div>';
  function sync() {
    var c = S.vcmp ? CMP[S.vcmp] : null, svg = $("vmSvg");
    svg.classList.toggle("cmp", !!c);
    svg.querySelectorAll(".vrow").forEach(function (g) {
      var k = g.dataset.row, inC = c && (k === c.a || k === c.b);
      g.classList.toggle("on", !!inC); g.classList.toggle("off", !!c && !inC); g.classList.toggle("sel", S.vrow === k);
      g.setAttribute("aria-pressed", S.vrow === k ? "true" : "false");
    });
    host.querySelectorAll("[data-cmp]").forEach(function (b) { var on = (b.dataset.cmp || null) === (S.vcmp || null) && !!b.dataset.cmp; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on ? "true" : "false"); });
    $("vmCmp").innerHTML = cmpBox(S.vcmp);
    $("vmDet").innerHTML = S.vrow ? '<div class="card">' + rowDetail(S.vrow) + "</div>" : '<p class="small muted">Select a branch to see its definition, a real input excerpt where one is saved, and which models ran it.</p>';
  }
  host.addEventListener("click", function (e) {
    var b = e.target.closest("[data-cmp]"); if (b) { S.vcmp = b.dataset.cmp || null; save(); sync(); return; }
    var r = e.target.closest(".vrow"); if (r) { S.vrow = S.vrow === r.dataset.row ? null : r.dataset.row; save(); sync(); return; }
    if (e.target.closest("[data-vclose]")) { S.vrow = null; save(); sync(); }
  });
  keys(host, function (el) { S.vrow = S.vrow === el.dataset.row ? null : el.dataset.row; save(); sync(); });
  sync();
}

/* ======================= Case: two routes through seaborn-2848 ======================= */
function run(k) { return T.runs.filter(function (r) { return r.key === k; })[0]; }
function step(k, id) { return run(k).steps.filter(function (s) { return s.id === id; })[0]; }
// counts for the M patch loop, read from the saved trajectory
function loopStats() {
  var r = run("g_c1"), out = { runs: 0, IndentationError: 0, SyntaxError: 0, TypeError: 0, other: 0, ok: 0, restores: [], writes: 0, last: r.steps[r.steps.length - 1].id, ie: [] };
  r.steps.forEach(function (s) {
    if (s.id < 24) return;
    var lastLine = s.cmd.trim().split("\n").pop();
    if (/python3? reproduce_issue\.py\s*$/.test(lastLine)) {
      out.runs++;
      if (s.out.indexOf("IndentationError") >= 0) { out.IndentationError++; out.ie.push(s.id); }
      else if (/SyntaxError/.test(s.out)) out.SyntaxError++;
      else if (/TypeError/.test(s.out)) out.TypeError++;
      else if (/Successfully ran/.test(s.out)) out.ok++;
      else out.other++;
    }
    if (s.out.indexOf("Updated 1 path from the index") >= 0) out.restores.push(s.id);
    if (s.out.indexOf("Successfully replaced the block.") >= 0) out.writes++;
  });
  return out;
}
var COLX = function (i) { return 150 + i * 126; }, NY = 78, MY = 280, W = 118, H = 50;
// [id, lane, column, kind, line 1, line 2, step ids, stage]
function nodes(L) {
  return [
    ["n0", "n", 0, "err", "✕ TypeError", "isnan · step 24", [24], 0],
    ["n1", "n", 1, "write", "✎ edit line 157", "sed · step 26", [26], 1],
    ["n2", "n", 2, "err", "✕ TypeError", "NoneType · step 27", [27], 1],
    ["n3", "n", 3, "write", "✎ script replaces", "function · step 30", [30], 1],
    ["n4", "n", 4, "err", "✕ IndentationError", "step 31", [31], 2],
    ["n5", "n", 5, "read", "read lines", "140–175 · step 32", [32], 3],
    ["n6", "n", 6, "write", "✎ rewrite whole", "function · step 33", [33], 4],
    ["n7", "n", 7, "ok", "✓ pairplot runs", "steps 34–35", [34, 35], 5],
    ["n8", "n", 8, "end-ok", "✓ submitted", "step 36 · reward 1", [36], 5],
    ["m0", "m", 0, "err", "✕ TypeError", "isnan · step 15", [15], 0],
    ["m1", "m", 1, "read", "read code,", "edit repro · 16–23", [16, 21, 23], 1],
    ["m3", "m", 3, "write", "✎ script replaces", "block · step 24", [24], 1],
    ["m4", "m", 4, "err", "✕ IndentationError", L.IndentationError + " of " + L.runs + " test runs", [L.ie[0], L.ie[L.ie.length - 1]], 2],
    ["m5", "m", 5, "read", "read the file", "after a failed run", [26], 3],
    ["mr", "m", "r", "restore", "↺ restore file", L.restores.length + "× · from step " + L.restores[0], [L.restores[0], 346], 4],
    ["m8", "m", 8, "end-bad", "✕ 5,400 s limit", "nothing submitted", [L.last], 5]
  ];
}
var DOCS = [["dn1", "n", 1, "line 157 guarded", 1], ["dn3", "n", 3, "two def lines", 1], ["dn6", "n", 6, "function rewritten", 4], ["dm3", "m", 3, "block replaced", 1], ["dmr", "m", "r", "original file", 4]];
function pos(n) { var x = n[2] === "r" ? COLX(4) : COLX(n[2]), y = n[1] === "n" ? NY : n[2] === "r" ? MY + 118 : MY; return { x: x, y: y }; }
function nodeSVG(n) {
  var p = pos(n), x = p.x - W / 2, y = p.y - H / 2, k = n[3], shape;
  if (k === "end-ok" || k === "end-bad") shape = '<rect x="' + x + '" y="' + y + '" width="' + W + '" height="' + H + '" rx="25" class="vn-end ' + k + '"/><rect x="' + (x + 4) + '" y="' + (y + 4) + '" width="' + (W - 8) + '" height="' + (H - 8) + '" rx="21" class="vn-end2 ' + k + '"/>';
  else shape = '<rect x="' + x + '" y="' + y + '" width="' + W + '" height="' + H + '" rx="' + (k === "read" ? 4 : 8) + '" class="vn-box ' + k + '"/>' + (k === "err" || k === "ok" ? '<rect x="' + x + '" y="' + y + '" width="6" height="' + H + '" rx="3" class="vn-bar ' + k + '"/>' : "");
  return '<g class="vnode" data-v="node" data-id="' + n[0] + '" data-stage="' + n[7] + '" tabindex="0" role="button" aria-label="' + esc((n[1] === "n" ? "N run: " : "M run: ") + n[4].replace("✕ ", "error ").replace("✓ ", "").replace("✎ ", "").replace("↺ ", "") + " " + n[5] + ". Open the recorded step.") + '">' + shape +
    '<text x="' + (p.x + 2) + '" y="' + (p.y - 3) + '" text-anchor="middle" class="vn-l1">' + esc(n[4]) + '</text><text x="' + (p.x + 2) + '" y="' + (p.y + 14) + '" text-anchor="middle" class="vn-l2">' + esc(n[5]) + "</text></g>";
}
function docSVG(d) {
  // N file states sit under their write; M's "block replaced" sits above its write, "original file" between the lane and the restore node
  var w = 100, h = 34, x = (d[2] === "r" ? COLX(4) : COLX(d[2])) - w / 2, y, a, b;
  if (d[1] === "n") { y = NY + 58; a = NY + H / 2; b = y; }
  else if (d[2] === "r") { y = MY + 42; a = MY + 118 - H / 2; b = y + h; }
  else { y = MY - H / 2 - 11 - h; a = MY - H / 2; b = y + h; }
  var cx = x + w / 2;
  return '<g class="vdoc" data-stage="' + d[4] + '"><path d="M' + cx + "," + a + " L" + cx + "," + b + '" class="ve writes"/>' +
    '<path d="M' + x + "," + y + " h" + (w - 12) + " l12,12 v" + (h - 12) + " h-" + w + ' z" class="vo-file"/><path d="M' + (x + w - 12) + "," + y + " v12 h12" + '" class="vo-fold"/>' +
    '<text x="' + (x + 8) + '" y="' + (y + 14) + '" class="vd-k">file</text><text x="' + (x + 8) + '" y="' + (y + 27) + '" class="vd-l">' + esc(d[3]) + "</text></g>";
}
function edge(a, b, stage, cls, lab, lx, ly) {
  return '<g class="vedge" data-stage="' + stage + '"><path d="M' + a.x + "," + a.y + " L" + b.x + "," + b.y + '" class="ve ' + (cls || "") + '" marker-end="url(#vfArr)"/>' + (lab ? T_(lx, ly, lab, "vel", "middle") : "") + "</g>";
}
function forkSVG(L) {
  var N = nodes(L), by = {}; N.forEach(function (n) { by[n[0]] = n; });
  function R(id) { var p = pos(by[id]); return { x: p.x + W / 2, y: p.y }; }
  function Lf(id) { var p = pos(by[id]); return { x: p.x - W / 2 - 2, y: p.y }; }
  var s = '<svg class="vsvg vfork" id="vfSvg" viewBox="0 0 1240 452" role="group" aria-labelledby="vfTitle vfDesc"><title id="vfTitle">Two recorded runs of seaborn-2848</title>' +
    '<desc id="vfDesc">Top lane: Gemma-4-26B without the skill reproduces the error, edits, hits an IndentationError, reads the file, rewrites the whole function, runs successfully and submits. Bottom lane: with the skill it reproduces the error, replaces a block, hits an IndentationError, reads the file, restores it and replaces the block again in a loop until the 5,400-second limit.</desc>' +
    '<defs><marker id="vfArr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink-3)"/></marker>' +
    '<marker id="vfArrL" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--bad)"/></marker></defs>';
  // lanes
  s += '<rect x="4" y="20" width="1232" height="170" rx="12" class="vlane n"/><rect x="4" y="200" width="1232" height="248" rx="12" class="vlane m"/>';
  s += '<circle cx="40" cy="' + NY + '" r="16" fill="var(--surface)" stroke="var(--n)" stroke-width="2.5"/>' + T_(40, NY + 5, "N", "vb-l on-light", "middle") + T_(40, NY + 34, "no skill", "vo-l2", "middle");
  s += '<circle cx="40" cy="' + MY + '" r="16" fill="var(--m)"/>' + T_(40, MY + 5, "M", "vb-l on-dark", "middle") + T_(40, MY + 34, "+ skill", "vo-l2", "middle");
  // the shared stretch: both routes hit an IndentationError right after a scripted edit, then read the file
  s += '<g class="vspan" data-stage="2"><path d="M' + (COLX(3) - 58) + ',12 H' + (COLX(5) + 58) + '" class="vbracket"/>' + T_((COLX(3) + COLX(5)) / 2, 10, "both runs: scripted edit → IndentationError → read the file", "vspan-l", "middle") + "</g>";
  // N lane edges
  ["n0", "n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8"].reduce(function (a, b) { s += edge(R(a), Lf(b), by[b][7]); return b; });
  // M lane edges
  s += edge(R("m0"), Lf("m1"), 1) + edge(R("m1"), Lf("m3"), 1) + edge(R("m3"), Lf("m4"), 2) + edge(R("m4"), Lf("m5"), 3);
  // the loop back-edge: read → restore → patch again
  var m5 = pos(by.m5), mr = pos(by.mr), m3 = pos(by.m3);
  s += '<g class="vedge loop" data-stage="4"><path d="M' + m5.x + "," + (m5.y + H / 2) + " V" + mr.y + " H" + (mr.x + W / 2 + 2) + '" class="ve back" marker-end="url(#vfArrL)"/>' +
    '<path d="M' + (mr.x - W / 2) + "," + mr.y + " H" + m3.x + " V" + (m3.y + H / 2 + 2) + '" class="ve back" marker-end="url(#vfArrL)"/>' +
    T_(m3.x + 6, mr.y + 36, "loop back-edge · " + L.runs + " test runs after the first patch", "vel loop-l", "start") + "</g>";
  // M exit: time runs out
  s += edge({ x: m5.x + W / 2, y: m5.y }, Lf("m8"), 5, "exit", "after step " + L.last + ": time limit", (m5.x + pos(by.m8).x) / 2, m5.y - 10);
  DOCS.forEach(function (d) { s += docSVG(d); });
  N.forEach(function (n) { s += nodeSVG(n); });
  return s + "</svg>";
}
var STAGES = [
  ["Same start", function () { return ["N step 24: TypeError: ufunc 'isnan' not supported — the issue reproduced.", "M step 15: the same TypeError, nine steps earlier."]; }],
  ["First edits", function () { return ["N: guards line 157 with sed (26), meets a new TypeError 'NoneType' object is not callable (27), then a Python script replaces the function (30).", "M: reads lines 140–170 and rewrites its reproduction script (16–23), then a Python script replaces the block (24)."]; }],
  ["IndentationError", function () { return ["N step 31: IndentationError: expected an indented block after function definition on line 146.", "M step 25: IndentationError: expected an indented block after 'except' statement on line 156."]; }],
  ["Read the file", function () { return ["N step 32: cat -n lines 140–175 of seaborn/_oldcore.py.", "M step 26: cat -n lines 150–170 of the same file."]; }],
  ["The routes split", function (L) { return ["N step 33: names the cause (“two def _lookup_single”) and rewrites the whole function once.", "M: restores the file (git checkout, output “Updated 1 path from the index”) and writes a new block; from step " + L.restores[0] + " on, restore and re-patch happen in one step."]; }],
  ["Outcome", function (L) { return ["N: pairplot runs (34), extra cases pass (35), submitted at step 36; verifier reward 1 (a rerun).", "M: " + L.runs + " test runs after the first patch — " + L.IndentationError + " IndentationError, " + L.SyntaxError + " SyntaxError, " + L.TypeError + " TypeError, " + L.ok + " successes — until the 5,400 s limit; nothing submitted, reward 0."]; }]
];
// code with indentation guides; hl = 0-based line indexes to mark
function codeGuides(lines, hl, note) {
  return '<pre class="vcode">' + lines.map(function (l, i) {
    var m = l.match(/^ */)[0].length, g = "";
    for (var d = 0; d < m; d += 4) g += '<span class="ig">' + "    ".slice(0, Math.min(4, m - d)) + "</span>";
    return '<span class="cl' + (hl && hl.indexOf(i) >= 0 ? " hl" : "") + '">' + g + esc(l.slice(m)) + (hl && hl.indexOf(i) >= 0 && note ? '<span class="cl-n">← ' + esc(note) + "</span>" : "") + "</span>";
  }).join("") + "</pre>";
}
function outHtml(s) { return clean(s).split("\n").map(function (l) { return /Error[:\s]|^\s*\^\s*$/.test(l) ? '<mark>' + esc(l) + "</mark>" : esc(l); }).join("\n"); }
function stepBox(k, id) {
  var s = step(k, id); if (!s) return "";
  return '<div class="vstep"><div class="vstep-h"><b>step ' + s.id + '</b><span class="rc ' + (s.rc === 0 ? "ok" : s.rc === -1 ? "na" : "bad") + '">exit ' + s.rc + "</span></div>" +
    "<details" + (/IndentationError|Successfully ran/.test(s.out) ? "" : " open") + "><summary>command</summary><pre class=\"vx\">$ " + esc(clean(s.cmd)) + "</pre></details>" + (s.out ? '<pre class="vx out">' + outHtml(s.out) + "</pre>" : "") + "</div>";
}
function nodeDetail(id, L) {
  var N = nodes(L), n = N.filter(function (x) { return x[0] === id; })[0], k = n[1] === "n" ? "g_c0" : "g_c1", lane = n[1] === "n" ? "Gemma-4-26B · N" : "Gemma-4-26B · M";
  var head = '<div class="vdet-h"><h3>' + esc(lane) + " · " + esc(n[4].replace(/^[✕✓✎↺] /, "") + " " + n[5]) + '</h3><button type="button" class="btn small" data-vclose>Close</button></div>';
  var extra = "";
  if (id === "n6") extra = '<p class="small">' + tag("rec") + "The function as written at step 33 (rebuilt from the command text):</p>" + codeGuides(D.n_fn, [9, 10, 13], "") + '<p class="small muted">Highlighted: the new norm-is-None branch.</p>';
  if (id === "n3") extra = '<p class="small">' + tag("rec") + "The agent's own reading at step 33: “The indentation error is because I added two def _lookup_single(self, key): and line 147 is also def _lookup_single(self, key):”.</p>";
  if (id === "m3" || id === "m4") {
    var file = ["            try:", "                normed = self.norm(key)", "            except TypeError as err:", "                if np.isnan(key):"];
    extra = '<div class="vside"><div><p class="small"><b>Lines 154–157 before the patch</b><br>' + tag("rec") + "line text matched by the step-24 script; indentation of 154–155 printed at step 21 " + tag("ed", "Editor's summary") + "156–157 indented by Python block rules</p>" + codeGuides(file, [2], "line 156") + "</div>" +
      '<div><p class="small"><b>First lines the script writes (step 24)</b><br>' + tag("rec") + "from the command text</p>" + codeGuides(D.m_blk.slice(0, 6), [0], "same depth as except") + "</div></div>" +
      '<p class="small">' + tag("ed") + "Reading: the new block starts at the depth of <code>except</code>, so the except clause has no body, which matches the message “expected an indented block after 'except' statement on line 156”.</p>";
  }
  if (id === "m4") extra += '<table class="vtab"><tr><th>Test runs after the first patch</th><td>' + L.runs + "</td></tr><tr><th>IndentationError</th><td>" + L.IndentationError + "</td></tr><tr><th>SyntaxError</th><td>" + L.SyntaxError + "</td></tr><tr><th>TypeError</th><td>" + L.TypeError + "</td></tr><tr><th>Successful runs</th><td>" + L.ok + "</td></tr></table><p class=\"small muted\">Errors are counted per test-run output; one loop pass is restore/patch → run → read, and several passes can share a step.</p>";
  if (id === "mr") extra = '<table class="vtab"><tr><th>Outputs “Updated 1 path from the index”</th><td>' + L.restores.length + " (first at step " + L.restores[0] + ")</td></tr><tr><th>Outputs “Successfully replaced the block.”</th><td>" + L.writes + '</td></tr></table><p class="small">' + tag("rec") + "Most saved commands are cut off before the restore command; the restore is identified by git's output. Step 346 shows the command in full: <code>git checkout seaborn/_oldcore.py</code> followed by the patch script.</p>";
  if (id === "m8") extra = '<p class="small">' + tag("rec") + "AgentTimeoutError at 5,400 s (wall clock 5,443 s in the results CSV). The source is left with an IndentationError, so test collection fails: the FAIL_TO_PASS test fails and 0 of 50 PASS_TO_PASS tests pass; reward 0, not rerun.</p>";
  if (id === "n8") extra = '<p class="small">' + tag("rec") + "Verifier reward 1.0. This N run is a rerun after a first attempt that crashed with zero tokens; the rerun's test-level output was not saved.</p>";
  var steps = n[6].filter(function (x, i, a) { return x != null && a.indexOf(x) === i; }).slice(0, 3);
  return head + extra + '<p class="small">' + tag("rec") + "Recorded command and output (condensed log):</p>" + steps.map(function (sid) { return stepBox(k, sid); }).join("") +
    '<p class="src">' + tag("rec") + "trajectory of the " + (n[1] === "n" ? "N" : "M") + " run · " + tag("ed") + "node grouping and labels</p>";
}
var playT = null;
function fork(host, S, save) {
  var L = loopStats();
  host.innerHTML = '<div class="vctl"><button type="button" class="btn primary" id="vfPlay"></button><span class="vrail" id="vfRail" role="group" aria-label="Replay stage">' +
    STAGES.map(function (st, i) { return '<button type="button" data-st="' + i + '">' + (i + 1) + " " + st[0] + "</button>"; }).join("") + '<button type="button" data-st="all">All</button></span></div>' +
    '<p class="vhint">The diagram scrolls sideways inside its box; replay keeps the current stage in view.</p><div class="vscroll" id="vfScroll"><div class="vfig wide">' + forkSVG(L) + "</div></div>" +
    '<p class="vlegend small"><span><i class="lg-w"></i>write action ✎</span><span><i class="lg-r"></i>read action</span><span><i class="lg-e"></i>run result ✕ / ✓</span><span><i class="lg-f"></i>file state</span><span><i class="lg-back"></i>loop back-edge</span><span><i class="lg-end"></i>end of run</span></p>' +
    '<div class="vcap" id="vfCap" aria-live="polite"></div><div class="vdet" id="vfDet" aria-live="polite"></div>';
  var svg = $("vfSvg");
  function sync() {
    var st = S.vf == null ? null : S.vf;
    svg.classList.toggle("staged", st != null);
    svg.querySelectorAll("[data-stage]").forEach(function (g) { var s2 = +g.dataset.stage; g.classList.toggle("cur", st != null && s2 === st); g.classList.toggle("later", st != null && s2 > st); });
    svg.querySelectorAll(".vnode").forEach(function (g) { g.classList.toggle("sel", S.vfn === g.dataset.id); g.setAttribute("aria-pressed", S.vfn === g.dataset.id ? "true" : "false"); });
    host.querySelectorAll("#vfRail button").forEach(function (b) { var on = b.dataset.st === "all" ? st == null : +b.dataset.st === st; b.classList.toggle("on", on); b.setAttribute("aria-pressed", on ? "true" : "false"); });
    $("vfPlay").textContent = playT ? "❚❚ Pause" : st != null && st < STAGES.length - 1 ? "▶ Continue" : st === STAGES.length - 1 ? "↺ Replay" : "▶ Replay the two routes";
    var cap = st == null ? ["Both runs hit an IndentationError after a scripted edit and then read the file. N rewrites the function once and submits; M restores the file and re-patches in a loop until the time limit.", ""] : STAGES[st][1](L);
    $("vfCap").innerHTML = st == null ? '<p class="vq">' + esc(cap[0]) + "</p>" : '<p class="vq"><b>' + (st + 1) + " · " + esc(STAGES[st][0]) + '</b></p><p class="vcl n"><span>N</span>' + esc(cap[0]) + '</p><p class="vcl m"><span>M</span>' + esc(cap[1]) + "</p>";
    $("vfDet").innerHTML = S.vfn ? '<div class="card">' + nodeDetail(S.vfn, L) + "</div>" : '<p class="small muted">Select a node to open its recorded command, output and code.</p>';
    // narrow screens: keep the current stage in view inside the scroll box
    var sc = $("vfScroll");
    if (st != null && sc.scrollWidth > sc.clientWidth + 4) {
      var cur = svg.querySelectorAll(".vnode.cur"), xs = []; cur.forEach(function (g) { var b = g.getBoundingClientRect(), r = sc.getBoundingClientRect(); xs.push(b.left - r.left + sc.scrollLeft + b.width / 2); });
      if (xs.length) sc.scrollTo({ left: Math.max(0, (Math.min.apply(null, xs) + Math.max.apply(null, xs)) / 2 - sc.clientWidth / 2), behavior: reduce() ? "auto" : "smooth" });
    }
  }
  function stop() { if (playT) clearTimeout(playT); playT = null; }
  function tick() { if (S.vf >= STAGES.length - 1) { playT = null; sync(); return; } S.vf++; save(); sync(); playT = setTimeout(tick, 2200); }
  $("vfPlay").addEventListener("click", function () {
    if (playT) { stop(); sync(); return; }
    // reduced motion: no timed stepping; show the complete static diagram
    if (reduce()) { S.vf = null; save(); sync(); return; }
    if (S.vf == null || S.vf >= STAGES.length - 1) S.vf = 0;
    save(); sync(); playT = setTimeout(tick, 2200); sync();
  });
  host.addEventListener("click", function (e) {
    var b = e.target.closest("#vfRail [data-st]"); if (b) { stop(); S.vf = b.dataset.st === "all" ? null : +b.dataset.st; save(); sync(); return; }
    var n = e.target.closest(".vnode"); if (n) { S.vfn = S.vfn === n.dataset.id ? null : n.dataset.id; save(); sync(); if (S.vfn) { var d = $("vfDet"), r = d.getBoundingClientRect(); if (r.top > window.innerHeight - 80) window.scrollBy({ top: Math.min(r.top - window.innerHeight + 260, r.top - 120), behavior: reduce() ? "auto" : "smooth" }); } return; }
    if (e.target.closest("[data-vclose]")) { S.vfn = null; save(); sync(); }
  });
  keys(host, function (el) { if (el.classList.contains("vnode")) { S.vfn = S.vfn === el.dataset.id ? null : el.dataset.id; save(); sync(); } });
  sync();
  return { stats: L };
}
window.SKVIS = { method: method, fork: fork, loopStats: loopStats, state: function () { return { playing: !!playT }; } };
})();
