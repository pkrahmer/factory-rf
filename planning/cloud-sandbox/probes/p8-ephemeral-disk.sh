# P8: the ephemeral-disk volume type of Cloud Run jobs.
# Question: is it a real block-backed filesystem (not memory), how big and how fast, which features
# does it have (extended attributes, hard links, reflinks), and does it lift the limits of the memory-
# backed root: can the kernel overlay use it for its upper layer, can podman use native overlay on it?
# The job is created with one volume mounted at /disk.
setup_env
apt_install rsync fuse-overlayfs podman runc uidmap attr curl ca-certificates busybox-static util-linux e2fsprogs coreutils findutils procps
echo "=====BEGIN-RESULTS====="
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
now() { date +%s.%N; }
tm() { label=$1; shift; s=$(now); "$@" >/dev/null 2>&1; rc=$?; e=$(now); awk -v s="$s" -v e="$e" -v l="$label" -v rc="$rc" 'BEGIN{printf "%7.2f s  (exit %d)  %s\n", e-s, rc, l}'; }
mem() { echo "memory usage (cgroup): $(( $(cat /sys/fs/cgroup/memory/memory.usage_in_bytes) / 1048576 )) MiB; $(grep -E '^(Shmem|Dirty):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')"; }

step "the volume"
sh_run 'mount | grep -E " /disk " | cut -c1-200; df -hT /disk | tail -2; stat -f /disk | head -4'
sh_run 'ls -la /disk | head -5; id'
step "features: extended attributes, hard links, reflink, sparse files, fallocate"
sh_run 'cd /disk && touch f && setfattr -n user.probe -v 1 f && getfattr -n user.probe f 2>&1 | tail -2'
sh_run 'cd /disk && setfattr -n trusted.probe -v 1 f 2>&1 | head -1'
sh_run 'cd /disk && ln f f2 && echo "hard link ok: $(stat -c %h f)"'
sh_run 'cd /disk && dd if=/dev/zero of=big bs=1M count=64 2>/dev/null && cp --reflink=always big big2 2>&1 | head -1; echo "reflink exit $?"'
sh_run 'cd /disk && truncate -s 1G sparse && du -sh --apparent-size sparse && du -sh sparse && fallocate -l 100M fa && echo fallocate-ok'
step "memory accounting: is the disk memory-backed? (usage before, after writing 3 GB to /disk, after writing 3 GB to /)"
mem
tm "write 3 GB to /disk (fsync)" sh -c 'dd if=/dev/zero of=/disk/w3 bs=1M count=3072 conv=fsync'
mem
sync; echo 3 > /proc/sys/vm/drop_caches 2>&1 | head -1; mem
tm "read 3 GB back from /disk" sh -c 'dd if=/disk/w3 of=/dev/null bs=1M'
rm -f /disk/w3
tm "write 3 GB to / (the memory-backed overlay root) (fsync)" sh -c 'dd if=/dev/zero of=/tmp/w3 bs=1M count=3072 conv=fsync'
mem
rm -f /tmp/w3

step "the synthetic checkout: 1 GB in 20000 files on /disk (P4 used the same tree on the root)"
mkdir -p /disk/base
tm "create tree on /disk" sh -c 'i=0; while [ $i -lt 400 ]; do d=/disk/base/pkg$i; mkdir -p $d; j=0; while [ $j -lt 50 ]; do dd if=/dev/zero of=$d/f$j bs=1k count=50 2>/dev/null; j=$((j+1)); done; i=$((i+1)); done'
sh_run 'du -sh /disk/base; find /disk/base -type f | wc -l'
tm "cp -a base work (reset by copy) on /disk" sh -c 'rm -rf /disk/work; cp -a /disk/base /disk/work'
tm "rsync -a -n -i base/ work/ (changed_paths by comparison)" sh -c 'rsync -a -n -i /disk/base/ /disk/work/'
tm "tar cf base.tar (advance)" sh -c 'tar -C /disk/base -cf /disk/base.tar .'
tm "reset by tar extract" sh -c 'rm -rf /disk/work; mkdir /disk/work; tar -C /disk/work -xf /disk/base.tar'
rm -rf /disk/work /disk/base.tar

