# P15: does the factory's own stage image build in a job, and does factory-rf's `make check` pass in it?
# Question: F0047-S0006 builds `vm/Dockerfile` at every start of the job and runs every stage's checks in
# containers of that image, as the job's root with every capability dropped (F0047 decision 3). Neither
# was ever done in the sandbox: P10 and P14 used `node:22-slim`. This probe does, by hand, what S0006's
# script and the factory's sync and check containers will do, with S0002's podman words:
#   1. installs the tools and upstream runc 1.5.2 (checked against S0006's pinned SHA-256);
#   2. builds the stage image from a fresh clone of the public factory-rf, timing it and sizing it;
#   3. runs `make sync` and `make check` of that clone in containers of the image, as the factory would;
#   4. times a copy and an rsync of the synced tree (S0001's copy snapshots) and reports the memory used.
# Needs no secret and no model: the clone is public, nothing calls a model API. Inputs: PROBE_PROXY and
# PROBE_NO_PROXY as for every probe. Run it with 8 cpu and 32Gi.
setup_env
apt_install podman fuse-overlayfs nftables git make curl ca-certificates rsync python3 procps
echo "=====BEGIN-RESULTS====="
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
t0=$(date +%s)
since() { echo "$(( $(date +%s) - $1 )) s"; }
mem() { awk '/^MemTotal|^MemAvailable|^Shmem:/{printf "%s %d MiB  ", $1, $2/1024}' /proc/meminfo; echo; df -h / | tail -1; }

step "0: the job"
echo "cpus $(nproc)"; mem
echo "apt: $(tail -1 /tmp/apt.log 2>/dev/null)"
run podman --version
run git --version
echo "snapshot.debian.org through the proxy: $(http_code https://snapshot.debian.org/ 15)"

step "1: upstream runc 1.5.2, checked against the SHA-256 pinned in F0047-S0006"
RUNC_SHA256=599f6f94ff8c5057241eff0d54c3c74f95c34935b6457b33fe545defc61e9488
curl -sSL -m 120 -o /tmp/runc.amd64 https://github.com/opencontainers/runc/releases/download/v1.5.2/runc.amd64; echo "download exit $?"
if echo "$RUNC_SHA256  /tmp/runc.amd64" | sha256sum -c -; then
  install -m 0755 /tmp/runc.amd64 /usr/local/bin/runc
else
  echo "runc checksum does not match: stopping"; echo "PROBE DONE"; exit 0
fi
run /usr/local/bin/runc --version
# S0002's global words, before every subcommand.
P="podman --runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay --storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs"
sh_run "$P info --format 'runtime {{.Host.OCIRuntime.Name}} at {{.Host.OCIRuntime.Path}}, storage {{.Store.GraphDriverName}}, cgroups {{.Host.CgroupsVersion}}'"

step "2: the stage image from a fresh clone of factory-rf (public, no credential)"
s=$(date +%s)
GIT_TERMINAL_PROMPT=0 git clone -q https://github.com/pkrahmer/factory-rf.git /srv/code; echo "clone exit $? after $(since $s)"
REF=$(git -C /srv/code rev-parse --short HEAD); echo "code at $REF"
s=$(date +%s)
$P build --network=host -f vm/Dockerfile --build-arg FACTORY_IMAGE=$REF -t factory-stage:probe /srv/code > /tmp/build.log 2>&1; rc=$?
echo "build exit $rc after $(since $s)"
if [ $rc -ne 0 ]; then
  echo "--- the build's last lines:"; grep -v -i "level=warning" /tmp/build.log | tail -25 | cut -c1-240
  echo "--- the apt lines (a pinned Debian version that left the mirror shows here):"; grep -i -E "version .* was not found|unable to locate|E: " /tmp/build.log | head -10 | cut -c1-240
  mem; echo "PROBE DONE"; exit 0
fi
sh_run "$P image inspect factory-stage:probe --format 'image size {{.Size}} bytes'"
sh_run "$P run --rm --network=host --http-proxy=false --cap-drop=all --security-opt=no-new-privileges factory-stage:probe sh -c 'git --version; make --version | head -1; uv --version; node --version; claude --version; opencode --version; id'"
mem

