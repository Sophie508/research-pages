#!/usr/bin/env python3
"""Apply saved article-link recovery to the existing intake review page.

No model, network, or benchmark verdict changes. The checked-in manifest supplies
the exact claim/statement mapping, article-anchor provenance and review status.
Running the updater repeatedly produces the same page.
"""
import copy
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
PAGE=ROOT/'veritas-intake-review/index.html'
MANIFEST=ROOT/'veritas-intake-review/article_source_revision.json'

CSS='''
/* Article-link revision: display source type and format. */
.tag.article-recovered{background:var(--info-soft);color:var(--info)}
.source-list{margin-top:9px}.source-row{padding:9px 0;border-top:1px solid var(--line)}
.source-row:first-child{border-top:0}.source-row a{display:block;margin-top:5px}
.source-label,.source-hint{font-size:12px;color:var(--ink2);margin-top:6px}
.source-history{margin-top:10px;border-top:1px solid var(--line);padding-top:7px;font-size:12px;color:var(--ink2)}
.source-history summary{cursor:pointer;color:var(--info)}
.revision-note{max-width:1000px;margin:16px auto 0;padding:12px 20px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink2);font-size:13px}
'''

JS='''
// BEGIN ARTICLE SOURCE RENDERER
const MATERIAL_LABELS={ACADEMIC:"Academic literature",OFFICIAL:"Official / judicial",NEWS:"News",ORGANIZATION:"Organization / company",SOCIAL:"Social post",REFERENCE:"Reference / document mirror",MEDIA_ARCHIVE:"Image archive",FACT_CHECK:"Fact-check",UNKNOWN:"Unclassified"};
function sourceLink(url,label){return /^https?:\\/\\//i.test(url||"")?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">${esc(label||url)}</a>`:""}
function sourceRow(s){
  const type=(s.material||{}).source_type||"UNKNOWN";
  const format=(s.material||{}).format||"UNKNOWN";
  return `<div class="source-row"><div class="evmeta"><span class="tag article">Article link #${s.rank}</span><span>${esc(MATERIAL_LABELS[type]||type)}</span><span>${esc(format)}</span></div>${sourceLink(s.url)}<details class="source-history" onclick="event.stopPropagation()"><summary>Source details</summary><div>Original anchor: ${esc((s.article_anchor||{}).anchor||"[unnamed link]")}</div>${s.page_date?`<div>Source date: ${esc(s.page_date)} (${esc(s.date_source||"unknown field")})</div>`:""}</details></div>`;
}
function evidenceHTML(e){
  if(!e.article_sources){
    const label=e.p==="external-verified"?"External search":e.p;
    const note=e.article_recovery_status?`<div class="source-hint">${e.article_recovery_status==="NO_ARTICLE_CANDIDATE"?"No article-link candidate was found; the previous external URL is retained.":"Not covered by this recovery batch; the previous external URL is retained."}</div>`:"";
    return `<div class="evitem">${esc(e.s)}<div class="evmeta"><span class="tag ${esc(e.p)}">${esc(label)}</span>${e.d?`<span class="mono">${esc(e.d)}</span>`:""}</div>${sourceLink(e.u)}${note}</div>`;
  }
  const selected=e.article_sources.filter(s=>s.selected),shown=selected.length?selected:e.article_sources;
  const others=selected.length?e.article_sources.filter(s=>!s.selected):[];
  const label="Fact-checking article links";
  const extra=others.length?`<details class="source-history" onclick="event.stopPropagation()"><summary>Other article candidates (${others.length})</summary>${others.map(sourceRow).join("")}</details>`:"";
  const old=e.previous_source||{};
  return `<div class="evitem">${esc(e.s)}<div class="source-label">${label}</div><div class="source-list">${shown.map(sourceRow).join("")}</div>${extra}<details class="source-history" onclick="event.stopPropagation()"><summary>Previous external-search URL</summary>${sourceLink(old.url)}${old.date?`<div>Previous source date: ${esc(old.date)}</div>`:""}</details></div>`;
}
// END ARTICLE SOURCE RENDERER
'''


