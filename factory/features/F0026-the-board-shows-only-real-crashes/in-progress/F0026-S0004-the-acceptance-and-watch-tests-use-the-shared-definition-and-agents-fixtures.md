---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 274
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-19T17:37:35.084294Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T17:28:06.004141Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T17:28:06.011389Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T17:28:29.901086Z'
  stage: intake
  run: 074f839f876a4f1bb54b687fc284e833
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T17:28:50.747992Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T17:31:41.105396Z'
  stage: tests
  run: 71d5025f285148f8a8bf8b062e8ad2f9
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T17:32:02.368822Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T17:34:01.224702Z'
  stage: doing
  run: 6a3127ead1384c5eab424cee64f3a1e4
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T17:34:22.744759Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T17:35:29.324266Z'
  stage: review
  run: 14caa561044b445c9c0443a35f5247b5
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T17:35:49.854421Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-19T17:37:14.313026Z'
  stage: docs
  run: b0206ba3c4ce4d4b9e919b4cec48cf83
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T17:37:35.084294Z'
  stage: smoke-test
---

# The acceptance and watch tests use the shared definition and agents fixtures

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0026-S0001 moved the `definition` fixture (the test remote's pipeline definition) to `tests/conftest.py`, but eleven earlier test modules still define their own word-for-word copy, which shadows the shared one. The fixture that installs a valid agent file for every role of the test remote's definition exists seven times: as the autouse `_agents` in `tests/entry/test_watch.py`, `tests/entry/test_watch_acceptance.py`, `tests/entry/test_watch_own_claim.py`, `tests/application/test_tick.py`, `tests/application/test_tick_disk.py` and `tests/application/test_tick_stop_records.py`, and as `installed_agents` with `pytestmark` in `tests/application/test_pipeline_loading_agents.py`. The next story that needs either one copies it again, which the reviewer counts as a finding. This story moves both to `tests/conftest.py`, under the standing leave of `CLAUDE.md` (*Tests*) to move a shared test helper, so the tester makes the change. No code changes. Every earlier test keeps its name and checks the same thing. The complete-feature pushes of the acceptance tests vary in title, stories and parameters, so they are not copies of `watch_support.push_complete`, and they stay.

## Interface

No module under `src/factory/` changes.

`tests/conftest.py` gains, beside `definition`:

```python
@pytest.fixture
def installed_agents(boundaries: Boundaries, agent_home: Path) -> None:
    """Install a valid agent file for every role of the remote's definition."""
```

- `installed_agents` is not autouse: a module that needs the agent files says so with `pytestmark = pytest.mark.usefixtures("installed_agents")`.

Changed under the standing leave to move a shared test helper, by the tester only. In each module nothing else changes, and every test keeps its name and what it checks:
- the `definition` fixture is removed from `tests/application/test_acceptance_closed.py`, `test_acceptance_reading.py`, `test_task_acceptance.py`, `test_stage_run_acceptance.py`, `test_acceptance_repeated.py`, `test_acceptance_snapshots.py`, `test_acceptance_hand_over.py`, `test_acceptance_service.py`, `test_acceptance_due_handler.py`, `test_acceptance_merged.py` and `test_acceptance_merged_before_approval.py`, which then use the one in `tests/conftest.py`, along with any import that only it used;
- the autouse `_agents` fixture is removed from the six modules named in the Description, which gain `pytestmark = pytest.mark.usefixtures("installed_agents")`, and the `installed_agents` fixture is removed from `tests/application/test_pipeline_loading_agents.py`, whose `pytestmark` stays.

Tests (the tester writes them): `tests/test_shared_fixtures.py` (new), the two searches of criteria 1 and 2. Every test of the eighteen changed modules keeps its name and id.

## Acceptance criteria

1. A test that reads every `.py` file under `tests/` finds `def definition(boundaries: Boundaries)` only in `tests/conftest.py`.
2. A test that reads every `.py` file under `tests/` finds `def installed_agents(` only in `tests/conftest.py`, and `def _agents(agent_home: Path, boundaries: Boundaries)` in no file.
3. `make check` stays green.
4. docs: none. No document names these fixtures; `docs/project-guide/stages.md` names `install_agents` in `tests/git_support.py`, which stays.

## Smoke test

```bash
grep -rln "^def definition(boundaries: Boundaries)" tests | sort
grep -rln "^def _agents(agent_home: Path, boundaries: Boundaries)\|^def installed_agents(" tests | sort
uv run pytest -q -p no:cacheprovider --no-cov -n 4 tests/application/test_acceptance_*.py tests/application/test_task_acceptance.py tests/application/test_stage_run_acceptance.py tests/application/test_tick.py tests/application/test_tick_disk.py tests/application/test_tick_stop_records.py tests/application/test_pipeline_loading_agents.py tests/entry/test_watch*.py > /dev/null; echo "pytest exit $?"
```
Expect: three lines, `tests/conftest.py`, `tests/conftest.py` and `pytest exit 0`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: no `src/` change. `tests/conftest.py` gains `installed_agents(boundaries: Boundaries, agent_home: Path) -> None`, not autouse. Its `boundaries` and `agent_home` fixtures exist (conftest lines 156 and 111). The eleven acceptance modules, six `_agents` modules and `test_pipeline_loading_agents.py` match the grep: each holds the copy the story names. `definition` is already in conftest (line 187). The two other hits are unrelated and the story leaves them out: `tests/adapters/test_agent_files.py::_agents(agent_home)` has a different signature, and `tests/domain/test_decision_rules.py::definition()` takes no `boundaries`.
   Criteria: 1 and 2 are each testable by one search test over `tests/**/*.py`. Both sides are covered, since each criterion requires a single definition site and the absence of the old `_agents`. Criteria 3 and 4 are the closing ones. This is a refactor with no new behaviour, so no rule lacks a failing-side criterion.
   Smoke test: the two greps and the pytest line are runnable. The `Expect:` line is checkable: `tests/conftest.py`, `tests/conftest.py`, `pytest exit 0`.
   Architecture: tests only, moved to the shared `tests/conftest.py` under the standing leave in CLAUDE.md (*Tests*). The tester makes the move, and the story names every changed module. No layer or `src/` change.
   Scope: the feature.md Scope names only S0001's files. This story comes from the acceptance reviewer's proposal (R13) and touches only tests, and it stays out of the feature's Out-of-scope items. It changes no test of `test_watcher_move_rule.py`. The edits to other stories' modules are limited to the standing leave (removing duplicate fixtures, with test names unchanged).
4. factory: started tests as self.
5. tester: Wrote the two search tests and made the fixture move myself, as the story assigns it to the tester under the standing leave in `CLAUDE.md` (*Tests*). No change under `src/`.

   Criterion → test:
   - criterion 1: tests/test_shared_fixtures.py::test_the_definition_fixture_is_defined_only_in_conftest
   - criterion 2: tests/test_shared_fixtures.py::test_the_agents_fixture_is_defined_only_in_conftest (both parts: `def installed_agents(` only in conftest, and `def _agents(agent_home: Path, boundaries: Boundaries)` in no file)
   - criteria 3 and 4: the closing ones. They need no test.

   The tests match each signature only at the start of a line (column 0). Otherwise they would find their own string literals in `tests/test_shared_fixtures.py`.

   Files created: `tests/test_shared_fixtures.py`.

   Files changed under the standing leave:
   - `tests/conftest.py`: gains `installed_agents(boundaries, agent_home) -> None`, not autouse, beside `definition`. It also imports `install_agents` from `git_support`.
   - The `definition` fixture is removed from these eleven files under `tests/application/`: `test_acceptance_closed.py`, `test_acceptance_due_handler.py`, `test_acceptance_hand_over.py`, `test_acceptance_merged.py`, `test_acceptance_merged_before_approval.py`, `test_acceptance_reading.py`, `test_acceptance_repeated.py`, `test_acceptance_service.py`, `test_acceptance_snapshots.py`, `test_stage_run_acceptance.py` and `test_task_acceptance.py`.
   - The autouse `_agents` fixture is replaced by `pytestmark = pytest.mark.usefixtures("installed_agents")` in `tests/application/test_tick.py`, `test_tick_disk.py`, `test_tick_stop_records.py`, `tests/entry/test_watch.py`, `test_watch_acceptance.py` and `test_watch_own_claim.py`. None of these modules had a `pytestmark` before.
   - `tests/application/test_pipeline_loading_agents.py`: its `installed_agents` fixture is removed and its `pytestmark` stays.
   - `ruff --select F401 --fix` removed the imports that only the removed fixtures used: `PIPELINE_YAML`, `install_agents` and `Path` where unused. Nothing else changed: every test keeps its name and what it checks.

   Run: `make test` once, after the move: `test: green (48.6 s)`. The new tests do not fail first: this story's change is the move itself, which the tester makes, so they pass once it is done. No module failed to import. `make lint` is green after shortening the new module's docstring line (E501). I skipped `make types` as the stage says. All the edits remove code, apart from the new fixture, which has the same signature as the one it replaces.

   Open: none. The coder has no code to write; `make check` for the whole suite is still to be run by the coder.

   `lint`: lint: green (0.0 s)
   `test`: test: green (44.1 s)
6. factory: started doing as self.
7. coder: Built nothing: the story changes no code under `src/factory/`, and the tester already moved the fixtures (`tests/conftest.py`: `installed_agents` beside `definition`; the copies removed from the eleven acceptance modules, the six `_agents` modules and `tests/application/test_pipeline_loading_agents.py`; the new searches in `tests/test_shared_fixtures.py`). I ran `make check` on the committed state and it passed: `test: green (44.2 s)`, coverage 99.07 %, `check: green`.

   Main choice: I left the working tree as it was. I did not touch the tester's move, for example to tidy imports in the changed test modules, because the coder never edits tests (R9). The tester owns that change.

   Refactor: there is no coder diff, so there was nothing to refactor. Description: no journal entry changed the task's meaning, so it stays as written.

   Noticed but not touched: nothing.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
   `mutants`: mutants: no module under src/factory changed by F0026-S0004
8. factory: started review as self.
9. reviewer: no findings

   What I checked:
   - Criterion 1 is tested by `tests/test_shared_fixtures.py::test_the_definition_fixture_is_defined_only_in_conftest`. It searches every `.py` file under `tests/` for the signature at column 0 and expects `conftest.py` only.
   - Criterion 2 is tested by `tests/test_shared_fixtures.py::test_the_agents_fixture_is_defined_only_in_conftest`. It covers both parts: `def installed_agents(` only in conftest, and the old `_agents(agent_home: Path, boundaries: Boundaries)` nowhere. `tests/adapters/test_agent_files.py::_agents(agent_home)` has a different signature, so the search correctly leaves it out.
   - The two tests check two different criteria, not two sides of one rule, so they don't need to be one parametrized test.
   - The coder's `make check` was green (entry 7).
   - No `src/` change, so no architecture, security or mutant question arises.
   - Every removed `definition` copy had the same body as the one in `tests/conftest.py` (`boundaries.pipeline_reader.parse(PIPELINE_YAML)`); only the docstrings differed.
   - Every removed `_agents` and `installed_agents` copy had the same body as the new shared `installed_agents`.
   - Swapping autouse for `pytest.mark.usefixtures` still installs the agent files before each test's argument fixtures.
   - The only imports dropped are those that only the removed fixtures used.
   - The `## Description` and Interface match what was built.
   - Criterion 4, `docs: none`, still holds: `docs/project-guide/stages.md:123` names `install_agents` in `tests/git_support.py`, which stays.

   Earlier tests (all under the standing leave to move a shared test helper; each test keeps its name and what it checks):
   - tests/conftest.py: gains the shared `installed_agents` fixture, the place it was moved to.
   - tests/application/test_acceptance_closed.py: copy of `definition` removed.
   - tests/application/test_acceptance_due_handler.py: copy of `definition` removed.
   - tests/application/test_acceptance_hand_over.py: copy of `definition` removed.
   - tests/application/test_acceptance_merged.py: copy of `definition` removed.
   - tests/application/test_acceptance_merged_before_approval.py: copy of `definition` removed.
   - tests/application/test_acceptance_reading.py: copy of `definition` removed.
   - tests/application/test_acceptance_repeated.py: copy of `definition` removed.
   - tests/application/test_acceptance_service.py: copy of `definition` removed.
   - tests/application/test_acceptance_snapshots.py: copy of `definition` removed.
   - tests/application/test_stage_run_acceptance.py: copy of `definition` removed.
   - tests/application/test_task_acceptance.py: copy of `definition` removed.
   - tests/application/test_pipeline_loading_agents.py: copy of `installed_agents` removed; its `pytestmark` stays.
   - tests/application/test_tick.py: autouse `_agents` replaced by `pytestmark = pytest.mark.usefixtures("installed_agents")`.
   - tests/application/test_tick_disk.py: autouse `_agents` replaced by the `installed_agents` `pytestmark`.
   - tests/application/test_tick_stop_records.py: autouse `_agents` replaced by the `installed_agents` `pytestmark`.
   - tests/entry/test_watch.py: autouse `_agents` replaced by the `installed_agents` `pytestmark`.
   - tests/entry/test_watch_acceptance.py: autouse `_agents` replaced by the `installed_agents` `pytestmark`.
   - tests/entry/test_watch_own_claim.py: autouse `_agents` replaced by the `installed_agents` `pytestmark`.

   Notes:
   - The coder's `make duplicates` reported `5 new` (entry 7). This branch changes nothing under `src/factory`, so those findings are not this diff's. They are worth a look at the feature's acceptance.
   - `mutants`: no module under `src/factory` changed, so there was no report to read.
10. factory: started docs as self.
11. documenter: Docs: none, as the criterion says. I changed no file.

    Cross-read: I read the story and the diff, which touches only `tests/` and nothing under `src/factory/`. I then searched the README and `docs/` for the moved fixtures (`definition`, `_agents`, `installed_agents`). No document names them. `docs/project-guide/stages.md:123` names `install_agents` in `tests/git_support.py`, which stays, so it is current. `docs/project-guide/git-and-hosting.md:195` (the test remote and its helpers) is also unaffected.

    Findings: none. The code matches the Interface.

    Stale text I noticed but did not touch: none.

    I ran no `make check`, because I changed no file.

    `check`: check: green
    `secrets`: secrets: green (0.6 s)
    `documents`: documents ok
12. factory: started smoke-test as self.
