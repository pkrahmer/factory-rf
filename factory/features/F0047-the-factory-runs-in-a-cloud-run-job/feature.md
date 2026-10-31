# The factory runs in a Cloud Run job

## Goal

The factory runs on a VM with ZFS and rootless Podman. A managed sandbox such as a Cloud Run job gives neither: no ZFS, no loop devices, no rootless engine, a memory-backed root filesystem, no direct internet, and a metadata server that a container can reach (and so can mint the job's tokens). `planning/cloud-sandbox/` measured on 2026-10-31 what that sandbox does offer: Podman 5.4 with runc as root on the host network with every control the factory uses (`--timeout`, `--pids-limit`, `--memory`, `--cap-drop`, bind mounts), a copy of a tree in 1.6 s per GiB, opencode 1.19.3 running a real task against an OpenAI-style model API behind an OAuth2 client-credentials grant. This feature adds the options that make the factory run there, each off by default so that the VM path is unchanged: a snapshot adapter that copies a directory, a container profile for a root engine on the host network, a preflight proof that a container cannot reach the metadata server, a refresher that keeps a short-lived bearer token in the login file, a split of the factory's code repository from the project it builds (the credential helper stops sending the project's token to other hosts), and a start script that turns a bare Debian job into a running instance, with the operator guide's chapter for it. For the operator who runs one instance in a job with a long task timeout and a nightly restart; the factory's recovery (the claim, the lease, the crash cap) already covers the restart. Done when every story below is merged and `make check` is green.

The hand-over note for whoever builds this is `planning/cloud-sandbox/HANDOVER-F0047.md`: read it before the first story. The evidence is in the rest of that folder.

## Scope

- `FACTORY_SNAPSHOTS=copy` and `FACTORY_SNAPSHOT_BASE`: `CopySnapshots`, which `FakeSnapshots` becomes a thin subclass of (S0001).
- `FACTORY_CONTAINER_PROFILE=job`: the `podman` words of a root engine on the host network, runc, fuse-overlayfs storage, no `--userns=keep-id` (S0002).
- The preflight item `metadata-block` for the job profile (S0003).
- The job profile without `fuse-overlayfs`: podman's native overlay on a tmpfs the start script mounts (S0009, S0006).
- `python -m factory.entry.refresh_token`: client-credentials token into the login file, atomically, before it expires (S0004).
- The credential helper's host check and `vm/setup.sh --code-url`: the factory's code from one repository, the project from another (S0005).
- `vm/job-start.sh` and the operator guide's chapter *On Cloud Run*: first boot installs the tools, builds the stage image, blocks the metadata server, starts the refresher and `factory-run` (S0006).
- The opencode runtime's lockdown with a company provider: `enabled_providers` and three environment switches (S0007).
- `FACTORY_IDLE_SHUTDOWN_ACTION=exit`: the idle shutdown ends `factory-run` with exit 0 instead of powering the machine off, which ends a job's execution (S0008).

## Out of scope

- Creating the job, its secrets, its schedule or its network: the operator's and the platform's (the operator's deployment tooling and pipelines); this feature documents what the job needs.
- Podman's overlay volumes (`-v base:/work:O,upperdir=...`) as a snapshot mechanism: measured good in P11, a later feature (a second `Snapshots` adapter and a mount change in `ContainerRuns`).
- A pre-built stage image pushed to a registry (the push is unresolved in the sandbox); the image is built at start-up.
- Rootless mode, `--userns=keep-id`, slirp4netns, pasta and a bridge network in the job profile: none works in the sandbox.
- A base URL for the hosting client (GitHub Enterprise on github.com needs none), a hosting-token refresher, and any change to the Claude Code runtime or the records contract.
- A fork of opencode: a company fork of opencode was read on 2026-10-31 (`planning/cloud-sandbox/`); its login is an interactive browser flow and its hardening lives on a newer line, so the factory keeps upstream opencode 1.19.3 and sets upstream's own switches (S0007).
- Any company value in this repository, a test or a document: tests and documents use `example.invalid` and made-up ids.

## Stories

The build order; start one at a time, the next when the one before is archived in `done/`.

- S0001: A snapshot adapter that copies a directory
- S0002: The container profile `job`
- S0003: The preflight proves that a container cannot reach the metadata server
- S0009: The job profile stores images with the native overlay (added on 2026-10-31 after P16)
- S0004: A refresher keeps a bearer token in the login file
- S0005: The factory's code comes from another repository than the project, and the credential helper answers only its host
- S0008: The idle shutdown can end the factory's process instead of powering the machine off (built before S0006, whose script sets it; added on 2026-10-31)
- S0006: One script turns a bare job into a running instance
- S0007: The opencode runtime limits what opencode may load and contact when it uses a company provider

## The human's changes

None. Checked against `factory/pipeline.yml`: the coder writes `src/*`, `template/*`, `claude/*` and `vm/*` (S0005 and S0006's scripts and `vm/Dockerfile` are under `vm/`), the tester `tests/*`, the documenter `README.md` and `docs/*`. The refresher runs as `python -m factory.entry.refresh_token`, so `pyproject.toml` gets no new script, and no dependency is added (the standard library's `urllib` does the HTTP).

## Decisions taken for the human

1. Every option is off by default; each story's first criterion is the unchanged default (all).
2. The copy adapter is `FakeSnapshots` promoted: the logic moves to `CopySnapshots`, which compares files in chunks instead of reading whole files into memory, and `FakeSnapshots` stays as a subclass so that the suite's six users and their tests change not at all (S0001).
3. In the job profile the container runs as the job's root with `--cap-drop=all`, as in the measured runs; no `--user` is added. The probes ran agents that way (P10), and a numeric user needs owned bind directories for no gain here (S0002).
4. The profile's global podman options (`--runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay --storage-opt overlay.mount_program=/usr/bin/fuse-overlayfs`) apply to every podman call the factory makes, queries included: the default storage fails over an overlay root and crun fails on a hybrid cgroup layout (P2, P3, P11) (S0002).
5. `--network=host` and `--http-proxy=false` in the job profile: no bridge reaches the outside, and podman would otherwise copy the job's proxy variables into every container (P2, P2b) (S0002).
6. A container that can reach the metadata server can mint the job's tokens (P2b). The rule that stops it is part of the start script, and the preflight proves it from a container, as the stop of a machine that fails it (S0003, S0006).
7. The bearer token is refreshed by a separate process into the login file the runtimes already read at every call; no runtime changes. It is refreshed every ten minutes (the human, 2026-10-31; a token that lives under twenty minutes at half its life). A container mounts the file when it starts and reads it once, so a half-life rule on a one-hour token would have left a run that starts just before a refresh thirty minutes of token for a forty-minute stage; the fixed interval leaves fifty (S0004).
8. The client secret never appears in a log line, an error message or an environment of a child process; it is read from a file that Secret Manager mounts (S0004).
9. The credential helper answers only for the host of `FACTORY_REPOSITORY_URL`, and the code clone of `--code-url` runs without credentials, so the project's token is never offered to the code repository's host (S0005).
10. The start script installs Debian's packages by name, not by exact version: a mirror keeps only the current version, so a pin would break the next start. runc comes from the upstream release with its published SHA-256 (S0006).
11. Everything lives in memory: the job's size must hold the checkout, the base copy, the engine's image layers and the stage image (about 16 GiB for the factory's own repository). The operator guide says so and gives the measured numbers (S0001, S0006).
12. A model with price 0 (an on-prem model) makes the per-run budget inert: opencode reports cost 0. The time limit is then the only bound. The operator guide says so (S0006).
13. The factory's own hardening of opencode stays small: the container is the boundary (no credentials in its environment, the metadata block, `--cap-drop=all`, the proxy's allow-list, the take). A URL guard on `webfetch` is not added: the shipped agents have no `webfetch` tool (S0007).
14. With a provider file opencode may load only that provider, fetch no public model list, not update itself and load no default plugin. These switches depend on the provider file because without it opencode needs its public model list; the check that opencode contacts nothing else at start is a probe in the sandbox, not a story. Run on 2026-10-31 (P14, `planning/cloud-sandbox/capabilities.md`): opencode 1.19.3 accepts `enabled_providers` without a word, the run works, and with the switches the one vendor host, `models.opencode.ai` (the public model list; not `models.dev`), is no longer contacted; `OPENCODE_DISABLE_MODELS_FETCH` is the switch that does it, the other two changed nothing observable in that task and stay as upstream's documented guards. What stays with every run, switches or not, is `registry.npmjs.org` (four connections at a run's start, most likely the provider's npm package the provider block names; an inference). A stage image that pre-installs that package, so that a run contacts no registry, is a candidate for later, not a story here (S0007).
15. The nightly restart of the job is accepted as it is (the human, 2026-10-31): a restart in the middle of a stage charges one crash to the work item in flight, and after `crash_cap` crashes (two by default) the work item waits for the human's answer, so a story in flight on two nights waits once. S0006's chapter says so. A stop between stages before the restart, like the idle shutdown, is a candidate for later, not a story here (S0006).
16. The repository split keeps the names of these stories, `--code-url` and `--code-ref` with `FACTORY_CODE_URL` and `FACTORY_CODE_REF` (the human, 2026-10-31); the multi-project plan in `planning/v1.2-candidates.md`, whose step 1 this split is, takes the same names (S0005, S0006).
17. The stage image's Debian packages follow the base image's release instead of exact versions (the human, 2026-10-31). The job rebuilds the image at every start, and Debian's mirror keeps only a package's current version, so a pinned version breaks the build at the next point release (P15 found today's pins resolving and the build taking 169 s). The base image stays pinned by digest, which fixes the Debian release; `uv`, Claude Code and opencode keep exact versions, because they shape a stage's result and their registries keep every version. A move to a new Debian release stays a deliberate change of the digest. This changes the rule of 2026-10-16 for the operating system's packages, and the VM's image with it (S0006).
18. The idle shutdown gets a second action, `exit`, for the job (the human, 2026-10-31, for parity with the VM): `systemctl poweroff` cannot work in a job, so without it an idle job is billed until its task timeout. `exit` sets the same stop flag a `SIGTERM` sets, so the loop ends cleanly after the tick in progress and `factory-run` returns 0, which ends the execution; the job's schedule or the operator starts it again, as an operator starts a stopped VM. The default stays `poweroff`; S0006's script sets `exit` where the job gives no value. Waking the job when work arrives is not in this feature (`planning/v1.2-candidates.md`, *One job per repository*) (S0008, S0006).
19. Decision 4 is corrected by measurement (P15, P16, 2026-10-31; decided for the human as unavoidable): podman's storage in a job uses the native kernel overlay on a tmpfs, not `fuse-overlayfs`. With FUSE the suite took 601 s (eight minutes are `check`'s limit), with the native overlay 182 s; the image build 199 s and 107 s. The factory's words drop the mount program (S0009), and the start script mounts the tmpfs at podman's storage root (S0006). The price: the image layers live in memory (the job's cgroup peaked at 5.4 GiB in P16).
20. At work the factory's code comes from the public factory-rf on github.com, cloned without a credential (measured in P15 to P21), at a tag or commit the job must name: `FACTORY_CODE_REF` is required and has no default, so that nothing pushed to factory-rf's `main` (by its own factory, for example) reaches a job unseen (the human, 2026-10-31). An internal copy of the code with its own token is not built (S0006).
