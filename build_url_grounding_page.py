#!/usr/bin/env python3
"""Render the URL grounding comparison page.

Data comes from the scratchpad experiment; this file only lays it out. Kept
alongside the page so the numbers on it can be traced back to a run.
"""
import json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE/'url-grounding-review'
# The experiment lives in a session scratchpad that gets cleaned up, so the
# committed copy is the fallback and the page stays buildable without it.
SRC = Path('/private/tmp/claude-501/-Users-sophie/19cfc553-fa68-44f0-a263-e5daa2f70645'
           '/scratchpad/url_review_data.json')
if SRC.exists():
    data = json.loads(SRC.read_text(encoding='utf-8'))
    shutil.copy(SRC, OUT/'data.json')
else:
    data = json.loads((OUT/'data.json').read_text(encoding='utf-8'))

n_rows = len(data)
n_claims = len({d['cid'] for d in data})
n_judged = sum(1 for d in data if d['judged'])
art_ok = sum(1 for d in data if any(c['v'] == 'ok' for c in d['cands']))
ext_ok = sum(1 for d in data if d['extv'] == 'ok')

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MCFC Bench — URL Grounding Review</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:#fafbfc; --card:#ffffff; --ink:#101828; --ink2:#475467; --ink3:#98a2b3;
  --line:#eaecf0; --accent:#e8590c; --info:#175cd3; --info-soft:#eff8ff;
  --ok:#067647; --ok-soft:#ecfdf3; --no:#b42318; --no-soft:#fef3f2;
  --na:#854708; --na-soft:#fffaeb;
  --shadow:0 1px 3px rgba(16,24,40,.07),0 1px 2px rgba(16,24,40,.04);
}
[data-theme="dark"] {
  --bg:#0c111d; --card:#161b26; --ink:#f5f5f6; --ink2:#94969c; --ink3:#61646c;
  --line:#1f242f; --accent:#ff692e; --info:#84adff; --info-soft:#0e1f3d;
  --ok:#75e0a7; --ok-soft:#053321; --no:#fda29b; --no-soft:#55160c;
  --na:#fec84b; --na-soft:#4e1d09;
  --shadow:0 1px 3px rgba(0,0,0,.4);
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans",-apple-system,"PingFang SC",sans-serif;font-size:15px;line-height:1.6}
nav{display:flex;align-items:center;gap:32px;padding:0 40px;height:64px;border-bottom:1px solid var(--line);background:var(--card);position:sticky;top:0;z-index:20}
.brand{font-family:"Plus Jakarta Sans",sans-serif;font-weight:800;font-size:20px;letter-spacing:-.02em}
.navlinks{display:flex;gap:28px;margin-left:auto;font-weight:500;color:var(--ink2);font-size:14.5px}
.navlinks a{color:inherit;text-decoration:none}
.navlinks a.on{color:var(--accent);font-weight:600}
#themeBtn{margin-left:20px;background:none;border:none;font-size:18px;cursor:pointer;color:var(--ink2)}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
h1{font-family:"Plus Jakarta Sans",sans-serif;font-weight:800;font-size:34px;letter-spacing:-.03em;margin:40px 0 10px}
.lede{color:var(--ink2);max-width:760px;margin-bottom:26px}
.lede b{color:var(--ink)}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:8px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 18px;box-shadow:var(--shadow)}
.stat .n{font-family:"Plus Jakarta Sans",sans-serif;font-weight:700;font-size:22px}
.stat .l{color:var(--ink3);font-size:12.5px}
.note{background:var(--info-soft);border:1px solid var(--line);border-left:3px solid var(--info);border-radius:10px;padding:14px 18px;margin:22px 0;color:var(--ink2);font-size:14px}
.note b{color:var(--ink)}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:26px 0 18px;padding-top:20px;border-top:1px solid var(--line)}
select,input{font-family:inherit;font-size:14px;padding:8px 12px;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink)}
input{flex:1;min-width:220px}
.count{margin-left:auto;color:var(--ink3);font-size:13px;font-family:"JetBrains Mono",monospace}
.row{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);padding:20px 22px;margin-bottom:16px}
.rhead{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;margin-bottom:10px}
.cid{font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--ink3)}
.tag{font-size:11.5px;font-weight:600;padding:2px 9px;border-radius:999px;background:var(--info-soft);color:var(--info)}
.stmt{font-weight:600;margin-bottom:8px}
.span{border-left:2px solid var(--line);padding-left:12px;color:var(--ink2);font-size:13.5px;margin-bottom:16px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:860px){.cols{grid-template-columns:1fr}}
.col{border:1px solid var(--line);border-radius:11px;padding:14px 16px}

