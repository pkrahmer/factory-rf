---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 470
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T21:52:58.336386Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T21:52:58.342285Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T21:53:29.391611Z'
  stage: intake
  run: a81b79acc40b428c83597fb4dff35450
---

# The agent files' folder and the image identity file are required settings

## Description

Two settings still fall back to paths of v1.1's image when they are unset: `FACTORY_CLAUDE_HOME`, the folder of the agent files that the sync container mounts at `/etc/factory/claude` and the preflight's `agents` item reads, defaults to `$HOME/.claude` and, without a `HOME`, to `/home/agent/.claude` (the second user's home); `FACTORY_IMAGE_ID_FILE`, the file of the image identity that `factory-run` and `factory-watch` read, defaults to `/opt/factory/image-id` (v1.1's image). On the VM both are set by the environment file `vm/setup.sh` writes (F0043-S0003), so the defaults are never right there, and a missing line would fail late and quietly. This story makes both required where they are read and refuses a relative path (decision 14 of `feature.md`): `read_settings` refuses a missing or blank `FACTORY_CLAUDE_HOME`, and, when it is given a reader of the image identity, a missing or blank `FACTORY_IMAGE_ID_FILE`, each with `SettingsInvalid` naming its variable, which `factory-run` reports as the stop of invalid settings. What stays: the reading of the image identity file itself (stripped; unreadable or empty refused, as today); `read_settings` without a reader reads no image identity and asks for no `FACTORY_IMAGE_ID_FILE`; every other setting. The model `InstanceSettings` and the default of its field `agent_home` stay in this story; S0006 (the settings model refuses what the reading refuses) makes the field required.

## Interface

`factory.domain.settings` (`domain`):

- `IMAGE_ID_FILE` goes; `read_settings` reads no `HOME` for the agent files.
- `read_settings(environ, read_file=None)`: `FACTORY_CLAUDE_HOME` unset, empty or blank raises `SettingsInvalid(AGENT_HOME_VARIABLE, "missing")`; a value that is not an absolute path raises `SettingsInvalid(AGENT_HOME_VARIABLE, "is not an absolute path")`; otherwise `agent_home` is `Path(<value>)`.
- With `read_file` given: `FACTORY_IMAGE_ID_FILE` unset, empty or blank raises `SettingsInvalid(IMAGE_ID_FILE_VARIABLE, "missing")` before `read_file` is called; a value that is not an absolute path raises `SettingsInvalid(IMAGE_ID_FILE_VARIABLE, "is not an absolute path")` before `read_file` is called; otherwise the file is read as today (`read_setting_file`: `cannot read <path>: <error>`, `<path> is empty`). Without `read_file` the variable is not read at all.

`factory.entry.run.main`: unchanged; a refused variable is the stop of invalid settings as for every other setting.

Tests (the tester writes and changes them; the leave is decision 25 of `feature.md`): new tests at the tester's choice, for example `tests/domain/test_settings_required_paths.py`. Earlier tests, each keeping its name and its assertions unless named here:

- `tests/settings_support.py`: `BASE` gains `"FACTORY_CLAUDE_HOME": "/srv/factory/factory-1/factory/claude"`, and its docstring says three required settings.
- `tests/domain/test_settings.py`: `test_the_two_required_variables_give_the_settings_and_their_defaults` also checks `agent_home` (its name kept); `test_a_missing_or_blank_required_variable_is_refused` gains `FACTORY_CLAUDE_HOME` among its variables; `test_the_image_identity_is_read_from_its_file` loses its row without the variable (`DEFAULT_IMAGE_PATH`); `test_an_image_identity_file_that_gives_no_identity_is_refused` and `test_the_image_label_variable_is_not_the_image_identity` set `FACTORY_IMAGE_ID_FILE` to the path their reader answers for; `DEFAULT_IMAGE_PATH` goes when nothing reads it.
- `tests/domain/test_settings_boundaries.py::test_agent_home_comes_from_its_variable_then_home_then_the_default`: it keeps its rows that set the variable (with and without `HOME`); its rows that fall back to `HOME` or to `/home/agent/.claude` go (its name kept).
- `tests/domain/test_settings_url_edges.py::test_a_refused_setting_names_its_variable_and_its_fault`: the rows `image-unreadable` and `image-empty` set `FACTORY_IMAGE_ID_FILE=/srv/factory/factory-1/image-id` and expect `cannot read /srv/factory/factory-1/image-id: denied` and `/srv/factory/factory-1/image-id is empty`.
- `tests/conftest.py`: the fixture `hosted_environment` gains `FACTORY_CLAUDE_HOME` (a folder under `tmp_path`).
- Every other earlier test that reads settings from an environment of its own and fails only because `FACTORY_CLAUDE_HOME`, or with a reader `FACTORY_IMAGE_ID_FILE`, is now required: its environment gains the variable, by the leave's rule (among them `tests/entry/test_run.py`, `tests/entry/test_wiring_run.py`, `tests/entry/test_wiring_boundaries.py`, `tests/entry/test_watch_settings.py`, `tests/application/test_boundaries_settings.py`, `tests/domain/test_default_git_identity.py` and the settings modules that build `CONTAINER` environments).

## Acceptance criteria

