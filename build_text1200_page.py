#!/usr/bin/env python3
"""Build the Text Intake page (six languages) from the intake page template.

The 2026-11-04 candidate batch: 1,200 text-only VeriTaS claims (English 300, Spanish 300, Hindi 180,
Arabic 180, Tamil 120, Filipino 120) through the intake chain on otakotak
(/scratch/users/suliu/mcfc-settle/intake_text1200/): article fetch with a Wayback fallback,
decontextualization, extraction, strict URL recovery, merge, verdict; then the link stage with the
settle step (run_link_text1200.sh, 8 shards). Claims whose fact-checking article could not be fetched
never entered the chain and are listed in a table, not as cards.

Reads linked_981.json + intake_batch.json from the analysis folder, writes veritas-intake-text1200/.
"""
import collections
import html as _html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / 'veritas-intake-review/index.html'
OUT = HERE / 'veritas-intake-text1200'
SRC = Path('/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs/intake_text1200_20261105')
LANGS = ['English', 'Spanish', 'Hindi', 'Arabic', 'Tamil', 'Filipino']
VERITAS = 'https://veritas.mai.informatik.tu-darmstadt.de/claims/'
esc = lambda t: _html.escape(str(t or ''))

linked = json.loads((SRC / 'linked_981.json').read_text(encoding='utf-8'))['records']
batch = json.loads((SRC / 'intake_batch.json').read_text(encoding='utf-8'))['records']
by_id = {str(b['claim_id']): b for b in batch}
(OUT / 'snapshots').mkdir(parents=True, exist_ok=True)


def keep_snapshot(hl):
    if hl and hl.startswith('snapshots/'):
        f = SRC / 'snapshots' / hl.split('/', 1)[1]
        if f.exists():
            shutil.copy(f, OUT / 'snapshots' / f.name)
        else:
            return ''
    return hl or ''


def provenance(e):
    rec = (e.get('url_recovery') or {}).get('status', '')
    if rec.endswith('_exempt'):
        return 'metadata'
    return e.get('source_url_origin') or ('none' if not e.get('source_url') else 'article')


rows = []
per_lang = {L: collections.Counter() for L in LANGS}
for r in sorted(linked, key=lambda r: r.get('claim_date') or '', reverse=True):
    cid = str(r['claim_id']); b = by_id.get(cid, {}); L = r['language']
    ev = []
    for e in r['extracted']['evidence_set']:
        cands = (e.get('link_sources') or {}).get('candidates') or []
        u = e.get('source_url') or ''
        ev.append({'s': e.get('statement', ''), 'span': e.get('support_span', ''), 'u': u, 'p': provenance(e),
                   'h': keep_snapshot(e.get('highlight_url')), 'st': e.get('url_status', ''),
                   'lv': e.get('link_verdict', ''), 'before': e.get('statement_before_settle', ''),
                   'prev': e.get('source_url_before_settle', '') or e.get('previous_source_url', ''),
                   'cands': [{'url': x['url'], 'verdict': x.get('verdict', '')} for x in cands if x.get('url') != u]})
    c = per_lang[L]
    c['claims'] += 1; c['extracted'] += r.get('n_extracted') or 0; c['kept'] += len(ev)
    c['hl'] += sum(1 for e in ev if e['h']); c['zero'] += (len(ev) == 0)
    g = (r.get('veracity_label') or ''); p = r.get('pred_label') or ''
    if g.startswith(('true', 'false')):
        c['scored'] += 1
        c['correct'] += (g.startswith('true') and p == 'Supported') or (g.startswith('false') and p == 'Refuted')
    orig = (r.get('veritas_claim') or '').strip()
    rows.append({'id': int(cid), 'claim': r['claim'], 'lang': L, 'date': (r.get('claim_date') or '')[:10], 'mod': 'text-only',
                 'pred': p, 'gold': g, 'art': r.get('url', ''), 'pub': b.get('publisher', r.get('publisher', '')), 'img': '',
                 'orig': orig if orig != r['claim'].strip() else '', 'veritas': VERITAS + cid, 'ev': ev})

# claims that never entered the chain (article not fetched) or failed in it
done_ids = {str(r['claim_id']) for r in linked}
missing = collections.defaultdict(collections.Counter)
for b in batch:
    if str(b['claim_id']) not in done_ids:
        missing[b['language']][b.get('publisher', '')] += 1

n_ev = sum(len(r['ev']) for r in rows); n_ex = sum(c['extracted'] for c in per_lang.values())
n_zero = sum(c['zero'] for c in per_lang.values()); n_hl = sum(c['hl'] for c in per_lang.values())
n_snap = sum(1 for r in rows for e in r['ev'] if e['h'].startswith('snapshots/'))

