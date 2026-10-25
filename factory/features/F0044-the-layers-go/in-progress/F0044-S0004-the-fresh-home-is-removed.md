---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 447
comments_read: [6398446445]
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-25T13:46:22.145696Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-25T13:46:22.151881Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-10-25T13:46:42.699710Z'
  stage: intake
  run: 6879e2bb5eb14438bebfc9560c81cffb
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-10-25T13:49:02.184072Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-10-25T13:49:20.089009Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-10-25T13:49:43.060038Z'
  stage: intake
  run: 5e3fbf00369e4be4b56e1f718a9715fb
- number: 7
  speaker: factory
  kind: started
  at: '2026-10-25T13:50:03.695310Z'
  stage: tests
- number: 8
  speaker: tester
  kind: result
  at: '2026-10-25T13:54:12.049964Z'
  stage: tests
  run: e8eee716f7974213b5e3832ecb9ebd74
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-25T13:54:32.716948Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-25T13:58:58.030953Z'
  stage: doing
  run: 3364d4f93fba431d923e3a9ffe42db78
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-25T13:59:18.652992Z'
  stage: review
- number: 12
  speaker: reviewer
  kind: result
  at: '2026-10-25T14:00:37.818140Z'
  stage: review
  run: 2da4563cb0664ba5a747048afa7d545a
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-25T14:00:58.972371Z'
  stage: docs
- number: 14
  speaker: documenter
  kind: result
  at: '2026-10-25T14:02:09.682534Z'
  stage: docs
  run: 6740030648b24b18bbb7ac0aab61171b
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-25T14:02:30.360283Z'
  stage: smoke-test
- number: 16
  speaker: smoke-tester
  kind: result
  at: '2026-10-25T14:03:07.689529Z'
  stage: smoke-test
  run: e18f9bc4598b4d388c46f19f4b499cbe
---

# The fresh home is removed

## Description

Since F0040 (agent code never runs with the factory's rights) an instance with an agent user resets that user's home before every agent run and every project command: `SudoAgentHome.reset` starts `python -I -B -m factory.entry.fresh_home --home <home> --keep <path>...` through `sudo`, which removes every file the agent's user made there except the logins, the runtimes' login state files, uv's package cache and the folders `FACTORY_OPENCODE_FOLDERS` names. On a `container` instance the agent's home is the dataset's `home/` (`HOME=/work/home`), and the rollback to the base gives every stage a fresh one; the wiring builds no agent home there (F0042-S0010). This story removes the reset and everything that exists only for it: the program, the two adapters, the interface `AgentHome` and its field in `Boundaries`, the domain's rules of what is kept, the wiring's `agent_home_of` and `fresh_home_command`, the home reset inside `run_sealed` and `SealedProjectCommands`, and the setting `FACTORY_OPENCODE_FOLDERS`, which after S0001 (no agent call starts through the write guard's wrapper) names only folders the reset keeps. It is built before S0005 (the second user) for the reason S0003 is (decision 1 of `feature.md`). What stays: `InstanceSettings.agent_home` and `FACTORY_CLAUDE_HOME`, the folder of the agent files that the sync container copies into `/work/home/.claude` and the preflight's `agents` item reads; the seal around a run and a project command until S0006; the session a run resumed after a provider limit finds in the dataset's home.

## Interface

Removed whole: `src/factory/entry/fresh_home.py`, `src/factory/adapters/agent_home.py`, `src/factory/adapters/home_files.py`, `src/factory/domain/agent_home.py`, `src/factory/application/agent_home.py`.

`factory.domain.containers` (`domain`): `beneath_or_at(relative: str, above: str) -> bool` moves here unchanged from `factory.domain.agent_home`, because `check_container_call` here and `FakeContainerRuns._map` read it; `factory.adapters.fake_containers` imports it from `factory.domain.containers` and no longer imports `factory.domain.agent_home`; the rows that test it are in `tests/domain/test_containers_beneath_or_at.py::test_beneath_or_at_gives_the_answers_it_gave_in_agent_home`. `inside_home`, `kept_paths`, `fate`, `removed_when_empty`, `HomeFate` and `FRESH_HOME_PREFIX` go with the module.

