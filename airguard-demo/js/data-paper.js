/* Facts transcribed by hand from the presented paper version and the AIRGuard repo's ledgers.
 * Paper: "AIRGuard: Guarding Agent Actions with Runtime Authority Control", WWW '27 submission #7481,
 * local PDF 7481_AIRGuard_Guarding_Agent_A.pdf (12 pages, md5 d7883f88247d808f71dd56ddda5e8bb2).
 * "L123" = the margin line number in that PDF. Table 1 was checked cell by cell against a 220-dpi render.
 */
window.PAPER = (function () {
"use strict";
var MODELS = ["Haiku 4.5", "Sonnet 4.6", "Opus 4.8", "GPT-5.6 Sol", "GPT-6 Luna", "GPT-6 Astra"];
var DEFS = ["No defense", "ARGUS", "MELON", "CaMeL", "VIGIL", "AIRGuard"];
// [DTAP ASR, DTAP UPR, DTAP tokens(M), AgentTrap ASR, AgentTrap UPR, AgentTrap tokens(M)] per defense, per model
var T1 = {
  "Haiku 4.5":   [[5.0, 52.0, 6.2, 19.8, 36.0, 10.4], [1.0, 50.0, 10.8, 20.9, 42.0, 59.6], [4.0, 54.0, 19.7, 23.1, 44.0, 41.2], [4.0, 34.0, 3.1, 2.2, 10.0, 2.3], [0.0, 24.0, 31.2, 4.4, 22.0, 34.6], [1.0, 44.0, 5.1, 13.2, 40.0, 10.9]],
  "Sonnet 4.6":  [[1.0, 86.0, 11.1, 17.6, 44.0, 8.4], [4.0, 64.0, 16.0, 13.2, 30.0, 18.7], [3.0, 60.0, 19.1, 7.7, 30.0, 13.7], [0.0, 40.0, 3.0, 2.2, 4.0, 1.7], [0.0, 28.0, 35.9, 2.2, 18.0, 23.1], [1.0, 84.0, 10.4, 7.7, 52.0, 6.5]],
  "Opus 4.8":    [[3.0, 80.0, 8.5, 17.6, 46.0, 6.8], [1.0, 72.0, 10.3, 16.5, 46.0, 16.0], [1.0, 72.0, 9.8, 16.5, 50.0, 12.8], [4.0, 34.0, 2.6, 2.2, 18.0, 1.4], [1.0, 46.0, 43.8, 6.6, 22.0, 26.3], [2.0, 70.0, 10.9, 7.7, 42.0, 5.0]],
  "GPT-5.6 Sol": [[19.0, 88.0, 31.2, 20.9, 60.0, 15.8], [26.0, 80.0, 32.2, 19.8, 46.0, 51.9], [24.0, 80.0, 32.5, 23.1, 54.0, 33.5], [16.0, 36.0, 7.3, 2.2, 6.0, 5.2], [18.0, 34.0, 91.9, 9.9, 14.0, 57.1], [9.0, 70.0, 31.2, 7.7, 62.0, 17.5]],
  "GPT-6 Luna":  [[2.0, 64.0, 20.6, 13.2, 50.0, 17.9], [1.0, 66.0, 16.5, 13.2, 38.0, 35.6], [1.0, 74.0, 18.3, 17.6, 36.0, 23.3], [3.0, 30.0, 5.1, 3.3, 6.0, 4.5], [4.0, 28.0, 47.4, 7.7, 18.0, 32.1], [0.0, 46.0, 50.3, 4.4, 30.0, 28.1]],
  "GPT-6 Astra": [[18.0, 86.0, 23.3, 14.3, 44.0, 17.3], [11.0, 80.0, 24.4, 13.2, 42.0, 47.1], [15.0, 72.0, 22.3, 15.4, 32.0, 25.9], [26.0, 34.0, 8.1, 2.2, 6.0, 5.1], [15.0, 28.0, 82.9, 7.7, 26.0, 44.5], [10.0, 70.0, 25.7, 11.0, 48.0, 15.7]]
};
function cell(model, def, col) { return T1[model][DEFS.indexOf(def)][col]; }
var BENCH = {
  agenttrap: { name: "AgentTrap", asrCol: 3, uprCol: 4, tokCol: 5, nAtk: 91, nBen: 50,
    asrDef: "攻击成功率：91 个攻击里，benchmark 判为 L2（攻击生效）的比例。越低越好。", uprDef: "正常任务完成率：50 个正常任务里，LLM judge 判为完成的比例。越高越好。", src: "§4.1 L572–576；附录 B L1357–1366" },
  dtap: { name: "DTAP-150", asrCol: 0, uprCol: 1, tokCol: 2, nAtk: 100, nBen: 50,
    asrDef: "攻击成功率：100 个攻击（50 个直接、50 个间接）里，DTAP 自带 judge 判为攻击成功的比例。越低越好。", uprDef: "正常任务完成率：50 个正常任务里，DTAP 自带 judge 判为完成的比例。越高越好。", src: "§4.1 L567–576；附录 B L1357–1366" }
};
return {
  version: { label: "WWW '27 投稿版 #7481", file: "7481_AIRGuard_Guarding_Agent_A.pdf", pages: 12, md5: "d7883f88247d808f71dd56ddda5e8bb2" },
  MODELS: MODELS, DEFS: DEFS, T1: T1, cell: cell, BENCH: BENCH,
  T2: [["No defense", 20.9], ["Prompt-only AIRGuard", 17.6], ["Full AIRGuard", 7.7]],
  fig1a: [["AgentDojo", 0.0], ["AgentLAB", 0.0], ["INFUSE", 0.5], ["DTAP", 13.7], ["AgentTrap", 23.1]],
  // Figure 1b: values the text states (L139–142); the remaining points are read off the plot and only shown as text.
  fig1b: { none: [17, 22], argusLong: 37, melonLong: 35 },
  finding1: { runs: 74, intervened: 46, execBlock: 39, graphStartup: 3, ccDrop: 1, tag: 1, deletion: 1, seq: 1, noAction: 28, argusApproved: [147, 175], melonApproved: [186, 215] },
  finding2: { blocked: 27, calls: 1168, runsTouched: 15, benignRuns: 300, camelFail: 112, camelHalt: 82, camelInsufficient: 16, vigilFail: 76, vigilVerifier: 17 },
  dtapIndirect: { none: [9, 300], airguard: [4, 300] }
};
})();
