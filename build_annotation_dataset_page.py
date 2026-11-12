#!/usr/bin/env python3
"""Build the Annotation Dataset page: the 2,000 claims selected for human annotation, plus the qualifying claims not selected,
by resource tier, language and type.

Reads analysis_outputs/annotation_dataset_export_<date>/ (claims.json and snapshots/, exported from
otakotak:/scratch/users/suliu/mcfc-settle/intake_text1200/ by export_dataset.py) and the selection in
analysis_outputs/annotation_2000_v1/claims_final.jsonl (select_2000.py). A claim qualifies if at least one evidence
statement survived the link stage and its claim, its fact-checking article or an evidence page is in the language.
Claim images and videos come from media.json and media/ beside the selection (build_media.py).
Evidence statements of the selected claims that were not in English are shown in the English of statement_translations.json
(translate_statements.py, check_translations.py), with the statement as extracted one click away.
Chinese claims that were report titles are shown in the wording of claim_normalization.json (stage_normalize_decon.py,
claim_normalization.py), with the title shown as the original.
Writes annotation-dataset/.
"""
import collections
import html as _html
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / 'veritas-intake-review/index.html'
OUT = HERE / 'annotation-dataset'
SRC = Path('/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs/annotation_dataset_export_20261111')
SEL = Path('/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs/annotation_2000_v1/claims_final.jsonl')
MEDIA = SEL.parent / 'media.json'  # build_media.py; images sit in SEL.parent / 'media'
AS_OF = '2026-11-13'
TIERS = {'English': 'High', 'Chinese': 'High', 'Hindi': 'Medium', 'Arabic': 'Medium', 'Tamil': 'Low', 'Indonesian': 'Low'}
QUOTA = {'High': 250, 'Medium': 150, 'Low': 100}
VERITAS = 'https://veritas.mai.informatik.tu-darmstadt.de/claims/'
esc = lambda t: _html.escape(str(t or ''))

rows = json.loads((SRC / 'claims.json').read_text(encoding='utf-8'))
sel = {json.loads(l)['claim_id']: json.loads(l)['script'] for l in SEL.open(encoding='utf-8')}
rest = {json.loads(l)['claim_id'] for l in (SEL.parent / 'not_selected.jsonl').open(encoding='utf-8')}
third = SEL.parent / 'excluded_third_language.jsonl'  # claims with an evidence page in a third language (third_language_check/)
n_third = sum(1 for _ in third.open(encoding='utf-8')) if third.exists() else 0
n_not = len(json.loads((SEL.parent / 'not_checkable.json').read_text(encoding='utf-8')))  # reports that do not check a claim
val = json.loads((SEL.parent / 'claim_validation.json').read_text(encoding='utf-8'))  # stage_validate_verdict.py, claims from outside VeriTaS
n_dis = sum(1 for v in val.values() if v['dismissed'])
n_repeat = len(rows) - n_third - n_not - n_dis
rows = [r for r in rows if r['id'] in sel or r['id'] in rest]  # select_2000.py drops exact repeats of a claim text
n_repeat -= len(rows)
(OUT / 'snapshots').mkdir(parents=True, exist_ok=True)
for f in (SRC / 'snapshots').iterdir():
    shutil.copy(f, OUT / 'snapshots' / f.name)
media = json.loads(MEDIA.read_text(encoding='utf-8'))
tr = json.loads((SEL.parent / 'statement_translations.json').read_text(encoding='utf-8'))
norm = json.loads((SEL.parent / 'claim_normalization.json').read_text(encoding='utf-8'))
(OUT / 'media').mkdir(exist_ok=True)
for f in (SEL.parent / 'media').iterdir():
    shutil.copy(f, OUT / 'media' / f.name)
for r in rows:
    r['tier'] = TIERS[r['lang']]
    r['mod'] = {'text-only': 'text', 'image-text': 'image', 'video': 'video'}[r['mod']]
    r['veritas'] = VERITAS + str(r['id']) if r['veritas'] else ''
    r['sel'] = r['id'] in sel
    r['script'] = sel.get(r['id']) or ''
    m = media.get(str(r['id'])) or {'items': [], 'note': ''}
    r['media'] = [{**x, 'src': x['src'] if x['src'].startswith('http') else 'media/' + x['src'],
                   **({'poster': 'media/' + x['poster']} if x.get('poster') else {})} for x in m['items']]
    r['mnote'] = m['note']
    if str(r['id']) in norm:
        r['orig'], r['claim'] = norm[str(r['id'])]['title_claim'], norm[str(r['id'])]['claim']
    for e in r['ev']:
        if e['s'] in tr:
            e['so'], e['s'] = e['s'], tr[e['s']]['en']
