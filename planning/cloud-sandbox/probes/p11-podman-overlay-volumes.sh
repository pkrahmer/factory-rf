# P11: podman's overlay volumes (-v SRC:DST:O) as the snapshot mechanism.
# Question: can a container work on a base directory through an overlay volume, so that the base is
# never written, the changes land in an upper directory we can keep (the "take" reads it) or discard
# (the "reset"), with the factory's flags, with several containers at once, and with a deleted file,
# a renamed directory, a numeric user, and a 1 GiB / 20000-file base?
setup_env
apt_install podman runc netavark nftables curl ca-certificates busybox-static util-linux rsync attr
echo "=====BEGIN-RESULTS====="
export PODMAN_IGNORE_CGROUPSV1_WARNING=1
make_rootfs
now() { date +%s.%N; }
tm() { label=$1; shift; s=$(now); "$@" >/dev/null 2>&1; rc=$?; e=$(now); awk -v s="$s" -v e="$e" -v l="$label" -v rc="$rc" 'BEGIN{printf "%7.2f s  (exit %d)  %s\n", e-s, rc, l}'; }
BB=docker.io/library/busybox:latest
mkdir -p /mnt/t && mount -t tmpfs -o size=6g tmpfs /mnt/t && echo "tmpfs at /mnt/t"
# graph roots: (a) on the memory-backed root, (b) on a tmpfs
pa() { podman --runtime=runc --storage-driver=overlay --cgroup-manager=cgroupfs --root /tmp/ga --runroot /tmp/ra "$@"; }
pv() { podman --runtime=runc --storage-driver=vfs --cgroup-manager=cgroupfs --root /tmp/gv --runroot /tmp/rv "$@"; }
pt() { podman --runtime=runc --storage-driver=overlay --cgroup-manager=cgroupfs --root /mnt/t/g --runroot /mnt/t/r "$@"; }
RUN="run --rm --http-proxy=false --network=host"

step "setup: a small base tree"
mkdir -p /tmp/base/dir1 /tmp/base/dir2 && echo one > /tmp/base/dir1/a && echo two > /tmp/base/dir2/b && echo top > /tmp/base/top.txt && chown -R 1000:1000 /tmp/base
sh_run 'find /tmp/base | sort'

step "O1: default upper (podman chooses), graph root on the memory-backed root, vfs driver"
run pv $RUN -v /tmp/base:/work:O $BB sh -c 'echo new > /work/n; rm /work/top.txt; ls /work'
sh_run 'ls /tmp/base; test -f /tmp/base/n && echo "BASE WAS WRITTEN" || echo "base untouched"'
step "O2: the same with overlay graph driver on the memory-backed root (expected to hit the upperdir limit)"
run pa $RUN -v /tmp/base:/work:O $BB sh -c 'echo new > /work/n; ls /work'
step "O3: overlay graph driver on a tmpfs graph root, default upper"
run pt $RUN -v /tmp/base:/work:O $BB sh -c 'echo new > /work/n; rm /work/top.txt; ls /work'
sh_run 'ls /tmp/base'

step "O4: explicit upperdir and workdir on a tmpfs, kept after the container ends"
rm -rf /mnt/t/u1 /mnt/t/w1; mkdir -p /mnt/t/u1 /mnt/t/w1
run pv $RUN -v /tmp/base:/work:O,upperdir=/mnt/t/u1,workdir=/mnt/t/w1 $BB sh -c 'echo new > /work/n; echo changed > /work/dir1/a; rm /work/top.txt; mkdir /work/d3; echo x > /work/d3/f'
sh_run 'echo "--- upper:"; find /mnt/t/u1 | sort; echo "--- types:"; find /mnt/t/u1 -type c | head -3; echo "base still:"; find /tmp/base -type f | sort; cat /tmp/base/dir1/a'
step "O5: the take: list changes from the upper dir (files, whiteouts as character devices, opaque dirs)"
sh_run 'cd /mnt/t/u1; find . -type f | sort | sed "s/^/added-or-modified: /"; find . -type c | sed "s/^/deleted: /"; for d in $(find . -type d); do v=$(getfattr -n trusted.overlay.opaque --only-values $d 2>/dev/null); [ -n "$v" ] && echo "opaque: $d"; done; echo done'
step "O6: reset = discard the upper; run again: clean view of the base?"
rm -rf /mnt/t/u1 /mnt/t/w1; mkdir -p /mnt/t/u1 /mnt/t/w1
run pv $RUN -v /tmp/base:/work:O,upperdir=/mnt/t/u1,workdir=/mnt/t/w1 $BB sh -c 'ls /work; cat /work/top.txt'

