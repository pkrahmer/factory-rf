---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 470
comments_read: []
handed_over: approval
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
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-26T21:53:49.612515Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-26T22:05:27.700588Z'
  stage: tests
  run: 8a102ca455d64488ba5393d29bb3c4ac
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-26T22:05:49.339775Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-26T22:11:54.377715Z'
  stage: doing
  run: eb6f0bdbf6fa41c0ba5ee2c896c43c2a
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-26T22:12:15.058196Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-26T22:12:57.735272Z'
  stage: review
  run: 83e599e72dde45ae9b256bc257ad7c83
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-26T22:13:18.552799Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-26T22:14:01.205521Z'
  stage: docs
  run: 8dd84647a14e425e94f62c32c2e1abb4
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-26T22:14:21.682763Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-26T22:14:40.586448Z'
  stage: smoke-test
  run: 264cef0704944804b34afebb338707c8
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
4. factory: started tests as vm.
5. tester: Wrote the tests for criteria 1 to 5. I also changed the earlier tests the Interface names, under the leave of decision 25 of `feature.md`. Every earlier test kept its name.

   - criterion 1: tests/domain/test_settings_required_paths.py::test_the_agent_files_folder_is_a_required_absolute_path (9 rows: unset, empty and blank, each with and without HOME, raise `missing`; `srv/agents` raises `is not an absolute path`; `/srv/agents` is accepted with and without HOME)
   - criterion 2: tests/domain/test_settings_required_paths.py::test_with_a_reader_the_image_identity_file_is_a_required_absolute_path (the reader records each path; a refusal leaves it asked nothing, the success asks exactly `[Path("/srv/factory/vm/image-id")]`)
   - criterion 3: tests/domain/test_settings_required_paths.py::test_without_a_reader_the_image_identity_file_is_not_read
   - criterion 4: tests/domain/test_settings_required_paths.py::test_the_old_defaults_of_the_two_paths_are_gone (rows: no `IMAGE_ID_FILE` attribute; no string literal under src/factory contains `/opt/factory/image-id`, searched with `tests/source_search.py`; `agent_home` is not `/home/ann/.claude`)
   - criterion 5: tests/entry/test_run_required_paths.py::test_a_missing_path_setting_is_the_stop_of_invalid_settings (it uses the conftest `environment` fixture, with the state directory under tmp_path)
   - criteria 6 and 7: not tests (make check; docs).

   Files created: tests/domain/test_settings_required_paths.py, tests/entry/test_run_required_paths.py.

   Earlier test files changed under the leave:
   - tests/settings_support.py: `BASE` gains `FACTORY_CLAUDE_HOME=/srv/factory/factory-1/factory/claude`; the docstring says three required settings.
   - tests/domain/test_settings.py: changed as the Interface names.
     - The two-required-variables test also checks `agent_home`.
     - The missing/blank test gains `FACTORY_CLAUDE_HOME`.
     - The image-file test loses its default row.
     - The refused-image-file and image-label tests set `FACTORY_IMAGE_ID_FILE` to `OTHER_IMAGE_PATH`, and their readers answer for it.
     - `DEFAULT_IMAGE_PATH` is removed.
   - tests/domain/test_settings_boundaries.py: the HOME and `/home/agent/.claude` fallback rows are removed.
   - tests/domain/test_settings_url_edges.py: the rows `image-unreadable` and `image-empty` now use `/srv/factory/factory-1/image-id`.
   - tests/conftest.py: the fixtures `environment` (which now also takes the `agent_home` fixture) and `hosted_environment` gain `FACTORY_CLAUDE_HOME=<tmp_path>/agent-home`. Neither creates the folder, as before, when the default path did not exist either.
   - tests/application/test_boundaries_settings.py and tests/domain/test_default_git_identity.py: both use `BASE` from settings_support instead of their own copy of the two-variable dict.
   - tests/entry/test_watch_settings.py: the fixture `valid_environment` sets `FACTORY_CLAUDE_HOME`.
   - tests/entry/test_wiring_boundaries.py::test_git_options_carry_the_settings_identity_and_the_git_environment: its environment gains `FACTORY_CLAUDE_HOME`.
   - Settings modules that build CONTAINER environments: no change needed, because they all build on `BASE`.
   - Other environments (test_run_state_variable, test_wiring_run, test_run): no change needed, because they come from the conftest fixtures.

   The test run: every module imported, so there was no collection error. The new tests fail for the right reason: DID NOT RAISE SettingsInvalid, `IMAGE_ID_FILE` still present, the old path still in src, and `main` returning 0 without FACTORY_CLAUDE_HOME. The criterion-5 row without FACTORY_IMAGE_ID_FILE already passes: today's default `/opt/factory/image-id` does not exist on this machine, so the read is refused under that variable anyway. Through a pipe mistake I ran `make test` twice instead of once; both runs were the same suite with no changes in between. `make lint` is green.

   Open: none.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/entry/test_run_required_paths.py::test_a_missing_path_setting_is_the_stop_of_invalid_settings[agent-home] - assert 0 == 2
