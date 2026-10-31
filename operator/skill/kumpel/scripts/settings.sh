#!/bin/sh
# The operator's settings: one JSON file outside every repository, read before every act.
#   settings.sh show                         print the settings
#   settings.sh init <owner/name> <checkout> write a new file with the defaults
#   settings.sh set <switch> on|off          change one switch (merge, answer, start_next)
#   settings.sh get <key>                    print one value (repository, checkout, or a switch)
# The file: ${KUMPEL_SETTINGS:-$HOME/.config/kumpel/settings.json}.
set -eu
file=${KUMPEL_SETTINGS:-$HOME/.config/kumpel/settings.json}
command=${1:-show}

case "$command" in
  init)
    [ $# -eq 3 ] || { echo "usage: settings.sh init <owner/name> <checkout>" >&2; exit 2; }
    mkdir -p "$(dirname "$file")"
    python3 - "$file" "$2" "$3" <<'PY'
import json, sys
path, repository, checkout = sys.argv[1:]
settings = {"repository": repository, "checkout": checkout,
            "switches": {"merge": False, "answer": True, "start_next": True}}
with open(path, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
PY
    echo "settings written: $file" ;;
  show)
    [ -f "$file" ] || { echo "no settings at $file; run: settings.sh init <owner/name> <checkout>"; exit 1; }
    python3 - "$file" <<'PY'
import json, sys
s = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"repository {s['repository']}, checkout {s['checkout']}")
print("switches: " + ", ".join(f"{k} {'on' if v else 'off'}" for k, v in s["switches"].items()))
PY
    ;;
  get)
    [ $# -eq 2 ] || { echo "usage: settings.sh get <key>" >&2; exit 2; }
    python3 - "$file" "$2" <<'PY'
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
    python3 - "$file" "$2" "$3" <<'PY'
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
  *) echo "usage: settings.sh show | init <owner/name> <checkout> | set <switch> on|off | get <key>" >&2; exit 2 ;;
esac
