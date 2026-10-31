# P9: how fast is the ephemeral-disk volume, measured without the page cache?
# fio with direct I/O: sequential and random, several block sizes and queue depths, a small-file
# workload without process-spawn overhead, parallel writers, and a repeat for variation.
# The job is created with one volume mounted at /disk, and for comparison the memory-backed root is
# measured the same way. Uses whatever size the volume has.
setup_env
apt_install fio rsync coreutils util-linux procps
echo "=====BEGIN-RESULTS====="
step "the volume and the tool"
sh_run 'df -hT /disk | tail -1; fio --version; nproc'
sh_run 'cat /sys/block/*/queue/scheduler 2>&1 | head -3; ls /sys/block | head'

F="fio --directory=/disk --size=2G --runtime=20 --time_based=0 --group_reporting --output-format=terse --terse-version=3 --minimal"
# terse v3 fields: 6 read bw KB/s, 7 read iops, 8 read lat... ; 47 write bw, 48 write iops. Print a readable line instead.
fio_run() { # fio_run <label> <fio args...>
  label=$1; shift
  out=$(fio --group_reporting --output-format=json "$@" 2>&1)
  echo "$out" | python3 -c '
import sys,json
t=sys.stdin.read()
try:
    d=json.loads(t[t.index("{"):])
except Exception as e:
    print("'"$label"': fio output unreadable:", t[:300].replace("\n"," ")); sys.exit()
j=d["jobs"][0]
def part(n,x):
    if x["io_bytes"]==0: return ""
    lat=x.get("clat_ns",{}).get("percentile",{})
    return "%s bw %.0f MB/s  iops %.0f  clat mean %.0f us p99 %.0f us" % (n, x["bw_bytes"]/1e6, x["iops"], x["clat_ns"]["mean"]/1000, lat.get("99.000000",0)/1000)
print("'"$label"': "+"  |  ".join(p for p in (part("read",j["read"]),part("write",j["write"])) if p))
' 2>&1 || python3 --version >/dev/null 2>&1 || echo "$label: no python3 to read fio json"
}
apt-get install -y -qq --no-install-recommends python3-minimal >/dev/null 2>&1

for where in /disk /tmp; do
  step "FIO on $where (direct I/O, 2 GiB file, 20 s per test)"
  mkdir -p $where/fio
  C="--directory=$where/fio --size=2G --runtime=20 --time_based --ioengine=libaio --direct=1 --name=t"
  fio_run "seq write 1M qd8   " $C --rw=write --bs=1M --iodepth=8
  fio_run "seq read  1M qd8   " $C --rw=read  --bs=1M --iodepth=8
  fio_run "rand write 4k qd1  " $C --rw=randwrite --bs=4k --iodepth=1
  fio_run "rand read  4k qd1  " $C --rw=randread  --bs=4k --iodepth=1
  fio_run "rand write 4k qd32 " $C --rw=randwrite --bs=4k --iodepth=32
  fio_run "rand read  4k qd32 " $C --rw=randread  --bs=4k --iodepth=32
  fio_run "mixed 70/30 4k qd16" $C --rw=randrw --rwmixread=70 --bs=4k --iodepth=16
  step "FIO on $where: buffered (page cache) sequential write with fsync at the end, 2 GiB"
  fio_run "buffered seq write " --directory=$where/fio --size=2G --ioengine=psync --bs=1M --rw=write --end_fsync=1 --name=b
  rm -rf $where/fio
done

step "FIO on /disk: two and four parallel writers (1 GiB each, direct, sequential 1M)"
mkdir -p /disk/fio
for n in 2 4; do
  fio_run "seq write x$n       " --directory=/disk/fio --size=1G --ioengine=libaio --direct=1 --rw=write --bs=1M --iodepth=8 --numjobs=$n --name=p --runtime=20 --time_based
done
rm -rf /disk/fio

step "FIO on /disk: the same sequential write three times (variation)"
mkdir -p /disk/fio
for i in 1 2 3; do fio_run "run $i seq write   " --directory=/disk/fio --size=2G --ioengine=libaio --direct=1 --rw=write --bs=1M --iodepth=8 --name=v --runtime=15 --time_based; done
rm -rf /disk/fio

step "SMALL FILES without process spawn: create 20000 files of 4 KiB, read them back, delete them (fio, one directory tree)"
for where in /disk /tmp; do
  mkdir -p $where/sf
  fio_run "$where create 20000x4k" --directory=$where/sf --nrfiles=20000 --filesize=4k --file_service_type=sequential --rw=write --bs=4k --ioengine=psync --name=c --numjobs=1 --fsync=0
  s=$(date +%s.%N); find $where/sf -type f | wc -l >/dev/null; e=$(date +%s.%N); awk -v s=$s -v e=$e -v w=$where 'BEGIN{printf "%s find over 20000 files: %.2f s\n", w, e-s}'
  s=$(date +%s.%N); cat $where/sf/*/* > /dev/null 2>&1 || find $where/sf -type f -exec cat {} + > /dev/null; e=$(date +%s.%N); awk -v s=$s -v e=$e -v w=$where 'BEGIN{printf "%s read all (cached): %.2f s\n", w, e-s}'
  s=$(date +%s.%N); rm -rf $where/sf; e=$(date +%s.%N); awk -v s=$s -v e=$e -v w=$where 'BEGIN{printf "%s delete tree: %.2f s\n", w, e-s}'
done

step "COLD-ish read of a tree: write 1 GiB in 5000 files on /disk, sync, then read with O_DIRECT through dd iflag=direct"
mkdir -p /disk/cold; i=0
s=$(date +%s.%N); while [ $i -lt 50 ]; do dd if=/dev/zero of=/disk/cold/f$i bs=1M count=20 oflag=direct 2>/dev/null; i=$((i+1)); done; e=$(date +%s.%N); awk -v s=$s -v e=$e 'BEGIN{printf "write 50 x 20 MiB direct: %.2f s (%.0f MB/s)\n", e-s, 1048576000/(e-s)/1e6}'
s=$(date +%s.%N); for f in /disk/cold/f*; do dd if=$f of=/dev/null bs=1M iflag=direct 2>/dev/null; done; e=$(date +%s.%N); awk -v s=$s -v e=$e 'BEGIN{printf "read 50 x 20 MiB direct: %.2f s (%.0f MB/s)\n", e-s, 1048576000/(e-s)/1e6}'
rm -rf /disk/cold

step "memory after"
sh_run 'echo "cgroup usage: $(( $(cat /sys/fs/cgroup/memory/memory.usage_in_bytes) / 1048576 )) MiB"; df -h /disk /tmp | cut -c1-80'
echo; echo "PROBE DONE"
