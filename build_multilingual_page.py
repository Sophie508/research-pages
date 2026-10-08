#!/usr/bin/env python3
"""Build the Multilingual page from the intake page template.

Three non-English VeriTaS claims (Arabic, Hindi, Telugu) run through our pipeline:
English evidence statements extracted from the original-language fact-checking
article, each also written in the article's language, then the pipeline's URL stage
(e2e/link_evidence_sources.py --settle): article links first, then a date-restricted
search, then the settle step that keeps looking until a page supports the statement,
drops it otherwise, and marks the supporting passages on the page.
Every attached link carries the language of the page it points to.
"""
import json, re, collections
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / 'veritas-intake-review/index.html'
OUT = HERE / 'multilingual'
SRC = Path('/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs/multilingual_20261008/multilingual_results_settled_v2.json')
LANG = {'ar': 'Arabic', 'hi': 'Hindi', 'te': 'Telugu', 'ta': 'Tamil', 'en': 'English', 'unknown': 'unknown'}

rows, lang_count, prov_count = [], collections.Counter(), collections.Counter()
for r in json.loads(SRC.read_text(encoding='utf-8')):
    if r.get('status') != 'ok': continue
    ev = []
    for e in (r['extracted'].get('evidence_set') or []):
        cands = (e.get('link_sources') or {}).get('candidates') or []
        ev.append({'s': e.get('statement', ''), 'o': e.get('statement_original', ''), 'span': e.get('support_span', ''),
                   'u': e.get('source_url') or '', 'p': e.get('provenance', 'none'),
                   'lang': e.get('source_lang', ''), 'lang_basis': e.get('source_lang_basis', ''),
                   'h': e.get('highlight_url') or '', 'st': e.get('url_status', ''),
                   'before': e.get('statement_before_settle', ''),
                   'cands': [{'url': c['url'], 'verdict': c.get('verdict', '')} for c in cands]})
        lang_count[e.get('source_lang') or 'no_url'] += 1; prov_count[e.get('provenance', 'none')] += 1
    rows.append({'id': int(r['claim_id']), 'claim': r['text'], 'claim_en': r.get('claim_en', ''), 'lang': r['lang'],
                 'date': r['date'], 'mod': 'text-only',
                 'pred': '', 'gold': '', 'art': r['article'], 'pub': r['publisher'], 'img': '', 'orig': '',
                 'veritas': r['veritas_url'], 'ev': ev})
n_ev = sum(len(r['ev']) for r in rows)

html = TEMPLATE.read_text(encoding='utf-8')
html = re.sub(r'(const DATA\s*=\s*)\[.*?\](;\s*\n)', lambda m: m.group(1) + json.dumps(rows, ensure_ascii=False).replace('</', '<\\/') + m.group(2), html, flags=re.S)
html = html.replace('<title>MCFC Bench — Claim Browser</title>', '<title>MCFC Bench · Multilingual</title>')
html = html.replace('<h1>Claim Overview</h1>', '<h1>Multilingual Claims</h1>')
html = re.sub(r'<div class="navlinks">.*?</div>', '<div class="navlinks"><a href="../">Home</a><a href="../veritas-intake-review/">VeriTaS Intake</a><a href="../deepfake-filter/">Deep Fake Filter</a></div>', html, count=1, flags=re.S)

lang_txt = ', '.join(f'{LANG.get(k, k) if k != "no_url" else "no link attached"} {v}' for k, v in lang_count.most_common())
note = (f'<div class="revision-note"><b>Non-English fact-checks through our pipeline: {len(rows)} claims, {n_ev} evidence statements.</b> '
        'Claims in Arabic, Hindi and Telugu, taken from the VeriTaS claim browser: text claims whose fact-checking article cites outside '
        'sources (regulators, government sites, news reports), so that the evidence can be checked against pages other than the fact-check. The extractor reads the original-language '
        'fact-checking article and writes each evidence statement in English; the statement is also given in the article\'s '
        'language, and the quoted passage it came from is kept as written. Links come from the pipeline\'s URL stage, the same '
        'procedure the annotation interface uses: the article\'s own hyperlinks first, then a web search restricted to pages dated '
        'before the claim. An LLM then reads each linked page and checks that it states the evidence. When it does not, the '
        'statement is cut back to what the page says, or other pages are tried: the article\'s cited sources as archived on or '
        'before the claim date, the other evidence pages of the claim, then a new search. A statement no page supports is dropped. '
        '"Highlighted" opens the page with the supporting passages marked, or a text copy of it when the passages cannot be marked '
        'on the live page. The language of each linked page is read from a language marker '
        'in its address when there is one, otherwise detected from the page text and kept only when the detector is at least 90% sure. '
        f'Linked-page languages: {lang_txt}. Three claims are far too few for a distribution; this page is for checking quality.</div>')
html = re.sub(r'<div class="revision-note">.*?</div>', note, html, count=1, flags=re.S)

controls = ('<div class="controls"> <label>Claim language: <select id="fLang"><option value="">All</option>'
            '<option value="ar">Arabic</option><option value="hi">Hindi</option><option value="te">Telugu</option></select></label> '
            '<span class="count" id="count"></span> </div>')