`factory.application.boundaries.Boundaries` (`application`): the field `agent_home: AgentHome | None` goes; `snapshots` and `containers` keep their defaults.

`factory.application.sealed_runs` (`application`): `run_sealed` resets no home; `SealedProjectCommands.__init__(inner, git, log)` loses `home`, and `_reset_home` goes.

`factory.domain.settings` (`domain`): `OPENCODE_FOLDERS_VARIABLE`, `InstanceSettings.opencode_folders`, `_opencode_folders`, `_opencode_folder` and the import of `inside_home` go; `FACTORY_OPENCODE_FOLDERS` is read by nothing (an instance that still sets it starts as before).

`factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime` (`adapters`): `LOGIN_STATE_FILE` goes from each.

`factory.entry.wiring` (`entry`): `FRESH_HOME_MODULE`, `UV_CACHE_FOLDER`, `fresh_home_command` and `agent_home_of` go (and from `__all__`), with the imports of `SudoAgentHome` and `kept_paths` and the import of the modules `claude_runtime` and `opencode_runtime` (read only for `LOGIN_STATE_FILE`); `_StageEnvironmentBoundaries` loses `agent_home`, and `_project_commands` its keyword `agent_home`; `build_boundaries` passes no `agent_home`; `_project_commands` builds `SealedProjectCommands(MakeProjectCommands(..., user=...), git, log)` for an agent user.

Tests (the leave is decision 20 of `feature.md`):

- Deleted whole: `tests/adapters/test_home_files.py`, `tests/adapters/test_sudo_agent_home.py`, `tests/application/test_agent_home_resets.py`, `tests/domain/test_agent_home.py`, `tests/domain/test_settings_opencode_folders.py`, `tests/entry/test_fresh_home.py`, `tests/entry/test_wiring_agent_home.py`, and the helper module `tests/home_files_support.py`.
- `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module`: the set loses `factory.adapters.agent_home`; `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`: the set loses `factory.entry.fresh_home`. Each keeps its name.
- F0042-S0010's `tests/entry/test_wiring_stage_environment.py::test_a_container_instance_gets_the_dataset_s_adapters_and_asks_for_no_tool`: the assertion `boundaries.agent_home is None` goes with the field; the test keeps its name.
- No other earlier test changes: `tests/application/test_sealed_project_commands.py`, `tests/application/test_sealed_runs.py`, `tests/entry/test_wiring_constants.py`, `tests/domain/test_settings.py` and `tests/domain/test_settings_boundaries.py` name nothing that goes and pass unchanged.

## Acceptance criteria

