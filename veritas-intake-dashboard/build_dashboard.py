#!/usr/bin/env python3
"""Build data/site.json for the intake dashboard from the clean items and the domain table.

    python3 make_domain_table.py      # when the items change: refresh data/domains.csv
    python3 build_dashboard.py        # writes data/site.json; index.html only displays it

Inputs: data/items.jsonl (a copy of intake_clean.jsonl, one item per claim) and data/domains.csv.
Nothing on the page is written by hand: every count comes from these two files.
"""
from __future__ import annotations

import csv, json, statistics, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_domain_table import domain_of  # noqa: E402

ITEMS = HERE / "data" / "items.jsonl"
DOMAINS = HERE / "data" / "domains.csv"
OUT = HERE / "data" / "site.json"
IMAGES = "../veritas-intake-review/media_clean/"    # the review page already serves the screened images


def final_type(row: dict) -> str:
    return row["type_manual"] or (row["type_auto"] if row["type_auto"] != "UNKNOWN" else "") or row["type_wikidata"] or "UNKNOWN"


def timing(e: dict, claim_date: str, check_date: str) -> str:
    """Where the source sits relative to the claim (t_c) and the fact-check (t_f)."""
    d = e.get("source_date")
    if not d:
        # strict recovery accepted these through a Wayback capture before the claim date
        return "before_claim_archived" if e["source_origin"] == "external_search_date_verified" else "undated"
    if d <= claim_date:
        return "before_claim"
    return "during_check" if check_date and d <= check_date else "after_check"


def counts(values) -> list[list]:
    return [[k, v] for k, v in Counter(values).most_common()]


def main() -> None:
    items = [json.loads(l) for l in ITEMS.read_text(encoding="utf-8").splitlines() if l.strip()]
    with DOMAINS.open(encoding="utf-8") as f:
        dom = {r["domain"]: r for r in csv.DictReader(f)}

    for it in items:
        it["images"] = [IMAGES + Path(p).name for p in it["images"]]
        for e in it["silver_evidence"]:
            if e["source_url"]:
                row = dom[domain_of(e["source_url"])]
                e["domain"] = row["domain"]
                e["outlet"] = row["name_manual"] or row["name"] or row["domain"]
                e["outlet_named"] = bool(row["name_manual"] or row["name"])
                e["source_type"] = final_type(row)
            else:
                e["domain"] = e["outlet"] = None
                e["outlet_named"] = False
                e["source_type"] = "METADATA"
            e["timing"] = timing(e, it["claim_date"], it["fact_check_date"])

    ev = [e for it in items for e in it["silver_evidence"]]
    urls = [e for e in ev if e["source_url"]]
    per_claim = [len(it["silver_evidence"]) for it in items]
    days = [(time.mktime(time.strptime(it["fact_check_date"], "%Y-%m-%d")) -
             time.mktime(time.strptime(it["claim_date"], "%Y-%m-%d"))) / 86400
            for it in items if it["fact_check_date"] and it["claim_date"]]
    pole = {"true": "Supported", "false": "Refuted"}
    labelled = [it for it in items if (it["veritas_veracity_label"] or "").split(" ")[0] in pole]
    agree = sum(1 for it in labelled if it["pipeline_verdict"] == pole[it["veritas_veracity_label"].split(" ")[0]])

    summary = {
        "claims": {"n": len(items), "modality": counts(it["modality"] for it in items),
                   "batch": counts(it["batch"] for it in items),
                   "normalization": counts(it["normalization_status"] for it in items),
                   "date_range": [min(it["claim_date"] for it in items), max(it["claim_date"] for it in items)],
                   "check_days_median": statistics.median(days), "check_days_mean": round(statistics.mean(days), 1)},
        "evidence": {"n": len(ev), "per_claim_mean": round(statistics.mean(per_claim), 1),
                     "per_claim_median": statistics.median(per_claim), "per_claim": counts(per_claim),
                     "origin": counts(e["source_origin"] for e in ev), "timing": counts(e["timing"] for e in ev)},
        "sources": {"n_urls": len(urls), "distinct_urls": len({e["source_url"] for e in urls}),
                    "domains": len({e["domain"] for e in urls}),
                    "named_domains": len({e["domain"] for e in urls if e["outlet_named"]}),
                    "named_urls": sum(1 for e in urls if e["outlet_named"]),
                    "type": counts(e["source_type"] for e in urls),
                    "top_outlets": [[o, n, t] for (o, t), n in Counter((e["outlet"], e["source_type"]) for e in urls).most_common(15)]},
        "verdict": {"pipeline": counts(it["pipeline_verdict"] for it in items),
                    "veritas_labelled": len(labelled), "agree_with_veritas": agree},
    }
    OUT.write_text(json.dumps({"built": time.strftime("%Y-%m-%d %H:%M"), "summary": summary, "items": items},
                              ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT.name}: {len(items)} claims, {len(ev)} evidence, {summary['sources']['domains']} domains")


if __name__ == "__main__":
    main()
