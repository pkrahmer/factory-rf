# Planning offline: numbers, decisions, gaps

For ideation and planning without access to the sandbox. Everything here is derived from `capabilities.md`,
`variants.md` and the raw `results/`. Treat each number as "measured once on 2026-10-31".

## Numbers to plan with

| Quantity | Value | Source |
|---|---|---|
| Largest job | 8 vCPU, 32 GiB | P6 |
| Memory-backed root: write speed | 2 to 4 GB/s | P6, P8, P9 |
| Ephemeral disk: size | 10 GiB total per job, ext4 | P8 |
| Ephemeral disk: throughput | 210 MB/s read or write, one shared ceiling (parallel writers do not add up) | P9 |
| Ephemeral disk: random 4 KiB | 11k write / 5.3k read IOPS at depth 1 (80 / 179 us); about 50k IOPS at depth 32 | P9 |
| Memory-backed root, same tests | 4.2 GB/s write, 6.3 GB/s read, 225k to 260k random IOPS | P9 |
| Ephemeral disk: 20000 small files (4 KiB, no process spawn) | create 0.2 s (buffered), `find` 0.02 s, read back 0.6 s (cached), delete 0.43 s (root: 0.16 s) | P9 |
| 1 GiB tree of 20000 files: build with `dd` | 17 to 20 s | P4, P8 |
| Reset by `cp -a` of that tree | 1.6 s (root and disk) | P4, P8 |
| Reset by tar extract | 1.8 s (root), 5.0 s (disk) | P4, P8 |
| Reset by overlay remount | 0.01 s (tmpfs upper), 0.06 s (disk) | P4, P8 |
| Diff by rsync dry run / by overlay upper | 0.2 s / 0.00 s | P4 |
| Apply the changes to the base | 0.08 s (overlay), 0.23 s (rsync) | P4 |
| Podman container start, second time | 0.16 s (native overlay on the disk) | P8 |
| Docker container start, second time | 0 to 1 s | P1 |
| Image pull, `python:3.12-slim` through the proxy | 6 to 8 s | P1, P8 |
| `podman --timeout` kill | exit 255, within about a second of the limit | P2, P3 |
| Job execution, everything included | 1.4 to 2.7 minutes | all |
| Dockerd start | under 1 s | P1 |

## Constraints to design against

1. **The factory runs in the same sandbox as the agents.** One job, one network namespace. Whatever the agent's
   container can reach, the factory's credentials can reach unless a rule says otherwise.
2. **Block the metadata server first** (`ip daddr 169.254.169.254 tcp dport 80 reject`, output and forward).
   Never rely on the job's service account for anything the factory needs: read tokens from mounted files or
   environment passed at creation.
3. **Everything leaves through one proxy.** No direct internet, no `no_proxy` for public names; containers do
   not inherit proxy variables unless told (Podman: `--http-proxy=false` to stop the automatic forwarding,
   then pass what is needed; Docker: the daemon reads them at start).
4. **Host network only.** Anything that listens (a test server on a port) listens in the job's namespace and
   collides with the factory's own ports and with parallel containers.
5. **Root, namespaced, without `CAP_MKNOD`.** Tools that create device nodes fail; images that need `MKNOD`
   (Docker's default set) need explicit capability lists.
6. **Memory is the disk, and the real disk is slow and small.** The 10 GiB ephemeral disk is capped at about 210 MB/s and 50k IOPS; a cold 1 GiB tree takes about 5 s to read, against well under a second from memory. Use it for what does not fit in memory (engine layers, the overlay upper layer of a big checkout), not for hot paths. Count the checkout, the virtualenv, the engine's image layers, the base copy and
   the overlay upper layer against the job's memory, or put the big ones on the 10 GiB ephemeral disk.
7. **The cgroup layout is a dependency.** Podman 5.x with runc works because cgroup v1 is still honoured. If
   the platform changes the layout (to v2), re-test: `crun` and Podman 6 become usable, and the hybrid
   workarounds may break.
8. **Nothing is persistent.** A restart of the job loses the checkout, the engine's storage and the base. The
   factory's state lives in git and in the hosting service; local state (logs, the cost records not yet
   pushed, the journal not yet committed) is at risk between pushes.

## Decision guide

```
Need a real separation between the factory and the agent's code?
├─ Yes, strongest: V6 (a job per step) or V8 (a VM with ZFS) -> needs a new architecture or another project
└─ Container-level is enough:
   ├─ Need image builds inside the job?            -> Podman (V1): Docker cannot RUN-build with default caps
   ├─ Prefer current upstream and a daemon?        -> Docker 29.9 (V2), explicit capability lists
   ├─ Need only a filesystem view and a time limit?-> bubblewrap (V5)
   └─ Need rootless or keep-id?                    -> not possible here
Snapshots:
   ├─ Memory budget is fine                        -> S1 overlay on a tmpfs
   ├─ Big tree                                     -> S2 overlay on the ephemeral disk (<= 10 GiB)
   └─ Simplest                                     -> S3 copy/rsync
```

## Questions a platform owner could answer (unmeasured, decisive)

- How does a person or a job obtain a valid bearer JWT for the model API (client credentials, a token
  service, a long-lived key)? The secret tried in P10 was rejected as "Invalid Token".
- Is there a supported way to push an image to the project's registry from a person's session or a build? (The
  three attempts failed with unreadable logs.)
- Will the execution environment stay on cgroup v1, and on which kernel line?
- What is the maximum task time of a job, and how are services' minimum instances and 24-hour restarts
  handled (for a long-running factory process)?
- Can the connector's proxy be reached by a VM in another project in the organisation, if a VM route is wanted?
- Can the public Ubuntu image project be allowed, or is there an approved Ubuntu or Debian image for VMs?

## What a feature for this could look like (ideas, not commitments)

These follow the factory's own seams and each is testable with the fakes the suite already has.

1. **A second `Snapshots` adapter** (overlay on a tmpfs or a directory), with the same interface tests as
   `ZfsSnapshots` and a fake-free test that runs on any Linux with root.
2. **A "job" profile for `PodmanRuns`**: root, `--network=host`, runc, no keep-id, `--http-proxy=false`, numeric
   user and owned bind directories; the preflight checks it by a probe container.
3. **A metadata block step** at start-up with a preflight item that proves it (a request to the metadata
   address must be refused from a container).
4. **A start-up image recipe**: an image or install script for the job (podman, runc, netavark, nftables,
   rsync, the tools) with pinned versions, since pushing images is unresolved.
5. **Settings and docs** for the profile, keeping the VM path as the primary one.
6. **Operator procedure**: how to create the job (size, ephemeral disk, connector, environment), how to place
   secrets, what a restart costs.

## Keeping this current

- Re-run the probe that backs a decision before building on it (`README.md`, "Reproducing a probe"): kernel,
  firewall and policies change without notice (two kernel builds were seen in one day).
- When a probe changes, change its script, re-run it, replace its file under `results/` and update the table
  line that cites it. Do not edit a result by hand.
- Add a probe for each new question instead of reasoning from the platform's documentation; the CLI help and
  the documentation were wrong or silent more than once in this work (for example the volume size limit was
  only visible in an error message).