1. The removed modules (rows of one parametrized test): `importlib.util.find_spec` is `None` for `factory.entry.fresh_home`, `factory.adapters.agent_home`, `factory.adapters.home_files`, `factory.domain.agent_home` and `factory.application.agent_home`.
2. The removed names (rows of one parametrized test): `Boundaries` has no field `agent_home` (`dataclasses.fields`); `InstanceSettings.model_fields` holds no `opencode_folders` and still holds `agent_home`; `OPENCODE_FOLDERS_VARIABLE` is no attribute of `factory.domain.settings`; `LOGIN_STATE_FILE` none of either runtime module; `fresh_home_command`, `agent_home_of`, `FRESH_HOME_MODULE` and `UV_CACHE_FOLDER` none of `factory.entry.wiring`; `SealedProjectCommands.__init__` has the parameters `inner`, `git`, `log` and no other.
3. `FACTORY_OPENCODE_FOLDERS` is read by nothing (rows of one parametrized test over `read_settings` and the base environment of `tests/settings_support.py`): with `FACTORY_OPENCODE_FOLDERS=.local/x` and with `FACTORY_OPENCODE_FOLDERS=/etc` (refused until now) the settings are read without a fault and equal those read without the variable.
4. A run and a command reset no home and keep their seal (rows of one parametrized test on the `boundaries` fixture with `FakeAgentRuntime`): a file `<tmp>/home/kept.txt` written before `run_sealed(boundaries, request)` of a request whose `HOME` is `<tmp>/home` is still there after it, and `boundaries.git.check_seal()` passes after it; the same file is there after `SealedProjectCommands(<a recording ProjectCommands of the test>, boundaries.git, <a recording log>).run("lint", time_limit=1 minute)`, which ran the inner command once.
5. The agent files stay: `read_settings` with `FACTORY_CLAUDE_HOME=/srv/factory/vm/factory/claude` gives `agent_home` `Path("/srv/factory/vm/factory/claude")`, and the sync container of `ContainerEnvironment.prepare` still mounts that folder read-only at `/etc/factory/claude` (the existing `tests/application/test_container_environment.py` stays green unchanged).
6. `factory.domain.containers.beneath_or_at` gives the answers of today's code, `relative == above or relative.startswith(f"{above}/")` (rows of one parametrized test, `tests/domain/test_containers_beneath_or_at.py::test_beneath_or_at_gives_the_answers_it_gave_in_agent_home`): a path equal to `above` is `True`; a path beneath it is `True`; a sibling with the same prefix (`ab` against `a`) is `False`; an unrelated path is `False`; with an empty `above`, `""` is `True`, `"a"` is `False` and `"/a"` is `True`.
7. `make check` stays green.
8. docs: `docs/project-guide/agents.md`, *The fresh home*: replaced by one paragraph that the agent's home is the dataset's `home/`, made fresh by the rollback, and that a resumed run finds its session there; `docs/project-guide/watching.md`, *Boundaries*: no `agent_home` field; `docs/project-guide/processes-and-checks.md`, *Sealed project commands*: no home reset; `docs/project-guide/README.md`, *The files*: the lines follow, and *Shared test helpers*: the line of `home_files_support.py` goes; `docs/project-guide/agents.md`, *The opencode runtime*, the paragraph **opencode's folders**: no fresh home, no `FACTORY_OPENCODE_FOLDERS` and no `agent_home_of`; `docs/project-guide/stage-environment.md`, the table of the two environments: the row `agent_home` goes; `docs/operator-guide.md`, *The agent runs as a second user*: the heading *The home is cleared before every run* and its paragraphs from the program's command block up to and including **First reset after the upgrade.** go, while the paragraphs after them (the refused `sudo`, the take, *The agent's login token*, *The agent's API key*, the checks on a running instance, *A `time_limit` under `sudo`*) stay in *The agent runs as a second user*; one sentence there says the dataset's rollback clears the home; the sentence "The agent's home is cleared before every run (see ...)" goes; the login token's paragraph no longer says the fresh home keeps the login or clears `.claude.json`; the table's rows *The home is fresh* and *The home is reset* go; *Configuration*: the row `FACTORY_OPENCODE_FOLDERS` goes from the table; *Running on opencode*: no fresh home and no `FACTORY_OPENCODE_FOLDERS`. `docs/decisions.md`: the entry "Every agent run and every project command starts from a fresh agent home" gains one closing line: "Replaced by the dataset's rollback, v1.2 F0044-S0004." `README.md`: none.

## Smoke test

```bash
for module in factory.entry.fresh_home factory.adapters.agent_home factory.adapters.home_files factory.domain.agent_home factory.application.agent_home; do uv run python -c "import $module" 2>/dev/null && echo present || echo gone; done
uv run python -c 'import dataclasses; from factory.application.boundaries import Boundaries; from factory.domain.settings import InstanceSettings as s; print("agent_home" in [f.name for f in dataclasses.fields(Boundaries)], "opencode_folders" in s.model_fields, "agent_home" in s.model_fields)'
```
Expect: six lines: `gone`, `gone`, `gone`, `gone`, `gone`, `False False True`

