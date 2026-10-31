#!/bin/sh
# The factory's state from GitHub alone, one line per open work-item pull request:
#   #<n> <work item> stage:<stage> <waits: <kind>|verdict posted|working>
# and a last line with the newest archive commit on main. Works for an instance on a VM or in a job.
# The factory marks its posts with `<!-- factory key=<id>:<kind>:<n> -->`; a comment without that
# marker is the human's (or the operator's), and ends the factory's wait.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
repo=$(sh "$here/settings.sh" get repository)
gh pr list --repo "$repo" --state open --limit 50 --json number,headRefName,labels \
  --jq '.[] | select(.headRefName | startswith("work-item/")) | "\(.number) \(.headRefName | sub("work-item/"; "")) \([.labels[].name | select(startswith("stage:"))] | join(","))"' |
while read -r number item stage; do
  last=$(gh pr view "$number" --repo "$repo" --json comments --jq '.comments[-1].body // ""' | tail -n 3)
  kind=$(printf '%s\n' "$last" | sed -n 's/^<!-- factory key=[^:]*:\([^:]*\):[^:]* -->$/\1/p' | tail -n 1)
  case "$kind" in
    question|attempts_cap|round_cap|crash_cap|stall|expiry|error) state="waits: $kind" ;;
    *)
      if printf '%s\n' "$last" | grep -q '<!-- operator verdict -->'; then state="verdict posted"
      elif [ "$stage" = "stage:approval" ]; then state="waits: approval"
      else state="working"
      fi ;;
  esac
  echo "#$number $item ${stage:-stage:?} $state"
done
gh api "repos/$repo/commits?per_page=20" --jq '[.[] | .commit.message | split("\n")[0] | select(startswith("work item ") and endswith(": merged, archived"))][0] // "no archive commit in the last 20"' |
  sed 's/^/last archive: /'
