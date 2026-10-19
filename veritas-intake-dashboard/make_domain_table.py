#!/usr/bin/env python3
"""Domain table for the intake dashboard: registered domain -> outlet name and source type.

    python3 make_domain_table.py [--items PATH] [--no-wikidata]

Every evidence URL is reduced to its registered domain (tldextract, Public Suffix List; Wayback
links are unwrapped first). For each domain the table holds:

  name / name_source / wikidata   outlet name from Wikidata (an item whose official website, P856,
                                  is that domain), else blank
  type_auto                       most common source type of its URLs (taxonomy.py, conservative:
                                  UNKNOWN unless a rule applies)
  type_wikidata                   NEWS / OFFICIAL / ACADEMIC / SOCIAL when the Wikidata item is an
                                  instance of one of the classes in WIKIDATA_CLASSES (blank if none or
                                  more than one matches); used only where type_auto is UNKNOWN
  name_manual / type_manual       filled by hand; never overwritten on a rerun

Rerunning keeps the manual columns and the Wikidata answers already fetched.
"""
from __future__ import annotations

import argparse, csv, json, subprocess, sys
from urllib.parse import urlsplit
from collections import Counter, defaultdict
from pathlib import Path

import tldextract

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import taxonomy  # noqa: E402

ITEMS = HERE / "data" / "items.jsonl"      # copy of intake_clean.jsonl
TABLE = HERE / "data" / "domains.csv"
FIELDS = ["domain", "n_urls", "name", "name_source", "wikidata", "type_auto", "type_wikidata", "name_manual", "type_manual"]
WIKIDATA_CLASSES = {   # instance of (P31) one of these, or of a subclass of one
    "NEWS": ["Q1193236", "Q11032", "Q1153191", "Q15265344", "Q1110794", "Q192283"],  # news media, newspaper, news website, broadcaster, daily newspaper, news agency
    "OFFICIAL": ["Q327333", "Q7188", "Q2659904"],                                     # government agency, government, government organization
    "ACADEMIC": ["Q5633421", "Q3918", "Q31855", "Q737498"],                           # scientific journal, university, research institute, academic journal
    "SOCIAL": ["Q3220391", "Q2715623"],                                               # social networking service, social media
}
EXTRACT = tldextract.TLDExtract(suffix_list_urls=())       # bundled suffix list, no download


def domain_of(url: str) -> str:
    original, _ = taxonomy.unwrap_wayback(url)
    parts = EXTRACT(original)
    # gov.uk and the like are public suffixes themselves, so www.gov.uk splits as domain "www"
    if parts.domain == "www" or not parts.top_domain_under_public_suffix:
        return (parts.suffix if parts.domain == "www" else parts.fqdn or urlsplit(original).hostname or original).lower()
    return parts.top_domain_under_public_suffix.lower()


def wikidata_names(domains: list[str]) -> dict[str, tuple[str, str]]:
    """{domain: (label, Q-id)} for items whose official website is the bare domain or www.domain.
    Uses curl (POST, the query is long) because this machine's Python cannot verify TLS certificates."""
    out: dict[str, tuple[str, str]] = {}
    for i in range(0, len(domains), 60):
        chunk = domains[i:i + 60]
        sites = " ".join(f"<{s}://{w}{d}{slash}>" for d in chunk for s in ("https", "http")
                         for w in ("", "www.") for slash in ("", "/"))
        query = ("SELECT ?item ?itemLabel ?site WHERE { VALUES ?site { " + sites + " } ?item wdt:P856 ?site . "
                 "SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\". } }")
        res = subprocess.run(["curl", "-s", "-m", "90", "https://query.wikidata.org/sparql",
                              "--data-urlencode", f"query={query}", "-H", "Accept: application/sparql-results+json",
                              "-A", "research-pages-domain-table/0.1"], capture_output=True, text=True)
        try:
            rows = json.loads(res.stdout)["results"]["bindings"]
        except (ValueError, KeyError):
            print(f"  wikidata chunk {i // 60} failed, left blank", file=sys.stderr)
            continue
        found = defaultdict(set)
        for r in rows:
            site = r["site"]["value"].split("://", 1)[1].removeprefix("www.").rstrip("/")
            qid = r["item"]["value"].rsplit("/", 1)[1]
            found[site].add((int(qid[1:]), qid, r["itemLabel"]["value"]))
        for d, items in found.items():
            _, qid, label = min(items)         # several items can share a website; the oldest is the outlet itself
            if label != qid:                   # an unlabeled item comes back as its bare Q-id
                out[d] = (label, qid)
    return out


