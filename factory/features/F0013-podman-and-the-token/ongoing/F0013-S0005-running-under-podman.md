---
stage: tests
pr: 186
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Running under Podman

## Assignment (as of log entry 1)

Podman, not Docker Desktop, is the container runtime at the human's work, and the first start (plan step 2) runs under both. The probe of 2026-10-17 (`planning/overnight/podman-probe-2026-10-17.md`) ran v1.1's image under rootless Podman 5.8.3 on Windows: the build, the start, the users, the volumes' owners and modes, `sudo`, the health check and `podman restart` work as under Docker. Three things differ, and the operator guide says none of them: after `podman machine stop` and `start` the container stays `Exited (0)`, and on Windows nothing restarts it: enabling Podman's `podman-restart.service` in the machine fails with `Access denied`, and an `unless-stopped` container stayed stopped (fault 2, tested after the pre-check); `podman-compose` 1.5.0 cannot build this compose file on Windows, while `podman compose` with the docker-compose v2 binary as its provider can (fault 3); and the disk record sees the machine's virtual disk, not the host drive (fault 4, as under Docker Desktop). The human's answers (2026-10-17): the operator guide gets a Podman section on the restart (what was tested on Windows, and the restart service on a Linux host) and on the Compose provider, and a section that names the runtimes that passed and a shared Linux host as the team setup. This story is documentation only: nothing under `src/`, `image/` or `tests/` changes, so the tester writes no test and the coder changes nothing; the restart on a Linux host was not tested and is left to the first start on such a host. The docs criterion carries the text (FEATURE decision 13).

## Interface

None: no code, no image file and no test changes. The documents the documenter changes are `docs/operator-guide.md` and `docs/decisions.md`.

## Acceptance criteria

1. Nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes; the tester and the coder each end with an entry saying so. The restart under Podman on Windows was tested by hand on 2026-10-17 (the probe's section "The restart service, tested"); the restart service on a Linux host is not testable here, and the observation of criterion 3 is left to the first start on such a host.
2. `make check` stays green.
3. docs: the operator guide gets a section *Container runtimes*, after *The container: compose, entrypoint and health check*, with this content:
   - **The runtimes.** The image and the compose file run under Docker Desktop and under rootless Podman with the docker-compose v2 binary as its Compose provider (probe of 2026-10-17, Podman 5.8.3 on Windows); Rancher Desktop with its moby engine is expected to work like Docker but is untested; a Mac is not probed. For a team, the setup is one shared Linux host (Docker Engine, or rootless Podman with the restart service below) that runs every instance, each its own compose project, rather than a runtime on every laptop.
   - **Podman: the commands.** Every `docker` command of the guide works with `podman` in its place (`podman build`, `podman exec`, `podman compose -f image/compose.yml up -d`); inside the container the users, groups, modes and the token's folder are the image's, while on the machine the named volumes belong to sub-ids that are invisible inside.
   - **Podman: the Compose provider.** `podman compose` hands the compose file to an external provider. Use the docker-compose v2 binary (standalone, Apache 2.0), named with `PODMAN_COMPOSE_PROVIDER` or `compose_providers` in `containers.conf`; `podman-compose` 1.5.0 cannot build this compose file on Windows (`no Containerfile or Dockerfile specified or found in context directory`, from `context: ..` with `dockerfile: image/Dockerfile`).
   - **Podman: the restart.** `restart: unless-stopped` stays in the compose file; it brings the container back after a crash and after `podman restart`, but not after the Podman machine or the host restarts. Docker Desktop restarts it by itself once it runs (its "start when you sign in" setting). On Windows, under Podman, nothing restarts the factory after a machine or host restart (tested on 2026-10-17): `systemctl --user enable podman-restart.service` in the WSL machine fails with `Failed to enable unit: Access denied`, and an `unless-stopped` container stayed `Exited` after `podman machine stop` and `podman machine start`. The operator runs `podman machine start` and then `podman compose -f image/compose.yml up -d`, by hand or as a scheduled task at logon. Until then the container stays `Exited (0)`: no tick runs, nothing is claimed or pushed, the health check does not run, so nothing shows unhealthy, and a lease the instance held expires; once started, the factory goes on as after any restart (see *A restart during a stage*). On a Linux host, `podman-restart.service` (it starts the containers matching `should-start-on-boot=true`) with `loginctl enable-linger` is the documented way; this was not tested here, and the guide says so. The morning observation, on a Linux host: with the service enabled and linger on, a restart of the host brings the container back `Up` in `podman ps -a` (not observed yet).
   - **Podman: the disk.** The disk record and the stop `disk_low` see the Podman machine's virtual disk, not the host drive, as under Docker Desktop; *What the container cannot see* names both runtimes.
   The section *The health check and the restart policy* points to the Podman restart. The decision log records the runtimes and the provider as the human's answers of 2026-10-17 from the probe, that the probe's build under Podman (Buildah behind the Docker-compatible API, the image's owners and modes as built) is the check of Buildah's defaults, that on Windows nothing restarts the factory after a machine or host restart (the restart service cannot be enabled, tested) so the operator starts the machine and then Compose, that the restart service on a Linux host is untested, and that Rancher Desktop is named untested because the probe did not run it. No other document changes, the guide uses no word the document check refuses, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
grep -o "podman-restart.service\|docker-compose v2\|Rancher Desktop\|Exited (0)\|should-start-on-boot" docs/operator-guide.md | sort -u
```
Expect: five lines, one per term, in any order: `podman-restart.service`, `docker-compose v2`, `Rancher Desktop`, `Exited (0)` and `should-start-on-boot`.

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: "None" is right for a documentation-only story. It names the two documents the documenter changes (`docs/operator-guide.md`, `docs/decisions.md`). No code behaviour is stated, so no Interface comment lacks a criterion.
   - Criteria: criterion 1 (nothing under `src/`, `image/`, `template/`, `claude/` or `tests/` changes) can be checked against the diff. The docs criterion names the section, its position, the five sub-topics and the decision-log content, and gives the exact strings to look for. No code rule states a limit or a rejected input, so there is no failing side to test. The tester has nothing to test (the Assignment says so) and ends with an entry saying that.
   - Demo: both commands can be run. The grep with `-o` and `sort -u` prints five lines if the five terms are present, and the BRE parentheses in `Exited (0)` are literal. `check_documents` is expected to print `documents ok`. Each Expect line can be checked against the output.
   - Architecture: no layer or interface is touched, and the story changes documents only.
   - Scope: the story is inside FEATURE decisions 3 to 5, 13 and 15 (faults 2, 3 and 4). It leaves out the items listed under "Out of scope": the image pins, a Mac and SELinux, `podman-compose` as a provider, and a test of the restart.
