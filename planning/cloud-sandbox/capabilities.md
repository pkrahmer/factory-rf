# Capabilities of the cloud sandbox

What Cloud Run jobs (second-generation execution environment) offer, as measured on 2026-10-31. Each
line names its evidence: `P1` to `P8` are the probes in `probes/`, their output is in `results/`.
"Documented" marks a statement taken from the platform's own CLI help or documentation and not measured.
"Not tested" says so. Verdicts: **yes**, **no**, **partly**, **unknown**.

## 1. The execution environment

| Question | Verdict | Detail | Evidence |
|---|---|---|---|
| Which execution environments can a job use? | gen2 only | Creating a job with `gen1` is refused: "not supported on resources of kind Execution". | P7 |
| Kernel | 6.9.12, x86_64 | The build changes between runs. | P6 |
| CPU | AMD EPYC 7B13 | Quota is a CFS limit: 8 vCPU gave `cfs_quota_us` 834200 (about 8.3 CPUs) and `nproc` 10. | P6 |
| Largest size obtainable | 8 vCPU, 32 GiB | Created and ran at that size. The CLI documents CPU values below 1, 1, 2, 4, 8. | P6 |
| Memory visible | the job's limit | 32 GiB limit showed `memory.limit_in_bytes` 34359738368. | P6 |
| Who is "root"? | namespaced root | `uid_map` is `0 1000 4294966295`: root inside maps to an ordinary host user. | P1 |
| Capabilities | reduced | `CapBnd` `000001fff7fcffff`: includes `CAP_SYS_ADMIN`, `CAP_NET_ADMIN`, `CAP_SYS_CHROOT`, `CAP_SETUID/GID`; lacks exactly `CAP_SYS_MODULE`, `CAP_SYS_RAWIO` and `CAP_MKNOD` (bits 16, 17 and 27). | P1, P5, P6 |
| `NoNewPrivs` | set (1) | setuid helpers gain nothing: `newuidmap` fails ("write to uid_map failed: Operation not permitted"), so rootless engines are impossible. | P6, earlier ad-hoc probe |
| seccomp | filter mode 2, one filter | Present; its content was not read. | P5, P6 |
| LSMs (AppArmor, SELinux, Landlock) | unknown | `/sys/kernel/security/lsm` does not exist. Landlock availability was not established. | P5 |
| User namespaces | yes | `unshare --user --map-root-user` works; `max_user_namespaces` 2147483647. Inside a nested user namespace the uid map is `0 0 1`. | P5 |
| Process namespaces | yes | `unshare --pid --mount-proc --fork` works. | P5 |
| Network namespaces | yes | `unshare --net` gives an empty namespace (loopback and two tunnel stubs). | P5 |
| Device nodes | very few | `/dev` holds only `core fd full fuse log mqueue null ptmx pts random shm stderr stdin stdout tty urandom zero`. No `/dev/net/tun`, no `/dev/kvm`, no loop devices. `mknod` is impossible without `CAP_MKNOD`. | P2, P4, P6 |
| `/dev/fuse` | yes | FUSE filesystems work (`fuse-overlayfs`). | P1, P2, P4 |
| Kernel modules | none loadable | `modprobe zfs` and `modprobe btrfs` find no module directory entries. | P6 |
| Platform environment variables | five | `CLOUD_RUN_JOB`, `CLOUD_RUN_EXECUTION`, `CLOUD_RUN_TASK_INDEX`, `CLOUD_RUN_TASK_COUNT`, `CLOUD_RUN_TASK_ATTEMPT`. | P6 |
| Resource limits | open | `nofile` 25000, `process` about 128000, others unlimited. | P6 |
| Maximum run time | documented, not tested | The task deadline is set with `--task-timeout`; the CLI help gives no maximum. Probes used 25 minutes. | CLI help |

## 2. Control groups

