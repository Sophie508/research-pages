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
                   'before': e.get('statement_before_settle', ''), 'prev': e.get('source_url_before_settle', ''),
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
  const basis=e.lang_basis==="url_marker"?"from address":e.lang_basis==="page_text"?"detected from page":e.lang_basis==="url_slug_script"?"from address script":e.lang_basis?"language not detected":"";
  const link=e.u?`<div class="source-row"><div class="evmeta"><span class="tag ${esc(e.p)}">${esc(PL[e.p]||e.p)}</span><span class="tag lang">${esc(LN[e.lang]||e.lang)}</span>${basis?`<span>${esc(basis)}</span>`:""}${e.st?`<span class="mono">${esc(SL[e.st]||e.st)}</span>`:""}</div>${sourceLink(e.u)}${e.h?` · <a href="${esc(e.h)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">highlighted ↗</a>`:""}${e.prev?`<div class="evmeta"><span>Replaced the link first attached:</span> ${sourceLink(e.prev)}</div>`:""}</div>`
    :`<div class="evmeta"><span class="tag ${esc(e.p)}">${esc(PL[e.p]||e.p)}</span></div>`;
  const others=e.cands.filter(c=>c.url!==e.u);
  const cands=others.length?`<details class="source-history" onclick="event.stopPropagation()"><summary>Other links checked, not used (${others.length})</summary><div class="muted">Each was checked for this statement and not chosen. The label is the link stage's first check of the page; the link above is the one the final check kept.</div>${others.map(c=>`<div class="source-row"><span class="mono">${esc(c.verdict)}</span> ${sourceLink(c.url)}</div>`).join("")}</details>`:"";
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

# ---- comparison of search languages (2026-10-12), rendered as a static section under the claim grid
import html as _html, shutil
from urllib.parse import urlsplit
AB = SRC.parent / 'search_ab'
VERSIONS = [('published', 'Shown above', 'English search; links ranked against the English statement'),
            ('en', 'English search', 'links ranked against the quoted passage'),
            ('original', 'Original-language search', 'links ranked against the quoted passage'),
            ('both', 'Both searches', 'original language first, then English')]
STATUS = {'kept': 'supported', 'kept_rewritten': 'cut back, supported', 'kept_compound': 'two pages together',
          'kept_archived': 'archived page supports it', 'replaced': 'replaced, supported',
          'rewritten_to_cited_source': 'cut back to cited source', 'unverifiable': 'page unreadable, not checked'}
LABEL = {'Refuted': 'Refuted', 'Supported': 'Supported', 'Not Enough Evidence': 'Not enough evidence',
         'Conflicting Evidence/Cherrypicking': 'Conflicting / cherry-picking'}
esc = lambda t: _html.escape(str(t or ''))


