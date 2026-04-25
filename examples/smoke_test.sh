#!/usr/bin/env bash
# End-to-end smoke test:
#   1. Copy the sample project into a tmp dir.
#   2. Initialize it as a git repo with one commit on `main`.
#   3. Run the full Flamboyance pipeline.
#   4. Show the resulting commit log on `main`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SAMPLE="$REPO_ROOT/examples/sample_project"
SCRATCH="$(mktemp -d -t flamboyance-XXXXXX)"
trap 'rm -rf "$SCRATCH"' EXIT

echo ">>> Staging sample project into $SCRATCH"
cp -R "$SAMPLE/." "$SCRATCH/"
cd "$SCRATCH"
git init -q -b main
git add .
git -c user.email=test@flamboyance -c user.name=Flamboyance \
    commit -q -m "initial sample project"

echo ">>> Running flamboyance discover"
PYTHONPATH="$REPO_ROOT" python3 -m orchestrator --root "$SCRATCH" discover -n 3

echo ">>> Running flamboyance run"
PYTHONPATH="$REPO_ROOT" python3 -m orchestrator -v --root "$SCRATCH" run -n 3 \
    --output "$SCRATCH/report.json"

echo ">>> Final git log on main:"
git -C "$SCRATCH" log --oneline --graph --all | head -40

echo
echo ">>> Report summary:"
python3 -c "
import json, sys
r = json.load(open('$SCRATCH/report.json'))
print(f\"  tasks planned : {len(r['tasks'])}\")
print(f\"  workers ok    : {sum(1 for w in r['worker_results'] if w['status'] == 'success')}\")
print(f\"  workers bad   : {sum(1 for w in r['worker_results'] if w['status'] != 'success')}\")
print(f\"  merges ok     : {sum(1 for m in r['merge_results'] if m['status'] in ('merged','auto-resolved'))}\")
print(f\"  merges conflict: {sum(1 for m in r['merge_results'] if m['status'] == 'conflict')}\")
"