| Question | Verdict | Detail | Evidence |
|---|---|---|---|
| Layout | hybrid | v1 controllers mounted separately (`blkio cpu,cpuacct cpuset devices freezer memory net_cls,net_prio perf_event pids`) plus a `cgroup2` mount at `/sys/fs/cgroup/unified`. | P6 |
| Can the job's root create cgroups and set limits by hand? | yes | `mkdir` under `pids` and `memory`, `pids.max` and `memory.limit_in_bytes` written; a pids limit of 20 stopped a fork loop ("Cannot fork"). | P5 |
| Podman 5.4.2 + `runc` enforces `--memory` | yes | `--memory=128m` against a 300 MB shell variable: exit 137; same command unlimited: success; the container sees 134217728. | P2 |
| `--cpus` enforced | yes | `--cpus=0.5` gave 1615 loop iterations against 3438 unlimited (about half); quota 50000 visible. | P2 |
| `--pids-limit` enforced | yes | 20: "can't fork". | P1, P2, P3 |
| `crun` (any version) | no | "cgroups in hybrid mode not supported, drop all controllers from cgroupv2": 1.8.1, 1.21 and the newest upstream 1.30.1. | P2, P3 |
| `runc` | yes | 1.1.5, 1.1.15 (Debian) and 1.5.2 (upstream, SHA-256 verified; also bundled in Docker 29.9.2). | P1, P2, P3 |
| Podman 6.x | no | Refuses to start: "Cgroups v1 not supported". Podman 5.4.2 starts and prints a deprecation warning on every call. | earlier ad-hoc probe, P2 |
| Docker's cgroup v1 support | documented | Deprecated, supported until at least May 2029; measured working (cgroupfs driver, v1). | Docker release notes, P1 |

## 3. Storage

| Question | Verdict | Detail | Evidence |
|---|---|---|---|
| What is `/` and `/tmp`? | memory | An overlay whose upper layer lives in memory; writes count against the job's memory. Writing 3 GiB raised the memory-backed share (`Shmem`) from 0.23 to 3.37 GiB. `df` reports the memory limit as the size. | P6, P8 |
| Write speed on that root | 2 to 4 GB/s | Buffered: 1 GiB in 0.53 s, 3 GiB in 1.33 s. Direct I/O: 4.2 GB/s write, 6.3 GB/s read sequential; 225k to 260k random 4 KiB IOPS. | P6, P8, P9 |
| Native kernel overlay with its upper layer on `/` | no | "filesystem on /tmp/up not supported as upperdir". An overlay cannot sit on an overlay. | P4 |
| Kernel overlay with upper and work on a tmpfs | yes | Mount options `redirect_dir=nofollow`; 200 modified files copied up in 0.02 s; a deletion appears as a character-device whiteout in the upper layer. | P4 |
| `ephemeral-disk` volume | yes | A real ext4 block device (`/dev/mapper/md0`), documented as temporary and not shared, mounted wherever the job asks. **At most 10 GiB in total per job** (20 GiB was refused). | P8 |
| Its speed | about 210 MB/s, about 50k IOPS, throttled | Direct I/O (no page cache), 4 vCPU: sequential 1 MiB write and read 210 MB/s; random 4 KiB at queue depth 32: 49.7k write and 50.0k read IOPS (about 205 MB/s); at queue depth 1: 11.0k write IOPS (80 us) and 5.3k read IOPS (179 us); mixed 70/30 at depth 16: 34.5k read + 14.8k write IOPS. The ceiling is shared: two and four parallel writers still total 210 MB/s, and three repeated runs gave 210, 210, 210 MB/s. The memory-backed root, same tests: 4.2 GB/s write, 6.3 GB/s read, 230k to 260k random IOPS (20 times and 5 times the disk). | P9 (the earlier 190 MB/s was a buffered write with a final fsync) |
| Is it memory-backed? | no | `Shmem` stayed at 0.23 GiB while 3 GiB were written; the cgroup's memory usage rose by the page cache (reclaimable) only. | P8 |
| Its features | ext4 | User xattrs yes, `trusted.*` xattrs refused, hard links yes, sparse files and `fallocate` yes, reflinks no. | P8 |
| Kernel overlay, podman native overlay, fuse-overlayfs on it | yes | Overlay with lower, upper and work on the disk, reset in 0.06 s; podman `--storage-driver=overlay` on the disk root works (second container start 0.16 s). | P8 |
| Other volume types | documented, not tested | `in-memory` (size-limited, counts as memory), `cloud-storage` (Cloud Storage FUSE bucket), `nfs` (server:/path). | CLI help |
| Filesystems the kernel knows | list | `ext3 ext4 squashfs erofs overlay fuse fuseblk fusectl 9p virtiofs ceph nfs nfs4 cifs smb3 btrfs tmpfs ramfs hugetlbfs` and the pseudo filesystems. No `xfs`, no `zfs`. | P4 |
| Mount an image file (ext4, xfs, btrfs) | no | `mount -o loop` fails: no loop control device. btrfs exists in the kernel but cannot be reached without a block device. | P4 |
| ZFS | no | Not in `/proc/filesystems`, no module. | P4, P6 |
| Reflink copies | no | "Operation not supported" on the root and on ext4. | P4, P8 |
| `drop_caches` | no | Writing to `/proc/sys/vm/drop_caches` is denied. | P8 |

