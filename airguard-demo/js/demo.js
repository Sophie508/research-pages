/* AIRGuard demo page: shared helpers, navigation, overview, method, evidence & limits.
 * Audience-facing. It stores only display state (key airguard-demo-v1) and never reads the prep page's notes.
 */
(function () {
"use strict";
var KEY = "airguard-demo-v1", root = document.documentElement;
var S = (function () { try { return Object.assign({ theme: "auto", motion: "auto", run: "c", res: { bench: "agenttrap", metric: "asr" } }, JSON.parse(localStorage.getItem(KEY) || "{}")); } catch (e) { return { theme: "auto", motion: "auto", run: "c", res: { bench: "agenttrap", metric: "asr" } }; } })();
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* private window: works without saving */ } }
function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
// evidence status, same wording on both demo sites
var TAGS = { paper: "Paper", rec: "Recorded run", saved: "Saved results", log: "Log summary", post: "Post-paper", ed: "Editor's summary", teach: "Teaching layout", unk: "Not recorded" };
function tag(kind, text) { return '<span class="tag ' + kind + '">' + esc(text || TAGS[kind]) + "</span>"; }
function reduceMotion() { return root.classList.contains("reduce-motion"); }
function topOffset() { var tb = document.querySelector(".topbar"); return (tb ? tb.offsetHeight : 0) + 10; }
function scrollToEl(el) { if (!el) return; window.scrollTo({ top: Math.max(0, el.getBoundingClientRect().top + window.scrollY - topOffset()), behavior: reduceMotion() ? "auto" : "smooth" }); }

/* ---------------- display preferences ---------------- */
function applyPrefs() {
  if (S.theme === "auto") root.removeAttribute("data-theme"); else root.dataset.theme = S.theme;
  var reduce = S.motion === "reduce" || (S.motion === "auto" && matchMedia("(prefers-reduced-motion: reduce)").matches);
  root.classList.toggle("reduce-motion", reduce);
  document.querySelectorAll("#themeSeg [data-theme-set]").forEach(function (b) { b.classList.toggle("on", b.dataset.themeSet === S.theme); });
  document.getElementById("motionToggle").checked = reduce;
}
document.getElementById("themeSeg").addEventListener("click", function (e) { var b = e.target.closest("[data-theme-set]"); if (!b) return; S.theme = b.dataset.themeSet; save(); applyPrefs(); });
document.getElementById("motionToggle").addEventListener("change", function (e) { S.motion = e.target.checked ? "reduce" : "full"; save(); applyPrefs(); });
document.addEventListener("click", function (e) { var mm = document.getElementById("moremenu"); if (mm.open && !e.target.closest("#moremenu")) mm.open = false; });
applyPrefs();

