#!/usr/bin/env python3
"""Build the Multilingual page from the intake page template.

Ten non-English VeriTaS claims through our pipeline (analysis_outputs/multilingual_20261008/run_ml_ten.py):
English evidence statements extracted from the original-language fact-checking article, each also
written in the article's language; the pipeline's URL stage with the settle step; then the pipeline's
merge and verdict prompts. Run twice, with the web search in English and in the article's language.
The claim cards show the English-search run; a section below compares the two runs claim by claim.
"""
import html as _html, json, re, shutil, collections
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / 'veritas-intake-review/index.html'
OUT = HERE / 'multilingual'
TEN = Path('/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs/multilingual_20261008/ten')
NOTES = TEN / 'page_notes.json'          # the short reading of the comparison, written after looking at the runs
LANG = {'ar': 'Arabic', 'hi': 'Hindi', 'te': 'Telugu', 'ta': 'Tamil', 'bn': 'Bengali', 'es': 'Spanish', 'pt': 'Portuguese',
        'fr': 'French', 'de': 'German', 'en': 'English', 'unknown': 'unknown'}
LABEL = {'Refuted': 'Refuted', 'Supported': 'Supported', 'Not Enough Evidence': 'Not enough evidence',
         'Conflicting Evidence/Cherrypicking': 'Conflicting / cherry-picking'}
STATUS = {'kept': 'supported', 'kept_rewritten': 'cut back, supported', 'kept_compound': 'two pages together',
          'kept_archived': 'archived page supports it', 'replaced': 'replaced, supported',
          'rewritten_to_cited_source': 'cut back to cited source', 'unverifiable': 'page unreadable, not checked'}
esc = lambda t: _html.escape(str(t or ''))

runs = {arm: json.loads((TEN / f'results_{arm}.json').read_text(encoding='utf-8'))['claims'] for arm in ('en', 'original')}
order = list(runs['en'])
(OUT / 'snapshots').mkdir(parents=True, exist_ok=True)


def keep_snapshot(hl, arm):
    """Copy a marked text copy next to the page; returns the link unchanged."""
    if hl and hl.startswith('snapshots/'):
        f = TEN / f'snapshots_{arm}' / hl.split('/', 1)[1]
        if f.exists():
            shutil.copy(f, OUT / 'snapshots' / f.name)
    return hl


# ---- claim cards: the English-search run
rows, lang_count = [], collections.Counter()
for cid in order:
    c = runs['en'][cid]
    ev = []
    for e in c['evidence']:
        cands = (e.get('link_sources') or {}).get('candidates') or []
        ev.append({'s': e.get('statement', ''), 'o': e.get('statement_original', ''), 'span': e.get('support_span', ''),
                   'u': e.get('source_url') or '', 'p': e.get('provenance', 'none'),
                   'lang': e.get('source_lang', ''), 'lang_basis': e.get('source_lang_basis', ''),
                   'h': keep_snapshot(e.get('highlight_url') or '', 'en'), 'st': e.get('url_status', ''),
                   'before': e.get('statement_before_settle', ''), 'prev': e.get('source_url_before_settle', ''),
                   'cands': [{'url': x['url'], 'verdict': x.get('verdict', '')} for x in cands]})
        lang_count[e.get('source_lang') or 'no_url'] += 1
    rows.append({'id': int(cid), 'claim': c['claim'], 'claim_en': c.get('claim_en', ''), 'lang': c['lang'], 'date': c['date'],
                 'mod': 'text-only', 'pred': LABEL.get(c['label'], c['label']), 'gold': '', 'vt': c.get('veritas', ''),
                 'art': c['article'], 'pub': c.get('publisher', ''), 'img': '', 'orig': '', 'veritas': c.get('veritas_url', ''),
                 'ev': ev})
n_ev = sum(len(r['ev']) for r in rows)
n_ex = sum(runs['en'][c]['n_extracted'] for c in order)
langs_present = sorted({r['lang'] for r in rows}, key=lambda k: LANG.get(k, k))