## 4. Network

| Question | Verdict | Detail | Evidence |
|---|---|---|---|
| Resolver | the metadata server | `nameserver 169.254.169.254`, search `google.internal`. Public names do not resolve directly; corporate names do. | P6 |
| Direct internet | no | Connections to public addresses (`1.1.1.1`, `8.8.8.8`) fail. Egress must use the configured VPC connector and then the proxy. | P6 |
| Egress configuration | organisation policy | Only the shared connector with `all-traffic` egress was accepted; the default "private ranges only" is refused by policy. Direct VPC egress needed subnet permissions the account lacked. | earlier ad-hoc probes |
| Ingress | internal only | The organisation allows only `internal` and `internal-and-cloud-load-balancing`. | policy listing |
| Proxy reachability | see table 4a | Through the corporate proxy, with plain HTTP `CONNECT`. | P6 |
| TLS interception | no, for tested hosts | The certificates seen through the proxy are the public issuers' (Sectigo for GitHub, GlobalSign for PyPI, Google Trust Services for the Anthropic API). | P6 |
| Platform firewall | yes | An nftables table `emerald_isolation` is installed (see 4b). Our own `nft` tables can be added beside it. | P2, P2b |
| `nft` / `iptables` usable | yes | `nft` works (rules load from a file); `iptables-save` printed nothing (iptables-nft is not the source of the rules). | P2b |
| IP forwarding | off by default, can be switched on | `ip_forward` 0; writing 1 is allowed. | P2b |

### 4a. Destinations through the proxy (HTTP status of one request, `curl -x`)

Status shows reachability, not authorisation. 2xx/3xx: reachable. 401, 404, 421: the server answered, so the
path through the proxy works. 403 and 400: answered with a refusal; the cause was not investigated.

| Reachable (200) | Redirect (301, 307) | Answered, needs auth or path (401, 404, 421) | Refused (403, 400) |
|---|---|---|---|
| github.com, api.github.com, pypi.org, registry.npmjs.org, registry.yarnpkg.com, deb.debian.org, archive.ubuntu.com, dl-cdn.alpinelinux.org, download.docker.com, astral.sh, proxy.golang.org, repo.maven.apache.org, rubygems.org, opencode.ai, models.dev, www.google.com | raw.githubusercontent.com, codeload.github.com, security.ubuntu.com, nodejs.org | registry-1.docker.io, mirror.gcr.io, quay.io, ghcr.io (401); objects.githubusercontent.com, files.pythonhosted.org, auth.docker.io, api.anthropic.com (404); api.openai.com (421) | crates.io, static.crates.io (403); storage.googleapis.com (400) |

Verified end to end through the proxy: `apt` (Debian), `curl` to GitHub, image pulls from Docker Hub
(busybox, python:3.12-slim in about 7 s), release downloads from GitHub, `npm`/`pip` indexes (status only).

### 4b. The platform's own firewall (read from the job)

An nftables table `emerald_isolation` with `OUTPUT`, `FORWARD` and `INPUT` chains (priority `mangle` for output,
`filter` for the others, policy accept). In summary:

- Traffic to the metadata server `169.254.169.254` is accepted on TCP 53, 80 and 443 and on UDP 53.
- Traffic to a second platform address (`169.254.169.253`) is accepted on a short list of ports, and
  `169.254.8.0/24` entirely; ICMP is accepted.
- Everything else in `169.254.0.0/16` and several IPv6 ranges is dropped; fragments are dropped.
- Nothing restricts ordinary destinations: reaching the outside is decided by the VPC connector and the proxy.

### 4c. Container networking inside the job

