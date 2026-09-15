#!/usr/bin/env python3
"""Build the Original Pipeline review page from the AVeriTeC multi-record run.

This is the other half of the benchmark story. The VeriTaS Intake page shows
their claims and their article links going through our pipeline; this one uses
AVeriTeC's fact-checking articles but OUR claims, normalized and
decontextualized by us rather than taken from the dataset's gold field.

Source: analysis_outputs/url_recovery_multi21_20260810 (2026-08-10), 21 claims
drawn from 17 AVeriTeC train articles. That run predates the strict temporal
policy, so its raw output contains evidence the policy would now reject. The
policy is applied here at build time rather than shipping a second standard:
an item survives only with an article-embedded URL or an externally recovered
one whose publication date was verified against the claim date.

Reuses the intake page as its template so the two pages stay visually identical.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "veritas-intake-review" / "index.html"
OUT_DIR = HERE / "original-pipeline-review"
SRC = Path("/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs"
           "/url_recovery_multi21_20260810/multi21_extract_with_recovered_urls.json")


def provenance(ev: dict) -> str:
    """How this evidence item got its URL, kept distinct because the guarantees
    differ: an article-embedded link is the fact-checker's, a recovered one is
    ours, and a recovered one without a page date was never date-verified."""
    recovery = ev.get("url_recovery") or {}
    status = recovery.get("status", "")
    if status == "recovered":
        return "external-verified"
    if status == "recovered_no_page_date":
        return "external-nodate"
    if status in ("all_candidates_rejected", "no_search_results"):
        return "ungrounded"
    if ev.get("source_url"):
        return "article"
    return "ungrounded"


# What the strict temporal policy refuses to keep: an item with no usable
# source at all, and an externally recovered one whose date we could not
# verify. Both would have been dropped had this run happened after the policy.
STRICT_DROP = {"ungrounded", "external-nodate"}


def build_rows() -> tuple[list[dict], dict]:
    payload = json.loads(SRC.read_text(encoding="utf-8"))
    rows, dropped = [], Counter()
    for r in payload["records"]:
        all_evidence = (r.get("extracted") or {}).get("evidence_set") or []
        evidence = []
        for e in all_evidence:
            p = provenance(e)
            if p in STRICT_DROP:
                dropped[p] += 1
            else:
                evidence.append(e)
        if not evidence:
            dropped["claims_left_empty"] += 1
            continue
        rows.append({
            "id": r["id"],
            "claim": r.get("claim") or "",
            "date": "",
            "mod": "text-only",
            "pred": (r.get("prediction") or {}).get("label") or "",
            "gold": r.get("gold_label") or "",
            "art": r.get("url") or "",
            "img": "",
            "orig": "",
            "ev": [{"s": e.get("statement") or "",
                    "u": e.get("source_url") or "",
                    "d": "",
                    "p": provenance(e)} for e in evidence],
        })
    rows.sort(key=lambda x: x["id"])
    return rows, dropped


def main() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    rows, dropped = build_rows()

    html = re.sub(r"(const DATA\s*=\s*)\[.*?\](;\s*\n)",
                  lambda m: m.group(1) + json.dumps(rows, ensure_ascii=False) + m.group(2),
                  html, flags=re.S)

    # The gold field here is an AVeriTeC verdict label, not a VeriTaS band, so
    # the intake page's string-prefix comparison would never match.
    html = html.replace(
        'if ((g.startsWith("true") && p==="Supported") || '
        '(g.startsWith("false") && p==="Refuted")) return "ok";',
        'if (g && g===p) return "ok";')
    html = html.replace('${d.gold?` · gold: ${esc(d.gold)}`:""}',
                        '${d.gold?` · gold: ${esc(d.gold)}`:""}')

    html = html.replace("<title>MCFC Bench — Claim Browser</title>",
                        "<title>MCFC Bench — Original Pipeline Review</title>")
    html = html.replace("<h1>Claim Overview</h1>",
                        "<h1>Original Pipeline</h1>")
    html = html.replace('<a href="#">Claim Browser</a>',
                        '<a href="../veritas-intake-review/">VeriTaS Intake</a>'
                        '<a href="#">Original Pipeline</a>')

    # Sorting by date is meaningless without claim dates in this artifact.
    html = html.replace(
        'list.sort((a,b)=>ord==="desc"?b.date.localeCompare(a.date):a.date.localeCompare(b.date));',
        'list.sort((a,b)=>ord==="desc"?b.id-a.id:a.id-b.id);')
    html = html.replace('<option value="desc">Newest first</option>'
                        '<option value="asc">Oldest first</option>',
                        '<option value="asc">Record id ↑</option>'
                        '<option value="desc">Record id ↓</option>')
    kept_claims = len(rows)
    kept_ev = sum(len(r["ev"]) for r in rows)
    note = ('<div class="controls" style="border-top:none;padding-top:0">'
            '<span class="count">AVeriTeC train. Claims are ours (normalized and '
            "decontextualized), articles are the dataset's. The 2026-08-10 run "
            'predates the strict temporal policy, so the policy is applied here: '
            f'{dropped["ungrounded"]} evidence items with no usable source and '
            f'{dropped["external-nodate"]} whose publication date could not be '
            f'verified were dropped, leaving {kept_ev} of 51 across '
            f'{kept_claims} claims.</span></div>')
    html = html.replace('<div class="grid" id="grid"></div>',
                        note + '\n<div class="grid" id="grid"></div>')

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")

    from collections import Counter
    prov = Counter(e["p"] for r in rows for e in r["ev"])
    agree = sum(1 for r in rows if r["gold"] and r["gold"] == r["pred"])
    print(f"wrote {OUT_DIR.name}/index.html")
    print(f"  {len(rows)} claims, {sum(len(r['ev']) for r in rows)} evidence")
    print(f"  provenance: {dict(prov)}")
    print(f"  verdict agrees with gold: {agree}/{sum(1 for r in rows if r['gold'])}")


if __name__ == "__main__":
    main()
