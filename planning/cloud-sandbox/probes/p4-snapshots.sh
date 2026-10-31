# P4: snapshot mechanisms without ZFS.
# Question: what can replace "snapshot the dataset, roll back, list what changed"? Tested on a
# synthetic checkout of about 1 GB in 20000 files (a source tree with a virtualenv looks like this).
# Each mechanism is timed for the three operations the factory's Snapshots interface has:
# reset (back to the base), advance (the base becomes the current state), changed_paths (the diff).
setup_env
apt_install rsync fuse-overlayfs e2fsprogs xfsprogs btrfs-progs util-linux coreutils findutils procps kmod attr
echo "=====BEGIN-RESULTS====="
t() { s=$(date +%s.%N); "$@" >/dev/null 2>&1; rc=$?; e=$(date +%s.%N); echo "$(echo "$e - $s" | bc 2>/dev/null || awk "BEGIN{print $e-$s}") s  (exit $rc)  $*"; }
now() { date +%s.%N; }
tm() { label=$1; shift; s=$(now); "$@" >/dev/null 2>&1; rc=$?; e=$(now); awk -v s="$s" -v e="$e" -v l="$label" -v rc="$rc" 'BEGIN{printf "%7.2f s  (exit %d)  %s\n", e-s, rc, l}'; }

step "what the kernel offers"
sh_run 'cat /proc/filesystems | tr "\n\t" "  " | fold -w 150'
sh_run 'ls -l /dev/loop-control /dev/loop0 2>&1 | head -3'
sh_run 'df -hT /tmp | tail -1; free -m | sed -n 2p'
sh_run 'grep -E "^(CapEff|NoNewPrivs)" /proc/self/status'

step "the synthetic checkout: 1 GB, 20000 files, 400 directories"
mkdir -p /tmp/base
tm "create tree" sh -c 'i=0; while [ $i -lt 400 ]; do d=/tmp/base/pkg$i; mkdir -p $d; j=0; while [ $j -lt 50 ]; do dd if=/dev/zero of=$d/f$j bs=1k count=50 2>/dev/null; j=$((j+1)); done; i=$((i+1)); done'
sh_run 'du -sh /tmp/base; find /tmp/base -type f | wc -l'

step "S1: plain copy (cp -a)"
tm "reset  = rm -rf work; cp -a base work" sh -c 'rm -rf /tmp/work; cp -a /tmp/base /tmp/work'
tm "touch 200 files in work" sh -c 'i=0; while [ $i -lt 200 ]; do echo x >> /tmp/work/pkg$((i%400))/f$((i%50)); i=$((i+1)); done'
tm "changed_paths = diff -rq base work" sh -c 'diff -rq /tmp/base /tmp/work'
tm "changed_paths = rsync -a -n -i base/ work/" sh -c 'rsync -a -n -i /tmp/base/ /tmp/work/'
tm "advance = rsync -a --delete work/ base/" sh -c 'rsync -a --delete /tmp/work/ /tmp/base/'

step "S2: copy with hard links (cp -al): shares data, so writes in place leak into the base"
tm "reset  = rm -rf work; cp -al base work" sh -c 'rm -rf /tmp/work; cp -al /tmp/base /tmp/work'
sh_run 'echo leak >> /tmp/work/pkg1/f1; if cmp -s /tmp/base/pkg1/f1 /tmp/work/pkg1/f1; then echo "BASE CHANGED BY A WRITE IN WORK: hard links share the file, so this is no snapshot"; else echo "base unchanged: the copy was not a hard link"; fi'
tm "rsync --link-dest style: copy-on-write only by replacing files" sh -c 'rm -rf /tmp/work2; rsync -a --link-dest=/tmp/base/ /tmp/base/ /tmp/work2/'

step "S3: reflink copy"
run sh -c 'cp -a --reflink=always /tmp/base /tmp/refl 2>&1 | head -2'

