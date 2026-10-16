#!/bin/sh
# Installs the image's agents and settings, prepares the runs directory and starts the
# instance. Git is configured by the factory itself, never here. The umask makes the
# factory's files group-writable, like the agent's under sudo, so either can remove the other's.
set -eu
umask 002
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
opt="${FACTORY_OPT:-/opt/factory}"
home="${FACTORY_CLAUDE_HOME:-$HOME/.claude}"
state="${FACTORY_STATE:-/state}"

if [ ! -d "$opt/claude/agents" ]; then
  log "missing $opt/claude/agents" >&2
  exit 1
fi
if [ ! -f "$opt/claude/settings.json" ]; then
  log "missing $opt/claude/settings.json" >&2
  exit 1
fi

# A replaced copy, so an agent the image no longer carries is gone from the home.
rm -rf "$home/agents"
mkdir -p "$home"
cp -R "$opt/claude/agents" "$home/agents"
cp "$opt/claude/settings.json" "$home/settings.json"
log "installed agents and settings into $home"

mkdir -p "$state/runs"
chmod 2750 "$state/runs"
log "prepared $state/runs"

log "starting instance ${FACTORY_INSTANCE:-unset}"
# A fixed directory, so the instance's `claude --version` runs in the same place each start.
cd "$opt"
exec python -m factory.entry.run
