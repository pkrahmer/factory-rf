#!/bin/sh
# Post the text of <file> as a comment on pull request <pr>, signed: a blank line, the signature
# line and the marker follow the text, so that a reader of the pull request or of the journal can
# tell Kumpel's comment from the human's, whose token posts it. A text already signed is posted
# as it is.
#   comment.sh <pr> <file>
set -eu
[ $# -eq 2 ] || { echo "usage: comment.sh <pull request> <file>" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd -P)
. "$here/../../../lib/site.sh"
. "$here/../../../lib/hosting.sh"
SITE_REPOSITORY=$(sh "$here/settings.sh" get repository)
export SITE_REPOSITORY
pr=$1 file=$2
[ -s "$file" ] || { echo "comment.sh: nothing to post in $file" >&2; exit 1; }

# Prints the JSON body of the comment: the file's text, signed once.
signed_body() {
  python3 -c '
import json, sys
signature = "\n\n— Kumpel, for the human who owns this project\n<!-- kumpel -->"
with open(sys.argv[1], encoding="utf-8") as text_file:
    text = text_file.read().rstrip("\n")
if not text.endswith(signature):
    text += signature
print(json.dumps({"body": text}))
' "$1"
}

hosting_repo_api POST "/issues/$pr/comments" "$(signed_body "$file")" >/dev/null || exit 1
echo "commented #$pr"
