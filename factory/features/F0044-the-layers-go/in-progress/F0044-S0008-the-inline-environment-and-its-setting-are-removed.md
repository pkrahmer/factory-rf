---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 451
comments_read: [6401042995]
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-25T17:49:35.531640Z'
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
7. `make check` stays green.
8. docs: `docs/operator-guide.md`, *Configuration*: the row `FACTORY_STAGE_ENVIRONMENT` goes, the rows `FACTORY_DATASET`, `FACTORY_WORKSPACE` and `FACTORY_STAGE_IMAGE` say required, and the paragraph *The stage environment* says there is one; *The preflight's items*: the rows `agent-environment`, `tool:make` and the runtime's tool go, the `opencode` item has one form, and the count follows; *The agent runtime*, *The agent in a container*: one environment; *The agent run's `PATH` and `HOME`*: the `HOME` is `/work/home`, and no item `agent-environment` checks it; *The service*: the environment file's table loses the row `FACTORY_STAGE_ENVIRONMENT`; `docs/project-guide/stage-environment.md`: *The stage environment* and *The settings and the wiring* describe one environment and `build_boundaries`' three faults; `docs/project-guide/watching.md`, *Boundaries*: `snapshots` and `containers` are required; *The tick*: one list of machine extras, `opencode_item(settings, agent_models)`, and no runtime executable among the tools; `docs/project-guide/stage-environment.md`, the opening paragraph and *The cycle*: one environment; *`run_agent`*: no comparison with the inline environment; *The preflight*: one list of items and no `CONTAINER_TOOLS`; `docs/project-guide/processes-and-checks.md`, *Project commands*: the string `"make"` appears in `factory.adapters.make_commands` alone, as `tests/test_make_search.py` allows; *Running as another user*: no `inline` instance; `docs/project-guide/README.md`, *The files*: the line of `stage-environment.md` follows; `README.md`: the paragraph that names `FACTORY_STAGE_ENVIRONMENT` says that every stage runs in throwaway containers on a ZFS dataset and points to the operator guide's chapter `## The machine`. `docs/decisions.md`: the entry "One snapshot instead of many layers" gains one line that the inline environment and its setting went with v1.2 F0044-S0008.

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
