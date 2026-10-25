---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 431
comments_read: [6391224129]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T00:06:11.842091Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T00:06:11.848014Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-25T00:06:29.801429Z'
  stage: intake
  run: 018f722281c84e70a5ca444649c82dcb
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-25T00:07:46.778408Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-25T00:08:04.754977Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-25T00:08:22.740686Z'
  stage: intake
  run: 2c5a4b2ffc3745d2967edf2eab935e15
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-25T00:08:42.892906Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-25T00:13:19.003744Z'
  stage: tests
  run: 3f5462b06e9d4387ae984a450ba6d331
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-25T00:13:39.457974Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-25T00:17:35.673762Z'
  stage: doing
  run: 13f82b7124804b1888f38bcc53bef24a
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-25T00:17:56.386012Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-25T00:19:19.054877Z'
  stage: review
  run: 3e8a102ac619422cad895645ea2d8680
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-25T00:19:39.867729Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-25T00:19:57.228998Z'
  stage: doing
  run: 203cf0d04cdf483197d8625f6b2e6ae8
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-25T00:20:17.501316Z'
  stage: tests
- number: 16
  speaker: tester
  kind: result
  at: '2026-10-25T00:23:10.727810Z'
  stage: tests
  run: 4c0fd5a1c547424a8cc9e09d6ddfa30a
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-25T00:23:31.207818Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-25T00:26:37.960388Z'
  stage: doing
  run: ddddd58c96254485a5a81add78e21d1f
---

# The checkout and the state directory are settings

## Description

