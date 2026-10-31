#!/bin/sh
# The facts the six approval checks need, for pull request <n> of work item <id>:
# the changed files, the tests changed (M = a test another story wrote), the journal's last lines,
# the Expect: lines, new markers, and the cost. Run from anywhere; it works in the checkout.
#   approval.sh <n> <id>
set -eu
[ $# -eq 2 ] || { echo "usage: approval.sh <pull request> <work item id>" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd)
repo=$(sh "$here/settings.sh" get repository)
cd "$(sh "$here/settings.sh" get checkout)"
git fetch -q
branch=origin/work-item/$2
echo "== files"; gh pr diff "$1" --repo "$repo" --name-only
echo "== tests changed (M = an earlier test)"; git diff --name-status "origin/main...$branch" -- tests
item=$(git ls-tree -r --name-only "$branch" factory/features | grep "/in-progress/$2-.*\.md$" | head -n 1)
echo "== the journal's last lines ($item)"; git show "$branch:$item" | sed -n '/^## Journal/,$p' | tail -n 30 | cut -c1-400
echo "== Expect lines"; git show "$branch:$item" | grep -n '^Expect' | cut -c1-200
echo "== new markers"
git diff "origin/main...$branch" -- src tests | grep -E '^\+' | grep -nE 'noqa|type: ignore|pragma: no|pytest.mark.skip|xfail' || echo "none"
echo "== cost"
git show "$branch:${item%.md}.costs.jsonl" 2>/dev/null | python3 -c "
import json, sys
records = [json.loads(line) for line in sys.stdin if line.strip()]
print(len(records), 'runs, \$', round(sum(float(r.get('cost_usd') or 0) for r in records), 2))" || echo "no cost record"
