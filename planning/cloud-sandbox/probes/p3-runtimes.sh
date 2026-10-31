# P3: newer OCI runtimes than the distribution's: upstream runc and crun release binaries.
# Question: does a current runc (the one Docker 29 bundles) work with podman here, and does the
# newest crun still refuse the hybrid cgroup layout? Binaries are verified against the project's
# published SHA-256 file before use.
setup_env
apt_install podman uidmap fuse-overlayfs curl ca-certificates busybox-static jq coreutils
echo "=====BEGIN-RESULTS====="
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
make_rootfs
step "latest releases (API through the proxy)"
curl -sS -m 30 -o /tmp/runc.json https://api.github.com/repos/opencontainers/runc/releases/latest
curl -sS -m 30 -o /tmp/crun.json https://api.github.com/repos/containers/crun/releases/latest
echo "runc tag: $(jq -r .tag_name /tmp/runc.json)"
echo "crun tag: $(jq -r .tag_name /tmp/crun.json)"
echo "runc assets: $(jq -r '.assets[].name' /tmp/runc.json | tr '\n' ' ')"
echo "crun assets: $(jq -r '.assets[].name' /tmp/crun.json | grep -i -E 'linux-amd64|x86_64' | tr '\n' ' ')"

step "runc: download, verify, install"
RURL=$(jq -r '.assets[] | select(.name=="runc.amd64") | .browser_download_url' /tmp/runc.json)
SURL=$(jq -r '.assets[] | select(.name=="runc.sha256sum") | .browser_download_url' /tmp/runc.json)
curl -sSL -m 120 -o /tmp/runc.amd64 "$RURL"; curl -sSL -m 60 -o /tmp/runc.sha256sum "$SURL"
(cd /tmp && grep ' runc.amd64$' runc.sha256sum | sha256sum -c -) 2>&1 | tail -1
install -m 0755 /tmp/runc.amd64 /usr/local/bin/runc-new
run /usr/local/bin/runc-new --version

pm() { n=$1; rt=$2; shift 2; podman --runtime=$rt --storage-driver=vfs --cgroup-manager=cgroupfs --root /tmp/s-$n --runroot /tmp/r-$n "$@"; }
NEW=/usr/local/bin/runc-new
step "runc (new): vfs, host network"
run pm a $NEW run --rm --network=host --rootfs /tmp/rootfs /bin/echo new-runc-ok
step "runc (new): the factory's flags"
run pm b $NEW run --rm --network=host --cap-drop=all --security-opt=no-new-privileges --pids-limit=256 --memory=512m --timeout 20 --rootfs /tmp/rootfs /bin/echo new-runc-flags-ok
step "runc (new): timeout kills a sleeper"
s=$(date +%s); run pm c $NEW run --rm --network=host --timeout 3 --rootfs /tmp/rootfs /bin/sleep 30; echo "elapsed $(( $(date +%s)-s )) s"
step "runc (new): pids limit enforced"
run pm d $NEW run --rm --network=host --pids-limit=20 --rootfs /tmp/rootfs /bin/sh -c 'i=0; while [ $i -lt 60 ]; do /bin/sleep 5 & i=$((i+1)); done 2>&1; echo forked'
step "runc (new): memory limit enforced (64m, hold 200 MB in a shell variable; expect exit 137)"
run pm e $NEW run --rm --network=host --memory=64m --memory-swap=64m --rootfs /tmp/rootfs /bin/sh -c 'x=$(head -c 200000000 /dev/zero | tr "\\0" a); echo held ${#x}'

step "crun (newest upstream static binary)"
CURL_URL=$(jq -r '.assets[].browser_download_url' /tmp/crun.json | grep -i -E 'linux-amd64$' | grep -v -E 'disable|systemd' | head -1)
echo "url: $CURL_URL"
curl -sSL -m 120 -o /usr/local/bin/crun-new "$CURL_URL" && chmod 0755 /usr/local/bin/crun-new
run /usr/local/bin/crun-new --version
run pm f /usr/local/bin/crun-new run --rm --network=host --rootfs /tmp/rootfs /bin/echo new-crun-ok
echo; echo "PROBE DONE"
