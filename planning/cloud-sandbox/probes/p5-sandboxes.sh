# P5: sandboxes that are not container engines.
# Question: if no OCI engine is wanted, which lightweight isolation works for "run the agent's command
# so that it can write only to one place, cannot see the credentials and can be killed whole"?
setup_env
apt_install util-linux libcap2-bin libcap2 procps curl ca-certificates coreutils iproute2 attr
apt_install bubblewrap
apt-get install -y -qq --no-install-recommends nsjail >/tmp/nsjail.log 2>&1; echo "nsjail install exit $? (a missing package is a result)"; tail -2 /tmp/nsjail.log | cut -c1-200
echo "=====BEGIN-RESULTS====="
step "kernel facilities"
sh_run 'cat /sys/kernel/security/lsm 2>&1; echo; grep -E "^(Seccomp|NoNewPrivs|CapEff|CapBnd)" /proc/self/status'
sh_run 'capsh --decode=$(grep CapEff /proc/self/status | cut -f2) 2>&1 | cut -c1-500'
sh_run 'cat /proc/sys/user/max_user_namespaces /proc/sys/kernel/unprivileged_userns_clone 2>&1'
sh_run 'ls /proc/self/ns | tr "\n" " "'
step "U1: unshare --pid --mount --fork (pid namespace: killing init kills the tree)"
run unshare --pid --mount-proc --fork sh -c 'echo "pid inside: $$"; ps -e | wc -l'
step "U2: user namespace as root (maps root to root)"
run unshare --user --map-root-user sh -c 'id; cat /proc/self/uid_map'
step "U3: network namespace (no interfaces: no way out)"
run unshare --net sh -c 'ip link 2>&1 | head -3; curl -sS -m 3 -o /dev/null https://github.com 2>&1 | head -1'
step "B1: bubblewrap, read-only root, one writable directory"
mkdir -p /tmp/w1; echo secret > /tmp/outside.txt
run bwrap --unshare-all --die-with-parent --ro-bind / / --bind /tmp/w1 /tmp/w1 --dev /dev --proc /proc sh -c 'echo ok > /tmp/w1/a && echo "write to w1: ok"; echo no > /etc/x 2>&1 || echo "write to /etc refused"; cat /tmp/outside.txt'
step "B2: bubblewrap with a tmpfs over a credential directory (hide it)"
mkdir -p /root/.creds; echo token > /root/.creds/t
run bwrap --unshare-all --die-with-parent --ro-bind / / --tmpfs /root --bind /tmp/w1 /tmp/w1 --dev /dev --proc /proc sh -c 'ls -la /root; cat /root/.creds/t 2>&1 || echo "credentials hidden"'
step "B3: bubblewrap, network kept (host network) and the proxy still usable"
run bwrap --unshare-pid --die-with-parent --ro-bind / / --bind /tmp/w1 /tmp/w1 --dev /dev --proc /proc curl -sS -m 10 -o /dev/null -w '%{http_code}\n' -x "$PROBE_PROXY" https://github.com
step "B4: bubblewrap, kill the tree at a time limit"
s=$(date +%s); run timeout 3 bwrap --unshare-pid --die-with-parent --ro-bind / / --dev /dev --proc /proc sh -c 'sleep 30 & sleep 30'; echo "elapsed $(( $(date +%s)-s )) s"; run sh -c 'ps -e | grep -c "[s]leep 30"'
step "B5: bubblewrap, nested user namespace with a non-root uid inside"
run bwrap --unshare-user --uid 1000 --gid 1000 --ro-bind / / --bind /tmp/w1 /tmp/w1 --dev /dev --proc /proc sh -c 'id; echo u > /tmp/w1/u; ls -ln /tmp/w1/u'
step "J1: nsjail"
run nsjail --version
run nsjail -Mo --user 0 --group 0 --disable_clone_newuser --chroot / --rlimit_as soft --time_limit 5 -- /bin/sh -c 'echo nsjail-ok'
step "L1: cgroup v1 limits written by hand (the factory's pids/memory limits without an engine)"
sh_run 'ls /sys/fs/cgroup/pids /sys/fs/cgroup/memory 2>&1 | head -6; mkdir /sys/fs/cgroup/pids/probe 2>&1 && echo "created pids cgroup"; echo 20 > /sys/fs/cgroup/pids/probe/pids.max 2>&1 && echo "pids.max set"; cat /sys/fs/cgroup/pids/probe/pids.max 2>&1'
sh_run 'mkdir /sys/fs/cgroup/memory/probe 2>&1 && echo "created memory cgroup"; echo 67108864 > /sys/fs/cgroup/memory/probe/memory.limit_in_bytes 2>&1 && echo "memory limit set"; cat /sys/fs/cgroup/memory/probe/memory.limit_in_bytes 2>&1'
sh_run 'echo $$ > /sys/fs/cgroup/pids/probe/cgroup.procs 2>&1 && echo "moved self into pids cgroup"; i=0; while [ $i -lt 40 ]; do sleep 1 & i=$((i+1)); done 2>&1 | tail -1; echo done'
step "L2: landlock available?"
sh_run 'dmesg 2>&1 | grep -i landlock | head -2; ls /sys/kernel/security/ 2>&1 | head'
echo; echo "PROBE DONE"
