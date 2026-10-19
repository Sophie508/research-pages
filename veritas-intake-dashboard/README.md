# VeriTaS intake dashboard

Page: https://sophie508.github.io/research-pages/veritas-intake-dashboard/

The page is generated from data; nothing on it is written by hand.

```
data/items.jsonl   one item per claim: normalized claim + silver evidence (copy of intake_clean.jsonl)
data/domains.csv   registered domain -> outlet name and source type
data/site.json     everything the page shows, built from the two files above
```

## Updating

1. Copy the new `intake_clean.jsonl` from the pipeline to `data/items.jsonl`.
2. `python3 make_domain_table.py` adds any new domains. It fetches names from Wikidata and keeps
   everything already in the table, including the manual columns.
3. Fill `name_manual` / `type_manual` in `data/domains.csv` for domains you want named or typed by
   hand. Manual values always win.
4. `python3 build_dashboard.py` writes `data/site.json`. Commit and push.

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