1. The agent files' folder (rows of one parametrized test over `read_settings` of `BASE` less `FACTORY_CLAUDE_HOME` plus the row's variables, no reader): no `FACTORY_CLAUDE_HOME`, `FACTORY_CLAUDE_HOME=""` and `FACTORY_CLAUDE_HOME="  "`, each with and without `HOME=/home/ann`, raise `SettingsInvalid` with variable `FACTORY_CLAUDE_HOME` and fault `missing`; `FACTORY_CLAUDE_HOME=srv/agents` raises it with `is not an absolute path`; `FACTORY_CLAUDE_HOME=/srv/agents` gives `agent_home == Path("/srv/agents")`, with and without `HOME=/home/ann`.
2. The image identity file with a reader (rows of one parametrized test over `read_settings(BASE | row, read_file)` with a reader that records every path it is asked for and answers `build-7\n` for any): no `FACTORY_IMAGE_ID_FILE`, `""` and `"  "` raise `SettingsInvalid` with variable `FACTORY_IMAGE_ID_FILE` and fault `missing`, and the reader was asked nothing; `FACTORY_IMAGE_ID_FILE=image-id` raises it with `is not an absolute path`, the reader asked nothing; `FACTORY_IMAGE_ID_FILE=/srv/factory/vm/image-id` gives `image == "build-7"`, the reader asked exactly `[Path("/srv/factory/vm/image-id")]`.
3. Without a reader (rows of one parametrized test): `read_settings(BASE)`, `read_settings(BASE | {"FACTORY_IMAGE_ID_FILE": "image-id"})` and `read_settings(BASE | {"FACTORY_IMAGE_ID_FILE": "/srv/x"})` each give `image is None` and raise nothing.
4. The old defaults are gone (rows of one parametrized test): `IMAGE_ID_FILE` is no attribute of `factory.domain.settings`; no module under `src/factory` holds the string `/opt/factory/image-id`; `read_settings` of `BASE` with `FACTORY_CLAUDE_HOME=/srv/agents` and `HOME=/home/ann` gives an `agent_home` that is not `Path("/home/ann/.claude")`.
5. The stop at the start (rows of one parametrized test over `factory.entry.run.main` with a state directory under `tmp_path` and a runner that records whether it ran): an environment that is valid but lacks `FACTORY_CLAUDE_HOME` returns `2`, does not run the runner, and the factory log in the state directory gains a line that holds `settings invalid: FACTORY_CLAUDE_HOME`; one that lacks `FACTORY_IMAGE_ID_FILE` returns `2` with a line that holds `settings invalid: FACTORY_IMAGE_ID_FILE`; with both set (the image identity file written under `tmp_path`) it returns `0` and the runner ran once.
6. `make check` stays green.
7. docs: `docs/operator-guide.md`, `## Configuration`: the rows `FACTORY_CLAUDE_HOME` and `FACTORY_IMAGE_ID_FILE` say required (the second for `factory-run` and `factory-watch`), absolute, and name the paths `vm/setup.sh` writes; no row or paragraph names `/opt/factory/image-id` or `/home/agent/.claude`; `## Looking at the remote: factory-watch`: it needs the same two settings, so it is run with the environment file of the service. `docs/project-guide/watching.md`, where it lists the fields of `InstanceSettings`: the two settings without defaults. `docs/decisions.md`: the entry "The image identity is read from a file the image build generates", if it is there, gains one closing line: "Since v1.2 F0045-S0005 `FACTORY_IMAGE_ID_FILE` is required and absolute; the default `/opt/factory/image-id` and the open point on a blank value went." `README.md`: none.

## Smoke test

```bash
uv run python - <<'EOF'
from factory.domain.errors import SettingsInvalid
from factory.domain.settings import read_settings
base = {"FACTORY_REPOSITORY_URL": "/srv/project.git", "FACTORY_INSTANCE": "vm", "HOME": "/home/x"}
home = {**base, "FACTORY_CLAUDE_HOME": "/srv/agents"}
for environ, reader in ((base, None), (home, lambda path: "build-7"), ({**home, "FACTORY_IMAGE_ID_FILE": "/srv/id"}, lambda path: "build-7")):
    try:
        settings = read_settings(environ, reader)
        print(settings.agent_home, settings.image)
    except SettingsInvalid as error:
        print(error)
EOF
```
Expect: three lines: `FACTORY_CLAUDE_HOME: missing`; `FACTORY_IMAGE_ID_FILE: missing`; `/srv/agents build-7`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: concrete. It names `factory.domain.settings`, `read_settings(environ, read_file=None)`, the exact `SettingsInvalid(variable, fault)` texts, and the removal of `IMAGE_ID_FILE`. `AGENT_HOME_VARIABLE`, `IMAGE_ID_FILE_VARIABLE` and `_NOT_ABSOLUTE` already exist in `src/factory/domain/settings.py`. The tests to change are named, and decision 25 of `feature.md` gives the leave for them.
   - Criteria: each is one parametrized test with explicit rows. Every rule has both sides. Missing, empty and blank are covered, as is a relative path against an absolute one. For the image file, the reader is asked nothing on a refusal and asked exactly one path on success. Without a reader the variable is not read. The old defaults are gone (criterion 4). `main` returns 2 with the log line, and returns 0 when both settings are set (criterion 5). `make check` and `docs:` are last.
   - Smoke test: runnable with `uv run python -`. The three `Expect:` lines are checkable. With no `FACTORY_CLAUDE_HOME`, the first case prints `FACTORY_CLAUDE_HOME: missing`. With the home set, a reader and no image file, the second prints `FACTORY_IMAGE_ID_FILE: missing`. With both set, the third prints `/srv/agents build-7`. It runs no pytest, so the `-q` rule does not apply.
   - Architecture: the rules live in `domain.settings`, which does no I/O, because the reader is injected. `entry.run` only reports the stop, so the layers hold.
   - Scope: this is S0005 of F0045 (decision 14). `InstanceSettings.agent_home` is left to S0006, as the story says. Nothing in "Out of scope" is touched. The leave for the earlier tests is decision 25.
