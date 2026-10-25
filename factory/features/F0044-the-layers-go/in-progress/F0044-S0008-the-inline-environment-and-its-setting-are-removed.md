---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 451
comments_read: [6401042995, 6401126933, 6401361580, 6401523245]
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-25T18:39:41.099596Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T17:47:39.260095Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T17:47:39.266053Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-25T17:48:01.235070Z'
  stage: intake
  run: e77602a1cabf45b5bd614c84636ea09d
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-25T17:49:17.708785Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-25T17:49:35.531640Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-25T17:49:55.229130Z'
  stage: intake
  run: 17f36ac62fe444399f4a3eb8ee039054
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-25T17:50:15.483400Z'
  stage: tests
- number: 8
  speaker: tester
  kind: question
  at: '2026-10-25T17:55:50.643103Z'
  stage: tests
  run: d8a4e097c52243d49318363f4fb42d6a
  blocked: question
- number: 9
  speaker: human
  kind: comment
  at: '2026-10-25T17:57:07.782087Z'
  stage: tests
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-25T17:57:25.632314Z'
  stage: tests
- number: 11
  speaker: tester
  kind: result
  at: '2026-10-25T17:58:58.095611Z'
  stage: tests
  run: 5ba88e1544d54d1d8ab35dfebdca02c3
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-25T17:59:19.221079Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-10-25T18:04:41.283195Z'
  stage: doing
  run: 86da23330be74429a155738618d3c84b
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-25T18:05:02.341179Z'
  stage: tests
- number: 15
  speaker: tester
  kind: question
  at: '2026-10-25T18:17:13.311598Z'
  stage: tests
  run: 0a06a1c175d14e588a7e95c08d7b3e1e
  blocked: question
- number: 16
  speaker: human
  kind: comment
  at: '2026-10-25T18:18:29.799664Z'
  stage: tests
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-25T18:18:47.762352Z'
  stage: tests
- number: 18
  speaker: tester
  kind: question
  at: '2026-10-25T18:25:18.709278Z'
  stage: tests
  run: 0330b823568646c199470d80435ad60e
  blocked: question
- number: 19
  speaker: human
  kind: comment
  at: '2026-10-25T18:33:46.154073Z'
  stage: tests
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-25T18:34:04.135175Z'
  stage: tests
- number: 21
  speaker: tester
  kind: result
  at: '2026-10-25T18:39:20.210376Z'
  stage: tests
  run: fe39a864fdf14e0c84da983f0ad74afb
- number: 22
  speaker: factory
  kind: started
  at: '2026-10-25T18:39:41.099596Z'
  stage: doing
---

# The inline environment and its setting are removed

## Description

