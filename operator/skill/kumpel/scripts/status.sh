#!/bin/sh
# The factory's state from the code host alone, one line per open work-item pull request:
#   #<n> <work item> stage:<stage> <waits: <kind>|verdict posted|working>
# and a last line with the newest archive commit on main. Works for an instance on a VM or in a job.
# The factory marks its posts with `<!-- factory key=<id>:<kind>:<n> -->`; a comment without that
# marker is the human's (or the operator's), and ends the factory's wait. Kumpel's verdict holds
# `<!-- kumpel verdict -->` anywhere in its body, since its signature follows the verdict.
set -eu
here=$(cd "$(dirname "$0")" && pwd -P)
. "$here/../../../lib/site.sh"
. "$here/../../../lib/hosting.sh"
SITE_REPOSITORY=$(sh "$here/settings.sh" get repository)
export SITE_REPOSITORY

# Prints `<n> <work item> <stage labels>` for each work-item pull request of the API's list.
work_items() {
  python3 -c '
import json, sys
for pull in json.load(sys.stdin):
    branch = pull["head"]["ref"]
    if branch.startswith("work-item/"):
        stages = [label["name"] for label in pull["labels"] if label["name"].startswith("stage:")]
        print(pull["number"], branch.removeprefix("work-item/"), ",".join(stages))
'
}

# The body of the newest comment of pull request <n>, nothing when it has none: the comment count
# names the last page of one comment each, so one more call fetches it alone.
newest_comment() {
  count=$(hosting_repo_api GET "/issues/$1" | python3 -c 'import json, sys; print(json.load(sys.stdin)["comments"])')
  [ "$count" -gt 0 ] || return 0
  hosting_repo_api GET "/issues/$1/comments?per_page=1&page=$count" |
    python3 -c 'import json, sys; print(json.load(sys.stdin)[-1]["body"])'
}

pulls=$(hosting_repo_api GET "/pulls?state=open&per_page=50")
items=$(printf '%s' "$pulls" | work_items)
while read -r number item stage; do
  [ -n "$number" ] || continue
  comment=$(newest_comment "$number")
  last=$(printf '%s\n' "$comment" | tail -n 3)
  kind=$(printf '%s\n' "$last" | sed -n 's/^<!-- factory key=[^:]*:\([^:]*\):[^:]* -->$/\1/p' | tail -n 1)
  case "$kind" in
    question|attempts_cap|round_cap|crash_cap|stall|expiry|error) state="waits: $kind" ;;
    *)
      if printf '%s\n' "$comment" | grep -q '<!-- kumpel verdict -->'; then state="verdict posted"
      elif [ "$stage" = "stage:approval" ]; then state="waits: approval"
      else state="working"
      fi ;;
  esac
  echo "#$number $item ${stage:-stage:?} $state"
done <<ITEMS
$items
ITEMS
hosting_repo_api GET "/commits?per_page=20" | python3 -c '
import json, sys
subjects = (commit["commit"]["message"].split("\n")[0] for commit in json.load(sys.stdin))
archives = [s for s in subjects if s.startswith("work item ") and s.endswith(": merged, archived")]
print(archives[0] if archives else "no archive commit in the last 20")
' | sed 's/^/last archive: /'