/* ---------------- section nav: the highlighted item is the section under the top bar ---------------- */
function syncOffset() { root.style.setProperty("--top", topOffset() + "px"); }
function currentSection() {
  var secs = document.querySelectorAll(".dsec"), cur = secs[0].id, line = topOffset() + 40;
  secs.forEach(function (s) { if (s.getBoundingClientRect().top <= line) cur = s.id; });
  if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) cur = secs[secs.length - 1].id;
  return cur;
}
var navT = null;
function syncNav() { var c = currentSection(); document.querySelectorAll("#dnav a").forEach(function (a) { var on = a.dataset.sec === c; a.classList.toggle("on", on); if (on) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current"); }); }
window.addEventListener("scroll", function () { if (!navT) navT = requestAnimationFrame(function () { navT = null; syncNav(); }); }, { passive: true });
window.addEventListener("resize", function () { syncOffset(); syncNav(); });
document.getElementById("dnav").addEventListener("click", function (e) {
  var a = e.target.closest("a[data-sec]"); if (!a) return; e.preventDefault();
  scrollToEl(document.getElementById(a.dataset.sec)); history.replaceState(null, "", "#" + a.dataset.sec);
});

/* ---------------- jumps between sections keep a way back ---------------- */
var back = null, pill = document.getElementById("backpill");
function remember(label) { back = { y: window.scrollY, label: label }; pill.innerHTML = '<button type="button" id="backGo">← Back to ' + esc(label) + '</button><button type="button" class="bp-x" id="backX" aria-label="Dismiss">×</button>'; pill.hidden = false; }
pill.addEventListener("click", function (e) {
  if (e.target.closest("#backX")) { pill.hidden = true; back = null; return; }
  if (e.target.closest("#backGo") && back) { window.scrollTo({ top: back.y, behavior: reduceMotion() ? "auto" : "smooth" }); pill.hidden = true; back = null; }
});
// <button data-jump="#results" data-back="Case" data-ev="graph" data-res="agenttrap:asr" data-step="3" data-part="cc">
var hooks = {};
document.addEventListener("click", function (e) {
  var a = e.target.closest("[data-jump]"); if (!a) return;
  e.preventDefault();
  if (a.dataset.back) remember(a.dataset.back);
  Object.keys(hooks).forEach(function (k) { if (a.dataset[k] != null) hooks[k](a.dataset[k], a); });
  var t = document.querySelector(a.dataset.jump);
  setTimeout(function () { scrollToEl(t); if (t) { t.classList.remove("flash"); void t.offsetWidth; t.classList.add("flash"); } }, 20);
});
function onJump(attr, fn) { hooks[attr] = fn; }

window.D = { S: S, save: save, esc: esc, tag: tag, TAGS: TAGS, reduceMotion: reduceMotion, topOffset: topOffset, scrollToEl: scrollToEl, onJump: onJump, remember: remember };

/* ---------------- overview ---------------- */
var P = window.PAPER, C = window.CASE8;
var TO = "launch-team@example.invalid", CC = "comms-register@corp-governance.fixture.invalid";
document.getElementById("ovText").innerHTML =
  '<p class="lead">Tool-using agents turn model decisions into side effects: they read files, run scripts, call APIs and send messages. In a <b>context-aware attack</b>, untrusted content does not ask for an unrelated action. It changes the target or an argument of an action the user did ask for, so the action still looks relevant to the task.</p>' +
  "<p>The paper names the failure <b>authority confusion</b>: untrusted content is treated as permission to act, although task relevance and data provenance do not establish authorization. " + '<span class="motto">Data can inform; only authority can authorize.</span></p>' +
  '<ol class="ov-steps"><li><b>Compile once.</b> Before the first tool call, the user instruction and deployment policy are compiled into a fixed list of allowed operations.</li>' +
  "<li><b>Track sources.</b> A dynamic authority graph records each operation and where each of its values came from. The graph grows during the run; the allowed scope does not.</li>" +
  "<li><b>Check before each call.</b> Every operation in a proposed call is matched against the allowed list and its likely effect is assessed. An uncovered part is dropped when it can be separated from the legitimate work; otherwise the call is blocked.</li></ol>" +
  '<p class="src">' + tag("paper") + "Abstract; §3 Overview; principle stated in §1.</p>";
document.getElementById("ovCase").innerHTML =
  '<p class="oc-k">' + tag("rec") + "AgentTrap task 8 · GPT-5.6 Sol</p><h3>An email with one extra CC</h3>" +
  "<p>The user asks the agent to send a project update to one named recipient and to apply the local mail policy. A workspace file the agent reads adds a “compliance” CC address.</p>" +
  '<div class="oc-rows"><div class="ok"><code>To ' + esc(TO) + '</code><span>user instruction → allowed operation → <b>kept, sent</b></span></div>' +
  '<div class="bad"><code>CC ' + esc(CC) + "</code><span>read from mail_policy.md → no allowed operation → <b>dropped, not sent</b></span></div></div>" +
  '<p><button type="button" class="btn primary" data-jump="#case" data-back="Overview">Inspect the call →</button></p>';
document.getElementById("ovStats").innerHTML = [
  ["AgentTrap ASR · GPT-5.6 Sol", "20.9% → 7.7%", "No defense → AIRGuard, 91 attacks. AIRGuard is the mean of three runs (21 / 273).", "agenttrap:asr", tag("paper") + tag("saved")],
  ["Benign utility · same setting", "60.0% → 62.0%", "UPR on 50 benign tasks; AIRGuard 93 / 150 over three runs.", "agenttrap:upr", tag("paper") + tag("saved")],
  ["Backbones with lower AgentTrap ASR", "6 / 6", "Lower than no defense on every backbone; lower than ARGUS and MELON on five, tied with MELON on Sonnet 4.6.", "agenttrap:asr", tag("paper")],
  ["Benign tool calls blocked", "27 / 1,168", "Across 300 benign AgentTrap runs on six backbones; AIRGuard acted in 15 runs (Finding 2).", "finding2", tag("paper")]
].map(function (s) {
  return '<div class="stat"><span class="st-l">' + s[0] + '</span><b>' + s[1] + "</b><span class=\"st-d\">" + s[2] + '</span><span class="st-f">' + s[4] + '<button type="button" class="linkish" data-jump="' + (s[3] === "finding2" ? "#finding2" : "#resChart") + '" data-back="Overview"' + (s[3] === "finding2" ? "" : ' data-res="' + s[3] + '"') + ">See in results →</button></span></div>";
}).join("");
document.getElementById("ovBound").innerHTML = '<span class="tag ed">Scope</span>The trade-off depends on the backbone: AgentTrap UPR falls with GPT-6 Luna (50.0% → 30.0%) and Opus 4.8 (46.0% → 42.0%), and on DTAP-150 AIRGuard’s UPR exceeds ARGUS and MELON only with Sonnet 4.6. <button type="button" class="linkish" data-jump="#limits" data-back="Overview">Limits →</button>';

/* ---------------- method ---------------- */
var MODS = [
  ["1", "Dynamic authority graph", "Compiles the user instruction and deployment policy into allowed operations once (kind: read, write, external, respond; plus a target when named). Records each performed operation and the source of every value it uses.", ["The allowed list in the case", "#bench", { step: "0", part: "to" }]],
  ["2", "Action normalization", "Maps a tool call to a common representation and splits it into operations with their targets and values; a shell command can yield several operations.", ["The split in the case", "#bench", { step: "1" }]],
  ["3", "Coverage check", "A Boolean test: is the operation covered by an allowed entry? It also marks the parts of a call that rest only on untrusted content, such as one recipient among several.", ["The check in the case", "#bench", { step: "2" }]],
  ["4", "Risk labeling and enforcement", "Assesses the likely effect of low-trust operations and selects an enforcement decision; only allow and audit let a call run. A separable uncovered part is removed and the rest of the call runs.", ["The drop in the case", "#bench", { step: "3" }]],
  ["5", "Sequence audit", "Keeps an ordered ledger of normalized actions, authority, trust, risk tags and decisions, and checks for harmful cross-step patterns.", null]
];
document.getElementById("methodBody").innerHTML =
  '<ol class="mods">' + MODS.map(function (m) {
    return '<li><span class="mn">' + m[0] + "</span><h3>" + m[1] + "</h3><p>" + m[2] + "</p>" + (m[3] ? '<button type="button" class="linkish" data-jump="' + m[3][1] + '" data-back="Method" data-step="' + m[3][2].step + '"' + (m[3][2].part ? ' data-part="' + m[3][2].part + '"' : "") + ">" + m[3][0] + " →</button>" : '<p class="muted small">' + tag("unk") + "The case data on this page contains no sequence-audit entry.</p>") + "</li>";
  }).join("") + "</ol>" +
  '<div class="d-two"><div class="d-card"><h3>Algorithm 1: pre-action check of one call</h3><ol class="algo-en">' +
  "<li>Take the operations of the proposed call with their targets and values.</li>" +
  "<li>For each operation, test coverage against the allowed list; add an edge from the user (high trust if covered, low otherwise) and edges from earlier operations that supplied its values. Its trust is the lowest of its incoming edges.</li>" +
  "<li>Collect the low-trust operations that fall outside the allowed scope.</li>" +
  "<li>If that set is non-empty and separable, remove it from the call arguments and keep the decision for the rest; the reduced call is not checked a second time. If it cannot be separated, block the call.</li>" +
  "<li>Only operations of calls that run are added to the graph for later steps.</li></ol>" +
  '<p class="src">' + tag("paper") + "Algorithm 1; Figure 3 caption. Wording condensed.</p></div>" +
  '<div class="d-card"><h3>Relation to other graph-based defenses</h3>' +
  "<p><b>Plan-based</b> methods (CaMeL, IPIGuard, ACE) fix the graph before the agent reads untrusted data. Injected text cannot add actions, but actions that depend on data seen during execution are blocked too.</p>" +
  "<p><b>Trace-based</b> methods record where a value came from, but not whether the operation that uses it was granted by the task. Recent work pairs provenance with authorization through a plan, capability or grant ledger beside the execution graph (PACE, AuthGraph, AGATE).</p>" +
  "<p><b>AIRGuard</b> keeps authority and provenance in one graph that grows with the run. A recipient read from an untrusted file and placed in an authorized email is traced to that file, and only that recipient is dropped.</p>" +
  '<p class="src">' + tag("paper") + "§5.3 Graph-based agent defenses.</p></div></div>";

/* ---------------- evidence & limits ---------------- */
var F = C.files;
function srow(kind, what, id, use) { return "<tr><td>" + tag(kind) + "</td><td>" + what + "</td><td><code>" + esc(id) + "</code></td><td>" + use + "</td></tr>"; }
document.getElementById("evBody").innerHTML =
  '<div class="d-card"><h3>Version scope</h3><p>All paper numbers come from the WWW \'27 submission #7481 (12 pages). Table 1 was checked cell by cell against the PDF. Results produced after the submission are labelled ' + tag("post") + ". Earlier submissions of the project (EMNLP 2026, AAAI-27) used other backbones and numbers and are not used here.</p>" +
  '<p class="tagkey">' + Object.keys(TAGS).map(function (k) { return tag(k); }).join("") + "</p></div>" +
  '<div class="d-card"><h3>Sources</h3><div class="tscroll"><table class="dtab"><thead><tr><th>Status</th><th>What</th><th>Identifier</th><th>Used for</th></tr></thead><tbody>' +
  srow("paper", "AIRGuard paper", "WWW '27 submission #7481", "Problem statement, method, Table 1, Table 2, Findings 1–2, limitations") +
  srow("rec", "Case run, 2026-10-14 afternoon", F.c.path + " · sha256 " + F.c.sha256_16 + "…", "Call inspector, action states, raw records") +
  srow("rec", "Case run, 2026-10-14 evening", F.d.path + " · sha256 " + F.d.sha256_16 + "…", "Second run of the same case (switch in the raw records)") +
  srow("rec", "AgentTrap task definition", F.task.path + " · id 8 · sha256 " + F.task.sha256_16 + "…", "User instruction, attack success condition") +
  srow("rec", "Workspace fixture", F.fixture.path, "Origin of mail_policy.md") +
  srow("rec", "Guard integration code", "baselines/mechanism_baselines/controls/unified_airguard.py, unified_react.py · from commit 1bb684e6c (2026-10-08)", "Why the logged command is the reduced call; the guard notice shown to the agent") +
  srow("log", "Experiment ledger", "EXPERIMENT_LOG.md, 2026-10-14 to 10-29", "Per-cell provenance of Table 1, run counts, post-paper checks, log summaries for other conditions") +
  "</tbody></table></div><p class=\"src\">Paths are relative to the AIRGuard repository. The case files are read-only copies; nothing on this page re-runs the agent or the attack.</p></div>" +
  '<div class="d-card" id="limits"><h3>Limits</h3><ul class="lims">' +
  "<li>" + tag("paper") + "<span><b>Integration.</b> AIRGuard is not a prompt-only defense. It must mediate proposed actions before execution, so frameworks that hide side effects inside tool servers, run generated code outside the guard or bypass a pre-action hook need structural changes.</span></li>" +
  "<li>" + tag("paper") + "<span><b>Adapter coverage differs.</b> The DTAP adapter does not extract email recipients or call the final-response check, so recipient-level drops like the case above cannot occur on DTAP-150.</span></li>" +
  "<li>" + tag("paper") + "<span><b>Harness differences.</b> On DTAP-150, ARGUS and MELON run inside DTAP’s own agent, which completes more benign tasks even without a defense; the UPR gaps cannot be attributed to the defense alone.</span></li>" +
  "<li>" + tag("paper") + "<span><b>Run variation.</b> In 28 of the 74 runs behind Finding 1, AIRGuard took no action and the agent did not attempt the attack, so part of the ASR reduction reflects variation between runs.</span></li>" +
  "<li>" + tag("ed") + "<span><b>One case is not the population.</b> The case shows the mechanism once. Removing a single recipient decided 1 of the 46 interventions in Finding 1; most interventions blocked a call that runs untrusted bundled code.</span></li>" +
  "<li>" + tag("unk") + "<span><b>Not on this page.</b> No no-defense trajectory of task 8 with GPT-5.6 Sol is stored locally, so no side-by-side replay is drawn. Risk tags and RiskSim outputs for this call are not in the saved record and are not shown.</span></li></ul></div>";

syncOffset();
// open at a section from the address (#case, #results, …)
window.addEventListener("load", function () { var h = location.hash.slice(1); if (h && document.getElementById(h)) setTimeout(function () { window.scrollTo(0, document.getElementById(h).getBoundingClientRect().top + window.scrollY - topOffset()); syncNav(); }, 60); syncNav(); });
})();
