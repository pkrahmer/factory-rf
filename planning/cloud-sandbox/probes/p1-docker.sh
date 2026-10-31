# P1: Docker Engine (docker:dind image) as the container runtime inside one Cloud Run job.
# Question: does a current dockerd start here, with which storage driver and flags, and do the controls
# the factory needs hold (memory and pids limits, read-only mounts, capability drop, time limit by the
# caller)? Version 2: the first run showed that containerd's overlay snapshotter fails on the job's own
# overlay root (option userxattr, EINVAL) and that Docker's default capability set contains MKNOD, which
# the sandbox's bounding set lacks; so this version puts the data root on a tmpfs and drops MKNOD.
setup_env
apk add --no-cache curl iptables nftables fuse-overlayfs >/tmp/apk.log 2>&1; echo "apk exit $?"
echo "=====BEGIN-RESULTS====="
step "versions"
run docker --version
run dockerd --version
run runc --version
step "identity of the sandbox the daemon meets"
sh_run 'cat /proc/self/uid_map; grep -E "^(CapBnd|NoNewPrivs)" /proc/self/status; head -3 /proc/self/cgroup'
sh_run 'df -hT / | tail -1'

# A tmpfs for data roots: overlay needs an upper directory on a filesystem that supports it.
mkdir -p /mnt/dr && mount -t tmpfs -o size=6g tmpfs /mnt/dr && echo "tmpfs for data roots mounted"

