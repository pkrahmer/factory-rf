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
| btrfs on the ephemeral disk's block device | no | `findmnt` shows `/dev/mapper/md0`, but the node does not exist inside the job (`/dev/mapper` and `/dev/md*` absent, `lsblk` lists only nbd/pmem stubs), `umount /disk` says "not mounted", `mkfs.btrfs` cannot open the device, `mount -t btrfs` is denied. | P12 |
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
| Podman overlay volume `-v base:/work:O,upperdir=U,workdir=W` (U and W on a tmpfs) | 0.01 s (`rm -rf` the upper) | none needed: the base is written by the sync step, not by the agent | 0.01 s: `find` the upper (files, whiteouts as character devices) | **yes, the best fit** (P11) |
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

## 11. A model API and opencode (measured end to end)

Probe P10, `results/p10-opencode-model-api.txt`. An OpenAI-style API of the organisation, authenticated by an
Azure-AD-style OAuth2 client-credentials grant: the client id and secret go to the identity provider's token
endpoint (form-encoded, with the API's scope) and the returned JWT is the bearer token for the API. The API
spec has `/models`, `/models_metadata`, `/chat/completions`, `/embeddings`, `/batches`, `/files`; the request
schema has `tools`, `tool_choice`, `parallel_tool_calls`, `stream`, `stream_options`, `reasoning_effort`.

| Question | Verdict | Detail | Evidence |
|---|---|---|---|
| Token from inside the job | yes | The token endpoint answered 200 through the proxy: `token_type` Bearer, `expires_in` 3599 s (one hour), a 1278-character JWT. | P10 |
| The stored secret | a bare client secret | 40 characters with `-`, `_`, `~`, no colon, JSON or whitespace; as a bearer it is refused (`401 Invalid Token`); as the client secret it works. The client id is stored nowhere in Secret Manager. | P10, read of properties only |
| Internal API host reachable | yes | Resolves to a private address; without a token it answers 401, directly and through the proxy. | P10 |
| **The proxy must NOT be used for the internal API host** | yes, important | With the host in `NO_PROXY` everything works; without it opencode ran 79 s and failed (exit 1, one event). Put the API's domain in `NO_PROXY`. | P10 C4 |
| `/models`, `/models_metadata` | yes | 35 models of several vendor families; each metadata entry has `context_window`, `max_output_tokens`, `pricing`, `rate_limit`, `reasoning_levels`, `aliases`, `hosted_on_prem`. | P10 |
| Plain, tool-call and streamed completions | yes | 200 on all three; the stream ends with `[DONE]` and carries a final `usage` chunk (`stream_options.include_usage`). | P10 B1 to B3 |
| Pinned opencode 1.19.3 from npm through the proxy in a `node:22-slim` container | yes | 9 to 15 s to install; prints 1.19.3. | P10 |
| The factory's opencode run: provider block, `--format json --auto --agent`, tools, result block | **yes** | Exit 0 in 15 s; 5 steps, 4 tool calls (`write`, `bash` x3), the file was created in the bind-mounted checkout, one session id, no error events, and the final text ended with a `<factory-result>` block that the factory's strict pattern accepts (`decision: doing`). Tokens 5614 in, 530 out, 21465 cache read. | P10 C2 |
| Cost as opencode reports it | **depends on the provider block's prices** | Without `cost` in the provider block opencode reports 0 (P10). With the catalogue's prices (dollars per million tokens, `pricing.per_1M_input_tokens` and `per_1M_output_tokens`) it reports a cost per step: a one-step task cost 0.00009 dollars and a four-step task with a test run 0.0005 dollars on the smallest Claude model, so the factory's budget stop works. | P10 C2, P13 |
| Metadata block rule | yes | Applied from a file; after it the metadata endpoint is unreachable from the job (000). | P10 |
| The token's one-hour life | design point | A long-running factory must fetch a new token before it expires and rewrite what holds it (opencode reads the key from `{env:...}` once per process, so a run lasts at most one token life unless the process is restarted with a fresh one). Not tested beyond one run. | spec, P10 |

### 11a. The model catalogue and a second run (P13)

`results/p13-claude-catalogue-and-cost.txt`.

| Question | Verdict | Detail | Evidence |
|---|---|---|---|
| Which models are hosted on-prem (free for the organisation)? | not the Claude ones | `hosted_on_prem` is true for deepseek, qwen, glm, a 27B model family and embedding/speech models; **false for every Claude model** (haiku, sonnet, opus in two generations). | P13 |
| Claude family in the catalogue | five models | Context 1,000,000 tokens, max output 128,000, reasoning levels `minimal` to `max`. Prices in dollars per million tokens (input / output): haiku 0.1 / 0.5, sonnet 2 / 10, opus 4 to 5 / 20 to 25; above 100k input tokens the price rises (haiku 0.5 / 2.5). Rate limit tiers `Basic`, `Advanced`, `VIP`, 100 requests per 60 s on Basic. | P13 |
| Catalogue field names | note | `pricing.per_1M_input_tokens`, `pricing.per_1M_output_tokens`, `pricing.per_1M_input_tokens_above_100k`; `rate_limit` by tier; `context_window`; `max_output_tokens`. A reader that expects other names reads price 0 without error. | P13 (the first run read 0) |
| Two tasks on the smallest Claude model | works, with a caveat | Both ran to exit 0 with tool calls (write, write, bash x2). **The strict result block parsed in one task and not in the other**: the model wrote `entry: <text>` on one line, but the parser requires `entry:` alone on its line, so the factory would end that run as `no_result` (a stall). The longer task parsed. | P13 |
| The python test the agent was to run | environment | The `node:22-slim` image has no `python3`; the agent reported that it could not run the test and asked (`decision: question`). The factory's stage image has the project's tools. | P13 |

## 12. Podman overlay volumes (`-v SRC:DST:O`)

Probe P11, `results/p11-podman-overlay-volumes.txt`. Podman 5.4.2 + runc, as root, host network.

| Question | Verdict | Detail | Evidence |
|---|---|---|---|
| Explicit `upperdir` and `workdir` on a tmpfs | **yes** | The container sees base plus its changes at the mount target; the base directory is never written; the upper holds added and modified files and a character-device whiteout for each deletion; a new directory appears as a directory. | P11 O4, O5 |
| Default upper (no `upperdir`) | partly | Fails with a `vfs` or overlay graph root on the memory-backed root (an overlay cannot sit on the root overlay); works when the graph root is on a tmpfs. Always give `upperdir` and `workdir`. | P11 O1, O2, O3 |
| Reset | free | Discard the upper and work directories; the next container sees the base again. | P11 O6, O12 |
| The factory's flags with an overlay volume | yes | `--cap-drop=all --security-opt=no-new-privileges --pids-limit --memory --user 1000:1000`: works; files copied up keep the numeric owner. | P11 O7 |
| `:ro,O` together | no | "can't use 'O' with other options". | P11 O8 |
| Two containers at once on one base, different uppers | yes | Each sees only its own writes. | P11 O9 |
| Rename of a directory inside the overlay | yes (busybox `mv`) | `mv dir1 dir1b` exit 0; the upper holds a whiteout for `dir1` and a copy as `dir1b`. GNU `mv` and other tools were not tried. | P11 O10, O11 |
| Cost on a 1 GiB, 20000-file base | small | Container start 0.18 s, 200 appends plus one delete 0.20 s, 199 files and 1 whiteout in the upper, `find` 0.01 s, reset 0.01 s. | P11 O12 |
| Lower tree on the memory-backed root | yes | Only the upper and work directories need the tmpfs or the disk. | P11 O13 |
| Opaque directories (a directory deleted and recreated) | untested | The take would have to read `trusted.overlay.opaque`; the probe's list showed none because none were created. | P11 O5 |

## P14: the opencode lockdown (2026-10-31, second run)

Probe `p14-opencode-lockdown.sh`, result `results/p14-opencode-lockdown.txt` (the first run failed by a bug of the probe and is kept as `results/p14-opencode-lockdown-run1-failed.txt`). Every outbound connection of the container went through a logging proxy on the job's loopback; the model API's host is in `no_proxy` and goes direct, so it is not in the lists by design. opencode 1.19.3 from npm, claude-sonnet-5, the same task in both runs (create `hello.txt`, end with the result block).

| | Hosts contacted (connections) | Exit | `hello.txt` | Result block parses |
|---|---|---|---|---|
| A, without the lockdown | `registry.npmjs.org` (4), `models.opencode.ai` (1) | 0, 7 s | `hello` | yes |
| B, with `enabled_providers: ["corp"]` and the three switches | `registry.npmjs.org` (4) | 0, 8 s | `hello` | yes |

- **Did run B still work?** Yes, completely: exit 0, 6 events, the file created, the strict result block parsed.
- **`enabled_providers`.** opencode 1.19.3 accepted it without a word: the "lines about the configuration" section of run B is empty, and the run behaved as in A.
- **Which switch changed the host list on its own (section D, each alone, start only).** Only `OPENCODE_DISABLE_MODELS_FETCH=1`: with it the list is `registry.npmjs.org`; with `OPENCODE_DISABLE_AUTOUPDATE=1` alone or `OPENCODE_DISABLE_DEFAULT_PLUGINS=1` alone it is `models.opencode.ai` and `registry.npmjs.org`, the same as run A. So the other two switches changed nothing observable in this task; they are not shown to be wrong, only not shown to matter here (an update check and default plugins may only act in other situations).
- **The model catalogue host is the vendor's, not `models.dev`.** The fetch of the public model list goes to `models.opencode.ai`, a vendor host. Without the fetch switch every run contacts it once.
- **What stays in B.** `registry.npmjs.org`, four connections in each run, also with all three switches. I did not read which package: the likely cause is opencode installing the provider's package (`@ai-sdk/openai-compatible`) from npm at the start of a run, which the provider block names; this is an inference, not shown. If it is that, the registry is needed at every start of a run and no switch removes it; a deployment that must not reach npm would have to pre-install the package, which was not tried.
- **Cost.** The runs reported no cost figure in the saved output (the probe prints none); not measured here.
- **Verdict against the probe's own VERDICT line.** By its letter S0007 fails (the line says B must list no npm registry), but the one host that is the vendor's, `models.opencode.ai`, is gone in B, the run works, the key is accepted, and the remaining registry traffic is not a vendor host and is not caused by a switch S0007 leaves out; S0007 does what its text says, and the line's "npm registry" condition asks for something the switches cannot give.
- **Also seen.** The metadata-block rule file loaded this time (exit 0); the token request returned 200.

## P15: the stage image and make check in a job (2026-10-31)

Probe `p15-stage-image-and-check.sh`, result `results/p15-stage-image-and-check.txt`. One job of 8 vCPU and 32 GiB (the CPU count seen was 9), run once, 6 min 58 s in all. The code was a fresh clone of the public factory-rf at the commit of the request; podman 5.4.2 with the S0002 words (`--runtime=runc`, `--cgroup-manager=cgroupfs`, overlay storage with `fuse-overlayfs`); runc 1.5.2 passed the SHA-256 pinned in S0006.

| Step | Result |
|---|---|
| The stage image build (`vm/Dockerfile`, `--network=host`) | exit 0 in **169 s**; image size **2,371,193,789 bytes** (2.2 GiB). The Debian packages pinned in `vm/Dockerfile` all resolved today. |
| Inside the image, as the job's root with every capability dropped | git 2.39.5, GNU Make 4.3, uv 0.9.2, node v18.20.4, Claude Code 2.1.296, opencode 1.19.3, `uid=0(root)` |
| `snapshot.debian.org` through the proxy | answered 200 |
| `make sync` (the factory's words, as root) | exit 0 in **8 s**, `sync: green (7.4 s)`; the work folder was 992 MB |
| `make check` | **exit 2 after 134 s** |
| Targets | `lint: green (0.4 s)`, `types: green (11.7 s)`, `layers: green (0.3 s)`, `sast: green (5.0 s)`, then `make: *** [Makefile:60: secrets] Error 1` with the line `ERROR: Potential secrets about to be committed to git repo!` |
| `licenses`, `test` | **not reached**: make stopped at `secrets`. No test ran, so no pytest summary and no `E` lines exist. |
| Copy snapshots on the synced tree | 1012 MB, 19030 files: `cp -a` 1 s (advance), empty and copy back 2 s (reset), `rsync` of an unchanged tree 1 s |
| `diff -r` of the two trees | 1 s, exit 2, with 226 "No such file or directory" lines for the same symlinks in both trees (links in the virtual environment and in the uv cache point to paths that exist only inside the image); exit 2 is the dangling links, not a difference between the trees |
| Memory (MemAvailable, MiB, of 32094) | 31155 at start; 28738 after the image build (Shmem 2725); 27698 after `make check` (Shmem 3737); 26676 after the copies (Shmem 4749); `/` held 4.7 GiB of 32 |

- **What the probe does not show.** Which file `detect-secrets` flagged: the probe prints only a one-line grep of the check log, not the secret hook's `Secret Type` and `Location` lines. On the same commit, run locally with the Makefile's own file filter (every tracked file except `uv.lock`, `.secrets.baseline`, `planning/`, `docs/runs/` and the cost records), the hook exits 0, so the cause is not visible from here. Candidates, none checked: a difference between the job's container and the VM that changes what the hook sees (the checkout was a `cp -a` copy owned by the job's root, git's view of it, the hook's version), or a file that exists only in the job's tree.
- **What that means for the questions of the request.** The build and the image work, the pinned Debian versions resolve today and the proxy reaches the date-pinned archive; `make sync` works as root. Whether the suite passes as root is **unanswered**, because the tests were never reached.
- **Verdict against the probe's VERDICT line.** S0006 can build its image at start (exit 0 in 169 s, the longest part of a start), but "the factory's checks run in the job" is not shown: `make check` exited 2 at the `secrets` target before the tests, for a reason the probe's log does not contain.

### P15, second run (2026-10-31, `results/p15-stage-image-and-check.txt`; the first run's log is `results/p15-stage-image-and-check-run1.txt`)

The probe now ran the check's seven targets with `make -k`, printed what `detect-secrets` flagged, and used `diff --no-dereference`. The job again had 8 vCPU and 32 GiB (10 CPUs seen), at the factory's commit that carries the false-positive records for the two acceptance reports; 17 min 26 s for the whole job.

| Target | Result |
|---|---|
| `make sync` | exit 0 in 8 s, `sync: green (7.4 s)` |
| `lint` | `green (0.5 s)` |
| `types` | `green (12.6 s)` |
| `layers` | `green (0.4 s)` |
| `sast` | `green (5.4 s)` |
| `secrets` | **`green (113.7 s)`**, and the probe's list of what `detect-secrets` flagged is empty: red in the first run, green now, as the answer from home said (the false positives are recorded in `.secrets.baseline`) |
| `licenses` | `green (0.5 s)` |
| `test` | **`green (601.2 s)`**: the whole suite passed in the job, as the job's root with every capability dropped |
| `make -k` as a whole | exit 0 after 736 s |

- **The suite as root: no test failed.** No `FAILED`, no `ERROR` and no `E` line is in the log, so no test expecting a file to be unreadable, unwritable or not owned by the user was hit. The root-in-container question of F0047 decision 3 is answered: the suite passes as root.
- **What the log does not hold.** Pytest's own summary line (the number of tests and the coverage) is not in the saved text: the probe keeps only the lines of the check log that match `passed|failed|error` from its tail, and the output shows only `All checks passed!` (ruff's line). The green `test` target is the Makefile's own result (it ends with its `green` line only when pytest and the coverage floor pass).
- **Time.** `test` took 601 s of the 736 s, in a container limited to 4 GiB memory and 4096 pids; the image build took 199 s. `make check` as the factory runs it would be about 12.5 minutes plus the sync and a base copy, under the 8-minute `time_limit` the pipeline definition gives `check` today: the factory's `check` would be stopped by its own time limit in this job unless it gets more time or more CPUs.
- **Copy snapshots on the synced tree** (1015 MB, 19039 files): copy 2 s, reset 3 s, `diff -r --no-dereference` 1 s and exit 0 (no dangling-link errors this time), `rsync` of an unchanged tree under 1 s.
- **Image and memory.** The image is 2,371,193,788 bytes; the tree and the image together held 4.7 GiB of the 32 at the end.
- **Verdict.** Against the probe's VERDICT line the checks run in the job, as root: every target is green, `secrets` included; the one thing the job changes is the time (`test` alone takes about ten minutes here), which the pipeline definition's 8-minute `time_limit` for `check` does not allow.