| Mode | Verdict | Detail | Evidence |
|---|---|---|---|
| `--network=host` | yes | Shares the job's namespace: same DNS, same proxy reach, and the same metadata access. | P1, P2 |
| `--network=none` | yes | | P2 |
| Default bridge (netavark, nftables installed) | partly | The container starts and DNS answers, but **no outbound connection works**, also after switching IP forwarding on and also to the proxy by IP. Docker's bridge also starts; its outbound path was not measured. | P2, P2b, P1 |
| slirp4netns, pasta | no | Both need `/dev/net/tun`, which does not exist. | P2 |
| Without `nftables` installed | no | netavark fails ("unable to execute nft"). | earlier ad-hoc probe |

## 5. The metadata server and the job's credentials

| Question | Verdict | Detail | Evidence |
|---|---|---|---|
| The job can read its own token endpoint | yes (200) | The status of `/instance/service-accounts/default/token` was 200 (the body was discarded, never logged). | P6 |
| A container can reach the metadata server | yes | Host-network and bridge containers, by address and by hostname, in both Podman and Docker. | P1, P2, P2b |
| Blocking works | yes | `table inet probeblock` with `ip daddr 169.254.169.254 tcp dport 80 reject` in the `output` and `forward` hooks made every container attempt fail with "Connection refused", by address and by name, while DNS (UDP 53), the proxy and name resolution kept working. The job's own access to metadata also stopped. HTTPS to the address was refused already. | P2b |
| Blackholing the address | no | The resolver IS that address: a blackhole route broke all name resolution. Block the port instead. | P2 (v1), P2b |
| nft pitfall | note | `fwd` is a reserved word; chain names must not be nft keywords. | P2 |

Consequence: anything that runs in a container with the host network can mint tokens for the job's service
account unless this rule is installed first. The rule belongs in the factory's start-up.

## 6. Container engines in the job