html = re.sub(r'<div class="controls">.*?</div>\s*<div class="grid" id="grid"></div>', controls + '\n<div class="grid" id="grid"></div>', html, count=1, flags=re.S)

evidence_js = r'''function evidenceHTML(e){
  const LN={ar:"Arabic",hi:"Hindi",te:"Telugu",ta:"Tamil",en:"English",unknown:"language unknown","ru/uk":"Cyrillic"};
  const PL={"article_link":"Article link","external_search":"External search","extractor":"Extractor citation","metadata":"Metadata","none":"No URL"};
  const SL={kept:"page supports it",kept_rewritten:"cut back to what the page says",kept_compound:"supported by two pages together",kept_archived:"supported by the archived page",replaced:"replaced by a page that supports it",rewritten_to_cited_source:"cut back to the article's cited source",unverifiable:"page could not be read; not checked"};
  const basis=e.lang_basis==="url_marker"?"from address":e.lang_basis==="page_text"?"detected from page":e.lang_basis==="url_slug_script"?"from address script":e.lang_basis?"page unreadable":"";
  const link=e.u?`<div class="source-row"><div class="evmeta"><span class="tag ${esc(e.p)}">${esc(PL[e.p]||e.p)}</span><span class="tag lang">${esc(LN[e.lang]||e.lang)}</span>${basis?`<span>${esc(basis)}</span>`:""}${e.st?`<span class="mono">${esc(SL[e.st]||e.st)}</span>`:""}</div>${sourceLink(e.u)}${e.h?` · <a href="${esc(e.h)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">highlighted ↗</a>`:""}</div>`
    :`<div class="evmeta"><span class="tag ${esc(e.p)}">${esc(PL[e.p]||e.p)}</span></div>`;
  const cands=e.cands.length?`<details class="source-history" onclick="event.stopPropagation()"><summary>Candidates judged (${e.cands.length})</summary>${e.cands.map(c=>`<div class="source-row"><span class="mono">${esc(c.verdict)}</span> ${sourceLink(c.url)}</div>`).join("")}</details>`:"";
  const before=e.before?`<details class="source-history" onclick="event.stopPropagation()"><summary>Statement before it was cut back</summary><div>${esc(e.before)}</div></details>`:"";
  return `<div class="evitem">${esc(e.s)}${before}${e.o?`<div class="deconbox" dir="auto">${esc(e.o)}</div>`:""}<details class="source-history" onclick="event.stopPropagation()"><summary>Passage in the article</summary><div dir="auto">${esc(e.span)}</div></details>${link}${cands}</div>`;
}'''
html = re.sub(r'function evidenceHTML\(e\)\{.*?\n\}\n// END ARTICLE SOURCE RENDERER', evidence_js + '\n// END ARTICLE SOURCE RENDERER', html, count=1, flags=re.S)

html = html.replace('''  <div class="claimtext">${esc(d.claim)}</div>''', '''  <div class="claimtext" dir="auto">${esc(d.claim)}</div>${d.claim_en?`<div class="source-label">${esc(d.claim_en)}</div>`:""}''')
html = html.replace('''  <span class="chip v-${vc}" style="margin-left:auto">${vlabel}${esc(d.pred||"—")}${d.gold?` · gold: ${esc(d.gold)}`:""}</span></div>''',
                    '''  <span class="chip mod">${esc({ar:"Arabic",hi:"Hindi",te:"Telugu"}[d.lang]||d.lang)}</span><span class="chip mod" style="margin-left:auto">${esc(d.pub)}</span></div>''')
html = html.replace('''  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article ↗</a></div></div></div>`;''',
                    '''  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article (${esc(d.pub)}) ↗</a> · <a href="${esc(d.veritas)}" target="_blank" onclick="event.stopPropagation()">VeriTaS claim page ↗</a></div></div></div>`;''')
html = html.replace('''  const fv=document.getElementById("fVerdict").value, fm=document.getElementById("fMod").value,
        fe=document.getElementById("fEv").value, ord=document.getElementById("fOrder").value;''', '''  const fl=document.getElementById("fLang").value, ord="desc";''')
html = html.replace('''    if(fv && vclass(d)!==fv) continue;
    if(fm && d.mod!==fm) continue;
    if(fe && !d.ev.some(e=>e.p===fe)) continue;''', '''    if(fl && d.lang!==fl) continue;''')
html = html.replace('for(const id of ["fVerdict","fMod","fEv","fOrder"])', 'for(const id of ["fLang"])')
html = html.replace('</style>', '.tag.lang{background:var(--info-soft);color:var(--info)}\n.tag.external_search{background:var(--warn-soft);color:var(--warn)}\n.tag.extractor{background:var(--ok-soft);color:var(--ok)}\n</style>', 1)

for marker in ('fLang', 'Multilingual Claims', 'evidenceHTML(e){\n  const LN'):
    assert marker in html, f'template patch failed: {marker}'
OUT.mkdir(exist_ok=True)
(OUT / 'index.html').write_text(html, encoding='utf-8')
print(f'wrote multilingual/index.html  claims={len(rows)}  evidence={n_ev}  langs={dict(lang_count)}  provenance={dict(prov_count)}')
