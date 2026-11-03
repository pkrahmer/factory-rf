#!/bin/sh
# Start story <id>: move it from its feature's backlog/ to in-progress/ on main, commit "<id>: start",
# pull and push, with Kumpel <kumpel@noreply.invalid> as its author. The factory claims it at its
# next tick.
#   start-story.sh <id>
set -eu
[ $# -eq 1 ] || { echo "usage: start-story.sh <story id, e.g. F0047-S0003>" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd -P)
. "$here/../../../lib/site.sh"
. "$here/../../../lib/hosting.sh"
cd "$(sh "$here/settings.sh" get checkout)"
git checkout -q main
hosting_git pull -q --no-rebase
file=$(ls factory/features/*/backlog/"$1"-*.md 2>/dev/null | head -n 1)
[ -n "$file" ] || { echo "start-story.sh: no story $1 in any backlog/" >&2; exit 1; }
folder=$(dirname "$(dirname "$file")")
mkdir -p "$folder/in-progress"
git mv "$file" "$folder/in-progress/"
# Kumpel is the commit's author, for this one commit: the clone's own identity is the human's.
GIT_AUTHOR_NAME=Kumpel GIT_AUTHOR_EMAIL=kumpel@noreply.invalid \
  GIT_COMMITTER_NAME=Kumpel GIT_COMMITTER_EMAIL=kumpel@noreply.invalid \
  git commit -q -m "$1: start"
hosting_git pull -q --no-rebase
hosting_git push -q
git log --oneline -1
