# P2b: follow-up to P2. (1) Can a bridge container get outbound access once IP forwarding is on?
# (2) Can the metadata server's HTTP port be blocked for containers, with a correctly written nft rule,
# without breaking DNS and the proxy? (3) What does the platform's own firewall allow, in full?
setup_env
apt_install podman runc netavark nftables iptables conmon uidmap curl ca-certificates busybox-static iproute2 util-linux dnsutils
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

step "F0: the platform's own firewall, complete (LINES_MAX raised)"
LINES_MAX=120 run nft list ruleset
LINES_MAX=60 run iptables-save
step "F0b: routing and interfaces"
sh_run 'ip addr; ip route; ip rule 2>&1 | head -5'
step "F0c: sysctls that matter for networking"
sh_run 'sysctl net.ipv4.ip_forward net.ipv4.conf.all.forwarding net.bridge.bridge-nf-call-iptables 2>&1 | head -5'

step "B0: bridge container to the proxy by IP, forwarding OFF (baseline)"
run pm B0 $RUN -e http_proxy=http://$PROXY_IP:$PROXY_PORT -e https_proxy=http://$PROXY_IP:$PROXY_PORT $BB sh -c 'wget -q -T 8 -O /dev/null https://github.com && echo bridge-github-via-proxy-ok'
step "B1: turn forwarding on, then the same"
run sh -c 'echo 1 > /proc/sys/net/ipv4/ip_forward; cat /proc/sys/net/ipv4/ip_forward'
run pm B1 $RUN -e http_proxy=http://$PROXY_IP:$PROXY_PORT -e https_proxy=http://$PROXY_IP:$PROXY_PORT $BB sh -c 'wget -q -T 8 -O /dev/null https://github.com && echo bridge-github-via-proxy-ok'
step "B2: a bridge container to a non-proxy destination (direct egress is expected to fail: no route out except the connector)"
run pm B2 $RUN $BB sh -c 'wget -q -T 6 -O /dev/null http://1.1.1.1 && echo direct-ok || echo direct-failed'
step "B3: the nft state after podman created its network (netavark's tables)"
LINES_MAX=60 run nft list tables

step "M1: baseline from a host-network container and a bridge container"
run pm M1 $RUN --network=host $BB sh -c "$META"
run pm M1b $RUN $BB sh -c "$META"
step "M2: our own rule, loaded from a file (chain names must not be nft keywords)"
cat > /tmp/probe.nft <<'EOF'
table inet probeblock {
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
run nft -f /tmp/probe.nft
run nft list table inet probeblock
step "M2a: host-network container after the rule"
run pm M2a $RUN --network=host $BB sh -c "$META"
step "M2b: bridge container after the rule"
run pm M2b $RUN $BB sh -c "$META"
step "M2c: by hostname"
run pm M2c $RUN --network=host $BB sh -c 'wget -q -T 5 -O /dev/null --header "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/id && echo metadata-REACHABLE || echo metadata-blocked'
step "M2d: https to the metadata address (port 443 is in the platform's own list too)"
run pm M2d $RUN --network=host $BB sh -c 'wget -q -T 5 -O /dev/null --no-check-certificate --header "Metadata-Flavor: Google" https://169.254.169.254/computeMetadata/v1/instance/id && echo https-REACHABLE || echo https-blocked-or-failed'
step "M2e: the job itself: DNS and proxy still fine; metadata refused"
sh_run 'getent hosts github.com | head -1; curl -sS -m 10 -x "$PROBE_PROXY" -o /dev/null -w "via proxy: %{http_code}\n" https://github.com; curl -sS -m 5 -o /dev/null -w "metadata: %{http_code}\n" -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/id 2>&1 | tail -1'
echo; echo "PROBE DONE"
