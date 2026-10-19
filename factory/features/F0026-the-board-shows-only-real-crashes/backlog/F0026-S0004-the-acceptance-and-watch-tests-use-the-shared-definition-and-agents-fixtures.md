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

## Acceptance criteria

1. Under `tests/`, only `tests/conftest.py` defines a fixture `definition(boundaries: Boundaries)`. The eleven modules' tests pass with the same test ids as before the change.
2. Under `tests/`, only `tests/conftest.py` defines `installed_agents`, and no module defines `_agents(agent_home: Path, boundaries: Boundaries)`. The seven modules' tests pass with the same test ids as before the change.
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
