---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 482
comments_read: [6546068187]
handed_over: null
claim:
  instance: vm
  stage: doing
  started_at: '2026-10-31T16:36:12.713545Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-31T16:25:00.023181Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-31T16:25:00.029241Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-31T16:25:34.096735Z'
  stage: intake
  run: 679415d43d2e4748bc9bb2efd57907a8
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-31T16:27:52.223160Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-31T16:28:10.241569Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-31T16:28:29.727744Z'
  stage: intake
  run: c96d9d8580cb4aefa59a74ba52a8ad8b
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-31T16:28:49.927822Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-31T16:35:50.611030Z'
  stage: tests
  run: f089d702076a4d32a7ee868d5e501bb7
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-31T16:36:12.713545Z'
  stage: doing
---

# The container profile job

## Description

`PodmanRuns` starts every container rootless with `--userns=keep-id`, on podman's default network and storage. In a Cloud Run job that cannot work: the job's root has `NoNewPrivs` (no `newuidmap`), the cgroup layout is hybrid (crun refuses it, runc accepts it), the root filesystem is an overlay (podman's overlay storage needs a mount program), no bridge network reaches the outside, and podman copies the job's proxy variables into every container. Measured on 2026-10-31 (`planning/cloud-sandbox/`, P2, P3, P10, P11): Podman 5.4 with `--runtime=runc --cgroup-manager=cgroupfs --storage-driver=overlay --storage-opt overlay.mount_program=/usr/bin/fuse-overlayfs`, `--network=host`, `--http-proxy=false`, as root with `--cap-drop=all`, ran the factory's other flags (`--timeout` ending a container with exit status 255, `--pids-limit`, `--memory`, `--security-opt=no-new-privileges`, bind mounts, `:ro`). This story adds the setting `FACTORY_CONTAINER_PROFILE` with the value `job` and gives `PodmanRuns` that profile. Unchanged: the default profile `rootless` and its words, the container call's DTOs, the grace and the exit-status reading (255 at or after the limit is the time limit, as today). Left to later stories: the metadata proof (S0003) and the start script (S0006).

## Interface

`factory.domain.settings` (domain): `CONTAINER_PROFILE_VARIABLE = "FACTORY_CONTAINER_PROFILE"` and the field `InstanceSettings.container_profile: Literal["rootless", "job"] = "rootless"`; unset or blank is `rootless`, `job` is accepted, anything else is `SettingsInvalid(FACTORY_CONTAINER_PROFILE, "is neither rootless nor job")`.

`factory.domain.containers` (domain): `JOB_PODMAN_OPTIONS: tuple[str, ...]` = `("--runtime=runc", "--cgroup-manager=cgroupfs", "--storage-driver=overlay", "--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs")`.

`factory.adapters.podman_runs` (adapters): `PodmanRuns(executable, image, workspace, *, time_limit=PODMAN_TIME_LIMIT, profile: Literal["rootless", "job"] = "rootless")`.

- `rootless`: every word as today.
- `job`: `launch` gives `<executable> <JOB_PODMAN_OPTIONS...> run --rm --http-proxy=false --network=host --timeout <seconds> --cap-drop=all --security-opt=no-new-privileges --pids-limit=<PIDS_LIMIT> --memory=<MEMORY_LIMIT> <--env words> <--volume words> --workdir <dir> <image> <command...>`: no `--userns=keep-id`, the global options before `run`, the other words in today's order. `version` runs `<executable> <JOB_PODMAN_OPTIONS...> --version` and `image_exists` runs `<executable> <JOB_PODMAN_OPTIONS...> image exists <image>`. Mounts, the grace, the mapping of results and the `ValueError` rules are those of `rootless`.

`factory.entry.wiring` (entry): `_container_adapters` gives `PodmanRuns` the setting's profile.

Tests (the tester writes them): `tests/domain/test_settings_container_profile.py`, `tests/adapters/test_podman_runs_job_profile.py` (the stand-in `podman` of `tests/podman_support.py`), `tests/entry/test_wiring_container_profile.py`. `tests/adapters/test_podman_runs*.py` pass unchanged.

## Acceptance criteria

1. With `FACTORY_CONTAINER_PROFILE` unset the words of `PodmanRuns.launch`, `version` and `image_exists` are exactly those of before this story (the existing tests pass unchanged; one new row compares a launch of the default with a launch of `profile="rootless"`).
2. `FACTORY_CONTAINER_PROFILE` is read, rows of one test: unset and blank give `rootless`; `job` gives `job`; `Job`, `root` and `job now` are refused as `is neither rootless nor job`.
3. A `job` launch of the command `["make", "check"]` with one environment entry `A=1`, one read-write mount and one `:ro` mount, the limit 90 s and the working directory `/work/checkout` has exactly these words in this order: the executable, the four `JOB_PODMAN_OPTIONS`, `run`, `--rm`, `--http-proxy=false`, `--network=host`, `--timeout`, `90`, `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096`, `--memory=4g`, `--env`, `A=1`, the workspace volume, the two mount volumes (the second ending `:ro`), `--workdir`, `/work/checkout`, the image, `make`, `check`; its time limit is 90 s plus the grace, its environment `None`.
4. A `job` launch contains none of `--userns=keep-id` and `--user`.
5. `version` of a `job` runner runs the executable, the four options and `--version`, and `image_exists` runs the executable, the four options, `image`, `exists` and the image name; their results and faults are those of `rootless` (exit 0 and 1, any other outcome a `ContainerError`).
6. `run` of a `job` runner reads the end as `rootless` does: exit status 255 at or after the limit is `timed_out`, 255 before it is the command's own, 125 is podman's own fault.
7. `build_boundaries` with the setting `job` gives a `PodmanRuns` whose launch has the four global options; with the setting unset, none.
8. A `job` launch with no command words, and one with a mount whose target is `/work` or `/work/x`, are each refused with `ValueError`, as `rootless` does (rows of one test).
9. `make check` stays green.
10. docs: `docs/operator-guide.md`: the variable in the configuration table and a subsection *The job profile*: what each word is for, with the measured facts (crun and Podman 6 refuse the hybrid cgroups, rootless is impossible under `NoNewPrivs`, no bridge reaches outside), and that the container runs as the job's root with every capability dropped. `docs/project-guide/stage-environment.md`: *The podman adapter* gains the profile and its words. `docs/decisions.md`: an entry *A root container profile for a managed sandbox*, from the feature's decisions 3 to 5. `README.md`: none.

## Smoke test

```bash
uv run python -c "
from datetime import timedelta
from pathlib import Path
from factory.adapters.podman_runs import PodmanRuns
runs = PodmanRuns('podman', 'img:1', Path('/work'), profile='job')
launch = runs.launch(['true'], mounts=[], environment={}, time_limit=timedelta(seconds=10), working_directory='/work/checkout')
print(launch.argv[:6])
print('--userns=keep-id' in launch.argv, '--network=host' in launch.argv)
"
```
Expect: two lines, `['podman', '--runtime=runc', '--cgroup-manager=cgroupfs', '--storage-driver=overlay', '--storage-opt=overlay.mount_program=/usr/bin/fuse-overlayfs', 'run']` and `False True`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-31 human: created.
2. factory: started intake as vm.
3. intake: 1. The Interface says that for `job` "the `ValueError` rules are those of `rootless`". Those rules are: a launch with no command words, and a mount whose target is `/work` or under it, are both refused with `ValueError`. No criterion tests either on a `job` runner. Without one, a coder could put the profile branch before the validation and every listed test would still pass. Options: (a) add a criterion "a `job` launch with no command words, or with a mount targeting `/work` or `/work/x`, is refused with `ValueError`, as `rootless` does", with the rows in one test; (b) drop the clause from the Interface. I would choose (a).
   2. The Interface says "The profile is fixed at construction and changes nothing else". It is not a testable behaviour, and no criterion covers it. Options: (a) delete the sentence; (b) replace it with a concrete rule that has a criterion, for example "a `rootless` runner built beside a `job` runner keeps its own words". I would choose (a), because criterion 1 already covers the default.
   3. Criterion 9 (docs) is an ordinary docs criterion and needs no change. The rest of the story is fine. The format check passed. The Interface names concrete modules and signatures. The smoke test runs no pytest, so the `-q` rule does not apply. The `Expect:` line is checkable against the output. The story is inside the feature's scope and the layering is correct: the domain holds the setting and the words, the adapter holds `PodmanRuns`, and the wiring is in entry.
4. 2026-10-31 human: Answers to question 3:

   1. (a): add the criterion, rows of one test: a `job` launch with no command words, and one with a mount whose target is `/work` or `/work/x`, are each refused with `ValueError`, as `rootless` does.
   2. (a): delete the sentence; criterion 1 covers the default.
   3. Nothing to change.
5. factory: started intake as vm.
6. intake: accepted, with the human's answer from journal entry 4 carried into the story (their edit, not mine): I deleted the Interface sentence "The profile is fixed at construction and changes nothing else" (answer 2a), and I added a new criterion 8 before the two closing ones: a `job` launch with no command words, and one with a mount targeting `/work` or `/work/x`, are each refused with `ValueError`, as `rootless` does, rows of one test (answer 1a). `make check` is now criterion 9 and docs is criterion 10. The Description did not change.
   - Interface: it names concrete modules and signatures: `domain.settings` (`CONTAINER_PROFILE_VARIABLE`, `InstanceSettings.container_profile`), `domain.containers.JOB_PODMAN_OPTIONS`, `adapters.podman_runs.PodmanRuns(..., profile=)` and `entry.wiring._container_adapters`. Every stated behaviour has a criterion. These are the settings values, the job word order, `version` and `image_exists`, the `ValueError` rules, and the wiring.
   - Criteria: each one is testable by one test function. The rules have both sides. The setting accepts unset, blank and `job` (criterion 2) and refuses `Job`, `root` and `job now` (criterion 2). The job profile has no `--userns=keep-id` or `--user` (criterion 4). `ValueError` is covered in criterion 8. Exit status 255 at or after the limit versus before it, and 125, are in criterion 6. The wiring is covered both with the setting `job` and with it unset (criterion 7).
   - Smoke test: the command is runnable and runs no pytest, so the `-q` rule does not apply. The `Expect:` line gives two exact lines to compare with the output.
   - Architecture: the setting and the option words are in the domain, `PodmanRuns` is in the adapters, and the profile is wired in the entry layer, so the layering holds.
   - Scope: the story is within F0047's scope item "FACTORY_CONTAINER_PROFILE=job" and touches nothing in "Out of scope". Its decisions 3 to 5 are the ones the story states.
7. factory: started tests as vm.
8. tester: I wrote the tests for criteria 1 to 8 against the Interface. They fail for the right reasons, and `make lint` is green.

   - criterion 1: tests/adapters/test_podman_runs_job_profile.py::test_the_default_profile_launches_as_the_rootless_one. The new row compares a default launch with a `profile="rootless"` launch. The existing tests/adapters/test_podman_runs*.py are unchanged and still pin the old words.
   - criterion 2: tests/domain/test_settings_container_profile.py::test_the_container_profile_is_rootless_by_default_or_job. Rows: unset, `""` and `" "` give rootless; `job` gives job; `Job`, `root` and `job now` give `SettingsInvalid(FACTORY_CONTAINER_PROFILE, …is neither rootless nor job…)`.
   - criterion 3: tests/adapters/test_podman_runs_job_profile.py::test_a_job_launch_puts_the_global_options_first_and_runs_on_the_host_network. It checks the exact argv, the time limit (90 s plus `CONTAINER_GRACE`) and `env is None`.
   - criterion 4: tests/adapters/test_podman_runs_job_profile.py::test_a_job_launch_maps_no_user
   - criterion 5: tests/adapters/test_podman_runs_job_profile.py::test_a_job_runner_s_queries_carry_the_global_options. It uses the stand-in `podman` of tests/podman_support.py. Rows: version prints its line; version exit 2 is a ContainerError; image_exists exit 0 is True, exit 1 is False, exit 125 is a ContainerError. Each row checks the recorded words: the four options, then the query.
   - criterion 6: tests/adapters/test_podman_runs_job_profile.py::test_a_job_run_reads_its_end_as_the_rootless_one. `run_process` is faked through the existing `run_process_recorder.Recorder`. Rows: 255 at the limit and after it are timed_out; 255 before it passes through as 255; 125 is podman's own fault. Each row also checks that the run's argv carries the four options.
   - criterion 7: tests/entry/test_wiring_container_profile.py::test_the_container_adapter_gets_the_setting_s_profile. Rows: unset gives no global options before `run`; `job` gives `JOB_PODMAN_OPTIONS` before `run`. In neither row does an option appear after `run`.
   - criterion 8: tests/adapters/test_podman_runs_job_profile.py::test_a_job_launch_refuses_no_command_or_a_mount_on_the_dataset. Rows: no command, a mount at `/work`, a mount at `/work/x`.
   - criteria 9 and 10: no test. They cover `make check` and the docs.

   Files I created: tests/domain/test_settings_container_profile.py, tests/adapters/test_podman_runs_job_profile.py and tests/entry/test_wiring_container_profile.py. I changed no earlier test file.

   Run result: tests/adapters/test_podman_runs_job_profile.py fails with `TypeError: PodmanRuns.__init__() got an unexpected keyword argument 'profile'`. The settings and wiring tests cannot import `CONTAINER_PROFILE_VARIABLE` from `factory.domain.settings` or `JOB_PODMAN_OPTIONS` from `factory.domain.containers`, because neither exists yet.

   My first `make test` call went to the background because I gave it the default timeout. I waited for that same run and did not run the tests again.

   Left untested: what a `ContainerError`'s command text says for a job runner. No criterion names it.

   `lint`: lint: green (0.2 s)
   `test`: ERROR tests/adapters/test_podman_runs_job_profile.py::test_a_job_run_reads_its_end_as_the_rootless_one[podman-s-own-fault] - TypeError: PodmanRuns.__init__() got an unexpected keyword argument 'pro...
9. factory: started doing as vm.
