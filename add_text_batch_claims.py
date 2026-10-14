#!/usr/bin/env python3
"""Add the text-only intake extension (2026-10-14) to the intake review page.

The claims were run through the same chain as the claims already on the page (extract, source
types, strict URL recovery, merge, verdict; analysis_outputs/veritas_intake_text100_20261014/
run_chain.py). Same row format as add_rescued_claims.py, which this copies; claims left with no
evidence after the strict URL policy are skipped, as there.

Reads chain_results.json from the pipeline repo, rewrites the DATA array in
veritas-intake-review/index.html in place.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "veritas-intake-review" / "index.html"
BATCH_DIR = Path("/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs/veritas_intake_text100_20261014")
RESCUED = BATCH_DIR / "chain_results.json"
TARGET_TEXT_ONLY = 100      # stop once the page holds this many text-only claims


def provenance(ev: dict) -> str:
    status = (ev.get("url_recovery") or {}).get("status", "")
    if status.endswith("_exempt"):
        return "metadata"
    if status == "recovered":
        return "external-verified"
    return "article"


def page_date(ev: dict) -> str:
    """The accepted candidate's own page date, when the recovery recorded one.
    Blank means it was verified by its Wayback existence bound instead."""
    recovery = ev.get("url_recovery") or {}
    target = recovery.get("recovered_url") or ""
    for cand in recovery.get("candidates_tried") or []:
        if cand.get("url") == target and "rejected" not in cand:
            return cand.get("page_date") or ""
    return ""


def main() -> None:
    rescued = json.loads(RESCUED.read_text(encoding="utf-8"))
    html = PAGE.read_text(encoding="utf-8")
    match = re.search(r"(const DATA\s*=\s*)(\[.*?\])(;\s*\n)", html, re.S)
    if not match:
        raise SystemExit("DATA array not found in the page")
    data = json.loads(match.group(2))
    existing = {d["id"] for d in data}
    # take claims in batch order (the 40 left over from intake_batch_200 first, then the seeded draw),
    # not in the order the parallel chain happened to finish them
    order = {b["claim_id"]: i for i, b in enumerate(json.loads((BATCH_DIR / "intake_batch.json").read_text())["records"])}
    rescued.sort(key=lambda r: order[r["claim_id"]])
    n_text = sum(1 for d in data if d["mod"] == "text-only")

    added = []
    for r in rescued:
        if n_text >= TARGET_TEXT_ONLY:
            break
        cid = r["claim_id"]
        if cid in existing:
            print(f"  {cid} already on the page, skipping")
            continue
        evidence = (r.get("extracted") or {}).get("evidence_set") or []
        if not evidence:
            print(f"  {cid} still has no evidence, skipping")
            continue
        entry = {
            "id": cid,
            "claim": r["claim"],
            "date": r.get("claim_date") or "",
            "mod": r.get("modality") or "text-only",
            "pred": r.get("pred_label") or "",
            "gold": r.get("veracity_label") or "",
            "art": r.get("url") or "",
            "img": "",
            "orig": r["veritas_claim"] if r.get("veritas_claim") and r["veritas_claim"] != r["claim"] else "",
            "ev": [{"s": e.get("statement") or "",
                    "u": e.get("source_url") or "",
                    "d": page_date(e),
                    "p": provenance(e)} for e in evidence],
        }
        data.append(entry)
        added.append(entry)
        n_text += 1
        print(f"  + {cid}  {len(entry['ev'])} evidence  verdict {entry['pred']}"
              f"  gold {entry['gold'] or '(none)'}")

    if not added:
        print("nothing to add")
        return

    payload = json.dumps(data, ensure_ascii=False)
    html = html[:match.start(2)] + payload + html[match.end(2):]
    # one note under the existing revision note, saying what was added and how it was drawn
    dates = sorted(e["date"] for e in added if e["date"])
    note = (f'<div class="revision-note" id="text-extension-note">Text-only extension: {len(added)} text-only claims were added '
            f'(claim dates {dates[0]} to {dates[-1]}), bringing the page to {n_text} text-only claims. Like the claims already here, '
            'they are VeriTaS claims tagged English, without media and not rectified. The time window was widened back to '
            '2025-12-01 because too few such claims were left after 2026-01-15; claims after 2026-03-31 have no fact-check '
            'article in VeriTaS yet. They went through the same chain (normalized claim, evidence extraction, strict URL '
            'recovery by date, merge, verdict). The article-link revision above was not applied to them. Claims whose fact-check '
            'article could not be downloaded, or that kept no evidence, are not shown; claims were taken in sampling order until '
            'the page reached 100 text-only claims.</div>')
    html = re.sub(r'<div class="revision-note" id="text-extension-note">.*?</div>\n?', "", html, flags=re.S)
    anchor = re.search(r'<div class="revision-note">.*?</div>\n', html, re.S)
    html = html[:anchor.end()] + note + "\n" + html[anchor.end():]
    PAGE.write_text(html, encoding="utf-8")
    print(f"\npage now holds {len(data)} claims "
          f"({len(data) - len(added)} before, {len(added)} added)")


if __name__ == "__main__":
    main()
