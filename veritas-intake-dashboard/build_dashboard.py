#!/usr/bin/env python3
"""Build data/site.json for the intake dashboard from the clean items and the domain table.

    python3 make_domain_table.py      # when the items change: refresh data/domains.csv
    python3 build_dashboard.py        # writes data/site.json; index.html only displays it

Inputs: data/items.jsonl (a copy of intake_clean.jsonl, one item per claim) and data/domains.csv.
Nothing on the page is written by hand: every count comes from these two files.
"""
from __future__ import annotations

import argparse, csv, json, shutil, statistics, sys, time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_domain_table import domain_of  # noqa: E402

ITEMS = HERE / "data" / "items.jsonl"
DOMAINS = HERE / "data" / "domains.csv"
OUT = HERE / "data" / "site.json"
IMAGES = "../veritas-intake-review/media_clean/"    # the review page already serves the screened images
# marked text copies the settle step wrote for pages whose passages cannot be linked with a text fragment
SNAPSHOTS_SRC = [Path.home() / "Downloads/mcfc-veritas-track3/analysis_outputs/veritas_intake_settle_20261020/runs" / d / "snapshots"
                 for d in ("full", "img", "redo", "requote")]      # text-only run, image-text run, Wayback-article rerun, second-attempt highlights
SNAPSHOTS = HERE / "snapshots"


def final_type(row: dict) -> str:
    return row["type_manual"] or (row["type_auto"] if row["type_auto"] != "UNKNOWN" else "") or row["type_wikidata"] or "UNKNOWN"


def timing(e: dict, claim_date: str, check_date: str) -> str:
    """Where the source sits relative to the claim (t_c) and the fact-check (t_f)."""
    if not e.get("source_url"):
        return "no_url"
    d = e.get("source_date")
    if not d:
        # strict recovery accepted these through a Wayback capture before the claim date
        return "before_claim_archived" if e["source_origin"] == "external_search_date_verified" else "not_dated"
    if d <= claim_date:
        return "before_claim"
    return "during_check" if check_date and d <= check_date else "after_check"


def counts(values) -> list[list]:
    return [[k, v] for k, v in Counter(values).most_common()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=Path, default=ITEMS)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--snapshots-src", type=Path, action="append", default=None, help="snapshot directories; repeatable")
    args = ap.parse_args()
    items = [json.loads(l) for l in args.items.read_text(encoding="utf-8").splitlines() if l.strip()]
    snapshot_dirs = args.snapshots_src or SNAPSHOTS_SRC
    SNAPSHOTS.mkdir(exist_ok=True)
    missing_snapshots = 0
    unknown_domains = set()
    with DOMAINS.open(encoding="utf-8") as f:
        dom = {r["domain"]: r for r in csv.DictReader(f)}

    for it in items:
        it["images"] = [IMAGES + Path(p).name for p in it["images"]]
        for e in it["silver_evidence"]:
            if e["source_url"]:
                d = domain_of(e["source_url"])
                row = dom.get(d)
                if row is None:          # a domain the table has not seen yet: run make_domain_table.py to name it
                    unknown_domains.add(d)
                    row = {"domain": d, "name": "", "name_manual": "", "type_manual": "", "type_auto": "UNKNOWN", "type_wikidata": ""}
                e["domain"] = row["domain"]
                e["outlet"] = row["name_manual"] or row["name"] or row["domain"]
                e["outlet_named"] = bool(row["name_manual"] or row["name"])
                e["source_type"] = final_type(row)
            else:
                e["domain"] = e["outlet"] = None
                e["outlet_named"] = False
                e["source_type"] = "METADATA"
            e["timing"] = timing(e, it["claim_date"], it["fact_check_date"])
            # a snapshot highlight is a file the settle step wrote; serve a copy next to the page
            h = (e.get("settle") or {}).get("highlight_url") or ""
            if h.startswith("snapshots/"):
                src = next((d / Path(h).name for d in snapshot_dirs if (d / Path(h).name).is_file()), None)
                if src is not None:
                    shutil.copy2(src, SNAPSHOTS / src.name)
                else:
                    missing_snapshots += 1
                    e["settle"]["highlight_url"] = None

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
    # the link + settle pass (text-only claims run through the main pipeline's link stage and settle step)
    passed = [it for it in items if it.get("link_settle_pass")]
    if passed:
        pev = [e for it in passed for e in it["silver_evidence"]]
        summary["pass"] = {
            "claims": len(passed), "scope_claims": len(items),
            "by_modality": counts(it["modality"] for it in passed),
            "evidence_before": sum(it["link_settle_pass"]["evidence_before"] for it in passed), "evidence_after": len(pev),
            "claims_no_evidence_left": sum(1 for it in passed if not it["silver_evidence"]),
            "claims_no_article_links": sum(1 for it in passed if not it["link_settle_pass"].get("article_link_pool")),
            "link_origin": counts(e["link"]["origin"] for e in pev if e.get("link")),
            "link_basis": counts(e["link"]["basis"] for e in pev if e.get("link")),
            "link_verdict": counts(e["link"]["verdict"] for e in pev if e.get("link")),
            "settle_status": counts(e["settle"]["status"] for e in pev if e.get("settle")),
            "highlighted": sum(1 for e in pev if (e.get("settle") or {}).get("highlight_url")),
            "verdict_recomputed": sum(1 for it in passed if it["link_settle_pass"].get("verdict_recomputed")),
            "verdict_changed": sum(1 for it in passed if it["link_settle_pass"].get("verdict_recomputed")
                                   and it["pipeline_verdict"] != it["link_settle_pass"].get("verdict_before")),
            "snapshot_highlights": sum(1 for e in pev if ((e.get("settle") or {}).get("highlight_url") or "").startswith("snapshots/")),
        }
    if unknown_domains:
        print(f"warning: {len(unknown_domains)} domains not in domains.csv (run make_domain_table.py): {sorted(unknown_domains)[:5]}")
    if passed:
        if missing_snapshots:
            print(f"warning: {missing_snapshots} snapshot files not found under {[str(d) for d in snapshot_dirs]}")
    args.out.write_text(json.dumps({"built": time.strftime("%Y-%m-%d %H:%M"), "summary": summary, "items": items},
                              ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.out.name}: {len(items)} claims, {len(ev)} evidence, {summary['sources']['domains']} domains"
          + (f", {summary['pass']['claims']} claims through the link + settle pass" if passed else ""))


if __name__ == "__main__":
    main()