## Journal

1. 2026-10-25 human: created.
2. factory: started intake as self.
3. intake: Format check passed. One question.

   1. The Interface moves `beneath_or_at(relative: str, above: str) -> bool` to `factory.domain.containers` "unchanged", and `factory.adapters.fake_containers` imports it from there. No criterion tests either. Criterion 2 covers only removed names. No test under `tests/` names `beneath_or_at` today, and its behaviour is covered only through `tests/domain/test_agent_home.py`, which this story deletes whole. After the story, nothing would catch a broken or missing move. Two coders could also move it differently and still pass every test.

      Options:
      - (a) Add a criterion, rows of one parametrized test, that `factory.domain.containers.beneath_or_at` exists and gives the same answers as before. The rows would be a path equal to `above`, a path beneath it, a sibling with the same prefix (`ab` against `a`), an unrelated path, and the empty `above` case if the current code handles it. The criterion would go before the two closing ones. Also state in the Interface that `fake_containers` no longer imports `factory.domain.agent_home`, and name the test that carries the rows.
      - (b) State that its behaviour is covered by the existing container tests, and name them.

      I would choose (a).

   The other checks found nothing else:
   - **Interface:** names concrete modules and signatures.
   - **Smoke test:** runnable, with a checkable `Expect:`. It runs no pytest, so the `-q` rule does not apply.
   - **Architecture:** removals only, layers respected.
   - **Scope:** inside the feature's S0004 scope.
4. 2026-10-25 human: (a). Add the criterion before the two closing ones: one parametrized test (for example `tests/domain/test_containers_beneath_or_at.py::test_beneath_or_at_gives_the_answers_it_gave_in_agent_home`) whose rows check that `factory.domain.containers.beneath_or_at` gives the same answers as today's code (`relative == above or relative.startswith(f"{above}/")`): a path equal to `above` is `True`, a path beneath it is `True`, a sibling with the same prefix (`ab` against `a`) is `False`, an unrelated path is `False`, and the empty `above` gives what that expression gives today (`""` is `True`, `"a"` is `False`, `"/a"` is `True`). Also state in the Interface that `factory.adapters.fake_containers` no longer imports `factory.domain.agent_home`, and name the test that carries the rows. A new test needs no leave.
5. factory: started intake as self.
6. intake: accepted
   - Interface: names concrete modules, signatures and removals. Per the human's answer (journal 4) it now also says `factory.adapters.fake_containers` no longer imports `factory.domain.agent_home`, and names the test that carries the `beneath_or_at` rows. That is the human's edit carried in, not mine.
   - Criteria: each is testable by one parametrized test. The `FACTORY_OPENCODE_FOLDERS` rule has both sides: `.local/x`, and `/etc`, which was refused before. The home reset has its absence criterion with the seal kept. Per journal 4 I added criterion 6 before the two closing ones: `beneath_or_at` rows for equal, beneath, same-prefix sibling, unrelated, and empty `above` with `""`/`"a"`/`"/a"`. `make check` and `docs:` are now criteria 7 and 8.
   - Smoke test: the commands are runnable, they run no pytest so the `-q` rule does not apply, and the `Expect:` line is checkable (six exact lines).
   - Architecture: removals only; the layers are respected and `beneath_or_at` moves down to the domain.
   - Scope: inside feature S0004. The tests changed or deleted are the ones decision 20 and decision 33 of `feature.md` give leave for, and the new test file needs no leave.