| Engine | Verdict | What works | What does not | Evidence |
|---|---|---|---|---|
| Podman 5.4.2 + runc 1.1.15 (Debian 13) | yes, as root | `run` with `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit`, `--memory`, `--cpus`, `--timeout` (kills at the limit, exit 255), `--rm`, `-v` (read-write and `:ro`; `:ro` enforcement seen in an earlier ad-hoc run, read-write in P8), `--read-only` rootfs not tested, `--user 1000:1000`, image pull through the proxy, `podman build` with `RUN`, storage drivers `vfs`, `overlay` (kernel, on a tmpfs or the disk volume) and fuse-overlayfs | `--userns=keep-id`; rootless; slirp4netns/pasta; the default network's outbound | P2, P2b, P3, P8 |
| Podman 4.3.1 + runc 1.1.5 (Debian 12) | yes, as root | The same list, older. | The same. | earlier ad-hoc probe |
| Podman 6.1.2 | no | | "Cgroups v1 not supported" | earlier ad-hoc probe |
| Upstream runc 1.5.2 with Podman 5.4.2 | yes | All controls above; checksum verified. | | P3 |
| crun 1.30.1 (newest) | no | | hybrid cgroups refused | P3 |
| Docker Engine 29.9.2 (`docker:dind`, runc 1.5.2) | yes, as root, with changes | `dockerd` starts in under a second with four storage options; memory (exit 137), pids, `--read-only`, read-write and `:ro` bind mounts, `--user`, image pulls through the proxy (the daemon honours the job's proxy variables), second container start about 1 s | Default capabilities (`MKNOD`): every run must use `--cap-drop=ALL` plus explicit `--cap-add` of the capabilities that exist; even `--cap-drop=MKNOD` is refused. `docker build` with a `RUN` step fails on capabilities. No `--timeout` (the caller kills). Storage cannot sit on `/` (overlay on overlay): use a tmpfs or the disk volume; `fuse-overlayfs` needs the package. | P1 |
| Rootless Docker/Podman | no | | `NoNewPrivs`, `newuidmap` | P6 and earlier |

`--userns=keep-id` as root: `runc create failed: can't get final child's PID from pipe: EOF` (P2). A numeric
`--user 1000:1000` works when the bind-mounted directory is owned by that uid and fails ("Permission denied")
when root owns it (P1, P2).

## 7. Isolation without an engine

| Tool | Verdict | Detail | Evidence |
|---|---|---|---|
| `unshare` (pid, mount, user, net) | yes | A pid namespace makes the first process pid 1; killing it ends the tree. | P5 |
| bubblewrap (`bwrap`) | yes | Read-only bind of `/`, one writable bind, `--tmpfs /root` hides a credential directory, `--unshare-pid --die-with-parent` plus `timeout 3` leaves no process behind, `--unshare-user --uid 1000` gives a non-root user that can write to the bind, host network kept. | P5 |
| nsjail | no | Not packaged in Debian 13. | P5 |
| Hand-made cgroups | yes | See section 2. | P5 |
| Landlock | unknown | | P5 |

## 8. Snapshots (replacements for ZFS)

On a 1 GiB tree of 20000 files (400 directories) on the memory-backed root, 4 vCPU, 16 GiB (P4), and on the
ephemeral disk (P8). The factory's interface has three operations: reset, advance, changed paths.

| Mechanism | Reset | Advance | Changed paths | Verdict |
|---|---|---|---|---|
| Copy (`rm -rf work; cp -a base work`) | 1.62 s (disk: 1.66 s) | rsync of the changes 0.23 s | `rsync -a -n -i` 0.20 s (disk: 0.18 s); `diff -rq` 1.8 s | works, simple, doubles the space |
| Hard-link copy (`cp -al`) | 0.63 s | n/a | n/a | **no**: writes in place change the base too |
| Reflink copy | n/a | n/a | n/a | **no**: not supported |
| Kernel overlay, upper and work on a tmpfs | 0.01 s | 0.08 s (apply whiteouts, rsync the upper) | 0.00 s: list the upper layer; deletions are character-device whiteouts | **yes, best on memory** |
| Kernel overlay, all on the ephemeral disk | 0.06 s | not timed | the upper layer | **yes, best for size** (10 GiB limit) |
| fuse-overlayfs | about 0.16 s per 200 writes | not timed | the upper layer | works, slower than the kernel overlay |
| tar archive as base | 1.84 s extract (disk: 4.95 s) | 1.30 s pack (disk: 4.63 s) | none | works, no diff |
| Loop-mounted ext4, xfs, btrfs image | n/a | n/a | n/a | **no**: no loop devices |
| btrfs snapshots, ZFS | n/a | n/a | n/a | **no** |

Overlay details that matter: a kernel overlay's upper layer must not be on the overlay root; with
`redirect_dir=nofollow` (as mounted here) renaming a directory that exists in the lower layer is refused with
`EXDEV` (tools fall back to copying); that rename case was **not tested**.

## 9. Images and registries (for Cloud Run itself)

| Question | Verdict | Detail | Evidence |
|---|---|---|---|
| Which registries may a job's image come from? | `gcr.io`, `*-docker.pkg.dev`, `docker.io` | Other registries (for example quay.io) are refused at creation: "Expected an image path like [host/]repo-path ... where host is one of [region.]gcr.io, [region-]docker.pkg.dev or docker.io". | earlier ad-hoc probe |
| Docker Hub images | via a pull-through mirror | Popular images resolve (`debian`, `ubuntu`, `docker:dind`); some third-party tags fail with "manifest unknown" from the mirror though they exist upstream. | earlier ad-hoc probe, P1 |
| Pushing to the project's own registry | unresolved | Three builds through Cloud Build ended in FAILURE at the push step, and the logs were not readable by the calling identities (Cloud Logging returned nothing). Not diagnosed. | earlier ad-hoc probe |
| Installing at start-up through the proxy | yes | The probes install podman, runc and tools with `apt` at every start; this adds tens of seconds per start (not timed separately). | all |
| Time of a probe execution | 1.4 to 2.7 minutes | Measured from start to completion for the eleven executions of this session, each including the package installs. A cold image import of a large image alone took 1 min 34 s once. | probes |

## 10. The organisation around the project (generic)

These are policies of the sandbox project's organisation, visible through the platform's own APIs. They
decide what can be built there, independently of the platform's technical limits:

- External IP addresses on VMs are denied; the serial console is disabled.
- Only a list of image projects may supply VM images (the public Ubuntu project is not on it); Container-
  Optimized OS is on it but cannot run this workload (no package manager, no ZFS, no non-container processes).
- VPC Service Controls are enforced on the project.
- Cloud Run: ingress internal only; egress through a VPC connector with `all-traffic`.
- People hold operator roles; the roles that create resources belong to pipeline service accounts, and a
  small set of impersonation grants is the sanctioned way for a person to act with them.
- Compute Engine VMs could not be created by people in the project.
