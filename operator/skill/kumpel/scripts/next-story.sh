#!/bin/sh
# The next story to start, from the checkout's main branch. Prints one line:
#   next: <story id>       the first story of a feature's *Stories* list that is still in its backlog/
#   busy: <work item id>   a work item is in progress; start nothing
#   none                   every listed story is started or done
# The features are taken in the order of their folders (F0001 before F0002); within a feature the
# order is the bullet list under `## Stories` in its feature.md (`- S0001: ...`), which is the build
# order the feature's text sets.
#   next-story.sh
set -eu
here=$(cd "$(dirname "$0")" && pwd)
cd "$(sh "$here/settings.sh" get checkout)"
git checkout -q main
git pull -q --no-rebase
for path in factory/features/*/in-progress/*.md; do
  [ -f "$path" ] || continue
  echo "busy: $(basename "$path" | cut -d- -f1-2)"
  exit 0
done
for feature in factory/features/*/; do
  [ -f "$feature/feature.md" ] || continue
  id=$(basename "$feature" | cut -d- -f1)
  for story in $(sed -n '/^## Stories/,/^## /p' "$feature/feature.md" | sed -n 's/^- \(S[0-9][0-9]*\):.*/\1/p'); do
    if ls "$feature/backlog/$id-$story-"*.md >/dev/null 2>&1; then
      echo "next: $id-$story"
      exit 0
    fi
  done
done
echo "none"