step "S4: kernel overlayfs as root, upper and work directories on a tmpfs (an overlay root cannot be an upper)"
mkdir -p /mnt/up /tmp/ov; mount -t tmpfs -o size=4g tmpfs /mnt/up && mkdir -p /mnt/up/upper /mnt/up/work
ovmount() { mount -t overlay overlay -o lowerdir=/tmp/base,upperdir=/mnt/up/upper,workdir=/mnt/up/work /tmp/ov 2>&1 || mount -t overlay overlay -o lowerdir=/tmp/base,upperdir=/mnt/up/upper,workdir=/mnt/up/work,userxattr /tmp/ov 2>&1; }
run ovmount
sh_run 'mount | grep " /tmp/ov " | cut -c1-200'
tm "touch 200 files through the overlay (copy-up of 200 x 50 KB)" sh -c 'i=0; while [ $i -lt 200 ]; do echo x >> /tmp/ov/pkg$((i%400))/f$((i%50)); i=$((i+1)); done; rm -f /tmp/ov/pkg7/f7; mkdir -p /tmp/ov/new; echo n > /tmp/ov/new/a'
tm "changed_paths = find upper (whiteouts are char devices 0/0)" sh -c 'find /mnt/up/upper -type f -o -type c | wc -l'
sh_run 'echo "files: $(find /mnt/up/upper -type f | wc -l)  whiteouts: $(find /mnt/up/upper -type c | wc -l)  dirs: $(find /mnt/up/upper -type d | wc -l)"; getfattr -d -m - /mnt/up/upper/new 2>&1 | head -3'
sh_run 'if cmp -s /tmp/base/pkg1/f1 /tmp/ov/pkg1/f1; then echo "file identical through overlay"; else echo "file differs through overlay (base below stays pristine)"; fi; test -f /tmp/base/pkg7/f7 && echo "base still has the deleted file" '
tm "advance = apply upper to base (delete whiteouts, rsync the rest)" sh -c 'cd /mnt/up/upper && find . -type c | while read p; do rm -rf "/tmp/base/$p"; done; rsync -a --exclude-from=/dev/null --no-specials --no-devices /mnt/up/upper/ /tmp/base/'
tm "reset = umount, empty upper/work, mount again" sh -c 'umount /tmp/ov; rm -rf /mnt/up/upper /mnt/up/work; mkdir -p /mnt/up/upper /mnt/up/work; mount -t overlay overlay -o lowerdir=/tmp/base,upperdir=/mnt/up/upper,workdir=/mnt/up/work /tmp/ov || mount -t overlay overlay -o lowerdir=/tmp/base,upperdir=/mnt/up/upper,workdir=/mnt/up/work,userxattr /tmp/ov'
sh_run 'find /mnt/up/upper | wc -l; ls /tmp/ov | head -2'
umount /tmp/ov 2>/dev/null
step "S4b: overlay with the lower tree ALSO on a tmpfs, and a containerised use: a podman container working on the overlay mount"
mkdir -p /mnt/low && mount -t tmpfs -o size=3g tmpfs /mnt/low && cp -a /tmp/base/. /mnt/low/ && echo "base copied onto tmpfs"
mkdir -p /mnt/up/upper2 /mnt/up/work2
run mount -t overlay overlay -o lowerdir=/mnt/low,upperdir=/mnt/up/upper2,workdir=/mnt/up/work2 /tmp/ov
sh_run 'echo ok > /tmp/ov/pkg0/newfile; ls /mnt/up/upper2/pkg0'
umount /tmp/ov 2>/dev/null

step "S5: fuse-overlayfs"
rm -rf /tmp/up /tmp/wk /tmp/ov; mkdir -p /tmp/up /tmp/wk /tmp/ov
run fuse-overlayfs -o lowerdir=/tmp/base,upperdir=/tmp/up,workdir=/tmp/wk /tmp/ov
tm "touch 200 files through fuse-overlayfs" sh -c 'i=0; while [ $i -lt 200 ]; do echo x >> /tmp/ov/pkg$((i%400))/f$((i%50)); i=$((i+1)); done'
sh_run 'find /tmp/up -type f | wc -l'
run fusermount3 -u /tmp/ov

step "S6: a loop-mounted filesystem image with its own snapshot facilities"
for fs in ext4 xfs btrfs; do
  rm -f /tmp/img.$fs; truncate -s 3G /tmp/img.$fs 2>&1
  case $fs in ext4) mkfs.ext4 -q -F /tmp/img.$fs >/dev/null 2>&1;; xfs) mkfs.xfs -q -f /tmp/img.$fs >/dev/null 2>&1;; btrfs) mkfs.btrfs -q -f /tmp/img.$fs >/dev/null 2>&1;; esac
  mkdir -p /tmp/m.$fs
  run mount -o loop /tmp/img.$fs /tmp/m.$fs
  sh_run "mount | grep /tmp/m.$fs | head -1"
  umount /tmp/m.$fs 2>/dev/null
done
step "S7: btrfs subvolume snapshot, if btrfs mounted"
if grep -q btrfs /proc/filesystems; then
  mount -o loop /tmp/img.btrfs /tmp/m.btrfs 2>&1 | head -2
  run btrfs subvolume create /tmp/m.btrfs/work
  tm "copy 1 GB into the subvolume" cp -a /tmp/base/. /tmp/m.btrfs/work/
  tm "advance = read-only snapshot" btrfs subvolume snapshot -r /tmp/m.btrfs/work /tmp/m.btrfs/base
  tm "reset = delete work, snapshot base into place" sh -c 'btrfs subvolume delete /tmp/m.btrfs/work && btrfs subvolume snapshot /tmp/m.btrfs/base /tmp/m.btrfs/work'
  umount /tmp/m.btrfs 2>/dev/null
else echo "btrfs is not in /proc/filesystems: not available in this kernel"; fi

step "S8: tar as base (pack once, unpack to reset)"
tm "advance = tar cf base.tar" sh -c 'tar -C /tmp/base -cf /tmp/base.tar .'
tm "reset = rm -rf work; tar xf" sh -c 'rm -rf /tmp/work; mkdir /tmp/work; tar -C /tmp/work -xf /tmp/base.tar'
sh_run 'ls -lh /tmp/base.tar | cut -c1-60'
step "memory and disk afterwards"
sh_run 'free -m | sed -n 2p; df -h /tmp | tail -1'
echo; echo "PROBE DONE"