rows.sort(key=lambda r: r['date'] or '', reverse=True)

cnt = collections.Counter((r['lang'], r['mod']) for r in rows if r['sel'])
all_cnt = collections.Counter(r['lang'] for r in rows)
sel_rows = [r for r in rows if r['sel']]
n_ev = sum(len(r['ev']) for r in sel_rows); n_nourl = sum(1 for r in sel_rows for e in r['ev'] if not e['u'])
n_tr = sum(1 for r in sel_rows for e in r['ev'] if e.get('so'))
n_out_sel = sum(1 for r in sel_rows if not r['veritas'])
n_norm = sum(1 for r in sel_rows if str(r['id']) in norm)
n_manual = sum(1 for r in sel_rows if norm.get(str(r['id']), {}).get('claim_from') == 'manual')
mm_rows = [r for r in sel_rows if r['mod'] != 'text']
n_media = sum(1 for r in mm_rows if r['media'])
n_vid = sum(1 for r in mm_rows if r['mod'] == 'video' and any(x['t'] == 'video' for x in r['media']))
n_vid_all = sum(1 for r in mm_rows if r['mod'] == 'video')
n_out = sum(1 for r in mm_rows if not r['veritas'])
n_zh = sum(1 for r in sel_rows if r['lang'] == 'Chinese'); n_simp = sum(1 for r in sel_rows if r['script'] == 'simplified')
zh_note = ('All selected Chinese claims are Simplified.' if n_simp == n_zh else
           f'{n_simp} of the {n_zh} selected Chinese claims are Simplified; the other {n_zh - n_simp} are worded in English and count as Chinese through their article or evidence pages.')
trs = []
for L, T in TIERS.items():
    q = QUOTA[T]; t, i, v = cnt[(L, 'text')], cnt[(L, 'image')], cnt[(L, 'video')]
    trs.append(f'<tr><th>{T}</th><th>{L}</th><td>{t} / {q}</td><td>{i + v} / {q}</td><td>{i}</td><td>{v}</td><td>{t + i + v} / {2 * q}</td><td>{all_cnt[L] - t - i - v}</td></tr>')
tt = sum(cnt[k] for k in cnt if k[1] == 'text'); ti = sum(cnt[k] for k in cnt if k[1] == 'image'); tv = sum(cnt[k] for k in cnt if k[1] == 'video')
trs.append(f'<tr><th>All</th><th></th><td>{tt} / 1000</td><td>{ti + tv} / 1000</td><td>{ti}</td><td>{tv}</td><td>{len(sel_rows)} / 2000</td><td>{len(rows) - len(sel_rows)}</td></tr>')
table = ('<div class="cmp-scroll"><table class="cmp"><tr><th>Tier</th><th>Language</th><th>Text vs quota</th><th>Multimodal vs quota</th><th>Image</th><th>Video</th><th>Selected</th><th>Not selected</th></tr>'
         + ''.join(trs) + '</table></div>')
