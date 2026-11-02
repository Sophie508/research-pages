#!/usr/bin/env python3
"""Build the data files of the AVeriTeC + AVerImaTeC review page.

    python3 build_review.py --src DIR      # DIR holds the four files collect_pages.py wrote on the server
                                           # (averitec_dev.json, averitec_train.json, averimatec_val.json,
                                           # averimatec_train.json); writes data/<key>.json, data/summary.json
                                           # and claim-image thumbnails under media/

Nothing on the page is written by hand: every number comes from these files.
"""
from __future__ import annotations

import argparse, json, re, statistics, time
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
MEDIA = HERE / "media"
IMAGES_SRC = Path.home() / "Downloads/mcfc-veritas-track3/datasets/averimatec/images"
KEYS = ["averitec_dev", "averitec_train", "averimatec_val", "averimatec_train"]
THUMB = 480
ARCHIVE = re.compile(r"^https?://web\.archive\.org/web/\d+(?:[a-z_]+)?/(https?://.*)$")


def domain_of(url: str) -> str:
    m = ARCHIVE.match(url or "")
    host = urlparse(m.group(1) if m else (url or "")).hostname or ""
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


def counts(values) -> list[list]:
    return [[k, v] for k, v in Counter(values).most_common()]


def bucket(r: float | None) -> str:
    if r is None:
        return "unscored"
    return "1.0" if r >= 1 else "0.5–0.99" if r >= 0.5 else "0.01–0.49" if r > 0 else "0"


def status_bucket(c: dict) -> str:
    s = str(c.get("status") or "")
    if c.get("ev2r"):
        return "scored"
    if s.startswith("fetch_error"):
        return "article not fetched"
    if s.startswith("pipeline_error"):
        return "pipeline error (model response)"
    if s.startswith("prediction_error"):
        return "verdict failed"
    if s == "ok" and not c["evidence"]:
        return "no evidence extracted"
    if s.startswith("page_quality") or "quality" in s:
        return "article failed the page check"
    return "other: " + s[:40] if s != "ok" else "judge call failed"


def thumbnail(name: str) -> str | None:
    """A JPEG copy of a claim image, longest side THUMB px, under media/. '#' in the dataset's names
    cannot appear in a URL, so it becomes '_'."""
    src = IMAGES_SRC / name
    if not src.is_file():
        return None
    out = MEDIA / (re.sub(r"[#\s]", "_", Path(name).stem) + ".jpg")
    if not out.is_file():
        from PIL import Image
        im = Image.open(src)
        im = im.convert("RGB")
        im.thumbnail((THUMB, THUMB))
        im.save(out, "JPEG", quality=72, optimize=True)
    return f"media/{out.name}"


