---
stage: docs
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 484
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-31T18:08:07.813061Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-31T18:08:07.818857Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-31T18:08:27.690055Z'
  stage: intake
  run: d20264d03b7a4a1088409634905937da
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-31T18:08:47.679066Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-31T18:15:23.870079Z'
  stage: tests
  run: 6509faa0b6ad489786c1fa3cbe0ca89f
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-31T18:15:45.941646Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-31T18:21:59.624763Z'
  stage: doing
  run: 0f57eb0a424b43cc90556714c78c9b40
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-31T18:22:20.245748Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-31T18:23:09.254795Z'
  stage: review
  run: 7b8b41d48791440cafd2fbaab92f4350
---

# The job profile stores images with the native overlay

## Description

S0002 gave the container profile `job` four global podman options, one of them `--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs`, because podman's overlay storage cannot sit on the job's root filesystem, which is itself an overlay. Measured since (`planning/cloud-sandbox/`, P15 and P16, 2026-10-31): with `fuse-overlayfs` every file a container reads from its image passes a userspace daemon, and factory-rf's `make test` took 601 s in a job of eight CPUs against 167 s on the four-CPU VM, so `check`'s eight minutes would end every stage there. With podman's storage on a tmpfs and the native kernel overlay, with no mount program, the same suite took 182 s and the image build 107 s instead of 199 s. The storage's place is the machine's (S0006's start script mounts a tmpfs at podman's storage root, as the VM's setup gives podman its storage); the factory's words only must stop naming the mount program. This story removes that option, so that `JOB_PODMAN_OPTIONS` holds three words and the job profile's storage is podman's native overlay wherever the machine put it. Unchanged: the profile `rootless` and its words, every other word of the profile `job`, the order of the words, `--storage-driver=overlay` (which makes podman refuse to start on an unsuitable root instead of falling back to a slower driver), and every setting.

## Interface

`factory.domain.containers` (domain): `JOB_PODMAN_OPTIONS: tuple[str, ...]` = `("--runtime=runc", "--cgroup-manager=cgroupfs", "--storage-driver=overlay")`.

No other module changes. `PodmanRuns` keeps putting `JOB_PODMAN_OPTIONS` after the executable in `launch`, `version` and `image_exists`.

