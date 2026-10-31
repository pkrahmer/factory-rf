---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: intake
  started_at: '2026-10-31T18:08:07.818857Z'
  lease_duration: 60
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
