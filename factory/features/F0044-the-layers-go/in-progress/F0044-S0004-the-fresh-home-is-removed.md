---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 447
comments_read: [6398446445]
handed_over: null
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