step "3: make sync and make check in containers of the image, the factory's words (S0002), as the job's root"
mkdir -p /srv/work/home
cp -a /srv/code /srv/work/checkout
NP="localhost,127.0.0.1${PROBE_NO_PROXY:+,$PROBE_NO_PROXY}"
PX=""
[ -n "${PROBE_PROXY:-}" ] && PX="--env http_proxy=$PROBE_PROXY --env https_proxy=$PROBE_PROXY --env HTTP_PROXY=$PROBE_PROXY --env HTTPS_PROXY=$PROBE_PROXY --env no_proxy=$NP --env NO_PROXY=$NP"
RUN="$P run --rm --http-proxy=false --network=host --cap-drop=all --security-opt=no-new-privileges --pids-limit=4096 --memory=4g --env HOME=/work/home $PX --volume /srv/work:/work --workdir /work/checkout"
s=$(date +%s)
timeout 420 $RUN --timeout 420 factory-stage:probe make sync > /tmp/sync.log 2>&1; rc=$?
echo "make sync exit $rc after $(since $s)"; grep -v -i "level=warning" /tmp/sync.log | tail -4 | cut -c1-200
du -sh /srv/work 2>/dev/null
if [ $rc -eq 0 ]; then
  s=$(date +%s)
  # `make -k` with the check's targets one by one: on plain main `secrets` is red by itself (commit ids
  # in two archived acceptance reports, found at home after the first run), so `make check` would stop
  # before `test`, which is the question here. -k runs every target and reports each.
  timeout 840 $RUN --timeout 840 factory-stage:probe make -k lint types layers sast secrets licenses test > /tmp/check.log 2>&1; rc=$?
  echo "make -k (the check's seven targets) exit $rc after $(since $s)"
  echo "--- every target's last line:"; grep -E "^[a-z]+: (green|red)|^check: green|Error|make: \*\*\*" /tmp/check.log | head -20 | cut -c1-200
  echo "--- what detect-secrets flagged (type and place only):"; grep -E "Secret Type|Location" /tmp/check.log | head -12 | cut -c1-200
  echo "--- pytest's summary:"; grep -E "passed|failed|error" /tmp/check.log | tail -3 | cut -c1-240
  echo "--- the failed tests and their E lines (first 60 lines):"
  grep -E "^FAILED|^ERROR|^E  |^tests/.*:[0-9]+: " /tmp/check.log | head -60 | cut -c1-240
  echo "--- the memory the run left:"; mem
fi

step "4: the copy snapshots of S0001 on the synced tree (reset is a copy into an emptied folder)"
echo "tree: $(du -sh /srv/work | cut -f1), files $(find /srv/work -type f | wc -l)"
s=$(date +%s); cp -a /srv/work /srv/base; echo "copy (advance): $(since $s)"
s=$(date +%s); find /srv/work -mindepth 1 -delete; cp -a /srv/base/. /srv/work/; echo "empty and copy back (reset): $(since $s)"
s=$(date +%s); diff -r -q --no-dereference /srv/base /srv/work > /dev/null; rc=$?; echo "diff of the two trees (changed_paths' cost, roughly): $(since $s), exit $rc"
s=$(date +%s); rsync -a --delete /srv/base/ /srv/work/; echo "rsync of an unchanged tree: $(since $s)"
mem

echo; echo "total $(since $t0)"
echo "VERDICT: S0006 can build its image at start if step 2's build exit is 0 (its time is the start's longest part), and the factory's checks run in the job if step 3's targets are green except `secrets` (red on plain main by itself; it should list only the two acceptance reports of F0023 and F0042). Failures of `test` in step 3 that pass on the VM are the root-in-container question of F0047 decision 3 (tests that expect a file to be unreadable or unwritable). A step-2 failure on an apt version is vm/Dockerfile's pinned Debian versions against a mirror that keeps only the current one."
echo "PROBE DONE"
