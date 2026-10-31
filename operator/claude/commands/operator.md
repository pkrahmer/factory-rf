---
description: Show or change the factory operator's switches (merge, answer, start_next)
argument-hint: "[<switch> on|off]"
---
The arguments are "$ARGUMENTS". When they are two words, a switch and `on` or `off`, run `sh ~/.claude/skills/factory-operator/scripts/settings.sh set <switch> <on|off>`; when they are empty, run `sh ~/.claude/skills/factory-operator/scripts/settings.sh show`. Print its output and nothing else, then go on with what you were doing; the change takes effect at your next act.
