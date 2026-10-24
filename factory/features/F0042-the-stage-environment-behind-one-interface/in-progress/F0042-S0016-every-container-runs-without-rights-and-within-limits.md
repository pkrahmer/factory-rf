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
