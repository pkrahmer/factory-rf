# The stage image carries only what runs

## Goal

After F0049 the base image is 1.58 GB, and about 1 GB of it never runs. Measured on factory-vm on 2026-11-04: npm's download cache stays in the image (441 MB in `/root/.npm`); opencode's package brings two builds of its executable, the normal one and a "baseline" one for CPUs without AVX2 (178 MB each); the factory's Node stays in `/opt/factory/node` although it serves only npm's install (201 MB); and both agent runtimes are installed, although every instance runs exactly one, the one `FACTORY_AGENT_RUNTIME` names (`vm/setup.sh --runtime`, `vm/job-start.sh`). An instance at work without a Claude key would carry Claude Code for nothing. This feature builds the base image for one runtime and leaves out what only the install needs: about 0.58 GB with Claude Code and 0.51 GB with opencode. It also moves both runtimes to their current releases, and makes every cost record show the image sizes, the free disk, the memory and the CPU, so that the next growth is seen from a distance. Two smaller findings of the same week go with it: a stop always says why and writes its log line once, and the factory fetches once per iteration. Done when every story below is merged and `make check` is green.

## Scope

- The base image installs only the runtime its build names, keeps only what that runtime runs, and leaves no download cache, no Node and no build leftovers behind (S0001).
- The pins of Claude Code and opencode move to their current releases (S0001).
- `vm/job-start.sh` builds for its own runtime; the operator's build command on a VM names the runtime (S0001).
- The object `machine` in every completed cost record: the base image and the project layer, the free space of the image store and of the dataset, the memory peak since boot and the memory total, the run's CPU time and its waits for a CPU and for memory; the build's log line with the sizes and the count of warnings; records contract 4.2 (S0002).
- A stop's detail is never empty; a command cut off by the factory's own stop is not judged; a standing stop writes its log line once (S0003).
- One fetch per iteration of `factory-run` (S0004).

## Out of scope

- Another base than `python:3.12-slim-bookworm`: Debian, Python with uv, and git with Perl are about 270 MB and needed.
- Removing images of other instances, or of instances that no longer exist: that stays the operator's act.
- The project's stage file (F0049): it builds on whichever base the instance has.
- A memory peak per run: it needs sampling during the run, since the kernel's peak cannot be reset before 6.12.
- Limits or warnings on the new measures: first the normal values are watched.
- A breakdown per container or per instance: the measures count every container of the factory user.
- A heartbeat of the instances: a Cloud Run job needs none, and for VMs it belongs to a later instance management harness (the human, 2026-11-04).

## Stories

- S0001: The base image holds only the instance's runtime, with nothing left from its install
- S0002: The cost records show the image sizes, the free disk, the memory and the CPU
- S0003: A stop says why, and is logged once
- S0004: One fetch per iteration

## The human's changes

After the merge, on factory-vm: rebuild `factory-stage:vm` with the runtime argument, renew `image-id`, and set the two version lines of `/srv/factory/vm/factory.env` (`FACTORY_CLAUDE_VERSION`, `FACTORY_OPENCODE_VERSION`) to the new pins, editing only those lines.

A leave, for S0001: its tester may change `tests/test_stage_image.py` to the image S0001 describes (its rows pin one build stage and both runtimes), and in `tests/test_vm_job_start.py` the row of the build command, for the runtime argument; nothing else in that module.

## Decisions taken for the human

1. **One runtime per image, chosen at build.** The build argument `AGENT_RUNTIME` (`claude` or `opencode`) has no default, so a build that does not name it fails at once rather than carrying the wrong runtime. Reason: every instance already names exactly one runtime, and switching it already means running the setup again; the preflight's version check and agent-run probe stop an instance whose image holds another runtime. The human, 2026-11-04.
2. **The install happens in a throwaway build stage.** Node, npm and npm's cache live only in a first stage; the image copies from it only what the runtime runs. Reason: nothing runs Node since F0049 decision 6, and a cleanup inside the same layer would still leave Node. Taken for the human, 2026-11-04.
3. **The runtimes move to their current releases**: Claude Code 2.1.318 (2026-11-03) and opencode 1.19.5 (2026-10-28). Node stays at 22.23.4, the newest 22.x, since it only runs the install. The human asked for current versions, 2026-11-04.
4. **The memory peak is the slice's high-water mark, and its name says so.** `memory_peak_since_boot_bytes` is the kernel's `memory.peak` of the containers' user slice. Reason: a peak per run would need sampling during the run, and the human judged it not worth the effort; the name keeps the value from being read as the run's own peak. The human, 2026-11-04.
5. **The machine's measures sit in one object, and the CPU and the waits are the run's own.** `machine` holds all nine values, so the run's own measures stay apart from the machine's state; `cpu_seconds`, `cpu_wait_seconds` and `memory_wait_seconds` are differences of the kernel's running totals between the run's start and end. Reason: the waits say whether the machine is too small, which the peak alone does not; the totals need no sampling. The human, 2026-11-04.
