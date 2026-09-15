#!/usr/bin/env python3
"""Add the three rescued claims to the intake review page.

These three came out of the production run with an empty evidence set, because
the extractor is retried only on exceptions and an empty result is not one. A
plain retry recovers all three, so they were re-run through the same chain as
the other claims (extract, source types, strict URL recovery, merge, verdict)
and belong on the page alongside the rest.

Reads rescued_three.json from the pipeline repo, rewrites the DATA array in
veritas-intake-review/index.html in place.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "veritas-intake-review" / "index.html"
RESCUED = Path("/Users/sophie/Downloads/mcfc-veritas-track3/analysis_outputs"
               "/veritas_intake_200_20260907/rescued_three.json")


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

    added = []
    for r in rescued:
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
            "orig": "",
            "ev": [{"s": e.get("statement") or "",
                    "u": e.get("source_url") or "",
                    "d": page_date(e),
                    "p": provenance(e)} for e in evidence],
        }
        data.append(entry)
        added.append(entry)
        print(f"  + {cid}  {len(entry['ev'])} evidence  verdict {entry['pred']}"
              f"  gold {entry['gold'] or '(none)'}")

    if not added:
        print("nothing to add")
        return

    payload = json.dumps(data, ensure_ascii=False)
    PAGE.write_text(html[:match.start(2)] + payload + html[match.end(2):], encoding="utf-8")
    print(f"\npage now holds {len(data)} claims "
          f"({len(data) - len(added)} before, {len(added)} added)")


if __name__ == "__main__":
    main()