def compare_section():
    pub = json.loads((AB / 'search_ab_results.json').read_text(encoding='utf-8'))['claims']
    arms = {a: json.loads((AB / f'search_ab_results_{a}.json').read_text(encoding='utf-8'))['claims'] for a in ('en', 'original', 'both')}
    extracted = {r['claim_id']: [e['statement'] for e in r['extracted']['evidence_set']]
                 for r in json.loads((SRC.parent / 'multilingual_results_v2.json').read_text(encoding='utf-8'))}
    (OUT / 'snapshots').mkdir(parents=True, exist_ok=True)

    def link(e):
        url, hl = e.get('source_url', ''), e.get('highlight_url') or ''
        if hl.startswith('snapshots/'):                     # copy the marked text copy next to the page
            for a in ('en', 'original', 'both'):
                f = AB / f'snapshots_{a}' / hl.split('/', 1)[1]
                if f.exists():
                    shutil.copy(f, OUT / 'snapshots' / f.name); break
        host = urlsplit(url).netloc.replace('www.', '') if url else ''
        out = f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(host)}</a>' if url else ''
        if hl:
            out += f' · <a href="{esc(hl)}" target="_blank" rel="noopener">highlighted ↗</a>'
        return out

    rows, details = [], []
    for cid in ('26141', '5567', '10888'):
        c = pub[cid]
        per = {'published': c['arms']['published'], **{a: arms[a][cid]['arms'][a] for a in arms}}
        cells = ''.join(f'<td><b>{esc(LABEL.get(per[k]["label"], per[k]["label"]))}</b><br><span class="muted">{len(per[k]["evidence"])} evidence</span></td>' for k, _, _ in VERSIONS)
        lang = {'ar': 'Arabic', 'hi': 'Hindi', 'te': 'Telugu'}[c['lang']]
        rows.append(f'<tr><th>{lang}<br><span class="muted">{esc(c["claim_en"][:90])}…</span></th>{cells}<td>{esc(c["veritas"])}</td></tr>')
        body = []
        for i, stmt in enumerate(extracted[cid], 1):
            tds = []
            for k, _, _ in VERSIONS:
                e = next((x for x in per[k]['evidence'] if (x.get('statement_before_settle') or x['statement']) == stmt), None)
                tds.append('<td class="muted">dropped</td>' if e is None else
                           f'<td>{esc(STATUS.get(e["url_status"], e["url_status"]))}<br>{link(e)}</td>')
            body.append(f'<tr><th>E{i}. {esc(stmt)}</th>{"".join(tds)}</tr>')
        heads = ''.join(f'<th>{esc(t)}</th>' for _, t, _ in VERSIONS)
        details.append(f'<details class="cmp-claim"><summary>{lang}: evidence per version</summary>'
                       f'<div class="cmp-scroll"><table class="cmp"><tr><th>Extracted evidence</th>{heads}</tr>{"".join(body)}</table></div></details>')
    heads = ''.join(f'<th>{esc(t)}<br><span class="muted">{esc(d)}</span></th>' for _, t, d in VERSIONS)
    return f"""<section class="cmp-section">
<h2>Does the search language change the evidence or the verdict?</h2>
<p>The same three claims, run four ways. The first column is the version shown above. The other three restart every statement
from the extractor's citation and differ only in the language of the web search used when the article's own links do not support
a statement: the English statement, the statement in the article's language, or both. All three rank the article's links against
the quoted passage, which is in the article's language. Each version then goes through the pipeline's merge and verdict prompts,
with the English claim. These claims have no gold evidence, so there is no EV2R score; the VeriTaS verdict is given for reference.</p>
<div class="cmp-scroll"><table class="cmp"><tr><th>Claim</th>{heads}<th>VeriTaS</th></tr>{''.join(rows)}</table></div>
<p><b>What it shows.</b> The verdict is the same in every version and agrees with VeriTaS. For the Arabic and Hindi claims the
links are the same under all three searches: every statement got its link from the article itself, so no search was needed. For the
Telugu claim, about a press conference in Washington, the English search added English news coverage (Times of India, OPB), and the
Telugu search found nothing the article's own links did not already give. Some differences between versions are run-to-run noise
rather than language: pages are fetched live, and the White House page was read directly in one run and from its Wayback copy in
another. Ranking against the quoted passage made the article's Facebook links come first for a few statements; Facebook pages cannot be
read, so those statements are kept as unreadable instead of being re-sourced or dropped.</p>
<p><b>Limits.</b> Three claims, chosen because their articles cite outside sources, mostly English-language institutions. This says
little about claims on local events whose sources are in the local language, where searching in the original language should matter
most.</p>
{''.join(details)}
</section>"""


html = html.replace('<div class="grid" id="grid"></div>', '<div class="grid" id="grid"></div>\n' + compare_section(), 1)
html = html.replace('</style>', '.cmp-section{max-width:1100px;margin:40px auto 24px;padding:0 16px;color:var(--ink2);line-height:1.6}\n'
                    '.cmp-section h2{color:var(--ink);font-size:1.3rem}.cmp-scroll{overflow-x:auto}\n'
                    'table.cmp{border-collapse:collapse;width:100%;min-width:760px;margin:12px 0;font-size:.9rem;background:var(--card)}\n'
                    'table.cmp th,table.cmp td{border:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}\n'
                    'table.cmp th{color:var(--ink);font-weight:600}.cmp-section .muted{color:var(--ink3);font-weight:400}\n'
                    'details.cmp-claim{margin:10px 0}details.cmp-claim summary{cursor:pointer;color:var(--ink);font-weight:600}\n</style>', 1)

for marker in ('fLang', 'Multilingual Claims', 'evidenceHTML(e){\n  const LN', 'cmp-section'):
    assert marker in html, f'template patch failed: {marker}'
OUT.mkdir(exist_ok=True)
(OUT / 'index.html').write_text(html, encoding='utf-8')
print(f'wrote multilingual/index.html  claims={len(rows)}  evidence={n_ev}  langs={dict(lang_count)}  provenance={dict(prov_count)}')