html = TEMPLATE.read_text(encoding='utf-8')
html = re.sub(r'(const DATA\s*=\s*)\[.*?\](;\s*\n)', lambda m: m.group(1) + json.dumps(rows, ensure_ascii=False).replace('</', '<\\/') + m.group(2), html, flags=re.S)
html = html.replace('<title>MCFC Bench — Claim Browser</title>', '<title>MCFC Bench · Multilingual</title>')
html = html.replace('<h1>Claim Overview</h1>', '<h1>Multilingual Claims</h1>')
html = re.sub(r'<div class="navlinks">.*?</div>', '<div class="navlinks"><a href="../">Home</a><a href="../veritas-intake-dashboard/">VeriTaS Intake</a><a href="../deepfake-filter/">Deep Fake Filter</a></div>', html, count=1, flags=re.S)

lang_txt = ', '.join(f'{LANG.get(k, k) if k != "no_url" else "no link attached"} {v}' for k, v in lang_count.most_common())
claim_langs = ', '.join(f'{LANG[k]} {sum(1 for r in rows if r["lang"] == k)}' for k in langs_present)
note = (f'<div class="revision-note"><b>Non-English fact-checks through our pipeline: {len(rows)} claims, {n_ex} evidence statements '
        f'extracted, {n_ev} kept.</b> Claim languages: {claim_langs}. All are text claims from the VeriTaS claim browser whose '
        'fact-checking article cites outside sources; seven were picked because the event is local and the sources are in the '
        'local language. The extractor reads the original-language article and writes each evidence statement in English; the '
        'statement is also given in the article\'s language, and the quoted passage it came from is kept as written. Links come '
        'from the pipeline\'s URL stage, the procedure the annotation interface uses: the article\'s own hyperlinks first (ranked '
        'against the quoted passage), then a web search restricted to pages dated before the claim. An LLM reads each linked page '
        'and checks that it states the evidence; when it does not, the statement is cut back to what the page says, or other pages '
        'are tried, and a statement no page supports is dropped. The verdict comes from the pipeline\'s merge and verdict prompts '
        'with the English claim. The cards show the run whose web search used the English statement; the section below the cards '
        'compares it with a run whose search used the statement in the article\'s language. "Highlighted" opens the page with the '
        'supporting passages marked, or a text copy of it. The language of each linked page is read from a marker in its address, '
        f'otherwise detected from the page text at 90% confidence or more. Linked-page languages: {lang_txt}. Ten claims are too few '
        'for rates; this page is for checking quality.</div>')
html = re.sub(r'<div class="revision-note">.*?</div>', note, html, count=1, flags=re.S)

options = ''.join(f'<option value="{k}">{LANG[k]}</option>' for k in langs_present)
controls = ('<div class="controls"> <label>Claim language: <select id="fLang"><option value="">All</option>' + options +
            '</select></label> <span class="count" id="count"></span> </div>')
html = re.sub(r'<div class="controls">.*?</div>\s*<div class="grid" id="grid"></div>', controls + '\n<div class="grid" id="grid"></div>', html, count=1, flags=re.S)

