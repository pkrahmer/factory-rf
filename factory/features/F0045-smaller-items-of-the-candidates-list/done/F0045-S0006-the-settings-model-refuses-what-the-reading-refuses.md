---
stage: done
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 471
comments_read: []
handed_over: approval
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T22:19:14.863330Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T22:19:14.869672Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T22:19:36.280313Z'
  stage: intake
  run: b4e4d0e251484311822f38277e51780a
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-26T22:19:56.571494Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-26T22:27:38.545407Z'
  stage: tests
  run: dddd9034c9e145e8b33be684574e4b98
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-26T22:27:58.927108Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-26T22:34:21.909308Z'
  stage: doing
  run: 7e8eb281067247f2a7f9945acdd52e9d
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-26T22:34:42.311546Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-26T22:35:30.120336Z'
  stage: review
  run: 8c396af07c3e4a18b516180cfdbe12f6
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-26T22:35:50.581917Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-26T22:36:04.169511Z'
  stage: doing
  run: 2ecbfc75c2074f1099d76fd871ed502a
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-26T22:36:24.392473Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-26T22:42:21.089385Z'
  stage: tests
  run: f1f4c513c2f0434da68eb5ee16e54c0d
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-26T22:42:42.000921Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-26T22:48:38.727766Z'
  stage: doing
  run: 0feece83ada341e3b247f53417a177ec
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-26T22:48:59.284501Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: result
  at: '2026-10-26T22:49:34.490320Z'
  stage: review
  run: 5095da23abbc4426a0222bf3b6c941c8
- number: 18
  speaker: factory
  kind: started
  at: '2026-10-26T22:49:55.236216Z'
  stage: docs
- number: 19
  speaker: documenter
  kind: result
  at: '2026-10-26T22:50:40.343595Z'
  stage: docs
  run: 152e0176d2ee4ca8b8ca5d9d292631f1
- number: 20
  speaker: factory
  kind: started
  at: '2026-10-26T22:51:00.832022Z'
  stage: smoke-test
- number: 21
  speaker: smoke-tester
  kind: result
  at: '2026-10-26T22:51:30.558371Z'
  stage: smoke-test
  run: ec2d499801674b42a94a3656f1126bb5
- number: 22
  speaker: factory
  kind: done
  at: '2026-10-26T22:53:53.470260Z'
  stage: approval
---

# The settings model refuses what the reading refuses

## Description

`InstanceSettings` is built by `read_settings` for every instance and directly by the suite. Two of its rules hold only in the reading. The field `agent_home` still defaults to `/home/agent/.claude`, the second user's home of v1.1, after S0005 (the agent files' folder and the image identity file are required settings) made `FACTORY_CLAUDE_HOME` required and absolute in `read_settings`; the human chose to remove the model's default too (the answers of 2026-10-25, decision 32 (b) of `feature.md`). And the names of `container_env` (F0046-S0002) are checked only in `read_settings`, so a model built in code accepts `container_env=("HOME",)`, a name the factory sets itself, while `ca_bundle` and `opencode_provider_file` are checked by the model as well (F0046-A0001, note 9). This story moves both rules into the model (decisions 14 and 18): `agent_home` is a required field that must be absolute, and the model checks every name of `container_env` with the reading's rule and the reading's texts. `read_settings` keeps raising `SettingsInvalid` naming its variable for the same faults, before the model is built. What stays: every other field and its default, the reading's faults and their texts, the containers' use of the names.

## Interface

`factory.domain.settings` (`domain`):

- `AGENT_HOME_DEFAULT` goes. `InstanceSettings.agent_home: Path` has no default; it is checked by the same validator as `checkout` and `state_directory`, so a relative path is refused with `is not an absolute path`.
- `InstanceSettings.container_env: tuple[str, ...] = ()` is checked by the model, name by name, in order, with the rule `read_settings` applies to `FACTORY_CONTAINER_ENV`: a name that is not a variable name (`[A-Za-z_][A-Za-z0-9_]*`) is refused with `holds <name>, which is not a variable name`; a name in `RESERVED_CONTAINER_NAMES` or beginning with `RESERVED_CONTAINER_PREFIX` with `holds <name>, which the factory sets itself`; a name given twice with `names <name> twice`. The rule is written once and used by both.
- `read_settings` is unchanged in behaviour: a fault of `FACTORY_CONTAINER_ENV` or `FACTORY_CLAUDE_HOME` raises `SettingsInvalid` naming the variable, never a `ValidationError`.

