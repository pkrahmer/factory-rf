#!/bin/sh
# The facts the six approval checks need, for pull request <n> of work item <id>:
# the changed files, the tests changed (M = a test another story wrote), what the journal says
# about the smoke test, the findings and the leaves, its last entry, the Expect: lines, new
# markers, and the cost from the factory's table on the pull request. Run from anywhere; it
# works in the checkout.
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
journal=$(git show "$branch:$item" | sed -n '/^## Journal/,$p')
echo "== what the journal says about the smoke test, the findings and the leaves ($item)"
printf '%s\n' "$journal" | grep -n -E 'smoke-tester:|Met its|Met `|[*][*]Met|Findings|leave' | tail -n 20 | cut -c1-300
echo "== the journal's last entry"
# Every entry starts with its number at column 0; keep the lines from the last such line on.
last=$(printf '%s\n' "$journal" | grep -n -E '^[0-9]+\. ' | tail -n 1 | cut -d: -f1)
printf '%s\n' "$journal" | tail -n "+${last:-1}" | head -n 12 | cut -c1-300
echo "== Expect lines"; git show "$branch:$item" | grep -n '^Expect' | cut -c1-200
echo "== new markers"
git diff "origin/main...$branch" -- src tests | grep -E '^\+' | grep -nE 'noqa|type: ignore|pragma: no|pytest.mark.skip|xfail' || echo "none"
echo "== cost (the factory's table on the pull request)"
gh pr view "$1" --repo "$repo" --json comments \
  --jq '[.comments[] | select(.body | contains(":cost_table:"))][-1].body // "no cost table yet"' |
  grep -E '^\| \*\*total|no cost table' || echo "no total line"
