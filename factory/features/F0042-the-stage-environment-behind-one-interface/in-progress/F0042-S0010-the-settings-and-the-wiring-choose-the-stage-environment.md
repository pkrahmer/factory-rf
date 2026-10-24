---
stage: review
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 421
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-24T20:49:56.848201Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-24T20:49:56.854221Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-24T20:50:18.764440Z'
  stage: intake
  run: 75697f5e9a794850b72785b292792af0
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-24T20:50:38.866151Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-24T20:56:04.534320Z'
  stage: tests
  run: 6c6af4f09a504bd9998ff153f12237d3
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-24T20:56:26.241008Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-24T21:01:26.948142Z'
  stage: doing
  run: 573f0956d74a43a0b08a6be4e1c02953
---

# The settings and the wiring choose the stage environment

## Description

An instance is told which stage environment it runs through its environment variables, as it is told its runtime: `FACTORY_STAGE_ENVIRONMENT` is `inline` (the default, v1.1's way) or `container`; a `container` instance also names its ZFS dataset (`FACTORY_DATASET`, for example `tank/factory/vm`), the dataset's mount point on the host (`FACTORY_WORKSPACE`, an absolute path), the stage image (`FACTORY_STAGE_IMAGE`) and, with defaults, the two executables (`FACTORY_PODMAN`, `FACTORY_ZFS`). This story adds them to `InstanceSettings` with the faults the other settings have (a `container` environment without a dataset, a workspace or an image is `SettingsInvalid`, and so is one with an agent user: the container is the second user), and makes the wiring build a `container` instance's boundaries: `ZfsSnapshots` and `PodmanRuns` of S0002 and S0003 in `snapshots` and `containers`, the runtime of S0008 started in containers with no `sudo`, no `factory-confine` and no leftovers program, `ContainerMakeCommands` of S0009 behind the recording commands, no agent home to reset, and the agent run's `HOME` set to `/work/home`. An `inline` instance's boundaries are built exactly as today. With this story an operator can start a `container` instance; the preflight that checks its tools is S0011's, the machine F0043's. What stays: the image, `compose.yml` and every setting of today, unchanged; `self` runs on `inline` without setting anything.

## Interface

`factory.domain.settings` (`domain`):

```python
STAGE_ENVIRONMENT_VARIABLE = "FACTORY_STAGE_ENVIRONMENT"
DATASET_VARIABLE = "FACTORY_DATASET"
WORKSPACE_VARIABLE = "FACTORY_WORKSPACE"
STAGE_IMAGE_VARIABLE = "FACTORY_STAGE_IMAGE"
PODMAN_EXECUTABLE_VARIABLE = "FACTORY_PODMAN"
ZFS_EXECUTABLE_VARIABLE = "FACTORY_ZFS"

StageEnvironmentName = Literal["inline", "container"]


class InstanceSettings(BaseModel):
    ...
    stage_environment: StageEnvironmentName = "inline"
    dataset: str | None = None
    workspace: Path | None = None
    stage_image: str | None = None
    podman_executable: str = "podman"
    zfs_executable: str = "zfs"
```

- `read_settings(environ, ...)` reads the six variables, each stripped of surrounding whitespace; a blank value counts as unset. `FACTORY_STAGE_ENVIRONMENT` unset or blank is `inline`; `inline` and `container` are themselves; anything else (`Container`, `podman`) is `SettingsInvalid(STAGE_ENVIRONMENT_VARIABLE, "holds <value>, which is neither inline nor container")`. `FACTORY_PODMAN` and `FACTORY_ZFS` unset or blank give their defaults; any other value is taken as the executable (one word, decision 14 of `feature.md`).
- For `container`, in this order: `FACTORY_DATASET` unset is `SettingsInvalid(DATASET_VARIABLE, "missing for the container environment")`; `FACTORY_WORKSPACE` unset is `SettingsInvalid(WORKSPACE_VARIABLE, "missing for the container environment")` and a relative value is `SettingsInvalid(WORKSPACE_VARIABLE, "is not an absolute path")`; `FACTORY_STAGE_IMAGE` unset is `SettingsInvalid(STAGE_IMAGE_VARIABLE, "missing for the container environment")`; `FACTORY_AGENT_USER` set is `SettingsInvalid(AGENT_USER_VARIABLE, "is set, but the container environment runs no second user")` (decision 15). For `inline` the five other variables are read and kept but no fault is raised for a missing one or for a relative `FACTORY_WORKSPACE`.
- `InstanceSettings` built directly follows the same rules through a model validator: `stage_environment="container"` with `dataset`, `workspace` or `stage_image` `None`, or with `agent_user` set, or with a relative `workspace`, is `ValidationError`; `inline` accepts any combination.

`factory.entry.wiring` (`entry`):

```python
WORK_HOME_ENVIRONMENT = {"HOME": WORK_HOME}


def build_boundaries(
    settings: InstanceSettings,
    token: str,
    *,
    hosting: HostingService | None = None,
    which: Callable[[str], str | None] = shutil.which,
    confine_executable: str | None = CONFINE_COMMAND,
    end_leftovers: bool = True,
) -> Boundaries: ...


def agent_run_environment(settings: InstanceSettings, base: Mapping[str, str]) -> dict[str, str]: ...
```

- `build_boundaries` with `settings.stage_environment == "inline"` returns exactly today's boundaries, `snapshots` and `containers` `None`. With `container`: `snapshots` is `ZfsSnapshots(settings.dataset, settings.workspace, executable=settings.zfs_executable)`; `containers` is `PodmanRuns(settings.podman_executable, settings.stage_image, settings.workspace)`; `agent_runtime` is the runtime of `settings.agent_runtime` built with `containers=<that PodmanRuns>`, `confine_executable=None`, `leftovers=None` and the login files, models and limits as today; `project_commands` is `RecordingProjectCommands(ContainerMakeCommands(snapshots, containers, git, checkout=settings.checkout), git, <the command records>, clock, log)`, with no `SealedProjectCommands` around it; `agent_home` is `None` (no agent user); everything else as today. The `which`, `confine_executable` and `end_leftovers` arguments are read for `inline` only.
- `agent_run_environment(settings, base)`: for `container` the copy's `HOME` is `/work/home` (`WORK_HOME`); for `inline` as today (the agent user's home when one is set, else the base's).

`factory.application.project_commands.RecordingProjectCommands` (`application`) gains a read-only property `inner -> ProjectCommands`, the implementation it records, so that the wiring's tests can see which one a `container` instance got (`SealedProjectCommands` has none: it is not used for `container`).

Tests (the tester writes them): `tests/domain/test_settings_stage_environment.py`, `tests/entry/test_wiring_stage_environment.py` (with `hosting=FakeHostingService()`, a token file and an image file in `tmp_path`, as `tests/entry/test_wiring_boundaries.py` does; the adapters are read by type and by their arguments; only the stand-in `zfs` and `podman` scripts of criteria 5 and 7 run, which record their arguments, and no real tool), `tests/entry/test_wiring_stage_environment_home.py`. The existing settings and wiring tests are unchanged.

## Acceptance criteria

1. `read_settings` (rows of one parametrized test over the base environment of `tests/settings_support.py`): no `FACTORY_STAGE_ENVIRONMENT`, an empty one and `  inline ` give `stage_environment` `inline`; `container` with `FACTORY_DATASET=tank/factory/vm`, `FACTORY_WORKSPACE=/srv/factory/vm/work` and `FACTORY_STAGE_IMAGE=factory-stage:1` gives `container`, `dataset` `tank/factory/vm`, `workspace` `Path("/srv/factory/vm/work")`, `stage_image` `factory-stage:1`, `podman_executable` `podman` and `zfs_executable` `zfs`; the same with `FACTORY_PODMAN=/usr/bin/podman` and `FACTORY_ZFS=/usr/local/bin/factory-zfs` gives those two; the same with `FACTORY_PODMAN="  "` and `FACTORY_ZFS=""` gives `podman` and `zfs`; `FACTORY_DATASET=" tank/factory/vm "`, `FACTORY_WORKSPACE=" /srv/factory/vm/work "` and `FACTORY_STAGE_IMAGE=" factory-stage:1 "` give the three values stripped.
2. The faults (rows of one parametrized test, each `SettingsInvalid` with the named variable and the text): `FACTORY_STAGE_ENVIRONMENT=Container` gives `FACTORY_STAGE_ENVIRONMENT` and `holds Container, which is neither inline nor container`; `container` without `FACTORY_DATASET`, and with `FACTORY_DATASET="  "`, each gives `FACTORY_DATASET` and `missing for the container environment`; with the dataset but without `FACTORY_WORKSPACE` gives `FACTORY_WORKSPACE` and `missing for the container environment`; with `FACTORY_WORKSPACE=srv/work` gives `FACTORY_WORKSPACE` and `is not an absolute path`; with the dataset and the workspace but without `FACTORY_STAGE_IMAGE` gives `FACTORY_STAGE_IMAGE` and `missing for the container environment`; with all three and `FACTORY_AGENT_USER=agent` gives `FACTORY_AGENT_USER` and `is set, but the container environment runs no second user`; `inline` with none of the five is accepted, `inline` with `FACTORY_AGENT_USER=agent` and `FACTORY_DATASET=tank/x` is accepted with `dataset` `tank/x`, and `inline` with `FACTORY_WORKSPACE=srv/work` is accepted with `workspace` `Path("srv/work")`.
3. `InstanceSettings` built directly (rows of one parametrized test through a `type[BaseModel]`): `stage_environment="container"` with the three set and no agent user is accepted; without `dataset`, without `workspace`, without `stage_image`, with `workspace=Path("srv/work")` and with `agent_user="agent"` each is `ValidationError`; `stage_environment="podman"` is `ValidationError`; `inline` without the three is accepted.
4. `build_boundaries` for `inline` settings gives `snapshots` `None`, `containers` `None`, and the runtime, the project commands and the agent home as today (the existing `tests/entry/test_wiring_*.py` are unchanged and green; one row asserts the two `None`s).
5. `build_boundaries` for `container` settings (dataset `tank/factory/vm`, workspace `<tmp>/work`, image `factory-stage:1`, `FACTORY_ZFS` and `FACTORY_PODMAN` set to two stand-in paths), called with `which` a function of the test that records every name it is asked for, `confine_executable="factory-confine"` and `end_leftovers=True`: the build succeeds (S0008's runtime refuses `containers` together with a confine executable, so none reached it) and `which` was asked for nothing; `snapshots` is a `ZfsSnapshots` whose `mount_point` is `<tmp>/work`; `containers` is a `PodmanRuns`; `containers.launch(["true"], mounts=[], environment={}, time_limit=1 s, working_directory="/work")` gives words that start with the podman stand-in's path and hold `factory-stage:1`; `snapshots.reset()` with a stand-in `zfs` that records its arguments records `rollback -r tank/factory/vm@base` (the executable and the dataset reached the adapter); `agent_runtime` is a `ClaudeCodeRuntime` whose `containers is boundaries.containers`, whose `confine_executable` is `None` and whose `leftovers` is `None`; with `FACTORY_AGENT_RUNTIME=opencode` it is an `OpencodeRuntime` whose `containers is boundaries.containers` and whose `leftovers` is `None` (it has no public `confine_executable`; the successful build shows none); `project_commands` is a `RecordingProjectCommands` whose `inner` is a `ContainerMakeCommands`; `agent_home` is `None`. One more row: with `claude_login_file` a file in `tmp_path` and the podman stand-in printing the completed reply of `tests/entry/test_wiring_login.py` while recording its words, `agent_runtime.run(<a request without os_user, its environment's HOME /work/home>)` ends completed and the recorded words hold `--volume <login file>:<login file>:ro` (the wiring gave the runtime its login file).
6. `agent_run_environment` (rows of one parametrized test): `container` settings give `HOME` `/work/home` and keep `PATH` and `LANG`; `inline` with an agent user gives the agent user's home; `inline` without one keeps the base's `HOME`; the base dict is not changed.
7. `build_tick` on `container` settings with `hosting` the fake does not start any `zfs` or `podman` (the stand-ins record no call) and builds a tick (the preflight's items for a container instance are S0011's; this row only pins that wiring a container instance runs nothing).
8. `make check` stays green.
9. docs: `docs/operator-guide.md`, *Configuration*: the six rows in its three-column table (variable, required, and in the meaning the default and the refusal text, as the other rows give them), a paragraph *The stage environment* after the table saying what `inline` and `container` are, that `container` needs the dataset, the workspace and the image, runs no second user and no kernel guard, and that the VM it runs on is F0043's (the machine and the stage image); `docs/project-guide/stage-environment.md` gains the section *The settings and the wiring* (the six settings and their faults, what `build_boundaries` builds for each environment, `agent_run_environment`'s `HOME`); `docs/project-guide/git-and-hosting.md` (which names `factory.domain.settings`): one sentence pointing to `stage-environment.md` for the new settings; `docs/project-guide/watching.md`, *Boundaries*: how the wiring fills `snapshots` and `containers`. `docs/project-guide/README.md`, *The files*: the line of `stage-environment.md` names the section *The settings and the wiring* and that the file also names `factory.domain.settings` and `factory.entry.wiring`. `docs/decisions.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
from pathlib import Path

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import read_settings

base = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "vm"}
s = read_settings({**base, "FACTORY_STAGE_ENVIRONMENT": "container", "FACTORY_DATASET": "tank/factory/vm", "FACTORY_WORKSPACE": "/srv/factory/vm/work", "FACTORY_STAGE_IMAGE": "factory-stage:1"})
print(s.stage_environment, s.dataset, s.workspace, s.stage_image, s.podman_executable, s.zfs_executable)
print(read_settings(base).stage_environment, read_settings(base).dataset)
for extra in ({"FACTORY_STAGE_ENVIRONMENT": "Container"}, {"FACTORY_STAGE_ENVIRONMENT": "container"}, {"FACTORY_STAGE_ENVIRONMENT": "container", "FACTORY_DATASET": "tank/x", "FACTORY_WORKSPACE": "srv/work"}):
    try:
        read_settings({**base, **extra})
    except SettingsInvalid as error:
        print(error.variable, "|", error.fault)
EOF
```
Expect: five lines: `container tank/factory/vm /srv/factory/vm/work factory-stage:1 podman zfs`; `inline None`; `FACTORY_STAGE_ENVIRONMENT | holds Container, which is neither inline nor container`; `FACTORY_DATASET | missing for the container environment`; `FACTORY_WORKSPACE | is not an absolute path`

```bash
uv run pytest tests/domain/test_settings_stage_environment.py tests/entry/test_wiring_stage_environment.py tests/entry/test_wiring_stage_environment_home.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

## Journal

1. 2026-10-24 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`factory.domain.settings` constants and six fields, `factory.entry.wiring.build_boundaries` and `agent_run_environment`, `RecordingProjectCommands.inner`). `WORK_HOME` and `CONFINE_COMMAND` exist in the source, and `build_boundaries` already takes `confine_executable`. Every behaviour in the Interface text (stripping, blank as unset, defaults, fault order and texts, the model validator, what each environment builds, `HOME`) has a criterion.
   Criteria: each is testable by a parametrized test or one function. Both sides of each rule are covered: valid and invalid environment names, each missing or relative value, the agent user, `inline` accepting any combination, `container` and `inline` boundaries, and `HOME` for the three cases. Minor gaps I left alone: a blank `FACTORY_WORKSPACE` or `FACTORY_STAGE_IMAGE` has no row of its own (the blank-dataset row and the blank rule cover it), and the order of the agent-user fault against the other three is shown only where all three are set.
   Smoke test: both commands are runnable. The pytest command passes no `-q`, and `pyproject.toml` `addopts` already sets `-q`, so the summary line `N passed in` exists for the `grep -c` to count. Every `Expect:` is checkable against the output.
   Architecture: settings and their faults stay in `domain`, the wiring in `entry`, and `RecordingProjectCommands.inner` in `application`. The adapters are reached only through their interfaces, and no new dependency or package is added.
   Scope: the story stays within F0042's scope line for S0010 and keeps to the feature's Out of scope list. Decisions 14 and 15 are carried as written, and no earlier test is changed (decision 18 (h)).
4. factory: started tests as self.
5. tester: Wrote the tests of the stage environment's settings and wiring from the Interface and criteria 1–7.

   Criterion → test:
   - criterion 1: tests/domain/test_settings_stage_environment.py::test_read_settings_reads_the_stage_environment_and_its_values (rows unset, empty, `  inline `, container, executables, blank-executables, padded-values)
   - criterion 2: tests/domain/test_settings_stage_environment.py::test_read_settings_refuses_a_stage_environment_it_cannot_run (the seven faults) and ::test_read_settings_accepts_any_values_for_the_inline_environment (the three accepted `inline` rows; they are a separate test because they assert values, not a fault)
   - criterion 3: tests/domain/test_settings_stage_environment.py::test_instance_settings_built_directly_follow_the_stage_environment_rules (through `type[BaseModel]`)
   - criterion 4: tests/entry/test_wiring_stage_environment.py::test_an_inline_instance_has_no_snapshots_and_no_containers (the existing wiring tests are unchanged)
   - criterion 5: tests/entry/test_wiring_stage_environment.py::test_a_container_instance_gets_the_dataset_s_adapters_and_asks_for_no_tool (asks `which` for nothing, ZfsSnapshots mount point, PodmanRuns launch words, zfs stand-in records `rollback -r tank/factory/vm@base`, `RecordingProjectCommands.inner` is `ContainerMakeCommands`, `agent_home` None), ::test_a_container_instance_s_runtime_runs_in_its_containers_unconfined[claude|opencode], ::test_a_container_instance_s_runtime_mounts_its_login_file (podman stand-in prints the REPLY of tests/entry/test_wiring_login.py, run ends completed, words hold `--volume <login>:<login>:ro`)
   - criterion 6: tests/entry/test_wiring_stage_environment_home.py::test_the_agent_run_s_home_follows_the_stage_environment
   - criterion 7: tests/entry/test_wiring_stage_environment.py::test_wiring_a_container_instance_s_tick_starts_no_tool
   - criteria 8 and 9 (make check, docs): no test.

   Files created: tests/domain/test_settings_stage_environment.py, tests/entry/test_wiring_stage_environment.py, tests/entry/test_wiring_stage_environment_home.py. I changed no earlier test file.

   Choices I made:
   - The wiring tests build `InstanceSettings` directly, with the two stand-in paths as `zfs_executable` and `podman_executable`. They do not go through `read_environment_settings`, because that function fixes the checkout and state paths to `/work/checkout` and `/state`, outside `tmp_path`. The token is `CREDENTIAL` from tests/wiring_support.py, as in tests/entry/test_wiring_boundaries.py. The opencode row sets `agent_runtime` on the settings.
   - The zfs and podman stand-ins are Python scripts written with `git_support.write_executable`. Each appends its arguments as one JSON line to a `calls` file beside it.

   `make test`, run once: the new tests fail for the right reason. The read_settings rows fail with AttributeError (`stage_environment` is missing). The container fixture and rows fail with a pydantic ValidationError (unknown fields). `RecordingProjectCommands.inner` and the `container` handling do not exist yet. No module failed to import: every imported name exists already. Some rows that pin today's behaviour may already pass (the inline rows of criterion 6, the `podman` row of criterion 3).

   `make lint`: green. I skipped the type check, as this stage says.

   `lint`: lint: green (0.5 s)
   `test`: ERROR tests/entry/test_wiring_stage_environment.py::test_wiring_a_container_instance_s_tick_starts_no_tool - pydantic_core._pydantic_core.ValidationError: 6 validation errors for InstanceSettings
6. factory: started doing as self.
7. coder: Built the stage environment's settings and wiring; `make check` green (coverage 99.19 %), the three new test modules pass, no test touched.

   What I built:
   - src/factory/domain/settings.py: the six variable constants, `StageEnvironmentName`, the six `InstanceSettings` fields, `_stage_environment` (blank → `inline`, anything but `inline`/`container` → the "neither inline nor container" fault, same shape as `_agent_runtime`), and one public rule `stage_environment_fault(stage_environment, *, dataset, workspace, stage_image, agent_user) -> (variable, fault) | None` (container checks in a private `_container_fault`, in the Interface's order: dataset, workspace missing, workspace relative, image, agent user). The model validator raises `ValueError` from it; `read_settings` calls it first and raises `SettingsInvalid(*fault)`, so the operator sees the variable instead of a pydantic error.
   - src/factory/application/project_commands.py: `RecordingProjectCommands.inner` read-only property.
   - src/factory/entry/wiring.py: `build_boundaries` picks `_inline_environment` (exactly today's sudo/leftovers/agent home/sealed commands, the only reader of `which`, `confine_executable`, `end_leftovers`) or `_container_environment` (`ZfsSnapshots`, `PodmanRuns`, runtime with `containers=` and no confine or leftovers, `ContainerMakeCommands`, no agent home). Each returns a private frozen dataclass `_StageEnvironmentBoundaries` holding the parts that differ. `_agent_runtime` now takes keyword arguments with defaults plus `containers`. New `WORK_HOME_ENVIRONMENT = {"HOME": WORK_HOME}` (reusing `factory.domain.containers.WORK_HOME`); `agent_run_environment` applies it for `container`.

   Main choice: one rule function used by both the model validator and `read_settings`. Rejected: building the model in `read_settings` and turning its `ValidationError` back into `SettingsInvalid`, which would mean reading the variable and the fault text back out of pydantic's message.

   Refactor pass: the only change was splitting `_container_fault` out to satisfy ruff's PLR0911 (too many return statements); otherwise nothing to change.

   Noticed, not touched:
   - `_container_environment` checks again that dataset, workspace and image are not `None`, only so mypy can narrow the types. The settings validator already guarantees them, so that line (`wiring.py:364`) can never run and is the one uncovered line in wiring.py.
   - `read_settings` now reads `FACTORY_AGENT_USER` earlier than before. When both the agent user and another setting are wrong, the agent user's "is not a name" fault now comes first; no existing test depends on that order.
   - `InstanceSettings` is not part of the records contract, so nothing was regenerated.
   - Docs (criterion 9) are left to the documenter.

   The journal changed nothing about the task's meaning; the Description stays as it is.

   `check`: check: green
   `duplicates`: duplicates: 13 new, 36 known, 2 gone