7. factory: started tests as self.
8. tester: I wrote the tests for criteria 1 to 6 and made the earlier-test changes the Interface lists, under the leave of decision 20. `make lint` is green. I skipped the type check, as the stage says. The single `make test` run is red on purpose: the removed names are still present, and `beneath_or_at` does not exist yet in `factory.domain.containers`.

   Each criterion and its test:
   - criterion 1: tests/test_home_reset_removed.py::test_the_modules_of_the_home_reset_are_gone (five rows, one per module)
   - criterion 2: tests/test_home_reset_removed.py::test_the_names_of_the_home_reset_are_gone. It has 11 rows:
     - the `Boundaries` field
     - `InstanceSettings` has no `opencode_folders` and still has `agent_home`
     - `OPENCODE_FOLDERS_VARIABLE`
     - `LOGIN_STATE_FILE` in each runtime module
     - the four names in wiring
     - the parameters of `SealedProjectCommands.__init__`, which are `self`, `inner`, `git` and `log`
   - criterion 3: tests/domain/test_settings_opencode_folders_ignored.py::test_the_opencode_folders_variable_changes_no_setting (rows `.local/x` and `/etc`)
   - criterion 4: tests/application/test_sealed_runs_no_home.py::test_a_sealed_run_leaves_the_home_alone_and_keeps_the_seal. It has two rows:
     - agent-run: `run_sealed` with `FakeAgentRuntime` and `HOME=<tmp>/home`
     - project-command: `SealedProjectCommands` around a recording `ProjectCommands`, which ran `lint` once

     Each row checks that `home/kept.txt` is still there, then calls `boundaries.git.check_seal()`.
   - criterion 5: tests/domain/test_settings_agent_files_stay.py::test_the_agent_files_folder_still_comes_from_its_variable. The sync-container mount is covered by the existing tests/application/test_container_environment.py, unchanged.
   - criterion 6: tests/domain/test_containers_beneath_or_at.py::test_beneath_or_at_gives_the_answers_it_gave_in_agent_home. It has seven rows: equal, beneath, `ab` against `a`, unrelated, and the empty `above` with `""`, `"a"` and `"/a"`.
   - criterion 7 (`make check`) and criterion 8 (docs) have no test.

   Criteria 4, 3 and the settings rows of criterion 2 check that something is absent. Today's code already passes them, so they cannot fail before the change.

   Files created:
   - tests/test_home_reset_removed.py
   - tests/application/test_sealed_runs_no_home.py
   - tests/domain/test_settings_opencode_folders_ignored.py
   - tests/domain/test_settings_agent_files_stay.py
   - tests/domain/test_containers_beneath_or_at.py

   Earlier test files deleted, as the Interface lists:
   - tests/adapters/test_home_files.py
   - tests/adapters/test_sudo_agent_home.py
   - tests/application/test_agent_home_resets.py
   - tests/domain/test_agent_home.py
   - tests/domain/test_settings_opencode_folders.py
   - tests/entry/test_fresh_home.py
   - tests/entry/test_wiring_agent_home.py
   - tests/home_files_support.py

   Earlier test files changed, each test keeping its name:
   - tests/test_wrapper_search.py: the set loses `factory.adapters.agent_home`
   - tests/entry/test_wiring.py: the set loses `factory.entry.fresh_home`
   - tests/entry/test_wiring_stage_environment.py: the assertion `boundaries.agent_home is None` is gone

   What the test run could not import: `beneath_or_at` from `factory.domain.containers`, so the module tests/domain/test_containers_beneath_or_at.py fails to collect. Everything else is a plain failure on what is there now:
   - the names-gone rows and modules-gone rows fail because the old modules and names still exist
   - the two wrapper and wiring set tests fail because the old modules still import what they did

   No question is open.

   `lint`: lint: green (0.7 s)
   `test`: FAILED tests/test_home_reset_removed.py::test_the_names_of_the_home_reset_are_gone[sealed-project-commands-parameters] - assert False