note = (f'<div class="revision-note"><b>Selection v1, as of {AS_OF}: {len(sel_rows)} claims selected for annotation, with {n_ev} evidence statements.</b> '
        f'The page opens on the selected claims. The Set filter also shows the {len(rows) - len(sel_rows)} qualifying claims not selected, which are kept as replacements. The {n_repeat} exact repeats of a claim text are left out. '
        f'{n_third} more claims are left out because one of their evidence pages is in a language other than English or the claim\'s own; the cells this left below quota were refilled from VeriTaS. '
        f'{n_not} more are left out because their report does not check a claim. '
        f'Claims from outside VeriTaS went through the VeriTaS claim validation and Stage 6 before selection: {n_dis} are left out, most because the claim refers to a video or an image that is not attached, and the {n_out_sel} selected ones passed. '
        'A claim qualifies if at least one evidence statement survived the link stage and its claim, its fact-checking article or an evidence page is in the language. '
        'Video counts as multimodal. Within each language and type, the selection takes Chinese Simplified first, one claim per fact-checking article first, '
        'claims with more linked evidence first, then the newest. ' + zh_note
        + f' {n_norm} selected Chinese claims were report titles phrased as questions. They are shown as statements, after the VeriTaS claim normalization step and our decontextualization step; the title is shown as the original. {n_manual} of them were reworded by hand because the rewritten claim was wrong.'
        + ' Type is estimated by a keyword rule for claims from outside VeriTaS. '
        f'{n_nourl} selected evidence statements have no source link yet. '
        f'{n_tr} selected evidence statements were extracted in the claim\'s language and are shown in English translation; the statement as extracted is one click away. '
        f'{n_media} of the {len(mm_rows)} selected image and video claims show their media; {n_vid} of the {n_vid_all} video claims have a playable video. '
        'VeriTaS claims show the media VeriTaS stores. Their videos are copies re-encoded at 480 px wide. '
        f'The {n_out} claims from outside VeriTaS show images from the fact-checking article, usually its screenshots of the claimed post, which may carry the fact-checker\'s marks. '
        'Where the article embeds the video itself, it is shown too; otherwise the original video was not kept.</div>')
# the quota chart is drawn from DATA when the page loads; the table stays as its table view
chart = ('<div class="qv"><div class="qv-tiles" id="qvTiles"></div>'
         '<div class="qv-legend"><span><i style="background:var(--c-text)"></i>Text</span><span><i style="background:var(--c-image)"></i>Image</span>'
         '<span><i style="background:var(--c-video)"></i>Video</span><span class="qv-poolh" title="Qualifying claims not selected, kept as replacements">pool left</span></div>'
         '<div id="qvRows"></div><div class="qv-hint">Hover a bar for counts. Click it to show those claims below.</div>'
         '<details class="qv-table"><summary>Table view</summary>' + table + '</details></div><div class="qv-tip" id="qvTip" hidden></div>')
chart_js = r'''<script>
(function(){
const TIERS=__TIERS__, QUOTA=__QUOTA__, MODS=["text","image","video"], NAME={text:"Text",image:"Image",video:"Video"};
const fmt=n=>n.toLocaleString("en-US"), c={}, pool={};
for(const d of DATA){ c[d.lang]=c[d.lang]||{text:0,image:0,video:0}; if(d.sel) c[d.lang][d.mod]++; else pool[d.lang]=(pool[d.lang]||0)+1; }
let tot={text:0,image:0,video:0}, met=0, nq=0, even=true, need=0;
for(const [L,T] of Object.entries(TIERS)){ const q=QUOTA[T], x=c[L]||{text:0,image:0,video:0};
  for(const m of MODS) tot[m]+=x[m];
  nq+=2; met+=(x.text>=q)+(x.image+x.video>=q); need+=2*q; if(x.text!==x.image+x.video) even=false; }
const sel=tot.text+tot.image+tot.video, mm=tot.image+tot.video;
const tile=(h,v,s)=>`<div class="qv-tile"><div class="qv-th">${h}</div><div class="qv-tv">${v}</div><div class="qv-ts">${s}</div></div>`;
document.getElementById("qvTiles").innerHTML=
  tile("Selected",`${fmt(sel)} / ${fmt(need)}`, met===nq?`all ${nq} quotas met`:`${met} of ${nq} quotas met`)+
  tile("Text : multimodal",`${fmt(tot.text)} : ${fmt(mm)}`, even?"50 / 50 in every language":"not 50 / 50 in every language")+
  tile("Image : video",`${fmt(tot.image)} : ${fmt(tot.video)}`,"within multimodal");
const max=Math.max(...Object.keys(TIERS).map(L=>MODS.reduce((s,m)=>s+((c[L]||{})[m]||0),0)));
let h="";
for(const T of ["High","Medium","Low"]){
  h+=`<div class="qv-group">${T} resource</div>`;
  for(const [L,TT] of Object.entries(TIERS)){ if(TT!==T) continue;
    const x=c[L]||{text:0,image:0,video:0}, n=x.text+x.image+x.video, q=QUOTA[T], p=pool[L]||0;
    const segs=MODS.filter(m=>x[m]).map(m=>`<span class="qv-seg" data-l="${L}" data-m="${m}" style="flex:${x[m]};background:var(--c-${m})"></span>`).join("");
    h+=`<div class="qv-row"><div class="qv-lang">${L}</div><div class="qv-track"><div class="qv-bar" style="width:calc((100% - 84px) * ${n/max})">${segs}</div><span class="qv-n">${fmt(n)}${n<2*q?` / ${fmt(2*q)}`:""}</span></div>`+
       `<div class="qv-pool${p<20?" low":""}" title="${p<20?"Few replacements left. ":""}${p} qualifying claims not selected">${fmt(p)}${p<20?'<span class="qv-low">low</span>':""}</div></div>`;
  }
}
document.getElementById("qvRows").innerHTML=h;
const tip=document.getElementById("qvTip");
for(const s of document.querySelectorAll(".qv-seg")){
  const L=s.dataset.l, m=s.dataset.m, x=c[L], q=QUOTA[TIERS[L]];
  const txt=m==="text"?`${L} · Text: ${x.text} of the ${q} text quota`:`${L} · ${NAME[m]}: ${x[m]}, so multimodal ${x.image+x.video} of the ${q} quota`;
  s.addEventListener("mousemove",e=>{tip.hidden=false;tip.textContent=txt;tip.style.left=Math.min(e.clientX+14,innerWidth-tip.offsetWidth-8)+"px";tip.style.top=(e.clientY+14)+"px";});
  s.addEventListener("mouseleave",()=>{tip.hidden=true;});
  s.addEventListener("click",()=>{
    for(const [id,v] of [["fSel","sel"],["fTier",""],["fLang",L],["fMod",m]]){ const el=document.getElementById(id); el.value=v; el.dispatchEvent(new Event("change")); }
    tip.hidden=true; document.querySelector(".controls").scrollIntoView({behavior:"smooth"});
  });
}
})();
</script>'''.replace('__TIERS__', json.dumps(TIERS)).replace('__QUOTA__', json.dumps(QUOTA))

