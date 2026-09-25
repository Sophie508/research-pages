#!/usr/bin/env python3
"""Build the Annotation Demo page from annotation-demo/data.json.

data.json is exported from the annotation submissions (see the human_eval
package): every claim whose pipeline verdict at least one annotator confirmed,
with that claim's evidence and whatever each annotator flagged on it.
Annotators are anonymised to A and B; the page is public and who judged what
is not the point.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "annotation-demo"
rows = json.loads((OUT / "data.json").read_text(encoding="utf-8"))

n_text = sum(1 for r in rows if r["kind"] == "text")
n_img = len(rows) - n_text
n_ev = sum(len(r["ev"]) for r in rows)
n_flag = sum(1 for r in rows for e in r["ev"] for m in e["marks"] if m["sf"] or m["uf"] or m["dead"])
n_split = sum(1 for r in rows if len({a["verdict"] for a in r["annotations"]}) > 1)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MCFC Bench — Annotation Demo</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:#fafbfc; --card:#ffffff; --ink:#101828; --ink2:#475467; --ink3:#98a2b3;
  --line:#eaecf0; --accent:#e8590c; --info:#175cd3; --info-soft:#eff8ff;
  --ok:#067647; --ok-soft:#ecfdf3; --warn:#b54708; --warn-soft:#fffaeb;
  --shadow:0 1px 3px rgba(16,24,40,.07),0 1px 2px rgba(16,24,40,.04);
}
[data-theme="dark"] {
  --bg:#0c111d; --card:#161b26; --ink:#f5f5f6; --ink2:#94969c; --ink3:#61646c;
  --line:#1f242f; --accent:#ff692e; --info:#84adff; --info-soft:#0e1f3d;
  --ok:#75e0a7; --ok-soft:#053321; --warn:#fec84b; --warn-soft:#4e1d09;
  --shadow:0 1px 3px rgba(0,0,0,.4);
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans",-apple-system,"PingFang SC",sans-serif;font-size:15px;line-height:1.6}
nav{display:flex;align-items:center;gap:32px;padding:0 40px;height:64px;border-bottom:1px solid var(--line);background:var(--card);position:sticky;top:0;z-index:5}
.brand{font-family:"Plus Jakarta Sans",sans-serif;font-weight:800;font-size:20px;letter-spacing:-.02em}
.navlinks{display:flex;gap:28px;margin-left:auto;font-weight:500;color:var(--ink2);font-size:14.5px;flex-wrap:wrap}
.navlinks a{color:inherit;text-decoration:none}
.navlinks a.on{color:var(--accent);font-weight:600}
#themeBtn{margin-left:20px;background:none;border:none;font-size:18px;cursor:pointer;color:var(--ink2)}
.hero{text-align:center;padding:56px 24px 8px}
h1{font-family:"Plus Jakarta Sans",sans-serif;font-weight:800;font-size:40px;letter-spacing:-.03em}
.wrap{max-width:980px;margin:0 auto;padding:0 24px 90px}
.note{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);padding:22px 26px;margin:28px 0 18px;color:var(--ink2);font-size:14.5px}
.note b{color:var(--ink)}
.controls{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:0 0 18px;font-size:13.5px;color:var(--ink2)}
.controls select{font-family:inherit;font-size:13.5px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
.count{font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--ink3);margin-left:auto}
.claim{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);padding:22px 26px;margin-bottom:16px}
.claim h2{font-family:"Plus Jakarta Sans",sans-serif;font-weight:700;font-size:17.5px;line-height:1.45;margin-bottom:10px}
.meta{display:flex;gap:10px;flex-wrap:wrap;font-family:"JetBrains Mono",monospace;font-size:11.5px;color:var(--ink3);margin-bottom:14px}
.chip{padding:2px 10px;border-radius:999px;font-family:"DM Sans";font-size:12px;font-weight:600;background:var(--info-soft);color:var(--info)}
.chip.ok{background:var(--ok-soft);color:var(--ok)}
.chip.warn{background:var(--warn-soft);color:var(--warn)}
.shot{margin:0 0 14px}
.shot img{max-width:100%;max-height:300px;border-radius:10px;border:1px solid var(--line)}
.verdicts{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.vbox{flex:1;min-width:190px;border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.vbox .lab{font-family:"JetBrains Mono",monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3)}
.vbox .val{font-weight:600;margin-top:3px}
.vbox .why{color:var(--ink2);font-size:13px;margin-top:6px}
.grp{font-family:"JetBrains Mono",monospace;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3);margin:18px 0 8px}
.ev{border-top:1px solid var(--line);padding:12px 0}
.ev .eid{font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--accent);font-weight:600}
.ev a{color:var(--info);font-size:13px;text-decoration:none}
.ev a:hover{text-decoration:underline}
.flags{margin-top:7px;display:flex;flex-direction:column;gap:4px}
.flag{font-size:12.5px;color:var(--warn);background:var(--warn-soft);border-radius:8px;padding:4px 10px;align-self:flex-start}
.foot{color:var(--ink3);font-size:13px;text-align:center;margin-top:34px}
@media (max-width:720px){nav{padding:0 16px;height:auto;flex-wrap:wrap;gap:12px;padding-top:12px;padding-bottom:12px}
  .navlinks{margin-left:0;gap:16px;font-size:13.5px}h1{font-size:30px}.wrap{padding:0 16px 60px}}
</style>
</head>
<body>
<nav><span class="brand">MCFC Bench</span>
<div class="navlinks"><a href="../">Home</a><a href="../veritas-intake-review/">VeriTaS Intake</a><a href="../averitec-averimatec-review/">AVeriTeC + AVerImaTeC</a><a href="../deepfake-filter/">Deep Fake Filter</a><a href="../baseline-reproduce/">Baseline Reproduce</a><a href="#" class="on">Annotation Demo</a></div>
<button id="themeBtn">🌙</button></nav>
<div class="hero"><h1>Annotation Demo</h1></div>
<div class="wrap">
<div class="controls">
  <label>Set: <select id="fKind"><option value="">All</option><option value="text">Text claims</option><option value="image">Image claims</option></select></label>
  <label>Verdict: <select id="fV"><option value="">All</option><option value="supported">supported</option><option value="refuted">refuted</option><option value="not_enough_evidence">not enough evidence</option></select></label>
  <label>Flags: <select id="fF"><option value="">All</option><option value="yes">Only claims with a flagged evidence item</option></select></label>
  <span class="count" id="count"></span>
</div>
<div id="list"></div>
<div class="foot">Annotator identities are not shown. The interface these annotations were made in is linked from the home page.</div>
</div>
<script>
const DATA = __DATA__;
const VLAB = {supported:"supported", refuted:"refuted", not_enough_evidence:"not enough evidence"};
const esc = s => String(s??"").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const host = u => { try { return new URL(u).hostname.replace(/^www\\./,""); } catch { return u; } };

function flagsOf(e) {
  const out = [];
  for (const m of e.marks) {
    const who = e.marks.length > 1 ? `Annotator ${m.by}: ` : "";
    for (const f of m.sf) out.push(who + f);
    for (const f of m.uf) out.push(who + f);
    if (m.dead) out.push(who + "The source page did not load.");
    if (m.dup) out.push(who + "Duplicate of " + m.dup.toUpperCase() + ".");
  }
  return out;
}

function card(r) {
  const split = new Set(r.annotations.map(a => a.verdict)).size > 1;
  const shots = r.imgs.map(p => `<div class="shot"><img src="${esc(p)}" alt=""></div>`).join("");
  const boxes = r.annotations.map(a => `<div class="vbox">
      <div class="lab">Annotator ${esc(a.by)}</div>
      <div class="val">${esc(VLAB[a.verdict] || a.verdict)} ${a.agrees ? '<span class="chip ok">matches pipeline</span>' : '<span class="chip warn">differs</span>'}</div>
      ${a.reasoning ? `<div class="why">${esc(a.reasoning)}</div>` : ""}
    </div>`).join("");
  const ev = r.ev.map(e => {
    const fl = flagsOf(e);
    return `<div class="ev"><div><span class="eid">${esc(e.eid.toUpperCase())}</span> ${esc(e.s)}</div>
      ${e.u ? `<a href="${esc(e.u)}" target="_blank" rel="noopener">${esc(host(e.u))} ↗</a>` : ""}
      ${fl.length ? `<div class="flags">${fl.map(f => `<span class="flag">${esc(f)}</span>`).join("")}</div>` : ""}</div>`;
  }).join("");
  return `<div class="claim">
    <h2>${esc(r.claim)}</h2>
    <div class="meta"><span>${esc(r.id)}</span>${r.date ? `<span>claimed ${esc(r.date)}</span>` : ""}
      <span class="chip">${r.kind === "image" ? "image claim" : "text claim"}</span>
      <span class="chip">${r.ev.length} evidence</span>
      ${split ? '<span class="chip warn">annotators split</span>' : ""}</div>
    ${shots}
    <div class="verdicts">
      <div class="vbox"><div class="lab">Pipeline</div><div class="val">${esc(VLAB[r.pipeline] || r.pipeline)}</div></div>
      ${boxes}
    </div>
    <div class="grp">Evidence as the pipeline extracted it</div>
    ${ev}</div>`;
}

function render() {
  const k = document.getElementById("fKind").value;
  const v = document.getElementById("fV").value;
  const f = document.getElementById("fF").value;
  const rows = DATA.filter(r => (!k || r.kind === k) && (!v || r.pipeline === v) &&
    (!f || r.ev.some(e => flagsOf(e).length)));
  document.getElementById("list").innerHTML = rows.map(card).join("") ||
    '<div class="note">No claim matches these filters.</div>';
  document.getElementById("count").textContent =
    `${rows.length} of ${DATA.length} claims · ${rows.reduce((n, r) => n + r.ev.length, 0)} evidence`;
}
for (const id of ["fKind", "fV", "fF"]) document.getElementById(id).onchange = render;
render();

const btn = document.getElementById("themeBtn");
function setTheme(t){document.documentElement.setAttribute("data-theme",t);btn.textContent=t==="dark"?"☀️":"🌙";localStorage.setItem("mcfc_theme",t)}
btn.onclick=()=>setTheme(document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark");
setTheme(localStorage.getItem("mcfc_theme")||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"));
</script>
</body></html>
"""

html = HTML.replace("__DATA__", json.dumps(rows, ensure_ascii=False))
(OUT / "index.html").write_text(html, encoding="utf-8")
print(f"wrote {OUT/'index.html'}: {len(rows)} claims ({n_text} text, {n_img} image), "
      f"{n_ev} evidence, {n_flag} flagged, {n_split} split")