def summarize(payload: dict) -> dict:
    claims = payload["claims"]
    text = payload["dataset"] == "averitec"
    scored = [c for c in claims if c["ev2r"]]
    n_split = payload["records_in_split"]
    ev = [e for c in claims for e in c["evidence"]]
    judged = [c for c in claims if c["correct"] is not None] if text else [c for c in claims if c["verdict"] and c["gold_label"]]
    correct = sum(1 for c in judged if (c["correct"] if text else c["verdict"] == c["gold_label"]))
    if text:
        lines = [l for c in claims for l in c["link_lines"]]
        outcomes = counts(l["outcome"] for l in lines)
        verifier = counts(l["verdict"] for l in lines)
        n_extract = sum(c["n_extract"] or 0 for c in claims)
        n_link = sum(c["n_link"] or 0 for c in claims)
    else:
        outcomes = counts(e["basis"] for e in ev)
        verifier = counts(e["verdict"] for e in ev if e["verdict"])
        n_extract = sum(c["n_extract"] or 0 for c in claims)
        n_link = sum(c["n_link"] or 0 for c in claims)
        if n_extract > n_link:   # statements the link stage dropped are not in linked.json; count them as a row
            outcomes.append(["dropped_no_candidate", n_extract - n_link])
    urls = [e["source_url"] for e in ev if e["source_url"]]
    # while a split is still running, the "all claims" average divides by the claims run so far
    n_all = n_split if len(claims) >= n_split else len(claims)
    per_claim = [len(c["evidence"]) for c in claims if c["evidence"]]
    return {
        "dataset": payload["dataset"], "split": payload["split"], "built": payload["built"],
        "records_in_split": n_split, "claims": len(claims), "pending": n_split - len(claims), "scored": len(scored),
        "evidence": {
            "recall": round(statistics.mean(c["ev2r"]["recall"] for c in scored), 4) if scored else None,
            "precision": round(statistics.mean(c["ev2r"]["precision"] for c in scored), 4) if scored else None,
            "f1": round(statistics.mean(c["ev2r"]["f1"] for c in scored), 4) if scored else None,
            "recall_all": round(sum(c["ev2r"]["recall"] for c in scored) / n_all, 4) if scored else None,
            "precision_all": round(sum(c["ev2r"]["precision"] for c in scored) / n_all, 4) if scored else None,
            "n_all": n_all,
            "recall_hist": counts(bucket(c["ev2r"]["recall"] if c["ev2r"] else None) for c in claims),
            "precision_hist": counts(bucket(c["ev2r"]["precision"] if c["ev2r"] else None) for c in claims),
        },
        "justification": {
            "recall": round(statistics.mean(c["ev2r"]["just_recall"] for c in scored if c["ev2r"]["just_recall"] is not None), 4) if scored else None,
            "precision": round(statistics.mean(c["ev2r"]["just_precision"] for c in scored if c["ev2r"]["just_precision"] is not None), 4) if scored else None,
        },
        "verdict": {"judged": len(judged), "correct": correct, "pred": counts(c["verdict"] or "none" for c in claims),
                    "gold": counts(c["gold_label"] for c in claims),
                    "confusion": counts(f"{c['gold_label']}→{c['verdict'] or 'none'}" for c in claims)},
        "decon": counts(c["decon_status"] or "unknown" for c in claims),
        "status": counts(status_bucket(c) for c in claims),
        "links": {"n_extract": n_extract, "n_link": n_link, "n_final": len(ev), "outcomes": outcomes, "verifier": verifier,
                  "n_urls": len(urls), "distinct_urls": len(set(urls)), "domains": len({domain_of(u) for u in urls}),
                  "top_domains": counts(domain_of(u) for u in urls)[:15],
                  "search_unavailable": sum(1 for e in ev if (e.get("basis") == "search_unavailable") or any(m["outcome"] == "kept_search_unavailable" for m in e.get("members", []))),
                  "images_exempt": sum(1 for e in ev if e["source_type"] == "image")},
        "per_claim": {"mean": round(statistics.mean(per_claim), 2) if per_claim else None, "median": statistics.median(per_claim) if per_claim else None,
                      "hist": sorted(counts(per_claim), key=lambda r: r[0])},
        "claims_with_images": sum(1 for c in claims if c.get("images")),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, required=True, help="directory with the four collect_pages.py files")
    a = ap.parse_args()
    DATA.mkdir(exist_ok=True)
    MEDIA.mkdir(exist_ok=True)
    summary = {"built": time.strftime("%Y-%m-%d %H:%M"), "splits": {}}
    missing_images = 0
    for key in KEYS:
        src = a.src / f"{key}.json"
        if not src.is_file():
            print(f"skip {key}: {src} not found")
            continue
        payload = json.loads(src.read_text(encoding="utf-8"))
        for c in payload["claims"]:
            c["article_domain"] = domain_of(c.get("article") or "")
            for e in c["evidence"]:
                e["domain"] = domain_of(e["source_url"]) if e["source_url"] else ""
            if c.get("images"):
                thumbs = [thumbnail(n) for n in c["images"]]
                missing_images += thumbs.count(None)
                c["images"] = [t for t in thumbs if t]
        summary["splits"][key] = summarize(payload)
        (DATA / f"{key}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        s = summary["splits"][key]
        print(f"{key}: {s['claims']} claims ({s['scored']} scored, {s['pending']} pending) of {s['records_in_split']}, "
              f"{s['links']['n_final']} evidence, R {s['evidence']['recall']} P {s['evidence']['precision']}, "
              f"verdict {s['verdict']['correct']}/{s['verdict']['judged']}")
    (DATA / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    if missing_images:
        print(f"warning: {missing_images} claim images not found under {IMAGES_SRC}")


if __name__ == "__main__":
    main()
