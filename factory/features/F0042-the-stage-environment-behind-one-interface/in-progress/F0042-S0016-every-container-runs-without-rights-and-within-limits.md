---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 420
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T20:27:49.238444Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T20:27:49.244418Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T20:28:10.015632Z'
  stage: intake
  run: 9694797ef2ee49f2894d5aa27a9c98c9
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T20:28:30.160352Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T20:31:29.042732Z'
  stage: tests
  run: ad9b2dd47a044da191bc0b7ab0e0b513
---

# Every container runs without rights and within limits

## Description

A v1.2 stage runs every project command, the sync and the agent in a throwaway rootless container (`PodmanRuns`, S0003). Today such a container keeps podman's default capabilities, may start any number of processes and may take all the machine's memory. Code in the checkout (a dependency's install script, a test, a file an agent was misled into writing) runs in these containers, and F0044 (the layers go) removes the second user and the kernel's write guard, so the container's own fence is what stays. This story narrows it. Every container is started with no capabilities (`--cap-drop=all`), cannot gain rights through a set-uid program (`--security-opt=no-new-privileges`), and is limited to 4096 processes and 4 GB of memory. Every container keeps podman's default network: the sync container needs the package index, the agent's container the model's API, and the check container runs `make sync` first, which needs the package index when the take changed `uv.lock` or `pyproject.toml` (the human's choice, 2026-10-24, over a check without network). Measured on 2026-10-24 on the local VM (Ubuntu 24.04, podman 4.9.3, rootless as `factory`): all four words are accepted, the container's effective capabilities are `0000000000000000`, a write to the dataset still works under `--userns=keep-id`, `--pids-limit=50` stops the 49th fork with "can't fork: Resource temporarily unavailable", `--memory=64m` sets the container's `memory.max` to 67108864, and the user's systemd delegates the `cpu memory pids` controllers. What stays: the `inline` environment and `self` are untouched (they run no container); the interface `ContainerRuns`, `ContainerCall` and every caller are unchanged; the exit statuses and time limits are read as today, with S0015's 255; a container killed for its memory before its time limit is an ordinary failure with its exit status, as any other. Decision 23 of `feature.md`.

## Interface

`factory.adapters.podman_runs` (`adapters`):

```python
PIDS_LIMIT = 4096
MEMORY_LIMIT = "4g"
```

- `PodmanRuns.launch` puts these four words right after `--timeout <seconds>` and before the first `--env`, in this order: `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096`, `--memory=4g` (the last two built from the constants). Each word carries a comment that says what it keeps out. `PodmanRuns.run` starts the words of `launch`, as today.
- Nothing else changes: `ContainerRuns`, `ContainerCall`, `FakeContainerRuns` and the callers stay as they are.

Tests (the tester writes them): new rows in a new test module, for example `tests/adapters/test_podman_runs_fence.py`, with the stand-in `podman` of `tests/podman_support.py`. The one earlier test this story changes, and nothing else in it (decision 18 (j)): `tests/adapters/test_podman_runs.py::test_launch_pins_the_podman_command_line`, whose expected words gain the four words `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096`, `--memory=4g` after `2400`.

## Acceptance criteria

1. `PodmanRuns.launch` with the mounts, environment and time limit of 40 minutes of `test_launch_pins_the_podman_command_line`: the words are `[<podman>, "run", "--rm", "--userns=keep-id", "--timeout", "2400", "--cap-drop=all", "--security-opt=no-new-privileges", "--pids-limit=4096", "--memory=4g", "--env", ...]`, with the `--env`, `--volume`, `--workdir`, image and command words exactly as that test pins them, and no word that starts with `--network`.
2. `PodmanRuns.run` with the stand-in `podman` of `tests/podman_support.py`: the arguments of its recorded call (`podman.calls()`) hold `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096` and `--memory=4g`, right after the `--timeout` word and its seconds.
3. `PIDS_LIMIT == 4096` and `MEMORY_LIMIT == "4g"`; with both replaced through `monkeypatch.setattr` on `factory.adapters.podman_runs` by `64` and `"64m"`, `launch` gives `--pids-limit=64` and `--memory=64m` in their places (one test).
4. `tests/adapters/test_podman_runs.py::test_launch_pins_the_podman_command_line` passes with exactly the change named in the Interface.
5. `make check` stays green.
6. docs: `docs/project-guide/stage-environment.md`, the section *The podman adapter*: the four words, each with what it keeps out; that every container keeps the default network and why (the sync and the check's `make sync`: the package index; the agent: the model's API); the limits as constants and why 4096 and 4 GB (the suite's workers under `-n auto` on the VM's cores, one container at a time on a machine of 8 GB); the measured facts of 2026-10-24 from the Description. `docs/operator-guide.md`, the section *The agent in a container*: its `podman run` words gain the four words, and one paragraph on a `container` instance's fence (no capabilities, no new rights, the two limits, the network kept), and that a memory kill before the time limit is an ordinary failure (a failed check, usually with make's exit status 2 when the kernel ended one of its children, 137 when it ended the container's first process). `docs/decisions.md`: a short entry "Every container runs without rights and within limits" (the reason: F0044 removes the second user and the write guard, so the container's own fence is what stays; why the network stays: the check's `make sync` needs the package index after a change of `uv.lock`, and the agent needs the model's API, so cutting it is a later step, for example an allow-list). `README.md`: none.

## Smoke test

```bash
uv run python -c 'from datetime import timedelta as t; from pathlib import Path as P; from factory.adapters.podman_runs import PodmanRuns as R; print(R("podman", "img", P("/srv/w")).launch(["true"], mounts=[], environment={}, time_limit=t(seconds=5), working_directory="/work").argv[6:11])' 2>/dev/null
```
Expect: one line, `['--cap-drop=all', '--security-opt=no-new-privileges', '--pids-limit=4096', '--memory=4g', '--volume']`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: `factory.adapters.podman_runs` names `PIDS_LIMIT = 4096` and `MEMORY_LIMIT = "4g"` and gives the exact placement and order of the four words in `PodmanRuns.launch`, after `--timeout <seconds>` and before the first `--env`. `launch` and `run` are real operations in `podman_runs.py`, and the argv layout I read there matches the stated position. It changes no interface, DTO or caller.
   - Criteria: each can be tested by one test function. They cover the exact argv with no `--network` word (1), the recorded call of `run` through the stand-in podman (2), and both constants plus their monkeypatched replacement (3). They also cover the one earlier test that changes, named with its change (4). The rules are the two limits and the four words. They have no failing side to test: the story validates nothing and rejects no input, so no refusal criterion is missing. The decision 18 (j) leave covers the earlier test, with the human's word.
   - Smoke test: the command is runnable. The `PodmanRuns("podman", "img", Path)` constructor matches, and with empty mounts and environment `argv[6:11]` is the four words followed by `--volume`, because `/work` is always the first volume. The `Expect:` line is a single exact list. No pytest is run, so the `-q` rule does not apply.
   - Architecture: the change stays in the adapters layer, in the one podman wrapper. `ContainerRuns` is untouched and the constants are module-level. The docs criterion names the files the documenter keeps.
   - Scope: this is S0016 of F0042, listed in the feature's Scope and Stories and Decision 23. It adds no `network` keyword, and removes no layer, so it stays outside the Out of scope list.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1–4. On purpose, they fail until the coder makes the change. Criteria 5 (`make check`) and 6 (docs) are for the coder's checks and the docs stage, so they have no test of their own.

   - criterion 1: tests/adapters/test_podman_runs_fence.py::test_launch_drops_every_right_and_limits_the_container. It uses the same mounts, environment and 40-minute limit as the earlier test, pins the full list of words with the four new ones after "2400", and checks that no word starts with `--network`.
   - criterion 2: tests/adapters/test_podman_runs_fence.py::test_a_run_starts_its_container_without_rights_and_within_limits. It runs through the stand-in `podman` with its default plan, and the four words must come right after the `--timeout` word and its seconds in `podman.calls()`.
   - criterion 3: tests/adapters/test_podman_runs_fence.py::test_the_limits_are_built_from_the_constants. It checks `PIDS_LIMIT == 4096` and `MEMORY_LIMIT == "4g"`, then uses `monkeypatch.setattr` to set them to 64 and "64m" and checks for `--pids-limit=64` and `--memory=64m` in their places.
   - criterion 4: tests/adapters/test_podman_runs.py::test_launch_pins_the_podman_command_line. The only change is the four words `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096` and `--memory=4g` added after "2400", as the Interface names under decision 18 (j).

   Files: I created tests/adapters/test_podman_runs_fence.py and changed tests/adapters/test_podman_runs.py, which an earlier story wrote; the change is only the one the Interface names.

   `make test` result:
   - tests/adapters/test_podman_runs_fence.py could not be imported. The cause is the names `PIDS_LIMIT` and `MEMORY_LIMIT`, which `factory.adapters.podman_runs` does not define yet.
   - test_launch_pins_the_podman_command_line fails on the list of words, because the four new words are not there yet.

   `make lint` is green. I skipped the type check, as this stage's instructions say.

   I considered building criterion 1's call from a helper shared with the earlier module, and decided against it. Criterion 4 allows only the one change in that test, so I wrote the call again in the new module.

   Nothing in the criteria needed my interpretation, so there is no open question.

   `lint`: lint: green (0.6 s)
   `test`: ERROR tests/adapters/test_podman_runs_fence.py - ImportError while importing test module '/work/checkout/tests/adapters/test_podman_runs_fence.py'.
