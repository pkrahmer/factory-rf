# Recommended setups, in order

Ranked by fit to what the factory does today and by how much of the ranking rests on measurements. The
evidence is in `capabilities.md` and `variants.md`. Written 2026-10-31.

## Platform and isolation

1. **A VM with ZFS and rootless Podman (V8).** The current design: no code changes, the strongest isolation.
   Not a platform limit; in the sandbox it is blocked by organisation policy (people cannot create VMs, no
   allowed Ubuntu image). If that route opens, nothing below is worth building for a trial.
2. **Podman 5.4 with runc, as root in one Cloud Run job, host network (V1).** The best-evidenced Cloud Run
   option: every control the factory uses was measured. Needed: drop `--userns=keep-id`, add
   `--runtime=runc --network=host --http-proxy=false`, run containers as a numeric user on owned bind
   directories, block the metadata server first. Risk: Podman 5 supports the platform's cgroup v1 only as a
   deprecated path.
3. **Docker Engine 29.9 as root in one job (V2).** Current software, cgroup v1 support documented to at least
   2029. Needs a new adapter, an explicit capability list on every run, its own time-limit handling, and
   cannot build images with `RUN` steps. Prefer it over 2 only if the deprecated Podman path is judged too risky.
4. **bubblewrap sandboxes (V5).** Simplest; namespaces and read-only binds work and a time limit kills the
   tree. Gives up the stage image as a unit; the agent's tools inside it are untested.
5. **One Cloud Run job per step (V6).** Hardest isolation, but untested, a different architecture and slow
   stages. See the next section.

Not recommended: Podman 4.3 (works, old), Podman 6 and any crun (refuse the platform's cgroups), generation 1
(refused for jobs), Container-Optimized OS (no package manager, no ZFS).

## Snapshots

1. **Podman overlay volume with an explicit upper layer (S5, `-v base:/work:O,upperdir=...,workdir=...`).** Measured in P11: the base is never written, reset is deleting a directory (0.01 s), the take reads the upper layer, it works with the factory's flags and a numeric user, and two containers can share one base. Upper and work directories on a tmpfs (or the ephemeral disk). Open: tools other than busybox `mv` for directory renames, and opaque directories.
2. **Kernel overlayfs mounted by the factory, upper layer on a tmpfs (S1).** Same idea without podman doing the mount; reset 0.01 s. Use it if the engine is not podman.
3. **Overlayfs on the ephemeral disk (S2).** Reset 0.06 s; 10 GiB, 210 MB/s ceiling. For large checkouts.
4. **Plain copy or rsync (S3).** 1.6 s reset per GiB, simplest, the fallback. Both a copy and an overlay need memory for the base.

Hard links, reflinks, loop images, btrfs (also on the ephemeral disk's device) and ZFS do not work here.

## The per-step design (option 5) in more detail

**Can the ephemeral disk be shared or remounted?** No, by the platform's own description (CLI help, not
tested): "data is not shared between instances and all data will be lost when the instance it is on is
terminated". Each task gets its own disk, created with the task and destroyed when it ends; a later execution
or a retry starts empty. Several containers of the *same* task can mount one volume, which helps a
factory-plus-worker layout inside one job but not a hand-over between steps.

State between steps therefore has to travel another way:

| Carrier | Status | Fit |
|---|---|---|
| Cloud Storage bucket mounted through Cloud Storage FUSE (`cloud-storage` volume) | documented, not tested | Shared and persistent, slow for many small files. Suits tarballs: pack the checkout at the end of a step, unpack at the start of the next (packing 1 GiB took 1.3 s; transfer times unmeasured). |
| NFS volume (`nfs`, `server:/path`) | documented, not tested | Shared, POSIX; needs a reachable NFS server, which the sandbox lacks. |
| `in-memory` volume | documented | Not shared; counts as memory. |
| Git plus the hosting service | works today | The factory already commits and pushes every stage; a step could clone and sync from scratch at the cost of a virtualenv rebuild. |
| Object store or registry (tarballs, images) | not tested | Bucket access by the probing identity was seen once (the build-source bucket); a new bucket under the enforced service controls is untested. |

**Estimated probability, from judgement (nothing in this design was run):** about 55 to 60 % that a small story
runs end to end this way, about 35 % that it is fast and robust enough to be pleasant. The links and my
estimate for each:

| Link | Chance |
|---|---|
| A bucket can be created or used and a job can mount it | about 75 % |
| Moving a packed 1 GiB base each way is fast enough | about 80 % |
| The factory can start and watch job executions (needs a credential with `run.jobs.run` and somewhere long-running to live) | about 65 % |
| A step job runs the agent without an engine | about 85 % |
| The stage image reaches the job (registry push unresolved; install at start costs tens of seconds) | about 70 % |
| The factory's code can be adapted (`StageEnvironment` is an interface, but job execution, bucket hand-over and a take from an archive are real work) | about 75 % |

Multiplied the links give 15 to 25 %; the higher figure assumes most failures are cheaply fixable and that
only the factory's own start-up and the registry push could block it. Speed will be poor: a job start took 1.4
to 2.7 minutes in the probes, so a story with about seven stages and their checks spends 15 to 25 minutes on
start-up alone. The gain over option 2 is restart behaviour: state lives in the bucket and git, so a failure
costs one step, not the whole checkout. Cost and quota under many short jobs are unknown.

Option 2 carries fewer unknown links (about 75 %), but a restart loses the checkout.

**Probes that would raise the confidence** (decided on 2026-10-31 not to run them now): a bucket with two jobs,
one writing a 1 GiB tree through the mount and one reading it back, timing both with FUSE and with a plain
copy; opencode in a job against the model proxy; whether a job can start another job under a service account
that holds only `run.jobs.run`.

## Caveats for every option

- The factory itself, its test suite and the agent runtimes were never run inside a job; every verdict is about
  the environment, not about a story passing.
- A job restart loses the checkout and the base; the factory's state is in git and the hosting service.
- The registry push is unresolved, so tools are installed at start-up (tens of seconds per start).
- Cloud Run services were not tested; all findings are for jobs.

## Suggested order of work

1. Ask for the VM route and the platform answers in `offline-planning.md` in parallel.
2. If the VM stays closed: option 2 with S5 (podman overlay volumes) as one feature, S3 (copy) as the fallback (a "job profile" for `PodmanRuns`, an overlay
   `Snapshots` adapter, a metadata-block step with a preflight proof, a start-up recipe), built by the factory
   itself, public defaults unchanged.
3. Before relying on it, run one real story in a job and add what it shows to `results/`.
