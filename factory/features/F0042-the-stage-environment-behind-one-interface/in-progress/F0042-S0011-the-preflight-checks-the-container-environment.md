---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 422
comments_read: [6389680101]
handed_over: null
claim: null
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
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-24T21:27:46.697350Z'
  stage: tests
  run: 16d4bb7b605a458ea547ec9eae74b1ce
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-24T21:28:07.346719Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-24T21:35:43.977138Z'
  stage: doing
  run: 35c95b3e8a784b47aa178999005f7c2c
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-24T21:36:04.934432Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-24T21:37:55.204011Z'
  stage: review
  run: 60f5b852070644f686f6e0f91f92a0bf
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-24T21:38:15.394308Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-24T21:38:33.083721Z'
  stage: doing
  run: 8215348cf8b44c81b6a321b605bfef88
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-24T21:38:53.965728Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-24T21:42:24.204925Z'
  stage: tests
  run: b9d7476cdffa441ebf90ccad8ec0fb5f
---

# The preflight checks the container environment

## Description

The preflight checks the machine once per image build before any claim, and probes `main` once per commit (`docs/project-guide/watching.md`, the operator guide's *The preflight's items*). A `container` instance needs other items than an `inline` one: that `podman` and `zfs` answer `--version`, that the dataset exists (`zfs list -H -o name <dataset>` names it) and that the stage image is there (`podman image exists <image>`); and its two probes, the agent run and the `lint` on `main`, must go through the environment like a stage, so that the dataset is prepared for `main` before either runs. The items `agent-user`, `tool:sudo`, `confinement` and `agent-environment` check layers a container replaces, or a `HOME` that is a path inside the container, and the items `tool:claude` and `tool:opencode` look for the runtime's executable on the host's `PATH`, where a `container` instance has none, and the item `tool:make` looks for `make`, which a `container` instance runs only inside its sync and check containers; none of them is run for `container`; the `opencode` item checks the model aliases only, since the executable is the stage image's and `agent-runtime-version` runs it there (decision 15 of `feature.md`). The `inline` environment keeps today's items unchanged, in their order. This story adds the four items to `factory.application.preflight`, gives `MachineChecks.run` the tools `CONTAINER_TOOLS` (`git` and `uv`, without `make` and the runtime's executable) for `container`, makes both probes call `prepare`, and makes `machine_extras` of the wiring choose the items by the environment. The items are tested with callables and the stand-in adapters of S0002 and S0003; the probes with `FakeSnapshots` and `FakeContainerRuns`. What stays: every item an `inline` instance runs today, word for word; the probe of the agent run only resolves `origin/main` first, which an `inline` instance always has after the tick's restore.

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
8. tester: I wrote the tests for criteria 1 to 10. The human's answer settled the `tool:make` question: a `container` instance checks `tool:git` and `tool:uv` only, through `CONTAINER_TOOLS`. The test checks the item names and does not name the constant.

   Criterion → test:
   - criterion 1: tests/application/test_container_items.py::test_a_tool_passes_with_its_version_line_or_fails_naming_the_error (rows: podman passes and fails, zfs passes and fails)
   - criterion 2: tests/application/test_container_items.py::test_the_dataset_item_passes_when_the_dataset_exists_and_says_how_to_make_it
   - criterion 3: tests/application/test_container_items.py::test_the_stage_image_item_passes_when_the_image_is_built_and_says_how_to_build_it
   - criterion 4: tests/application/test_opencode_item_container.py::test_a_container_instance_s_opencode_item_ignores_the_path_and_checks_the_aliases
   - criterion 5: tests/application/test_agent_run_probe_environment.py::test_the_probe_runs_after_the_dataset_is_prepared_for_main
   - criterion 6: tests/application/test_agent_run_probe_environment.py::test_a_fault_of_preparing_the_environment_fails_the_probe_before_any_run (rows: no-main with an empty bare remote and its clone, no-base, sync-fails)
   - criterion 7: tests/application/test_preflight_run_environment.py::test_the_lint_probe_runs_in_a_check_container_after_the_environment_is_prepared (rows: passes, sync-fails, no-base; `project_commands` is a `ContainerMakeCommands` on the fakes)
   - criterion 8: tests/entry/test_wiring_container_extras.py::test_the_extras_are_chosen_by_the_stage_environment_in_the_operator_guides_order (four rows: container, container-opencode, and the two inline rows of test_wiring_extras.py)
   - criterion 9: tests/entry/test_wiring_container_extras.py::test_the_container_items_run_the_podman_and_zfs_the_settings_name. Its last clause (no `agent-user`, `tool:sudo`, `agent-environment` or `confinement` for `container`) is covered by criterion 8's exact lists.
   - criterion 10: tests/application/test_machine_checks_container.py::test_a_container_instance_checks_git_and_uv_but_no_make_and_no_runtime_executable (rows: container, container-opencode, inline). Each row passes one extra item, so the test also checks that the extras follow the first items.
   - criteria 11 and 12: no test (make check, docs).

   Two assertions go a little past the criteria's wording. Both follow from the Interface's order (prepare first, then run):
   - Criterion 6's sync-fails row also checks that the runtime got no request. The criterion says this only for the other two rows.
   - Criterion 7's `prepare` rows check that no `factory-check` call ran.

   Files created:
   - tests/application/test_container_items.py
   - tests/application/test_opencode_item_container.py
   - tests/application/test_machine_checks_container.py
   - tests/application/test_agent_run_probe_environment.py
   - tests/application/test_preflight_run_environment.py
   - tests/entry/test_wiring_container_extras.py

   I changed no earlier test file.

   `make test` (one run, last five lines): tests/application/test_container_items.py cannot be imported, because `factory.application.preflight` has no `tool_version_item`, `dataset_item` or `stage_image_item` yet. The three rows of the probe-fault test fail with `assert not True`: today the probe passes without preparing. The five lines show nothing else; the factory records the full last line. `make lint`: green. I skipped the type check, as the stage says.

   `lint`: lint: green (0.6 s)
   `test`: ERROR tests/application/test_container_items.py - ImportError while importing test module '/work/checkout/tests/application/test_container_items.py'.
9. factory: started doing as self.
10. coder: I built the container preflight: four new items, both probes now go through the stage environment, and the wiring picks the items by environment. All six of the tester's files pass, and `make check` is green after the refactor.

    What I built:
    - `src/factory/application/preflight.py`:
      - Three new items, `tool_version_item`, `dataset_item` and `stage_image_item`, with `_DATASET_ITEM` and `_STAGE_IMAGE_ITEM`.
      - `CONTAINER_TOOLS = ("git", "uv")` sits beside `REQUIRED_TOOLS`, as the human's answer asked. `MachineChecks._tools()` returns it for `container`, so no `make` and no runtime executable are checked. `inline` is unchanged.
      - For `container`, `opencode_item` skips the `PATH` check and checks only the aliases.
      - `agent_run_probe_item` resolves `origin/main` first. With no `origin/main` it fails with `no origin/main to prepare the stage environment from`. Otherwise it calls `prepare(main, MAIN_BRANCH, sync_time_limit=PROBE_TIME_LIMIT)` and then `run_agent` on the same environment. `SnapshotError` and `ContainerError` fail the item with the error's text.
      - `Preflight._run_probe` calls `prepare` after the checkout and reset of `main`. `Preflight.run` now also catches `SnapshotError` and `ContainerError`, with the same stop detail.
    - `src/factory/entry/wiring.py`:
      - `machine_extras` keeps `token-file` first. It then adds `_container_items` (`podman`, `zfs`, `dataset`, `stage-image`) or `_inline_items` (today's `agent-user`, `tool:sudo`, `agent-environment`, `confinement`, unchanged). The `opencode` and `agent-run-probe` items follow, as before.
      - Both `_container_environment` and `_container_items` now build the adapters through one private `_container_adapters(settings)`. Building them runs no command.

    Main choice: `_container_adapters` returns a small frozen dataclass, `_ContainerAdapters`. It holds the adapters plus the dataset and image names already checked against `None`, so the items get typed `str` names. I rejected two alternatives:
    - Public `dataset` and `image` properties on `ZfsSnapshots` and `PodmanRuns`: that would widen the adapters for the wiring's sake.
    - Reading `settings.dataset` again in the items: mypy would need a second `None` check.

    Refactor: the only change was renaming a local in `agent_run_probe_item` to `stage_environment`.

    Noticed, not touched:
    - The coverage report shows one line of `wiring.py` uncovered (line 390). By my count of the diff that is the `SettingsInvalid` raise in `_container_adapters`; the raise was already there before, I only moved it. I didn't open the line to confirm.
    - `sast` prints bandit's `nosec encountered (B606)` warning for `process.py`. That marker is the exception `CLAUDE.md` allows.

    Journal: the human's answer fixed `CONTAINER_TOOLS` as a named constant and the `container` tool list as git and uv only. That only makes the Interface sentence more precise, so I left `## Description` as it is.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 36 known, 2 gone
11. factory: started review as self.
12. reviewer: Groups 1 to 3 pass. I read every criterion and every rule of the Interface against the six new test files, `src/factory/application/preflight.py` and `src/factory/entry/wiring.py`.
    - Criteria 1 to 10 each have a parametrized test that checks what the criterion names. That includes both errors of `tool_version_item`, the three faults of the probe, both caught errors in `Preflight.run`, and both forms of the `opencode` item.
    - The rule "building the adapters runs no command" stays covered by `tests/entry/test_wiring_stage_environment.py::test_wiring_a_container_instance_s_tick_starts_no_tool`, because `build_tick` calls `machine_extras`.
    - Layers hold. No silencing marker was added. The coder's `make check` was green (entry 10).
    - The 11 new findings from `make duplicates` all sit in modules this diff does not touch.

    Group 4 (quality) fails. This is round 0, so test-file copies count as findings:

    1. `tests/application/test_machine_checks_container.py:35-39`: the fixture `installed` is a word-for-word copy of `installed` in `tests/application/test_machine_checks_runtime.py:32-36`. Fix: the tester moves it to `tests/conftest.py` under the standing leave, and both modules use it from there.
    2. `tests/application/test_machine_checks_container.py:16-21` and `tests/application/test_opencode_item_container.py:13-18`: the same `CONTAINER` settings dict is defined in two new modules. The container `InstanceSettings` is also built twice, in `test_agent_run_probe_environment.py:29-42` (fixture `container_settings`) and in `test_preflight_run_environment.py:66-76`. Fix: one shared constant or builder in a support module (e.g. `tests/container_support.py`), used by all four.
    3. `tests/application/test_container_items.py:11-12`: it defines `DATASET` and `IMAGE` again, though `tests/zfs_support.py:14` and `tests/podman_support.py:10` already hold them. `tests/entry/test_wiring_container_extras.py` imports those. Fix: import them instead of redefining them.

    Description corrected:
    - It said: "leaves the runtime's executable out of `MachineChecks.run`'s tools for `container`". It now says: "gives `MachineChecks.run` the tools `CONTAINER_TOOLS` (`git` and `uv`, without `make` and the runtime's executable) for `container`".
    - Added to the list of items not run for `container`: "the item `tool:make` looks for `make`, which a `container` instance runs only inside its sync and check containers".

    Both corrections follow the human's answer in entry 6. Its Interface sentence ("`REQUIRED_TOOLS` alone") is left as the human said to read it.

    Earlier tests: none. Every test file in the diff is new (status `A`).
13. factory: started doing as self.
14. coder: All three of the reviewer's findings in entry 12 are changes to tests, so I changed no code and no test. They fall under the standing leave to move a shared test helper, and the tester makes them:

    1. Move the fixture `installed` to `tests/conftest.py`. It is in `tests/application/test_machine_checks_container.py:35-39` and in `tests/application/test_machine_checks_runtime.py:32-36`. Both modules then use the shared fixture.
    2. Move the container settings to one shared support module, for example `tests/container_support.py`. Today they are in four places:
       - the `CONTAINER` settings dict in `tests/application/test_machine_checks_container.py:16-21`
       - the same dict in `tests/application/test_opencode_item_container.py:13-18`
       - the container `InstanceSettings` built by the fixture `container_settings` in `tests/application/test_agent_run_probe_environment.py:29-42`
       - the same `InstanceSettings` built again in `tests/application/test_preflight_run_environment.py:66-76`

       All four modules then use the shared constant or builder.
    3. In `tests/application/test_container_items.py:11-12`, drop the local `DATASET` and `IMAGE`. Import them from `tests/zfs_support.py` and `tests/podman_support.py`, as `tests/entry/test_wiring_container_extras.py` already does.

    Every test keeps its name and checks the same thing. All the files above are new on this branch except `tests/application/test_machine_checks_runtime.py`, an earlier story's module, which only changes to use the shared fixture.

    I did not run `make check` this round, because I changed nothing. The code under `src/factory` is as I left it in entry 10, when `make check` was green.
15. factory: started tests as self.
16. tester: I made the three helper moves the coder named in entry 14 for the reviewer's findings in entry 12. They fall under the standing leave in `CLAUDE.md`. Every test keeps its name and checks the same thing. I changed no code under `src/factory` and added no test.

    1. The fixture `installed` now lives in `tests/conftest.py`. I removed its two copies, from `tests/application/test_machine_checks_container.py` and from `tests/application/test_machine_checks_runtime.py`. Both modules now use the shared fixture, and the imports it needed are gone from them.
    2. `tests/container_support.py` now holds two shared pieces:
       - `CONTAINER`, the settings fields of a container instance, built from `DATASET` and `MOUNT_POINT` of `tests/zfs_support.py` and `IMAGE` of `tests/podman_support.py`. The values are the same as before.
       - `container_instance_settings(tmp_path, agent_home)`, which builds the container `InstanceSettings` with the state at `tmp_path/state` and the workspace at `tmp_path/workspace`. Those are the same values as before: `dataset.workspace` is `tmp_path/workspace`.

       Four modules now use them:
       - `tests/application/test_machine_checks_container.py` and `tests/application/test_opencode_item_container.py` import `CONTAINER` instead of their own dicts.
       - The fixture `container_settings` in `tests/application/test_agent_run_probe_environment.py` returns `container_instance_settings(...)`.
       - `tests/application/test_preflight_run_environment.py` calls `container_instance_settings(...)` instead of building the settings inline.
    3. `tests/application/test_container_items.py` no longer defines its own `DATASET` and `IMAGE`. It imports them from `tests/zfs_support.py` and `tests/podman_support.py`.

    Files I created: none.

    Files I changed:
    - New on this branch: the five test modules above, and `tests/container_support.py`.
    - From earlier stories, changed under the standing leave: `tests/conftest.py` (added the fixture `installed`) and `tests/application/test_machine_checks_runtime.py` (now uses the shared fixture instead of its own copy).

    Modules the test run could not import: none. The code already exists, so `make test` is green (last line `test: green (67.9 s)`, coverage 99.19 %). `make lint` is green after ruff sorted the imports in `test_container_items.py`. As the stage says, I did not run the type check.

    `lint`: lint: green (0.5 s)
    `test`: test: green (65.2 s)