Tests (the tester writes and changes them; the leave is decision 26 of `feature.md`): new tests at the tester's choice, for example `tests/domain/test_settings_model_rules.py`. Earlier tests: every construction of `InstanceSettings` under `tests/` that gives no `agent_home` (on 2026-10-26 thirty-eight constructions in thirty-three modules, among them the fixtures `local_settings` and `disk_settings` of `tests/conftest.py`, `tests/proof_support.py` and `tests/application/test_checkout_preparer_seal.py`) gains an absolute `agent_home`, a path under `tmp_path` where the test reads the agent files and otherwise one shared constant the tester places in `tests/settings_support.py`; each test keeps its name and its assertions; the tester names each changed module in its entry.

## Acceptance criteria

1. The field is required and absolute (rows of one parametrized test, the model built through a variable typed `type[BaseModel]`, with `repository_url` and `instance` given): without `agent_home` it raises `ValidationError` naming `agent_home`; `agent_home="agents"` raises `ValidationError` holding `is not an absolute path`; `agent_home="/srv/agents"` gives `agent_home == Path("/srv/agents")`.
2. The names of `container_env` in the model (rows of one parametrized test, the model built as in criterion 1 with `agent_home="/srv/agents"`): `()`, `("HTTPS_PROXY",)` and `("HTTPS_PROXY", "NO_PROXY", "_X1")` are accepted and kept in order; `("HOME",)`, `("ANTHROPIC_API_KEY",)` and `("FACTORY_X",)` raise `ValidationError` holding `holds <name>, which the factory sets itself`; `("1A",)` and `("A-B",)` raise it holding `holds <name>, which is not a variable name`; `("A", "A")` raises it holding `names A twice`.
3. The reading names its variable (rows of one parametrized test over `read_settings` of `BASE` of `tests/settings_support.py` with `FACTORY_CONTAINER_ENV` set to `HOME`, `1A` and `A,A`): each raises `SettingsInvalid` (not `ValidationError`) with variable `FACTORY_CONTAINER_ENV` and the fault text of criterion 2 for that name.
4. The old default is gone (rows of one parametrized test): `AGENT_HOME_DEFAULT` is no attribute of `factory.domain.settings`; no module under `src/factory` holds the string `/home/agent`.
5. `make check` stays green.
6. docs: `docs/project-guide/watching.md`, where it lists the fields of `InstanceSettings`: `agent_home` required and absolute, and the model's check of `container_env` with its three faults; `docs/project-guide/README.md`, the line of `tests/settings_support.py` under *Shared test helpers*: the constant the tester added, if any. `docs/decisions.md`: the entry of `FACTORY_CONTAINER_ENV` (F0046-S0002) gains one closing line: "Since v1.2 F0045-S0006 the settings model checks the names too, with the same rule and texts." `docs/operator-guide.md`, `README.md`: none (no setting changes).

## Smoke test

