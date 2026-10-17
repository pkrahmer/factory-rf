# Podman probe of v1.1's image (2026-10-17, F0013's input)

Podman 5.8.3 CLI (`winget install RedHat.Podman`, the human's go), the default rootless machine (WSL, 10 CPUs, 2 GiB), v1.1 at `68386ca0` in a throwaway clone; the image pins unpinned in the clone only (they are the human's, before step 2). Instance `probe`, a dummy token file, a repository that does not exist. Script: the session's `scratchpad/podman_probe.sh`.

## What works under rootless Podman (provider: docker-compose v2)

- Build: 42 s. Up: the container starts, the entrypoint installs the agents and settings, prepares `/state/runs`, writes the disk record and reaches the expected `repository_unavailable` stop.
- Users and groups: `factory` 1000, `agent` 1001, both in `factory-work` 1002; inside the container the named volumes have the image's owners and modes (`/work` 2775, `/home/agent/.claude` 3775, `agents/` 2755, `settings.json` 0644); on the machine they map to sub-ids (525287), invisible inside.
- `sudo -n -u agent` works; a file the agent makes in `/work` is `1001:1002`, group-writable. The agent cannot rewrite `settings.json` (S0025) and can add its own files.
- The healthcheck runs (`starting`, then the stop's text, exit 1); the restart policy reads `unless-stopped`; `podman restart` brings it back.

## Faults

1. **The agent can read the hosting token, under Docker Desktop too.** Compose ignores a file secret's `uid`, `gid` and `mode` outside Swarm mode (its own warning); the file is a bind mount with the host file's permissions, on Windows `-rwxrwxrwx 0 0`. Under Podman `sudo -u agent cat /run/secrets/hosting-token` printed the token; a minimal compose file on Docker Desktop showed the same mode and uid 1001 reading it. The image's design (`image/compose.yml`: "The factory's user (uid 1000) alone reads the token: mode 0400") does not hold on either runtime. A security fault for v1.1, not a Podman one.
2. **No restart after the machine restarts.** After `podman machine stop` and `start` the container stayed `Exited (0)`: `unless-stopped` needs Podman's restart service (`podman-restart.service`) or a Quadlet unit inside the machine. Docker Desktop restarts it on its own.
3. **`podman-compose` 1.5.0 cannot build our compose file on Windows** (`no Containerfile or Dockerfile specified or found in context directory`: `context: ..` with `dockerfile: image/Dockerfile`). `podman compose` with the docker-compose v2 binary as provider works. The operator guide should name docker-compose v2 (standalone, Apache 2.0) as the provider.
4. Known, both runtimes: the disk record sees the VM's virtual disk (1023.8 GB free), not the host drive; the heartbeat's `df -h /c` on the host stays the guard.
5. Not Podman: the image pins are placeholders (`@sha256:000…`, `=0~unpinned`), so the image builds nowhere until the human pins it (step 2).

Not probed: a Mac (no machine here); Podman without a Compose provider; a real run with a token.

## The human's answers (2026-10-17)

- Fault 1: the token file is mounted into a folder only the factory user can enter (for example `/home/factory/.secrets`, mode 0700, made in the image), so the agent cannot traverse it whatever the file's own mode; the first story of F0013, before any real run with a token.
- F0013 also takes faults 2 (the restart service in the Podman machine, operator guide) and 3 (docker-compose v2 as the provider, operator guide), drafted from this record.
- The probe's container, volumes and images in the Podman machine and its clones were deleted.

## The restart service, tested (2026-10-17, after F0013's pre-check)

The machine's `podman-restart.service` (a user unit) starts `podman start --all --filter should-start-on-boot=true`; it was disabled. `systemctl --user enable podman-restart.service` inside the WSL machine failed with `Failed to enable unit: Access denied` (linger is on), and an `unless-stopped` test container stayed `Exited` after `podman machine stop` and `start`. On Windows, therefore, nothing restarts the factory after a machine or host restart: the operator runs `podman machine start` and then `podman compose -f image/compose.yml up -d` (by hand, or as a scheduled task at logon). On a Linux host the service with linger is the documented way; not tested here.
