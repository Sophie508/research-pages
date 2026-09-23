#!/usr/bin/env python3
"""Build the Deep Fake Filter page from the intake page template, so it looks
and behaves like the other review pages: every claim is a card with its media
on top, and the card opens on click to show the evidence.

Selection is one rule: the claim has media and at least one medium's
authenticity label from the VeriTaS four-model ensemble starts with
"fabricated". Tags, confidence and contextualization are VeriTaS's own. Where
our pipeline has been run on a claim, its evidence statements appear inside the
card in the intake page's evidence format; the rest open to VeriTaS's own
explanation and the source links until they are run.
"""
import json, re
from pathlib import Path
HERE = Path(__file__).resolve().parent
TEMPLATE = HERE/'veritas-intake-review/index.html'
OUT = HERE/'deepfake-filter'
raw = json.loads((OUT/'data.json').read_text(encoding='utf-8'))
EXTRACT = Path('/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs/deepfake_claims_20260923/extract3/extract3_results.json')
ext = {}
if EXTRACT.exists():
    for r in json.loads(EXTRACT.read_text(encoding='utf-8')):
        if r.get('status') != 'ok': continue
        ev = []
        for e in (r.get('extracted') or {}).get('evidence_set') or []:
            item = {'s': e.get('statement',''), 'u': e.get('source_url') or '', 'd': '', 'p': e.get('provenance','none')}
            if e.get('article_candidates'):
                item['article_sources'] = [{'url': c['url'], 'rank': k, 'origin': 'ARTICLE_HYPERLINK', 'selected': c['url']==e.get('source_url'),
                                            'support_status': c['verdict'], 'support_reason': c.get('why',''), 'role': None,
                                            'material': {'source_type': 'UNKNOWN', 'format': 'HTML'}} for k, c in enumerate(e['article_candidates'], 1)]
                item['previous_source'] = {'url': '', 'date': ''}
            ev.append(item)
        ext[str(r['claim_id'])] = ev
rows = []
for d in raw:
    rv = (d.get('reviews') or [{}])[0]
    rows.append({'id': d['id'], 'claim': d['claim'], 'date': d.get('date',''), 'mod': 'image-text', 'pred': '', 'gold': '',
                 'art': rv.get('url',''), 'img': f"media/{d['imgs'][0]}" if d.get('imgs') else '', 'orig': '',
                 'ev': ext.get(str(d['id']), []),
                 'tags': d['tags'], 'conf': d['conf'], 'score': d['score'], 'ctx': d.get('ctx',[]), 'veracity': d.get('veracity',''),
                 'why': d.get('why',''), 'rating': rv.get('rating',''), 'pub': rv.get('pub',''), 'app': (d.get('appearances') or [''])[0]})
n = len(rows); n_ext = sum(1 for r in rows if r['ev'])
tagc = {t: sum(1 for r in rows if t in r['tags']) for t in ('AI-generated','Manipulated','Forged')}
confc = {c: sum(1 for r in rows if r['conf']==c) for c in ('certain','rather certain','rather uncertain')}

html = TEMPLATE.read_text(encoding='utf-8')
html = re.sub(r'(const DATA\s*=\s*)\[.*?\](;\s*\n)', lambda m: m.group(1)+json.dumps(rows, ensure_ascii=False)+m.group(2), html, flags=re.S)
html = html.replace('<title>MCFC Bench — Claim Browser</title>', '<title>MCFC Bench — Deep Fake Filter</title>')
html = html.replace('<h1>Claim Overview</h1>', '<h1>Deep Fake Filter</h1>')
html = re.sub(r'<div class="navlinks">.*?</div>', '<div class="navlinks"><a href="../">Home</a><a href="../veritas-intake-review/">VeriTaS Intake</a><a href="../averitec-averimatec-review/">AVeriTeC + AVerImaTeC</a><a href="../baseline-reproduce/">Baseline Reproduce</a><a href="#" class="on">Deep Fake Filter</a></div>', html, count=1, flags=re.S)
note = (f'<div class="note"><b>The VeriTaS claims whose media VeriTaS itself judged fabricated: {n} of 197 in the export.</b> One selection rule: the claim carries media, and at least one medium\'s '
        'authenticity label from the VeriTaS four-model ensemble is "fabricated" at any confidence. Real media in a false context is excluded as a contextualization failure, not a fabrication. '
        f'Tags are VeriTaS\'s: AI-generated {tagc["AI-generated"]}, Manipulated {tagc["Manipulated"]}, Forged {tagc["Forged"]} (a claim may carry several); confidence certain {confc["certain"]}, '
        f'rather certain {confc["rather certain"]}, rather uncertain {confc["rather uncertain"]}. Click a card to open it. Our pipeline has been run on {n_ext} claims so far; those cards show the '
        'extracted evidence with the link each statement ended up with, in the same format as the intake page. The others open to VeriTaS\'s own explanation of the verdict and the source links.</div>')