9. factory: started doing as self.
10. coder: I removed the home reset and everything that existed only for it. `make check` is green: lint, types, layers, sast, secrets, licenses, and test (74.7 s).

    Built:
    - **Deleted:** `src/factory/entry/fresh_home.py`, `src/factory/adapters/agent_home.py`, `src/factory/adapters/home_files.py`, `src/factory/domain/agent_home.py`, `src/factory/application/agent_home.py`.
    - `src/factory/domain/containers.py`: `beneath_or_at` moved here unchanged. It sits above `check_container_call`, which uses it.
    - `src/factory/adapters/fake_containers.py`: now imports `beneath_or_at` from `factory.domain.containers`.
    - `src/factory/application/boundaries.py`: the field `agent_home` and its import are gone.
    - `src/factory/application/sealed_runs.py`:
      - `run_sealed` resets no home.
      - `SealedProjectCommands.__init__` now takes only `(inner, git, log)`, and `_reset_home` is gone.
      - Imports that are now unused are gone.
      - The docstrings no longer mention the reset.
    - `src/factory/domain/settings.py`: `OPENCODE_FOLDERS_VARIABLE`, `InstanceSettings.opencode_folders`, `_opencode_folders`, `_opencode_folder` and the import of `inside_home` are gone. `agent_home` and `FACTORY_CLAUDE_HOME` stay.
    - `src/factory/adapters/claude_runtime.py` and `src/factory/adapters/opencode_runtime.py`: `LOGIN_STATE_FILE` is gone from both.
    - `src/factory/entry/wiring.py`:
      - Gone: `FRESH_HOME_MODULE`, `UV_CACHE_FOLDER`, `fresh_home_command` and `agent_home_of`, also from `__all__`.
      - Gone: the imports of `SudoAgentHome`, `kept_paths` and the `claude_runtime`/`opencode_runtime` modules.
      - `_StageEnvironmentBoundaries` loses `agent_home`, and `_project_commands` loses its keyword `agent_home`.
      - For an agent user, `_project_commands` now builds `SealedProjectCommands(MakeProjectCommands(..., user=user), git, log)`.

    Main choice: I took everything out, as the Interface says, and left no inert placeholder. I rejected keeping `SealedProjectCommands`'s `home` parameter as an optional no-op for compatibility, because criterion 2 requires exactly the parameters `inner`, `git` and `log`, and nothing passes a home any more. `beneath_or_at` went into `containers.py` as a plain module-level function, unchanged. I did not put it into a shared path-helpers module, because no other module needs it.

    Refactor pass: I read the diff and found nothing more to change; the change is removals only. The only step left was ruff format dropping a trailing blank line in `sealed_runs.py`.

    Noticed, not touched: `make duplicates` reports `7 new, 34 known, 4 gone`. Two of the new findings are claude_runtime/opencode_runtime similar-code pairs; together with the gone pair they are the same lines moved after `LOGIN_STATE_FILE` was removed. The other two similar-code pairs (fake_containers/podman_runs, podman_runs/zfs_snapshots) and the three vulture dead-code findings (`FakeContainerRuns`, its `calls`, `FakeSnapshots`) are in files I did not change or only changed an import in. The baseline is not mine to update. The docs for criterion 8 are the documenter's.

    `check`: check: green
    `duplicates`: duplicates: 7 new, 34 known, 4 gone