html = TEMPLATE.read_text(encoding='utf-8')
html = re.sub(r'(const DATA\s*=\s*)\[.*?\](;\s*\n)', lambda m: m.group(1) + json.dumps(rows, ensure_ascii=False).replace('</', '<\\/') + ';const BASIS={original_claim:"claim in the language",article:"article in the language",evidence_page:"evidence page in the language"}' + m.group(2), html, flags=re.S)
html = html.replace('<title>MCFC Bench — Claim Browser</title>', '<title>MCFC Bench · Annotation Dataset</title>')
html = html.replace('<h1>Claim Overview</h1>', '<h1>Annotation Dataset</h1>')
html = html.replace('document.getElementById("pill").textContent=DATA.length+" claims";',
                    f'document.getElementById("pill").textContent="{len(sel_rows):,} selected · {len(rows) - len(sel_rows):,} not selected";')
html = re.sub(r'<div class="navlinks">.*?</div>', '<div class="navlinks"><a href="../">Home</a><a href="../annotation-demo/">Annotation Demo</a><a href="../veritas-intake-text1200/">Text Intake</a></div>', html, count=1, flags=re.S)
html = re.sub(r'<div class="revision-note">.*?</div>', lambda m: note + chart, html, count=1, flags=re.S)
html = html.replace('</body>', chart_js + '\n</body>', 1)
html = re.sub(r'<div class="revision-note" id="text-extension-note">.*?</div>', '', html, count=1, flags=re.S)

opt = lambda xs: ''.join(f'<option value="{x}">{x}</option>' for x in xs)
controls = ('<div class="controls"> <label>Set: <select id="fSel"><option value="sel">Selected</option><option value="rest">Not selected</option><option value="">All</option></select></label>'
            ' <label>Tier: <select id="fTier"><option value="">All</option>' + opt(['High', 'Medium', 'Low']) + '</select></label>'
            ' <label>Language: <select id="fLang"><option value="">All</option>' + opt(TIERS) + '</select></label>'
            ' <label>Type: <select id="fMod"><option value="">All</option>' + opt(['text', 'image', 'video']) + '</select></label>'
            ' <label>Verdict: <select id="fVerdict"><option value="">All</option><option value="ok">Matches rating</option>'
            '<option value="bad">Differs from rating</option><option value="na">NEI / Conflicting / no rating</option></select></label>'
            ' <label>Evidence: <select id="fEv"><option value="">All</option><option value="external_search">Has an external-search link</option>'
            '<option value="snap">Has a snapshot highlight</option></select></label>'
            ' <label>Order: <select id="fOrder"><option value="desc">Newest first</option><option value="asc">Oldest first</option></select></label>'
            ' <span class="count" id="count"></span> </div>')