html = re.sub(r'<div class="revision-note">.*?</div>', note.replace('<div class="note">','<div class="revision-note">',1), html, count=1, flags=re.S)
# filters: tag, confidence, extracted, order (replace verdict/modality/evidence filters)
controls = ('<div class="controls"> <label>Tag: <select id="fTag"><option value="">All</option><option value="AI-generated">AI-generated</option><option value="Manipulated">Manipulated</option><option value="Forged">Forged</option></select></label> '
            '<label>Confidence: <select id="fConf"><option value="">All</option><option value="certain">certain</option><option value="rather certain">rather certain</option><option value="rather uncertain">rather uncertain</option></select></label> '
            '<label>Evidence: <select id="fEv"><option value="">All claims</option><option value="yes">Extracted by our pipeline</option></select></label> '
            '<label>Order: <select id="fOrder"><option value="desc">Newest first</option><option value="asc">Oldest first</option></select></label> <span class="count" id="count"></span> </div>')
html = re.sub(r'<div class="controls">.*?</div>\s*<div class="grid" id="grid"></div>', controls+'\n<div class="grid" id="grid"></div>', html, count=1, flags=re.S)
# card: tags + confidence in the footer instead of verdict chip; detail shows VeriTaS explanation, rating, evidence, sources
html = html.replace('''  <span class="chip v-${vc}" style="margin-left:auto">${vlabel}${esc(d.pred||"—")}${d.gold?` · gold: ${esc(d.gold)}`:""}</span></div>''',
'''  ${d.tags.map(t=>`<span class="chip mod">${esc(t)}</span>`).join("")}<span class="chip mod" style="margin-left:auto">${esc(d.conf)} · ${d.score}</span>${d.ev.length?`<span class="chip mod">extracted</span>`:""}</div>''')
html = html.replace('''  <div class="detail">${decon}<h4>Evidence (${d.ev.length})</h4>${ev}
  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article ↗</a></div></div></div>`;''',
'''  <div class="detail"><h4>VeriTaS verdict</h4><div class="deconbox">${esc(d.why)}</div>
  <div class="cfoot"><span>context: ${esc((d.ctx||[]).join(", ")||"n/a")}</span><span>veracity: ${esc(d.veracity||"n/a")}</span>${d.rating?`<span>publisher rating: ${esc(d.rating)}</span>`:""}</div>
  ${d.ev.length?`<h4>Evidence (${d.ev.length}) · extracted by our pipeline</h4>${ev}`:`<h4>Evidence</h4><div class="deconbox">Not run through our pipeline yet.</div>`}
  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article (${esc(d.pub||"")}) ↗</a>${d.app?` · <a href="${esc(d.app)}" target="_blank" onclick="event.stopPropagation()">original post ↗</a>`:""}</div></div></div>`;''')
# render: new filters
html = html.replace('''  const fv=document.getElementById("fVerdict").value, fm=document.getElementById("fMod").value,
        fe=document.getElementById("fEv").value, ord=document.getElementById("fOrder").value;''',
'''  const ft=document.getElementById("fTag").value, fc=document.getElementById("fConf").value,
        fe=document.getElementById("fEv").value, ord=document.getElementById("fOrder").value;''')
html = html.replace('''    if(fv && vclass(d)!==fv) continue;
    if(fm && d.mod!==fm) continue;
    if(fe && !d.ev.some(e=>e.p===fe)) continue;''',
'''    if(ft && !d.tags.includes(ft)) continue;
    if(fc && d.conf!==fc) continue;
    if(fe && !d.ev.length) continue;''')
html = html.replace('for(const id of ["fVerdict","fMod","fEv","fOrder"])', 'for(const id of ["fTag","fConf","fEv","fOrder"])')
html = html.replace('const label=e.p==="external-verified"?"External search":e.p;', 'const label=e.p==="external-verified"?"External search":e.p==="none"?"No URL (fact-checker finding)":e.p;')
html = html.replace('</style>', '.tag.none{background:var(--na-soft, #fffaeb);color:var(--na, #854708)}\n.tag.article-recovered{background:var(--ok-soft, #ecfdf3);color:var(--ok, #067647)}\n</style>', 1)
(OUT/'index.html').write_text(html, encoding='utf-8')
print(f'wrote deepfake-filter/index.html  n={n}  extracted={n_ext}  tags={tagc}  conf={confc}')
