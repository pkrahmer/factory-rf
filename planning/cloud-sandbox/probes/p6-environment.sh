# P6: what the environment itself offers, without any container engine.
# Resources, kernel features, devices, limits, and a network matrix: what a direct connection reaches,
# what the proxy reaches and what the metadata server hands out. Run with the largest size allowed to
# also show whether the size itself can be had.
setup_env
apt_install curl ca-certificates libcap2-bin procps iproute2 dnsutils util-linux coreutils kmod
echo "=====BEGIN-RESULTS====="
step "platform"
run uname -a
sh_run 'grep -m1 "model name" /proc/cpuinfo; nproc; free -m | sed -n 2p'
sh_run 'cat /proc/self/cgroup | head -3; ls /sys/fs/cgroup | tr "\n" " "'
sh_run 'for f in memory/memory.limit_in_bytes cpu/cpu.cfs_quota_us pids/pids.max; do printf "%s: " $f; cat /sys/fs/cgroup/$f 2>&1; done'
sh_run 'grep -E "^(Seccomp|NoNewPrivs|CapEff|CapBnd)" /proc/self/status; capsh --decode=$(grep CapEff /proc/self/status | cut -f2) 2>&1 | cut -c1-500'
sh_run 'cat /proc/filesystems | tr "\n" " "'
sh_run 'ls /dev | tr "\n" " "'
sh_run 'ulimit -a | head -20'
sh_run 'df -hT / /tmp /dev/shm /run 2>&1'
sh_run 'mount | head -25 | cut -c1-130'
sh_run 'zcat /proc/config.gz 2>/dev/null | grep -E "CONFIG_(BTRFS_FS|XFS_FS|OVERLAY_FS|FUSE_FS|USER_NS|CGROUP_BPF|BLK_DEV_LOOP|MD|DM_THIN|ZFS)=" | head; echo "(config.gz: $(ls -l /proc/config.gz 2>&1 | wc -l))"'
sh_run 'lsmod 2>&1 | head -5; modprobe zfs 2>&1 | head -2; modprobe btrfs 2>&1 | head -2'
step "environment variable NAMES set by the platform (values are not printed)"
sh_run 'env | cut -d= -f1 | grep -E "^(CLOUD_RUN|K_|GOOGLE)" | sort | tr "\n" " "'
step "write throughput to the memory-backed disk (1 GB)"
sh_run 'dd if=/dev/zero of=/tmp/big bs=1M count=1024 conv=fsync 2>&1 | tail -1; rm -f /tmp/big'
step "can a single file or tree exceed the container memory? (writes 5 GB in /tmp; the job's memory is the limit)"
sh_run 'dd if=/dev/zero of=/tmp/big bs=1M count=5120 2>&1 | tail -1; df -h /tmp | tail -1; rm -f /tmp/big'

step "NET1: resolver and direct reachability (no proxy)"
sh_run 'cat /etc/resolv.conf'
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
for h in github.com pypi.org registry.npmjs.org deb.debian.org; do echo "dns $h: $(getent hosts $h | head -1 || echo NONE)"; done
sh_run 'curl -sS -m 6 -o /dev/null -w "direct to 1.1.1.1: %{http_code}\n" https://1.1.1.1 2>&1 | tail -1'
sh_run 'curl -sS -m 6 -o /dev/null -w "direct to 8.8.8.8: %{http_code}\n" https://8.8.8.8 2>&1 | tail -1'
step "NET2: the metadata server from the job itself (status only)"
for p in instance/id project/project-id instance/service-accounts/default/email instance/service-accounts/default/token; do
  printf "%s -> " "$p"; curl -sS -m 5 -o /dev/null -w '%{http_code}\n' -H 'Metadata-Flavor: Google' "http://169.254.169.254/computeMetadata/v1/$p" 2>&1 | tail -1
done
step "NET3: through the proxy: HTTP status per destination"
if [ -n "${PROBE_PROXY:-}" ]; then
  for u in https://github.com https://api.github.com https://raw.githubusercontent.com https://objects.githubusercontent.com https://codeload.github.com \
           https://pypi.org/simple/ https://files.pythonhosted.org/ https://registry.npmjs.org/ https://registry.yarnpkg.com/ \
           https://deb.debian.org/ http://archive.ubuntu.com/ http://security.ubuntu.com/ https://dl-cdn.alpinelinux.org/ \
           https://registry-1.docker.io/v2/ https://auth.docker.io/ https://mirror.gcr.io/v2/ https://quay.io/v2/ https://ghcr.io/v2/ \
           https://download.docker.com/ https://astral.sh/ https://crates.io/ https://static.crates.io/ https://proxy.golang.org/ \
           https://repo.maven.apache.org/maven2/ https://rubygems.org/ https://api.anthropic.com/ https://api.openai.com/ \
           https://opencode.ai/ https://models.dev/ https://nodejs.org/ https://storage.googleapis.com/ https://www.google.com/; do
    printf '%s  ' "$(curl -sS -m 10 -x "$PROBE_PROXY" -o /dev/null -w '%{http_code}' "$u" 2>&1 | tail -1 | cut -c1-60)"; echo "$u"
  done
  step "NET4: does the proxy rewrite TLS? (issuer of three hosts)"
  for h in github.com pypi.org api.anthropic.com; do printf "%s: " $h; curl -sS -m 10 -x "$PROBE_PROXY" -v -o /dev/null https://$h 2>&1 | grep -i 'issuer:' | head -1; done
else echo "no proxy given"; fi
echo; echo "PROBE DONE"
