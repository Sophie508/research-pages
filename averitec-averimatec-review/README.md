# AVeriTeC + AVerImaTeC review

Page: https://sophie508.github.io/research-pages/averitec-averimatec-review/

The full splits of both datasets through the pipeline with the link stage on (dataset claim
plus fact-check article as input; decontextualization; evidence extraction; a source link per
statement; verdict; official EV2R with Gemma 4 26B). Nothing on the page is written by hand.

```
data/summary.json          per-split numbers for the cards and panels
data/<dataset>_<split>.json  every claim of that split with its evidence, links, judge output, gold QA
media/                     claim-image thumbnails (AVerImaTeC), longest side 480 px
```

## Updating

On the server (otakotak), from `/scratch/users/suliu/mcfc-settle`:

```
/scratch/users/suliu/mcfc-venv/bin/python full_ev2r_run/collect_pages.py
```

writes `full_ev2r_run/pages/<dataset>_<split>.json` from the latest scored result of every
claim (text splits: the runner's report files plus the merged evidence file and the shard log
each report names; image-text splits: `runs/averimatec_<split>/`). Then on the Mac:

```
rsync -az otakotak:/scratch/users/suliu/mcfc-settle/full_ev2r_run/pages/ <dir>/
python3 build_review.py --src <dir>
```

`refresh.sh` does all of this and commits and pushes when the data changed; it was used to
republish the page while the AVeriTeC train link queue was still running.

## What the page shows

- **Results by split**: EV2R evidence recall and precision over the scored claims, the same
  averaged over every claim in the split (unscored = 0), the number scored, and verdict accuracy.
- **Per split**: recall and precision buckets, the verdict confusion against the gold label,
  the link stage's outcome per statement (for AVeriTeC, per statement before the merge to two,
  read back from the shard logs because the merged evidence keeps only one URL), the verifier's
  label, decontextualization status, evidence per claim, unscored claims by reason, top domains.
- **Per claim**: the decontextualized claim and the dataset's original, claim images, the
  fact-check article, each evidence statement with its source link, link-stage pills, the EV2R
  judge's match to the gold items, and an **article passage** link: a text-fragment URL that
  opens the fact-check article with the passage the statement was extracted from marked
  (Chrome, Edge, Safari 16.1+, Firefox 131+). The settle step, which marks passages on the
  source page itself, is off in this run, so highlights are on the article only.
