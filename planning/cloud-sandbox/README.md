# Cloud sandbox findings

What a managed, locked-down container platform (Google Cloud Run jobs, second-generation execution
environment, in a corporate sandbox project behind an egress proxy) can and cannot do for the factory's
isolation model, measured on 2026-10-31. The factory's current design needs a ZFS dataset, rootless Podman
and a normal Linux host; none of that exists here, so this folder records which replacements were
tested, what worked, what failed and why, so that later planning can proceed from facts and offline.

Nothing here names the company, the project, the proxy or any account. The probe scripts take every
environment-specific value from environment variables, and the stored results are sanitised
(`<proxy-host>`, `<project>`, ...). The platform's own names (Cloud Run, Debian, runc, the nftables table
`emerald_isolation` that the platform installs) are kept: they are facts about the platform.

## Read in this order

| File | What it holds |
|---|---|
| `capabilities.md` | The capability matrix: what the environment supports, what it refuses, with the evidence for each line. Start here for a yes/no answer. |
| `variants.md` | Every plan variant that was tested (Podman, Docker, newer runtimes, engine-free sandboxes, snapshot replacements, the ephemeral disk), its verdict, the flags that work, and what each would mean for the factory's code. |
| `recommendations.md` | The ranked setups (platform, isolation, snapshots), the per-step design with the ephemeral-disk sharing facts and a probability estimate, and a suggested order of work. |
| `offline-planning.md` | The numbers to plan with, a decision guide, the list of what was NOT tested, and how to re-run a probe when the platform changes. |
| `results/` | The raw, sanitised output of every probe run (`p1` to `p12`). Quote these, do not trust summaries over them. |
| `probes/` | The scripts: `run_probe.sh` (create a throwaway job, run it once, print its log, delete it), `lib.sh` and one script per question. |

## The short version

- **A container engine works, but only as root inside the job, on the host network.** Podman 5.4.2 with
  runc, and Docker 29.9.2 with its bundled runc 1.5.2, both run containers with memory, pids, read-only
  and capability controls. Rootless mode, `--userns=keep-id`, slirp4netns, pasta and bridge networking
  with outbound access do not work.
- **The kernel is the constraint, not the engine.** The job's "root" lives in a user namespace with a
  reduced capability set (no `CAP_MKNOD`), `NoNewPrivs` is set and the cgroup layout is hybrid (v1
  controllers plus an empty v2 mount). Podman 6 and crun (any version, 1.30.1 included) refuse that
  layout; runc accepts it.
- **ZFS and loop devices do not exist**, but a kernel overlayfs works if its upper layer is on a tmpfs or
  on the ephemeral disk volume (real ext4, but capped at 10 GiB, 210 MB/s and 50k IOPS). That gives a snapshot replacement with a reset of 0.01 s and a diff for
  free (the upper layer).
- **The root filesystem is memory.** Everything written to `/` or `/tmp` counts against the job's memory
  (up to 32 GiB). An `ephemeral-disk` volume (ext4, at most 10 GiB per job) is real disk.
- **Containers can read the job's credentials** from the metadata server unless a firewall rule stops it;
  such a rule works and costs nothing the factory needs.
- **There is no direct internet.** All outbound traffic goes through the corporate proxy, which reaches
  the package indexes, GitHub, container registries and model APIs listed in `capabilities.md`.

## Reproducing a probe

```bash
export PROBE_PROJECT=<project-id>         # required
export PROBE_REGION=us-central1
export PROBE_IMPERSONATE=<service account to act as>   # optional
export PROBE_RUN_AS=<service account the job runs as>   # optional
export PROBE_CONNECTOR=projects/<host>/locations/<region>/connectors/<name>   # optional egress connector
export PROBE_PROXY=http://<proxy-host>:<port>          # optional, used by the scripts for downloads
planning/cloud-sandbox/probes/run_probe.sh <name> <image> <script> [cpu] [memory] [gen]
# example: the Docker probe
planning/cloud-sandbox/probes/run_probe.sh docker docker.io/library/docker:dind p1-docker.sh 2 8Gi
# the ephemeral disk probe needs the volume
PROBE_EXTRA_ARGS="--add-volume=name=scratch,type=ephemeral-disk,size=10Gi --add-volume-mount=volume=scratch,mount-path=/disk" \
  planning/cloud-sandbox/probes/run_probe.sh ephemeral-disk docker.io/library/debian:trixie-slim p8-ephemeral-disk.sh 4 8Gi
```

Each run creates one job `probe-<name>` with no ingress, no schedule and no retries, and deletes it when
the log has been read (also on failure). A run takes one to three minutes.

## Honest limits of these findings

- One day, one kernel version (6.9.12), one region, one project. Within that day two different kernel
  builds of 6.9.12 were seen (build dates 2026-09-25 and 2026-10-30, in the earlier ad-hoc probes; the
  stored `p6` run shows the first). The platform changes the kernel, the firewall and the policies
  without notice; re-run the relevant probe before building on a finding.
- The first runs of P1, P2, P4 and P5 contained mistakes in the probes themselves (a streaming test that
  never held memory, a nft keyword used as a chain name, a package that does not exist, an inverted
  message). The scripts in `probes/` are the corrected ones and `results/` holds the corrected runs; where
  a check is still weak, `capabilities.md` says so.
- Earlier, ad-hoc probes (podman 4.3.1 on Debian bookworm, podman 6.1.2, crun 1.8 and 1.21) ran before the
  harness existed; their conclusions are recorded in `variants.md` but their raw logs were not kept.