.ctitle{font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--ink3);margin-bottom:10px}
.cand{padding:10px 0;border-top:1px dashed var(--line)}
.cand:first-of-type{border-top:none;padding-top:0}
.u{font-family:"JetBrains Mono",monospace;font-size:12px;word-break:break-all;line-height:1.5}
.u a{color:var(--info);text-decoration:none}
.u a:hover{text-decoration:underline}
.meta2{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-bottom:5px}
.pos{font-family:"JetBrains Mono",monospace;font-size:10.5px;font-weight:600;padding:1px 7px;border-radius:5px;background:var(--info-soft);color:var(--info)}
.v{font-size:10.5px;font-weight:700;padding:1px 8px;border-radius:999px}
.v.ok{background:var(--ok-soft);color:var(--ok)}
.v.no{background:var(--no-soft);color:var(--no)}
.v.na{background:var(--na-soft);color:var(--na)}
.anch{font-size:12.5px;color:var(--ink2);margin-top:4px}
.anch em{color:var(--ink);font-style:normal;font-weight:600}
.ctx{font-size:12.5px;color:var(--ink3);margin-top:5px;line-height:1.55}
.ba{display:flex;align-items:stretch;gap:14px;margin:8px 0 22px;flex-wrap:wrap}
.bacell{flex:1;min-width:210px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 20px;box-shadow:var(--shadow)}
.bacell.ok{border-color:var(--ok);background:var(--ok-soft)}
.bal{font-size:11.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--ink3)}
.ban{font-family:"Plus Jakarta Sans",sans-serif;font-weight:800;font-size:34px;letter-spacing:-.02em;line-height:1.2}
.bacell.ok .ban{color:var(--ok)}
.bad{color:var(--ink2);font-size:13px}
.baarrow{display:flex;align-items:center;font-size:26px;color:var(--ink3)}
.note.warn{background:var(--na-soft);border-left-color:var(--na)}
.col.before{background:var(--no-soft);border-color:var(--line)}
.col.after{background:var(--ok-soft);border-color:var(--ok)}
.picked{font-size:11.5px;font-weight:700;color:var(--ok);margin-bottom:8px}
.col.pending .picked{color:var(--ink3);font-weight:600}
.col.nofix{background:var(--bg);border-color:var(--line)}
.alts{margin-top:12px;border-top:1px dashed var(--line);padding-top:10px}
.alts summary{cursor:pointer;font-size:12.5px;color:var(--ink3)}
.alts .cand{padding-left:12px;border-left:2px solid var(--line);margin-top:8px;border-top:none}
.foot{margin:50px 0 80px;padding-top:20px;border-top:1px solid var(--line);color:var(--ink3);font-size:13px}
</style>
</head>
<body>
<nav><span class="brand">MCFC Bench</span>
<div class="navlinks"><a href="../">Home</a><a href="../veritas-intake-review/">VeriTaS Intake</a><a href="../original-pipeline-review/">Original Pipeline</a><a href="#" class="on">URL Grounding</a></div>
<button id="themeBtn">🌙</button></nav>
<div class="wrap">
<h1>URL Grounding Review</h1>
<p class="lede">Half the evidence in this batch was grounded by searching the open web, because
extraction returned those statements without a source URL. The fact-checking articles they came
from still contained usable hyperlinks nobody looked at. <b>Each row is one such statement: the URL
the pipeline shipped, and the article hyperlink that replaces it.</b> The replacement is chosen by
shortlisting the three best candidates in the article and keeping whichever one verification
accepts, not by trusting the top-ranked guess.</p>

<div class="ba">
  <div class="bacell"><div class="bal">Before</div><div class="ban">52.0%</div>
    <div class="bad">184 of 354 evidence items grounded by open-web search</div></div>
  <div class="baarrow">&rarr;</div>
  <div class="bacell ok"><div class="bal">After</div><div class="ban">7.6%</div>
    <div class="bad">157 of those 184 resolve to a link the article already had, leaving 27</div></div>
