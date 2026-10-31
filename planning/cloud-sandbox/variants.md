# Plan variants: what was tested, what it means

Every variant considered for running the factory's stage isolation on the cloud sandbox, with its verdict.
Evidence references (`P1` to `P8`) point to `results/`; "ad-hoc" marks earlier probes whose logs were not kept.
`capabilities.md` has the detailed matrix; this file is about choosing.

## The factory's isolation model today (what has to be replaced)

One ZFS dataset per instance, rolled back to its one snapshot before every stage; every agent call and every
project command in a throwaway rootless Podman container on that dataset (`podman run --rm
--userns=keep-id --timeout ...`, `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit`,
`--memory`, the dataset at `/work`, read-only login files); after the agent the factory *takes* only the changed
paths the role may write. The seams in the code are two interfaces, `Snapshots` (`reset`, `advance`,
`changed_paths`, `mount_point`) and `ContainerRuns` (`launch`, `run`), with adapters `ZfsSnapshots` and
`PodmanRuns`. Everything below is measured against that.

## Summary

| # | Variant | Verdict | One line |
|---|---|---|---|
| V1 | Podman 5.4 + runc, as root in one job, host network, overlay snapshots | **feasible** | Best evidence; needs a root/host-network mode in the adapter and a metadata block. |
| V2 | Docker Engine 29.9 + runc 1.5, as root in one job | **feasible, more work** | Current software, but a new adapter and explicit capability handling. |
| V3 | Podman 4.3 + runc (Debian 12) | works, **not advised** | Old; no reason to prefer it over V1. |
| V4 | Podman 6 or any crun | **no** | Needs cgroup v2 or accepts no hybrid layout. |
| V5 | Engine-free sandboxes (bubblewrap) | **feasible**, different model | No images; isolation by namespaces and bind mounts. |
| V6 | One Cloud Run job per stage step | **not tested** | Hardest isolation, a different architecture; notes below. |
| V7 | Generation 1 execution environment | **no** | Not available for jobs. |
| V8 | A Compute Engine VM with ZFS (the existing design) | blocked here, **not a platform limit** | Needs an allowed Ubuntu image and VM rights. |
| V9 | A VM on Container-Optimized OS | **no** | No package manager, no ZFS, no host processes, Docker only. |
| S1 | Snapshot: overlayfs, upper on a tmpfs | **yes** | Fastest; counts against memory. |
| S2 | Snapshot: overlayfs on the ephemeral disk | **yes** | 10 GiB cap; real disk. |
| S3 | Snapshot: plain copy or rsync | works | Simple; 1.6 s per GiB. |
| S5 | Snapshot: podman `:O` overlay volume with `upperdir` on a tmpfs | **yes, preferred** | No reset step, the upper layer is the take's list; needs the container engine of V1/V2. |
| S4 | Snapshot: hard links, reflinks, loop images, btrfs (also on the disk's device), ZFS | **no** | See `capabilities.md` section 8 and P12. |

## V1. Podman 5.4 + runc, root, host network

**Setup that was measured.** Debian 13 (trixie) image from the Docker Hub mirror, `apt install podman runc
netavark nftables ...` through the proxy at every start, `podman --runtime=runc --cgroup-manager=cgroupfs`,
storage `overlay` on the ephemeral disk or `vfs`/fuse-overlayfs elsewhere, `--network=host`.

**What the factory's flags become**

| Today | In the job | Evidence |
|---|---|---|
| `--rm` | works | all |
| `--userns=keep-id` | **fails** with runc as root ("can't get final child's PID from pipe: EOF"). Drop it; run the container as a numeric user (`--user <uid>:<gid>`) and make the bind-mounted directories belong to that uid | P2 |
| `--timeout <s>` | works: kills at the limit, exit status **255** (the factory already reads 255 at or after the limit as the time limit) | P2, P3 |
| `--cap-drop=all` | works | P3, P8 |
| `--security-opt=no-new-privileges` | works | P3, P8 |
| `--pids-limit=4096` | works (tested at 20) | P2, P3 |
| `--memory=4g` | works (tested at 128m: exit 137) | P2 |
| (new) `--cpus` | works | P2 |
| `--env NAME=value` | works; **add `--http-proxy=false`**, because Podman forwards the job's proxy variables into containers otherwise (and busybox ignores `no_proxy`) | P2 |
| `--volume src:dst[:ro]` | works | P8 and ad-hoc |
| default network | **replace with `--network=host`** | P2b |
| `--workdir`, image, command words | not individually tested; no reason to fail | |
| `--runtime=runc` | **required** (Debian's podman prefers crun, which fails) | P2, P3 |
| rootless storage under the user | replace with a graph root on the disk volume or `vfs` | P8, P2 |

**What the adapters would need.** `PodmanRuns` gains a mode "as root, host network, runc, no keep-id, proxy
variables not forwarded"; `Snapshots` gets a new adapter (see S1/S2); the preflight loses the ZFS items and
gains an overlay check, a metadata-block check and a runtime check. The host-side process (the factory itself)
must also run in the job; with `NoNewPrivs` it cannot `sudo`, which it does not need.

**Risks.**
- Podman 5 supports cgroup v1 only as a deprecated path and says so on every call; Podman 6 dropped it. If the
  platform stays on this layout the line ends at 5.x; if it moves to cgroup v2, `crun` and Podman 6 work.
- Root in the job is a namespaced root with a reduced capability set, but the agent's container shares the
  network namespace with the factory process. The metadata block (capabilities.md section 5) is therefore
  part of the isolation, not an option; the factory's own tokens must come from files, never from metadata.
- The job's working disk is memory unless the ephemeral disk is used (10 GiB cap).
- Debian's runc is 1.1.x (current upstream is 1.5.x); the upstream binary worked and was checksum-verified.

**Verdict.** Feasible. Estimated work: one root/host-network profile in `PodmanRuns`, one `Snapshots`
adapter, setup of the image (install at start or a pre-built image, see "Images" below), preflight items, docs.

## V2. Docker Engine 29.9

**Measured** with the `docker:dind` image (Alpine, Docker 29.9.2, runc 1.5.2): the daemon starts in under a
second when started with `--iptables=false --ip6tables=false --bridge=none` (or with defaults; the bridge
starts), on a tmpfs data root; four storage options work (containerd overlayfs, `overlay2`, `fuse-overlayfs`,
`vfs`); none works on the job's overlay root.

**Differences to Podman that matter**
- Every run must say `--cap-drop=ALL` plus `--cap-add` of the default capabilities that exist here
  (`CHOWN DAC_OVERRIDE FOWNER FSETID KILL SETGID SETUID SETPCAP NET_BIND_SERVICE SYS_CHROOT SETFCAP`); the
  default set contains `MKNOD`, which the sandbox lacks, and Docker refuses even to *name* it.
- `docker build` with a `RUN` step fails ("unable to apply caps"), because BuildKit uses the default set.
  Podman builds fine. If images must be built inside the job, Podman is the better fit.
- No `--timeout` and no `--userns`: the adapter starts detached, waits and kills (measured: start, 3 s, kill,
  remove in 3 s, no container left).
- The daemon is a long-running process with a socket; Podman is daemonless. A crashed daemon takes every
  container with it.
- The proxy: the daemon reads the proxy variables at start; containers do not inherit them.
- Bridge networking: the daemon starts and a container runs; outbound access on the bridge was **not**
  measured (the probe was malformed); the equivalent Podman bridge had no outbound path, so assume the same
  until measured.

**Verdict.** Feasible and current, but it needs a different adapter, explicit capabilities and its own
time-limit handling. Prefer it only if Podman's deprecated cgroup v1 path is judged too risky; Docker documents
cgroup v1 support until at least May 2029. Docker on the ephemeral disk was not tested (expected to work: ext4
and overlay2 are the same as the podman case).

## V3. Podman 4.3.1 (Debian 12)

Worked in every ad-hoc test (runc 1.1.5, host network, vfs/overlay, the factory's flags, `--timeout` exit 255).
It is from late 2022 and Debian 12 is oldstable. No capability that Podman 5.4 lacks was found. Not advised.

## V4. Podman 6 and crun

Podman 6.1.2 refuses to start ("Cgroups v1 not supported"). crun 1.8.1, 1.21 and the newest upstream 1.30.1
all refuse the hybrid layout ("cgroups in hybrid mode not supported"). No flag changes that (`--cgroups=disabled`
is incompatible with runc and does not help crun). Revisit only if the platform moves to cgroup v2.

## V5. Engine-free sandboxes

bubblewrap works: read-only root with one writable bind, credential directories hidden by an empty tmpfs, a
pid namespace so that `timeout` ends the whole tree, a non-root uid inside, host network kept for the proxy.
cgroups can be written by hand for pids and memory limits. This would replace `ContainerRuns` by a much
smaller adapter and remove the engine, the image pull and the root-owned storage.

What it gives up: the stage image as a unit (the tools come from the job's own image or an unpacked tarball),
isolation of the filesystem view beyond what bind mounts express, and anything that expects an OCI image. What
it keeps: namespaces, read-only mounts, the time limit, resource limits. Not measured: Landlock (not
visible), seccomp inside the sandbox, and whether the agent's tools (git, make, uv, node, the runtimes) work
in a bwrap view of the job's own filesystem (very likely; not run).

**Verdict.** Feasible and simple; a real alternative if "images" are not essential. It changes the model:
the isolation is then a view of one filesystem, not a separate image.

## V6. One Cloud Run job per stage step (not tested)

The ephemeral disk cannot carry state between steps: it is per task, created and destroyed with it (platform
description, not tested). `recommendations.md` lists the carriers (bucket mount, NFS, git, object store) and a
probability estimate; read it before choosing this variant.

Hard isolation without any engine: every sync, agent run and check is its own job execution with its own
sandbox, kernel and filesystem. Design notes, none measured:
- State between steps cannot be an ephemeral disk (not shared). The candidates are a Cloud Storage bucket
  mounted with Cloud Storage FUSE (documented volume type, slow for many small files) or an NFS volume
  (documented; needs a server), or pushing every step's result through git/an object store.
- Each step pays a start-up of tens of seconds (measured executions: 1.4 to 2.7 minutes with installs; a
  prebuilt image would cut the installs).
- The factory process would stay a small long-running service that creates and watches executions.
- It removes the need for any engine, root, snapshot or metadata block inside the sandbox, at the price of a
  new architecture, cloud-API calls from the factory and slower stages.

## V7 to V9: platform alternatives

- **V7 gen1.** `--execution-environment=gen1` is refused for jobs. Only services accept it, and a service was
  not tested.
- **V8 a VM with ZFS.** Technically the cleanest (rootless Podman, ZFS, the code as it is), but the sandbox's
  organisation allows VM images only from an allow-list without the public Ubuntu project, and people could not
  create VMs there. Not a platform limit: another project or an exception removes it.
- **V9 a VM on Container-Optimized OS.** Allowed as an image, unusable: no package manager, no third-party
  kernel modules (so no ZFS), no non-containerised processes, Docker rather than Podman (documented).

## Agent runtime check (opencode in the job, measured)

The factory's opencode runtime was reproduced by hand in the V1 setup (Podman 5.4 + runc, root, host network,
`--http-proxy=false`, the pinned opencode 1.19.3 installed with npm through the proxy in a Node 22 container,
the provider block of F0046-S0001 with `{env:KEY}` for the bearer). It ran a real agent task with tool calls and
produced a parsable result block (capabilities.md section 11). What still needs work for the factory:
prices in the provider file (cost was 0), the one-hour token life (the key variable must be refreshed outside
opencode), the proxy exclusion for the internal API, and the per-run `opencode-<run>.json` and login shell
(the factory's own path) were not exercised; the probe used a hand-written config and `LLM_KEY` directly.

## Snapshot variants

**S5 is now the preferred one** (measured in P11): give each agent container its own overlay view of the base,
`-v <base>:/work:O,upperdir=<tmpfs>/<run>/upper,workdir=<tmpfs>/<run>/work`. The base is only ever written by
the sync step; the agent writes into the upper layer; after the run the factory reads the upper layer (files =
added or modified, character devices = deleted) for the take and removes it. Reset and the diff walk
disappear, and `advance` becomes "the sync step ran". The checks can take the same view, copy the taken files
into a fresh upper, and run. Always pass `upperdir` and `workdir` (the default upper fails on the memory-backed
root), do not combine `:ro` with `O`, and keep both directories on a tmpfs or the ephemeral disk. Open:
directory renames with tools other than busybox `mv`, opaque directories in the take, and how the sync step
(which writes the base) coexists with running checks.

The measured numbers are in `capabilities.md` section 8. The recommendation by situation:

| Situation | Use |
|---|---|
| Checkout plus tools well below the job's memory | **S1** overlayfs with the upper and work directories on a tmpfs; base tree on the root or a tmpfs. Reset 0.01 s. |
| A big checkout, or a memory budget that matters | **S2** everything on the ephemeral disk (10 GiB cap, 210 MB/s ceiling: a 1 GiB tree reads cold in about 5 s). Reset 0.06 s. |
| Simplicity matters more than speed | **S3** `cp -a` or rsync from a base directory: 1.6 s per GiB for reset, 0.2 s for the diff. |

**Design sketch for an overlay adapter** (not built): `mount_point` is the overlay mount; `reset()` unmounts,
empties upper and work, mounts again; `advance()` applies the upper layer to the lower tree (delete the whiteouts,
rsync the rest, then reset); `changed_paths()` walks the upper layer: regular files are `added` or `modified`
(compare with the lower tree to tell them apart), character devices with device number 0/0 are `deleted`,
directories are skipped as today. Open points: opaque directories and directory renames
(`redirect_dir=nofollow`), whether the base tree should be a tmpfs copy, and the memory cost of a Python
virtualenv in the upper layer. `trusted.*` xattrs are refused to this root on ext4, yet the plain overlay mount
(without `userxattr`) worked on both a tmpfs and the ephemeral disk, so the refusal did not bite; the probes'
`userxattr` fallback was never needed.

## Images (how the stage image gets into the job)

- Pushing to the project's own registry failed three times for reasons that could not be read (the build logs
  were invisible). Until that is solved, the stage image cannot be baked and pushed from inside the project.
- The working path in the probes is "start from a mirrored public base image and install at start-up through
  the proxy". It works and costs tens of seconds per start; it also means every start re-downloads packages.
- A Docker Hub image the mirror serves can be used as it is (for example `docker:dind` for V2).
- Images from other registries are refused at job creation.

## What was NOT tested (so do not assume)

- Cloud Run **services** (long-running, minimum instances, CPU always allocated, the 24-hour restart behaviour
  mentioned in the planning), including gen1 for services.
- The maximum task time of a job, and what a restart in the middle of a stage looks like to the factory.
- Cloud Storage FUSE and NFS volumes; more than one ephemeral disk; sizes between the tested ones.
- The factory itself, its test suite, the agent runtimes (Claude Code, opencode) and the model proxy inside a job.
- Landlock, seccomp contents, AppArmor/SELinux (none visible).
- Docker's bridge outbound, Docker on the ephemeral disk, `docker build` with another builder.
- Directory renames in the overlay; very large trees; concurrency of two jobs on one project; cost.
- GPU, arm64, several tasks per execution.