lang_js = json.dumps({k: v for k, v in LANG.items() if k != 'unknown'}, ensure_ascii=False)
evidence_js = r'''function evidenceHTML(e){
  const LN=Object.assign(__LANGS__,{unknown:"language unknown","ru/uk":"Cyrillic"});
  const PL={"article_link":"Article link","external_search":"External search","extractor":"Extractor citation","metadata":"Metadata","none":"No URL"};
  const SL={kept:"page supports it",kept_rewritten:"cut back to what the page says",kept_compound:"supported by two pages together",kept_archived:"supported by the archived page",replaced:"replaced by a page that supports it",rewritten_to_cited_source:"cut back to the article's cited source",unverifiable:"page could not be read; not checked"};
  const basis=e.lang_basis==="url_marker"?"from address":e.lang_basis==="page_text"?"detected from page":e.lang_basis==="url_slug_script"?"from address script":e.lang_basis?"language not detected":"";
  const link=e.u?`<div class="source-row"><div class="evmeta"><span class="tag ${esc(e.p)}">${esc(PL[e.p]||e.p)}</span><span class="tag lang">${esc(LN[e.lang]||e.lang)}</span>${basis?`<span>${esc(basis)}</span>`:""}${e.st?`<span class="mono">${esc(SL[e.st]||e.st)}</span>`:""}</div>${sourceLink(e.u)}${e.h?` · <a href="${esc(e.h)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">highlighted ↗</a>`:""}${e.prev?`<div class="evmeta"><span>Replaced the link first attached:</span> ${sourceLink(e.prev)}</div>`:""}</div>`
    :`<div class="evmeta"><span class="tag ${esc(e.p)}">${esc(PL[e.p]||e.p)}</span></div>`;
  const others=e.cands.filter(c=>c.url!==e.u);
  const cands=others.length?`<details class="source-history" onclick="event.stopPropagation()"><summary>Other links checked, not used (${others.length})</summary><div class="muted">Each was checked for this statement and not chosen. The label is the link stage's first check of the page; the link above is the one the final check kept.</div>${others.map(c=>`<div class="source-row"><span class="mono">${esc(c.verdict)}</span> ${sourceLink(c.url)}</div>`).join("")}</details>`:"";
  const before=e.before?`<details class="source-history" onclick="event.stopPropagation()"><summary>Statement before it was cut back</summary><div>${esc(e.before)}</div></details>`:"";
  return `<div class="evitem">${esc(e.s)}${before}${e.o?`<div class="deconbox" dir="auto">${esc(e.o)}</div>`:""}<details class="source-history" onclick="event.stopPropagation()"><summary>Passage in the article</summary><div dir="auto">${esc(e.span)}</div></details>${link}${cands}</div>`;
}'''.replace('__LANGS__', lang_js)
html = re.sub(r'function evidenceHTML\(e\)\{.*?\n\}\n// END ARTICLE SOURCE RENDERER', lambda m: evidence_js + '\n// END ARTICLE SOURCE RENDERER', html, count=1, flags=re.S)

html = html.replace('''  <div class="claimtext">${esc(d.claim)}</div>''',
                    '''  <div class="claimtext" dir="auto">${esc(d.claim)}</div>${d.claim_en?`<div class="source-label">${esc(d.claim_en)}</div>`:""}'''
                    '''<div class="source-label"><b>Verdict:</b> ${esc(d.pred||"—")}${d.vt?` · VeriTaS: ${esc(d.vt)}`:""}</div>''')
html = html.replace('''  <span class="chip v-${vc}" style="margin-left:auto">${vlabel}${esc(d.pred||"—")}${d.gold?` · gold: ${esc(d.gold)}`:""}</span></div>''',
                    '''  <span class="chip mod">${esc((__LANGS__)[d.lang]||d.lang)}</span><span class="chip mod" style="margin-left:auto">${esc(d.pub)}</span></div>'''.replace('__LANGS__', lang_js))
html = html.replace('''  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article ↗</a></div></div></div>`;''',
                    '''  <h4>Source</h4><a href="${esc(d.art)}" target="_blank" onclick="event.stopPropagation()">fact-checking article (${esc(d.pub)}) ↗</a> · <a href="${esc(d.veritas)}" target="_blank" onclick="event.stopPropagation()">VeriTaS claim page ↗</a></div></div></div>`;''')
html = html.replace('''  const fv=document.getElementById("fVerdict").value, fm=document.getElementById("fMod").value,
        fe=document.getElementById("fEv").value, ord=document.getElementById("fOrder").value;''', '''  const fl=document.getElementById("fLang").value, ord="desc";''')
html = html.replace('''    if(fv && vclass(d)!==fv) continue;
    if(fm && d.mod!==fm) continue;
    if(fe && !d.ev.some(e=>e.p===fe)) continue;''', '''    if(fl && d.lang!==fl) continue;''')