6. factory: started doing as vm.
7. coder: Made `FACTORY_CLAUDE_HOME` required, and `FACTORY_IMAGE_ID_FILE` required when a reader is given. Both must also be absolute paths. `make check` is green and the smoke test prints the three expected lines.

   - What I built: everything is in `src/factory/domain/settings.py`.
     - The constant `IMAGE_ID_FILE` (`/opt/factory/image-id`) is gone, and so is `_HOME_VARIABLE`. Nothing reads `HOME` any more.
     - There is one new private helper, `_required_absolute_path(environ, variable)`. It reuses the existing `_required`, which raises `missing` for an unset, empty or blank value. It raises `is not an absolute path` for a relative one.
     - `_agent_home` and `_image` both call this helper. `_image` calls it before `read_file`, so a refused variable means the reader is never asked. Without a reader, `_image` is not called and the variable is not read, as before.
     - `factory.entry.run` is unchanged. A refused variable takes the existing path for invalid settings.
   - Main choice: one shared helper for the "required and absolute" rule, built on `_required`. I rejected the alternative of making `_optional_absolute_path` check for a missing value too: it would need a flag or a second return branch, and its optional callers would get a slightly different contract.
   - Refactor: I read the diff and changed nothing more. The `is_absolute` check in the new helper is two lines that are similar to `_optional_absolute_path`. Reusing that function would mean narrowing a `Path | None` that can never be `None`, so I left it as it is.
   - Noticed, not touched:
     - `AGENT_HOME_DEFAULT` (`/home/agent/.claude`) stays as the default of the `InstanceSettings.agent_home` field. The story leaves that to S0006.
     - The docs criterion (operator guide, `watching.md`, `decisions.md`) is the documenter's.
   - Journal: no entry changed the meaning of the task, so the Description is unchanged.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 43 known, 0 gone
8. factory: started review as vm.
9. reviewer: no findings

   Read the diff of `src/factory/domain/settings.py` and the 11 test files against criteria 1 to 7 and the Interface.
   - Code: `_agent_home` and `_image` both go through `_required_absolute_path`. It builds on `_required`, so unset, empty and blank all give `missing`, and a relative path gives `is not an absolute path`.
   - `_image` checks the variable before it calls `read_file`, and without a reader the variable is never read.
   - `IMAGE_ID_FILE` and `_HOME_VARIABLE` are gone. `AGENT_HOME_DEFAULT` stays only as the default of the `InstanceSettings.agent_home` field, which the Description leaves to S0006.
   - `read_settings` has one caller under `src` (`entry/wiring.py:200`, with a reader), so `factory-run` and `factory-watch` both get the new rules. `entry.run` is unchanged.

   Criteria and their tests:
   - Criteria 1 to 4: `tests/domain/test_settings_required_paths.py`, one parametrized test each. The rows match the criteria, the refused and accepted sides included: the 9 agent-home rows, the recording reader asked `[]` on every refusal and exactly one path on success, the three rows without a reader, and the three "gone" rows.
   - Criterion 5: `tests/entry/test_run_required_paths.py`, with rows for both missing variables (status 2, the log line, the runner not run) and the row with both set (status 0, the runner run once).
   - Criterion 6: the coder's `make check` was green (journal 7).
   - Criterion 7: for the documenter.

   The Interface states no other limit. The architecture holds: the rule is in the domain and the reader is injected. No suppression markers and no secrets. The Description, the Interface and the docs criterion match what was built.

   Rejected as a finding: the near-duplicate `is_absolute` check in `_required_absolute_path` next to `_optional_absolute_path`. Reusing the optional helper would mean narrowing a `Path | None` that is never `None`, and `make duplicates` reports 0 new.

   Earlier tests changed (status M):
   - tests/settings_support.py: decision 25 of `feature.md` (named in the Interface).
   - tests/conftest.py: decision 25 (`hosted_environment` is named in the Interface; `environment` falls under its "every other earlier test" rule). Both fixtures only gain `FACTORY_CLAUDE_HOME`.
   - tests/domain/test_settings.py: decision 25 (named in the Interface; the changes match it, and every name is kept).
   - tests/domain/test_settings_boundaries.py: decision 25 (named in the Interface; only the fallback rows went, and the name is kept).
   - tests/domain/test_settings_url_edges.py: decision 25 (named in the Interface; the two image rows changed as stated).
   - tests/application/test_boundaries_settings.py: decision 25 (its environment gains the variable through the shared `BASE`, the assertions unchanged).
   - tests/domain/test_default_git_identity.py: the standing leave to move a shared test helper (its local copy of `BASE` is replaced by `settings_support.BASE`), and decision 25.
   - tests/entry/test_watch_settings.py: decision 25 (the fixture `valid_environment` gains the variable).
   - tests/entry/test_wiring_boundaries.py: decision 25 (one environment gains the variable).