</div>

<div class="stats">
  <div class="stat"><div class="n">__ROWS__</div><div class="l">statements re-grounded to an article link</div></div>
  <div class="stat"><div class="n">__CLAIMS__ / 85</div><div class="l">claims in the intake batch affected</div></div>
  <div class="stat"><div class="n">__JUDGED__</div><div class="l">rows independently verified</div></div>
  <div class="stat"><div class="n">11 vs 8</div><div class="l">verified support: article link vs web search</div></div>
</div>

<div class="note warn"><b>Why three candidates and not one.</b> Of the 11 verified rows where an
article link establishes the statement, only <b>3</b> were the top-ranked candidate. Six were
ranked second and two third. Ranking by position in the document is not reliable enough to pick
blind, so the shortlist goes to verification and the winner is whatever survives. Every row shows
the candidates that were not selected, so the ranking failures stay visible.</div>

<div class="note"><b>The two sources are complementary, not interchangeable.</b> Across the 42
verified rows the article link supports 11 times and web search 8, but they agree on only 2. Nine
statements are established by the article link where web search failed, and six the other way. That
is why web search stays in the pipeline as a fallback, triggered by failed verification rather than
by the absence of an article candidate.</div>

<div class="note"><b>Reading the verdicts.</b> A judge fetched each page and had to quote one
sentence establishing the statement on its own. <span class="v ok">supports</span> it found one,
<span class="v no">no</span> the page is only on topic, <span class="v na">unfetchable</span> the
page blocked the fetch. The 115 rows without verdicts show their shortlist as proposed, not proven.</div>

<div class="note"><b>Where the link sits</b> relative to the sentence the statement came from:
<span class="pos">SPAN</span> inside it, <span class="pos">SENT</span> same sentence,
<span class="pos">PARA</span> same paragraph, <span class="pos">ADJ</span> next paragraph,
<span class="pos">SECT</span> same section, <span class="pos">FAR</span> elsewhere. Most are far,
which is why proximity alone does not pick the right one.</div>

<div class="controls">
  <select id="f1">
    <option value="all">All rows</option>
    <option value="judged">Verified only</option>
    <option value="artwin">Article link verified to support</option>\n    <option value="rescue">Article link works where web search failed</option>\n    <option value="notrank1">Winner was not the top-ranked candidate</option>
    <option value="extwin">Web search supports</option>
    <option value="near">Link is in or beside the sentence</option>
  </select>
  <select id="sort">
    <option value="default">Verified first</option>
    <option value="cid">By claim id</option>
  </select>
  <input id="q" placeholder="Search statement, URL or domain">
  <span class="count" id="count"></span>
</div>
<div id="list"></div>
<div class="foot">VeriTaS intake batch, 2026-09. Article markup re-parsed into sections,
paragraphs and sentences; page furniture, the outlet's own domain and the claim's appearance
URLs are excluded from candidates. Verification used a single fixed judge and rubric across
both columns.</div>
</div>
<script>
const DATA = __DATA__;
const esc = s => (s||"").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const short = u => { try { const x = new URL(u); return x.hostname.replace(/^www\\./,"") + x.pathname; } catch(e) { return u; } };
const vlabel = {ok:"supports", no:"no", na:"unfetchable"};
const NEAR = new Set(["SPAN","SENT","PARA"]);

