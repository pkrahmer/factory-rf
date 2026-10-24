---
stage: approval
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 421
comments_read: []
handed_over: approval
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
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-24T21:01:47.432915Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-24T21:03:22.882308Z'
  stage: review
  run: 153a4a8f364747f98966b3d43d5433f0
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-24T21:03:43.462382Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-24T21:04:07.712611Z'
  stage: doing
  run: ee9ebf259a384d9f91c6d7ad75e9ab58
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-24T21:04:28.265262Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-24T21:07:22.771460Z'
  stage: tests
  run: b433c0869e2743c6b7cf764557595c0a
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-24T21:07:43.375862Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-24T21:10:42.176096Z'
  stage: doing
  run: 6b36e4c470da4ace880dc76c5ec670b8
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-24T21:11:03.062008Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-24T21:12:23.441219Z'
  stage: review
  run: e3f18e78d38a498bb121efd69f53eab0
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-24T21:12:44.179338Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-24T21:13:40.358664Z'
  stage: docs
  run: 4cd4b6be77db48448c3ca1f29b871f60
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-24T21:14:00.717754Z'
  stage: smoke-test
- number: 21
  speaker: smoke-tester
  kind: result
  at: '2026-10-24T21:14:34.820065Z'
  stage: smoke-test
  run: 75c3abb052b540c59155fd3c7ad34044
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
8. More rows of the parametrized test of criterion 2, for the blank values and the order of the container faults: `container` with the dataset and `FACTORY_WORKSPACE="  "` gives `FACTORY_WORKSPACE` and `missing for the container environment`; with the dataset, the workspace and `FACTORY_STAGE_IMAGE="  "` gives `FACTORY_STAGE_IMAGE` and `missing for the container environment`; with the dataset and `FACTORY_WORKSPACE=srv/work` but without `FACTORY_STAGE_IMAGE` gives `FACTORY_WORKSPACE` and `is not an absolute path` (the relative workspace comes before the missing image); with `FACTORY_AGENT_USER=agent` but without `FACTORY_DATASET` gives `FACTORY_DATASET` and `missing for the container environment` (the agent user comes last).
9. `make check` stays green.
10. docs: `docs/operator-guide.md`, *Configuration*: the six rows in its three-column table (variable, required, and in the meaning the default and the refusal text, as the other rows give them), a paragraph *The stage environment* after the table saying what `inline` and `container` are, that `container` needs the dataset, the workspace and the image, runs no second user and no kernel guard, and that the VM it runs on is F0043's (the machine and the stage image); `docs/project-guide/stage-environment.md` gains the section *The settings and the wiring* (the six settings and their faults, what `build_boundaries` builds for each environment, `agent_run_environment`'s `HOME`); `docs/project-guide/git-and-hosting.md` (which names `factory.domain.settings`): one sentence pointing to `stage-environment.md` for the new settings; `docs/project-guide/watching.md`, *Boundaries*: how the wiring fills `snapshots` and `containers`. `docs/project-guide/README.md`, *The files*: the line of `stage-environment.md` names the section *The settings and the wiring* and that the file also names `factory.domain.settings` and `factory.entry.wiring`. `docs/decisions.md`: none.

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
8. factory: started review as self.
9. reviewer: Review, round 0. Group 1 (acceptance criteria) fails. I stopped there and did not judge groups 2 to 5. Before reporting I went through every criterion (1 to 7) and every rule of the Interface. Criteria 1 and 3 to 7 each have a test that checks what they say: the inline `None`s, the container adapters and their arguments, `which` never asked, the `inner` of `RecordingProjectCommands`, the runtime's `containers`/`confine_executable`/`leftovers`, the login volume, `HOME`, and the tick that starts no tool. The coder's `make check` was green (journal entry 7).

   Findings:
   1. `tests/domain/test_settings_stage_environment.py`, `test_read_settings_refuses_a_stage_environment_it_cannot_run` and `test_read_settings_accepts_any_values_for_the_inline_environment`: criterion 2 asks for one parametrized test, and its accepted `inline` rows are the other side of the same rule (container refuses a missing value or a relative `srv/work`, inline accepts them). Writing them as two test functions splits that rule. Fix: merge them into one parametrized test where each row expects either `(variable, fault)` or the values read, the way the criterion 3 test already handles `accepted`.
   2. criterion 8 added: it needs its test. The Interface makes a blank value count as unset and fixes the order of the container faults, but no row covers a blank `FACTORY_WORKSPACE` or `FACTORY_STAGE_IMAGE`. Example: if `or None` is dropped after `_optional(environ, STAGE_IMAGE_VARIABLE)` in `src/factory/domain/settings.py`, a blank image is accepted and every test still passes. Two order cases are also untested: a relative workspace before a missing image, and the agent user checked last (`agent_user` with no dataset). The new criterion 8 (old 8 and 9 are now 9 and 10) adds these as rows of the criterion 2 test. They need no change under `src/`.

   Earlier tests: none. The diff only adds test files (`A`: the three new modules) and changes no test file that `main` already holds.
