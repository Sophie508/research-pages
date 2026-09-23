#!/usr/bin/env python3
"""Build the AVeriTeC + AVerImaTeC review page from the intake page template.

Both datasets carry gold labels and gold evidence, so this is where EV2R can be
shown per claim. AVerImaTeC rows come from the 2026-08-30 val run after the new
URL stage: every evidence statement keeps its statement text, the link it ended
up with, how that link was obtained (article hyperlink, dated external search,
image, metadata) and whether the verifier confirmed it. Only statements with no
candidate link of any kind were dropped (18 of 397). AVeriTeC rows are the 20
claims already on the site, still from the older URL stage, and are labelled so.

The intake page is the template so all three review pages share one look; only
DATA, the labels and the dataset filter differ.
"""
import json, re, shutil
from pathlib import Path
HERE = Path(__file__).resolve().parent
TEMPLATE = HERE/'veritas-intake-review/index.html'
OUT = HERE/'averitec-averimatec-review'; (OUT/'media').mkdir(parents=True, exist_ok=True)
MCFC = Path('/Users/sophie/Downloads/mcfc-veritas-track3'); DESK = Path('/Users/sophie/Desktop/multi culture fact checking')
IMG = DESK/'datasets/averimatec/images'

# ---- AVerImaTeC (new URL stage) ----
inp = json.load(open(MCFC/'results/url_revision_aug30/ev2r_input_link_or_drop.json'))
gold = json.load(open(DESK/'datasets/averimatec/val.json'))
_p = json.load(open(MCFC/'results/t2_averimatec_mm_predict_val_n108_gemma4_26b_20260830_100302.json'))
pred = {r['id']: r for r in (_p.get('records', _p) if isinstance(_p, dict) else _p)}
import glob, os
ev2r_f = sorted(glob.glob(str(MCFC/'track3_veritas/pipeline/results/*amt_val_link_or_drop*ev2r_official*.json')), key=os.path.getmtime)[-1]
ev2r = {r['id']: r['evidence'] for r in json.load(open(ev2r_f))['records'] if isinstance(r.get('evidence'), dict)}
dec = {r['key']: r for r in (json.loads(l) for l in open(MCFC/'results/url_revision_aug30/verify_and_drop.jsonl') if l.strip())}
orig = {r['id']: r for r in json.load(open(MCFC/'results/clean_val_ev2r_input_single.json'))}
gold_to_pipe = {r.get('averimatec_gold_index', r['id']): r['id'] for r in json.load(open(MCFC/'results/clean_val_ev2r_input_single.json'))}

def prov(e, d=None):
    t = e.get('source_type')
    if t == 'image': return 'image'
    if t == 'metadata': return 'metadata'
    # Which stage produced the link that was attached: the verifier's record
    # names each candidate's stage, so the attached URL is looked up there.
    if d:
        stage = next((c['stage'] for c in d.get('candidates', []) if c['url'] == e.get('source_url')), None)
        if stage == 'article': return 'article-recovered'
        if stage == 'external': return 'external-verified'
    return 'article' if e.get('source_url') else 'ungrounded'

rows = []
for r in inp:
    gi = r['id']; g = gold[gi]; pid = gold_to_pipe.get(gi, gi)
    img = ''
    for im in (g.get('claim_images') or [])[:1]:
        fn = os.path.basename(im)
        if (IMG/fn).exists():
            # '#' in a src is a fragment marker, so the served name drops it.
            safe = fn.replace('#', '_')
            dst = OUT/'media'/safe
            if not dst.exists(): shutil.copy(IMG/fn, dst)
            img = 'media/'+safe
    ev = []
    for i, e in enumerate((r.get('extracted') or {}).get('evidence_set') or []):
        d = dec.get(f'{pid}:{i}')
        p = prov(e, d); item = {'s': e.get('statement',''), 'u': e.get('source_url') or '', 'd': '', 'p': p}
        if d and d.get('candidates'):
            srcs = []
            for k, c in enumerate(d['candidates'], 1):
                sel = (c['url'] == e.get('source_url'))
                srcs.append({'url': c['url'], 'rank': k, 'origin': 'ARTICLE_HYPERLINK' if c['stage']=='article' else 'EXTERNAL_SEARCH',
                             'selected': sel, 'support_status': c['verdict'], 'support_reason': c.get('why',''), 'role': None,
                             'material': {'source_type': 'UNKNOWN', 'format': 'HTML'}})
            item['article_sources'] = srcs
            oe = ((orig[pid].get('extracted') or {}).get('evidence_set') or [])[i] if pid in orig else {}
            item['previous_source'] = {'url': oe.get('source_url') or '', 'date': ''}
            item['attach'] = e.get('url_attach', '')
        ev.append(item)
    sc = ev2r.get(gi, {})
    rows.append({'ds': 'AVerImaTeC', 'id': gi, 'claim': r.get('claim') or g.get('claim_text',''), 'date': (r.get('claim_date') or g.get('date') or '')[:10],
                 'mod': 'image-text' if img else 'text-only', 'pred': (pred.get(pid, {}).get('prediction') or {}).get('label',''),
                 'gold': g.get('label',''), 'art': r.get('url',''), 'img': img, 'orig': '', 'ev': ev,
                 'ev2r': {'R': round(sc.get('recall',0),2), 'P': round(sc.get('precision',0),2), 'n_ref': sc.get('n_ref',0)}})
