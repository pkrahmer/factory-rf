#!/bin/sh
# The operator's settings: the site file's repository and checkout, and one JSON file outside every
# repository for the switches (and for the repository and the checkout when the site gives none).
#   settings.sh show                         print the settings
#   settings.sh init [<owner/name> <checkout>] write a new file with the defaults; no arguments when
#                                            the site gives the repository and the checkout
#   settings.sh set <switch> on|off          change one switch (merge, answer, start_next)
#   settings.sh get <key>                    print one value (repository, checkout, or a switch)
# The file: ${KUMPEL_SETTINGS:-$HOME/.config/kumpel/settings.json}.
set -eu
here=$(cd "$(dirname "$0")" && pwd -P)
. "$here/../../../lib/site.sh"
# Without a site file the JSON file answers alone; a faulty one has said why on standard error.
if [ -f "$(site_path)" ]; then
  site_load || :
fi
file=${KUMPEL_SETTINGS:-$HOME/.config/kumpel/settings.json}
command=${1:-show}

# The site's value for repository or checkout, nothing when it gives none.
site_answer() {
  case "$1" in
    repository) site_value SITE_REPOSITORY ;;
    checkout) site_value SITE_CHECKOUT ;;
  esac
}

site_gives_both() {
  [ -n "$(site_answer repository)" ] && [ -n "$(site_answer checkout)" ]
}

case "$command" in
  init)
    # The JSON file keeps a repository and a checkout only when the site gives none.
    if [ $# -eq 3 ]; then
      repository=$2 checkout=$3
    elif [ $# -eq 1 ] && site_gives_both; then
      repository= checkout=
    else
      echo "usage: settings.sh init <owner/name> <checkout>" >&2; exit 2
    fi
    mkdir -p "$(dirname "$file")"
    python3 -I - "$file" "$repository" "$checkout" <<'PY'
import json, sys
path, repository, checkout = sys.argv[1:]
settings = {"repository": repository, "checkout": checkout} if repository else {}
settings["switches"] = {"merge": False, "answer": True, "start_next": True}
with open(path, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
PY
    echo "settings written: $file" ;;
  show)
    [ -f "$file" ] || { echo "no settings at $file; run: settings.sh init <owner/name> <checkout>"; exit 1; }
    python3 -I - "$file" "$(site_answer repository)" "$(site_answer checkout)" <<'PY'
import json, sys
path, repository, checkout = sys.argv[1:]
s = json.load(open(path, encoding="utf-8"))
print(f"repository {repository or s['repository']}, checkout {checkout or s['checkout']}")
print("switches: " + ", ".join(f"{k} {'on' if v else 'off'}" for k, v in s["switches"].items()))
PY
    ;;
  get)
    [ $# -eq 2 ] || { echo "usage: settings.sh get <key>" >&2; exit 2; }
    answer=$(site_answer "$2")
    if [ -n "$answer" ]; then
      printf '%s\n' "$answer"
      exit 0
    fi
    python3 -I - "$file" "$2" <<'PY'
import json, sys
s = json.load(open(sys.argv[1], encoding="utf-8"))
key = sys.argv[2]
if key in s["switches"]:
    print("on" if s["switches"][key] else "off")
elif key in ("repository", "checkout"):
    print(s[key])
else:
    sys.exit(f"unknown key: {key}")
PY
    ;;
  set)
    [ $# -eq 3 ] || { echo "usage: settings.sh set <switch> on|off" >&2; exit 2; }
    case "$3" in on|off) ;; *) echo "settings.sh: $3 is neither on nor off" >&2; exit 2 ;; esac
    python3 -I - "$file" "$2" "$3" <<'PY'
import json, sys
path, switch, value = sys.argv[1:]
s = json.load(open(path, encoding="utf-8"))
if switch not in s["switches"]:
    sys.exit(f"unknown switch: {switch} (known: {', '.join(s['switches'])})")
s["switches"][switch] = value == "on"
with open(path, "w", encoding="utf-8") as f:
    json.dump(s, f, indent=2)
    f.write("\n")
print(f"{switch} {value}")
PY
    ;;
  *) echo "usage: settings.sh show | init [<owner/name> <checkout>] | set <switch> on|off | get <key>" >&2; exit 2 ;;
esac