html = re.sub(r'<div class="controls">.*?</div>\s*<div class="grid" id="grid"></div>', lambda m: controls + '\n<div class="grid" id="grid"></div>', html, count=1, flags=re.S)

evidence_js = r'''function evidenceHTML(e){
  const PL={"article_link":"Article link","external_search":"External search","extractor":"Extractor citation","metadata":"Metadata","article":"Article","none":"No URL"};
  const SL={kept:"page supports it",kept_rewritten:"cut back to what the page says",kept_compound:"supported by two pages together",kept_archived:"supported by the archived page",replaced:"replaced by a page that supports it",rewritten_to_cited_source:"cut back to the article's cited source",unverifiable:"page could not be read; not checked"};
  const link=e.u?`<div class="source-row"><div class="evmeta"><span class="tag ${esc(e.p)}">${esc(PL[e.p]||e.p)}</span>${e.st?`<span class="mono">${esc(SL[e.st]||e.st)}</span>`:""}${e.lv?`<span class="mono">${esc(e.lv)}</span>`:""}</div>${sourceLink(e.u)}${e.h?` · <a href="${esc(e.h)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">highlighted ↗</a>`:""}${e.prev&&e.prev!==e.u?`<div class="evmeta"><span>Replaced the link first attached:</span> ${sourceLink(e.prev)}</div>`:""}</div>`
    :`<div class="evmeta"><span class="tag ${esc(e.p)}">${esc(PL[e.p]||e.p)}</span></div>`;
  const cands=e.cands.length?`<details class="source-history" onclick="event.stopPropagation()"><summary>Other links checked, not used (${e.cands.length})</summary><div class="muted">Each was checked for this statement and not chosen. The label is the link stage's first check of the page.</div>${e.cands.map(c=>`<div class="source-row"><span class="mono">${esc(c.verdict)}</span> ${sourceLink(c.url)}</div>`).join("")}</details>`:"";
  const before=e.before?`<details class="source-history" onclick="event.stopPropagation()"><summary>Statement before it was cut back</summary><div>${esc(e.before)}</div></details>`:"";
  const orig=e.so?`<details class="source-history" onclick="event.stopPropagation()"><summary>Statement before translation</summary><div dir="auto">${esc(e.so)}</div></details>`:"";
  return `<div class="evitem">${esc(e.s)}${orig}${before}<details class="source-history" onclick="event.stopPropagation()"><summary>Passage in the article</summary><div dir="auto">${esc(e.span)}</div></details>${link}${cands}</div>`;
}'''
# A link shows as one line: no scheme, no text fragment, percent-escapes decoded, cut with an ellipsis where the card ends.
# The href keeps the full URL and the tooltip shows it.
source_link_js = r"""function sourceLink(url,label){
  if(!/^https?:\/\//i.test(url||"")) return "";
  let t=label;
  if(!t){ t=url.split("#:~:text=")[0].replace(/^https?:\/\/(www\.)?/i,""); try{t=decodeURI(t);}catch(_){} }
  return `<a class="srcurl" href="${esc(url)}" title="${esc(url)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">${esc(t)}</a>`;
}"""
old_source_link = 'function sourceLink(url,label){return /^https?:\\/\\//i.test(url||"")?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">${esc(label||url)}</a>`:""}'
assert html.count(old_source_link) == 1
html = html.replace(old_source_link, source_link_js)
html = html.replace('</style>', '.srcurl{max-width:100%;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n</style>', 1)
html = re.sub(r'function evidenceHTML\(e\)\{.*?\n\}\n// END ARTICLE SOURCE RENDERER', lambda m: evidence_js + '\n// END ARTICLE SOURCE RENDERER', html, count=1, flags=re.S)

