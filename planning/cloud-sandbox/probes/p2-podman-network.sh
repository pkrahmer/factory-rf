# P2: podman 5 on Debian trixie: network modes, the metadata server's exposure, limits, build, users.
# Question: which network modes work without /dev/net/tun, can the default bridge reach the outside,
# can a container reach the metadata server (it would hand out the job's credentials), can that be
# blocked without breaking DNS (the resolver IS the metadata address), and do the resource limits bite?
# Version 2: version 1 showed that blackholing the metadata address breaks DNS, that podman forwards
# the job's proxy variables into containers (so every test needs --http-proxy=false) and that the nft
# rule must be loaded from a file.
setup_env
apt_install podman runc crun netavark nftables iptables passt slirp4netns conmon uidmap fuse-overlayfs curl ca-certificates busybox-static iproute2 util-linux dnsutils
echo "=====BEGIN-RESULTS====="
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
make_rootfs
pm() { n=$1; shift; podman --runtime=runc --storage-driver=vfs --cgroup-manager=cgroupfs --root /tmp/s-$n --runroot /tmp/r-$n "$@"; }
RUN="run --rm --http-proxy=false"
BB=docker.io/library/busybox:latest
PROXY_HOST=$(echo "$PROBE_PROXY" | sed -e 's#^[a-z]*://##' -e 's#:[0-9]*$##')
PROXY_PORT=$(echo "$PROBE_PROXY" | sed -e 's#.*:##')
PROXY_IP=$(getent hosts "$PROXY_HOST" | awk '{print $1; exit}')
META='wget -q -T 5 -O /dev/null --header "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/id && echo metadata-REACHABLE || echo metadata-blocked'

step "versions and device nodes"
run podman --version
sh_run 'ls -l /dev/net/tun /dev/fuse /dev/kvm 2>&1; echo "ip_forward: $(cat /proc/sys/net/ipv4/ip_forward)"; cat /etc/resolv.conf'
step "N1: --network=host"
run pm N1 $RUN --network=host --rootfs /tmp/rootfs /bin/echo N1-ok
step "N2: --network=none"
run pm N2 $RUN --network=none --rootfs /tmp/rootfs /bin/echo N2-ok
step "N3: default bridge (netavark with nftables)"
run pm N3 $RUN --rootfs /tmp/rootfs /bin/echo N3-bridge-ok
step "N4: bridge container to the proxy by IP (does the bridge have outbound NAT here?)"
run pm N4 $RUN -e http_proxy=http://$PROXY_IP:$PROXY_PORT -e https_proxy=http://$PROXY_IP:$PROXY_PORT $BB sh -c 'wget -q -T 8 -O /dev/null https://github.com && echo bridge-github-via-proxy-ok'
step "N4b: bridge container, name resolution inside (resolver reachable from the bridge?)"
run pm N4b $RUN $BB sh -c 'nslookup github.com 2>&1 | tail -3'
step "N5: slirp4netns"
run pm N5 $RUN --network=slirp4netns --rootfs /tmp/rootfs /bin/echo N5-ok
step "N6: pasta"
run pm N6 $RUN --network=pasta --rootfs /tmp/rootfs /bin/echo N6-ok

step "M0: the job itself: DNS works, metadata HTTP status"
sh_run 'getent hosts github.com | head -1; curl -sS -m 5 -o /dev/null -w "metadata http: %{http_code}\n" -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/id'
step "M1: metadata from a --network=host container (no proxy variables inside)"
run pm M1 $RUN --network=host $BB sh -c "$META"
step "M2: metadata from a bridge container"
run pm M2 $RUN $BB sh -c "$META"
step "M3: block only TCP port 80 to the metadata address (DNS on port 53 stays), in output and forward"
cat > /tmp/probe.nft <<'EOF'
table inet probe {
  chain out { type filter hook output priority 0; policy accept; ip daddr 169.254.169.254 tcp dport 80 reject; }
  chain fwd { type filter hook forward priority 0; policy accept; ip daddr 169.254.169.254 tcp dport 80 reject; }
}
EOF
run nft -f /tmp/probe.nft
run nft list ruleset
step "M3a: host-network container after the rule"
run pm M3a $RUN --network=host $BB sh -c "$META"
step "M3b: bridge container after the rule"
run pm M3b $RUN $BB sh -c "$META"
step "M3c: the job itself after the rule: metadata refused, DNS still works, proxy still works"
sh_run 'curl -sS -m 5 -o /dev/null -w "metadata http: %{http_code}\n" -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/id 2>&1 | tail -1; getent hosts github.com | head -1; curl -sS -m 10 -x "$PROBE_PROXY" -o /dev/null -w "via proxy: %{http_code}\n" https://github.com'
step "M3d: the metadata hostname instead of the address (metadata.google.internal)"
run pm M3d $RUN --network=host $BB sh -c 'wget -q -T 5 -O /dev/null --header "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/id && echo metadata-REACHABLE || echo metadata-blocked'

step "MEM1: hold 300 MB in a shell variable under --memory=128m (expect killed, exit 137)"
run pm Q1 $RUN --network=host --memory=128m --memory-swap=128m $BB sh -c 'x=$(head -c 300000000 /dev/zero | tr "\0" a); echo held ${#x}'
step "MEM2: the same without a limit (expect it to succeed)"
run pm Q2 $RUN --network=host $BB sh -c 'x=$(head -c 300000000 /dev/zero | tr "\0" a); echo held ${#x}'
step "MEM3: the limits as the container sees them"
run pm Q3 $RUN --network=host --memory=128m --cpus=0.5 $BB sh -c 'cat /sys/fs/cgroup/memory/memory.limit_in_bytes /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>&1'
step "CPU1: --cpus=0.5 throttles (busy loop 4 s; compare iteration counts)"
run pm Q4 $RUN --network=host --cpus=0.5 $BB sh -c 'i=0; end=$(( $(date +%s)+4 )); while [ $(date +%s) -lt $end ]; do i=$((i+1)); done; echo iterations $i'
run pm Q5 $RUN --network=host $BB sh -c 'i=0; end=$(( $(date +%s)+4 )); while [ $(date +%s) -lt $end ]; do i=$((i+1)); done; echo iterations $i'
step "TIME1: a container whose process ignores the time limit and spawns children; podman --timeout kills the whole tree?"
run pm T1 $RUN --network=host --timeout 3 $BB sh -c 'sleep 60 & sleep 60 & sleep 60'
run sh -c 'ps -e | grep -c "[s]leep 60"'
step "BUILD1: podman build with a RUN step (docker build failed here on capabilities)"
mkdir -p /tmp/bt && printf 'FROM docker.io/library/busybox:latest\nRUN echo built > /built\n' > /tmp/bt/Containerfile
run pm B1 build --network=host -t probe-built /tmp/bt
step "UID1: a numeric user writing to a bind mount that belongs to that user (the keep-id replacement)"
mkdir -p /tmp/work && chown 1000:1000 /tmp/work
run pm U1 $RUN --network=host --user 1000:1000 -v /tmp/work:/work $BB sh -c 'id; echo u > /work/u; ls -ln /work/u'
run ls -ln /tmp/work/u
step "UID2: the same bind mount owned by root: the numeric user is refused (so ownership must match)"
mkdir -p /tmp/work2
run pm U2 $RUN --network=host --user 1000:1000 -v /tmp/work2:/work $BB sh -c 'echo u > /work/u 2>&1; echo "exit $?"'
step "UID3: --userns=keep-id as root (what the factory sets for rootless)"
run pm U3 $RUN --network=host --userns=keep-id --rootfs /tmp/rootfs /bin/id
echo; echo "PROBE DONE"