html = html.replace('for(const id of ["fVerdict","fMod","fEv","fOrder"])', 'for(const id of ["fLang"])')


# ---- English search vs original-language search
def link_cell(e, arm):
    url, hl = e.get('source_url', ''), keep_snapshot(e.get('highlight_url') or '', arm)
    host = urlsplit(url).netloc.replace('www.', '') if url else ''
    out = f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(host)}</a>' if url else ''
    if hl:
        out += f' · <a href="{esc(hl)}" target="_blank" rel="noopener">highlighted ↗</a>'
    lang = e.get('source_lang', '')
    return out + (f' <span class="muted">({esc(LANG.get(lang, lang))})</span>' if lang and lang not in ('unknown', 'uncertain') else '')


def compare_section():
    summary, details = [], []
    agg = collections.Counter()
    for cid in order:
        a, b = runs['en'][cid], runs['original'][cid]
        ua = {e.get('source_url') for e in a['evidence'] if e.get('source_url')}
        ub = {e.get('source_url') for e in b['evidence'] if e.get('source_url')}
        local = lambda run: sum(1 for e in run['evidence'] if e.get('source_lang') == run['lang'])
        agg['claims'] += 1
        agg['verdict_differs'] += a['label'] != b['label']
        agg['links_differ'] += ua != ub
        agg['only_original'] += len(ub - ua); agg['only_english'] += len(ua - ub)
        agg['kept_en'] += len(a['evidence']); agg['kept_or'] += len(b['evidence'])
        agg['local_en'] += local(a); agg['local_or'] += local(b)
        agg['hl_en'] += sum(1 for e in a['evidence'] if e.get('highlight_url'))
        agg['hl_or'] += sum(1 for e in b['evidence'] if e.get('highlight_url'))
        cell = lambda run: (f'<td><b>{esc(LABEL.get(run["label"], run["label"]))}</b><br><span class="muted">{len(run["evidence"])} of '
                            f'{run["n_extracted"]} kept · {sum(1 for e in run["evidence"] if e.get("highlight_url"))} highlighted · '
                            f'{local(run)} in {esc(LANG.get(run["lang"]))}</span></td>')
        same = 'same links' if ua == ub else f'{len(ub - ua)} only via original, {len(ua - ub)} only via English'
        summary.append(f'<tr><th>{esc(LANG[a["lang"]])}<br><span class="muted">{esc(a["claim_en"][:95])}…</span></th>{cell(a)}{cell(b)}'
                       f'<td>{esc(same)}</td><td>{esc(a.get("veritas"))}</td></tr>')
        extracted = [e for e in (json.loads((TEN.parent / 'multilingual_results_10.json').read_text(encoding='utf-8')))
                     if e['claim_id'] == cid][0]['extracted']['evidence_set']
        body = []
        for i, x in enumerate(extracted, 1):
            tds = []
            for arm, run in (('en', a), ('original', b)):
                e = next((y for y in run['evidence'] if (y.get('statement_before_settle') or y['statement']) == x['statement']), None)
                tds.append('<td class="muted">dropped</td>' if e is None else
                           f'<td>{esc(STATUS.get(e.get("url_status"), e.get("url_status")))}<br>{link_cell(e, arm)}</td>')
            body.append(f'<tr><th>E{i}. {esc(x["statement"])}</th>{"".join(tds)}</tr>')
        reasons = (f'<div class="cmp-reasons"><div><b>Rationale, English search ({esc(LABEL.get(a["label"], a["label"]))}).</b> {esc(a.get("reasoning"))}</div>'
                   f'<div><b>Rationale, original-language search ({esc(LABEL.get(b["label"], b["label"]))}).</b> {esc(b.get("reasoning"))}</div></div>')
        details.append(f'<details class="cmp-claim"><summary>{esc(LANG[a["lang"]])}: {esc(a["claim_en"][:80])}…</summary>'
                       f'<div class="cmp-scroll"><table class="cmp"><tr><th>Extracted evidence</th><th>English search</th>'
                       f'<th>Original-language search</th></tr>{"".join(body)}</table></div>{reasons}</details>')
    notes = json.loads(NOTES.read_text(encoding='utf-8')) if NOTES.exists() else {}
    facts = (f'Across the {agg["claims"]} claims: the verdict differs between the two runs for {agg["verdict_differs"]}; the attached links '
             f'differ for {agg["links_differ"]}, with {agg["only_original"]} links found only through the original-language search and '
             f'{agg["only_english"]} only through the English one. Evidence kept: {agg["kept_en"]} (English search) and {agg["kept_or"]} '
             f'(original-language search), of which {agg["local_en"]} and {agg["local_or"]} link to a page in the claim\'s language, and '
             f'{agg["hl_en"]} and {agg["hl_or"]} carry a highlight.')
    return f"""<section class="cmp-section">
<h2>English search vs search in the article's language</h2>
<p>The same ten claims, run twice. The two runs differ only in the language of the web search used when the article's own links do
not support a statement: the English statement, or the statement in the article's language. Everything else is the same: the
extraction, the article's links (ranked against the quoted passage), the check of every page, the merge and verdict prompts with the
English claim. These claims have no gold evidence, so there is no EV2R score; the VeriTaS verdict is given for reference.</p>
<div class="cmp-scroll"><table class="cmp"><tr><th>Claim</th><th>English search</th><th>Original-language search</th><th>Links</th><th>VeriTaS</th></tr>{''.join(summary)}</table></div>
<p><b>Counts.</b> {esc(facts)}</p>
{''.join(f'<p><b>{esc(k)}.</b> {esc(v)}</p>' for k, v in notes.items())}
{''.join(details)}
</section>"""