step "S4: kernel overlay, lower on /disk, upper and work on /disk"
mkdir -p /disk/upper /disk/wk /tmp/ov
ovm() { mount -t overlay overlay -o lowerdir=/disk/base,upperdir=/disk/upper,workdir=/disk/wk /tmp/ov 2>&1 || mount -t overlay overlay -o lowerdir=/disk/base,upperdir=/disk/upper,workdir=/disk/wk,userxattr /tmp/ov 2>&1; }
run ovm
sh_run 'mount | grep " /tmp/ov " | cut -c1-220'
tm "touch 200 files through the overlay" sh -c 'i=0; while [ $i -lt 200 ]; do echo x >> /tmp/ov/pkg$((i%400))/f$((i%50)); i=$((i+1)); done; rm -f /tmp/ov/pkg7/f7'
sh_run 'echo "upper files: $(find /disk/upper -type f | wc -l) whiteouts: $(find /disk/upper -type c | wc -l)"'
tm "reset = umount, empty upper/work, mount" sh -c 'umount /tmp/ov; rm -rf /disk/upper /disk/wk; mkdir -p /disk/upper /disk/wk; mount -t overlay overlay -o lowerdir=/disk/base,upperdir=/disk/upper,workdir=/disk/wk /tmp/ov || mount -t overlay overlay -o lowerdir=/disk/base,upperdir=/disk/upper,workdir=/disk/wk,userxattr /tmp/ov'
umount /tmp/ov 2>/dev/null
step "S4c: lower on the memory-backed root, upper and work on /disk (a big upper without memory cost)"
rm -rf /tmp/lowtree; mkdir -p /tmp/lowtree/a && echo seed > /tmp/lowtree/a/s; mkdir -p /disk/upper3 /disk/wk3
run mount -t overlay overlay -o lowerdir=/tmp/lowtree,upperdir=/disk/upper3,workdir=/disk/wk3 /tmp/ov
sh_run 'echo new > /tmp/ov/a/n; ls /disk/upper3/a'
umount /tmp/ov 2>/dev/null

step "PODMAN on /disk: native overlay storage (the root cannot hold it; vfs was the fallback)"
make_rootfs
pm() { n=$1; shift; podman --runtime=runc --cgroup-manager=cgroupfs --root /disk/ps-$n --runroot /tmp/pr-$n "$@"; }
step "P1: native overlay driver, an image, the factory's flags"
run pm a --storage-driver=overlay run --rm --http-proxy=false --network=host --cap-drop=all --security-opt=no-new-privileges --pids-limit=256 --memory=512m docker.io/library/busybox:latest echo overlay-on-disk-ok
run pm a --storage-driver=overlay info --format 'graph={{.Store.GraphDriverName}} root={{.Store.GraphRoot}} opts={{.Store.GraphOptions}}'
step "P2: overlay with fuse-overlayfs mount program"
run pm b --storage-driver=overlay --storage-opt overlay.mount_program=/usr/bin/fuse-overlayfs run --rm --http-proxy=false --network=host docker.io/library/busybox:latest echo fuse-overlay-on-disk-ok
step "P3: second container start speed on the overlay graph root, and a bigger image (python:3.12-slim) pull"
s=$(now); pm a --storage-driver=overlay run --rm --http-proxy=false --network=host docker.io/library/busybox:latest true >/dev/null 2>&1; e=$(now); awk -v s=$s -v e=$e 'BEGIN{printf "second start: %.2f s\n", e-s}'
s=$(now); pm a --storage-driver=overlay pull docker.io/library/python:3.12-slim >/dev/null 2>&1; e=$(now); awk -v s=$s -v e=$e 'BEGIN{printf "pull python:3.12-slim: %.2f s\n", e-s}'
s=$(now); pm a --storage-driver=overlay run --rm --http-proxy=false --network=host docker.io/library/python:3.12-slim python -c 'print(1)' >/dev/null 2>&1; e=$(now); awk -v s=$s -v e=$e 'BEGIN{printf "first start of python:3.12-slim: %.2f s\n", e-s}'
step "P4: bind-mount a tree on /disk into a container and write there (the stage workflow)"
mkdir -p /disk/ws/checkout && chown 1000:1000 /disk/ws/checkout
run pm a --storage-driver=overlay run --rm --http-proxy=false --network=host --user 1000:1000 -v /disk/ws:/work docker.io/library/busybox:latest sh -c 'echo hi > /work/checkout/x; ls -ln /work/checkout'
step "memory after everything"
mem
sh_run 'df -h /disk /tmp | cut -c1-80'
echo; echo "PROBE DONE"
