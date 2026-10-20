# VeriTaS intake dashboard

Page: https://sophie508.github.io/research-pages/veritas-intake-dashboard/

The page is generated from data; nothing on it is written by hand.

```
data/items.jsonl   one item per claim: normalized claim + silver evidence (copy of intake_clean.jsonl)
data/domains.csv   registered domain -> outlet name and source type
data/site.json     everything the page shows, built from the two files above
```

## Updating

One command on the pipeline side does it all: `build_clean.py --publish` (in the pipeline repo's
`analysis_outputs/veritas_intake_clean_20261014/`). It builds the clean items from the pipeline
outputs, writes them to `data/items.jsonl`, then runs the two scripts here:

- `make_domain_table.py` adds any new domains. It fetches names from Wikidata and keeps everything
  already in the table, including the manual columns.
- `build_dashboard.py` writes `data/site.json`.

Then review the diff and push. To name or type a domain by hand, fill `name_manual` /
`type_manual` in `data/domains.csv` and rerun `build_dashboard.py`; manual values always win.

## The link + settle pass

For the text-only claims the evidence comes from the main pipeline's link stage and settle step
(2026-10-20). The page shows, per evidence item, the tier its link came from (the extractor's
citation, a link in the fact-check article, or a search), the verifier's label, what the settle step
did (kept / rewritten / kept with a second page / replaced / unverifiable) and a link that opens the
page with the supporting passage marked. Marked text copies live in `snapshots/`; `build_dashboard.py`
copies the ones the data references from the run's snapshot directory. `?data=<file>` previews another
data file from `data/` before it is published.

## How a source gets its name and type

- **Domain:** the registered domain of the URL (tldextract; Wayback links are unwrapped first), so
  `forums.bbc.co.uk` and `www.bbc.co.uk` count as one.
- **Name:** `name_manual`, else the label of the Wikidata item whose official website (P856) is that
  domain, else the bare domain.
- **Type:** `type_manual`, else the conservative domain/path rules in `taxonomy.py`, else the
  Wikidata item's class (news media, government agency, academic journal, social network; left
  blank when it matches more than one), else Unclassified. `taxonomy.py` is the classifier from the
  earlier article-link revision.

`source_date` is the page date strict URL recovery recorded. "Before the claim (by archive
capture)" means it was verified through a Wayback capture instead. Links taken from the fact-check
article are not dated.