10. factory: started doing as self.
11. coder: Round 1: both of the reviewer's findings are test changes, so I changed no code and no test.

    The tester should make these two changes in `tests/domain/test_settings_stage_environment.py`:
    1. Merge `test_read_settings_refuses_a_stage_environment_it_cannot_run` and `test_read_settings_accepts_any_values_for_the_inline_environment` into one parametrized test. Each row expects either a `(variable, fault)` or the values read, the same way the criterion 3 test handles `accepted`.
    2. Add the four rows of the new criterion 8 to that test:
       - `container` with the dataset and `FACTORY_WORKSPACE="  "` gives `FACTORY_WORKSPACE`, "missing for the container environment".
       - The dataset, the workspace and `FACTORY_STAGE_IMAGE="  "` gives `FACTORY_STAGE_IMAGE`, "missing for the container environment".
       - The dataset and `FACTORY_WORKSPACE=srv/work` with no image gives `FACTORY_WORKSPACE`, "is not an absolute path".
       - `FACTORY_AGENT_USER=agent` with no dataset gives `FACTORY_DATASET`, "missing for the container environment".

    I did not run the new rows, because they don't exist yet. I expect them to pass against the current `src/factory/domain/settings.py`, from reading the code:
    - A blank workspace becomes `None` through `_optional_path` (line 176), and a blank image becomes `None` through `or None` (line 177).
    - `_container_fault` (line 150) checks in the order the Interface gives: dataset, workspace missing, workspace relative, image, agent user last.

    If a row fails, it comes back to doing as a fix under `src/`.

    Noticed, not touched: what entry 7 listed is still open. That is the unreachable `None` narrowing in `_container_environment` in `src/factory/entry/wiring.py`, and `FACTORY_AGENT_USER`'s "is not a name" fault now coming before other settings' faults. The Description is unchanged: the journal added criterion 8, and the reviewer already wrote it into the Description.