step "O7: the factory's flags (cap-drop=all, no-new-privileges, pids, memory) with an overlay volume"
rm -rf /mnt/t/u2 /mnt/t/w2; mkdir -p /mnt/t/u2 /mnt/t/w2
run pv $RUN --cap-drop=all --security-opt=no-new-privileges --pids-limit=256 --memory=512m --user 1000:1000 -v /tmp/base:/work:O,upperdir=/mnt/t/u2,workdir=/mnt/t/w2 $BB sh -c 'id; echo u > /work/u; echo m >> /work/dir1/a; ls -ln /work/u'
sh_run 'ls -ln /mnt/t/u2 /mnt/t/u2/dir1 2>&1 | head -8'
step "O8: a read-only lower with an overlay on top (the base mounted :ro,O is refused or fine?)"
rm -rf /mnt/t/u3 /mnt/t/w3; mkdir -p /mnt/t/u3 /mnt/t/w3
run pv $RUN -v /tmp/base:/work:ro,O,upperdir=/mnt/t/u3,workdir=/mnt/t/w3 $BB sh -c 'echo x > /work/x; echo "write exit $?"'
step "O9: two containers at the same time, same base, different uppers"
rm -rf /mnt/t/ua /mnt/t/wa /mnt/t/ub /mnt/t/wb; mkdir -p /mnt/t/ua /mnt/t/wa /mnt/t/ub /mnt/t/wb
( pv $RUN -v /tmp/base:/work:O,upperdir=/mnt/t/ua,workdir=/mnt/t/wa $BB sh -c 'echo A > /work/who; sleep 3; cat /work/who' > /tmp/ca.out 2>&1 ) &
( pt $RUN -v /tmp/base:/work:O,upperdir=/mnt/t/ub,workdir=/mnt/t/wb $BB sh -c 'echo B > /work/who; sleep 3; cat /work/who' > /tmp/cb.out 2>&1 ) &
wait; echo "A sees: $(cat /tmp/ca.out | tail -1); B sees: $(cat /tmp/cb.out | tail -1)"
step "O10: a directory rename inside the overlay (the redirect_dir / EXDEV question)"
rm -rf /mnt/t/u4 /mnt/t/w4; mkdir -p /mnt/t/u4 /mnt/t/w4
run pv $RUN -v /tmp/base:/work:O,upperdir=/mnt/t/u4,workdir=/mnt/t/w4 $BB sh -c 'mv /work/dir1 /work/dir1b; echo "mv exit $?"; ls /work /work/dir1b'
sh_run 'find /mnt/t/u4 | sort | head -12'
step "O11: the same rename with a tool that falls back (busybox mv copies on EXDEV? cp -r then rm)"
rm -rf /mnt/t/u5 /mnt/t/w5; mkdir -p /mnt/t/u5 /mnt/t/w5
run pv $RUN -v /tmp/base:/work:O,upperdir=/mnt/t/u5,workdir=/mnt/t/w5 $BB sh -c 'cp -a /work/dir2 /work/dir2b && rm -rf /work/dir2; ls /work'

step "O12: a 1 GiB, 20000-file base: time for the mount at container start, writes and the reset"
mkdir -p /mnt/t/big
i=0; while [ $i -lt 400 ]; do d=/mnt/t/big/pkg$i; mkdir -p $d; j=0; while [ $j -lt 50 ]; do dd if=/dev/zero of=$d/f$j bs=1k count=50 2>/dev/null; j=$((j+1)); done; i=$((i+1)); done
sh_run 'du -sh /mnt/t/big | tail -1; find /mnt/t/big -type f | wc -l'
rm -rf /mnt/t/ub2 /mnt/t/wb2; mkdir -p /mnt/t/ub2 /mnt/t/wb2
s=$(now); pv $RUN -v /mnt/t/big:/work:O,upperdir=/mnt/t/ub2,workdir=/mnt/t/wb2 $BB true >/dev/null 2>&1; e=$(now); awk -v s=$s -v e=$e 'BEGIN{printf "container start with a 20000-file lower: %.2f s\n", e-s}'
s=$(now); pv $RUN -v /mnt/t/big:/work:O,upperdir=/mnt/t/ub2,workdir=/mnt/t/wb2 $BB sh -c 'i=0; while [ $i -lt 200 ]; do echo x >> /work/pkg$((i%400))/f$((i%50)); i=$((i+1)); done; rm -f /work/pkg7/f7' >/dev/null 2>&1; e=$(now); awk -v s=$s -v e=$e 'BEGIN{printf "200 appends (copy-up) + 1 delete: %.2f s\n", e-s}'
sh_run 'echo "upper: files $(find /mnt/t/ub2 -type f | wc -l), whiteouts $(find /mnt/t/ub2 -type c | wc -l)"'
tm "changed paths = find upper" sh -c 'find /mnt/t/ub2 -type f -o -type c | wc -l'
tm "reset = rm -rf upper and work" sh -c 'rm -rf /mnt/t/ub2 /mnt/t/wb2; mkdir -p /mnt/t/ub2 /mnt/t/wb2'
step "O13: the lower tree on the memory-backed root instead of a tmpfs (lower on an overlay root is fine?)"
cp -a /mnt/t/big /tmp/bigroot 2>/dev/null
rm -rf /mnt/t/ub3 /mnt/t/wb3; mkdir -p /mnt/t/ub3 /mnt/t/wb3
run pv $RUN -v /tmp/bigroot:/work:O,upperdir=/mnt/t/ub3,workdir=/mnt/t/wb3 $BB sh -c 'echo x >> /work/pkg1/f1; ls /work | wc -l'
step "memory after"
sh_run 'echo "cgroup usage: $(( $(cat /sys/fs/cgroup/memory/memory.usage_in_bytes) / 1048576 )) MiB"'
echo; echo "PROBE DONE"
