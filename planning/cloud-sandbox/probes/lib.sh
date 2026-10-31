#!/bin/sh
# Shared helpers of every probe. POSIX sh only: the probe images are Debian or Alpine.
# The probe's own output follows the line "=====BEGIN-RESULTS=====", so that package-manager noise
# printed before it can be cut away when the log is read.

step() { echo; echo "##### $*"; }

# run <command...>: print the command, its first lines of output and its exit status.
run() {
  echo "\$ $*"
  out=$("$@" 2>&1); rc=$?
  echo "$out" | head -"${LINES_MAX:-20}"
  echo "[exit $rc]"
}

# sh_run <shell text>: the same for a shell command line.
sh_run() {
  echo "\$ $*"
  out=$(sh -c "$*" 2>&1); rc=$?
  echo "$out" | head -"${LINES_MAX:-20}"
  echo "[exit $rc]"
}

# setup_env: route package managers and downloads through the proxy the job is given.
# The metadata server and localhost are never proxied.
setup_env() {
  if [ -n "${PROBE_PROXY:-}" ]; then
    export http_proxy="$PROBE_PROXY" https_proxy="$PROBE_PROXY" HTTP_PROXY="$PROBE_PROXY" HTTPS_PROXY="$PROBE_PROXY"
    export no_proxy="169.254.169.254,metadata.google.internal,localhost,127.0.0.1"
    export NO_PROXY="$no_proxy"
    if [ -d /etc/apt/apt.conf.d ]; then
      echo "Acquire::http::Proxy \"$PROBE_PROXY\"; Acquire::https::Proxy \"$PROBE_PROXY\";" > /etc/apt/apt.conf.d/99proxy
    fi
  fi
  export DEBIAN_FRONTEND=noninteractive
}

# apt_install <packages...>: quiet install; the exit status is reported, the noise is kept in a file.
apt_install() {
  apt-get update -qq >/dev/null 2>&1
  apt-get install -y -qq --no-install-recommends "$@" >/tmp/apt.log 2>&1
  echo "apt install exit $? ($*)"
}

# A root filesystem for container tests that need no image pull.
make_rootfs() {
  R=${1:-/tmp/rootfs}
  mkdir -p "$R/bin" "$R/proc" "$R/dev" "$R/tmp"
  B=$(command -v busybox)
  cp "$B" "$R/bin/busybox" && for t in sh echo id cat ls sleep wget; do ln -sf busybox "$R/bin/$t"; done
}

# fetch the HTTP status of a URL through the proxy (empty body discarded)
http_code() { curl -sS -m "${2:-12}" -o /dev/null -w '%{http_code}' "$1" 2>&1 | tail -1; }