html = html.replace('''  const img = d.img ? `<img class="cardimg" src="${d.img}" loading="lazy" alt="claim media">` : "";''',
                    '''  const one = x => x.t==="video" ? `<video class="cardimg" controls preload="none" playsinline${x.poster?` poster="${esc(x.poster)}"`:""} src="${esc(x.src)}" onclick="event.stopPropagation()"></video>`
                                 : `<img class="cardimg" src="${esc(x.src)}" loading="lazy" alt="claim media">`;
  const img = d.media.length ? one(d.media[0]) + (d.media.length>1?`<div class="mmore">+${d.media.length-1} more, open the card</div>`:"") : "";
  const mediaDetail = d.media.length ? `<h4>Claim media (${d.media.length})</h4><div class="mgrid">${d.media.map(one).join("")}</div><div class="muted">${esc(d.mnote)}</div>` : "";''')
html = html.replace('''  <div class="claimtext">${esc(d.claim)}</div>''', '''  <div class="claimtext" dir="auto">${esc(d.claim)}</div>''')
html = html.replace('''  <div class="cfoot"><span>#${d.id}</span><span>${d.date}</span><span class="chip mod">${d.mod}</span>''',
                    '''  <div class="cfoot"><span>#${d.id}</span><span>${d.date}</span><span class="chip mod">${esc(d.tier)}</span><span class="chip mod">${esc(d.lang)}</span>${d.script?`<span class="chip mod">${esc(d.script)}</span>`:""}${d.sel?"":`<span class="chip mod">not selected</span>`}<span class="chip mod">${esc(d.mod)}</span><span class="chip mod">${esc(d.pub)}</span>''')
html = html.replace('''${d.gold?` · gold: ${esc(d.gold)}`:""}''', '''${d.gold?` · rating: ${esc(d.gold)}`:""}''')
html = html.replace('''<div class="deconbox">original: ${esc(d.orig)}</div>''', '''<div class="deconbox" dir="auto">original: ${esc(d.orig)}</div>''')
html = html.replace('''  <div class="detail">${decon}<h4>Evidence (${d.ev.length})</h4>${ev}''',
                    '''  <div class="detail">${mediaDetail}${decon}<h4>Evidence (${d.ev.length})</h4>${d.ev.length?ev:'<div class="muted">No statement survived the link and settle steps.</div>'}''')
html = html.replace('''  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article ↗</a></div></div></div>`;''',
                    '''  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article (${esc(d.pub)}) ↗</a>${d.veritas?` · <a href="${esc(d.veritas)}" target="_blank" onclick="event.stopPropagation()">VeriTaS claim page ↗</a>`:""}<h4>Language basis</h4>${esc(BASIS[d.basis]||d.basis)}${d.est?" · type estimated by keyword rule":""}</div></div></div>`;''')
html = html.replace('''  const fv=document.getElementById("fVerdict").value, fm=document.getElementById("fMod").value,
        fe=document.getElementById("fEv").value, ord=document.getElementById("fOrder").value;''',
                    '''  const fv=document.getElementById("fVerdict").value, fl=document.getElementById("fLang").value, fm=document.getElementById("fMod").value,
        fe=document.getElementById("fEv").value, ord=document.getElementById("fOrder").value, ft=document.getElementById("fTier").value, fs=document.getElementById("fSel").value;''')
html = html.replace('''    if(fv && vclass(d)!==fv) continue;
    if(fm && d.mod!==fm) continue;
    if(fe && !d.ev.some(e=>e.p===fe)) continue;''',
                    '''    if(fv && vclass(d)!==fv) continue;
    if(fl && d.lang!==fl) continue;
    if(fm && d.mod!==fm) continue;
    if(ft && d.tier!==ft) continue;
    if(fs==="sel" && !d.sel) continue;
    if(fs==="rest" && d.sel) continue;
    if(fe==="some" && !d.ev.length) continue;
    if(fe==="none" && d.ev.length) continue;
    if(fe==="external_search" && !d.ev.some(e=>e.p==="external_search")) continue;
    if(fe==="snap" && !d.ev.some(e=>e.h.startsWith("snapshots/"))) continue;''')