F0042 kept v1.1's way, the agent in the factory's own checkout with the undo after it, as `InlineEnvironment`, chosen by `FACTORY_STAGE_ENVIRONMENT=inline`, so that `self` could keep building on Docker. After S0001 to S0006 the inline environment has lost every layer that made it safe, `self` builds this feature on the image it runs, which is not rebuilt from `main` after this story (an image with this story refuses an instance without a dataset), and after S0007 (the suite's stages run on the container fakes) the suite no longer needs it. This story removes it: `InlineEnvironment`, the choice in `stage_environment_of`, the setting `FACTORY_STAGE_ENVIRONMENT` and the faults that depended on it, the wiring's inline branch, and the preflight's items and branches that only an `inline` instance ran (`agent-environment`, the runtime's executable and `make` on the host's `PATH`, the `opencode` item's `PATH` check). `Boundaries.snapshots` and `Boundaries.containers` become required, every request's working directory is the dataset's checkout, and the dataset, the workspace and the stage image are required to build an instance's boundaries (decision 10 of `feature.md`). What stays: `ContainerEnvironment` as F0042 built it, the only environment; the runtimes' call without a container, for the suite (decision 2); `MakeProjectCommands` (decision 3); `read_settings` reading the six settings of F0042-S0010 less `FACTORY_STAGE_ENVIRONMENT`, with their faults (a relative `FACTORY_WORKSPACE`, F0043-S0002's checkout or state directory inside it); the undo's module, which nothing calls after this story and S0009 removes (decision 13).

## Interface

`factory.application.stage_environment` (`application`): `InlineEnvironment` and the import of `UndoService` go;

```python
def stage_environment_of(boundaries: Boundaries) -> StageEnvironment:
    """The container environment on the boundaries' snapshots and containers."""
```

`factory.application.boundaries.Boundaries` (`application`): `snapshots: Snapshots` and `containers: ContainerRuns`, both required (keyword fields without a default, before the fields with defaults).

`factory.application.task.StageTask` and `factory.application.preflight._probe_request`: `working_directory` is `boundaries.snapshots.mount_point / "checkout"`.

`factory.domain.settings` (`domain`): `STAGE_ENVIRONMENT_VARIABLE`, `StageEnvironmentName`, `InstanceSettings.stage_environment`, `stage_environment_fault` with its fault `missing for the container environment`, and the model validator's rules for `stage_environment == "container"` go. `dataset`, `workspace` and `stage_image` keep their types and `None` defaults; `read_settings` reads them as F0042-S0010 does for `inline` (no fault for a missing one). `workspace_overlap_fault(workspace: Path | None, checkout: Path, state_directory: Path) -> tuple[str, str] | None` loses its first parameter: `None` when `workspace` is `None`; otherwise first `(WORKSPACE_VARIABLE, "is not an absolute path")` for a relative workspace, then F0043-S0002's faults of a checkout and then a state directory that lies inside it. `read_settings` raises its fault as `SettingsInvalid`, and the model validator of `InstanceSettings` keeps calling it (a `ValidationError` with `<variable>: <fault>`), so a model built directly with a workspace refuses the same combinations as before.

`factory.entry.wiring` (`entry`):

- `build_boundaries(settings, token, *, hosting=None)` raises `SettingsInvalid(DATASET_VARIABLE, "missing")`, then `SettingsInvalid(WORKSPACE_VARIABLE, "missing")`, then `SettingsInvalid(STAGE_IMAGE_VARIABLE, "missing")` for the first of the three that is `None`, before it builds anything; otherwise it builds what F0042-S0010 builds for `container`.
- `agent_run_environment(settings, base)` sets `HOME` to `/work/home` (`WORK_HOME`), whatever the settings.
- `machine_extras` gives `token-file`, `podman`, `zfs`, `dataset`, `stage-image`, `opencode` under opencode, `agent-run-probe`, in that order.

`factory.application.preflight` (`application`): `agent_environment_item`, `_home_fault`, `_path_fault`, `_AGENT_ENVIRONMENT_ITEM`, `CONTAINER_TOOLS` (equal to the new `REQUIRED_TOOLS`) and `MachineChecks._runtime_executable` go; `REQUIRED_TOOLS = ("git", "uv")`; `MachineChecks.run` checks no runtime executable on the host; `opencode_item(settings, agent_models)` checks the model aliases only (decision 16).

`vm/setup.sh` (the coder's `vm/*`): the environment file it writes loses the line `FACTORY_STAGE_ENVIRONMENT=container`, which nothing reads; the VM's present file keeps it, unread, until the script runs again.

`tests/test_make_search.py::test_only_the_make_class_names_make` then finds the string `make` in `factory.adapters.make_commands` alone (leave, decision 24).

Tests (the leave is decision 24 of `feature.md`):

- Deleted whole: `tests/application/test_stage_environment.py`, `tests/application/test_agent_environment_item.py`, `tests/entry/test_wiring_extras_path.py`, F0042-S0010's `tests/entry/test_wiring_stage_environment_home.py` (its rows join criterion 5 here).
- `tests/application/test_stage_environment_of.py::test_the_container_environment_needs_both_snapshots_and_containers` becomes `test_the_environment_of_the_boundaries_is_the_container_one`; `tests/application/test_stage_environment_calls.py::test_a_stage_built_without_an_environment_runs_the_inline_one` and `tests/application/test_stall_environment.py::test_a_stall_built_without_an_environment_undoes_inline_as_before` are deleted.
- `tests/application/test_machine_checks_runtime.py::test_the_last_required_tool_is_the_runtime_s_executable` is deleted; F0042-S0011's `tests/application/test_machine_checks_container.py`, `tests/application/test_opencode_item_container.py` and `tests/entry/test_wiring_container_extras.py` lose their `inline` rows; `tests/application/test_opencode_item.py` (its three tests) calls the narrowed `opencode_item`; `tests/entry/test_wiring_extras.py` (both tests) expects the container list; `tests/test_make_search.py::test_only_the_make_class_names_make` expects `{"factory.adapters.make_commands"}`.
- F0042-S0010's `tests/domain/test_settings_stage_environment.py` and `tests/entry/test_wiring_stage_environment.py`: the rows of `FACTORY_STAGE_ENVIRONMENT` and of `inline` go, the faults of a missing dataset, workspace or image are `build_boundaries`' `missing`; F0043-S0002's `tests/domain/test_settings_paths.py`: the rows that set `FACTORY_STAGE_ENVIRONMENT` drop it, and the row of an `inline` instance whose checkout lies in the workspace becomes a refusal.
- The tests that build boundaries through the wiring give settings with a dataset, a workspace under `tmp_path` and a stage image, and a test that runs a stage or the probe through the wiring uses the stand-in `zfs` of `tests/zfs_support.py` and `podman` of `tests/podman_support.py`: `tests/wiring_support.py`, the fixture `hosted_environment` of `tests/conftest.py`, `tests/entry/test_wiring_boundaries.py` (its eleven tests that call `build_boundaries`), `tests/entry/test_wiring_run.py` (its three tests), `tests/entry/test_wiring_handlers.py::test_a_tick_over_the_handler_factory_runs_one_stage`, `tests/entry/test_wiring_environment.py::test_a_tick_in_the_production_environment_hands_the_agent_no_token`, `tests/entry/test_wiring_human_handlers.py::test_the_run_entry_runs_the_stage_of_a_started_story_without_a_pull_request`, `tests/entry/test_wiring_acceptance.py::test_without_an_acceptance_stage_the_handlers_build_refuse_and_a_story_still_ticks`, `tests/entry/test_wiring_preflight.py::test_the_built_tick_stops_at_a_failed_machine_item`, `tests/entry/test_wiring_api_login.py`, `tests/entry/test_wiring_login.py`, `tests/entry/test_wiring_provider_limit.py`, `tests/entry/test_wiring_opencode.py`, `tests/entry/test_wiring_command_records.py`, `tests/entry/test_wiring_known_results.py`, `tests/entry/test_wiring_project_agents.py`, `tests/entry/test_wiring_record_logs.py`, `tests/entry/test_wiring_stop_records.py`, `tests/entry/test_wiring_waiter.py` (their one test each), `tests/entry/test_run.py` (its ten tests that run `run_instance` or `main` on a valid environment), `tests/entry/test_run_health_file.py`, `tests/entry/test_run_waiter.py`, `tests/entry/test_watch_main.py` and `tests/entry/test_watch_settings.py::test_a_valid_environment_gets_past_the_settings_to_the_fixed_checkout`; each keeps its name and what it checks.
- `tests/application/test_task.py::test_the_request_carries_the_agent_checkout_and_guard_without_os_user` and the probe tests that read the request's working directory read the dataset's checkout alone.

## Acceptance criteria

1. The removed names (rows of one parametrized test): `InlineEnvironment` is no attribute of `factory.application.stage_environment`; `STAGE_ENVIRONMENT_VARIABLE` and `StageEnvironmentName` none of `factory.domain.settings`; `InstanceSettings.model_fields` holds no `stage_environment` and still holds `dataset`, `workspace`, `stage_image`; `agent_environment_item` is none of `factory.application.preflight`; `REQUIRED_TOOLS == ("git", "uv")`; `dataclasses.fields(Boundaries)` gives `snapshots` and `containers` without a default; `CONTAINER_TOOLS` is none of `factory.application.preflight`; `vm/setup.sh` holds no `FACTORY_STAGE_ENVIRONMENT`.
2. `stage_environment_of` of the `boundaries` fixture is a `ContainerEnvironment` on its snapshots and containers.
3. `FACTORY_STAGE_ENVIRONMENT` is read by nothing (rows of one parametrized test over `read_settings` with the base environment of `tests/settings_support.py` and the three container variables): with `FACTORY_STAGE_ENVIRONMENT=inline`, with `=podman` (refused until now) and without it, the settings are equal; `FACTORY_WORKSPACE=srv/work` is `SettingsInvalid` naming `FACTORY_WORKSPACE` with `is not an absolute path`, with and without `FACTORY_STAGE_ENVIRONMENT`; `FACTORY_WORKSPACE=/work` without `FACTORY_CHECKOUT` is `SettingsInvalid` naming `FACTORY_CHECKOUT` with `/work/checkout lies inside FACTORY_WORKSPACE`; the base environment without the three is read without a fault.
4. `build_boundaries` refuses an incomplete instance (rows of one parametrized test, each with `hosting` the fake): settings without a dataset raise `SettingsInvalid` naming `FACTORY_DATASET` with `missing`; with a dataset and without a workspace, `FACTORY_WORKSPACE`; with both and without an image, `FACTORY_STAGE_IMAGE`; without a dataset and with `hosting` left out, the refusal comes before PyGithub's `get_repo` is called; with all three the build succeeds, runs no `zfs` and no `podman` (the stand-ins record no call), and gives a `ZfsSnapshots`, a `PodmanRuns`, a runtime whose `containers is boundaries.containers` and project commands whose `inner` is a `ContainerMakeCommands`.
5. `agent_run_environment(settings, {"HOME": "/home/x", "PATH": "/usr/bin", "LANG": "C.UTF-8"})` gives `HOME` `/work/home` and keeps `PATH` and `LANG`, and the given dict is unchanged.
6. The preflight (rows of one parametrized test): `machine_extras` under Claude Code gives `token-file`, `podman`, `zfs`, `dataset`, `stage-image`, `agent-run-probe`, under opencode the same with `opencode` before `agent-run-probe`; `MachineChecks.run` with a `which` that records its names gives first `tool:git`, `tool:uv`, `hosting-service`, `agents`, `agent-runtime-version` and asks for neither `make`, `claude` nor `opencode`; `opencode_item(settings, ["sonnet"])` passes with every alias mapped and fails with `no model is set for sonnet in FACTORY_OPENCODE_MODELS` without.
7. The request of a stage task (composed by `TaskComposer` in `factory.application.task`, with `factory.application.take.agent_working_directory`) and the probe's request (`_probe_request`) have `working_directory == boundaries.snapshots.mount_point / "checkout"` (two rows of one parametrized test).
8. `workspace_overlap_fault(workspace, checkout, state_directory)` (rows of one parametrized test): a state directory inside the workspace gives `("FACTORY_STATE", "<state directory> lies inside FACTORY_WORKSPACE")`; a relative workspace together with an inner checkout gives the relative-workspace fault `("FACTORY_WORKSPACE", "is not an absolute path")` (checked first); a checkout and a state directory both inside the workspace give the checkout's fault (checkout before state directory); a `None` workspace gives `None`; `InstanceSettings(...)` built directly with an inner checkout raises a `ValidationError` whose text holds `FACTORY_CHECKOUT: <checkout> lies inside FACTORY_WORKSPACE`.
9. `make check` stays green.
10. docs: `docs/operator-guide.md`, *Configuration*: the row `FACTORY_STAGE_ENVIRONMENT` goes, the rows `FACTORY_DATASET`, `FACTORY_WORKSPACE` and `FACTORY_STAGE_IMAGE` say required, and the paragraph *The stage environment* says there is one; *The preflight's items*: the rows `agent-environment`, `tool:make` and the runtime's tool go, the `opencode` item has one form, and the count follows; *The agent runtime*, *The agent in a container*: one environment; *The agent run's `PATH` and `HOME`*: the `HOME` is `/work/home`, and no item `agent-environment` checks it; *The service*: the environment file's table loses the row `FACTORY_STAGE_ENVIRONMENT`; `docs/project-guide/stage-environment.md`: *The stage environment* and *The settings and the wiring* describe one environment and `build_boundaries`' three faults; `docs/project-guide/watching.md`, *Boundaries*: `snapshots` and `containers` are required; *The tick*: one list of machine extras, `opencode_item(settings, agent_models)`, and no runtime executable among the tools; `docs/project-guide/stage-environment.md`, the opening paragraph and *The cycle*: one environment; *`run_agent`*: no comparison with the inline environment; *The preflight*: one list of items and no `CONTAINER_TOOLS`; `docs/project-guide/processes-and-checks.md`, *Project commands*: the string `"make"` appears in `factory.adapters.make_commands` alone, as `tests/test_make_search.py` allows; *Running as another user*: no `inline` instance; `docs/project-guide/README.md`, *The files*: the line of `stage-environment.md` follows; `README.md`: the paragraph that names `FACTORY_STAGE_ENVIRONMENT` says that every stage runs in throwaway containers on a ZFS dataset and points to the operator guide's chapter `## The machine`. `docs/decisions.md`: the entry "One snapshot instead of many layers" gains one line that the inline environment and its setting went with v1.2 F0044-S0008.

## Smoke test

```bash
uv run python - <<'EOF'
import dataclasses
from factory.application import stage_environment
from factory.application.boundaries import Boundaries
from factory.application.preflight import REQUIRED_TOOLS
from factory.domain import settings

print(hasattr(stage_environment, "InlineEnvironment"), hasattr(settings, "STAGE_ENVIRONMENT_VARIABLE"), REQUIRED_TOOLS)
print([field.name for field in dataclasses.fields(Boundaries) if field.name in ("snapshots", "containers") and field.default is dataclasses.MISSING])
EOF
```
Expect: two lines: `False False ('git', 'uv')`; `['snapshots', 'containers']`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: Questions (the format check passed; no finding from it). The Interface, the smoke test, the architecture and the scope are in order. Two Interface behaviours have no criterion, so two testers could read them differently and both pass:

   1. The Interface says `factory.application.task.StageTask` and `factory.application.preflight._probe_request` take `working_directory` as `boundaries.snapshots.mount_point / "checkout"`. The Interface's test list names `test_task.py` and "the probe tests", but no acceptance criterion states the value. Should I add a criterion before the two closing ones? Suggested: "the request of a stage task and the probe's request have `working_directory == boundaries.snapshots.mount_point / "checkout"`" (two rows of one parametrized test). I would choose this.

   2. The `workspace_overlap_fault` rules lack their failing sides and their order:
      - Criterion 3 covers a relative workspace and a checkout inside the workspace. It has no row for a state directory inside the workspace (`<state directory> lies inside FACTORY_WORKSPACE`, naming `FACTORY_STATE_DIRECTORY`; please confirm the variable name and the exact wording).
      - The order is stated in the Interface (relative first, then checkout, then state directory) but has no row.
      - `None` for a `None` workspace has no row.
      - The Interface says the model validator of `InstanceSettings` keeps calling the function, so a model built directly refuses the same combinations with a `ValidationError` reading `<variable>: <fault>`. Nothing tests that.
      Should I add one criterion with rows for these? Suggested rows: state directory inside the workspace; a relative workspace together with an inner checkout, which gives the relative fault; a `None` workspace, which gives `None`; and `InstanceSettings(...)` built directly with an inner checkout, which gives a `ValidationError`. I would choose this.
4. 2026-10-25 human: Yes to both, as you suggest.
   1. Add the criterion before the two closing ones: the request of a stage task and the probe's request have `working_directory == boundaries.snapshots.mount_point / "checkout"` (two rows of one parametrized test). The class that composes the stage request on `main` is `TaskComposer` in `factory.application.task`, and S0007 put the value in `factory.application.take.agent_working_directory`.
   2. Add one criterion with these rows. The variable is `FACTORY_STATE` (`STATE_VARIABLE` in `factory.domain.settings`), and the wording is today's `f"{path} lies inside FACTORY_WORKSPACE"`:
      - a state directory inside the workspace gives `("FACTORY_STATE", "<state directory> lies inside FACTORY_WORKSPACE")`;
      - a relative workspace together with an inner checkout gives the relative-workspace fault (it is checked first);
      - a checkout and a state directory both inside the workspace give the checkout's fault (checkout before state directory);
      - a `None` workspace gives `None`;
      - `InstanceSettings(...)` built directly with an inner checkout raises a `ValidationError` whose text holds `FACTORY_CHECKOUT: <checkout> lies inside FACTORY_WORKSPACE`.
5. factory: started intake as self.
6. intake: accepted
   Carried in from journal entry 4 (the human's answer to my questions in entry 3): I added two criteria before the two closing ones, which are now 9 (`make check`) and 10 (`docs:`). New criterion 7: the stage task's request and the probe's request have `working_directory == boundaries.snapshots.mount_point / "checkout"`. New criterion 8: the rows of `workspace_overlap_fault` and the `InstanceSettings` validator. These are the rows the human listed: a state directory inside the workspace, with `FACTORY_STATE` and the wording `<path> lies inside FACTORY_WORKSPACE`; relative workspace first; checkout before state directory; a `None` workspace; and a direct `InstanceSettings` with an inner checkout giving a `ValidationError`. The Description is unchanged, because the task's meaning did not change.
   - Interface: concrete modules and signatures (`stage_environment_of`, `Boundaries`, `workspace_overlap_fault`, `build_boundaries`, `agent_run_environment`, `machine_extras`, `opencode_item`, `REQUIRED_TOOLS`). The names that go are listed, and so are the tests changed or deleted.
   - Criteria: each is testable by a parametrized test. Every rule has its failing side: the three `missing` faults in order, the relative workspace, the inner checkout, the inner state directory, the removed names, and the `opencode_item` failure text. The ordering clauses are covered by criteria 4 and 8.
   - Smoke test: one runnable `uv run python -` script. It has no pytest command, so the `-q` rule does not apply. Its two `Expect:` lines are checkable against the output.
   - Architecture: the changes keep the layer order (domain settings, application boundaries/preflight/task, entry wiring). The container environment stays the only implementation behind the interface, and the runtimes' call without a container stays (decision 2).
   - Scope: within the feature's S0008 scope and its decisions 2, 3, 10, 13, 16, 24 and 37. The undo's module stays for S0009, and no "Out of scope" item is touched. The test changes are covered by the human's leave in decision 24, on the corrected list of decision 37.
7. factory: started tests as self.
8. tester: I wrote the tests for criteria 1 to 8 and made the deletions the Interface names. I stopped before adapting the existing tests the Interface lists, because the budget would not cover them. That list is the wiring-based tests, which need a dataset, workspace and image, plus `wiring_support`, `hosted_environment`, the inline rows and the narrowed `opencode_item` callers. The question is who adapts them and when.

   Criterion → test:
   - criterion 1: tests/test_one_stage_environment.py::test_the_inline_environment_s_names_are_gone
   - criterion 2: tests/application/test_stage_environment_of.py::test_the_environment_of_the_boundaries_is_the_container_one. This is the renamed test; the file is rewritten. It checks "on its snapshots and containers" through `ContainerEnvironment._snapshots` and `._containers`, with `noqa: SLF001`.
   - criterion 3: tests/domain/test_settings_one_environment.py::test_the_stage_environment_setting_is_read_by_nothing
   - criterion 4: tests/entry/test_wiring_one_environment.py::test_build_boundaries_needs_the_dataset_the_workspace_and_the_image
   - criterion 5: tests/entry/test_wiring_one_environment.py::test_the_agent_run_s_home_is_the_dataset_s
   - criterion 6: tests/entry/test_wiring_one_preflight.py::test_the_preflight_checks_the_one_environment_s_items
   - criterion 7: tests/application/test_request_working_directory.py::test_the_request_works_in_the_dataset_s_checkout
   - criterion 8: tests/domain/test_settings_one_environment.py::test_a_workspace_refuses_a_relative_path_and_an_inner_checkout_or_state
   - criteria 9 and 10: no test (`make check`, docs).

   Files created: tests/test_one_stage_environment.py, tests/domain/test_settings_one_environment.py, tests/entry/test_wiring_one_environment.py, tests/entry/test_wiring_one_preflight.py, tests/application/test_request_working_directory.py.

   Earlier test files changed under decision 24's leave:
   - Deleted whole: tests/application/test_stage_environment.py, tests/application/test_agent_environment_item.py, tests/entry/test_wiring_stage_environment_home.py. The Interface also names tests/entry/test_wiring_extras_path.py for deletion, but that file does not exist on this branch.
   - Rewritten: tests/application/test_stage_environment_of.py.
   - Single tests deleted: test_the_last_required_tool_is_the_runtime_s_executable in tests/application/test_machine_checks_runtime.py, test_a_stage_built_without_an_environment_runs_the_inline_one in tests/application/test_stage_environment_calls.py, and test_a_stall_built_without_an_environment_undoes_inline_as_before in tests/application/test_stall_environment.py. Ruff removed the imports this left unused.

   One `make test` run is red. The failures I saw are for the right reason: `opencode_item()` still wants `find` and `environment`, and `MachineChecks.run` still asks for `make` and the runtime's executable. `make lint` is green. No module was missing at import: every module under test exists. Only names are missing, so the failures are TypeErrors and assertion failures, not collection errors.

   Not done: the rest of the Interface's test list.
   - The wiring-based tests: tests/wiring_support.py, the `hosted_environment` fixture, test_wiring_boundaries (11 tests), test_wiring_run, test_wiring_handlers, test_wiring_environment, test_wiring_human_handlers, test_wiring_acceptance, test_wiring_preflight, test_wiring_api_login/login/provider_limit/opencode/command_records/known_results/project_agents/record_logs/stop_records/waiter, test_run (10 tests), test_run_health_file, test_run_waiter, test_watch_main, test_watch_settings.
   - The inline rows of test_machine_checks_container, test_opencode_item_container and test_wiring_container_extras.
   - The three tests of test_opencode_item.
   - test_wiring_extras.
   - test_make_search::test_only_the_make_class_names_make.
   - The rows of test_settings_stage_environment, test_wiring_stage_environment and test_settings_paths.
   - test_task::test_the_request_carries_the_agent_checkout_and_guard_without_os_user.
   - tests/application/test_stage_on_container_fakes.py: it uses `inline_boundaries` (snapshots=None), which stops type-checking once `snapshots` is required, and so do the other callers of `container_support.inline_boundaries`.

   Options:
   (a) Move to `doing` now. The coder implements against the new tests, then ends with `tests`, naming the Interface's list (decision 24) as the approved test change. The tester then adapts those tests against the real code in a "test change the human approved" run.
   (b) Run this tests stage again so that it adapts them all before the coder starts. The adaptations would be written blind, against code that does not exist yet.
   I would choose (a). Adapting tests that run through the wiring is safer once `build_boundaries` raises the three `missing` faults for real.
9. 2026-10-25 human: (a). End with `doing`. The coder implements against the new tests, then ends with `tests` and names the Interface's list (decisions 24 and 37) as the approved test change; the tester then adapts all of it in one run against the real code, including `container_support.inline_boundaries`'s callers such as `tests/application/test_stage_on_container_fakes.py`. `tests/entry/test_wiring_extras_path.py` was already deleted by F0044-S0001, so nothing is left to delete there.
10. factory: started tests as self.
11. tester: In journal entry 9 the human chose option (a): this stage ends with `doing`. The tests from entry 8 are already committed on the branch, at fbd93b28 and the commits before it, so I wrote no new tests in this run and changed no files. I ran `make lint` again and it is green. I did not run `make test` again: it already ran once, in entry 8. It was red on purpose: the failures were TypeErrors and assertion failures because names are missing, not because a module could not be imported.

    Criterion → test:
    - criterion 1: tests/test_one_stage_environment.py::test_the_inline_environment_s_names_are_gone
    - criterion 2: tests/application/test_stage_environment_of.py::test_the_environment_of_the_boundaries_is_the_container_one
    - criterion 3: tests/domain/test_settings_one_environment.py::test_the_stage_environment_setting_is_read_by_nothing
    - criterion 4: tests/entry/test_wiring_one_environment.py::test_build_boundaries_needs_the_dataset_the_workspace_and_the_image
    - criterion 5: tests/entry/test_wiring_one_environment.py::test_the_agent_run_s_home_is_the_dataset_s
    - criterion 6: tests/entry/test_wiring_one_preflight.py::test_the_preflight_checks_the_one_environment_s_items
    - criterion 7: tests/application/test_request_working_directory.py::test_the_request_works_in_the_dataset_s_checkout
    - criterion 8: tests/domain/test_settings_one_environment.py::test_a_workspace_refuses_a_relative_path_and_an_inner_checkout_or_state
    - criteria 9 and 10: no test (`make check`, docs).

    Files created (in entry 8's run): tests/test_one_stage_environment.py, tests/domain/test_settings_one_environment.py, tests/entry/test_wiring_one_environment.py, tests/entry/test_wiring_one_preflight.py, tests/application/test_request_working_directory.py. Rewritten: tests/application/test_stage_environment_of.py.

    Deleted under decision 24, as entry 8 lists:
    - whole files: test_stage_environment.py, test_agent_environment_item.py and test_wiring_stage_environment_home.py
    - three single tests

    Modules the test run could not import: none. Every module under test exists; only names are missing.

    Still open, as the human decided in entry 9: the coder implements against these tests and then ends with `tests`, naming the Interface's test list (decisions 24 and 37) as the approved test change. The tester then adapts all of that list in one run against the real code. This includes the callers of `container_support.inline_boundaries`, such as tests/application/test_stage_on_container_fakes.py.

    `lint`: lint: green (0.2 s)
    `test`: FAILED tests/entry/test_wiring_one_preflight.py::test_the_preflight_checks_the_one_environment_s_items[opencode-unmapped] - TypeError: opencode_item() missing 2 required positional arguments: 'find...
12. factory: started doing as self.
13. coder: I implemented the story against the tester's new tests. All 39 rows of criteria 1–8 pass, in tests/test_one_stage_environment.py, tests/domain/test_settings_one_environment.py, tests/entry/test_wiring_one_environment.py, tests/entry/test_wiring_one_preflight.py, tests/application/test_request_working_directory.py and tests/application/test_stage_environment_of.py. `make lint` and `make layers` are green, and `mypy --strict` is clean over `src`. `make check` is red, and that is expected: the existing tests still use what this story removes. I end with `tests`, as the human decided in journal entry 9. The approved test change is the Interface's whole test list (decisions 24 and 37 of `feature.md`), adapted by the tester in one run against this code, including the callers of `container_support.inline_boundaries` such as `tests/application/test_stage_on_container_fakes.py`.

    What I built:
    - src/factory/domain/settings.py: removed `STAGE_ENVIRONMENT_VARIABLE`, `StageEnvironmentName`, `InstanceSettings.stage_environment`, `stage_environment_fault`, `_container_fault` and `_stage_environment`. `workspace_overlap_fault(workspace, checkout, state_directory)` returns `None` without a workspace. Otherwise it gives the relative-workspace fault first, then the checkout's, then the state directory's. `read_settings` and the model validator (now `_workspace_apart`) both call it.
    - src/factory/application/boundaries.py: `snapshots` and `containers` are required.
    - src/factory/application/stage_environment.py: removed `InlineEnvironment` and the import of `UndoService`. `stage_environment_of` always gives `ContainerEnvironment`.
    - src/factory/application/take.py: `agent_working_directory` is always `snapshots.mount_point / "checkout"`.
    - src/factory/application/preflight.py: `REQUIRED_TOOLS = ("git", "uv")`. Removed `CONTAINER_TOOLS`, `agent_environment_item`, `_home_fault`, `_path_fault`, `_AGENT_ENVIRONMENT_ITEM`, `MachineChecks._tools` and `MachineChecks._runtime_executable`. The signature is now `opencode_item(settings, agent_models)`.
    - src/factory/entry/wiring.py: `build_boundaries` calls `_container_adapters` first. It now raises `SettingsInvalid(<FACTORY_DATASET|FACTORY_WORKSPACE|FACTORY_STAGE_IMAGE>, "missing")` before PyGithub or anything else is built. Removed `_StageEnvironmentBoundaries`, `_inline_environment`, `_container_environment` and `_which_on`. `agent_run_environment` always sets `HOME` to `WORK_HOME`; its settings parameter is kept for the Interface's signature, renamed `_settings`. `machine_extras` now builds one list.
    - vm/setup.sh: removed the line `FACTORY_STAGE_ENVIRONMENT=container`.

    Main choice and the alternative I rejected: I put the three `missing` faults in the existing `_container_adapters`, which `machine_extras` also uses, and call it at the top of `build_boundaries`. I rejected a separate check before the build, because it would repeat the three None tests that `_container_adapters` needs anyway to narrow the types.

    Refactor pass: I read the diff. Only deletions and the merge of the container branch into `build_boundaries`; nothing more to change.

    What the tester must adapt (from `make test`):
    - On the Interface's list: test_opencode_item, test_opencode_item_container, test_machine_checks_container, test_wiring_container_extras, test_wiring_extras, test_settings_stage_environment, test_wiring_stage_environment, test_settings_paths, test_wiring_boundaries, test_wiring_run, test_wiring_api_login/login/opencode/command_records/known_results/project_agents/record_logs/stop_records/waiter/provider_limit/preflight, test_run, test_run_health_file, test_run_waiter, test_stage_environment_calls, test_stage_on_container_fakes, test_make_search.
    - Not named on the list but failing for the same reasons, so inside the same leave in my reading:
      - tests/container_support.py: `container_instance_settings` passes `stage_environment`, and `inline_boundaries` passes `snapshots=None`. This breaks test_agent_run_probe_environment and test_preflight_run_environment.
      - Tests that build boundaries without snapshots, which fail in `agent_working_directory`: test_stage_run, test_stalls, test_stall_edges.
      - Tests that expect `make` and the runtime's executable among the tools: test_preflight, test_preflight_run, test_preflight_stale_main_stop, test_preflight_stops_commit.
      - tests/entry/test_wiring_agent_environment.py and tests/entry/test_wiring_without_agent_user.py, which expect the inline extras and `MakeProjectCommands`.
      - tests/test_vm_setup_text.py, whose ENVIRONMENT table still has the row `FACTORY_STAGE_ENVIRONMENT`.

    Noticed, not touched: the Interface names `tests/entry/test_watch_main.py` and others that I did not see fail on this run. The tester should still check each entry on the list. The undo module stays in place, unused, for S0009.
14. factory: started tests as self.
15. tester: Mode: the test change the human approved (entries 9 and 13). I adapted part of the Interface's test list against the coder's code, then stopped because this run's budget was running out. The rest of the list is still to do. Six tests also need the human's word on what they should check now. `make lint` is green. I ran `make test` twice: the second run was a slip in a piped command, and I did not read its output. It is red, with 57 failures in the 17 modules listed under "Not done" below.

    Done (each test keeps its name and what it checks, unless noted):
    - tests/container_support.py: `CONTAINER` drops `stage_environment`, and `inline_boundaries` is removed. Its callers are adapted:
      - tests/application/test_stage_on_container_fakes.py: the `no-snapshots` row of `test_the_request_works_in_the_datasets_checkout_when_the_boundaries_hold_snapshots` is gone.
      - tests/application/test_stage_environment_calls.py: `test_after_the_agent_the_environment_takes_and_its_report_closes_the_entry` now reads the agent's file from the dataset's checkout.
      - The calls in test_stage_run, test_stall_edges and test_stalls are dropped (see the question).
    - New shared helper `with_dataset(settings, root)` in tests/wiring_support.py. It adds a dataset, `<root>/work`, the image, and the stand-in `zfs` and `podman` (tests/zfs_support.py, tests/podman_support.py).
      - The `local_settings` fixture uses it.
      - The settings of test_wiring_boundaries, test_wiring_run, test_wiring_preflight, test_wiring_api_login, test_wiring_login, test_wiring_provider_limit, test_run, test_run_health_file and test_run_waiter are wrapped in it.
    - The `hosted_environment` fixture (tests/conftest.py) gains FACTORY_DATASET, FACTORY_WORKSPACE under tmp_path, FACTORY_STAGE_IMAGE, FACTORY_ZFS and FACTORY_PODMAN (the stand-ins).
    - tests/domain/test_settings_stage_environment.py: the rows of FACTORY_STAGE_ENVIRONMENT, of `inline` and of the `missing for the container environment` faults are gone. Rows added: missing and blank values are read as `None`.
    - tests/domain/test_settings_paths.py: drops FACTORY_STAGE_ENVIRONMENT. Its `inline` row is now the refusal `FACTORY_CHECKOUT: /work/checkout lies inside FACTORY_WORKSPACE`.
    - tests/domain/test_settings_agent_user_unread.py: drops FACTORY_STAGE_ENVIRONMENT.
    - tests/entry/test_wiring_stage_environment.py: `test_an_inline_instance_has_no_snapshots_and_no_containers` is deleted (the `missing` refusals cover it), and the fixture drops `stage_environment`.
    - Inline rows removed from test_machine_checks_container, test_opencode_item_container and test_wiring_container_extras.
    - tests/application/test_opencode_item.py (all three tests) calls `opencode_item(settings, models)`. The PATH rows are gone.
    - tests/test_make_search.py now expects `{"factory.adapters.make_commands"}`.
    - tests/test_vm_setup_text.py loses the FACTORY_STAGE_ENVIRONMENT row.

    Now passing: test_watch_main, test_watch_settings, test_run_health_file, test_run_waiter, test_run, test_agent_run_probe_environment, test_preflight_run_environment, and most of the wiring tests.

    Not done (57 failures from `make test`):
    - The tool lists still expect `tool:make` or the runtime's executable: test_preflight (4), test_preflight_run (6), test_preflight_stale_main_stop (6), test_preflight_stops_commit (7), test_wiring_extras (3).
    - These still expect the inline extras or `MakeProjectCommands`: test_wiring_agent_environment (2), test_wiring_without_agent_user (3).
    - These now call the runtime through the `podman` stand-in, so the stand-in has to reply as the runtime and record the login: test_wiring_api_login (2), test_wiring_login (2), test_wiring_provider_limit (1), test_wiring_opencode (4), test_wiring_run (1), test_wiring_boundaries (2: project commands run in the dataset's checkout, and the run files under `runs`), test_wiring_command_records (1).
    - Not yet re-checked: test_wiring_handlers, test_wiring_environment, test_wiring_human_handlers and test_wiring_acceptance passed in this run. I did not go through test_task's working-directory test or the other probe tests one by one.

    Question: six tests check what an agent does in the host's own checkout. In the container environment the agent cannot do that: it works in the dataset, and only files are taken from it. The tests are:
    - tests/application/test_stage_run.py::test_a_run_adds_exactly_one_commit_of_its_own, the 3 rows `*-agent-committed`
    - tests/application/test_stall_edges.py::test_a_stall_after_the_agent_left_drops_its_commit_on_the_branch
    - tests/application/test_stalls.py::test_the_agents_own_commit_stays_below_the_one_stall_commit
    - tests/application/test_stalls.py::test_an_agent_that_left_the_branch_is_brought_back_and_its_other_branch_kept

    Options:
    - (a) Delete them, and the `agent-committed` rows, as inline behaviour that left with the inline environment, like the tests decision 24 already deletes.
    - (b) Rewrite them so the stand-in runtime commits, or switches branch, in the dataset's checkout. Each then checks what the container environment does with that: a different check under the same name.
    - (c) Keep them as they are, red.

    I would choose (a). Afterwards a further tests run in this mode should finish the list above.

    Criterion → test (unchanged from entry 11):
    - criterion 1: tests/test_one_stage_environment.py::test_the_inline_environment_s_names_are_gone
    - criterion 2: tests/application/test_stage_environment_of.py::test_the_environment_of_the_boundaries_is_the_container_one
    - criterion 3: tests/domain/test_settings_one_environment.py::test_the_stage_environment_setting_is_read_by_nothing
    - criterion 4: tests/entry/test_wiring_one_environment.py::test_build_boundaries_needs_the_dataset_the_workspace_and_the_image
    - criterion 5: tests/entry/test_wiring_one_environment.py::test_the_agent_run_s_home_is_the_dataset_s
    - criterion 6: tests/entry/test_wiring_one_preflight.py::test_the_preflight_checks_the_one_environment_s_items
    - criterion 7: tests/application/test_request_working_directory.py::test_the_request_works_in_the_dataset_s_checkout
    - criterion 8: tests/domain/test_settings_one_environment.py::test_a_workspace_refuses_a_relative_path_and_an_inner_checkout_or_state
    - criteria 9 and 10: no test.

    Files created in this run: none. The shared helper is in the existing tests/wiring_support.py. Modules the test run could not import: none.
16. 2026-10-25 human: (a). Delete the three `*-agent-committed` rows of `tests/application/test_stage_run.py::test_a_run_adds_exactly_one_commit_of_its_own` and the three tests `tests/application/test_stall_edges.py::test_a_stall_after_the_agent_left_drops_its_commit_on_the_branch`, `tests/application/test_stalls.py::test_the_agents_own_commit_stays_below_the_one_stall_commit` and `::test_an_agent_that_left_the_branch_is_brought_back_and_its_other_branch_kept`. They check inline behaviour that leaves with the inline environment; this is the take-over of S0007's inline-only tests that the Interface already names (decisions 24 and 37). Then run this mode again and finish the rest of the list.
17. factory: started tests as self.
18. tester: Mode: the test change the human approved (entries 9, 13 and 16). I made the deletions from entry 16 and worked further down the list from entry 15. I stopped before the end because this run's budget was running low. `make lint` is green. I ran `make test` once at the end and it is red with 13 failures, listed under "Not done". While working I also ran pytest directly on the modules I changed (with `--no-cov`), to see each one go green.

    Done (each test keeps its name and what it checks, unless noted):
    - Entry 16, the human's (a):
      - tests/application/test_stage_run.py::test_a_run_adds_exactly_one_commit_of_its_own loses its `commits` parametrization and the three `*-agent-committed` rows. `CommittingRuntime` became `HeadNotingRuntime`, which only notes the start head.
      - Deleted: tests/application/test_stall_edges.py::test_a_stall_after_the_agent_left_drops_its_commit_on_the_branch, tests/application/test_stalls.py::test_the_agents_own_commit_stays_below_the_one_stall_commit and ::test_an_agent_that_left_the_branch_is_brought_back_and_its_other_branch_kept. Unused imports were removed with them.
    - Tests that expected `make` and the runtime's executable among the required tools:
      - tests/application/test_preflight.py: the item list is now five (`SEVEN` renamed `FIVE`), and `ALL_TOOLS` drops make and claude.
      - test_preflight.py::test_the_claude_tool_item_asks_for_the_configured_executable is deleted. It checked the runtime's tool item, which criterion 6 removes, like test_machine_checks_runtime's deleted test.
      - test_preflight_run.py, test_preflight_stale_main_stop.py and test_preflight_stops_commit.py now make `uv` the missing tool instead of `make`. `TOOLS` in test_preflight_run.py drops make and claude. All four modules pass.
    - tests/entry/test_wiring_extras.py (both tests): settings wrapped in `with_dataset`. They now expect `[*CONTAINER_ITEMS, "agent-run-probe"]`. Both pass.
    - tests/wiring_support.py::with_dataset (this story's helper) now creates `<root>/work`. Its `podman` stand-in prints `PODMAN_VERSION` and its `zfs` stand-in answers `--version` and `list` with the dataset, so the preflight's extras pass.
    - tests/entry/test_wiring_agent_environment.py is deleted whole. It checked the item `agent-environment` that criterion 1 removes, like the Interface's deleted test_agent_environment_item.py.
    - tests/entry/test_wiring_without_agent_user.py:
      - test_the_extras_name_no_agent_user_and_no_sudo: rows `claude` (the container list plus `agent-run-probe`) and `opencode` (the same with `opencode` before `agent-run-probe`). The inline rows and the `stage_environment` updates are gone.
      - test_the_project_commands_run_without_a_user: no longer parametrized; it expects `ContainerMakeCommands`. The module passes.

    Not done (the 13 failures of `make test`):
    - test_wiring_login (2), test_wiring_api_login (2), test_wiring_opencode::test_the_built_opencode_runtime_runs_with_the_instance_s_models_denies_key_and_limit (2), test_wiring_provider_limit (1).
    - test_wiring_opencode::test_the_opencode_item_comes_after_confinement_only_under_opencode (2): it still needs `with_dataset` and the container list.
    - test_wiring_boundaries::test_the_built_project_commands_run_in_the_checkout (GitError: `HEAD` is missing in the dataset's checkout).
    - test_wiring_boundaries::test_the_built_agent_runtime_keeps_its_run_files_under_runs (FileExistsError).
    - test_wiring_command_records (FileNotFoundError).

    Question: the login and runtime tests read the environment that the claude or opencode stand-in recorded. Through the container environment the runtime starts `podman run ... <image> <words>`. The login is not passed as an `--env` word. The `factory-login` shell script reads it inside the container, so the stand-in `podman` (which by default exits silently) never starts the runtime's stand-in. What should these tests check now?
    - (a) Plan the stand-in `podman` to run the words after the image (`PodmanPlan(image=IMAGE)`). The login script and the claude or opencode stand-in then run on the host. Each test keeps checking the environment the runtime's stand-in sees. This needs the container's paths (the login file's mount, the runtime executable) to be reachable on the host in the test, and may need a plan that answers `image exists` differently from `run`.
    - (b) Check the `podman run` words instead: the login file is mounted and named to the login script, and no secret stands in the argv. That is a different check under the same name.
    - (c) Delete them as inline-only, like entry 16.
    I would choose (a), and fall back to (b) for any test where the paths cannot be made reachable. After the answer, one more run in this mode should finish the list above, including test_wiring_boundaries and test_wiring_command_records.

    Criterion → test (unchanged from entry 11):
    - criterion 1: tests/test_one_stage_environment.py::test_the_inline_environment_s_names_are_gone
    - criterion 2: tests/application/test_stage_environment_of.py::test_the_environment_of_the_boundaries_is_the_container_one
    - criterion 3: tests/domain/test_settings_one_environment.py::test_the_stage_environment_setting_is_read_by_nothing
    - criterion 4: tests/entry/test_wiring_one_environment.py::test_build_boundaries_needs_the_dataset_the_workspace_and_the_image
    - criterion 5: tests/entry/test_wiring_one_environment.py::test_the_agent_run_s_home_is_the_dataset_s
    - criterion 6: tests/entry/test_wiring_one_preflight.py::test_the_preflight_checks_the_one_environment_s_items
    - criterion 7: tests/application/test_request_working_directory.py::test_the_request_works_in_the_dataset_s_checkout
    - criterion 8: tests/domain/test_settings_one_environment.py::test_a_workspace_refuses_a_relative_path_and_an_inner_checkout_or_state
    - criteria 9 and 10: no test.

    Files created in this run: none. Deleted: tests/entry/test_wiring_agent_environment.py. Modules the test run could not import: none.
19. 2026-10-25 human: (b) for all of them. Running the container's words on the host would rebuild in the tests what the container does, with host paths standing in for the container's; that is fragile and not what runs on the VM. The wiring tests check what the wiring builds: the `podman run` words, with the login file mounted read-only and named to the login script, the instance's settings (models, denied key, limit) in the words or the mounted configuration as the runtime passes them, and no secret in the argv. Each test keeps its name. What the runtime does inside the container stays covered by the container runtimes' own tests (`tests/adapters/test_claude_runtime_container.py`, `tests/adapters/test_opencode_runtime_container.py`).

    Also, as the Interface says (the pre-check's edit 4): `tests/entry/test_wiring_boundaries.py::test_the_built_project_commands_run_in_the_checkout` is deleted, because criterion 4 covers the container project commands. Then finish the list in this run, with `test_wiring_boundaries::test_the_built_agent_runtime_keeps_its_run_files_under_runs` and `test_wiring_command_records`.
20. factory: started tests as self.
21. tester: Mode: the test change the human approved (entry 19, option (b) for every login and runtime wiring test, plus the deletion from the pre-check's edit 4). I finished the rest of the list from entry 18. `make lint` is green. I ran `make test` once at the end and it is green ("test: green (64.8 s)", coverage 99.56 %). While working I also ran pytest directly, with `--no-cov`, on the modules I changed. I skipped the type check, as the stage says. Running mypy by hand on the changed files only gave import-untyped noise from outside the Makefile's configuration, so the coder's `make check` is the real type check.

    Done (each test keeps its name):
    - tests/wiring_support.py (this story's helper) gains three helpers:
      - `dataset_podman(root, plan)`: re-plans the stand-in `podman` that `with_dataset` wrote.
      - `run_words(podman)`: the words of the one `podman run` call.
      - `after_image(words)`: the container's command, the words after the image.
    - Each test now plans the stand-in `podman` to print the runtime's reply, so the runtime reads that reply as the container's output.
    - tests/entry/test_wiring_login.py::test_the_built_runtime_hands_the_login_file_s_token_to_claude: parametrized on `configured` only. It checks three things in the `podman run` words:
      - the container's command starts with `login_argv(LoginFiles(subscription=...))`, or with no login words when no file is set;
      - the login file is mounted `<file>:<file>:ro` only when it is set;
      - the token appears in no word.
    - tests/entry/test_wiring_api_login.py::test_the_built_runtime_hands_the_api_login_file_s_key_to_claude: the same checks for the API login file and its key.
    - tests/entry/test_wiring_provider_limit.py::test_the_built_runtime_recognizes_the_configured_limit_status: `podman` prints the 429 error reply, and the test still expects `provider_limit`. The claude stand-in is gone.
    - tests/entry/test_wiring_opencode.py::test_the_built_opencode_runtime_runs_with_the_instance_s_models_denies_key_and_limit (both rows). It checks:
      - `--model anthropic/claude-sonnet-5-5` in the container's command;
      - an `OPENCODE_CONFIG=<path>` `--env` word whose path lies under `state/runs` and is mounted read-only;
      - the API login words and the read-only mount of the API login file;
      - the key appears in no word;
      - the end reason, `completed` or `provider_limit`, comes from the reply `podman` prints.
      - Rejected: checking the denied `git push*` rule inside the configuration. The runtime deletes that file after the run, and the stand-in `podman` (tests/podman_support.py, written by F0042) does not record file contents. Changing it would be a change to another story's helper, which needs the human's leave. The rule's content stays covered by tests/adapters/test_opencode_runtime_container.py.
    - tests/entry/test_wiring_opencode.py::test_the_opencode_item_comes_after_confinement_only_under_opencode: the settings are wrapped in `with_dataset`. The rows now expect `[*CONTAINER_ITEMS, "opencode"]` and `CONTAINER_ITEMS`, each followed by `agent-run-probe`.
    - tests/entry/test_wiring_boundaries.py:
      - test_the_built_project_commands_run_in_the_checkout is deleted, as entry 19 and the Interface say (criterion 4 covers the container project commands).
      - test_the_built_agent_runtime_keeps_its_run_files_under_runs now checks that the `--append-system-prompt-file` path in the container's command lies under `state/runs` and is mounted read-only. The working folder is made with `exist_ok`, because `with_dataset` already makes `<tmp>/work`.
    - tests/entry/test_wiring_command_records.py::test_the_built_project_commands_record_a_run_in_the_state_directory: the test makes `<workspace>/checkout`, which the dataset's base would hold and the stand-in `zfs` does not make. It plans `podman` to print `lint: green (0 s)`, and still expects the record `("lint", HEAD, "passed")`.

    Criterion → test (unchanged from entry 11):
    - criterion 1: tests/test_one_stage_environment.py::test_the_inline_environment_s_names_are_gone
    - criterion 2: tests/application/test_stage_environment_of.py::test_the_environment_of_the_boundaries_is_the_container_one
    - criterion 3: tests/domain/test_settings_one_environment.py::test_the_stage_environment_setting_is_read_by_nothing
    - criterion 4: tests/entry/test_wiring_one_environment.py::test_build_boundaries_needs_the_dataset_the_workspace_and_the_image
    - criterion 5: tests/entry/test_wiring_one_environment.py::test_the_agent_run_s_home_is_the_dataset_s
    - criterion 6: tests/entry/test_wiring_one_preflight.py::test_the_preflight_checks_the_one_environment_s_items
    - criterion 7: tests/application/test_request_working_directory.py::test_the_request_works_in_the_dataset_s_checkout
    - criterion 8: tests/domain/test_settings_one_environment.py::test_a_workspace_refuses_a_relative_path_and_an_inner_checkout_or_state
    - criteria 9 and 10: no test.

    Files created in this run: none. Changed: tests/wiring_support.py, tests/entry/test_wiring_login.py, test_wiring_api_login.py, test_wiring_provider_limit.py, test_wiring_opencode.py, test_wiring_boundaries.py, test_wiring_command_records.py. Modules the test run could not import: none.

    `lint`: lint: green (0.2 s)
    `test`: test: green (63.6 s)
22. factory: started doing as self.