11. factory: started review as self.
12. reviewer: no findings

    I reviewed `git diff main...HEAD -- . ':!factory'` against the work item.
    - **Criteria 1 to 6:** each has the parametrized test that the tester's entry (journal 8) names, and each test checks what its criterion says:
      - criterion 1: `tests/test_home_reset_removed.py::test_the_modules_of_the_home_reset_are_gone`
      - criterion 2: `tests/test_home_reset_removed.py::test_the_names_of_the_home_reset_are_gone`, 11 rows, including the exact `__init__` parameters
      - criterion 3: `tests/domain/test_settings_opencode_folders_ignored.py`, with the `.local/x` row and the `/etc` row that used to be refused
      - criterion 4: `tests/application/test_sealed_runs_no_home.py`, where both rows check that the file is kept and that `check_seal`, and the command row also checks that the inner command ran exactly once
      - criterion 5: `tests/domain/test_settings_agent_files_stay.py`, plus the existing `tests/application/test_container_environment.py`, unchanged
      - criterion 6: `tests/domain/test_containers_beneath_or_at.py`, 7 rows
    - **Check:** the factory's `make check` after the coder was green (journal 10).
    - **Architecture:** the change only removes code, plus one move down within `domain`. `beneath_or_at` moved unchanged to `src/factory/domain/containers.py:37`. `fake_containers` imports it from there. Nothing in `src/` still mentions a removed name.
    - **Security:** no marker or baseline entry was added.
    - **Quality:** the docstrings of `run_sealed` and `SealedProjectCommands.run` no longer mention the reset. No dead imports are left: `sys` is still used in `wiring.py`.
    - **`make duplicates` (7 new):** I ran it and read the new findings.
      - The claude_runtime/opencode_runtime pairs are the known pairs at new line numbers, now that `LOGIN_STATE_FILE` is gone.
      - The fake_containers/podman_runs and podman_runs/zfs_snapshots pairs, and the vulture findings for `FakeContainerRuns`, `calls` and `FakeSnapshots`, come from code this diff does not touch.
    - **Work item:** the Description, Interface and criteria match what was built, and the journal names the main decision and the option rejected (keeping `home` as a no-op parameter).

    Earlier tests:
    - tests/adapters/test_home_files.py: deleted, under the human's leave (story Interface, decision 20 of `feature.md`)
    - tests/adapters/test_sudo_agent_home.py: deleted, under the human's leave (decision 20)
    - tests/application/test_agent_home_resets.py: deleted, under the human's leave (decision 20)
    - tests/domain/test_agent_home.py: deleted, under the human's leave (decision 20)
    - tests/domain/test_settings_opencode_folders.py: deleted, under the human's leave (decision 20)
    - tests/entry/test_fresh_home.py: deleted, under the human's leave (decision 20)
    - tests/entry/test_wiring_agent_home.py: deleted, under the human's leave (decision 20)
    - tests/home_files_support.py: deleted, under the human's leave (decision 20)
    - tests/test_wrapper_search.py: the set loses `factory.adapters.agent_home` and the test keeps its name, under the human's leave (decision 20)
    - tests/entry/test_wiring.py: the set loses `factory.entry.fresh_home` and the test keeps its name, under the human's leave (decisions 20 and 33(a))
    - tests/entry/test_wiring_stage_environment.py: the assertion `boundaries.agent_home is None` is gone and the test keeps its name, under the human's leave (decision 20)