html = html.replace('for(const id of ["fVerdict","fMod","fEv","fOrder"])', 'for(const id of ["fSel","fTier","fLang","fMod","fVerdict","fEv","fOrder"])')
html = html.replace('</style>', '.tag.external_search{background:var(--warn-soft);color:var(--warn)}\n.tag.extractor{background:var(--ok-soft);color:var(--ok)}\n'
                    '.tag.article_link{background:var(--info-soft);color:var(--info)}\n.muted{color:var(--ink3)}\n'
                    '.cmp-scroll{overflow-x:auto;max-width:1000px;margin:0 auto}\n'
                    'table.cmp{border-collapse:collapse;width:100%;min-width:760px;margin:12px 0;font-size:.85rem;background:var(--card)}\n'
                    'table.cmp th,table.cmp td{border:1px solid var(--line);padding:6px 9px;vertical-align:top;text-align:left}\n'
                    'table.cmp th{color:var(--ink);font-weight:600}\n'
                    '.cardimg{object-fit:contain;background:var(--line)}\nvideo.cardimg{background:#000}\n'
                    '.mmore{font-size:12px;color:var(--ink3);padding:4px 16px 0}\n'
                    '.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;margin-bottom:6px}\n'
                    '.mgrid .cardimg{max-height:220px;border-radius:8px}\n'
                    # text is a neutral gray on purpose; image and video checked with the dataviz palette validator in both themes
                    ':root{--c-text:#b4b0a8;--c-image:#2e78d6;--c-video:#e8663a}\n[data-theme="dark"]{--c-text:#77736b;--c-image:#4a89e0;--c-video:#e06c38}\n'
                    '.qv{max-width:1000px;margin:16px auto 0;padding:22px 24px 14px;border:1px solid var(--line);border-radius:10px;background:var(--card);box-shadow:var(--shadow)}\n'
                    '.qv-tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:22px}\n'
                    '.qv-th{color:var(--ink2);font-size:14px}.qv-tv{font-size:32px;font-weight:700;color:var(--ink);line-height:1.2;font-variant-numeric:tabular-nums}.qv-ts{color:var(--ink3);font-size:13px}\n'
                    '.qv-legend{display:flex;gap:18px;align-items:center;font-size:14px;color:var(--ink2);margin-bottom:6px}\n'
                    '.qv-legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}\n'
                    '.qv-poolh{margin-left:auto;color:var(--ink3);cursor:help}\n'
                    '.qv-group{color:var(--ink3);font-size:13px;margin:12px 0 2px}\n'
                    '.qv-row{display:grid;grid-template-columns:110px 1fr 64px;align-items:center;gap:10px;height:30px}\n'
                    '.qv-lang{color:var(--ink);font-size:14px}\n'
                    '.qv-track{display:flex;align-items:center;gap:8px;min-width:0}\n'
                    '.qv-bar{display:flex;gap:2px;height:22px;border-radius:4px;overflow:hidden;flex:none}\n'
                    '.qv-seg{height:100%;min-width:2px;cursor:pointer}.qv-seg:hover{filter:brightness(1.1)}\n'
                    '.qv-n{color:var(--ink3);font-size:13px;white-space:nowrap;font-variant-numeric:tabular-nums}\n'
                    '.qv-pool{text-align:right;color:var(--ink2);font-size:14px;font-variant-numeric:tabular-nums;cursor:help}\n'
                    '.qv-pool.low{color:var(--warn)}.qv-low{font-size:11px;margin-left:4px}\n'
                    '.qv-hint{color:var(--ink3);font-size:12px;margin-top:10px}\n'
                    '.qv-table summary{cursor:pointer;color:var(--ink2);font-size:13px;margin-top:8px}\n'
                    '.qv-tip{position:fixed;z-index:50;pointer-events:none;background:var(--ink);color:var(--bg);font-size:12px;padding:5px 9px;border-radius:6px;max-width:280px}\n'
                    '@media (max-width:640px){.qv{padding:16px}.qv-tiles{grid-template-columns:1fr;gap:10px}.qv-tv{font-size:26px}.qv-row{grid-template-columns:78px 1fr 48px;gap:6px}.qv-lang{font-size:13px}}\n</style>', 1)

(OUT / 'index.html').write_text(html, encoding='utf-8')
print(len(rows), 'claims', n_ev, 'evidence', n_nourl, 'without a link', (OUT / 'index.html').stat().st_size // 1024, 'KB', len(list((OUT / 'snapshots').iterdir())), 'snapshots')
print(sorted(cnt.items()))