12. factory: started tests as self.
13. tester: Made the test change the coder's entry 11 names, which carries out the reviewer's findings 1 and 2 (criterion 8). The only file I changed is tests/domain/test_settings_stage_environment.py, a module I wrote in this story. I changed no earlier test file and created no new file.

    What changed:
    - `test_read_settings_refuses_a_stage_environment_it_cannot_run` and `test_read_settings_accepts_any_values_for_the_inline_environment` are now one parametrized test, `test_read_settings_runs_a_container_only_with_its_values_and_inline_with_any`. Each row expects one of two things:
      - a `(variable, fault)` tuple, checked against the raised `SettingsInvalid`;
      - or a dict of the values read, which includes `stage_environment: inline` for the accepted inline rows.
    - The four rows of criterion 8 are added:
      - `blank-workspace`: `FACTORY_WORKSPACE="  "` → FACTORY_WORKSPACE, "missing for the container environment"
      - `blank-image`: `FACTORY_STAGE_IMAGE="  "` → FACTORY_STAGE_IMAGE, "missing for the container environment"
      - `relative-workspace-before-no-image`: dataset and `srv/work`, no image → FACTORY_WORKSPACE, "is not an absolute path"
      - `agent-user-after-no-dataset`: `container` with `FACTORY_AGENT_USER=agent` and no dataset → FACTORY_DATASET, "missing for the container environment"

    Criterion → test now:
    - criterion 1: tests/domain/test_settings_stage_environment.py::test_read_settings_reads_the_stage_environment_and_its_values
    - criterion 2: tests/domain/test_settings_stage_environment.py::test_read_settings_runs_a_container_only_with_its_values_and_inline_with_any
    - criterion 3: tests/domain/test_settings_stage_environment.py::test_instance_settings_built_directly_follow_the_stage_environment_rules
    - criterion 4: tests/entry/test_wiring_stage_environment.py::test_an_inline_instance_has_no_snapshots_and_no_containers
    - criterion 5: tests/entry/test_wiring_stage_environment.py::test_a_container_instance_gets_the_dataset_s_adapters_and_asks_for_no_tool, ::test_a_container_instance_s_runtime_runs_in_its_containers_unconfined, ::test_a_container_instance_s_runtime_mounts_its_login_file
    - criterion 6: tests/entry/test_wiring_stage_environment_home.py::test_the_agent_run_s_home_follows_the_stage_environment
    - criterion 7: tests/entry/test_wiring_stage_environment.py::test_wiring_a_container_instance_s_tick_starts_no_tool
    - criterion 8: the four new rows of the criterion 2 test (named above)
    - criteria 9 and 10 (make check, docs): no test.

    `make test`, run once: green (coverage 99.19 %). The new rows pass against the current src/factory/domain/settings.py, as the coder expected. No module failed to import. `make lint`: green.

    `lint`: lint: green (0.6 s)
    `test`: test: green (66.6 s)
14. factory: started doing as self.
15. coder: Round 1: the reviewer's two findings, the merged criterion 2 test and the criterion 8 rows, were test changes, and the tester made them in tests/domain/test_settings_stage_environment.py (entry 13). This round needed no change under src/, and I made none and touched no test. I ran `make check` on the committed state and it is green, with coverage at 99.19 %. The new rows pass against src/factory/domain/settings.py as it stands.

    What this story built is unchanged from entry 7:
    - src/factory/domain/settings.py: the six settings, `StageEnvironmentName`, and `stage_environment_fault`, which both the model validator and `read_settings` use.
    - src/factory/application/project_commands.py: `RecordingProjectCommands.inner`.
    - src/factory/entry/wiring.py: `_inline_environment` and `_container_environment` behind `build_boundaries`, `WORK_HOME_ENVIRONMENT`, and the container `HOME` in `agent_run_environment`.

    Main choice (also unchanged): one rule function shared by the validator and `read_settings`. I rejected turning pydantic's `ValidationError` back into `SettingsInvalid`, because that would mean parsing pydantic's message text.

    Refactor pass: I read the diff (three src files, about 217 lines added) and found nothing to change.

    Noticed, not touched (still open from entries 7 and 11):
    - src/factory/entry/wiring.py:364 is the `None` check in `_container_environment`. It exists only so mypy can narrow the types, the settings validator already rules it out, and it is the one uncovered line in that file.
    - `FACTORY_AGENT_USER`'s "is not a name" fault now comes before faults in settings that are read later.

    The journal added criterion 8, and the reviewer already wrote it into the Description, so I left the Description as it is.

    `check`: check: green

    `check`: check: green
    `duplicates`: duplicates: 13 new, 36 known, 2 gone
