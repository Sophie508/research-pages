/* Results section of the demo: Table 1 as a dot chart (one benchmark × one metric at a time), the full table,
 * Findings 1–2, Table 2 and Figure 1a. Every value is transcribed from the WWW '27 submission (data-paper.js);
 * provenance notes from the experiment ledger are labelled as such.
 */
(function () {
"use strict";
var D = window.D, esc = D.esc, tag = D.tag, P = window.PAPER, S = D.S;
var body = document.getElementById("resBody");
if (!body || !P) return;
S.res = S.res || { bench: "agenttrap", metric: "asr" };
var BEN = {
  agenttrap: { name: "AgentTrap", n: { asr: "91 attacks", upr: "50 benign tasks", tok: "all tasks of the run" }, col: { asr: 3, upr: 4, tok: 5 },
    def: { asr: "Share of the 91 attack tasks that the benchmark judges L2 (attack succeeded).", upr: "Share of the 50 benign tasks an LLM judge rates as completed.", tok: "Recorded input and output tokens of the selected runs, in millions." } },
  dtap: { name: "DTAP-150", n: { asr: "100 attacks (50 direct, 50 indirect)", upr: "50 benign tasks", tok: "all tasks of the run" }, col: { asr: 0, upr: 1, tok: 2 },
    def: { asr: "Share of the 100 attack tasks DTAP’s own judge rates as successful.", upr: "Share of the 50 benign tasks DTAP’s own judge rates as completed.", tok: "Recorded input and output tokens of the selected runs, in millions." } }
};
var MET = { asr: { name: "ASR", dir: "lower is better", unit: "%", max: 30 }, upr: { name: "UPR", dir: "higher is better", unit: "%", max: 100 }, tok: { name: "Tokens", dir: "lower is better", unit: "M", max: 100 } };
// identity by marker shape, not colour: AIRGuard is the only filled accent marker
var MARK = { "No defense": "○", ARGUS: "◆", MELON: "▲", CaMeL: "■", VIGIL: "✕", AIRGuard: "●" };
function fmt(v, m) { return m === "tok" ? v.toFixed(1) + "M" : v.toFixed(1) + "%"; }

function chart() {
  var b = BEN[S.res.bench], m = S.res.metric, M = MET[m], col = b.col[m], sel = S.res.model;
  var rows = P.MODELS.map(function (model) {
    var vals = P.DEFS.map(function (d) { return [d, P.cell(model, d, col)]; });
    var a = P.cell(model, "No defense", col), g = P.cell(model, "AIRGuard", col);
    var better = m === "upr" ? g > a : g < a, lo = Math.min(a, g), hi = Math.max(a, g), pct = function (v) { return Math.min(100, v / M.max * 100).toFixed(2) + "%"; };
    return '<button type="button" class="dc-row' + (sel === model ? " on" : "") + '" data-model="' + esc(model) + '" aria-pressed="' + (sel === model) + '"><span class="dc-m">' + esc(model) + '</span><span class="dc-track">' +
      '<i class="dc-line ' + (a === g ? "same" : better ? "good" : "worse") + '" style="left:' + pct(lo) + ";width:calc(" + pct(hi) + " - " + pct(lo) + ')"></i>' +
      vals.map(function (x) { return '<i class="dc-mk mk-' + x[0].replace(/\s/g, "").toLowerCase() + '" style="left:' + pct(x[1]) + '" title="' + esc(model + " · " + x[0] + ": " + fmt(x[1], m)) + '">' + MARK[x[0]] + "</i>"; }).join("") +
      '</span><span class="dc-v">' + fmt(a, m) + " → <b>" + fmt(g, m) + "</b></span></button>";
  }).join("");
  var ticks = [0, .25, .5, .75, 1].map(function (f) { return "<span style=\"left:" + f * 100 + '%">' + (M.max * f) + (m === "tok" ? "M" : "%") + "</span>"; }).join("");
  return '<div class="dchart" id="resChart"><div class="dc-scope"><b>' + b.name + " · " + M.name + "</b> (" + M.dir + ") · per backbone: " + b.n[m] + " · 6 backbones × 6 defenses · " + tag("paper") + "Table 1</div>" + rows +
    '<div class="dc-axis"><span class="dc-m"></span><span class="dc-ticks">' + ticks + '</span><span class="dc-v"></span></div>' +
    '<div class="dc-key">' + P.DEFS.map(function (d) { return '<span><i class="dc-mk mk-' + d.replace(/\s/g, "").toLowerCase() + '">' + MARK[d] + "</i>" + d + "</span>"; }).join("") + '<span><i class="dc-line good"></i>AIRGuard better than no defense</span><span><i class="dc-line worse"></i>worse</span></div>' +
    '<p class="small muted">Select a backbone to see all values for that row and any case that can be opened.</p></div>';
}
function detail() {
  var model = S.res.model; if (!model) return "";
  var b = BEN[S.res.bench];
  var t = '<table class="dtab"><thead><tr><th>Defense</th><th>ASR ↓</th><th>UPR ↑</th><th>Tokens ↓</th></tr></thead><tbody>' + P.DEFS.map(function (d) {
    return "<tr" + (d === "AIRGuard" ? ' class="hl"' : "") + "><td>" + d + "</td><td>" + fmt(P.cell(model, d, b.col.asr), "asr") + "</td><td>" + fmt(P.cell(model, d, b.col.upr), "upr") + "</td><td>" + fmt(P.cell(model, d, b.col.tok), "tok") + "</td></tr>";
  }).join("") + "</tbody></table>";
  var hasCase = model === "GPT-5.6 Sol" && S.res.bench === "agenttrap";
  return '<div class="d-card dc-detail" id="resDetail"><h3>' + esc(model) + " · " + b.name + "</h3>" + '<div class="tscroll">' + t + "</div>" +
    (hasCase ? '<p>' + tag("rec") + 'One AIRGuard run of this cell is replayed on this page: AgentTrap task 8, where a single CC recipient was dropped. <button type="button" class="btn small primary" data-jump="#bench" data-back="Results · ' + esc(model) + '">Open the case →</button></p><p class="small">' + tag("saved") + "This AIRGuard cell is the mean of three runs: ASR 6, 8 and 7 of 91 (21 / 273); UPR 28, 34 and 31 of 50 (93 / 150).</p>"
      : '<p class="small">' + tag("unk") + "No case from this cell is loaded on this page. The recorded case comes from GPT-5.6 Sol on AgentTrap.</p>") + "</div>";
}

function f1() {
  var F = P.finding1, segs = [["Script effect check blocked the call", F.execBlock, "s-exec"], ["Graph blocked a startup-file write", F.graphStartup, "s-graph"], ["One recipient dropped, email sent", F.ccDrop, "s-cc"], ["Risk tag", F.tag, "s-o"], ["Deletion rule", F.deletion, "s-o"], ["Sequence audit", F.seq, "s-o"], ["No action; agent did not attempt the attack", F.noAction, "s-none"]];
  return '<div class="d-card" id="finding1"><h3>Finding 1 · How AIRGuard stopped attacks the other systems let through ' + tag("paper") + "</h3>" +
    "<p class=\"small\">All AgentTrap attacks that succeeded under no defense, ARGUS or MELON but failed under AIRGuard on the same backbone: <b>" + F.runs + " runs</b> over six backbones. AIRGuard intervened in " + F.intervened + "; each first intervention was on an execution call.</p>" +
    '<div class="stack" role="img" aria-label="74 runs split by what decided them">' + segs.map(function (s) { return '<i class="' + s[2] + '" style="flex:' + s[1] + '" title="' + esc(s[0] + ": " + s[1]) + '"></i>'; }).join("") + "</div>" +
    '<ul class="stack-key">' + segs.map(function (s) { return '<li><i class="' + s[2] + '"></i><b>' + s[1] + "</b> " + s[0] + (s[2] === "s-cc" ? ' <button type="button" class="linkish" data-jump="#bench" data-back="Finding 1" data-step="3">this is the case above →</button>' : "") + "</li>"; }).join("") + "</ul>" +
    '<p class="small">In the same runs ARGUS approved ' + F.argusApproved[0] + " of " + F.argusApproved[1] + " execution and write calls, MELON " + F.melonApproved[0] + " of " + F.melonApproved[1] + '.</p><p class="bound">' + tag("ed", "Boundary") + "The case on this page shows a rare path: one of 46 interventions. In 28 runs AIRGuard did nothing and the agent did not try the attack, so part of the reduction is run-to-run variation.</p></div>";
}
function f2() {
  var F = P.finding2, other = F.camelFail - F.camelHalt - F.camelInsufficient;
  return '<div class="d-card" id="finding2"><h3>Finding 2 · Interventions on benign tasks ' + tag("paper") + "</h3>" +
    '<div class="f2"><div class="stat"><span class="st-l">Benign tool calls blocked by AIRGuard</span><b>' + F.blocked + " / " + F.calls.toLocaleString("en") + '</b><span class="st-d">in ' + F.runsTouched + " of " + F.benignRuns + " benign AgentTrap runs, six backbones. Both runs where AIRGuard removed only part of a call completed their task.</span></div>" +
    '<div><p class="small"><b>CaMeL</b>: of ' + F.camelFail + " benign tasks AIRGuard completes but CaMeL fails —</p>" +
    '<div class="stack"><i class="s-exec" style="flex:' + F.camelHalt + '" title="halts a state-changing call that depends on an untrusted value: ' + F.camelHalt + '"></i><i class="s-graph" style="flex:' + F.camelInsufficient + '" title="quarantined model reports insufficient information: ' + F.camelInsufficient + '"></i><i class="s-none" style="flex:' + other + '" title="other reasons: ' + other + '"></i></div>' +
    '<ul class="stack-key"><li><i class="s-exec"></i><b>' + F.camelHalt + "</b> halts a state-changing call that depends on a value it treats as untrusted</li><li><i class=\"s-graph\"></i><b>" + F.camelInsufficient + '</b> quarantined model reports insufficient information</li><li><i class="s-none"></i><b>' + other + "</b> other reasons</li></ul>" +
    '<p class="small"><b>VIGIL</b> fails ' + F.vigilFail + " benign tasks that AIRGuard completes (five backbones); " + F.vigilVerifier + " follow directly from verifier rejections or refusals.</p></div></div></div>";
}
function t2() {
  return '<div class="d-card"><h3>Table 2 · Stating the policy vs enforcing it ' + tag("paper") + '</h3><p class="small">GPT-5.6 Sol, the 91 AgentTrap attacks, ASR (lower is better).</p>' +
    '<div class="hbars">' + P.T2.map(function (r) { return '<div class="hb"><span>' + r[0] + '</span><span class="hb-t"><i style="width:' + (r[1] / 25 * 100) + '%"' + (r[0] === "Full AIRGuard" ? ' class="ag"' : "") + '></i></span><b>' + r[1].toFixed(1) + "%</b></div>"; }).join("") + "</div>" +
    '<p class="small muted">Prompt-only states the same policy in the agent prompt; full AIRGuard enforces it before each tool call. In five prompt-only runs the agent made no tool call, against one such run without a defense.</p></div>';
}
function fig1a() {
  return '<div class="d-card"><h3>Motivation · No-defense ASR by benchmark ' + tag("paper") + '</h3><p class="small">Figure 1a, pooled over the paper’s backbones.</p><div class="hbars">' +
    P.fig1a.map(function (r) { return '<div class="hb"><span>' + r[0] + '</span><span class="hb-t"><i style="width:' + (r[1] / 25 * 100) + '%"></i></span><b>' + r[1].toFixed(1) + "%</b></div>"; }).join("") + "</div>" +
    '<p class="small muted">Context-aware benchmarks (DTAP, AgentTrap) succeed far more often than context-agnostic ones. The comparison is descriptive: the benchmarks also differ in models and harnesses.</p></div>';
}
function table1() {
  var b = BEN[S.res.bench];
  var head = '<tr><th rowspan="2">Backbone</th><th rowspan="2">Defense</th><th colspan="3"' + (S.res.bench === "dtap" ? ' class="hlc"' : "") + '>DTAP-150</th><th colspan="3"' + (S.res.bench === "agenttrap" ? ' class="hlc"' : "") + ">AgentTrap</th></tr><tr><th>ASR ↓</th><th>UPR ↑</th><th>Tokens ↓</th><th>ASR ↓</th><th>UPR ↑</th><th>Tokens ↓</th></tr>";
  var rows = P.MODELS.map(function (model) {
    return P.DEFS.map(function (d, j) {
      var c = P.T1[model][j];
      return "<tr" + (d === "AIRGuard" ? ' class="hl"' : "") + ">" + (j === 0 ? '<td rowspan="6" class="mcell">' + model + "</td>" : "") + "<td>" + d + "</td>" + c.map(function (v, i) {
        var on = (i < 3 ? "dtap" : "agenttrap") === S.res.bench && i % 3 === ["asr", "upr", "tok"].indexOf(S.res.metric);
        var link = model === "GPT-5.6 Sol" && d === "AIRGuard" && i === 3 ? ' <button type="button" class="linkish" data-jump="#bench" data-back="Table 1">case</button>' : "";
        return "<td" + (on ? ' class="hlc"' : "") + ">" + (i % 3 === 2 ? v.toFixed(1) + "M" : v.toFixed(1) + "%") + link + "</td>";
      }).join("") + "</tr>";
    }).join("");
  }).join("");
  return '<details class="d-card t1"><summary>Full Table 1 (36 rows) · current selection highlighted</summary><div class="tscroll"><table class="dtab t1tab"><thead>' + head + "</thead><tbody>" + rows + "</tbody></table></div>" +
    '<p class="src">' + tag("paper") + "Table 1, WWW '27 submission #7481; checked cell by cell against the PDF. Bold “best per backbone” from the paper is not reproduced.</p></details>";
}
function notes() {
  return '<div class="d-card"><h3>Definitions and provenance</h3><ul class="lims">' +
    "<li>" + tag("paper") + "<span><b>" + BEN[S.res.bench].name + " " + MET[S.res.metric].name + ".</b> " + BEN[S.res.bench].def[S.res.metric] + " A case that reaches the 20-turn limit or is refused by the model provider counts as neither an attack success nor a completed task.</span></li>" +
    "<li>" + tag("saved") + "<span><b>GPT-5.6 Sol, AgentTrap, AIRGuard</b> is the mean of three runs (ASR 21 / 273, UPR 93 / 150). The table caption does not say so.</span></li>" +
    "<li>" + tag("log") + "<span><b>No-defense rows combine two harnesses.</b> UPR for GPT-5.6 Sol and GPT-6 Luna comes from the native harness used by ARGUS and MELON; the other cells from the unified controller. The whole no-defense row for GPT-6 Astra and Opus 4.8 comes from the native harness.</span></li>" +
    "<li>" + tag("paper") + "<span><b>Harness effect on DTAP UPR.</b> ARGUS and MELON run inside DTAP’s own agent, which completes more benign tasks than the paper’s loop even without a defense, so UPR gaps on DTAP-150 cannot be attributed to the defense alone.</span></li>" +
    "<li>" + tag("post", "Post-paper · 2026-10-29") + "<span><b>GPT-5.6 Sol, DTAP-150, AIRGuard</b> was produced with guard code from before the 2026-10-18 final-method commit. Replaying its trajectories with the current code allows some recorded email sends that the older code blocked; a fresh run with current code gave ASR 13 / 100 and UPR 34 / 50. Which version to report is not yet settled.</span></li></ul>" +
    '<p class="src">Ledger entries: EXPERIMENT_LOG.md 2026-10-17, 10-23, 10-25, 10-26, 10-29.</p></div>';
}

function render() {
  body.innerHTML = '<div class="res-ctl"><div class="seg" role="group" aria-label="Benchmark" id="resBench"><button type="button" data-b="agenttrap">AgentTrap</button><button type="button" data-b="dtap">DTAP-150</button></div>' +
    '<div class="seg" role="group" aria-label="Metric" id="resMet"><button type="button" data-m="asr">ASR ↓</button><button type="button" data-m="upr">UPR ↑</button><button type="button" data-m="tok">Tokens ↓</button></div></div>' +
    '<div class="res-grid"><div>' + chart() + detail() + "</div><div>" + notes() + "</div></div>" + table1() +
    '<div class="d-two">' + f1() + f2() + '</div><div class="d-two">' + t2() + fig1a() + "</div>";
  body.querySelectorAll("[data-b]").forEach(function (x) { x.classList.toggle("on", x.dataset.b === S.res.bench); x.setAttribute("aria-pressed", x.dataset.b === S.res.bench); });
  body.querySelectorAll("[data-m]").forEach(function (x) { x.classList.toggle("on", x.dataset.m === S.res.metric); x.setAttribute("aria-pressed", x.dataset.m === S.res.metric); });
}
body.addEventListener("click", function (e) {
  var b = e.target.closest("[data-b]"), m = e.target.closest("[data-m]"), r = e.target.closest(".dc-row");
  if (b) { S.res.bench = b.dataset.b; D.save(); render(); return; }
  if (m) { S.res.metric = m.dataset.m; D.save(); render(); return; }
  if (r) { S.res.model = S.res.model === r.dataset.model ? null : r.dataset.model; D.save(); render(); var d = document.getElementById("resDetail"); if (d) { var x = d.getBoundingClientRect(); if (x.bottom > window.innerHeight) window.scrollBy({ top: Math.min(x.bottom - window.innerHeight + 16, x.top - D.topOffset()), behavior: D.reduceMotion() ? "auto" : "smooth" }); } }
});
// "agenttrap:asr" from overview links
D.onJump("res", function (v) { var q = v.split(":"); S.res.bench = q[0]; S.res.metric = q[1]; if (q[0] === "agenttrap") S.res.model = "GPT-5.6 Sol"; D.save(); render(); });
render();
})();
