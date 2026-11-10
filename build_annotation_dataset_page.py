#!/usr/bin/env python3
"""Build the Annotation Dataset page: the 2,000 claims selected for human annotation, plus the qualifying claims not selected,
by resource tier, language and type.

Reads analysis_outputs/annotation_dataset_export_<date>/ (claims.json and snapshots/, exported from
otakotak:/scratch/users/suliu/mcfc-settle/intake_text1200/ by export_dataset.py) and the selection in
analysis_outputs/annotation_2000_v1/claims_final.jsonl (select_2000.py). A claim qualifies if at least one evidence
statement survived the link stage and its claim, its fact-checking article or an evidence page is in the language.
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
SRC = Path('/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs/annotation_dataset_export_20261110')
SEL = Path('/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs/annotation_2000_v1/claims_final.jsonl')
AS_OF = '2026-11-10'
TIERS = {'English': 'High', 'Chinese': 'High', 'Hindi': 'Medium', 'Arabic': 'Medium', 'Tamil': 'Low', 'Indonesian': 'Low'}
QUOTA = {'High': 250, 'Medium': 150, 'Low': 100}
VERITAS = 'https://veritas.mai.informatik.tu-darmstadt.de/claims/'
esc = lambda t: _html.escape(str(t or ''))

rows = json.loads((SRC / 'claims.json').read_text(encoding='utf-8'))
sel = {json.loads(l)['claim_id']: json.loads(l)['script'] for l in SEL.open(encoding='utf-8')}
(OUT / 'snapshots').mkdir(parents=True, exist_ok=True)
for f in (SRC / 'snapshots').iterdir():
    shutil.copy(f, OUT / 'snapshots' / f.name)
for r in rows:
    r['tier'] = TIERS[r['lang']]
    r['mod'] = {'text-only': 'text', 'image-text': 'image', 'video': 'video'}[r['mod']]
    r['veritas'] = VERITAS + str(r['id']) if r['veritas'] else ''
    r['sel'] = r['id'] in sel
    r['script'] = sel.get(r['id']) or ''
rows.sort(key=lambda r: r['date'] or '', reverse=True)

cnt = collections.Counter((r['lang'], r['mod']) for r in rows if r['sel'])
all_cnt = collections.Counter(r['lang'] for r in rows)
sel_rows = [r for r in rows if r['sel']]
n_ev = sum(len(r['ev']) for r in sel_rows); n_nourl = sum(1 for r in sel_rows for e in r['ev'] if not e['u'])
trs = []
for L, T in TIERS.items():
    q = QUOTA[T]; t, i, v = cnt[(L, 'text')], cnt[(L, 'image')], cnt[(L, 'video')]
    trs.append(f'<tr><th>{T}</th><th>{L}</th><td>{t} / {q}</td><td>{i + v} / {q}</td><td>{i}</td><td>{v}</td><td>{t + i + v} / {2 * q}</td><td>{all_cnt[L] - t - i - v}</td></tr>')
tt = sum(cnt[k] for k in cnt if k[1] == 'text'); ti = sum(cnt[k] for k in cnt if k[1] == 'image'); tv = sum(cnt[k] for k in cnt if k[1] == 'video')
trs.append(f'<tr><th>All</th><th></th><td>{tt} / 1000</td><td>{ti + tv} / 1000</td><td>{ti}</td><td>{tv}</td><td>{len(sel_rows)} / 2000</td><td>{len(rows) - len(sel_rows)}</td></tr>')
table = ('<div class="cmp-scroll"><table class="cmp"><tr><th>Tier</th><th>Language</th><th>Text vs quota</th><th>Multimodal vs quota</th><th>Image</th><th>Video</th><th>Selected</th><th>Not selected</th></tr>'
         + ''.join(trs) + '</table></div>')
note = (f'<div class="revision-note"><b>Selection v1, as of {AS_OF}: {len(sel_rows)} claims selected for annotation, with {n_ev} evidence statements.</b> '
        f'The page opens on the selected claims. The Set filter also shows the {len(rows) - len(sel_rows)} qualifying claims not selected, which are kept as replacements. '
        'A claim qualifies if at least one evidence statement survived the link stage and its claim, its fact-checking article or an evidence page is in the language. '
        'Video counts as multimodal. Within each language and type, the selection takes Chinese Simplified first, one claim per fact-checking article first, '
        'claims with more linked evidence first, then the newest. All selected Chinese claims are Simplified. Type is estimated by a keyword rule for claims from outside VeriTaS. '
        f'{n_nourl} selected evidence statements have no source link yet. Image and video files are not shown here.</div>' + table)

html = TEMPLATE.read_text(encoding='utf-8')
html = re.sub(r'(const DATA\s*=\s*)\[.*?\](;\s*\n)', lambda m: m.group(1) + json.dumps(rows, ensure_ascii=False).replace('</', '<\\/') + ';const BASIS={original_claim:"claim in the language",article:"article in the language",evidence_page:"evidence page in the language"}' + m.group(2), html, flags=re.S)
html = html.replace('<title>MCFC Bench — Claim Browser</title>', '<title>MCFC Bench · Annotation Dataset</title>')
html = html.replace('<h1>Claim Overview</h1>', '<h1>Annotation Dataset</h1>')
html = re.sub(r'<div class="navlinks">.*?</div>', '<div class="navlinks"><a href="../">Home</a><a href="../annotation-demo/">Annotation Demo</a><a href="../veritas-intake-text1200/">Text Intake</a></div>', html, count=1, flags=re.S)
html = re.sub(r'<div class="revision-note">.*?</div>', lambda m: note, html, count=1, flags=re.S)
html = re.sub(r'<div class="revision-note" id="text-extension-note">.*?</div>', '', html, count=1, flags=re.S)

opt = lambda xs: ''.join(f'<option value="{x}">{x}</option>' for x in xs)
controls = ('<div class="controls"> <label>Set: <select id="fSel"><option value="sel">Selected 2,000</option><option value="rest">Not selected</option><option value="">All</option></select></label>'
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
  return `<div class="evitem">${esc(e.s)}${before}<details class="source-history" onclick="event.stopPropagation()"><summary>Passage in the article</summary><div dir="auto">${esc(e.span)}</div></details>${link}${cands}</div>`;
}'''
html = re.sub(r'function evidenceHTML\(e\)\{.*?\n\}\n// END ARTICLE SOURCE RENDERER', lambda m: evidence_js + '\n// END ARTICLE SOURCE RENDERER', html, count=1, flags=re.S)

html = html.replace('''  <div class="claimtext">${esc(d.claim)}</div>''', '''  <div class="claimtext" dir="auto">${esc(d.claim)}</div>''')
html = html.replace('''  <div class="cfoot"><span>#${d.id}</span><span>${d.date}</span><span class="chip mod">${d.mod}</span>''',
                    '''  <div class="cfoot"><span>#${d.id}</span><span>${d.date}</span><span class="chip mod">${esc(d.tier)}</span><span class="chip mod">${esc(d.lang)}</span>${d.script?`<span class="chip mod">${esc(d.script)}</span>`:""}${d.sel?"":`<span class="chip mod">not selected</span>`}<span class="chip mod">${esc(d.mod)}</span><span class="chip mod">${esc(d.pub)}</span>''')
html = html.replace('''${d.gold?` · gold: ${esc(d.gold)}`:""}''', '''${d.gold?` · rating: ${esc(d.gold)}`:""}''')
html = html.replace('''<div class="deconbox">original: ${esc(d.orig)}</div>''', '''<div class="deconbox" dir="auto">original: ${esc(d.orig)}</div>''')
html = html.replace('''  <div class="detail">${decon}<h4>Evidence (${d.ev.length})</h4>${ev}''',
                    '''  <div class="detail">${decon}<h4>Evidence (${d.ev.length})</h4>${d.ev.length?ev:'<div class="muted">No statement survived the link and settle steps.</div>'}''')
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
                    'table.cmp th{color:var(--ink);font-weight:600}\n</style>', 1)

(OUT / 'index.html').write_text(html, encoding='utf-8')
print(len(rows), 'claims', n_ev, 'evidence', n_nourl, 'without a link', (OUT / 'index.html').stat().st_size // 1024, 'KB', len(list((OUT / 'snapshots').iterdir())), 'snapshots')
print(sorted(cnt.items()))