16. factory: started review as self.
17. reviewer: Review, round 1. I read the work item, the diff's stat and name-status, the diff under `src/` and the three new test modules.

    Group 1 (acceptance criteria) passes. I checked every criterion from 1 to 8 and every rule of the Interface:
    - criterion 1: `test_read_settings_reads_the_stage_environment_and_its_values`.
    - criteria 2 and 8: the merged `test_read_settings_runs_a_container_only_with_its_values_and_inline_with_any`. It has the faults, the four rows of criterion 8 (blank workspace, blank image, relative workspace before missing image, agent user after missing dataset) and the accepted `inline` rows, all in one parametrized test.
    - criterion 3: through `type[BaseModel]`.
    - criterion 4: the two `None`s.
    - criterion 5: `which` is never asked, `ZfsSnapshots.mount_point`, the podman words, `rollback -r tank/factory/vm@base`, `inner` is `ContainerMakeCommands`, `agent_home` is `None`, the claude and opencode rows, and the login volume.
    - criterion 6: `HOME` in three rows, and the base dict is unchanged.
    - criterion 7: the tick starts no tool.

    The coder's `make check` was green (entries 7 and 15).

    Group 2 (architecture) passes:
    - The settings rule is pure and sits in `domain` (`stage_environment_fault`, shared by the model validator and `read_settings`).
    - `RecordingProjectCommands.inner` is in `application`.
    - Only `factory.entry.wiring` builds `ZfsSnapshots`, `PodmanRuns` and `ContainerMakeCommands`.

    Group 3 (security) passes: no silencing marker, and no strings built into commands.

    Group 4 (quality) passes:
    - The docstrings on `stage_environment_fault`, `inner`, `build_boundaries` and `agent_run_environment` say what they do.
    - I ran `make duplicates` (13 new, 36 known, 2 gone; it exits with an error because new findings exist). All 13 new findings are in modules from earlier stories (`claude_runtime`/`opencode_runtime`, `podman_runs`, `zfs_snapshots`, `fake_containers`, `fake_snapshots`). None is in the three files this diff changes.

    Considered and not counted as findings:
    - The `None` guard in `_container_environment` (`src/factory/entry/wiring.py`) can never run, because the settings validator already rules it out. It is there only so mypy can narrow the types, so I did not count it as dead code.
    - `FACTORY_AGENT_USER` is now read earlier in `read_settings`. That changes only which fault is reported first when two settings are wrong; no rule fixes that order.

    Group 5 (work item hygiene) passes. The Description matches what was built, and the journal names the main choice (one rule function) and what was rejected (parsing pydantic's error text back). The docs criterion (now 10) still lists what the reader must know.

    no findings

    Earlier tests: none needed. The diff only adds test files (`A`: `tests/domain/test_settings_stage_environment.py`, `tests/entry/test_wiring_stage_environment.py`, `tests/entry/test_wiring_stage_environment_home.py`) and changes no test file that `main` already holds.

    Notes:
    1. `tests/entry/test_wiring_stage_environment.py`, `_recording_stand_in` and `_calls`: a second recording stand-in for `zfs` and `podman`. `tests/zfs_support.py` (`ZFS_SCRIPT`, `Zfs.arguments`) and `tests/podman_support.py` (`PODMAN_SCRIPT`, `PodmanPlan`) already provide these. The shared stand-ins could be used instead.
    2. `tests/entry/test_wiring_stage_environment.py`, `IMAGE` and `DATASET`: copies of `tests/podman_support.IMAGE` and `tests/zfs_support.DATASET`.
18. factory: started docs as self.
19. documenter: Docs round 1. I read the story, the diff of src and tests, and the documents below. The diff matches the Interface and the criteria, so I have no findings for the coder. I changed only documents, so I did not run `make check`; the factory's check after this stage decides. I ran no example, because I wrote no runnable one.

    Files changed:
    - docs/operator-guide.md, *Configuration*: six new rows in the settings table (`FACTORY_STAGE_ENVIRONMENT`, `FACTORY_DATASET`, `FACTORY_WORKSPACE`, `FACTORY_STAGE_IMAGE`, `FACTORY_PODMAN`, `FACTORY_ZFS`), each with its default and refusal text. A paragraph *The stage environment* follows the table. It says what `inline` and `container` are, that `container` needs the dataset, the workspace and the image, runs no second user and has no kernel guard, the order of the faults, and that the VM and stage image are F0043's and the preflight items S0011's.
    - docs/project-guide/stage-environment.md: new section *The settings and the wiring* (the six settings and their faults, `stage_environment_fault` shared by `read_settings` and the model validator, what `build_boundaries` builds for each environment, `RecordingProjectCommands.inner`, `HOME` in `agent_run_environment`, the tests). I also corrected the intro, which said nothing wires `ZfsSnapshots` or `PodmanRuns` yet, and the closing line of *Wiring and tests*, which said the real tools come with a later story.
    - docs/project-guide/watching.md, *Boundaries*: it said `build_boundaries` leaves `snapshots` and `containers` `None` for now. It now says they are `None` for `inline` and filled for `container`.
    - docs/project-guide/git-and-hosting.md: one sentence in the `identity` row pointing to `stage-environment.md` for the new settings.
    - docs/project-guide/README.md: the line of `stage-environment.md` now names *The settings and the wiring* and `factory.domain.settings` and `factory.entry.wiring`.

    docs/decisions.md: none, as the criterion says.

    Cross-read and found current: the rest of docs/operator-guide.md (the agent-user, leftovers and fresh-home passages still describe the `inline` environment correctly), and docs/project-guide/processes-and-checks.md, *Container project commands*, which already describes `ContainerMakeCommands`.

    Stale, not mine, not touched: nothing found beyond the passages above. One note on code, not docs: in src/factory/entry/wiring.py, the `None` guard in `_container_environment` can never run (the validator rules it out) and is the one uncovered line there. The reviewer and the coder already named it.

    `check`: check: green (not run again: passed on tree 65b825c80dd1 at 2026-10-24T21:09:24Z)
    `secrets`: secrets: green (2.0 s)
    `documents`: documents ok
20. factory: started smoke-test as self.
21. smoke-tester: Smoke test, round 1. I ran both commands under `## Smoke test` from the repository root, exactly as written and in order. I fixed nothing.

    Command 1 (`uv run python - <<'EOF' … read_settings …`). Exit 0. uv first created `.venv` and printed its setup lines: "Using CPython 3.12.15…", "Creating virtual environment…", a hardlink warning, "Installed 106 packages", "Bytecode compiled…". After those, the script printed:
    ```
    container tank/factory/vm /srv/factory/vm/work factory-stage:1 podman zfs
    inline None
    FACTORY_STAGE_ENVIRONMENT | holds Container, which is neither inline nor container
    FACTORY_DATASET | missing for the container environment
    FACTORY_WORKSPACE | is not an absolute path
    ```
    Met `Expect:` — yes. These are the five lines expected, word for word. The uv lines are its one-time environment setup, not output of the script.

    Command 2 (`uv run pytest <the three story test modules> 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '`). Exit 0.
    ```
    1
    ```
    Met `Expect:` — yes. To see the last line itself, I ran the same three modules once more without the pipe (`-p no:cacheprovider`). Its last line was `38 passed in 0.09s`.

    Judgement against `## Acceptance criteria`: the smoke test contradicts no criterion.
    - Line 1 of command 1 matches criterion 1: the container settings, with `podman` and `zfs` as defaults.
    - Line 2 matches criterion 1 and the description: inline is the default, and `dataset` is `None` when unset.
    - The three fault lines match criterion 2: the text for a wrong environment name, a missing dataset and a relative workspace.
    - Command 2 shows the story's three test modules green; these cover criteria 1 to 8.

    The smoke test does not exercise criterion 9 (`make check`) or criterion 10 (docs). The factory's checks and the docs stage cover those. Neither run left a tracked change. The only modified file is the work item's `.costs.jsonl` sidecar, which is the factory's.

    Findings: none.
