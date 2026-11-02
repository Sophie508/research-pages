#!/bin/bash
# Rebuild the review page from the server's current results and push it if anything changed.
#   bash refresh.sh            # one pass
#   bash refresh.sh --loop     # every 90 min until the AVeriTeC train link queue reports done
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
RAW="${RAW:-/tmp/averitec-review-raw}"
S=/scratch/users/suliu/mcfc-settle
mkdir -p "$RAW"

refresh() {
  ssh -o BatchMode=yes -o ConnectTimeout=30 otakotak "cd $S && /scratch/users/suliu/mcfc-venv/bin/python full_ev2r_run/collect_pages.py" || return 1
  rsync -az otakotak:$S/full_ev2r_run/pages/ "$RAW/" || return 1
  python3 "$HERE/build_review.py" --src "$RAW" || return 1
  cd "$HERE/.." || return 1
  if git status --porcelain averitec-averimatec-review | grep -q .; then
    local n
    n=$(python3 -c "import json;s=json.load(open('$HERE/data/summary.json'))['splits']['averitec_train'];print(f\"{s['claims']} of {s['records_in_split']} claims\")")
    git add averitec-averimatec-review
    git commit -q -m "averitec-averimatec-review: rebuild, AVeriTeC train link pass at $n" && git push -q origin main
    echo "$(date -u +%FT%TZ) pushed: train at $n"
  else
    echo "$(date -u +%FT%TZ) no change"
  fi
}

if [ "${1:-}" = "--loop" ]; then
  while true; do
    refresh
    if ssh -o BatchMode=yes otakotak "grep -q 'QUEUE DONE' $S/full_ev2r_run/logs/trainlink.log && grep -q 'QUEUE DONE' $S/full_ev2r_run/logs/trainrepair.log"; then
      echo "$(date -u +%FT%TZ) both queues done"; refresh; break
    fi
    sleep 5400
  done
else
  refresh
fi