```bash
uv run python - <<'EOF'
from pydantic import ValidationError
from factory.domain import settings
from factory.domain.settings import InstanceSettings
print(hasattr(settings, "AGENT_HOME_DEFAULT"))
for extra in ({}, {"agent_home": "/srv/agents", "container_env": ("HOME",)}, {"agent_home": "/srv/agents"}):
    try:
        print(InstanceSettings(repository_url="/srv/project.git", instance="vm", **extra).agent_home)
    except ValidationError as error:
        first = error.errors()[0]
        print(first["type"], "which the factory sets itself" in first["msg"])
EOF
```
Expect: four lines: `False`; `missing False`; `value_error True`; `/srv/agents`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names `factory.domain.settings`, `AGENT_HOME_DEFAULT` (still at line 49 of `src/factory/domain/settings.py`, the only `/home/agent` under `src/factory`), the field `agent_home: Path` (line 106), the validator that already covers `checkout` and `state_directory`, and the reading's rule at lines 280-297 whose three texts the story quotes. Every behaviour it states has a criterion: required and absolute (1), the three name faults and the accepted order (2), the reading's `SettingsInvalid` (3), the removal (4).
   - Criteria: each is one parametrized test with concrete rows. Both sides are covered: accepted and refused for `agent_home`, and for `container_env` the accepted lists, reserved names, the `FACTORY_` prefix, bad names and a duplicate. Criterion 3 covers the reading, with the variable and fault text per row. Criterion 4 covers the constant and the string. Criteria 5 and 6 close the list, and the docs criterion names its files and the exact closing line.
   - Smoke test: runnable with `uv run python -`, no pytest, so the `-q` rule does not apply. I traced it against the code. `InstanceSettings` with only `repository_url` and `instance` gives `missing` first, whose message lacks the text, so `False`. `HOME` gives `value_error True`. The valid case prints `/srv/agents`. The `Expect:` line gives four lines that can be checked exactly.
   - Architecture: both rules live in `factory.domain`, a pure model with no I/O, and `read_settings` stays in the same module. The story writes the rule once and uses it from both.
   - Scope: within S0006 of `feature.md` (decisions 14 and 18, the human's answer 32 (b)). The leave for the earlier tests is decision 26, which the story cites. It changes no test beyond that leave and has nothing from "Out of scope".
4. factory: started tests as vm.
5. tester: Tests written for every criterion. They are red on purpose: the model still has a default `agent_home` and does not check `container_env`.

   - criterion 1: tests/domain/test_settings_model_rules.py::test_the_settings_model_requires_an_absolute_agent_home (rows: missing, relative, absolute)
   - criterion 2: tests/domain/test_settings_model_rules.py::test_the_settings_model_checks_the_container_env_names (rows: none, one, three, home, api-key, factory-prefix, leading-digit, dash, twice)
   - criterion 3: tests/domain/test_settings_model_rules.py::test_the_reading_names_the_container_env_variable_for_a_refused_name (rows: HOME, 1A, A,A)
   - criterion 4: tests/domain/test_settings_model_rules.py::test_the_old_agent_home_default_is_gone (rows: constant, string; the string row reads every `*.py` under the installed `factory` package)
   - criteria 5 and 6: no test (the check and the docs).

   Files created: `tests/domain/test_settings_model_rules.py`.

   Shared constant: `AGENT_HOME = Path("/srv/factory/factory-1/factory/claude")` in `tests/settings_support.py`. `BASE["FACTORY_CLAUDE_HOME"]` is now `str(AGENT_HOME)`, the same value as before. The module docstring was updated to mention it. The documenter should name this constant under *Shared test helpers* (criterion 6).

   Earlier test modules changed under the Interface's leave (decision 26). Every construction of `InstanceSettings` that gave no `agent_home` now gives one. Every test keeps its name and its assertions.
   - Given `AGENT_HOME` (no test there reads agent files through the settings):
     - tests/conftest.py (fixture `disk_settings`)
     - tests/application/test_container_environment_extra.py
     - tests/application/test_checkout_preparer_seal.py
     - tests/application/test_repository_waiter.py
     - tests/application/test_patient_runs.py
     - tests/application/test_cost_image.py
     - tests/application/test_scheduler.py
     - tests/application/test_tick_disk.py
     - tests/application/test_opencode_item.py
     - tests/application/test_opencode_item_container.py
     - tests/adapters/test_agent_launch_extra.py
     - tests/domain/test_settings_container_env.py
     - tests/domain/test_container_extra_environment.py
     - tests/domain/test_settings.py
     - tests/domain/test_settings_opencode_provider.py
     - tests/domain/test_settings_one_environment.py
     - tests/domain/test_settings_min_free.py
     - tests/domain/test_settings_paths.py (`REQUIRED`)
     - tests/domain/test_settings_stage_environment.py (`_DIRECT_CONTAINER`)
   - tests/application/test_tick_stop_records.py: its `settings` fixture now uses the `agent_home` fixture (`tmp_path / "agent-home"`). That is the path the row `agent-definition-invalid` writes its agent file to.
   - Already gave an `agent_home`, so unchanged: tests/proof_support.py, the `local_settings` fixture in conftest, and the other entry/application modules. My count is therefore below the Interface's 38/33.

   Test run: I ran `make test` once. The last lines show the new rows failing for the right reasons: `DID NOT RAISE ValidationError` for the refused container names, `assert True == False` for the constant, and `settings.py` listed for the `/home/agent` string. That output showed only the last failures, so I did not see whether the earlier rows were also red. Every module imported; nothing failed to import.

   `make lint`: green. The type check was skipped, as this stage allows.

   Open: nothing.

   `lint`: lint: green (0.2 s)
   `test`: FAILED tests/domain/test_settings_model_rules.py::test_the_old_agent_home_default_is_gone[string] - AssertionError: assert [PosixPath('/...settings.py')] == []
6. factory: started doing as vm.
7. coder: Built: `src/factory/domain/settings.py` is the only file changed. `AGENT_HOME_DEFAULT` is removed, so no `/home/agent` string is left under `src/factory`. `InstanceSettings.agent_home: Path` has no default and joins `_absolute`, the same field validator as `checkout` and `state_directory`. A new public pure function, `container_env_fault(names) -> str | None`, holds the names rule in one place. It checks names in order and returns the first fault: `holds <name>, which is not a variable name`, then `holds <name>, which the factory sets itself`, then `names <name> twice`. Both callers use it. The model's `container_env` field validator raises `ValueError(fault)`. `_container_env` in `read_settings` raises `SettingsInvalid(FACTORY_CONTAINER_ENV, fault)` before the model is built, so the reading still names its variable. That replaces the old `_check_container_name` helper and the duplicate check inside the loop.

   Main choice: I followed the module's existing `workspace_overlap_fault` pattern, a pure function that returns the fault text and leaves each caller to wrap it in its own exception. I rejected a helper that raises `SettingsInvalid`, with the model catching it and re-raising a `ValueError`. That would have put exception translation inside a validator for no gain.

   `make check` is green; `make test` took 161.6 s. `make duplicates`: 0 new, 43 known, 0 gone. The story's smoke test prints the expected four lines: `False`, `missing False`, `value_error True`, `/srv/agents`. `InstanceSettings` is not in the records contract, so no schema needed regenerating. Refactor pass: I read the diff and nothing needed changing. The journal did not change the task's meaning, so `## Description` is unchanged.

   Noticed but not touched: nothing outside this story.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 43 known, 0 gone
8. factory: started review as vm.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (`src/factory/domain/settings.py`, the new `tests/domain/test_settings_model_rules.py`, `tests/settings_support.py` and 20 earlier test modules) against the work item.

   Group 1 (acceptance criteria) passes:
   - Criteria 1 to 4 each have one parametrized test whose rows match the criterion. Both sides are covered: missing, relative and absolute `agent_home`; accepted, reserved, prefixed, malformed and repeated container names; and the reading's `SettingsInvalid` with its variable and text. The factory's `make check` after the coder was green (journal entry 7).

   Groups 2 to 4 (`src/`) also pass:
   - The rule is written once, in `container_env_fault`, and both callers use it: the model's validator wraps the fault in `ValueError`, and `read_settings` raises `SettingsInvalid` before the model is built. This follows the existing `workspace_overlap_fault` pattern.
   - `agent_home` joins `_absolute`. `AGENT_HOME_DEFAULT` and the `/home/agent` string are gone from `src/`. `InstanceSettings` is built in only one place under `src/` (`read_settings`), and that call passes `agent_home`.
   - The new comment and docstring say why, not what.

   Findings:
   1. `tests/domain/test_settings_model_rules.py:17-18`: `_SET_BY_FACTORY` and `_NOT_A_NAME` are second copies of the same constants in `tests/domain/test_settings_container_env.py:17-18`. This is round 0, so it sends the item back. Fix: the tester moves both constants to `tests/settings_support.py` under the standing leave to move a shared test helper, and both modules import them from there. Every earlier test keeps its name and its assertions.

   Earlier tests changed (status M):
   - `tests/settings_support.py`: the story's leave (Interface, decision 26 of `feature.md`) to place one shared constant there. `AGENT_HOME` was added and `BASE` keeps the same value.
   - `tests/conftest.py` (`disk_settings`): the story's leave (decision 26), adds `agent_home=AGENT_HOME`.
   - `tests/adapters/test_agent_launch_extra.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_checkout_preparer_seal.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_container_environment_extra.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_cost_image.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_opencode_item.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_opencode_item_container.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_patient_runs.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_repository_waiter.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_scheduler.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_tick_disk.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/application/test_tick_stop_records.py`: the story's leave (decision 26). Its `agent_home` is a path under `tmp_path`, from the existing `agent_home` fixture, where the test reads its agent files.
   - `tests/domain/test_container_extra_environment.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/domain/test_settings.py`: the story's leave (decision 26), adds `agent_home` (and reformats).
   - `tests/domain/test_settings_container_env.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/domain/test_settings_min_free.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/domain/test_settings_one_environment.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/domain/test_settings_opencode_provider.py`: the story's leave (decision 26), adds `agent_home`.
   - `tests/domain/test_settings_paths.py` (`REQUIRED`): the story's leave (decision 26), adds `agent_home`.
   - `tests/domain/test_settings_stage_environment.py` (`_DIRECT_CONTAINER`): the story's leave (decision 26), adds `agent_home`.
10. factory: started doing as vm.
11. coder: Round 1: the reviewer's only finding is a test change, so no code changes. Under the standing leave in `CLAUDE.md` to move a shared test helper, the tester makes this move:

    - **What moves:** the constants `_SET_BY_FACTORY` and `_NOT_A_NAME`.
    - **From:** `tests/domain/test_settings_model_rules.py:17-18` and `tests/domain/test_settings_container_env.py:17-18`, where they are copies of each other.
    - **To:** one shared place, `tests/settings_support.py`.
    - **Then:** both modules import them from there. Every earlier test keeps its name and its assertions.

    `src/factory/domain/settings.py` stays as round 0 left it. Nothing else is open. The journal did not change the task's meaning, so `## Description` is unchanged.
12. factory: started tests as vm.
13. tester: Round 1: I made the test change named in coder entry 11, which settles the reviewer's finding 1 (two copies of the same constants). I did this under the standing leave in `CLAUDE.md` to move a shared test helper. No test was added, renamed or had its assertions changed.

    **What moved:** the two fault texts, `"which is not a variable name"` and `"which the factory sets itself"`. They now live once, as `NOT_A_NAME` and `SET_BY_FACTORY`, in `tests/settings_support.py`. They are public names because two modules import them. I updated that module's docstring to mention them.

    **Earlier test files changed under the leave:**
    - `tests/domain/test_settings_container_env.py` (written by F0046-S0002): its private `_NOT_A_NAME` and `_SET_BY_FACTORY` are gone. It now imports both from `settings_support`, and its parametrize rows use the shared names. Every test keeps its name and its expected texts.

    **This story's test file:**
    - `tests/domain/test_settings_model_rules.py`: the same change, private copies removed and the shared constants imported.

    The criterion → test mapping is unchanged from entry 5:
    - criterion 1: tests/domain/test_settings_model_rules.py::test_the_settings_model_requires_an_absolute_agent_home
    - criterion 2: tests/domain/test_settings_model_rules.py::test_the_settings_model_checks_the_container_env_names
    - criterion 3: tests/domain/test_settings_model_rules.py::test_the_reading_names_the_container_env_variable_for_a_refused_name
    - criterion 4: tests/domain/test_settings_model_rules.py::test_the_old_agent_home_default_is_gone

    **For the documenter (criterion 6):** the *Shared test helpers* line for `tests/settings_support.py` should now name `AGENT_HOME`, `NOT_A_NAME` and `SET_BY_FACTORY`.

    **Files created:** none. **Modules the test run could not import:** none.

    **Checks:** `make test` passed once (`test: green (161.6 s)`; the code already exists from round 0). `make lint` is green. I skipped the type check, as this stage allows.

    **Open:** nothing.

    `lint`: lint: green (0.2 s)
    `test`: test: green (161.5 s)
14. factory: started doing as vm.
15. coder: Round 1: no code change. The reviewer's only finding was that two test constants had been copied between test files. The tester settled it in entry 13: `NOT_A_NAME` and `SET_BY_FACTORY` moved to `tests/settings_support.py`, and `tests/domain/test_settings_container_env.py` and `tests/domain/test_settings_model_rules.py` now import them from there. The code is as round 0 left it, all in `src/factory/domain/settings.py`:
    - `AGENT_HOME_DEFAULT` is removed.
    - `agent_home` is required, and the same check as `checkout` and `state_directory` (`_absolute`) refuses a relative path.
    - One pure function, `container_env_fault`, holds the rule for container variable names. The model's validator and `read_settings` both use it.

    Main choice, from round 0: the rule is a function that returns the fault text, and each caller raises its own exception. This follows the module's existing `workspace_overlap_fault`. I rejected a helper that raises `SettingsInvalid` and has the model translate it into a `ValueError`.

    `make check` is green on this round's committed state (`test: green (161.3 s)`, `check: green`). Refactor pass: there is no new diff in this round, so nothing to change. The journal did not change the task's meaning, so `## Description` is unchanged.

    Noticed but not touched: nothing.

    `check`: check: green
    `duplicates`: duplicates: 0 new, 43 known, 0 gone
16. factory: started review as vm.
17. reviewer: Round 1 review. I read `git diff main...HEAD -- . ':!factory'` against the work item: `src/factory/domain/settings.py`, the new `tests/domain/test_settings_model_rules.py`, `tests/settings_support.py` and 20 earlier test modules.

    no findings

    - Group 1 (acceptance criteria) passes:
      - Criteria 1 to 4 each have one parametrized test, and its rows match the criterion exactly.
      - Criterion 1: missing, relative and absolute `agent_home`, built through `type[BaseModel]`.
      - Criterion 2: the accepted lists are kept in order. The refused names are reserved (`HOME`, `ANTHROPIC_API_KEY`), prefixed (`FACTORY_X`), not names (`1A`, `A-B`) or repeated (`A,A`), each with its text.
      - Criterion 3: the reading's `SettingsInvalid`, its variable and its exact fault text.
      - Criterion 4: the constant and the `/home/agent` string.
      - The factory's `make check` after the coder was green (entry 15).
    - Group 2 (architecture) passes. The rule is written once, in the pure domain function `container_env_fault`, which returns the fault text. The model's validator wraps it in `ValueError`; `read_settings` raises `SettingsInvalid(FACTORY_CONTAINER_ENV, …)` before the model is built. This follows the existing `workspace_overlap_fault`. The order of the checks and the skipping of blank parts are unchanged from the old `_container_env`.
    - Group 3 (security) passes: no markers added and no new baseline entry.
    - Group 4 (quality) passes:
      - `agent_home` now goes through `_absolute`.
      - `AGENT_HOME_DEFAULT` and the old `_check_container_name` are gone, and nothing dead is left.
      - The new comment says why, and `container_env_fault` has its docstring.
    - Group 5 (work item hygiene) passes. The journal gives the main choice and the option the coder rejected. The Description matches what was built. On the docs criterion: tester entry 13 names all three constants for the *Shared test helpers* line (`AGENT_HOME`, `NOT_A_NAME`, `SET_BY_FACTORY`), while criterion 6 still says "the constant the tester added". I don't count that as a finding, because entry 13 tells the documenter.
    - Round 0 finding 1 (the copied constants) is settled. `NOT_A_NAME` and `SET_BY_FACTORY` now live once in `tests/settings_support.py`, and both modules import them from there.

    Earlier tests changed (status M):
    - `tests/settings_support.py`: the story's leave (decision 26) for the shared `AGENT_HOME`, and `BASE` keeps the same value. Plus the standing leave to move a shared test helper for `NOT_A_NAME` and `SET_BY_FACTORY`.
    - `tests/domain/test_settings_container_env.py`: the standing leave to move a shared test helper (its private `_NOT_A_NAME` and `_SET_BY_FACTORY` are now imported from `settings_support`, with the same texts and names), and decision 26 (adds `agent_home`).
    - `tests/conftest.py` (`disk_settings`): decision 26, adds `agent_home`.
    - `tests/application/test_tick_stop_records.py`: decision 26. Its `agent_home` is the existing `tmp_path` fixture, where the test reads its agent files.
    - These modules only add `agent_home=AGENT_HOME` to their settings, under decision 26:
      - `tests/adapters/test_agent_launch_extra.py`
      - `tests/application/test_checkout_preparer_seal.py`
      - `tests/application/test_container_environment_extra.py`
      - `tests/application/test_cost_image.py`
      - `tests/application/test_opencode_item.py`
      - `tests/application/test_opencode_item_container.py`
      - `tests/application/test_patient_runs.py`
      - `tests/application/test_repository_waiter.py`
      - `tests/application/test_scheduler.py`
      - `tests/application/test_tick_disk.py`
      - `tests/domain/test_container_extra_environment.py`
      - `tests/domain/test_settings.py`
      - `tests/domain/test_settings_min_free.py`
      - `tests/domain/test_settings_one_environment.py`
      - `tests/domain/test_settings_opencode_provider.py`
      - `tests/domain/test_settings_paths.py` (`REQUIRED`)
      - `tests/domain/test_settings_stage_environment.py`
18. factory: started docs as vm.
19. documenter: Docs for F0045-S0006. I changed only documents, so I did not run `make check`. The factory's checks run right after this stage.

    Files changed:
    - `docs/project-guide/watching.md`: I replaced the sentence that said `agent_home` still carries `AGENT_HOME_DEFAULT`. It is now stale: the default is gone. The new text says the model refuses the same faults as the reading. `agent_home` is required and absolute. `container_env` is checked by `container_env_fault` with its three faults. The reading raises `SettingsInvalid` and a model built in code raises `ValidationError`.
    - `docs/project-guide/README.md`: the `settings_support.py` line under *Shared test helpers* now names `AGENT_HOME`, `NOT_A_NAME` and `SET_BY_FACTORY`, as tester entry 13 says. Criterion 6 only says "the constant the tester added".
    - `docs/decisions.md`: I added the closing line to the `FACTORY_CONTAINER_ENV` entry (F0046-S0002), word for word as criterion 6 gives it.

    Cross-read and found current against the diff:
    - `docs/operator-guide.md`: the `FACTORY_CONTAINER_ENV` rows and the `FACTORY_CLAUDE_HOME` text still describe the reading's behaviour, which is unchanged. Criterion 6 says to leave `operator-guide.md` and `README.md` alone.
    - `docs/project-guide/stage-environment.md` and `docs/project-guide/agents.md`: they mention the container environment extras and the agent home only through the reading, which is unchanged.

    No code finding. Smoke test and code match the Interface (round 1 reviewer: no findings).

    Stale text I noticed but did not touch: none that belongs to this story. The remaining `/home/agent` mentions in `docs/decisions.md` (lines 442, 534, 729, 926) are dated decision entries about the image, not the settings model, so they are history and not mine to edit.

    `check`: check: green (not run again: passed on tree efbdc90fd7e6 at 2026-10-26T22:45:46Z)
    `secrets`: secrets: green (1.6 s)
    `documents`: documents ok
20. factory: started smoke-test as vm.
21. smoke-tester: Ran the smoke test once from the repository root, as written. I fixed nothing.

    Command 1 (the `uv run python - <<'EOF' … EOF` script under `## Smoke test`), exit status 0:

    ```
    Bytecode compiled 4164 files in 57ms
    False
    missing False
    value_error True
    /srv/agents
    ```

    Expect: four lines: `False`; `missing False`; `value_error True`; `/srv/agents`. **Met.** The first line is uv's bytecode notice, not output of the script. The script's four lines match the expectation in order:
    - `AGENT_HOME_DEFAULT` is gone.
    - Leaving out `agent_home` fails with type `missing`.
    - `container_env=("HOME",)` fails with a value error holding "which the factory sets itself".
    - `agent_home="/srv/agents"` is kept.

    Against the acceptance criteria: nothing the smoke test showed contradicts any of them. I also ran one check outside the smoke test, for criterion 4: `grep -rn "/home/agent" src/factory` finds nothing. The smoke test does not exercise criteria 2 (beyond `HOME`), 3, 5 and 6; it contradicts none of them. `make check` is the factory's gate after this stage.

    Findings: none.
22. factory: done (pull request merged); cost: 10 runs, 17.4 min, 76 turns, 268330 tokens in (2007867 more from cache), 31941 out, $2.89
