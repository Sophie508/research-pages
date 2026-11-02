/* Inline-SVG helpers shared by the demo diagrams, and the Method system diagram.
 * Nodes carry one or two short labels; edges carry their type in line style, marker and label, not colour alone.
 * Everything drawn in the system diagram follows Algorithm 1 and §3 of the WWW '27 submission.
 */
(function () {
"use strict";
var D = window.D, esc = D.esc, tag = D.tag;

/* ---------------- helpers ---------------- */
// markers are styled by CSS classes, so they follow the light and dark tokens
function defs(p) {
  return "<defs>" + ["ctl", "auth", "val", "file", "data", "none"].map(function (k) {
    return '<marker id="' + p + "-" + k + '" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="mk mk-' + k + '" d="M0,0 L10,5 L0,10 z"/></marker>';
  }).join("") + "</defs>";
}
// a node: lines[0] is the bold label, lines[1] (optional) the secondary label; o.mono puts line 2 in monospace
function node(id, x, y, w, h, cls, lines, o) {
  o = o || {};
  var t1y = lines[1] ? y + h / 2 - 3 : y + h / 2 + 5, label = lines.join(" · ");
  var shape = o.diamond ? '<path class="nb" d="M' + (x + w / 2) + "," + y + " L" + (x + w) + "," + (y + h / 2) + " L" + (x + w / 2) + "," + (y + h) + " L" + x + "," + (y + h / 2) + ' z"/>'
    : '<rect class="nb" x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + (o.rx == null ? 10 : o.rx) + '"/>' + (o.double ? '<rect class="nb2" x="' + (x + 4) + '" y="' + (y + 4) + '" width="' + (w - 8) + '" height="' + (h - 8) + '" rx="7"/>' : "");
  var tx = o.center || o.diamond ? x + w / 2 : x + 12, anchor = o.center || o.diamond ? ' text-anchor="middle"' : "";
  return '<g class="vz-n ' + cls + '" data-n="' + id + '"' + (o.static ? "" : ' tabindex="0" role="button" aria-label="' + esc(label) + '"') + ">" + shape +
    '<text class="t1" x="' + tx + '" y="' + t1y + '"' + anchor + ">" + esc(lines[0]) + "</text>" +
    (lines[1] ? '<text class="t2' + (o.mono ? " mono" : "") + '" x="' + tx + '" y="' + (y + h / 2 + 14) + '"' + anchor + ">" + esc(lines[1]) + "</text>" : "") + "</g>";
}
// an edge through the given points; the label sits on a halo at label point lp = [x, y]
function edge(id, p, pts, cls, label, lp, o) {
  o = o || {};
  var d = "M" + pts.map(function (q) { return q[0] + "," + q[1]; }).join(" L");
  return '<g class="vz-e ' + cls + '" data-e="' + id + '"><path d="' + d + '"' + (o.noArrow ? "" : ' marker-end="url(#' + p + "-" + o.mk + ')"') + "/>" +
    (label ? '<text class="el" x="' + lp[0] + '" y="' + lp[1] + '"' + (o.anchor ? ' text-anchor="' + o.anchor + '"' : ' text-anchor="middle"') + ">" + esc(label) + "</text>" : "") + "</g>";
}
// clicking or pressing Enter / Space on a node calls fn(id)
function bindNodes(svg, fn) {
  svg.addEventListener("click", function (e) { var g = e.target.closest(".vz-n[tabindex]"); if (g) fn(g.dataset.n); });
  svg.addEventListener("keydown", function (e) { if (e.key !== "Enter" && e.key !== " ") return; var g = e.target.closest(".vz-n[tabindex]"); if (g) { e.preventDefault(); fn(g.dataset.n); } });
}
function mark(svg, ids, cls) { svg.querySelectorAll(".vz-n, .vz-e").forEach(function (g) { g.classList.toggle(cls, ids.indexOf(g.dataset.n || g.dataset.e) >= 0); }); }
window.VZ = { defs: defs, node: node, edge: edge, bindNodes: bindNodes, mark: mark };

/* ---------------- Method: system structure ---------------- */
var host = document.getElementById("sysDiagram");
if (!host) return;
var P = "sys";
var COMMIT = "commit 1685e3a6c (2026-10-22)";
// what each part is, where the paper defines it, where the code is, and where the case shows it
var INFO = {
  task: ["User task g", "The user’s instruction: the only source of authority besides the deployment policy.", "Algorithm 1, Require", "src/airguard/envelope.py · derive_envelope (input)", ["The instruction in the case", "#paths", { pick: "c_inst" }]],
  policy: ["Deployment policy P", "Set by whoever deploys the agent. Compiled together with the task.", "§3 Module 1; Algorithm 1, Require", "src/airguard/envelope.py · derive_envelope", null, "The case record does not show a separate policy text."],
  compile: ["Compile authority (once)", "Before the first tool call a model turns g and P into a list of allowed operations. Each entry has a kind (read, write, external, respond) and, when the instruction names one, a target. External targets that only appear in content read later are never added.", "§3 Module 1; CompileAuthority(g, P)", "src/airguard/envelope.py · derive_envelope", ["The compiled list in the case", "#paths", { pick: "a_to" }]],
  alpha: ["Allowed operations α_task", "Fixed for the whole run. The graph grows; this scope does not.", "§3 Module 1", "src/airguard/envelope.py (entries); src/airguard/graph.py · TrustGraph.allowed_by (lookup)", ["The CC has no entry", "#paths", { pick: "a_cc" }]],
  agent: ["Agent proposes a call", "The LLM agent proposes one tool call u per turn. Nothing runs before the check below.", "Algorithm 1, input u", "baselines/mechanism_baselines/controls/unified_react.py (agent loop)", ["Turn 3 in the case", "#proc", { stage: 0 }]],
  norm: ["Normalize and split (Module 2)", "Maps the call to a common action type and splits it into operations, each with a target and the values it uses. A shell command can yield several operations; one email can yield one operation per recipient.", "Algorithm 1, line 1", "src/airguard/guard.py · action_from_tool_call; src/airguard/graph.py · TrustGraph.propose", ["The split in the case", "#proc", { stage: 1 }]],
  cov: ["Coverage and trust (Modules 1 and 3)", "For each operation: is it covered by an allowed entry? Add an edge from the user (high trust if covered, low otherwise) and an edge from every earlier operation whose output supplies a value. Trust is the lowest of the incoming edges. Low-trust operations that reach outside the workspace, write untrusted values into dependency or persistence files, or copy files out of scope form the set V.", "Algorithm 1, lines 2–8", "src/airguard/graph.py · TrustGraph.allowed_by, TrustGraph.violations", ["The check in the case", "#proc", { stage: 2 }]],
  graph: ["Authority graph G_i (dynamic)", "Records performed operations, their authority and the source of every value. It is read during each check and grows only when a call actually runs.", "§3 Module 1; Algorithm 1, lines 4–5 and 18", "src/airguard/graph.py · TrustGraph", ["The value-source edge of the CC", "#paths", { pick: "s_cc" }]],
  risk: ["Risk labeling and enforcement (Module 4)", "Rule tags (e.g. secret access, hidden recipients, destructive writes, persistence) and, only for process.exec and output.respond, a focused model assessment (RiskSim) feed a fixed priority cascade. Covered low-risk actions may run under audit; uncovered actions resolve to ask, inspect or block. The model cannot grant a missing capability.", "Algorithm 1, lines 9–10", "src/airguard/authority_context.py · detect_risk_tags; src/airguard/risk_simulation.py · simulate_risk; src/airguard/enforcement.py · decide_enforcement", null, "Risk tags and RiskSim output for the case call are not in the saved record."],
  seq: ["Sequence audit (Module 5)", "Compares the call with earlier ledger entries for fixed cross-step patterns (e.g. secret access then network transmission). It can only make the decision stricter.", "Algorithm 1, line 11", "src/airguard/audit_containment.py · audit_sequence", null, "The case data on this page contains no sequence-audit entry."],
  ledger: ["Ledger L (dynamic)", "Ordered record of each normalized action with its authority, trust, risk tags and decision.", "§3 Module 5; Algorithm 1, line 16", "src/airguard/graph.py · TrustGraph.record (appends the entry; commits operations to the graph only if the call executed)", null],
  drop: ["Drop the uncovered part, or block", "If V is not empty, its arguments are removed from the call and the decision for the rest is kept, without a second check. If they cannot be removed, the call is blocked.", "Algorithm 1, lines 12–14", "src/airguard/graph.py · drop_violations (called in guard.check_action)", ["The CC being dropped", "#proc", { stage: 3 }]],
  gate: ["Run only allow or audit", "Only these two decisions execute the call; ask, inspect and block do not.", "Algorithm 1, line 17", "src/airguard/guard.py · check_action", ["The executed call", "#proc", { stage: 4 }]],
  exec: ["Execute; then update the graph", "The (possibly reduced) call runs, and only then are its operations and edges added to the graph for later steps.", "Algorithm 1, line 18; Figure 3 caption", "baselines/mechanism_baselines/controls/unified_airguard.py (runs the reduced arguments); src/airguard/graph.py · TrustGraph.record", ["The executed call", "#proc", { stage: 4 }]],
  obs: ["Observation back to the agent", "The tool output returns to the agent; credential patterns are redacted first. The guard also reads the output: every value in it is traced to this call, so a later call that uses one of those values gets a value-source edge. When part of a call was dropped, the evaluated integration appends a guard line naming it.", "Appendix, post-action guard", "src/airguard/guard.py · observe_output → graph.py · TrustGraph.observe; src/airguard/output_guard.py · redact_credentials; baselines/mechanism_baselines/controls/unified_react.py", ["How the CC value got its source edge", "#paths", { pick: "s_cc" }]],
  blocked: ["Not executed", "Nothing runs; the agent receives a block notice and continues.", "Algorithm 1, lines 17–20", "baselines/mechanism_baselines/controls/unified_react.py (BLOCKED observation)", null, "Not exercised in the case: its call was allowed with one part dropped."]
};
function svg() {
  var s = '<svg class="vz sys" viewBox="0 0 1120 580" role="img" aria-labelledby="sysT sysD"><title id="sysT">AIRGuard system structure</title><desc id="sysD">Once per run, the user task and deployment policy are compiled into a fixed list of allowed operations. Before every tool call, the proposed call is normalized and split, each operation is checked against the allowed list and the dynamic authority graph, a decision is made and possibly escalated by the sequence audit, uncovered parts are dropped or the call is blocked, and only allowed or audited calls run and update the graph.</desc>' + defs(P);
  s += '<rect class="band once" x="8" y="8" width="1104" height="128" rx="14"/><text class="bl" x="22" y="28">ONCE PER RUN · before the first tool call</text>';
  s += '<rect class="band loop" x="8" y="148" width="1104" height="424" rx="14"/><text class="bl" x="22" y="168">BEFORE EVERY TOOL CALL</text>';
  // once per run
  s += edge("e-tc", P, [[220, 62], [248, 76]], "data", "", null, { mk: "data" }) + edge("e-pc", P, [[220, 108], [248, 92]], "data", "", null, { mk: "data" });
  s += edge("e-ca", P, [[430, 84], [488, 84]], "data", "writes", [459, 76], { mk: "data" });
  s += node("task", 40, 40, 180, 42, "in", ["User task g"]) + node("policy", 40, 88, 180, 40, "in", ["Deployment policy P"]);
  s += node("compile", 250, 60, 180, 48, "proc", ["Compile authority", "model · once"]);
  s += node("alpha", 490, 52, 200, 64, "state fixed", ["Allowed operations α", "fixed · 🔒"], { double: true });
  // per call, row 1 (left to right)
  s += edge("e-an", P, [[154, 213], [212, 213]], "ctl", "call u", [183, 205], { mk: "ctl" });
  s += edge("e-nc", P, [[384, 213], [444, 213]], "ctl", "ops O", [414, 205], { mk: "ctl" });
  s += edge("e-cr", P, [[646, 213], [706, 213]], "ctl", "trust · V", [676, 205], { mk: "ctl" });
  s += edge("e-rs", P, [[878, 213], [938, 213]], "ctl", "d", [908, 205], { mk: "ctl" });
  s += edge("e-ac", P, [[560, 116], [560, 183]], "data", "reads: covered?", [566, 152], { mk: "data", anchor: "start" });
  // state row
  s += edge("e-gc", P, [[490, 300], [490, 243]], "data", "value sources", [484, 276], { mk: "data", anchor: "end" });
  s += edge("e-ls", P, [[1050, 300], [1050, 243]], "data", "earlier entries", [1044, 276], { mk: "data", anchor: "end" });
  // per call, row 2 (right to left)
  s += edge("e-sd", P, [[1100, 213], [1112, 213], [1112, 448], [1102, 448]], "ctl", "d (only stricter)", [1106, 395], { mk: "ctl", anchor: "end" });
  s += edge("e-dl", P, [[985, 420], [985, 362]], "data", "append (u, d)", [979, 395], { mk: "data", anchor: "end" });
  s += edge("e-dg", P, [[915, 448], [854, 448]], "ctl", "u′", [884, 440], { mk: "ctl" });
  s += edge("e-ge", P, [[700, 448], [642, 448]], "ctl ok", "", null, { mk: "ctl" });
  s += '<text class="el br-ok" x="671" y="412" text-anchor="middle">allow · audit</text>';
  s += edge("e-gb", P, [[775, 487], [775, 512]], "ctl alt", "ask · inspect · block", [783, 503], { mk: "ctl", anchor: "start" });
  s += edge("e-eg", P, [[600, 420], [600, 362]], "data", "add ops + edges", [606, 395], { mk: "data", anchor: "start" });
  s += edge("e-og", P, [[330, 420], [330, 331], [444, 331]], "data", "returned values", [336, 380], { mk: "data", anchor: "start" });
  s += edge("e-eo", P, [[470, 448], [407, 448]], "ctl", "result", [438, 440], { mk: "ctl" });
  s += edge("e-oa", P, [[215, 448], [80, 448], [80, 243]], "ctl", "next turn", [86, 344], { mk: "ctl", anchor: "start" });
  s += edge("e-ba", P, [[700, 536], [120, 536], [120, 243]], "ctl alt", "notice, next turn", [126, 520], { mk: "ctl", anchor: "start" });
  s += node("agent", 24, 185, 130, 56, "agent", ["Agent (LLM)", "proposes call u"]);
  s += node("norm", 214, 185, 170, 56, "proc", ["Normalize & split", "Module 2"]);
  s += node("cov", 446, 185, 200, 56, "proc key", ["Coverage + trust", "Modules 1 + 3"]);
  s += node("risk", 708, 185, 170, 56, "proc", ["Risk tags → decide", "Module 4"]);
  s += node("seq", 940, 185, 160, 56, "proc", ["Sequence audit", "Module 5"]);
  s += node("graph", 446, 302, 200, 58, "state dyn", ["Authority graph G", "grows · dynamic"]);
  s += node("ledger", 930, 302, 170, 58, "state dyn", ["Ledger L", "grows · dynamic"]);
  s += node("drop", 915, 420, 185, 56, "proc key", ["Drop V, keep d", "or block if inseparable"]);
  s += node("gate", 700, 410, 152, 76, "gate", ["run?"], { diamond: true });
  s += node("exec", 470, 420, 172, 56, "proc ok", ["Execute the call", "tool runs"]);
  s += node("obs", 215, 420, 190, 56, "proc", ["Observation", "credentials redacted"]);
  s += node("blocked", 700, 514, 170, 44, "proc alt", ["Not executed"]);
  return s + "</svg>";
}
host.innerHTML = '<p class="vz-obs">Authority is fixed once per run; every tool call is split into operations and checked against it, and only allowed parts run.</p>' +
  '<div class="vz-scroll" tabindex="0" aria-label="System diagram; scroll sideways on small screens">' + svg() + "</div>" +
  '<p class="vz-key"><span><i class="k-ctl"></i>control flow</span><span><i class="k-data"></i>reads / writes state</span><span><i class="k-fixed"></i>fixed state</span><span><i class="k-dyn"></i>dynamic state</span><span><i class="k-alt"></i>not executed</span><span class="muted">Select a part for its definition, algorithm line, code and case step.</span></p>' +
  '<div class="vz-detail" id="sysDetail" aria-live="polite"></div>';
var sv = host.querySelector("svg.sys"), cur = null;
function show(id) {
  cur = cur === id ? null : id;
  VZ.mark(sv, cur ? [cur] : [], "sel");
  var el = document.getElementById("sysDetail"), x = INFO[cur];
  if (!x) { el.innerHTML = ""; return; }
  el.innerHTML = "<h4>" + esc(x[0]) + "</h4><p>" + esc(x[1]) + "</p>" +
    '<dl><dt>Paper</dt><dd>' + esc(x[2]) + "</dd><dt>Code</dt><dd><code>" + esc(x[3]) + "</code> · " + COMMIT + "</dd>" +
    "<dt>Case</dt><dd>" + (x[4] ? '<button type="button" class="linkish" data-jump="' + x[4][1] + '" data-back="Method"' + (x[4][2].stage != null ? ' data-stage="' + x[4][2].stage + '"' : "") + (x[4][2].pick ? ' data-pick="' + x[4][2].pick + '"' : "") + ">" + esc(x[4][0]) + " →</button>" : "") + (x[5] ? " " + tag("unk") + esc(x[5]) : "") + "</dd></dl>";
}
VZ.bindNodes(sv, show);
window.VZ.showSys = show;
})();
