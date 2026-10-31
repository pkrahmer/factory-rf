# P19: is a Cloud Run worker pool the same sandbox as a job, and how does it treat a process that ends?
# F0047 builds for a job (a task with a timeout, a nightly restart). A worker pool runs a long-lived
# process with no timeout and a fixed number of instances, which may fit an always-on factory better. This
# probe runs in a worker pool (through run_worker_pool.sh) and answers:
#   1. The sandbox: the same kernel, cgroups, root, NoNewPrivs and CPUs as a job (P6)?
#   2. The factory's needs: nft's metadata block, a tmpfs mount, podman as root with S0009's words, a
#      container with the factory's limits, the proxy?
#   3. The lifecycle: each start prints a line with its own id; after its checks the process exits 0 (or
#      with PROBE_MODEL=stay it waits). The harness watches whether the pool starts it again, then scales
#      to zero (does the process get SIGTERM first?) and back to one.
# Needs no secret and no model. Lines the harness keeps start with `probe:`.
echo "=====BEGIN-RESULTS====="
id=$(head -c 6 /dev/urandom | od -An -tx1 | tr -d ' \n')
t0=$(date +%s)
say() { echo "probe: [$id +$(( $(date +%s) - t0 ))s] $*"; }
trap 'say "got SIGTERM"; exit 0' TERM
say "start, pid $$, at $(date -u +%H:%M:%S), boot id $(cat /proc/sys/kernel/random/boot_id 2>/dev/null | cut -c1-8)"
say "kernel $(uname -r), cpus $(nproc), mem $(awk '/^MemTotal/{print int($2/1024) " MiB"}' /proc/meminfo)"
say "uid $(id -u), $(grep -E '^(CapEff|NoNewPrivs)' /proc/self/status | tr '\n\t' '  ')"
say "cgroups: $(stat -fc %T /sys/fs/cgroup), root fs $(stat -fc %T /)"
setup_env
apt_install podman nftables curl ca-certificates
say "apt: $(tail -1 /tmp/apt.log 2>/dev/null | cut -c1-120)"
cat > /tmp/block.nft <<'NFT'
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
NFT
nft -f /tmp/block.nft; say "nft metadata block: exit $?"
code=$(curl -sS -m 5 -o /dev/null -w '%{http_code}' -H 'Metadata-Flavor: Google' http://169.254.169.254/computeMetadata/v1/instance/id 2>/dev/null | tail -1)
say "metadata server after the block: $code (000 means blocked)"
mkdir -p /var/lib/containers
mount -t tmpfs tmpfs /var/lib/containers; say "tmpfs at /var/lib/containers: exit $?"
RUNC_SHA256=599f6f94ff8c5057241eff0d54c3c74f95c34935b6457b33fe545defc61e9488
curl -sSL -m 120 -o /tmp/runc.amd64 https://github.com/opencontainers/runc/releases/download/v1.5.2/runc.amd64
if echo "$RUNC_SHA256  /tmp/runc.amd64" | sha256sum -c - >/dev/null 2>&1; then
  install -m 0755 /tmp/runc.amd64 /usr/local/bin/runc; say "runc 1.5.2 installed"
else
  say "runc checksum failed"
fi
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
P="podman --runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay"
s=$(date +%s)
out=$($P run --rm --http-proxy=false --network=host --timeout 60 --cap-drop=all --security-opt=no-new-privileges --pids-limit=4096 --memory=1g docker.io/library/debian:trixie-slim sh -c 'echo inside uid $(id -u); cat /proc/self/status | grep -E "^CapEff"' 2>&1 | grep -v -i "level=warning" | tr '\n' ' ' | cut -c1-200)
say "container with the factory's words: '$out' after $(( $(date +%s) - s )) s"
say "storage: $($P info --format '{{.Store.GraphDriverName}}, native diff {{index .Store.GraphStatus "Native Overlay Diff"}}, backing {{index .Store.GraphStatus "Backing Filesystem"}}' 2>/dev/null)"
if [ "${PROBE_MODEL:-}" = "stay" ]; then
  say "checks done; staying"
  while :; do sleep 30; say "alive"; done
fi
say "checks done; exiting 0 now (does the pool start this process again?)"
echo "PROBE DONE"
exit 0
