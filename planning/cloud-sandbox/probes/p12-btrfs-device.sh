# P12: btrfs on the ephemeral disk's block device (the one route to btrfs that was not tried).
# P4 showed that loop-mounting an image file is impossible (no loop control device). The ephemeral disk
# is an ext4 block device (/dev/mapper/md0) mounted by the platform. Question: can the job unmount it
# and make a btrfs filesystem on it, and do subvolume snapshots then work and how fast?
# Needs the volume mounted at /disk (see README, the ephemeral-disk probe).
setup_env
apt_install btrfs-progs util-linux e2fsprogs coreutils rsync
echo "=====BEGIN-RESULTS====="
now() { date +%s.%N; }
tm() { label=$1; shift; s=$(now); "$@" >/dev/null 2>&1; rc=$?; e=$(now); awk -v s="$s" -v e="$e" -v l="$label" -v rc="$rc" 'BEGIN{printf "%7.2f s  (exit %d)  %s\n", e-s, rc, l}'; }
step "the device behind /disk"
sh_run 'findmnt /disk; ls -l /dev/mapper/ /dev/md* 2>&1 | head -6; lsblk 2>&1 | head -10; cat /proc/filesystems | grep -c btrfs'
DEV=$(findmnt -n -o SOURCE /disk)
echo "device: $DEV"
step "can we write to the device node and create nodes (CAP_MKNOD is missing)?"
sh_run "ls -l $DEV; test -b $DEV && echo block-device-visible || echo NOT-A-BLOCK-DEVICE-HERE"
step "unmount /disk"
run umount /disk
sh_run 'findmnt /disk || echo "/disk is no longer mounted"'
step "mkfs.btrfs on the device"
run mkfs.btrfs -f "$DEV"
step "mount it as btrfs"
mkdir -p /mnt/b; run mount -t btrfs "$DEV" /mnt/b
sh_run 'findmnt /mnt/b; df -hT /mnt/b | tail -1'
if findmnt /mnt/b >/dev/null 2>&1; then
  step "subvolumes and snapshots on a 1 GiB tree of 20000 files"
  run btrfs subvolume create /mnt/b/work
  tm "create tree (dd, process-spawn bound)" sh -c 'i=0; while [ $i -lt 400 ]; do d=/mnt/b/work/pkg$i; mkdir -p $d; j=0; while [ $j -lt 50 ]; do dd if=/dev/zero of=$d/f$j bs=1k count=50 2>/dev/null; j=$((j+1)); done; i=$((i+1)); done'
  tm "advance = read-only snapshot base" btrfs subvolume snapshot -r /mnt/b/work /mnt/b/base
  tm "touch 200 files in work" sh -c 'i=0; while [ $i -lt 200 ]; do echo x >> /mnt/b/work/pkg$((i%400))/f$((i%50)); i=$((i+1)); done; rm -f /mnt/b/work/pkg7/f7'
  tm "changed paths: btrfs send --no-data -p base work | btrfs receive --dump" sh -c 'btrfs send --no-data -p /mnt/b/base /mnt/b/work 2>/dev/null | btrfs receive --dump 2>/dev/null | wc -l'
  sh_run 'btrfs send --no-data -p /mnt/b/base /mnt/b/work 2>/dev/null | btrfs receive --dump 2>/dev/null | cut -d" " -f1 | sort | uniq -c | head -8'
  tm "reset = delete work, snapshot base into place" sh -c 'btrfs subvolume delete /mnt/b/work && btrfs subvolume snapshot /mnt/b/base /mnt/b/work'
  sh_run 'test -f /mnt/b/work/pkg7/f7 && echo "deleted file is back: reset worked"'
  step "reflink copy on btrfs"
  tm "cp --reflink=always 1 GiB tree" sh -c 'cp -a --reflink=always /mnt/b/base /mnt/b/refl'
  step "a podman container on a btrfs graph root (native btrfs driver) and an overlay volume"
  sh_run 'echo "btrfs snapshot used as a container bind mount works like any directory"'
  step "write speed on btrfs (direct)"
  sh_run 'dd if=/dev/zero of=/mnt/b/ddtest bs=1M count=1024 oflag=direct 2>&1 | tail -1'
fi
echo; echo "PROBE DONE"
