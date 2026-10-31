# P16: is the test suite slow in the job because of fuse-overlayfs?
# P15's second run: `make test` took 601 s in a job of 8 requested CPUs (10 seen), against 167 s on the
# 4-CPU VM, about nine times slower per CPU. S0002's podman words store images through fuse-overlayfs, so
# every file a container reads from its image (Python, git, node, every process the tests start) passes a
# userspace daemon. P8 showed podman's native kernel overlay working with its storage on a tmpfs. This
# probe repeats P15's `make sync` and `make test` with the storage on a tmpfs and the native overlay, and
# with nothing else changed, so its time compares with P15's 601 s. Needs no secret and no model.
# Inputs: PROBE_PROXY and PROBE_NO_PROXY as for every probe. Run it with 8 cpu and 32Gi.
setup_env
apt_install podman fuse-overlayfs nftables git make curl ca-certificates rsync python3 procps
echo "=====BEGIN-RESULTS====="
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
t0=$(date +%s)
since() { echo "$(( $(date +%s) - $1 )) s"; }
mem() { awk '/^MemTotal|^MemAvailable|^Shmem:/{printf "%s %d MiB  ", $1, $2/1024}' /proc/meminfo; echo; }

step "0: the job"
echo "cpus $(nproc)"; mem
grep -m1 "model name" /proc/cpuinfo

step "1: upstream runc 1.5.2, as in P15"
RUNC_SHA256=599f6f94ff8c5057241eff0d54c3c74f95c34935b6457b33fe545defc61e9488
curl -sSL -m 120 -o /tmp/runc.amd64 https://github.com/opencontainers/runc/releases/download/v1.5.2/runc.amd64
echo "$RUNC_SHA256  /tmp/runc.amd64" | sha256sum -c - && install -m 0755 /tmp/runc.amd64 /usr/local/bin/runc || { echo "runc failed: stopping"; echo "PROBE DONE"; exit 0; }

step "2: podman storage on a tmpfs, the native kernel overlay (no fuse-overlayfs)"
mkdir -p /srv/cstore && mount -t tmpfs -o size=24g tmpfs /srv/cstore; echo "tmpfs mount exit $?"
P="podman --runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay --root /srv/cstore/root --runroot /srv/cstore/run"
sh_run "$P info --format 'runtime {{.Host.OCIRuntime.Path}}, storage {{.Store.GraphDriverName}} at {{.Store.GraphRoot}}, native diff {{index .Store.GraphStatus \"Native Overlay Diff\"}}, backing {{index .Store.GraphStatus \"Backing Filesystem\"}}'"
sh_run "$P info 2>&1 | grep -i -E 'mount_program|fuse' | head -3; echo '(no line above: no mount program)'"

step "3: the stage image, as in P15"
s=$(date +%s)
GIT_TERMINAL_PROMPT=0 git clone -q https://github.com/pkrahmer/factory-rf.git /srv/code; echo "clone exit $? after $(since $s), at $(git -C /srv/code rev-parse --short HEAD)"
s=$(date +%s)
$P build --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=probe -t factory-stage:probe /srv/code > /tmp/build.log 2>&1; rc=$?
echo "build exit $rc after $(since $s)"
[ $rc -eq 0 ] || { grep -v -i "level=warning" /tmp/build.log | tail -15 | cut -c1-240; echo "PROBE DONE"; exit 0; }

step "4: make sync and make test in containers of the image, P15's words except the storage"
mkdir -p /srv/work/home
cp -a /srv/code /srv/work/checkout
NP="localhost,127.0.0.1${PROBE_NO_PROXY:+,$PROBE_NO_PROXY}"
PX=""
[ -n "${PROBE_PROXY:-}" ] && PX="--env http_proxy=$PROBE_PROXY --env https_proxy=$PROBE_PROXY --env HTTP_PROXY=$PROBE_PROXY --env HTTPS_PROXY=$PROBE_PROXY --env no_proxy=$NP --env NO_PROXY=$NP"
RUN="$P run --rm --http-proxy=false --network=host --cap-drop=all --security-opt=no-new-privileges --pids-limit=4096 --memory=4g --env HOME=/work/home $PX --volume /srv/work:/work --workdir /work/checkout"
s=$(date +%s)
timeout 420 $RUN --timeout 420 factory-stage:probe make sync > /tmp/sync.log 2>&1; rc=$?
echo "make sync exit $rc after $(since $s)"; tail -2 /tmp/sync.log | cut -c1-200
s=$(date +%s)
timeout 900 $RUN --timeout 900 factory-stage:probe make test > /tmp/test.log 2>&1; rc=$?
echo "make test exit $rc after $(since $s)"
echo "--- the test target's last lines:"; grep -v -i "level=warning" /tmp/test.log | tail -6 | cut -c1-240
echo "--- failed tests and their E lines (first 40 lines):"; grep -E "^FAILED|^ERROR|^E  " /tmp/test.log | head -40 | cut -c1-240
s=$(date +%s)
timeout 120 $RUN --timeout 120 factory-stage:probe sh -c 'for i in $(seq 1 50); do python3 -c pass; done' > /dev/null 2>&1
echo "50 python starts in one container: $(since $s)"
mem

echo; echo "total $(since $t0)"
echo "VERDICT: compare make test's time with P15's 601 s (fuse-overlayfs) and the VM's 167 s on 4 CPUs. If it is close to the VM's per CPU, S0002's storage words should change to a tmpfs root with the native overlay. If it is still near 600 s, fuse-overlayfs is not the cause, and the job's CPUs or the memory limit are next."
echo "PROBE DONE"
