# The factory shows what it runs and what it uses

## Goal

After F0049 the base image is 1.58 GB, and about 1 GB of it never runs. Measured on factory-vm on 2026-11-04: npm's download cache stays in the image (441 MB in `/root/.npm`); opencode's package brings two builds of its executable, the normal one and a "baseline" one for CPUs without AVX2 (178 MB each); the factory's Node stays in `/opt/factory/node` although it serves only npm's install (201 MB); and both agent runtimes are installed, although every instance runs exactly one, the one `FACTORY_AGENT_RUNTIME` names (`vm/setup.sh --runtime`, `vm/job-start.sh`). An instance at work without a Claude key would carry Claude Code for nothing. This feature builds the base image for one runtime and leaves out what only the install needs: about 0.58 GB with Claude Code and 0.51 GB with opencode. It also moves both runtimes to their current releases, and makes every cost record show the image sizes, the free disk, the memory and the CPU, so that the next growth is seen from a distance. Two smaller findings of the same week go with it: a stop always says why and writes its log line once, and the factory fetches once per iteration. Last, every agent run's transcript, which the dataset's rollback throws away today, is kept in a folder inside the site (a local directory on a VM, a Cloud Storage bucket mounted into a Cloud Run job), never on GitHub, and the cost record names it reliably and sums up the run's tool calls without any content. Done when every story below is merged and `make check` is green.

## Scope

- The base image installs only the runtime its build names, keeps only what that runtime runs, and leaves no download cache, no Node and no build leftovers behind (S0001).
- The pins of Claude Code and opencode move to their current releases (S0001).
- `vm/job-start.sh` builds for its own runtime; the operator's build command on a VM names the runtime (S0001).
- The object `machine` in every completed cost record: the base image and the project layer, the free space of the image store and of the dataset, the memory peak since boot and the memory total, the run's CPU time and its waits for a CPU and for memory; the build's log line with the sizes and the count of warnings; records contract 4.2 (S0002).
- A stop's detail is never empty; a command cut off by the factory's own stop is not judged; a standing stop writes its log line once (S0003).
- One fetch per iteration of `factory-run` (S0004).
- The transcript folder `FACTORY_TRANSCRIPT_DIR`, optional (old copies are removed by the site, not by the factory): each run's transcript kept there, compressed, named by its run id, referred to by the record with its path and SHA-256 (S0005).
- A summary of the run's tool calls without content in the cost record (S0006).
- The folder on the VM (`vm/setup.sh`) and the operator's steps for a bucket in Cloud Run; `vm/job-start.sh` checks the folder (S0007).
- A refused push or hosting call is retried and logged: a log line per counted handler error, retries of result pushes, git's reason in `PushFailed`, the GitHub client's backoff with PATCH, and a test of a hosting failure after the claim (S0008, from `planning/outage-2026-11-04.md`).

## Out of scope

- Another base than `python:3.12-slim-bookworm`: Debian, Python with uv, and git with Perl are about 270 MB and needed.
- Removing images of other instances, or of instances that no longer exist: that stays the operator's act.
- The project's stage file (F0049): it builds on whichever base the instance has.
- A memory peak per run: it needs sampling during the run, since the kernel's peak cannot be reset before 6.12.
- Limits or warnings on the new measures: first the normal values are watched.
- A breakdown per container or per instance: the measures count every container of the factory user.
- A transcript on GitHub, or in any place outside the site (feature decision 6).
- Creating a bucket or any other cloud resource: the operator's step, described in the guide.
- An evaluation of the transcripts: it runs later, inside the site.
- A capped event that tries again by itself every few minutes: the cap of three tries stays; a restart or a new commit wakes it (the human, 2026-11-04).
- A heartbeat of the instances: a Cloud Run job needs none, and for VMs it belongs to a later instance management harness (the human, 2026-11-04).

## Stories

The build order. S0008 comes right after S0002, because GitHub's incident of 2026-11-04 cost three finished runs to refused pushes (the human, 2026-11-04).

- S0001: The base image holds only the instance's runtime, with nothing left from its install
- S0002: The cost records show the image sizes, the free disk, the memory and the CPU
- S0008: A refused push or hosting call is retried and logged
- S0003: A stop says why, and is logged once
- S0004: One fetch per iteration
- S0005: A run's transcript is kept in the transcript folder
- S0006: The cost record sums up the run's tool calls
- S0007: The transcript folder is set up on the VM and in Cloud Run

## The human's changes

After the merge, on factory-vm: rebuild `factory-stage:vm` with the runtime argument, renew `image-id`, and set the two version lines of `/srv/factory/vm/factory.env` (`FACTORY_CLAUDE_VERSION`, `FACTORY_OPENCODE_VERSION`) to the new pins, editing only those lines.