Tests (the tester changes them, under this story's leave to change the earlier tests of S0002): `tests/adapters/test_podman_runs_job_profile.py`'s `JOB_WORDS` and every expectation built on it hold the three words; `tests/entry/test_wiring_container_profile.py` as far as it names the options. No other earlier test changes.

## Acceptance criteria

1. With the profile `rootless` (the default) the words of `launch`, `version` and `image_exists` are exactly those of before this story (the existing tests pass unchanged).
2. `JOB_PODMAN_OPTIONS` is exactly `("--runtime=runc", "--cgroup-manager=cgroupfs", "--storage-driver=overlay")`.
3. A `job` launch, `version` and `image_exists` carry those three words right after the executable and no word that contains `mount_program` or `fuse-overlayfs`; every other word and its place are as S0002's criteria give them, with the three words in place of the four.
4. No file under `src/` names `fuse-overlayfs` or `mount_program` (a test that reads the source).
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, *The job profile*: the words' table without the mount program; a sentence that podman's storage root must be on a filesystem the kernel's overlay accepts as its upper layer (a tmpfs in a job, whose root filesystem is an overlay), with the measured numbers (the suite 601 s with `fuse-overlayfs`, 182 s with the native overlay on a tmpfs; the image build 199 s and 107 s), and that the layers then count against the job's memory. `docs/project-guide/stage-environment.md`: `JOB_PODMAN_OPTIONS` with three words. `docs/decisions.md`: the entry *A root container profile for a managed sandbox* gains a line that names this change and its reason, from the feature's decision 19. `README.md`: none.

## Smoke test

```bash
uv run python -c "
from factory.domain.containers import JOB_PODMAN_OPTIONS
print(list(JOB_PODMAN_OPTIONS))
"
```
Expect: one line, `['--runtime=runc', '--cgroup-manager=cgroupfs', '--storage-driver=overlay']`

```bash
grep -rn -e fuse-overlayfs -e mount_program src/ ; echo "exit $?"
```
Expect: one line, `exit 1`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-31 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: names the concrete constant `factory.domain.containers.JOB_PODMAN_OPTIONS` with its exact three-word value. I checked the source: the constant exists at `src/factory/domain/containers.py:21` with the fourth word `--storage-opt=overlay.mount_program=...` at line 25, and `PodmanRuns` uses it at `podman_runs.py:72`. The story says no other module changes, and that matches the source. It also names the two test files the tester may change.
   Criteria: all five testable by one test each. (1) is the existing `rootless` tests passing unchanged. (2) is the exact tuple. (3) is the three words right after the executable in `launch`, `version` and `image_exists`, with no word containing `mount_program` or `fuse-overlayfs`. (4) is a source-reading test. (5) is `make check`. The failing side is covered by the no-`mount_program` and no-`fuse-overlayfs` clauses in (3) and by (4). The docs criterion is last.
   Smoke test: both commands are runnable. Neither uses pytest, so the `-q` rule does not apply. Each `Expect:` is checkable against the output. The grep currently finds the line at containers.py:25, so the second expectation (`exit 1`) fails until the story is built.
   Architecture: the change is a domain constant only. The adapter and the layers stay as `CLAUDE.md` describes.
   Scope: it matches feature.md's scope bullet 'job profile without fuse-overlayfs' and decision 19. S0009 is listed in the Stories. The story changes S0002's tests with the leave it states, and names the two files.
4. factory: started tests as vm.
5. tester: Wrote the tests for the three-word job profile. They are red on purpose: `src/factory/domain/containers.py` still holds the fourth word, `--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs`.

   Criterion → test:
   - criterion 1: the existing rootless tests, which I left unchanged: `tests/adapters/test_podman_runs.py`, `test_podman_runs_fence.py`, `test_podman_runs_results.py`, and `tests/adapters/test_podman_runs_job_profile.py::test_the_default_profile_launches_as_the_rootless_one`.
   - criterion 2: `tests/domain/test_containers_job_options.py::test_the_job_options_store_images_with_the_native_overlay`
   - criterion 3: `tests/adapters/test_podman_runs_job_profile.py::test_a_job_launch_puts_the_global_options_first_and_runs_on_the_host_network`, `::test_a_job_runner_s_queries_carry_the_global_options`, `::test_a_job_run_reads_its_end_as_the_rootless_one` (the three words right after the executable, every other word in its place), and the new `::test_a_job_runner_names_no_mount_program` (one row each for launch, version and image-exists; no word may contain `mount_program` or `fuse-overlayfs`).
   - criterion 4: `tests/test_mount_program_search.py::test_no_source_file_names_the_overlay_mount_program`, with one row per name. It reads every file under `src/` and skips `__pycache__`.
   - criteria 5 and 6 (`make check`, docs): no test.

   Files:
   - Created `tests/domain/test_containers_job_options.py` and `tests/test_mount_program_search.py`.
   - Changed `tests/adapters/test_podman_runs_job_profile.py`, an earlier test of S0002, under this story's own leave:
     - `JOB_WORDS` now holds the three words.
     - Added the constant `MOUNT_PROGRAM_WORDS`.
     - In `test_a_job_run_reads_its_end_as_the_rootless_one`, the slice `argv[1:5]` became `argv[1 : 1 + len(JOB_WORDS)]`.
     - Added the new test and its three helpers.
   - Left `tests/entry/test_wiring_container_profile.py` unchanged. It names the options only through `JOB_PODMAN_OPTIONS`, so it follows the constant.

   Run: `make test` fails for the right reason. Before the change the job-profile tests get four words where they expect three, the new no-mount-program rows for launch, version and image-exists find `--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs`, and the constant and source-search tests fail. Every module imported; no collection errors. `make lint` is green.

   I started that one `make test` run without the large timeout, so the shell tool moved it to the background; I waited for its output file and did not run it again. Open: nothing.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/adapters/test_podman_runs_job_profile.py::test_a_job_runner_s_queries_carry_the_global_options[exists-fault] - AssertionError: assert [['--runtime=...exists', ...]] == [['--runtime=......
6. factory: started doing as vm.
7. coder: I removed the fourth word, `--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs`, from `JOB_PODMAN_OPTIONS` in `src/factory/domain/containers.py`. The tuple now holds the three words the Interface gives, in the same order. I also rewrote the comment above the constant, which said the overlay root "needs a mount program". It now says why `--storage-driver=overlay` stays: it makes podman refuse an unsuitable storage root instead of falling back to a slower driver. It also says the machine puts that root on a filesystem the kernel's own overlay accepts. No other module changed: `PodmanRuns` still puts the constant after the executable.

   `make check` is green (`test: green (166.0 s)`, `check: green`). `grep -rn -e fuse-overlayfs -e mount_program src/` finds nothing.

   Main choice: the comment explains the reason in its own words and cites nothing. I rejected citing `docs/decisions.md`, because the entry that names this change and its reason does not exist yet: the docs stage writes it (criterion 6), so a citation now would point at nothing.

   Refactor: the diff is three lines, and nothing needed changing.

   Noticed but not touched: `docs/decisions.md:1247` (*A root container profile for a managed sandbox*) still lists four options. The operator guide and `docs/project-guide/stage-environment.md` likely do too. Both are the docs stage's work under criterion 6. The journal did not change the meaning of the task, so I did not rewrite the Description.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 41 known, 0 gone
8. factory: started review as vm.
9. reviewer: no findings

   What I reviewed: `git diff main...HEAD -- . ':!factory'` (`src/factory/domain/containers.py`, `tests/adapters/test_podman_runs_job_profile.py`, the new `tests/domain/test_containers_job_options.py` and the new `tests/test_mount_program_search.py`), plus the work item.

   - Acceptance criteria:
     - Criterion 1: the rootless tests are unchanged in the diff (`test_podman_runs*.py` and `test_the_default_profile_launches_as_the_rootless_one`).
     - Criterion 2: `test_the_job_options_store_images_with_the_native_overlay` compares the constant with the exact tuple.
     - Criterion 3: three tests pin the exact argv of a `job` launch, `version` and `image_exists`, with the three words right after the executable: `test_a_job_launch_puts_the_global_options_first...`, `test_a_job_runner_s_queries_carry_the_global_options` and the end-reading test, which now slices by `len(JOB_WORDS)`. For the failing side, `test_a_job_runner_names_no_mount_program` has one row each for launch, version and image-exists.
     - Criterion 4: `test_no_source_file_names_the_overlay_mount_program` reads every file under `src/`, not only `*.py`. That is right, because `src/factory/contract/*.schema.json` are files under `src/` too. So it is not a copy of `search_support.modules_matching`, which searches only `*.py`.
     - The coder's `make check` was green (entry 7). The Interface states no other rule or limit.
   - Architecture: only a domain constant changed. `PodmanRuns` still puts it after the executable (`podman_runs.py:72`), and no layer changed.
   - Security: no secrets, no markers, no commands built from strings.
   - Quality: the new comment above `JOB_PODMAN_OPTIONS` (`containers.py:18-21`) says why the remaining overlay word stays and why the mount program went, and it does not name the removed program, as criterion 4 requires. `duplicates` reported 0 new.
   - Work item hygiene: the Description matches what was built. The coder's entry names the comment choice and what was rejected. The docs criterion still lists the four documents and what each must say.

   Earlier tests:
   - `tests/adapters/test_podman_runs_job_profile.py`: changed under the story's own leave, which the human wrote into the Interface (`JOB_WORDS` and every expectation built on it hold the three words). Two edits did that: `JOB_WORDS` now holds three words, and the slice `argv[1:5]` became `argv[1 : 1 + len(JOB_WORDS)]`. Beyond that the file only gains `MOUNT_PROGRAM_WORDS`, three helpers and a new test (no leave needed); every earlier test keeps its name and what it checks.
