#!/bin/sh
# The command of a Cloud Run job: turns a bare debian:trixie-slim into a running instance and
# ends in factory-run. Nothing persists between the job's starts, so every start installs,
# clones and builds again. The job's environment is the instance's configuration; the script
# sets a derived setting only where the job gave none.
set -eu

JOB_PODMAN_OPTIONS="--runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay"
DEFAULT_RUNC_VERSION=1.5.2
DEFAULT_RUNC_SHA256=599f6f94ff8c5057241eff0d54c3c74f95c34935b6457b33fe545defc61e9488

stop() {
  printf 'job-start: %s\n' "$2" >&2
  exit "$1"
}

failed() {
  stop 1 "$1: failed"
}

step() {
  printf 'job-start: %s\n' "$1"
}

require() {
  eval "value=\${$1:-}"
  if [ -z "$value" ]; then
    stop 2 "$1 is not set"
  fi
}

default() {
  eval "value=\${$1:-}"
  if [ -z "$value" ]; then
    eval "$1=\$2"
  fi
  export "$1"
}

# The pins live in the code checkout's stage image, read the way vm/setup.sh reads them.
dockerfile_arg() {
  sed -n "s/^ARG $1=//p" "$code/vm/Dockerfile" 2>/dev/null || true
}

for name in FACTORY_INSTANCE FACTORY_REPOSITORY_URL FACTORY_CODE_URL FACTORY_CODE_REF FACTORY_TOKEN_FILE; do
  require "$name"
done
if [ ! -f "$FACTORY_TOKEN_FILE" ] || [ ! -r "$FACTORY_TOKEN_FILE" ]; then
  stop 2 "FACTORY_TOKEN_FILE is not a file"
fi
# A version without its own checksum would be installed unchecked.
if [ -n "${RUNC_VERSION:-}" ]; then
  require RUNC_SHA256
fi

step inputs
runc_version=${RUNC_VERSION:-$DEFAULT_RUNC_VERSION}
runc_sha256=${RUNC_SHA256:-$DEFAULT_RUNC_SHA256}
prefix=${FACTORY_JOB_PREFIX:-}
root=${FACTORY_JOB_ROOT:-/srv/factory/$FACTORY_INSTANCE}
code=$root/factory
default FACTORY_STAGE_IMAGE "factory-stage:$FACTORY_INSTANCE"
default FACTORY_SNAPSHOTS copy
default FACTORY_SNAPSHOT_BASE "$root/base"
default FACTORY_WORKSPACE "$root/work"
default FACTORY_CHECKOUT "$root/repo"
default FACTORY_STATE "$root/state"
default FACTORY_CLAUDE_HOME "$code/claude"
default FACTORY_IMAGE_ID_FILE "$root/image-id"
default FACTORY_CONTAINER_PROFILE job
default FACTORY_AGENT_RUNTIME opencode
default FACTORY_IDLE_SHUTDOWN_ACTION exit

step proxy
proxy=${HTTPS_PROXY:-${https_proxy:-}}
if [ -n "$proxy" ]; then
  export HTTPS_PROXY="$proxy" https_proxy="$proxy"
  cat >"$prefix/etc/apt/apt.conf.d/99proxy" <<EOF || failed proxy
Acquire::http::Proxy "$proxy";
Acquire::https::Proxy "$proxy";
EOF
fi

step packages
apt-get update || failed packages
apt-get install -y --no-install-recommends podman uidmap nftables git make curl ca-certificates rsync python3 python3-venv || failed packages

step runc
download=$(mktemp -d) || failed runc
curl -fsSL -o "$download/runc.amd64" "https://github.com/opencontainers/runc/releases/download/v$runc_version/runc.amd64" || failed runc
# The checksum is the script's own: one downloaded beside the binary would check nothing.
printf '%s  %s\n' "$runc_sha256" "$download/runc.amd64" | sha256sum -c >/dev/null || stop 1 "runc: checksum does not match"
install -m 0755 "$download/runc.amd64" "$prefix/usr/local/bin/runc" || failed runc
rm -rf "$download"

step metadata
mkdir -p "$root" || failed metadata
cat >"$root/metadata-block.nft" <<'EOF' || failed metadata
table inet factory_block {
  chain blockout {
    type filter hook output priority 0; policy accept;
    ip daddr 169.254.169.254 tcp dport 80 reject
  }
  chain blockfwd {
    type filter hook forward priority 0; policy accept;
    ip daddr 169.254.169.254 tcp dport 80 reject
  }
}
EOF
nft -f "$root/metadata-block.nft" || failed metadata

step directories
mkdir -p "$FACTORY_WORKSPACE" "$FACTORY_SNAPSHOT_BASE" "$FACTORY_CHECKOUT" "$FACTORY_STATE" || failed directories

step storage
storage=$prefix/var/lib/containers
# Images need the kernel's overlay, which the job's own root filesystem cannot carry.
mkdir -p "$storage" && mount -t tmpfs tmpfs "$storage" || stop 1 "storage: cannot mount a tmpfs at $storage"

step code
unset GIT_ASKPASS SSH_ASKPASS
GIT_TERMINAL_PROMPT=0 git clone --no-checkout "$FACTORY_CODE_URL" "$code" || failed code
GIT_TERMINAL_PROMPT=0 git -C "$code" checkout --detach "$FACTORY_CODE_REF" || stop 1 "code: no ref $FACTORY_CODE_REF in $FACTORY_CODE_URL"

step tools
tools=$root/tools
uv_version=$(dockerfile_arg UV_VERSION)
# The preflight compares the stage image's agent runtime with these versions.
default FACTORY_CLAUDE_VERSION "$(dockerfile_arg CLAUDE_CODE_VERSION)"
default FACTORY_OPENCODE_VERSION "$(dockerfile_arg OPENCODE_VERSION)"
python3 -m venv "$tools" || failed tools
"$tools/bin/pip" install -q "uv==$uv_version" || failed tools
(cd "$code" && "$tools/bin/uv" sync --frozen --no-dev) || failed tools

step image
# shellcheck disable=SC2086 # the options are words of their own
(cd "$code" && podman $JOB_PODMAN_OPTIONS build --network=host -f vm/Dockerfile --build-arg "FACTORY_IMAGE=$FACTORY_CODE_REF" -t "$FACTORY_STAGE_IMAGE" "$code") || failed image
cat /proc/sys/kernel/random/uuid >"$FACTORY_IMAGE_ID_FILE" || failed image

step token
if [ -n "${FACTORY_TOKEN_URL:-}" ]; then
  "$code/.venv/bin/python" -m factory.entry.refresh_token --once || failed token
  "$code/.venv/bin/python" -m factory.entry.refresh_token &
fi

step start
exec "$code/.venv/bin/factory-run"