10. factory: started docs as vm.
11. documenter: Documented that `FACTORY_CLAUDE_HOME` and `FACTORY_IMAGE_ID_FILE` are now required, absolute settings. The code matches the Interface and the criteria, so there are no findings for the coder. I changed only documents, so I did not run `make check` (the factory's checks decide). I did not run the smoke test.

    Files changed:
    - `docs/operator-guide.md`, `## Configuration`:
      - The `FACTORY_IMAGE_ID_FILE` row now says required for `factory-run` and `factory-watch`, absolute, with no default. It names `/srv/factory/<instance>/image-id`, which `vm/setup.sh` writes, and the refusals `missing` and `is not an absolute path`.
      - The `FACTORY_CLAUDE_HOME` row now says required and absolute, with no default and no `HOME` fallback. It names `/srv/factory/<instance>/factory/claude` and the same two refusals.
      - Neither row names `/opt/factory/image-id` or `/home/agent/.claude` any more.
    - `docs/operator-guide.md`, `## Looking at the remote: factory-watch`: it needs the same two path settings, so run it with the service's environment file, which `vm/setup.sh` writes.
    - `docs/project-guide/watching.md`, the `InstanceSettings` fields paragraph: states the two required settings and what `read_settings` refuses. It also says the `agent_home` field still has its default (`AGENT_HOME_DEFAULT`) until S0006. The criterion said the settings have no defaults, but the model keeps the field default in this story, so I wrote it that way.
    - `docs/decisions.md`, the entry "The image identity is read from a file the image build generates": added the closing line the criterion gave. I left its earlier "Open:" sentence in place; the new line closes it.

    Cross-read and found current:
    - `docs/operator-guide.md`:
      - the settings paragraph under the table, which says a required variable that is missing, empty or blank is refused;
      - the image identity paragraph;
      - the image build and cost-record paragraphs;
      - the `vm/setup.sh` environment file table;
      - the preflight `agents` item and its paragraph on which variables to check;
      - `## The agent files`.
    - `vm/setup.sh` writes both variables (lines 369–370), as the guide says.
    - `README.md`: no mention, and the criterion says none.

    Stale text I saw and did not touch (history, not this story's):
    - `docs/decisions.md` line 285, about F0010-S0006, says the build writes the uuid to `/opt/factory/image-id`. That is the build's own path in v1.1's image, so I did not change it.
    - `docs/decisions.md` line 440 and line 532 name `/home/agent/.claude` and `/home/agent/.claude-token` as v1.1 image paths.
    - `docs/decisions.md` line 1146 says the operator renews `FACTORY_IMAGE_ID_FILE`, which is still true.
    - `docs/operator-guide.md` line 96 says a missing file "cannot be read" is refused; it does not mention the new refusal of an unset variable. It is still true, and the table row now covers the new case.

    `check`: check: green (not run again: passed on tree a55791824ecf at 2026-10-26T22:09:07Z)
    `secrets`: secrets: green (2.1 s)
    `documents`: documents ok
12. factory: started smoke-test as vm.
13. smoke-tester: Smoke test passed: the one command printed the three expected lines, so there are no findings.

    I ran the single command under `## Smoke test` from the repository root, exactly as written.

    Command 1 (`uv run python -` with the heredoc that calls `read_settings` three times):
    ```
    Bytecode compiled 4164 files in 60ms
    FACTORY_CLAUDE_HOME: missing
    FACTORY_IMAGE_ID_FILE: missing
    /srv/agents build-7
    ```
    Met its `Expect:` line. The three lines are exactly `FACTORY_CLAUDE_HOME: missing`, `FACTORY_IMAGE_ID_FILE: missing` and `/srv/agents build-7`. The first line of output is uv compiling bytecode, not the program's output.

    Checked against the acceptance criteria:
    - The first case sets `HOME=/home/x` but no `FACTORY_CLAUDE_HOME`. It is still refused as `missing`, so nothing falls back to `HOME` (criteria 1 and 4).
    - The second case passes a reader but no `FACTORY_IMAGE_ID_FILE`. It is refused as `missing` (criterion 2).
    - The third case gives `agent_home` from the variable and the image identity from the reader (criteria 1 and 2).
    - The output contradicts no criterion. Criteria 3, 5, 6 and 7 are not covered by the smoke test: the tests cover 3 and 5 (journal 5 and 9), the factory's checks cover 6, and the documenter covered 7.

    Findings: none.
