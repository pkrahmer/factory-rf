#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# Reset the site's trial repository to tag <tag>, so that a run can be repeated: close its open
# work-item pull requests, delete its work-item branches and move main to the tag's commit by
# force. The move cannot be undone, so without --yes it only prints the plan. It works through the
# API alone, and only on the repository that is both SITE_REPOSITORY and SITE_RESET_REPOSITORY.
#   reset-to-tag.sh <tag> [--yes]
set -eu
case $# in
  1) yes= ;;
  2) [ "$2" = --yes ] || { echo "usage: reset-to-tag.sh <tag> [--yes]" >&2; exit 2; }; yes=1 ;;
  *) echo "usage: reset-to-tag.sh <tag> [--yes]" >&2; exit 2 ;;
esac
here=$(cd "$(dirname "$0")" && pwd -P)
. "$here/../../../lib/site.sh"
. "$here/../../../lib/hosting.sh"
tag=$1
site_require SITE_REPOSITORY SITE_RESET_REPOSITORY || exit 2
if [ "$SITE_REPOSITORY" != "$SITE_RESET_REPOSITORY" ]; then
  echo "reset-to-tag.sh: $SITE_REPOSITORY is not the site's resettable repository" >&2
  exit 1
fi

# Prints the value of the dotted `path` in the JSON on standard input.
json_field() {
  python3 -I -c '
import json, sys
value = json.load(sys.stdin)
for key in sys.argv[1].split("."):
    value = value[key]
print(value)
' "$1"
}

# Prints the commit the tag names; an annotated tag is followed once to its object. Only a 404
# means the tag is missing; any other failure keeps the hosting client's message.
tag_commit() {
  errors=$(mktemp)
  if ! ref=$(hosting_repo_api GET "/git/ref/tags/$tag" 2>"$errors"); then
    if grep -q ': 404' "$errors"; then
      echo "reset-to-tag.sh: no tag $tag" >&2
    else
      cat "$errors" >&2
    fi
    rm -f "$errors"
    return 1
  fi
  rm -f "$errors"
  sha=$(printf '%s' "$ref" | json_field object.sha)
  if [ "$(printf '%s' "$ref" | json_field object.type)" = tag ]; then
    annotated=$(hosting_repo_api GET "/git/tags/$sha") || return 1
    sha=$(printf '%s' "$annotated" | json_field object.sha)
  fi
  printf '%s\n' "$sha"
}

commit=$(tag_commit) || exit 1
open_pulls=$(hosting_repo_api GET "/pulls?state=open&per_page=100") || exit 1
pulls=$(printf '%s' "$open_pulls" | python3 -I -c '
import json, sys
for pull in json.load(sys.stdin):
    if pull["head"]["ref"].startswith("work-item/"):
        print(pull["number"])
')
refs=$(hosting_repo_api GET "/git/matching-refs/heads/work-item/") || exit 1
branches=$(printf '%s' "$refs" | python3 -I -c '
import json, sys
for ref in json.load(sys.stdin):
    print(ref["ref"].removeprefix("refs/heads/"))
')
short=$(printf '%.7s' "$commit")

if [ -z "$yes" ]; then
  echo "would close $(printf '%s' "$pulls" | grep -c .) open work-item pull request(s)"
  echo "would delete $(printf '%s' "$branches" | grep -c .) work-item branch(es)"
  echo "would move main to $short"
  echo "run again with --yes"
  exit 1
fi
# Each step stops the script at its first failure, so that a half reset is visible.
for number in $pulls; do
  hosting_repo_api PATCH "/pulls/$number" '{"state":"closed"}' >/dev/null || exit 1
  echo "closed #$number"
done
for branch in $branches; do
  hosting_repo_api DELETE "/git/refs/heads/$branch" >/dev/null || exit 1
  echo "deleted $branch"
done
hosting_repo_api PATCH /git/refs/heads/main "{\"sha\":\"$commit\",\"force\":true}" >/dev/null || exit 1
echo "moved main to $short"