html = html.replace('<div class="grid" id="grid"></div>', '<div class="grid" id="grid"></div>\n' + compare_section(), 1)
html = html.replace('</style>', '.tag.lang{background:var(--info-soft);color:var(--info)}\n.tag.external_search{background:var(--warn-soft);color:var(--warn)}\n'
                    '.tag.extractor{background:var(--ok-soft);color:var(--ok)}\n'
                    '.cmp-section{max-width:1100px;margin:40px auto 24px;padding:0 16px;color:var(--ink2);line-height:1.6}\n'
                    '.cmp-section h2{color:var(--ink);font-size:1.3rem}.cmp-scroll{overflow-x:auto}\n'
                    'table.cmp{border-collapse:collapse;width:100%;min-width:760px;margin:12px 0;font-size:.9rem;background:var(--card)}\n'
                    'table.cmp th,table.cmp td{border:1px solid var(--line);padding:8px 10px;vertical-align:top;text-align:left}\n'
                    'table.cmp th{color:var(--ink);font-weight:600}.cmp-section .muted{color:var(--ink3);font-weight:400}\n'
                    'details.cmp-claim{margin:10px 0}details.cmp-claim summary{cursor:pointer;color:var(--ink);font-weight:600}\n'
                    '.cmp-reasons{display:grid;gap:10px;margin:8px 0 16px}\n</style>', 1)

for marker in ('fLang', 'Multilingual Claims', 'evidenceHTML(e){\n  const LN', 'cmp-section', 'Verdict:</b>'):
    assert marker in html, f'template patch failed: {marker}'
OUT.mkdir(exist_ok=True)
used = set(re.findall(r'snapshots/[0-9a-f]+\.html', html))
for f in (OUT / 'snapshots').glob('*.html'):          # drop marked copies no version on the page links to any more
    if f'snapshots/{f.name}' not in used:
        f.unlink()
(OUT / 'index.html').write_text(html, encoding='utf-8')
print(f'wrote multilingual/index.html  claims={len(rows)}  evidence={n_ev}/{n_ex}  snapshots={len(used)}  langs={dict(lang_count)}')
