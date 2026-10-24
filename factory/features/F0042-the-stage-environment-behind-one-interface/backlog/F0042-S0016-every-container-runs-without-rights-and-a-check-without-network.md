# Every container runs without rights, and a check without network

## Description

A v1.2 stage runs every project command, the sync and the agent in a throwaway rootless container (`PodmanRuns`, S0003). Today such a container keeps podman's default capabilities, may start any number of processes, may take all the machine's memory, and has the network. Code in the checkout (a dependency's install script, a test, a file an agent was misled into writing) runs in these containers, and F0044 (the layers go) removes the second user and the kernel's write guard, so the container's own fence is what stays. This story narrows it. Every container is started with no capabilities (`--cap-drop=all`), cannot gain rights through a set-uid program (`--security-opt=no-new-privileges`), and is limited to 4096 processes and 4 GB of memory. A container whose call does not ask for the network runs without it (`--network=none`): the check container of S0009 asks for none, because `make check`, `make test` and the smoke test need no network; the sync container (S0007: `git fetch` from a read-only mount and `uv sync` from the package index) and the agent's container (S0008: the model's API) ask for it. Measured on 2026-10-24 on the local VM (Ubuntu 24.04, podman 4.9.3, rootless as `factory`): all these words are accepted, the container's effective capabilities are `0000000000000000`, a write to the dataset still works under `--userns=keep-id`, `--network=none` refuses an outbound connection the default network allows, `--pids-limit=50` stops the 49th fork with "can't fork: Resource temporarily unavailable", `--memory=64m` sets the container's `memory.max` to 67108864, and the user's systemd delegates the `cpu memory pids` controllers. What stays: the `inline` environment and `self` are untouched (they run no container); the exit statuses and time limits are read as today, with S0015's 255; a container killed for its memory before its time limit is an ordinary failure with its exit status, as any other. Decision 23 of `feature.md`.

## Interface

`factory.application.containers.ContainerRuns` (`application`): `launch` and `run` each gain the keyword `network: bool = False`, after `working_directory`; their docstrings say that a call without `network=True` runs without network.

`factory.domain.containers.ContainerCall` (`domain`): gains the field `network: bool = False`.

`factory.adapters.podman_runs` (`adapters`):

```python
PIDS_LIMIT = 4096
MEMORY_LIMIT = "4g"
```

- `PodmanRuns.launch` puts these words right after `--timeout <seconds>` and before the first `--env`, in this order: `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096`, `--memory=4g`, and, when `network` is `False`, `--network=none`. With `network=True` no `--network` word is added (podman's default network). Each word carries a comment that says what it keeps out.
- `PodmanRuns.run` passes `network` through to `launch`.

`factory.adapters.fake_containers.FakeContainerRuns` (`adapters`): records `network` in the `ContainerCall`; it runs on the host as before and cannot cut the network (its docstring says so).

The callers:
- `factory.adapters.agent_launch.container_launch` passes `network=True` (the agent's call and the version's call both).
- `factory.application.stage_environment.ContainerEnvironment` passes `network=True` for the sync container.
- `factory.adapters.make_commands.ContainerMakeCommands` (S0009) passes nothing, so its check container runs without network.

Tests (the tester writes them): new rows in new test modules, for example `tests/adapters/test_podman_runs_fence.py` and `tests/application/test_container_networks.py`, with the stand-in `podman` of `tests/podman_support.py` and `FakeContainerRuns`. The earlier tests this story changes, and nothing else in them (decision 18 (j)):
- `tests/adapters/test_podman_runs.py::test_launch_pins_the_podman_command_line`: the expected words gain the five words `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096`, `--memory=4g`, `--network=none` after `2400`.
- `tests/adapters/test_agent_launch_container.py::test_a_container_launch_mounts_the_files_read_only_at_their_own_paths`, `tests/adapters/test_claude_runtime_container.py::test_the_version_runs_in_a_container_with_the_version_time_limit` and `tests/adapters/test_opencode_runtime_container.py::test_the_version_runs_in_a_container_with_the_version_time_limit`: each expected `ContainerCall` gains `network=True`.

## Acceptance criteria

1. `PodmanRuns.launch` with `network=True`, the mounts, environment and time limit of 40 minutes of `test_launch_pins_the_podman_command_line`: the words are `[<podman>, "run", "--rm", "--userns=keep-id", "--timeout", "2400", "--cap-drop=all", "--security-opt=no-new-privileges", "--pids-limit=4096", "--memory=4g", "--env", ...]`, with the `--env`, `--volume`, `--workdir`, image and command words exactly as that test pins them, and no word that starts with `--network`.
2. The network (rows of one parametrized test, `launch` with otherwise equal arguments): `network=False` gives the words of criterion 1 with `--network=none` right after `--memory=4g`; `network=True` gives no `--network` word; a call without the keyword gives the same words as `network=False`.
3. `PodmanRuns.run` with a stand-in `podman` that prints its arguments: the printed words hold `--network=none` for a call without `network` and do not hold it for `network=True`; both hold `--cap-drop=all`, `--security-opt=no-new-privileges`, `--pids-limit=4096` and `--memory=4g`.
4. `PIDS_LIMIT == 4096` and `MEMORY_LIMIT == "4g"`, and the words of criterion 1 are built from them (one test).
5. `FakeContainerRuns` records `network` (rows of one parametrized test): a `launch` and a `run` with `network=True` each record a `ContainerCall` with `network=True`; without the keyword, with `network=False`. `ContainerCall` built without `network` has `network=False`.
6. The callers, each through `FakeContainerRuns` (rows of one parametrized test where they share a shape): the agent's call of a Claude Code runtime and of an opencode runtime built with `containers` (as S0008's tests build them) records `network=True`; their version calls record `network=True`; the sync of `ContainerEnvironment.prepare` (as S0007's tests run it) records `network=True`; `ContainerMakeCommands.run("check", ...)` (as S0009's tests run it) records `network=False`.
7. The four earlier tests named in the Interface pass with exactly the change named there.
8. `make check` stays green.
9. docs: `docs/project-guide/stage-environment.md`, the section *The podman adapter*: the five words, each with what it keeps out; which calls ask for the network and why (the sync: the package index; the agent: the model's API; the check: none needed); the limits as constants and why 4096 and 4 GB (the suite's workers under `-n auto` on the VM's cores, one container at a time on a machine of 8 GB); the measured facts of 2026-10-24 from the Description; that the fake cannot cut the network. `docs/operator-guide.md`, the section *What the container cannot see*: one paragraph on a `container` instance's fence (no capabilities, no new rights, the two limits, no network for the checks), and that a memory kill shows as a failed check with exit status 137 before the time limit. `docs/decisions.md`: a short entry "Every container runs without rights, and a check without network" (the reason: F0044 removes the second user and the write guard, so the container's own fence is what stays; the choice of `network` per call with no network as the default, so a new caller is closed until it asks). `README.md`: none.

## Smoke test

```bash
uv run python -c 'from datetime import timedelta as t; from pathlib import Path as P; from factory.adapters.podman_runs import PodmanRuns as R; r = R("podman", "img", P("/srv/w")); a = lambda **k: r.launch(["true"], mounts=[], environment={}, time_limit=t(seconds=5), working_directory="/work", **k).argv[6:11]; print(a(), a(network=True))' 2>/dev/null
```
Expect: one line, `['--cap-drop=all', '--security-opt=no-new-privileges', '--pids-limit=4096', '--memory=4g', '--network=none'] ['--cap-drop=all', '--security-opt=no-new-privileges', '--pids-limit=4096', '--memory=4g', '--volume']`

## Journal
