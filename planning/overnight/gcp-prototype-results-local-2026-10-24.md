# Prototype results: local Hyper-V VM, not GCP (2026-10-24)

The GCP runbook's (`planning/overnight/gcp-runbook-2026-10-24.md`) sections 4 to 6, run by Claude through `multipass exec` on the local VM of `planning/overnight/local-vm-runbook-2026-10-24.md`. The GCP-only parts (NAT, IAP, no service account, the metadata server) are not covered.

## The machine

- Multipass 1.17.0 on Windows 11, driver Hyper-V Host Compute System (`hcs`); the VM `factory-vm`: 4 cores, 8 GB, 60 GB disk.
- Ubuntu 24.04.5 LTS, kernel `6.8.0-147-generic`, `zfs-2.2.2-0ubuntu9.5` (module the same), `podman version 4.9.3`.
- The pool `tank` on a 30 GB file, `/var/lib/factory-pool.img` (`ashift=12`, `compression=lz4`, `atime=off`); `tank/factory/vm` mounted at `/srv/factory/vm/work`; `zfs allow -u factory snapshot,destroy,rollback,diff,mount` on it. `/etc/subuid` and `/etc/subgid` hold `factory:165536:65536` from `useradd`.

## The answers

1. **The rollback of a mounted dataset works as the user `factory` through `zfs allow` alone.** `zfs rollback -r tank/factory/vm@base`: status 0, 0.010 s; the deleted file is back, the added ones are gone. **The `sudoers` fallback is not needed** on Ubuntu 24.04's ZFS 2.2.2. (The shell's working directory was inside the dataset while it rolled back.)
2. **The base moves forward** (`zfs destroy` then `zfs snapshot` on `@base`): status 0, 0.017 to 0.020 s.
3. **`zfs diff -FH`** gives the expected lines, with a directory line `M / <path>` for each changed folder: `-  F .../checkout/a`, `+  F .../checkout/b`, `+  F .../home/c`.
4. **`--userns=keep-id`:** the files a container writes belong to `factory` (uid 1001) on the host.
5. **Podman's time limit:** `podman run --rm --timeout 3 ... sleep 30` ends after 3.04 s with **status 255**, not 137. The factory's code (`KILL_STATUSES = {137, -9}` in `factory.adapters.agent_launch`, read by `factory.adapters.podman_runs` and the runtimes' `in_container` reading) would read it as a failure with status 255, not as `time_limit`. A story is needed before the first stage on a VM.
6. **Container start**, `podman run --rm alpine:3.20 true`: 0.150 s and 0.144 s (the image already pulled).
7. **A `:ro` mount** cannot be written: `touch: /upstream/x: Read-only file system`.
8. **The sync** (`git init` once, `fetch` from the read-only bare repository, `checkout -f FETCH_HEAD`) in `alpine/git:v2.45.2`, a small public repository (`octocat/Hello-World`; the runbook's `pkrahmer/factory-timeline` is private and needs a token): warm 0.18 s. A commit inside the container shows in `zfs diff` under `checkout/.git/`, and the rollback (0.011 s) removes it.

## Found on the way

- `/srv/factory/vm` belongs to root when ZFS makes the mount point's parent; the bare repository's folder needs `chown factory:factory /srv/factory/vm` (the setup script's `folders` step must do it).
- `sudo -iu factory bash -c '...'` re-parses the command through a login shell; a script file is the reliable way to run a block as `factory`.
- The runbook's section 6 names a private repository; it should name a public one.

## The plan's target

The start of a stage (rollback, sync, advance, container start) took well under 1 s here on a small repository, against the plan's target of under 20 s. factory-rf's own sync (`uv sync --frozen` in the sync container) is not measured yet; it comes with the first stage on the VM.
