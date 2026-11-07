#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Merge pull request <pr> of work item <id> once it is open, ready and at stage:approval, with a
# merge commit (the factory reads a story's state from its branch), and wait for the factory's
# archive commit on main, so that the next story starts only after the merged one is archived.
# Whether the story deserves the merge is the skill's judgement (references/approving.md).
#   merge.sh <pr> <id>
# The wait: KUMPEL_POLL_SECONDS between polls (15), KUMPEL_ARCHIVE_WAIT at most (300).
set -eu
[ $# -eq 2 ] || { echo "usage: merge.sh <pull request> <work item id>" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd -P)
. "$here/../../../lib/site.sh"
. "$here/../../../lib/hosting.sh"
SITE_REPOSITORY=$(sh "$here/settings.sh" get repository)
export SITE_REPOSITORY
pr=$1 item=$2
poll=${KUMPEL_POLL_SECONDS:-15}
wait=${KUMPEL_ARCHIVE_WAIT:-300}

# Prints the first reason the pull request of the API's answer may not be merged, nothing when none.
refusal() {
  python3 -I -c '
import json, sys
pr, item = sys.argv[1:]
pull = json.load(sys.stdin)
if pull["state"] != "open":
    print(f"#{pr} is not open")
elif pull["draft"]:
    print(f"#{pr} is a draft")
elif "stage:approval" not in [label["name"] for label in pull["labels"]]:
    print(f"#{pr} is not at stage:approval")
elif pull["head"]["ref"] != f"work-item/{item}":
    print(f"#{pr} is not the pull request of {item}")
' "$pr" "$item"
}

archived() {
  commits=$(hosting_repo_api GET "/commits?per_page=20") || return 1
  printf '%s' "$commits" | python3 -I -c '
import json, sys
subject = f"work item {sys.argv[1]}: merged, archived"
sys.exit(0 if any(c["commit"]["message"].split("\n")[0] == subject for c in json.load(sys.stdin)) else 1)
' "$item"
}

pull=$(hosting_repo_api GET "/pulls/$pr") || exit 1
reason=$(printf '%s' "$pull" | refusal)
[ -z "$reason" ] || { echo "merge.sh: $reason" >&2; exit 1; }
branch=$(printf '%s' "$pull" | python3 -I -c 'import json, sys; print(json.load(sys.stdin)["head"]["ref"])')
# The merge commit says Kumpel merged it, since the human's token makes it.
body=$(python3 -I -c '
import json, sys
print(json.dumps({
    "merge_method": "merge",
    "commit_title": f"Merge pull request #{sys.argv[1]} from {sys.argv[2]}",
    "commit_message": "Merged by Kumpel after the six approval checks.",
}))
' "$pr" "$branch")
hosting_repo_api PUT "/pulls/$pr/merge" "$body" >/dev/null || exit 1
echo "merged #$pr"
# The clock, not a sum of the pauses, ends the wait, so a pause of 0 still ends it.
start=$(date +%s)
while :; do
  if archived; then
    echo "archived $item"
    exit 0
  fi
  [ $(($(date +%s) - start)) -lt "$wait" ] || break
  sleep "$poll"
done
echo "merge.sh: merged, but no archive commit for $item after $wait s" >&2
exit 1