13. factory: started docs as self.
14. documenter: I wrote the documentation criterion 8 asks for and cross-read the rest against the diff. The code matches the Interface, so there are no findings. I changed only documents, so I did not run `make check`; the factory's checks after this stage decide.

    Files changed, one line each:
    - `docs/project-guide/agents.md`: *The fresh home* (the program, its rule, its walk, `SudoAgentHome`, `agent_home_of`, what was kept, its tests) is replaced by one paragraph, *The agent's home*. The home is the dataset's `home/`, the rollback makes it fresh, and a resumed run finds its session there. In **opencode's folders** the fresh home, `FACTORY_OPENCODE_FOLDERS` and `agent_home_of` are gone, and the rollback is named.
    - `docs/project-guide/watching.md`, *Boundaries*: the `agent_home` field and its wiring are gone, and `snapshots` and `containers` are now described as the last fields.
    - `docs/project-guide/processes-and-checks.md`, *Sealed project commands*: the signature is `SealedProjectCommands(inner, git, log)`. The `home` parameter and the reset with its error path are gone, and the text says it resets no home.
    - `docs/project-guide/stage-environment.md`: the `agent_home` row of the table of the two environments is gone. `run_agent` of the inline environment no longer says that the home is reset.
    - `docs/project-guide/README.md`: the `agents.md` line no longer lists the removed modules and refers to *The agent's home*. The line of `home_files_support.py` under *Shared test helpers* is gone.
    - `docs/operator-guide.md`:
      - The heading *The home is cleared before every run* and its text, up to and including **First reset after the upgrade.**, are replaced by one sentence: the dataset's rollback clears the home. The paragraphs after them stay.
      - The sentence "The agent's home is cleared before every run (see ...)" is gone. The agent-files paragraph now says the rollback clears what a run wrote.
      - The login token's paragraph no longer says the fresh home keeps the login or clears `.claude.json`.
      - The rows *The home is fresh* and *The home is reset* are gone from the table of checks.
      - The `FACTORY_OPENCODE_FOLDERS` row is gone from *Configuration*.
      - *Running on opencode* names no fresh home and no `FACTORY_OPENCODE_FOLDERS`.
    - `docs/decisions.md`: the entry "Every agent run and every project command starts from a fresh agent home" gains the closing line "Replaced by the dataset's rollback, v1.2 F0044-S0004."
    - `README.md`: not changed, as the criterion says.

    Cross-read and found current: `README.md`; `docs/project-guide/stages.md`. After the edits, a grep of the README, the operator guide and the project guide finds no `fresh_home`, `agent_home_of`, `home_files`, `FACTORY_OPENCODE_FOLDERS`, `LOGIN_STATE_FILE`, `kept_paths` or `inside_home`. `InstanceSettings.agent_home` and `FACTORY_CLAUDE_HOME` stay documented. The other mentions of `agent_home`, in `watching.md` and `stages.md`, are about that setting or about test helper arguments, not the removed field. I ran no example, because I wrote none that is a command.

    Seen and not touched:
    - `docs/decisions.md` keeps older entries that name `FACTORY_OPENCODE_FOLDERS`, `AgentHome` and `fresh_home` (lines near 760, 866 and 990). They are history, and only the one closing line was asked for.
    - `docs/operator-guide.md`, in the opencode section: "every recreated container has a fresh home" describes the Docker path. It is unrelated to this story and F0044 removes that path later.
    - `docs/project-guide/agents.md` (line 121 in the old file) still describes `LOGIN_STATE_FILE`-free logins only through other paragraphs. I found no remaining reference.

    `check`: check: green (not run again: passed on tree 0040404b5470 at 2026-10-25T13:57:34Z)
    `secrets`: secrets: green (3.5 s)
    `documents`: documents ok
15. factory: started smoke-test as self.
16. smoke-tester: Ran both smoke-test commands from the repository root exactly as written, in order. I changed nothing.

    Command 1 (the import loop over the five removed modules):
    ```
    gone
    gone
    gone
    gone
    gone
    ```
    Met its Expect: each of the five modules prints `gone`.

    Command 2 (the fields of `Boundaries` and `InstanceSettings`):
    ```
    Bytecode compiled 4164 files in 110ms
    False False True
    ```
    Met its Expect: the sixth line is `False False True`. The extra line `Bytecode compiled 4164 files in 110ms` is uv's own message about the environment, on stderr. The loop in command 1 sends stderr to `/dev/null` and this command does not, so it shows up only here. It is not output of the code under test, and I don't count it as a finding.

    Checked against the acceptance criteria: nothing in the smoke test contradicts any of them. Command 1 confirms criterion 1 (the modules are gone). Command 2 confirms the field parts of criterion 2: `Boundaries` has no `agent_home`, and `InstanceSettings` has no `opencode_folders` but still has `agent_home`. That `agent_home` setting is the one criterion 5 keeps. A grep of `src/` also finds no `OPENCODE_FOLDERS`, `fresh_home`, `LOGIN_STATE_FILE` or `agent_home_of`; that is consistent with criteria 2 and 3, though the smoke test did not ask for it. The smoke test does not cover criteria 4, 6, 7 and 8; the stage's tests and checks do.

    Findings: none.