html = TEMPLATE.read_text(encoding='utf-8')
html = re.sub(r'(const DATA\s*=\s*)\[.*?\](;\s*\n)', lambda m: m.group(1) + json.dumps(rows, ensure_ascii=False).replace('</', '<\\/') + m.group(2), html, flags=re.S)
html = html.replace('<title>MCFC Bench — Claim Browser</title>', '<title>MCFC Bench · Text Intake, Six Languages</title>')
html = html.replace('<h1>Claim Overview</h1>', '<h1>Text Intake, Six Languages</h1>')
html = re.sub(r'<div class="navlinks">.*?</div>', '<div class="navlinks"><a href="../">Home</a><a href="../veritas-intake-dashboard/">VeriTaS Intake</a><a href="../multilingual/">Multilingual</a><a href="../averitec-averimatec-review/">AVeriTeC + AVerImaTeC</a></div>', html, count=1, flags=re.S)

# summary table per language
planned = collections.Counter(b['language'] for b in batch)
trs = []
for L in LANGS:
    c = per_lang[L]; m = sum(missing[L].values())
    miss_txt = ', '.join(f'{esc(k)} {v}' for k, v in missing[L].most_common(3)) if m else ''
    acc = f'{c["correct"]}/{c["scored"]}' if c['scored'] else ''
    trs.append(f'<tr><th>{L}</th><td>{planned[L]}</td><td>{c["claims"]}</td><td>{m}{(" <span class=muted>(" + miss_txt + ")</span>") if miss_txt else ""}</td>'
               f'<td>{c["extracted"]}</td><td>{c["kept"]}</td><td>{c["hl"]}</td><td>{c["zero"]}</td><td>{acc}</td></tr>')
tot = collections.Counter()
for c in per_lang.values():
    tot.update(c)
trs.append(f'<tr><th>All</th><td>{sum(planned.values())}</td><td>{tot["claims"]}</td><td>{sum(sum(v.values()) for v in missing.values())}</td>'
           f'<td>{tot["extracted"]}</td><td>{tot["kept"]}</td><td>{tot["hl"]}</td><td>{tot["zero"]}</td><td>{tot["correct"]}/{tot["scored"]}</td></tr>')
table = ('<div class="cmp-scroll"><table class="cmp"><tr><th>Language</th><th>Planned</th><th>Through the chain</th><th>Article not fetched</th>'
         '<th>Evidence extracted</th><th>Evidence kept</th><th>With highlight</th><th>Claims with no evidence kept</th>'
         '<th>Verdict matches VeriTaS rating</th></tr>' + ''.join(trs) + '</table></div>')

note = (f'<div class="revision-note"><b>Text-only candidate batch of 2026-11-04: {len(rows)} claims through the pipeline, '
        f'{n_ex} evidence statements extracted, {n_ev} kept after the link and settle steps.</b> The batch is the 1,200 newest '
        'text-only VeriTaS claims in six languages (English and Spanish 300 each, Hindi and Arabic 180 each, Tamil and Filipino '
        '120 each), excluding claims already used elsewhere and video claims. A claim is on this page only if its fact-checking '
        'article could be fetched, live or from the Wayback Machine; the table gives the publishers behind the missing ones. '
        'Each claim went through decontextualization, evidence extraction from the article, strict URL recovery, merge and '
        'verdict, then the link stage: the article\'s own hyperlinks first, ranked against the quoted passage, then a web search '
        'restricted to pages dated before the claim. An LLM reads each linked page and checks that it states the evidence; when '
        'it does not, the statement is cut back to what the page says or other pages are tried, and a statement no page supports '
        f'is dropped. "Highlighted" opens the page with the supporting passage marked ({n_hl - n_snap} direct links) or a text '
        f'copy of the page ({n_snap} snapshots). {n_zero} claims lost every statement and are kept on the page so the loss can '
        'be inspected. The VeriTaS rating is the publisher\'s own rating as recorded by VeriTaS; "matches" counts Supported '
        'against a true rating and Refuted against a false one, so it is a rough check, not an accuracy figure.</div>' + table)
html = re.sub(r'<div class="revision-note">.*?</div>', note, html, count=1, flags=re.S)
html = re.sub(r'<div class="revision-note" id="text-extension-note">.*?</div>', '', html, count=1, flags=re.S)

