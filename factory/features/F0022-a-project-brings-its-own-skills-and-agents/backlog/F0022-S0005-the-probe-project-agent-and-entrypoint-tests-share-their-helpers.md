# The probe, project agent and entrypoint tests share their helpers

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0022's reviewers noted three copied test helpers that nobody moved (S0001's entry 13, S0002's entry 17), and the acceptance found a fourth copy of the same kind. (1) `ENVIRONMENT`, the agent environment of the probe tests, is written four times: in `tests/application/test_agent_run_probe.py`, `test_agent_run_probe_project_agent.py`, `test_agent_run_probe_login.py` and `test_agent_run_probe_opencode.py`. `COMPLETED` is written twice, in the first two of those. The `settings` fixture, the agent-user settings with `pinned_agent_version="fake"`, is written three times with the same body, in the first three. (2) `PROJECT_CODER = AGENT_FILE.replace("Do the work.", "The project's coder.")` is written twice, in `tests/application/test_agent_run_probe_project_agent.py` and `tests/entry/test_wiring_project_agents.py`. (3) The entrypoint's `layout` fixture (`Layout(tmp_path)` of `tests/test_entrypoint.py`) is written three times: in `tests/test_entrypoint.py`, `tests/test_agent_home_ownership.py` and `tests/test_entrypoint_skills.py`. It shadows the other `layout` fixture of `tests/conftest.py`, which builds the confinement's layout. A fifth copy would be the next reviewer's finding. This story moves each helper to one shared place under the standing leave of `CLAUDE.md` (*Tests*). Every earlier test keeps its name and checks the same thing. It changes no code. The `PROJECT_CODER` of `tests/application/test_project_agents.py` is another text (model `opus`, tools `[Read]`) and stays where it is.

## Interface

No module under `src/factory/` changes.

Tests (the tester makes the moves, under the standing leave):

- `tests/probe_support.py` (new): `ENVIRONMENT` and `COMPLETED`, each exactly as `tests/application/test_agent_run_probe.py` holds it today. The four probe modules import `ENVIRONMENT` from it, and the two that hold `COMPLETED` import that too. None keeps its own copy.
- `tests/conftest.py`: a fixture `probe_settings(agent_home, tmp_path)` with the body of today's `settings` fixture of `tests/application/test_agent_run_probe.py`. In `test_agent_run_probe.py`, `test_agent_run_probe_project_agent.py` and `test_agent_run_probe_login.py`, the local `settings` fixture goes and the tests take `probe_settings`. The `settings` fixture of `test_agent_run_probe_opencode.py` is another one (it installs an agent and sets login files) and stays.
- `tests/git_support.py`: `PROJECT_CODER`, as written today in `tests/entry/test_wiring_project_agents.py`. The two modules that hold that text import it.
- `tests/conftest.py`: a fixture `image_layout(tmp_path)` that returns `Layout(tmp_path)` of `tests/test_entrypoint.py`. The three local `layout` fixtures go, and the tests that used them take `image_layout`. The conftest's `layout` fixture stays as it is.
- The tester's entry names each earlier test file it changed.

## Acceptance criteria

1. Every test function of the eight changed test modules (`tests/application/test_agent_run_probe.py`, `test_agent_run_probe_project_agent.py`, `test_agent_run_probe_login.py`, `test_agent_run_probe_opencode.py`, `tests/entry/test_wiring_project_agents.py`, `tests/test_entrypoint.py`, `tests/test_agent_home_ownership.py` and `tests/test_entrypoint_skills.py`) keeps its name and its parametrize ids. `pytest --collect-only -q` lists the same test ids before and after the change.
2. Under `tests/`, `ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin"` is assigned in exactly one module (`tests/probe_support.py`), and `COMPLETED = AgentRunResult(` with `entry="probe"` in exactly one. `PROJECT_CODER = AGENT_FILE.replace(` is assigned in exactly one (`tests/git_support.py`). `return Layout(tmp_path)` is written in exactly one (`tests/conftest.py`).
3. `make check` stays green.
4. docs: none. No behaviour and no document changes; the project guide does not name test helpers of these modules.

## Smoke test

```bash
grep -rlF 'ENVIRONMENT = {"PATH": "/opt/factory/bin:/usr/bin"' tests | wc -l
```
Expect: `1`

```bash
grep -rlF 'PROJECT_CODER = AGENT_FILE.replace(' tests | wc -l; grep -rlF 'return Layout(tmp_path)' tests | wc -l
```
Expect: `1`, then `1`

```bash
uv run pytest -q tests/application/test_agent_run_probe.py tests/application/test_agent_run_probe_project_agent.py tests/application/test_agent_run_probe_login.py tests/entry/test_wiring_project_agents.py tests/test_entrypoint_skills.py 2>&1 | tail -1 | grep -c ' passed'
```
Expect: `1`

## Journal