The factory's own checkout lies at `/work/checkout` and its state directory at `/state`: both are fixed in the code (`CHECKOUT_PATH` and `STATE_DIRECTORY` of `factory.domain.settings`), because in v1.1's container they are volumes and nothing else needs to move them. On the machine of v1.2 the factory runs as a systemd service on the host, under `/srv/factory/<instance>` (`planning/v1.2-plan.md`, "The cycle of a stage", step 1: the factory's own clone at `/srv/factory/<instance>/repo`; "Where the factory runs": `/state` as a folder of the service), and S0003's environment file names both places. This story makes them settings: `FACTORY_CHECKOUT` and `FACTORY_STATE`, each an absolute path, each with today's value as its default, read by `read_settings` with the fault a relative `FACTORY_WORKSPACE` has (`is not an absolute path`) and, on a `container` instance (F0042-S0010), a fault when either lies inside `FACTORY_WORKSPACE`, whose every rollback would reset it, and makes `factory-run` write the stop of invalid settings into the directory `FACTORY_STATE` names, so that a fault on the VM lands where `factory-health --state-directory` reads it. The name `FACTORY_STATE` is the one the entrypoint already reads for `/state/runs`. What stays: a compose instance that sets neither variable runs exactly as today; `factory-health` keeps its `--state-directory` option and its default `/state`; the entrypoint is unchanged; every other setting and fault is unchanged (decision 1 of `feature.md`).

## Interface

`factory.domain.settings` (`domain`):

```python
CHECKOUT_VARIABLE = "FACTORY_CHECKOUT"
STATE_VARIABLE = "FACTORY_STATE"
```

- `read_settings(environ, ...)` reads the two variables, each stripped of surrounding whitespace; a blank or unset value gives the default (`CHECKOUT_PATH`, `/work/checkout`; `STATE_DIRECTORY`, `/state`). A relative value is `SettingsInvalid(<variable>, "is not an absolute path")`. The two are read after the instance's name and before the image identity file, `FACTORY_CHECKOUT` first, so a fault in them is reported after one in `FACTORY_REPOSITORY_URL` or `FACTORY_INSTANCE` and before one in any other variable; `InstanceSettings.checkout` and `InstanceSettings.state_directory` take them. `InstanceSettings` built directly refuses a relative `checkout` or `state_directory` through a validator (`ValidationError`), and accepts any absolute path, except inside the workspace of a `container` instance (the next rule).
- For a `container` instance (`stage_environment` and `workspace`, the fields of F0042-S0010, which is merged before this story starts): a `checkout` that is the `workspace` or lies inside it (`Path.is_relative_to`, by path parts, so `/srv/factory/vm/workrepo` is not inside `/srv/factory/vm/work`) is `SettingsInvalid(CHECKOUT_VARIABLE, "<checkout> lies inside FACTORY_WORKSPACE")`, because every rollback of the dataset would reset the factory's own work tree; a `state_directory` there is `SettingsInvalid(STATE_VARIABLE, "<state_directory> lies inside FACTORY_WORKSPACE")`, because the agent's container would reach the health file and the runs. The checkout is checked first, and both after S0010's faults of the container settings, so an unset or relative workspace is reported as S0010 says. An `inline` instance accepts any absolute paths. `InstanceSettings` built directly refuses the same through its model validator (`ValidationError`).
- Nothing else of the settings changes: `CHECKOUT_PATH` and `STATE_DIRECTORY` keep their names and values (`tests/test_image_gitconfig.py` reads `CHECKOUT_PATH`).

`factory.entry.run` (`entry`):

```python
def main(
    environ: Mapping[str, str] | None = None,
    *,
    runner: Callable[[InstanceSettings], None] | None = None,
    state_directory: Path = STATE_DIRECTORY,
    clock: Clock | None = None,
) -> int: ...
```

- The signature does not change; `state_directory` becomes the fallback. The stop of invalid settings (`settings invalid: <variable>: <fault>` in the factory log, the `preflight_failed` stop in `health.json`) is written to the directory `FACTORY_STATE` names in the environment read (stripped) when it is set, non-blank and absolute, else to `state_directory`. A relative `FACTORY_STATE` is itself the fault reported, and the stop goes to `state_directory`. The same rule places the stop of a `SettingsInvalid` the runner raises after the settings were read (the token file of `run_instance`): under the directory `FACTORY_STATE` names, else under `state_directory`; today that stop always goes to `state_directory`.

`factory.entry.health` (`entry`): unchanged; `--state-directory` stays, default `STATE_DIRECTORY`.

Tests (the tester writes them): `tests/domain/test_settings_paths.py` and `tests/entry/test_run_state_variable.py` (built like `tests/entry/test_run.py`, with a runner that raises or records and a manual clock). One earlier test changes, by the leave of decision 15 of `feature.md`: `test_the_checkout_and_state_directory_are_not_read_from_the_environment` of `tests/domain/test_settings.py` pins that `FACTORY_CHECKOUT` is ignored; the tester removes its `FACTORY_CHECKOUT` entry and renames it `test_a_variable_the_settings_do_not_name_is_not_read`, keeping its `FACTORY_STATE_DIRECTORY` and `SOMETHING_ELSE` entries and both assertions. Every other settings and run test is unchanged.

## Acceptance criteria

1. `read_settings` (rows of one parametrized test over `BASE` of `tests/settings_support.py`): neither variable gives `checkout` `Path("/work/checkout")` and `state_directory` `Path("/state")`; `FACTORY_CHECKOUT=/srv/factory/vm/repo` and `FACTORY_STATE=/srv/factory/vm/state` give those two paths; `FACTORY_CHECKOUT=  /srv/factory/vm/repo  ` (surrounding spaces) gives `Path("/srv/factory/vm/repo")`, and `FACTORY_STATE=  /srv/factory/vm/state  ` gives `Path("/srv/factory/vm/state")`; an empty `FACTORY_STATE` gives `Path("/state")`, and a `FACTORY_CHECKOUT` of only spaces gives `Path("/work/checkout")`.
2. The faults (rows of one parametrized test, each `SettingsInvalid` with the named variable and the text `is not an absolute path`): `FACTORY_CHECKOUT=srv/repo`; `FACTORY_STATE=state`; `FACTORY_STATE=./state`; and the order: `FACTORY_CHECKOUT=relative` together with `FACTORY_MIN_FREE_GB=0` reports `FACTORY_CHECKOUT`; `FACTORY_CHECKOUT=relative` read with a `read_file` that raises (`raising` of `tests/settings_support.py`) reports `FACTORY_CHECKOUT`, and `FACTORY_STATE=relative` read with it reports `FACTORY_STATE`; `FACTORY_CHECKOUT=relative` together with `FACTORY_STATE=relative` reports `FACTORY_CHECKOUT`; while `FACTORY_INSTANCE=Bad` together with `FACTORY_CHECKOUT=relative` reports `FACTORY_INSTANCE`.
3. `InstanceSettings` built directly (rows of one parametrized test through a `type[BaseModel]`): `checkout=Path("/srv/factory/vm/repo")` is accepted; `checkout=Path("srv/repo")` is `ValidationError`; `state_directory=Path("/srv/factory/vm/state")` is accepted; `state_directory=Path("state")` is `ValidationError`.
4. `factory.entry.run.main` with an invalid environment (the `environment` fixture of `tests/entry/test_run.py` with `FACTORY_REPOSITORY_URL=https://example.invalid/a.git,https://example.invalid/b.git`, which names two repositories), `FACTORY_STATE=<tmp>/state` and `state_directory=<tmp>/fallback`: returns 2, `<tmp>/state/factory.log` holds the line ending `settings invalid: FACTORY_REPOSITORY_URL: names more than one repository`, `<tmp>/state/health.json` holds the `preflight_failed` stop with that detail, and `<tmp>/fallback` does not exist afterwards (the environment's directory wins over the fallback).
5. The fallback (rows of one parametrized test, each with `state_directory=<tmp>/fallback` and returning 2): an invalid environment without `FACTORY_STATE` writes the log line and the stop under `<tmp>/fallback`; one with `FACTORY_STATE=` (blank) writes them under `<tmp>/fallback`; one whose other variables are valid (the `environment` fixture of `tests/entry/test_run.py`) and whose `FACTORY_STATE` is `state` (relative), run from `<tmp>` as the current directory, writes under `<tmp>/fallback` the line ending `settings invalid: FACTORY_STATE: is not an absolute path` and the stop with that detail, and makes no directory named `state` under the current directory.
6. `main` with a valid environment (the `environment` fixture of `tests/entry/test_run.py` with `FACTORY_CHECKOUT=<tmp>/repo` and `FACTORY_STATE=<tmp>/state`) and `state_directory=<tmp>/fallback` (rows of one parametrized test): with a recording runner, the runner receives settings whose `checkout` is `<tmp>/repo` and `state_directory` `<tmp>/state`, and `main` returns 0; with a runner that raises `SettingsInvalid("FACTORY_TOKEN_FILE", "cannot read <tmp>/token")`, `main` returns 2 and `<tmp>/state/factory.log` holds the line ending `settings invalid: FACTORY_TOKEN_FILE: cannot read <tmp>/token`; in both rows `<tmp>/fallback` does not exist afterwards; with a runner that raises `SettingsInvalid("FACTORY_TOKEN_FILE", "cannot read <tmp>/token")` and `FACTORY_STATE` unset, `main` returns 2 and the line ending `settings invalid: FACTORY_TOKEN_FILE: cannot read <tmp>/token` and the stop are under `<tmp>/fallback`; with an invalid environment (the two repositories of criterion 4) and `FACTORY_STATE` padded as `  <tmp>/state  `, `main` returns 2 and the log line and the stop are under `<tmp>/state` (the variable is stripped), and `<tmp>/fallback` does not exist afterwards.
7. The workspace of a `container` instance (rows of one parametrized test over `BASE` with `FACTORY_STAGE_ENVIRONMENT=container`, `FACTORY_DATASET=tank/factory/vm` and `FACTORY_STAGE_IMAGE=factory-stage:1`, each refusal a `SettingsInvalid` with the named variable and the exact text): `FACTORY_WORKSPACE=/work` without `FACTORY_CHECKOUT` gives `FACTORY_CHECKOUT` and `/work/checkout lies inside FACTORY_WORKSPACE`; `FACTORY_WORKSPACE=/srv/factory/vm/work` with `FACTORY_CHECKOUT=/srv/factory/vm/work` gives `FACTORY_CHECKOUT` and `/srv/factory/vm/work lies inside FACTORY_WORKSPACE`; with `FACTORY_CHECKOUT=/srv/factory/vm/repo` and `FACTORY_STATE=/srv/factory/vm/work/state` gives `FACTORY_STATE` and `/srv/factory/vm/work/state lies inside FACTORY_WORKSPACE`; with `FACTORY_CHECKOUT=/srv/factory/vm/work/checkout` and `FACTORY_STATE=/srv/factory/vm/work/state` gives `FACTORY_CHECKOUT` (the checkout first); `FACTORY_WORKSPACE=srv/work` gives `FACTORY_WORKSPACE` and `is not an absolute path` (S0010's fault first); `FACTORY_WORKSPACE=/srv/factory/vm/work` with `FACTORY_CHECKOUT=/srv/factory/vm/repo` and `FACTORY_STATE=/srv/factory/vm/state` is accepted, and so is `FACTORY_CHECKOUT=/srv/factory/vm/workrepo` with the same state (a sibling whose name starts with the workspace's); `BASE` with `FACTORY_WORKSPACE=/work` and no `FACTORY_STAGE_ENVIRONMENT` (inline) is accepted with `checkout` `Path("/work/checkout")`. Built directly through a `type[BaseModel]`: `stage_environment="container"` with `dataset`, `stage_image`, `workspace=Path("/work")` and the default `checkout` is `ValidationError`; the same with `workspace=Path("/srv/factory/vm/work")` and `checkout=Path("/srv/factory/vm/repo")` is accepted; the same with `workspace=Path("/srv/factory/vm/work")`, `checkout=Path("/srv/factory/vm/repo")` and `state_directory=Path("/srv/factory/vm/work/state")` is `ValidationError`.
8. `make check` stays green.
9. docs: `docs/operator-guide.md`, *Configuration*: two table rows right after `FACTORY_INSTANCE` (a relative path is reported right after the instance's fault), and the sentence "it reports the first fault in the order of the table" corrected to the code's order (the stage environment's faults, the inside-workspace fault among them, come before those of the variables below `FACTORY_AGENT_USER`), `FACTORY_CHECKOUT` (no; the factory's own checkout, an absolute path; default `/work/checkout`; a relative path is refused with `FACTORY_CHECKOUT` as the variable) and `FACTORY_STATE` (no; the state directory, an absolute path; default `/state`; a relative path is refused with `FACTORY_STATE` as the variable; `factory-health --state-directory <it>` reads the same place), and the paragraph "The checkout and the state directory are not settings you can change ..." rewritten: they are, through these two variables, the image leaves both unset, and the VM of v1.2 sets both under `/srv/factory/<instance>` (pointing to `## The machine`); *When the process refuses to start*: the stop and the log line go to the directory `FACTORY_STATE` names, else `/state`, and a relative `FACTORY_STATE` is the fault itself; *The entrypoint*: the sentence "(the factory ignores `FACTORY_STATE`: the state directory is fixed)" becomes one that says the factory reads it too; *The health check and the restart policy*: the `--state-directory` option of `factory-health`. `docs/project-guide/git-and-hosting.md` (which names `factory.domain.settings`): one sentence on the two path settings and their validator; `docs/operator-guide.md`, the paragraph *The stage environment* after the table, and `docs/project-guide/stage-environment.md`, *The settings and the wiring*: one sentence each on the rule that a `container` instance's checkout and state directory lie outside `FACTORY_WORKSPACE`, with its fault `<path> lies inside FACTORY_WORKSPACE`; `docs/project-guide/watching.md` (which names `factory.entry.run` and `factory.entry.health`): where the stop of invalid settings goes. `docs/decisions.md`: a new short entry "The checkout and the state directory are settings" naming 2026-10-24, `planning/v1.2-plan.md` and F0043, and under "One instance runs one project, and the settings can name no second one", whose sentence "The checkout and the state directory are constants, never read from the environment" no longer holds, a line "Superseded in part by *The checkout and the state directory are settings*" saying what changed. `README.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
from pathlib import Path

from factory.domain.errors import SettingsInvalid
from factory.domain.settings import CHECKOUT_PATH, STATE_DIRECTORY, read_settings

base = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "vm"}
s = read_settings({**base, "FACTORY_CHECKOUT": " /srv/factory/vm/repo ", "FACTORY_STATE": "/srv/factory/vm/state"})
print(s.checkout, s.state_directory)
d = read_settings(base)
print(d.checkout == CHECKOUT_PATH, d.state_directory == STATE_DIRECTORY, d.checkout, d.state_directory)
for extra in ({"FACTORY_CHECKOUT": "srv/repo"}, {"FACTORY_STATE": "./state"}, {"FACTORY_CHECKOUT": "x", "FACTORY_MIN_FREE_GB": "0"}):
    try:
        read_settings({**base, **extra})
    except SettingsInvalid as error:
        print(error.variable, "|", error.fault)
EOF
```
Expect: five lines: `/srv/factory/vm/repo /srv/factory/vm/state`; `True True /work/checkout /state`; `FACTORY_CHECKOUT | is not an absolute path`; `FACTORY_STATE | is not an absolute path`; `FACTORY_CHECKOUT | is not an absolute path`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
FACTORY_REPOSITORY_URL='https://example.invalid/a.git,https://example.invalid/b.git' FACTORY_INSTANCE=vm FACTORY_STATE="$d/state" uv run factory-run; echo "status $?"
grep -c 'settings invalid: FACTORY_REPOSITORY_URL: names more than one repository' "$d/state/factory.log"; grep -c preflight_failed "$d/state/health.json"
```
Expect: four lines: the time-stamped line ending `settings invalid: FACTORY_REPOSITORY_URL: names more than one repository`, `status 2`, `1`, `1`

```bash
uv run pytest tests/domain/test_settings_paths.py tests/entry/test_run_state_variable.py tests/domain/test_settings.py tests/entry/test_run.py tests/entry/test_health.py 2>&1 | tail -1 | grep -cE '^[0-9]+ passed in '
```
Expect: `1`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: Format check passed. Interface, smoke tests and architecture look sound, and the scope is within feature.md decision 1. Three Interface rules have no criterion, so two coders could read them differently and still pass:

   1. The Interface says `InstanceSettings` built directly refuses "the same" through its model validator. That includes a `state_directory` inside the workspace of a `container` instance. Criterion 7's directly built rows cover only the `checkout` side: the default checkout with `workspace=/work` is refused, and a valid pair is accepted. Nothing tests a directly built `state_directory` inside `workspace`, for example `workspace=/srv/factory/vm/work` with `state_directory=/srv/factory/vm/work/state` and a valid checkout. Proposed: add that row as `ValidationError`. I would choose this.

   2. The `main` rule says the stop of a `SettingsInvalid` the runner raises goes under the `FACTORY_STATE` directory, "else under `state_directory`". Criterion 6 covers only the first branch, with `FACTORY_STATE` set. Nothing tests the runner-raised fault with `FACTORY_STATE` unset, blank or relative. Today's behaviour (always `state_directory`) would pass every criterion in either case. Proposed: add a row in which the runner raises `SettingsInvalid` and `FACTORY_STATE` is unset, and the stop and the log line land under `<tmp>/fallback`. I would choose this.

   3. The `main` rule says `FACTORY_STATE` is read "(stripped)". No criterion has a padded value in `main`. Criterion 1 tests the strip only in `read_settings`, and `main` reads the variable separately to place the stop. Proposed: add a row in which `FACTORY_STATE` is `  <tmp>/state  ` with an invalid environment, and the stop lands under `<tmp>/state`. I would choose this.
4. 2026-10-25 human: Yes to all three, as you propose; add them to the criteria yourself (the work item is your write path), then continue:
   1. Criterion 7 gains the row: `InstanceSettings` built directly with `workspace=/srv/factory/vm/work`, `state_directory=/srv/factory/vm/work/state` and a valid checkout raises `ValidationError`.
   2. Criterion 6 gains the row: the runner raises `SettingsInvalid` with `FACTORY_STATE` unset, and the stop and its log line land under the fallback `state_directory` (`<tmp>/fallback`).
   3. Criterion 6 gains the row: `FACTORY_STATE` is `  <tmp>/state  ` (padded) with an invalid environment, and the stop lands under `<tmp>/state`.
   Each is a row of the parametrized test its criterion already has; nothing else changes.
5. factory: started intake as self.
6. intake: accepted
   - Interface: concrete. It names `factory.domain.settings` (`CHECKOUT_VARIABLE`, `STATE_VARIABLE`, `read_settings`, the `InstanceSettings` validators) and `factory.entry.run.main` with its full signature. The order of faults and the exact fault texts are stated.
   - Criteria: each is testable by one parametrized test function. Every rule has both sides: absolute against relative, set against blank or unset, `container` against `inline`, a workspace sibling (`workrepo`) against a path inside it, checkout first against state first, and the `FACTORY_STATE` directory against the fallback. The three gaps from my first question are closed with the human's answer, journal entry 4. I wrote them into the criteria as that answer asked:
     - Criterion 6 gains a runner-raised `SettingsInvalid` with `FACTORY_STATE` unset, which must land under the fallback.
     - Criterion 6 gains a padded `FACTORY_STATE` with an invalid environment, which must land under `<tmp>/state`.
     - Criterion 7 gains a directly built `InstanceSettings` with `state_directory` inside the workspace, which must raise `ValidationError`.
   - Smoke test: the three blocks are runnable. The pytest command passes no `-q`, and I did not check the project's pytest configuration for an `addopts` setting. Each `Expect:` line is checkable. The one hedge is that the first block's third `Expect:` line relies on `FACTORY_CHECKOUT` being read before `FACTORY_MIN_FREE_GB`, which criterion 2 pins.
   - Architecture: the changes sit in `domain` (pure settings rules) and `entry` (placing the stop). No new dependency or layer. `factory-health` and the entrypoint are unchanged.
   - Scope: this is decision 1 of `feature.md`, and nothing in its Out of scope is touched. The one earlier test it changes has the human's leave in decision 15.
7. factory: started tests as self.
8. tester: I wrote the tests for criteria 1–7 from the Interface and the criteria. Criteria 8 (`make check`) and 9 (docs) have no test of their own.

   - criterion 1: tests/domain/test_settings_paths.py::test_the_checkout_and_the_state_directory_are_read_with_their_defaults
   - criterion 2: tests/domain/test_settings_paths.py::test_a_relative_checkout_or_state_directory_is_refused_in_its_order, plus tests/domain/test_settings_paths.py::test_a_fault_of_the_instance_is_reported_before_one_of_the_checkout. The `FACTORY_INSTANCE=Bad` row is a separate function because its fault is not `is not an absolute path`; only the variable is checked.
   - criterion 3: tests/domain/test_settings_paths.py::test_settings_built_directly_refuse_a_relative_checkout_or_state_directory
   - criterion 4: tests/entry/test_run_state_variable.py::test_the_stop_of_invalid_settings_goes_to_the_directory_the_environment_names
   - criterion 5: tests/entry/test_run_state_variable.py::test_the_stop_of_invalid_settings_falls_back_to_the_given_directory (it changes into `tmp_path` as the current directory for every row)
   - criterion 6: tests/entry/test_run_state_variable.py::test_the_runner_gets_the_paths_and_its_settings_fault_follows_the_state_variable (rows: recorded, runner-fault, runner-fault-without-state, state-padded)
   - criterion 7: two functions, one for the rows read from the environment and one for the rows built directly:
     - tests/domain/test_settings_paths.py::test_a_container_instance_keeps_its_checkout_and_state_outside_the_workspace
     - tests/domain/test_settings_paths.py::test_settings_built_directly_keep_a_container_checkout_and_state_outside_the_workspace

   Files created:
   - tests/domain/test_settings_paths.py
   - tests/entry/test_run_state_variable.py

   Earlier test files changed:
   - tests/domain/test_settings.py: by the leave of decision 15 named in the Interface, `test_the_checkout_and_state_directory_are_not_read_from_the_environment` is renamed `test_a_variable_the_settings_do_not_name_is_not_read`. Its `FACTORY_CHECKOUT` entry is removed; the `FACTORY_STATE_DIRECTORY` and `SOMETHING_ELSE` entries and both assertions stay.
   - tests/entry/test_run.py and tests/conftest.py: under the standing leave to move a shared test helper, the `image_file` and `environment` fixtures moved from tests/entry/test_run.py to tests/conftest.py, unchanged, because the criteria use that `environment` fixture. tests/entry/test_run.py also drops its copy of `HOSTED_URL` and imports it from `wiring_support`, which holds the same value. Every test in test_run.py keeps its name and checks the same thing. tests/entry/test_wiring_container_extras.py has its own `environment` fixture, which takes precedence there.

   Red run (`make test`, once): the tests fail on wrong results, not on import errors. Examples: `state-relative` gives `assert 0 == 2`, `recorded` sees `/state` instead of `<tmp>/state`, and `runner-fault` and `state-padded` hit `FileNotFoundError` because the stop is not under `<tmp>/state`. `CHECKOUT_VARIABLE` and `STATE_VARIABLE` are not imported by the tests, so the test runner could import every module and there were no collection errors. The tail I read showed only the last entry-test failures; I did not rerun to count the domain failures.

   `make lint` is green. I skipped the type check as this stage says.

   `lint`: lint: green (0.5 s)
   `test`: FAILED tests/entry/test_run_state_variable.py::test_the_runner_gets_the_paths_and_its_settings_fault_follows_the_state_variable[state-padded] - FileNotFoundError: [Errno 2] No such file or director...
9. factory: started doing as self.
10. coder: I built the code that makes the checkout and the state directory settings. `make check` is green, and the tester's new tests in `tests/domain/test_settings_paths.py` and `tests/entry/test_run_state_variable.py` pass without changes.

    - `src/factory/domain/settings.py`:
      - New constants `CHECKOUT_VARIABLE` (`FACTORY_CHECKOUT`) and `STATE_VARIABLE` (`FACTORY_STATE`).
      - `_absolute_path` reads each variable stripped. A blank or unset value gives the default; a relative value is `SettingsInvalid(<variable>, "is not an absolute path")`. `read_settings` calls it after `_instance` and before `_image`, checkout first.
      - A `field_validator` on `checkout` and `state_directory` refuses relative paths when `InstanceSettings` is built directly.
      - The new public `workspace_overlap_fault(stage_environment, workspace, checkout, state_directory)` gives `<path> lies inside FACTORY_WORKSPACE`. It compares by path parts (`Path.is_relative_to`) and checks the checkout first. Both `read_settings` and the model validator call it as `stage_environment_fault(...) or workspace_overlap_fault(...)`, so the container faults stay first.
      - The new public `named_state_directory(environ)` returns the absolute directory `FACTORY_STATE` names, else `None`.
      - The fault text "is not an absolute path" is now one constant, `_NOT_ABSOLUTE`, which the existing workspace fault also uses.
    - `src/factory/entry/run.py`: `main` reads the environment once into `variables`. Any `SettingsInvalid`, from reading the settings or from the runner, is reported under `named_state_directory(variables) or state_directory`. A relative `FACTORY_STATE` is itself the fault from `read_settings`, and its stop goes to the fallback. The signature is unchanged.

    Main choice: the inside-workspace rule is its own function next to `stage_environment_fault`. I first added `checkout` and `state_directory` as keyword arguments to `stage_environment_fault`, but ruff's PLR0913 refused seven arguments, and a separate rule also keeps the existing function's contract as it was.

    Rejected:
    - Reading `FACTORY_STATE` with its own stripping code in `run.py`: that would copy `_optional_path` from the domain module.
    - Placing the stop from the settings that were read: they don't exist when reading fails.

    Refactor: I read the diff and found nothing to change.

    Noticed, not touched:
    - The docs that criterion 9 names (the operator guide, the project guide, the decision log) are the documenter's.
    - `factory.entry.health` is unchanged, as the Interface says.
    - `InstanceSettings` is not part of the records contract, so no schema needs regenerating.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 36 known, 2 gone
11. factory: started review as self.
12. reviewer: I checked every criterion and every rule of the Interface against `git diff main...HEAD -- . ':!factory'`. I read `src/factory/domain/settings.py`, `src/factory/entry/run.py`, `tests/domain/test_settings_paths.py` and `tests/entry/test_run_state_variable.py`, and the changes to `tests/domain/test_settings.py`, `tests/entry/test_run.py` and `tests/conftest.py`. Criteria 1 and 3 to 7 each have a test that checks what the criterion states, with every row it names: the fallback, the padded and blank `FACTORY_STATE`, the runner's fault with and without the variable, the workspace sibling, the checkout checked first, and S0010's fault coming first. The coder's `make check` was green (entry 10). I also ran `make duplicates`: all 11 new findings are in `claude_runtime`/`opencode_runtime`, `fake_containers`, `podman_runs`, `zfs_snapshots` and `fake_snapshots`. None of those files is in this diff.

    Findings:
    1. `tests/domain/test_settings_paths.py:106` (`test_a_fault_of_the_instance_is_reported_before_one_of_the_checkout`): criterion 2 asks for its order rows as rows of one parametrized test. The `FACTORY_INSTANCE=Bad` with `FACTORY_CHECKOUT=relative` row is a separate test function instead, so one side of the order rule (the instance before the checkout) is split from the others (the checkout before the image, the state and `FACTORY_MIN_FREE_GB`). Fix: make it a row of `test_a_relative_checkout_or_state_directory_is_refused_in_its_order`. To do that, change that test's expected column from a variable to the full `(variable, fault)` pair, with the instance's own fault text in that row, and delete the separate function.

    Groups 2 to 5 were not reviewed, because group 1 failed.

    Earlier tests:
    - `tests/domain/test_settings.py`: the human's leave, decision 15 of `feature.md`, named in the story's Interface. Only the `FACTORY_CHECKOUT` entry was removed and the test renamed to `test_a_variable_the_settings_do_not_name_is_not_read`. The `FACTORY_STATE_DIRECTORY` and `SOMETHING_ELSE` entries and both assertions are kept.
    - `tests/entry/test_run.py`: the standing leave to move a shared test helper. The `image_file` and `environment` fixtures moved to `tests/conftest.py` unchanged. The module's copy of `HOSTED_URL` now comes from `wiring_support`, which holds the same value. Every test keeps its name and what it checks.
    - `tests/conftest.py`: the standing leave to move a shared test helper. It only adds the two fixtures moved from `tests/entry/test_run.py`.
13. factory: started doing as self.
14. coder: Round 1: the reviewer's only finding (entry 12, finding 1) asks for a test change and no code change, so I changed nothing and am sending it to the tester.

    The change the tester should make, in `tests/domain/test_settings_paths.py`:
    - Move the `FACTORY_INSTANCE=Bad` with `FACTORY_CHECKOUT=relative` case into `test_a_relative_checkout_or_state_directory_is_refused_in_its_order` as one more row.
    - Change that test's expected column from the variable alone to the full `(variable, fault)` pair, with the instance's own fault text in the new row.
    - Delete the separate function `test_a_fault_of_the_instance_is_reported_before_one_of_the_checkout`.

    Code: `src/factory/domain/settings.py` already reports the instance's fault before the checkout's, so the merged test should pass with no code change. I did not run it, because the merged test does not exist yet. I did not run `make check` this round either, since nothing in the working tree changed; it was green in entry 10.

    Rejected: changing the test myself. The coder never edits tests.

    Noticed, not touched: nothing new beyond entry 10.
15. factory: started tests as self.
16. tester: Round 1, an approved test change: the coder named it in entry 14, from the reviewer's finding 1 in entry 12. I made only that change, in `tests/domain/test_settings_paths.py`:
    - The case with `FACTORY_INSTANCE=Bad` and `FACTORY_CHECKOUT=relative` is now the row `instance-before-checkout` of `test_a_relative_checkout_or_state_directory_is_refused_in_its_order`. It expects `("FACTORY_INSTANCE", "is not a name")`, which is the instance's own fault text from `_name` in `src/factory/domain/settings.py`.
    - That test's expected column is now the full `(variable, fault)` pair (`fault: tuple[str, str]`) instead of the variable alone. The text shared by the other rows is the new module constant `NOT_ABSOLUTE`.
    - I deleted the separate function `test_a_fault_of_the_instance_is_reported_before_one_of_the_checkout`.

    Criterion 2 now maps to one test: tests/domain/test_settings_paths.py::test_a_relative_checkout_or_state_directory_is_refused_in_its_order. The mapping for the other criteria is the same as in entry 8.

    No files created. No other test files changed. I ran `make test` once and it is green: coverage 99.20 %, `test: green (66.8 s)`. Every module imported. `make lint` is green.

    `lint`: lint: green (0.6 s)
    `test`: test: green (67.4 s)
17. factory: started doing as self.
18. coder: Round 1: the reviewer's only finding (entry 12, finding 1) needed a test change and no code change. The tester made it in entry 16: the instance-before-checkout case is now a row of `test_a_relative_checkout_or_state_directory_is_refused_in_its_order` in `tests/domain/test_settings_paths.py`.

    What I built this round: nothing. I did not touch `src/factory/domain/settings.py` or `src/factory/entry/run.py`. The code from entry 10 already reports `FACTORY_INSTANCE`'s fault before `FACTORY_CHECKOUT`'s, and the merged row passes against it.

    - I ran `make check` on the committed state. It is green: `test: green (66.2 s)`, coverage 99.20 %, then `check: green`.
    - Refactor: no diff of mine this round, so nothing to change.
    - Main choice: leave the code as it is rather than adjust it to the merged test, because the test already passes. Rejected: any code change, since the finding asked for none.
    - Description: no journal entry since entry 10 changed what the task means, so I did not rewrite it.

    Noticed, not touched: the same as entry 10. The docs that criterion 9 names belong to the documenter. The 11 new `make duplicates` findings the reviewer listed are in files outside this diff.

    `check`: check: green
    `duplicates`: duplicates: 11 new, 36 known, 2 gone