A leave, for S0001: its tester may change `tests/test_stage_image.py` to the image S0001 describes (its rows pin one build stage and both runtimes), and in `tests/test_vm_job_start.py` the row of the build command, for the runtime argument; nothing else in that module.

## Decisions taken for the human

1. **One runtime per image, chosen at build.** The build argument `AGENT_RUNTIME` (`claude` or `opencode`) has no default, so a build that does not name it fails at once rather than carrying the wrong runtime. Reason: every instance already names exactly one runtime, and switching it already means running the setup again; the preflight's version check and agent-run probe stop an instance whose image holds another runtime. The human, 2026-11-04.
2. **The install happens in a throwaway build stage.** Node, npm and npm's cache live only in a first stage; the image copies from it only what the runtime runs. Reason: nothing runs Node since F0049 decision 6, and a cleanup inside the same layer would still leave Node. Taken for the human, 2026-11-04.
3. **The runtimes move to their current releases**: Claude Code 2.1.318 (2026-11-03) and opencode 1.19.5 (2026-10-28). Node stays at 22.23.4, the newest 22.x, since it only runs the install. The human asked for current versions, 2026-11-04.
4. **The memory peak is the slice's high-water mark, and its name says so.** `memory_peak_since_boot_bytes` is the kernel's `memory.peak` of the containers' user slice. Reason: a peak per run would need sampling during the run, and the human judged it not worth the effort; the name keeps the value from being read as the run's own peak. The human, 2026-11-04.
5. **The machine's measures sit in one object, and the CPU and the waits are the run's own.** `machine` holds all nine values, so the run's own measures stay apart from the machine's state; `cpu_seconds`, `cpu_wait_seconds` and `memory_wait_seconds` are differences of the kernel's running totals between the run's start and end. Reason: the waits say whether the machine is too small, which the peak alone does not; the totals need no sampling. The human, 2026-11-04.
6. **Transcripts stay inside the site; GitHub gets only numbers.** A transcript holds whole conversations, which no scan of secrets can clear, so it goes only to the folder the site names (`FACTORY_TRANSCRIPT_DIR`): a local directory on a VM, a bucket of the site's own GCP project in Cloud Run, mounted as a volume, so the factory needs no cloud client. An unset folder keeps no transcript and is no fault. The cost record refers to its transcript by path and SHA-256 and sums up the tool calls without content. Reason: the human, 2026-11-04: transcripts may hold sensitive information that the other places' scans do not cover, and Cloud Run, where the telemetry matters most, has no machine that outlives the job.
7. **The seams of S0002 and the contract pins.** S0002's tester named its seams (`factory.domain.machine`, `Images.size_bytes` and `store_path`, `ImageBuild.warnings`, `MachineReadings`), accepted as the Interface. Leave for S0002's tester: the `"4.1"` pins in `tests/domain/test_contract_version_4.py` and in `tests/domain/test_contract.py::test_a_schema_starts_with_the_dialect_and_the_contract_version` become `"4.2"`, nothing else in those modules; the pins stay a deliberate guard, as in F0049 decision 8. Taken for the human on PR #539, 2026-11-04.
8. **S0002's record seams, "adopted", and a leave.** `MachineTotals` and `machine_differences` in `factory.domain.machine`, `MachineReadings` in `factory.application.machine`, `CgroupMachineReadings(slice_folder, meminfo)` in `factory.adapters.machine_files`, and `Boundaries.machine` with the start's image sizes; the conftest's `boundaries` fixture adapted to the new field only. "Adopts an image" means only the return to the base. Leave for S0002's tester: the two expected build lines of `tests/entry/test_run_project_image_rebuild.py` take the new form, with sizes from a shared `tests/sized_images.py`; nothing else in that file. Taken for the human on PR #539, 2026-11-04.
9. **S0008's leaves.** `push_reason` drops git's two advice lines (`Please make sure you have the correct access rights`, `and the repository exists.`) and `hint:` lines; the reviewer adds that sentence to the Interface. `Git` gains a 22nd operation, `last_push_output()`; leave for the tester in the three tests that pin twenty-one operations (`tests/application/test_git_interface.py`, `tests/application/test_interfaces.py`, `tests/test_checkout_hygiene_removed.py`), and in four tests of `tests/application/test_dispatcher.py` to leave out `handler error ` lines; nothing else in those modules. Taken for the human on PR #540, 2026-11-04.
10. **The factory deletes no old transcripts.** A VM removes them with a `tmpfiles.d` rule that `vm/setup.sh` writes, and a Cloud Run bucket with its lifecycle rule; `FACTORY_TRANSCRIPT_DAYS` and its code are dropped from S0005. The opencode transcript is the run's own JSON event stream, which its wrapper already reads. Reason: the human, 2026-11-04: a cleanup in the factory is code the sites already have. Taken on PR #543.