options = ''.join(f'<option value="{L}">{L}</option>' for L in LANGS)
controls = ('<div class="controls"> <label>Language: <select id="fLang"><option value="">All</option>' + options + '</select></label>'
            ' <label>Verdict: <select id="fVerdict"><option value="">All</option><option value="ok">Matches rating</option>'
            '<option value="bad">Differs from rating</option><option value="na">NEI / Conflicting / no rating</option></select></label>'
            ' <label>Evidence: <select id="fEv"><option value="">All</option><option value="some">Has evidence kept</option>'
            '<option value="none">No evidence kept</option><option value="external_search">Has an external-search link</option>'
            '<option value="snap">Has a snapshot highlight</option></select></label>'
            ' <label>Order: <select id="fOrder"><option value="desc">Newest first</option><option value="asc">Oldest first</option></select></label>'
            ' <span class="count" id="count"></span> </div>')
html = re.sub(r'<div class="controls">.*?</div>\s*<div class="grid" id="grid"></div>', controls + '\n<div class="grid" id="grid"></div>', html, count=1, flags=re.S)

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
                    '''  <div class="cfoot"><span>#${d.id}</span><span>${d.date}</span><span class="chip mod">${esc(d.lang)}</span><span class="chip mod">${esc(d.pub)}</span>''')
html = html.replace('''${d.gold?` · gold: ${esc(d.gold)}`:""}''', '''${d.gold?` · rating: ${esc(d.gold)}`:""}''')
html = html.replace('''<div class="deconbox">original: ${esc(d.orig)}</div>''', '''<div class="deconbox" dir="auto">original: ${esc(d.orig)}</div>''')
html = html.replace('''  <div class="detail">${decon}<h4>Evidence (${d.ev.length})</h4>${ev}''',
                    '''  <div class="detail">${decon}<h4>Evidence (${d.ev.length})</h4>${d.ev.length?ev:'<div class="muted">No statement survived the link and settle steps.</div>'}''')
html = html.replace('''  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article ↗</a></div></div></div>`;''',
                    '''  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article (${esc(d.pub)}) ↗</a> · <a href="${esc(d.veritas)}" target="_blank" onclick="event.stopPropagation()">VeriTaS claim page ↗</a></div></div></div>`;''')
html = html.replace('''  const fv=document.getElementById("fVerdict").value, fm=document.getElementById("fMod").value,
        fe=document.getElementById("fEv").value, ord=document.getElementById("fOrder").value;''',
                    '''  const fv=document.getElementById("fVerdict").value, fl=document.getElementById("fLang").value,
        fe=document.getElementById("fEv").value, ord=document.getElementById("fOrder").value;''')
html = html.replace('''    if(fv && vclass(d)!==fv) continue;
    if(fm && d.mod!==fm) continue;
    if(fe && !d.ev.some(e=>e.p===fe)) continue;''',
                    '''    if(fv && vclass(d)!==fv) continue;
    if(fl && d.lang!==fl) continue;
    if(fe==="some" && !d.ev.length) continue;
    if(fe==="none" && d.ev.length) continue;
    if(fe==="external_search" && !d.ev.some(e=>e.p==="external_search")) continue;
    if(fe==="snap" && !d.ev.some(e=>e.h.startsWith("snapshots/"))) continue;''')
html = html.replace('for(const id of ["fVerdict","fMod","fEv","fOrder"])', 'for(const id of ["fVerdict","fLang","fEv","fOrder"])')
html = html.replace('</style>', '.tag.external_search{background:var(--warn-soft);color:var(--warn)}\n.tag.extractor{background:var(--ok-soft);color:var(--ok)}\n'
                    '.tag.article_link{background:var(--info-soft);color:var(--info)}\n.muted{color:var(--ink3)}\n'
                    '.cmp-scroll{overflow-x:auto;max-width:1000px;margin:0 auto}\n'
                    'table.cmp{border-collapse:collapse;width:100%;min-width:760px;margin:12px 0;font-size:.85rem;background:var(--card)}\n'
                    'table.cmp th,table.cmp td{border:1px solid var(--line);padding:6px 9px;vertical-align:top;text-align:left}\n'
                    'table.cmp th{color:var(--ink);font-weight:600}\n</style>', 1)

(OUT / 'index.html').write_text(html, encoding='utf-8')
print(f'{len(rows)} claims, {n_ex} extracted, {n_ev} kept, {n_hl} highlighted ({n_snap} snapshots), {n_zero} claims with no evidence; '
      f'missing per language: {{ {", ".join(f"{L}: {sum(missing[L].values())}" for L in LANGS)} }}')
print('wrote', OUT / 'index.html', (OUT / 'index.html').stat().st_size // 1024, 'KB;', len(list((OUT / 'snapshots').iterdir())), 'snapshots')