n_amt = len(rows); n_ev_amt = sum(len(x['ev']) for x in rows)

# ---- AVeriTeC (existing 20, older URL stage) ----
# The 20 AVeriTeC rows were lifted from the retired original-pipeline page and
# kept here as data so the page no longer depends on that page existing.
old = json.loads((OUT/'averitec_rows.json').read_text(encoding='utf-8'))
for x in old: x['ds'] = 'AVeriTeC'; x['ev2r'] = None
rows += old

html = TEMPLATE.read_text(encoding='utf-8')
html = re.sub(r'(const DATA\s*=\s*)\[.*?\](;\s*\n)', lambda m: m.group(1)+json.dumps(rows, ensure_ascii=False)+m.group(2), html, flags=re.S)
html = html.replace('<title>MCFC Bench — Claim Browser</title>', '<title>MCFC Bench — AVeriTeC + AVerImaTeC Review</title>')
html = html.replace('<h1>Claim Overview</h1>', '<h1>AVeriTeC + AVerImaTeC</h1>')
# gold labels here are AVeriTeC-style verdict strings, not VeriTaS bands
html = html.replace('if ((g.startsWith("true") && p==="Supported") || (g.startsWith("false") && p==="Refuted")) return "ok";', 'if (g && g===p) return "ok";')
# dataset filter + EV2R chip + image/attach tags
html = html.replace('<label>Verdict: <select id="fVerdict">', '<label>Dataset: <select id="fDs"><option value="">Both</option><option value="AVerImaTeC">AVerImaTeC (new URL stage)</option><option value="AVeriTeC">AVeriTeC (older URL stage)</option></select></label> <label>Verdict: <select id="fVerdict">')
html = html.replace('for(const id of ["fVerdict","fMod","fEv","fOrder"])', 'for(const id of ["fDs","fVerdict","fMod","fEv","fOrder"])')
html = html.replace('    if(fv && vclass(d)!==fv) continue;', '    const fds=document.getElementById("fDs").value; if(fds && d.ds!==fds) continue;\n    if(fv && vclass(d)!==fv) continue;')
html = html.replace('<span class="chip mod">${d.mod}</span>', '<span class="chip mod">${d.mod}</span><span class="chip mod">${d.ds}</span>${d.ev2r?`<span class="chip mod" title="official-protocol EV2R, evidence score for this claim">EV2R R ${d.ev2r.R} · P ${d.ev2r.P}</span>`:""}')
html = html.replace('const label=e.p==="external-verified"?"External search":e.p;', 'const label=e.p==="external-verified"?"External search":e.p==="image"?"Image evidence":e.p==="metadata"?"Metadata (no URL by design)":e.p;')
html = html.replace('.tag.metadata{', '.tag.image{background:var(--info-soft);color:var(--info)}\n.tag.metadata{', 1) if '.tag.metadata{' in html else html.replace('</style>', '.tag.image{background:var(--info-soft);color:var(--info)}\n</style>', 1)
html = html.replace('<option value="external-verified">Has external (date-verified)</option>', '<option value="external-verified">Has external (date-verified)</option><option value="image">Has image evidence</option>')
# nav: this page is the third review page
html = re.sub(r'<div class="navlinks">.*?</div>', '<div class="navlinks"><a href="../">Home</a><a href="../veritas-intake-review/">VeriTaS Intake</a><a href="#" class="on">AVeriTeC + AVerImaTeC</a><a href="../baseline-reproduce/">Baseline Reproduce</a><a href="../deepfake-filter/">Deep Fake Filter</a></div>', html, count=1, flags=re.S)
# intro note: replace the intake page's own note block
note = (f'<div class="note"><b>Two datasets with ground truth, one page.</b> AVerImaTeC val ({n_amt} claims, {n_ev_amt} evidence items) '
        'is the 2026-08-30 run of our pipeline after the new URL stage: for each evidence statement the article\'s own hyperlinks are shortlisted first and a dated external-search '
        'URL second; the statement keeps whichever link it got, and the verifier\'s verdict on that link is shown but did not decide anything. Only statements with no candidate link '
        'of any kind were dropped (18 of 397). Image evidence and metadata carry no URL by design and are kept. The EV2R chip on each card is the official-protocol evidence score for '
        'that claim; over the set it is R 0.733 / P 0.621, level with the run before the URL stage (R 0.724 / P 0.619), because EV2R scores statements, not links. '
        'AVeriTeC (20 claims) is the earlier text-only run and has not yet been through the new URL stage; it is labelled as such.</div>')
html = re.sub(r'<div class="note">.*?</div>\s*<div class="controls">', note+'\n<div class="controls">', html, count=1, flags=re.S)
(OUT/'index.html').write_text(html, encoding='utf-8')
print(f'wrote averitec-averimatec-review/index.html  AVerImaTeC {n_amt} claims / {n_ev_amt} evidence, AVeriTeC {len(old)} claims; images {len(list((OUT/"media").iterdir()))}')