dstart() {
  n=$1; root=$2; shift 2
  mkdir -p $root/d-$n /tmp/x-$n
  dockerd --data-root $root/d-$n/data --exec-root /tmp/x-$n --pidfile /tmp/x-$n/pid \
    -H unix:///tmp/x-$n/sock "$@" >/tmp/x-$n/log 2>&1 &
  i=0
  while [ $i -lt 40 ]; do
    docker -H unix:///tmp/x-$n/sock info >/dev/null 2>&1 && { echo "daemon $n up after $i s"; return 0; }
    i=$((i+1)); sleep 1
  done
  echo "daemon $n did NOT come up; last log lines:"; tail -12 /tmp/x-$n/log | cut -c1-300
  return 1
}
dstop() { kill "$(cat /tmp/x-$1/pid 2>/dev/null)" 2>/dev/null; sleep 3; }
D() { n=$1; shift; docker -H unix:///tmp/x-$n/sock "$@"; }
info() { D "$1" info --format 'storage={{.Driver}} cgroup={{.CgroupDriver}}/v{{.CgroupVersion}} runc-features=ok' 2>&1 | head -2; }
# Docker names every capability of its default set and refuses ones the sandbox's bounding set lacks
# (CAP_MKNOD is missing: even --cap-drop=MKNOD is refused). So every run drops ALL and adds back only
# the default capabilities that exist here.
CAPS="--cap-drop=ALL --cap-add=CHOWN --cap-add=DAC_OVERRIDE --cap-add=FOWNER --cap-add=FSETID --cap-add=KILL --cap-add=SETGID --cap-add=SETUID --cap-add=SETPCAP --cap-add=NET_BIND_SERVICE --cap-add=SYS_CHROOT --cap-add=SETFCAP"
dr() { n=$1; shift; D "$n" run --rm $CAPS "$@"; }
NOFW="--iptables=false --ip6tables=false --bridge=none"
GOOD=

try() { # try <name> <root> <dockerd flags...>: start and run one container
  n=$1; root=$2; shift 2
  step "$n: $*  (data root $root)"
  if dstart "$n" "$root" "$@"; then
    info "$n"
    if dr "$n" --network=host busybox echo "$n-ok" 2>&1 | tail -3 | tee /tmp/try.out | grep -q "$n-ok"; then
      echo "RESULT $n: container ran"; [ -z "$GOOD" ] && { GOOD=$n; GOOD_ROOT=$root; GOOD_FLAGS="$*"; }
    else echo "RESULT $n: container did NOT run:"; cut -c1-420 /tmp/try.out; fi
    dstop "$n"
  fi
}

try v1 /mnt/dr $NOFW
try v2 /mnt/dr $NOFW --feature containerd-snapshotter=false --storage-driver=overlay2
try v3 /mnt/dr $NOFW --feature containerd-snapshotter=false --storage-driver=fuse-overlayfs
try v4 /mnt/dr $NOFW --feature containerd-snapshotter=false --storage-driver=vfs
echo; echo "first working variant: ${GOOD:-NONE}  flags: ${GOOD_FLAGS:-}  root: ${GOOD_ROOT:-}"

if [ -n "$GOOD" ]; then
  step "FULL TESTS on $GOOD"
  dstart T "$GOOD_ROOT" $GOOD_FLAGS >/dev/null 2>&1 || dstart T "$GOOD_ROOT" $GOOD_FLAGS
  step "T1: the factory's controls (cap-drop ALL, no-new-privileges, memory, pids)"
  run dr T --network=host --security-opt=no-new-privileges --memory=256m --pids-limit=256 busybox echo T1-flags-ok
  step "T2: pids limit enforced (20) by a fork loop"
  run dr T --network=host --pids-limit=20 busybox sh -c 'i=0; while [ $i -lt 60 ]; do sleep 5 & i=$((i+1)); done 2>&1; echo forked'
  step "T3: memory limit enforced: hold 300 MB in a shell variable under --memory=128m (expect exit 137), and without a limit (expect success)"
  run dr T --network=host --memory=128m --memory-swap=128m busybox sh -c 'x=$(head -c 300000000 /dev/zero | tr "\\0" a); echo held ${#x}'
  run dr T --network=host busybox sh -c 'x=$(head -c 300000000 /dev/zero | tr "\\0" a); echo held ${#x}'
  run dr T --network=host --memory=128m --cpus=0.5 busybox sh -c 'cat /sys/fs/cgroup/memory/memory.limit_in_bytes /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>&1'
  step "T4: bind mounts: read-write works, read-only enforced; read-only root"
  mkdir -p /tmp/work /tmp/ro; echo hello > /tmp/ro/f
  run dr T --network=host -v /tmp/work:/work -v /tmp/ro:/ro:ro busybox sh -c 'echo x > /work/w; cat /work/w; echo y > /ro/z; echo "ro write exit $?"'
  run dr T --network=host --read-only busybox sh -c 'echo y > /z; echo "ro root write exit $?"'
  step "T5: time limit: docker run has none; the caller starts detached, waits, kills"
  s=$(date +%s)
  D T run -d --name sleeper $CAPS --network=host busybox sleep 60 >/dev/null 2>&1
  sleep 3; D T kill sleeper >/dev/null 2>&1; D T rm -f sleeper >/dev/null 2>&1
  echo "start, wait 3 s, kill, remove: $(( $(date +%s)-s )) s; containers left: $(D T ps -aq | wc -l)"
  step "T6: a numeric user writing to a bind mount that belongs to it, and to one that belongs to root"
  chown 1000:1000 /tmp/work; mkdir -p /tmp/work2
  run dr T --network=host --user 1000:1000 -v /tmp/work:/work busybox sh -c 'id; echo u > /work/u; ls -ln /work/u'
  run dr T --network=host --user 1000:1000 -v /tmp/work2:/work busybox sh -c 'echo u > /work/u 2>&1; echo "exit $?"'
  step "T7: reach the metadata server from the container (status only)"
  run dr T --network=host busybox sh -c 'wget -q -T 5 -O /dev/null --header "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/id && echo metadata-REACHABLE || echo metadata-blocked'
  step "T8: second start speed and image pull through the proxy (daemon honours the proxy env)"
  s=$(date +%s); D T run --rm $CAPS --network=host busybox true; echo "second start: $(( $(date +%s)-s )) s"
  step "T9: a bigger image through the proxy (python:3.12-slim, about 50 MB)"
  s=$(date +%s); D T pull python:3.12-slim 2>&1 | tail -2; echo "pull took $(( $(date +%s)-s )) s"
  step "T10: docker build with a Dockerfile (needs buildkit; uses the proxy for apt)"
  mkdir -p /tmp/bt && printf 'FROM busybox\nRUN echo built > /built\n' > /tmp/bt/Dockerfile
  s=$(date +%s); run D T build --network=host -t probe-built /tmp/bt; echo "build took $(( $(date +%s)-s )) s"
  dstop T
  step "T11: default bridge networking (iptables on, containerd image store): does the daemon start, can a container reach out?"
  PROXY_HOST=$(echo "$PROBE_PROXY" | sed -e 's#^[a-z]*://##' -e 's#:[0-9]*$##'); PROXY_PORT=$(echo "$PROBE_PROXY" | sed -e 's#.*:##')
  PROXY_IP=$(getent hosts "$PROXY_HOST" | awk '{print $1; exit}')
  if dstart Tn "$GOOD_ROOT"; then
    run dr Tn busybox echo bridge-ok
    run dr Tn busybox sh -c "wget -q -T 6 -O /dev/null -Y on -e use_proxy=on https_proxy=http://$PROXY_IP:$PROXY_PORT https://github.com && echo bridge-proxy-ok || echo bridge-proxy-failed"
    run dr Tn busybox sh -c 'wget -q -T 5 -O /dev/null --header "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/id && echo metadata-REACHABLE || echo metadata-blocked'
    dstop Tn
  else echo "daemon with default networking did not start"; tail -5 /tmp/x-Tn/log | cut -c1-300; fi
fi
echo; echo "PROBE DONE"
