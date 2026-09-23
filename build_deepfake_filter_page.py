#!/usr/bin/env python3
"""Build the Deep Fake Filter page: the VeriTaS claims whose media VeriTaS
itself labelled fabricated.

Selection is one rule and nothing else: the claim has media, and at least one
medium's authenticity label from the VeriTaS 4-model ensemble starts with
"fabricated". Tags (AI-generated / Manipulated / Forged), confidence tiers and
the contextualization label are VeriTaS's own; the publisher's raw rating is
shown beside them as an independent signal but did not take part in selection.
No evidence extraction has been run on these claims yet.
"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent; OUT = HERE/'deepfake-filter'
data = json.loads((OUT/'data.json').read_text(encoding='utf-8'))
n = len(data); by_tag = {}
for d in data:
    for t in (d['tags'] or ['untagged']): by_tag[t] = by_tag.get(t, 0) + 1
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MCFC Bench — Deep Fake Filter</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#fafbfc;--card:#ffffff;--ink:#101828;--ink2:#475467;--ink3:#98a2b3;--line:#eaecf0;--accent:#e8590c;--info:#175cd3;--info-soft:#eff8ff;--ok:#067647;--ok-soft:#ecfdf3;--no:#b42318;--no-soft:#fef3f2;--na:#854708;--na-soft:#fffaeb;--shadow:0 1px 3px rgba(16,24,40,.07),0 1px 2px rgba(16,24,40,.04)}
[data-theme="dark"]{--bg:#0c111d;--card:#161b26;--ink:#f5f5f6;--ink2:#94969c;--ink3:#61646c;--line:#1f242f;--accent:#ff692e;--info:#84adff;--info-soft:#0e1f3d;--ok:#75e0a7;--ok-soft:#053321;--no:#fda29b;--no-soft:#55160c;--na:#fec84b;--na-soft:#4e1d09;--shadow:0 1px 3px rgba(0,0,0,.4)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans",-apple-system,"PingFang SC",sans-serif;font-size:15px;line-height:1.6}
nav{display:flex;align-items:center;gap:32px;padding:0 40px;height:64px;border-bottom:1px solid var(--line);background:var(--card);position:sticky;top:0;z-index:20}
.brand{font-family:"Plus Jakarta Sans",sans-serif;font-weight:800;font-size:20px;letter-spacing:-.02em}
.navlinks{display:flex;gap:28px;margin-left:auto;font-weight:500;color:var(--ink2);font-size:14.5px;flex-wrap:wrap}
.navlinks a{color:inherit;text-decoration:none}.navlinks a.on{color:var(--accent);font-weight:600}
#themeBtn{margin-left:20px;background:none;border:none;font-size:18px;cursor:pointer;color:var(--ink2)}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
h1{font-family:"Plus Jakarta Sans",sans-serif;font-weight:800;font-size:34px;letter-spacing:-.03em;margin:40px 0 10px}
.lede{color:var(--ink2);max-width:780px;margin-bottom:22px}.lede b{color:var(--ink)}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:8px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 18px;box-shadow:var(--shadow)}
.stat .n{font-family:"Plus Jakarta Sans",sans-serif;font-weight:700;font-size:22px}.stat .l{color:var(--ink3);font-size:12.5px}
.note{background:var(--info-soft);border:1px solid var(--line);border-left:3px solid var(--info);border-radius:10px;padding:14px 18px;margin:22px 0;color:var(--ink2);font-size:14px}.note b{color:var(--ink)}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:26px 0 18px;padding-top:20px;border-top:1px solid var(--line)}
select,input{font-family:inherit;font-size:14px;padding:8px 12px;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink)}
input{flex:1;min-width:220px}.count{margin-left:auto;color:var(--ink3);font-size:13px;font-family:"JetBrains Mono",monospace}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:16px;margin-bottom:80px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);overflow:hidden;display:flex;flex-direction:column}
.img{width:100%;aspect-ratio:16/10;object-fit:contain;background:#000;display:block}
.body{padding:16px 18px;display:flex;flex-direction:column;gap:9px}
.rhead{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
.cid{font-family:"JetBrains Mono",monospace;font-size:11.5px;color:var(--ink3)}
.tag{font-size:11px;font-weight:700;padding:2px 9px;border-radius:999px}
.tag.ai{background:var(--no-soft);color:var(--no)}.tag.man{background:var(--na-soft);color:var(--na)}.tag.forg{background:var(--info-soft);color:var(--info)}.tag.conf{background:var(--bg);color:var(--ink2);border:1px solid var(--line)}
.claim{font-weight:600;line-height:1.45}
.why{font-size:13px;color:var(--ink2);border-left:2px solid var(--line);padding-left:10px}
.meta{font-size:12.5px;color:var(--ink3);display:flex;flex-wrap:wrap;gap:6px 14px}
.meta a{color:var(--info);text-decoration:none}.meta a:hover{text-decoration:underline}
.rating{font-size:12px;color:var(--ink2)}.rating b{color:var(--ink)}
.foot{margin:50px 0 80px;padding-top:20px;border-top:1px solid var(--line);color:var(--ink3);font-size:13px}
</style></head>
<body>
<nav><span class="brand">MCFC Bench</span>
<div class="navlinks"><a href="../">Home</a><a href="../veritas-intake-review/">VeriTaS Intake</a><a href="../averitec-averimatec-review/">AVeriTeC + AVerImaTeC</a><a href="../baseline-reproduce/">Baseline Reproduce</a><a href="#" class="on">Deep Fake Filter</a></div>
<button id="themeBtn">🌙</button></nav>
<div class="wrap">
<h1>Deep Fake Filter</h1>
<p class="lede">Every claim in the VeriTaS export whose media VeriTaS itself judged to be fabricated. <b>Selection is one rule:</b> the claim carries media, and at least one medium's authenticity label from the VeriTaS four-model ensemble is "fabricated" at any confidence. Real media shown in a false context is not in this set; that is a contextualization failure, not a fabrication. Nothing here has been through evidence extraction yet: this page exists to look at what the set contains.</p>
<div class="stats">
  <div class="stat"><div class="n">__N__</div><div class="l">claims, of 197 in the export (143 with media verdicts)</div></div>
  <div class="stat"><div class="n">__AI__ / __MAN__ / __FORG__</div><div class="l">AI-generated / Manipulated / Forged (a claim can carry several)</div></div>
  <div class="stat"><div class="n">__CERT__ / __RC__ / __RU__</div><div class="l">certain / rather certain / rather uncertain</div></div>
</div>
<div class="note"><b>Signals shown, and which one selected.</b> The <b>VeriTaS authenticity label</b> did the selecting: score at or below &minus;1/3 on its &minus;1..+1 scale, mapped to the three confidence tiers in the export's own convention (certain &le; &minus;0.9, rather certain &le; &minus;2/3, rather uncertain &le; &minus;1/3). Two more signals are displayed but did <b>not</b> take part in selection: the <b>publisher's own rating text</b> from the fact-checking article, and the <b>contextualization label</b>, which says whether the claim also misrepresents what the media shows. Tags follow VeriTaS's definitions: AI-generated is synthesized by AI, Manipulated is a real recording altered to change its meaning, Forged is mostly or entirely a manual invention.</div>
<div class="controls">
  <select id="ftag"><option value="all">All tags</option><option value="AI-generated">AI-generated</option><option value="Manipulated">Manipulated</option><option value="Forged">Forged</option></select>
  <select id="fconf"><option value="all">All confidence</option><option value="certain">certain only</option><option value="rather certain">rather certain</option><option value="rather uncertain">rather uncertain</option></select>
  <select id="fctx"><option value="all">Any contextualization</option><option value="incorrect">also miscontextualized</option><option value="correct">context correct</option></select>
  <input id="q" placeholder="Search claim, publisher or rating">
  <span class="count" id="count"></span>
</div>
<div class="grid" id="grid"></div>
<div class="foot">Source: VeriTaS dataset export, downloaded 2026-09-08 (claims.json, 197 claims; images/). Authenticity, contextualization and veracity labels and explanations are VeriTaS's own. Media files are served from this page for review only.</div>
</div>
<script>
const DATA = __DATA__;
const esc = s => String(s||"").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const cls = t => t==="AI-generated"?"ai":t==="Manipulated"?"man":"forg";
function card(d){
  const img = d.imgs && d.imgs.length ? `<img class="img" src="media/${esc(d.imgs[0])}" loading="lazy" alt="">` : "";
  const tags = (d.tags.length?d.tags:["untagged"]).map(t=>`<span class="tag ${cls(t)}">${esc(t)}</span>`).join("");
  const rv = (d.reviews||[]).map(r=>`<a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.pub||"fact-check")} &#8599;</a>`).join(" ");
  const rating = (d.reviews||[]).filter(r=>r.rating).map(r=>`<b>${esc(r.rating)}</b>`).join(", ");
  const ap = (d.appearances||[]).slice(0,1).map(a=>`<a href="${esc(a)}" target="_blank" rel="noopener">original post &#8599;</a>`).join("");
  return `<div class="card">${img}<div class="body">
    <div class="rhead"><span class="cid">claim ${esc(d.id)}${d.date?" · "+esc(d.date):""}</span>${tags}<span class="tag conf">${esc(d.conf)} · ${d.score}</span></div>
    <div class="claim">${esc(d.claim)}</div>
    <div class="why">${esc(d.why)}</div>
    ${rating?`<div class="rating">publisher rating: ${rating}</div>`:""}
    <div class="meta"><span>veracity: ${esc(d.veracity||"n/a")}</span><span>context: ${esc((d.ctx||[]).join(", ")||"n/a")}</span>${rv}${ap}</div>
  </div></div>`;
}
function render(){
  const t=ftag.value, c=fconf.value, x=fctx.value, term=q.value.trim().toLowerCase();
  let list = DATA.filter(d => (t==="all"||d.tags.includes(t)) && (c==="all"||d.conf===c) &&
    (x==="all"||(d.ctx||[]).some(v=>v.startsWith(x))) &&
    (!term || (d.claim+" "+(d.reviews||[]).map(r=>(r.pub||"")+" "+(r.rating||"")).join(" ")).toLowerCase().includes(term)));
  count.textContent = `${list.length} / ${DATA.length} claims`;
  document.getElementById("grid").innerHTML = list.map(card).join("") || `<div class="card"><div class="body" style="color:var(--ink3)">Nothing matches.</div></div>`;
}
[ftag,fconf,fctx,q].forEach(el=>el.addEventListener("input",render)); render();
const btn=document.getElementById("themeBtn");
function setTheme(t){document.documentElement.setAttribute("data-theme",t);btn.textContent=t==="dark"?"☀️":"🌙";localStorage.setItem("mcfc_theme",t)}
btn.onclick=()=>setTheme(document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark");
setTheme(localStorage.getItem("mcfc_theme")||(matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"));
</script></body></html>
"""
conf = {k: sum(1 for d in data if d['conf']==k) for k in ('certain','rather certain','rather uncertain')}
html = (HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False)).replace('__N__', str(n))
        .replace('__AI__', str(by_tag.get('AI-generated',0))).replace('__MAN__', str(by_tag.get('Manipulated',0))).replace('__FORG__', str(by_tag.get('Forged',0)))
        .replace('__CERT__', str(conf['certain'])).replace('__RC__', str(conf['rather certain'])).replace('__RU__', str(conf['rather uncertain'])))
(OUT/'index.html').write_text(html, encoding='utf-8')
print(f'wrote deepfake-filter/index.html  {len(html):,} bytes  n={n}  tags={by_tag}  conf={conf}')
