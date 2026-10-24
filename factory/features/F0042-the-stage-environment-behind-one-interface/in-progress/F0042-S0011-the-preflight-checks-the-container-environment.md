---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 422
comments_read: [6389680101]
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-24T21:21:52.918786Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T21:17:12.657451Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T21:17:12.663119Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T21:17:34.022830Z'
  stage: intake
  run: efd6e38c6de2461091caf450bc4a228c
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T21:17:54.169017Z'
  stage: tests
- number: 5
  speaker: tester
  kind: question
  at: '2026-10-24T21:19:13.665087Z'
  stage: tests
  run: fa5361a9f91c47f2bf0cbe9ef9709097
  blocked: question
- number: 6
  speaker: human
  kind: comment
  at: '2026-10-24T21:21:34.887322Z'
  stage: tests
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-24T21:21:52.918786Z'
  stage: tests
---

# The preflight checks the container environment

## Description

The preflight checks the machine once per image build before any claim, and probes `main` once per commit (`docs/project-guide/watching.md`, the operator guide's *The preflight's items*). A `container` instance needs other items than an `inline` one: that `podman` and `zfs` answer `--version`, that the dataset exists (`zfs list -H -o name <dataset>` names it) and that the stage image is there (`podman image exists <image>`); and its two probes, the agent run and the `lint` on `main`, must go through the environment like a stage, so that the dataset is prepared for `main` before either runs. The items `agent-user`, `tool:sudo`, `confinement` and `agent-environment` check layers a container replaces, or a `HOME` that is a path inside the container, and the items `tool:claude` and `tool:opencode` look for the runtime's executable on the host's `PATH`, where a `container` instance has none; none of them is run for `container`; the `opencode` item checks the model aliases only, since the executable is the stage image's and `agent-runtime-version` runs it there (decision 15 of `feature.md`). The `inline` environment keeps today's items unchanged, in their order. This story adds the four items to `factory.application.preflight`, leaves the runtime's executable out of `MachineChecks.run`'s tools for `container`, makes both probes call `prepare`, and makes `machine_extras` of the wiring choose the items by the environment. The items are tested with callables and the stand-in adapters of S0002 and S0003; the probes with `FakeSnapshots` and `FakeContainerRuns`. What stays: every item an `inline` instance runs today, word for word; the probe of the agent run only resolves `origin/main` first, which an `inline` instance always has after the tick's restore.

## Interface

`factory.application.preflight` (`application`):

```python
_DATASET_ITEM = "dataset"
_STAGE_IMAGE_ITEM = "stage-image"


def tool_version_item(name: str, version: Callable[[], str]) -> PreflightItem:
    """Check that the tool `name` answers `--version`: `version()` returns its line or raises."""


def dataset_item(dataset: str, exists: Callable[[], bool]) -> PreflightItem:
    """Check that the ZFS dataset `dataset` exists."""


def stage_image_item(image: str, exists: Callable[[], bool]) -> PreflightItem:
    """Check that the stage image `image` is built."""


def opencode_item(
    settings: InstanceSettings,
    environment: Mapping[str, str],
    find: Callable[[str, str], str | None],
    agent_models: Sequence[str],
) -> PreflightItem: ...
```