def apply_records(data,manifest):
    updated=copy.deepcopy(data);records={(r['claim_id'],r['statement']):r for r in manifest['records']};changes=[]
    for claim in updated:
        for n,e in enumerate(claim['ev']):
            r=records.get((str(claim['id']),e['s']))
            if r is None:continue
            if n!=r['evidence_index'] or claim['art']!=r['article_url']:raise ValueError('Evidence mapping changed')
            previous=e.get('previous_source') or {'url':e['u'],'date':e['d'],'provenance':e['p']}
            if previous!=r['original_source']:raise ValueError('Original evidence source changed')
            if not r['sources']:
                e['article_recovery_status']=r['status'];continue
            selected=[s for s in r['sources'] if s['selected']]
            primary=(selected or r['sources'])[0]
            e.update(u=primary['url'],d=primary.get('page_date') or '',p='article-recovered',
                previous_source=r['original_source'],article_sources=r['sources'],article_selection_basis=r['selection_basis'],
                article_recovery_status=r['status'])
            changes.append({'claim_id':claim['id'],'evidence_index':n,'statement':e['s'],
                'previous_url':r['original_source']['url'],'displayed_article_urls':[s['url'] for s in selected or r['sources']],
                'all_article_candidates':[s['url'] for s in r['sources']],'selection_basis':r['selection_basis']})
    return updated,changes


def update():
    manifest=json.loads(MANIFEST.read_text());text=PAGE.read_text()
    match=re.search(r'(const DATA\s*=\s*)(\[.*?\])(;\s*\n)',text,re.S)
    if not match:raise ValueError('DATA not found')
    data=json.loads(match.group(2));updated,changes=apply_records(data,manifest)
    payload=json.dumps(updated,ensure_ascii=False).replace('</','<\\/')
    text=text[:match.start(2)]+payload+text[match.end(2):]
    if 'BEGIN ARTICLE SOURCE RENDERER' not in text:
        text=text.replace('</style>',CSS+'\n</style>',1)
        old='function esc(s){const d=document.createElement("div");d.textContent=s;return d.innerHTML}'
        new='function esc(s){return String(s??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/\x27/g,"&#39;")}'
        if old not in text:raise ValueError('Unexpected escape function')
        text=text.replace(old,new+JS,1)
        text=re.sub(r'  const ev = d\.ev\.map\(.*?\)\.join\(""\);', '  const ev = d.ev.map(evidenceHTML).join("");',text,count=1)
        old_option='<option value="article">Has article URL</option>'
        text=text.replace(old_option,'<option value="article">Has original article URL</option><option value="article-recovered">Has recovered article links</option>',1)
        note=(f'<div class="revision-note">Article-link revision: {len(changes)} evidence statements now show links recovered from their fact-checking articles. '
              'Source types and formats are shown beside each link. Previous external URLs remain in history. '
              'Claim verdicts have not been recomputed.</div>')
        marker='<div class="controls">'
        text=text.replace(marker,note+'\n'+marker,1)
    # Refresh presentation when rerunning on an already revised page.
    text=re.sub(r'// BEGIN ARTICLE SOURCE RENDERER.*?// END ARTICLE SOURCE RENDERER',
                lambda _:JS.strip(),text,flags=re.S)
    text=re.sub(r'<div class="revision-note">.*?</div>',
                lambda _:f'<div class="revision-note">Article-link revision: {len(changes)} evidence statements now show links recovered from their fact-checking articles. Source types and formats are shown beside each link. Previous external URLs remain in history. Claim verdicts have not been recomputed.</div>',text,count=1)
    text='\n'.join(line for line in text.split('\n') if not line.startswith(('.source-status','.review-concern')))
    text=text.replace('/* Article-link revision: material type and support status remain separate. */',
                      '/* Article-link revision: display source type and format. */')
    PAGE.write_text(text)
    out=ROOT/'veritas-intake-review/article_source_changes.json'
    out.write_text(json.dumps({'version':manifest['version'],'changed_evidence':len(changes),'changes':changes},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'claims':len(updated),'evidence':sum(len(c['ev']) for c in updated),'changed_evidence':len(changes)},ensure_ascii=False))


if __name__=='__main__':update()