def sparql(query: str) -> list[dict]:
    res = subprocess.run(["curl", "-s", "-m", "120", "https://query.wikidata.org/sparql", "--data-urlencode",
                          f"query={query}", "-H", "Accept: application/sparql-results+json",
                          "-A", "research-pages-domain-table/0.1"], capture_output=True, text=True)
    return json.loads(res.stdout)["results"]["bindings"]


def wikidata_types(qids: list[str]) -> dict[str, str]:
    """{Q-id: type} for items that fall under exactly one type's classes."""
    hits: dict[str, set] = defaultdict(set)
    items = " ".join(f"wd:{q}" for q in qids)
    for t, classes in WIKIDATA_CLASSES.items():
        cls = " ".join(f"wd:{c}" for c in classes)
        try:
            rows = sparql(f"SELECT DISTINCT ?item WHERE {{ VALUES ?item {{ {items} }} VALUES ?c {{ {cls} }} "
                          f"?item wdt:P31/wdt:P279* ?c . }}")
        except (ValueError, KeyError):
            print(f"  wikidata types for {t} failed, left blank", file=sys.stderr)
            continue
        for r in rows:
            hits[r["item"]["value"].rsplit("/", 1)[1]].add(t)
    return {q: next(iter(ts)) for q, ts in hits.items() if len(ts) == 1}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", type=Path, default=ITEMS)
    ap.add_argument("--no-wikidata", action="store_true")
    args = ap.parse_args()

    urls_by_domain: dict[str, list[str]] = defaultdict(list)
    for line in args.items.read_text(encoding="utf-8").splitlines():
        for e in json.loads(line)["silver_evidence"]:
            if e.get("source_url"):
                urls_by_domain[domain_of(e["source_url"])].append(e["source_url"])

    old = {}
    if TABLE.exists():
        with TABLE.open(encoding="utf-8") as f:
            old = {r["domain"]: r for r in csv.DictReader(f)}
    todo = [d for d in urls_by_domain if not old.get(d, {}).get("name_source")]
    names = {} if args.no_wikidata else wikidata_names(sorted(todo))

    qids = sorted({names.get(d, ("", old.get(d, {}).get("wikidata", "")))[1] for d in urls_by_domain} - {""})
    wd_type = {} if args.no_wikidata else wikidata_types(qids)

    rows = []
    for d, urls in sorted(urls_by_domain.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        prev = old.get(d, {})
        types = Counter(taxonomy.classify_source(u)["source_type"] for u in urls)
        row = {"domain": d, "n_urls": len(urls), "type_auto": types.most_common(1)[0][0],
               "name": prev.get("name", ""), "name_source": prev.get("name_source", ""),
               "wikidata": prev.get("wikidata", ""),
               "name_manual": prev.get("name_manual", ""), "type_manual": prev.get("type_manual", "")}
        if d in names:
            row["name"], row["wikidata"] = names[d]
            row["name_source"] = "wikidata"
        row["type_wikidata"] = wd_type.get(row["wikidata"], prev.get("type_wikidata", "") if args.no_wikidata else "")
        rows.append(row)
    TABLE.parent.mkdir(exist_ok=True)
    with TABLE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)
    named = sum(1 for r in rows if r["name"] or r["name_manual"])
    print(f"{len(rows)} domains, {sum(r['n_urls'] for r in rows)} URLs; named {named} "
          f"(covering {sum(r['n_urls'] for r in rows if r['name'] or r['name_manual'])} URLs)")


if __name__ == "__main__":
    main()