- `tool_version_item("podman", version)` passes with `detail` the line `version()` returned (so the factory log names the version once per image build, as the probe's login line is logged), and fails with `detail` `<name> does not answer --version: <the error's message>` when `version()` raises `SnapshotError` or `ContainerError`; the item's name is `name` (`podman`, `zfs`).
- `dataset_item(dataset, exists)` passes when `exists()` is true; fails with `detail` `the dataset <dataset> does not exist; make it with zfs create, and its base with zfs snapshot <dataset>@base` when false; fails with `detail` `cannot list the dataset <dataset>: <message>` when `exists()` raises `SnapshotError`.
- `stage_image_item(image, exists)` passes when true; fails with `detail` `the stage image <image> is not built; build it with podman build` when false; fails with `detail` `cannot look for the stage image <image>: <message>` on `ContainerError`.
- `opencode_item` for `settings.stage_environment == "container"` checks the aliases only: a missing `PATH` entry or a missing executable on it is no fault; the alias faults are as today. For `inline` it is unchanged.
- `agent_run_probe_item(boundaries, settings, environment)`: before the run, `main = boundaries.git.resolve("origin/main")`; `None` fails the item with `detail` `no origin/main to prepare the stage environment from`; otherwise `stage_environment_of(boundaries).prepare(main, MAIN_BRANCH, sync_time_limit=PROBE_TIME_LIMIT)` and then `run_agent(request)` on the same object, as S0005 left it. `SnapshotError` and `ContainerError` from `prepare` fail the item with `str(error)` as the detail, as an `AgentRuntimeError` does. For the inline environment `prepare` does nothing and `resolve` is the one new git call.
- `Preflight._run_probe`: after the checkout and reset of `main`, `stage_environment_of(boundaries).prepare(main, MAIN_BRANCH, sync_time_limit=PROBE_TIME_LIMIT)` before `project_commands.run(PROBE_COMMAND, ...)`; `Preflight.run` catches `SnapshotError` and `ContainerError` beside `GitError` and `ProjectCommandError` around the probe, with the same `the probe on main could not run: <error>` detail and the `preflight_failed` stop.

- `MachineChecks.run`: for `settings.stage_environment == "container"` the tools are `REQUIRED_TOOLS` alone, without the runtime's executable (`tool:claude` or `tool:opencode`; decision 15 of `feature.md`); `agent-runtime-version` runs the executable in the stage image (S0008) and is the check of its presence. For `inline` it is unchanged.

`factory.entry.wiring` (`entry`): `machine_extras(boundaries, settings, which, environment)`:

- For `inline`: unchanged (`token-file`, `agent-user`, `tool:sudo` with an agent user, `agent-environment`, `confinement`, `opencode` under opencode, `agent-run-probe`).
- For `container`: `token-file`, `podman` (`tool_version_item("podman", <the PodmanRuns of the boundaries>.version)`), `zfs` (`tool_version_item("zfs", <the ZfsSnapshots>.version)`), `dataset` (`dataset_item(settings.dataset, <the ZfsSnapshots>.dataset_exists)`), `stage-image` (`stage_image_item(settings.stage_image, <the PodmanRuns>.image_exists)`), `opencode` under opencode, `agent-run-probe`; in that order. `machine_extras` builds the two adapters from the settings as `build_boundaries` does (`ZfsSnapshots(settings.dataset, settings.workspace, executable=settings.zfs_executable)` and `PodmanRuns(settings.podman_executable, settings.stage_image, settings.workspace)`, through one private function of the wiring that both call), so its signature, `build_tick` and `tests/wiring_support.py` stay as they are; `boundaries.snapshots` and `boundaries.containers` stay typed as the interfaces, and no `isinstance` narrows them. Building the adapters runs no command (S0010's criterion 7 stays true).

Tests (the tester writes them): `tests/application/test_container_items.py` (the four items with callables), `tests/application/test_agent_run_probe_environment.py` and `tests/application/test_preflight_run_environment.py` (the probes on boundaries with `FakeSnapshots`, `FakeContainerRuns`, a `Makefile` with `sync` and `lint` pushed to `main`, and `FakeAgentRuntime`), `tests/application/test_opencode_item_container.py`, `tests/application/test_machine_checks_container.py` (`MachineChecks.run` with a `which` that records the names it is asked for), `tests/entry/test_wiring_container_extras.py` (the order, with `machine_item` of `tests/wiring_support.py` and stand-in `zfs` and `podman` scripts). `tests/entry/test_wiring_extras.py` and the existing probe tests are unchanged.

## Acceptance criteria

1. `tool_version_item` (rows of one parametrized test): `version` returning `podman version 4.9.3` gives `PreflightItem(name="podman", passed=True, detail="podman version 4.9.3")`; `version` raising `ContainerError("podman --version", "exit status 127")` gives `passed` false and `detail` `podman does not answer --version: container command podman --version failed: exit status 127`; the same with `zfs` and a `SnapshotError`.
2. `dataset_item("tank/factory/vm", exists)` (rows of one parametrized test): `True` passes with the name `dataset`; `False` fails with `detail` `the dataset tank/factory/vm does not exist; make it with zfs create, and its base with zfs snapshot tank/factory/vm@base`; a `SnapshotError("zfs list -H -o name tank/factory/vm", "permission denied")` fails with `detail` `cannot list the dataset tank/factory/vm: snapshot command zfs list -H -o name tank/factory/vm failed: permission denied`.
3. `stage_image_item("factory-stage:1", exists)` (rows of one parametrized test): `True` passes with the name `stage-image`; `False` fails with `detail` `the stage image factory-stage:1 is not built; build it with podman build`; a `ContainerError("podman image exists factory-stage:1", "cannot connect")` fails with `detail` `cannot look for the stage image factory-stage:1: container command podman image exists factory-stage:1 failed: cannot connect`.
4. `opencode_item` (rows of one parametrized test): `container` settings with an environment without `PATH` and every alias mapped passes; `container` settings with a `PATH` on which `find` finds no `opencode` and every alias mapped passes; `container` settings with an unmapped alias `sonnet` fails with `detail` `no model is set for sonnet in FACTORY_OPENCODE_MODELS` only; `inline` settings with an environment without `PATH` fail with `the agent run has no PATH` as today.
5. `agent_run_probe_item` on boundaries with `FakeSnapshots`, `FakeContainerRuns` and a `FakeAgentRuntime` with a completed run queued, the host checkout fetched and on `main` at `origin/main` as the tick's restore leaves it (the sync container fetches the host's local branches only): the item passes, and afterwards the dataset's checkout is on `main` at `origin/main`'s commit with the `sync` marker written, and `snapshots.changed_paths()` is `[]` (the base moved; the fake run writes into the host checkout, not the dataset); the fake runtime's one request is the probe's (prompt `PROBE_PROMPT`, decisions `["question"]`, the coder's budget 0.10).
6. The probe's faults (rows of one parametrized test): a remote without `main` (an empty bare remote) fails the item with `detail` `no origin/main to prepare the stage environment from` and the runtime got no request; a `FakeSnapshots` without a base fails it with `detail` `snapshot command reset failed: no base at <base>` and the runtime got no request; a `Makefile` whose `sync` exits 1 printing `boom` fails it with `detail` `container command sync failed: boom`.
7. `Preflight.run` on container-fake boundaries with a passing machine report: the `lint` probe runs after `prepare`: the fake containers recorded, in order, the sync container of the probe's `prepare` and then the check container (`factory-check` among its words with `lint` last), the result passes and the stamp records `main_probed`; with a `Makefile` whose `sync` exits 1 printing `boom`, `Preflight.run` returns `preflight_failed` and the stop's detail is `the probe on main could not run: container command sync failed: boom`; with a `FakeSnapshots` without a base, it returns `preflight_failed` and the stop's detail is `the probe on main could not run: snapshot command reset failed: no base at <base>`; in both rows no check container ran (rows of one parametrized test).
8. `machine_extras` (rows of one parametrized test, with stand-in `zfs` and `podman` scripts that answer `--version`, `list` and `image exists` as planned): `container` settings give the names `["token-file", "podman", "zfs", "dataset", "stage-image", "agent-run-probe"]`; `container` with `FACTORY_AGENT_RUNTIME=opencode` gives `[..., "stage-image", "opencode", "agent-run-probe"]`; `inline` without and with an agent user give today's two lists (the rows of `tests/entry/test_wiring_extras.py`, repeated here unchanged so that the one test holds all four).
9. The four items run the adapters the wiring built: with the stand-in `podman` of `tests/podman_support.py` (one plan for every call, so the test plans it again between the calls) planned to print `podman version 4.9.3` and exit 0 for the `podman` item and to exit 1 for the `stage-image` item, the workspace an existing folder under `tmp_path` (`PodmanRuns` runs its queries there), and `zfs` planned to print `zfs-2.2.2` and `list` to exit 0 with the dataset's name, `machine_item(..., "podman")` passes with that detail, `machine_item(..., "stage-image")` fails with `the stage image factory-stage:1 is not built; build it with podman build`, `machine_item(..., "dataset")` passes; and the inline items `agent-user`, `tool:sudo`, `agent-environment` and `confinement` are absent from the container list (criterion 8's list has none of them).
10. `MachineChecks.run` (rows of one parametrized test, with a `which` that finds every tool and records the names it is asked for): `container` settings under Claude Code give the first five item names `tool:git`, `tool:uv`, `hosting-service`, `agents`, `agent-runtime-version` (no `tool:make`: decision 15), then the extras, and `which` was not asked for `claude`; `container` settings under opencode give the same names, and `which` was not asked for `opencode`; `inline` settings under Claude Code give today's `tool:git`, `tool:uv`, `tool:make`, `tool:claude`, `hosting-service`, `agents`, `agent-runtime-version`.
11. `make check` stays green.
12. docs: `docs/operator-guide.md`, *The preflight's items*: the four rows `podman`, `zfs`, `dataset`, `stage-image` (what passes, the detail, what to do), one sentence per item an `inline` instance runs that a `container` instance does not and why, the `opencode` item's two forms, the probes' `prepare` and the new form of `the probe on main could not run`, and the count of items for each environment; *The probe of the agent run*: the dataset is prepared for `main` first and the two faults it adds; `docs/project-guide/stage-environment.md` gains the section *The preflight* (the items, the callables, the probes through the environment, the runtime's tool left out for `container`), and its line in `docs/project-guide/README.md`, *The files*, names that section; `docs/project-guide/processes-and-checks.md` (which names `factory.application.preflight`): one sentence pointing there; `docs/project-guide/watching.md`: the extras' order for `container`, and that `MachineChecks.run` checks no runtime executable for it. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
from factory.application.preflight import dataset_item, stage_image_item, tool_version_item
from factory.domain.errors import ContainerError, SnapshotError

def fails(error):
    def raise_it():
        raise error
    return raise_it

print(tool_version_item("podman", lambda: "podman version 4.9.3").model_dump())
print(tool_version_item("zfs", fails(SnapshotError("zfs --version", "exit status 127"))).detail)
print(dataset_item("tank/factory/vm", lambda: False).detail)
print(stage_image_item("factory-stage:1", fails(ContainerError("podman image exists factory-stage:1", "cannot connect"))).detail)
EOF
```
Expect: four lines: `{'name': 'podman', 'passed': True, 'detail': 'podman version 4.9.3'}`; `zfs does not answer --version: snapshot command zfs --version failed: exit status 127`; `the dataset tank/factory/vm does not exist; make it with zfs create, and its base with zfs snapshot tank/factory/vm@base`; `cannot look for the stage image factory-stage:1: container command podman image exists factory-stage:1 failed: cannot connect`

```bash
uv run pytest tests/application/test_container_items.py tests/application/test_agent_run_probe_environment.py tests/application/test_preflight_run_environment.py tests/application/test_opencode_item_container.py tests/application/test_machine_checks_container.py tests/entry/test_wiring_container_extras.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`factory.application.preflight`: `tool_version_item`, `dataset_item`, `stage_image_item`, `opencode_item`; `factory.entry.wiring.machine_extras`), and the probe and `MachineChecks.run` changes are stated with exact details and error types. The wiring places the adapters correctly (built from settings in entry, interfaces kept in boundaries).
   Criteria: 1 to 4 cover each item's pass side and each failing side with exact detail strings, both error types included. 5 and 6 cover the probe's pass side and its three faults (no origin/main, SnapshotError, ContainerError). 7 covers the lint probe order after prepare and both caught errors with the stop detail. 8 to 10 cover the extras' order for each environment and runtime, the adapters actually run, and `MachineChecks.run`'s tools for container and inline. Each is testable by one parametrized test function without further decisions. Every Interface clause has a criterion, and none needs a decision the story leaves open.
   Smoke test: both blocks are runnable. The pytest command passes no `-q`, and `pyproject.toml` `addopts` sets a single `-q`, so the last line is the `N passed in ...` summary that the `grep -cE` matches. Each Expect line gives an exact, checkable output.
   Architecture: the items and probes sit in `application`. The `podman`/`zfs` adapters are reached only through their wrapper classes, built in `entry.wiring`. `boundaries.snapshots` and `boundaries.containers` stay typed as the interfaces, which fits the layer rules and decisions 1 and 15 of `feature.md`.
   Scope: it matches the S0011 line in the feature's Scope. It removes no layer and does not touch the inline items. The test files it names are new, and it changes no earlier test.
4. factory: started tests as self.
5. tester: Question before the tests: does a `container` instance check `tool:make`?

   The Interface and criterion 10 disagree:
   - Interface, `MachineChecks.run`: "for `settings.stage_environment == "container"` the tools are `REQUIRED_TOOLS` alone, without the runtime's executable". `REQUIRED_TOOLS` is still `("git", "uv", "make")` (`src/factory/application/preflight.py:50`), so the items would be `tool:git`, `tool:uv`, `tool:make`, `hosting-service`, `agents`, `agent-runtime-version`.
   - Criterion 10: "`container` settings ... give the first five item names `tool:git`, `tool:uv`, `hosting-service`, `agents`, `agent-runtime-version` (no `tool:make`: decision 15)". That leaves `make` out as well.
   - The Description says only that the runtime's executable is left out for `container`. It says nothing about `make`.

   Options:
   A. Criterion 10 is right. A container instance runs `make` only inside the sync and check containers, so the host checks `git` and `uv` only. The Interface sentence would then read "`REQUIRED_TOOLS` without `make` and without the runtime's executable". It would also need to say how: a second constant, or a filter in `MachineChecks.run`. Note that `tests/test_make_search.py` allows the string `"make"` only in `make_commands` and in `preflight`'s `REQUIRED_TOOLS`, and a filter like that may touch it.
   B. The Interface is right. For `container`, criterion 10's list becomes `tool:git`, `tool:uv`, `tool:make`, `hosting-service`, `agents`, `agent-runtime-version` (six names), and the "(no `tool:make`)" remark is dropped.

   I'd choose A, because criterion 10 cites decision 15 for it and the host never runs `make` in a container instance. Please confirm, and say whether the Interface should name a constant for the container's tools (for example `CONTAINER_TOOLS = ("git", "uv")`), so the test can name it or just check the item names.

   What I did: I read the work item, `factory.application.preflight`, `factory.application.stage_environment`, the fake snapshots and containers, `ContainerMakeCommands`, `tests/container_support.py`, `tests/wiring_support.py` and the current probe, preflight-run, machine-checks and wiring-extras tests. The other criteria (1 to 9) can be tested as written. I wrote no tests and created no files, so I have not run `make test` or `make lint` in this run. I'll write all six test files once this is answered.
6. 2026-10-24 human: A. Criterion 10 is right, by decision 15 of `feature.md` ("The item `tool:make` is not run for `container` either"): a `container` instance runs `make` only inside the sync and check containers, so the host checks `git` and `uv` only. Read the Interface sentence as "`REQUIRED_TOOLS` without `make` and without the runtime's executable". Name it as a constant in `factory.application.preflight`: `CONTAINER_TOOLS = ("git", "uv")`, beside `REQUIRED_TOOLS`, and `MachineChecks.run` uses it for `settings.stage_environment == "container"`; no filter on `REQUIRED_TOOLS`, so `tests/test_make_search.py` stays as it is. The test may name the constant and check the item names; for `inline` the items stay exactly as today.
7. factory: started tests as self.