function cand(c){
  return `<div class="cand">
    <div class="meta2"><span class="pos">${esc(c.p)}</span>${c.v?`<span class="v ${c.v}">${vlabel[c.v]}</span>`:""}</div>
    <div class="u"><a href="${esc(c.u)}" target="_blank" rel="noopener">${esc(short(c.u))}</a></div>
    ${c.a?`<div class="anch">anchor: <em>${esc(c.a)}</em></div>`:""}
    ${c.c?`<div class="ctx">${esc(c.c)}</div>`:""}
  </div>`;
}
function pickOf(d){
  for (let i = 0; i < d.cands.length; i++) if (d.cands[i].v === "ok") return {c: d.cands[i], rank: i+1};
  return null;
}
function row(d){
  const pick = pickOf(d);
  const rest = d.cands.filter(c => !pick || c !== pick.c);
  let after;
  if (pick) {
    after = `<div class="picked">kept by verification &middot; ranked #${pick.rank} of ${d.cands.length}</div>` + cand(pick.c);
  } else if (d.judged) {
    after = `<div class="ctx">None of the ${d.cands.length} article candidates established the statement, so this row still falls back to web search.</div>`;
  } else {
    after = `<div class="picked">shortlist, not yet verified</div>` + d.cands.map(cand).join("");
  }
  const showRest = pick || (d.judged && d.cands.length);
  return `<div class="row">
    <div class="rhead"><span class="cid">claim ${esc(d.cid)}</span>
      ${d.stype?`<span class="tag">${esc(d.stype)}</span>`:""}
      ${d.judged?`<span class="tag">verified</span>`:""}
      <span class="cid"><a href="${esc(d.art)}" target="_blank" rel="noopener" style="color:inherit">source article &#8599;</a></span></div>
    <div class="stmt">${esc(d.stmt)}</div>
    ${d.span?`<div class="span">derived from: ${esc(d.span)}</div>`:""}
    <div class="cols">
      <div class="col before">
        <div class="ctitle">Before &mdash; open web search</div>
        <div class="cand">
          <div class="meta2">${d.extv?`<span class="v ${d.extv}">${vlabel[d.extv]}</span>`:""}</div>
          <div class="u"><a href="${esc(d.ext)}" target="_blank" rel="noopener">${esc(short(d.ext))}</a></div>
          ${d.extq?`<div class="ctx">quoted: ${esc(d.extq)}</div>`:""}
        </div>
      </div>
      <div class="col ${pick?"after":(d.judged?"nofix":"after pending")}">
        <div class="ctitle">After &mdash; link from the article</div>
        ${after}
      </div>
    </div>
    ${showRest && rest.length?`<details class="alts"><summary>${rest.length} candidate${rest.length>1?"s":""} not selected</summary>${rest.map(cand).join("")}</details>`:""}
  </div>`;
}
function render(){
  const f = f1.value, s = sort.value, term = q.value.trim().toLowerCase();
  let list = DATA.filter(d => {
    if (f === "judged" && !d.judged) return false;
    const pk = pickOf(d);
    if (f === "artwin" && !pk) return false;
    if (f === "rescue" && !(pk && d.extv !== "ok")) return false;
    if (f === "notrank1" && !(pk && pk.rank > 1)) return false;
    if (f === "extwin" && d.extv !== "ok") return false;
    if (f === "near" && !d.cands.some(c => NEAR.has(c.p))) return false;
    if (term) {
      const hay = (d.stmt + " " + d.ext + " " + d.cands.map(c => c.u).join(" ")).toLowerCase();
      if (!hay.includes(term)) return false;
    }
    return true;
  });
  if (s === "cid") list = list.slice().sort((a,b) => a.cid.localeCompare(b.cid));
  count.textContent = `${list.length} / ${DATA.length} rows`;
  document.getElementById("list").innerHTML = list.map(row).join("") ||
    `<div class="row" style="color:var(--ink3)">Nothing matches.</div>`;
}
[f1, sort, q].forEach(el => el.addEventListener("input", render));
render();
const btn = document.getElementById("themeBtn");
function setTheme(t){document.documentElement.setAttribute("data-theme",t);btn.textContent=t==="dark"?"☀️":"🌙";localStorage.setItem("mcfc_theme",t)}
btn.onclick = () => setTheme(document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark");
setTheme(localStorage.getItem("mcfc_theme")||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"));
</script>
</body></html>
"""

html = (HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False))
            .replace('__CLAIMS__', str(n_claims)).replace('__ROWS__', str(n_rows))
            .replace('__JUDGED__', str(n_judged))
            .replace('__ARTOK__', str(art_ok)).replace('__EXTOK__', str(ext_ok)))
(OUT/'index.html').write_text(html, encoding='utf-8')
print(f'wrote url-grounding-review/index.html  {len(html):,} bytes')
print(f'  {n_rows} rows, {n_claims} claims, {n_judged} verified, article {art_ok} vs web {ext_ok}')
