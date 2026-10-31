#!/bin/sh
# Start story <id>: move it from its feature's backlog/ to in-progress/ on main, commit "<id>: start",
# pull and push. The factory claims it at its next tick.
#   start-story.sh <id>
set -eu
[ $# -eq 1 ] || { echo "usage: start-story.sh <story id, e.g. F0047-S0003>" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd)
cd "$(sh "$here/settings.sh" get checkout)"
git checkout -q main
git pull -q --no-rebase
file=$(ls factory/features/*/backlog/"$1"-*.md 2>/dev/null | head -n 1)
[ -n "$file" ] || { echo "start-story.sh: no story $1 in any backlog/" >&2; exit 1; }
folder=$(dirname "$(dirname "$file")")
mkdir -p "$folder/in-progress"
git mv "$file" "$folder/in-progress/"
git commit -q -m "$1: start"
git pull -q --no-rebase
git push -q
git log --oneline -1
