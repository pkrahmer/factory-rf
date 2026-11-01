---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 494
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-01T13:56:45.159335Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-01T13:56:45.165562Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-01T13:57:04.852436Z'
  stage: intake
  run: 2219ab4fc2e24c62923c5962f3f5328e
---

# The agent runtimes share one state-directory helper, and a failed write is tested
<!-- proposed by feature acceptance of 2026-11-01; refine before starting -->

## Description

S0010 gave `OpencodeRuntime` a `_make_state_directory` that copies `ClaudeCodeRuntime._make_state_directory`: `mkdir(parents=True, exist_ok=True)`, and an `OSError` becomes `state_directory_error`. `CLAUDE.md` puts what the runtimes share in `factory.adapters.agent_launch`, and `state_directory_error` already lives there. S0010 also changed the earlier test row `state-missing` into `state-a-file`, which now fails at the `mkdir`. So the `OSError` branch of `OpencodeRuntime._write_files` (`src/factory/adapters/opencode_runtime.py:625-626`) has no test any more, and the same branch of `ClaudeCodeRuntime._write_files` (`src/factory/adapters/claude_runtime.py:422-423`) had none before. A full disk or a state folder the factory's user cannot write still reaches those lines. This story moves the `mkdir` into one helper in `agent_launch`, which both runtimes call. It also tests, for both runtimes, a state directory that exists but cannot be written. Unchanged: every message and every `AgentRuntimeError` detail, the order of the `mkdir` before the run files' `try`/`finally` (S0010's reason: the cleanup would otherwise hide the error), the runtimes' `_write_files`, and every earlier test. Left to a later story: a shared helper for the write itself, because the two runtimes write different files.

## Interface

`factory.adapters.agent_launch` (adapters):

```python
def make_state_directory(state_directory: Path) -> None:
    """Make `state_directory` with its parents; an `OSError` is `state_directory_error`."""
```

- A missing `state_directory` is made, with its missing parents.
- An existing directory is left as it is, and so are the files in it.
- An `OSError` of the `mkdir` (a file where the folder should be, a parent that cannot be written) raises `state_directory_error(state_directory, error)`, from the `OSError`: an `AgentRuntimeError` whose detail starts `cannot write the state directory <state_directory>: `.

`factory.adapters.claude_runtime` and `factory.adapters.opencode_runtime` (adapters): each runtime's `_make_state_directory` is removed, and `run` calls `make_state_directory(self._state_directory)` at the place where it called the method. Nothing else in either module changes.

Tests (the tester writes them):

- `tests/adapters/test_agent_launch_state_directory.py`, for the helper;
- `tests/adapters/test_runtime_state_directory_write.py`, for both runtimes through their existing stand-ins (`tests/adapters/claude_stand_in.py`, `tests/adapters/opencode_stand_in.py`).

To make the write fail after the `mkdir` succeeds, the test gives a state directory that exists with mode `0o500`. It is skipped when the test runs with root's file rights, as `tests/application/test_tick_stop_records.py` does. `tests/adapters/test_opencode_runtime.py`, `tests/adapters/test_opencode_runtime_runs_folder.py` and the Claude Code runtime's tests pass unchanged.

Two notes of S0004's review, folded in by the human (2026-11-01), each under the human's leave over the named test and nothing else in its file:

- `tests/adapters/test_oauth_token.py`, the row `incomplete-read`: its expected detail is written out as a literal (what `fetch` gives for `http.client.IncompleteRead(b"")`), not computed with the code's own expression `str(CUT_SHORT) or type(CUT_SHORT).__name__`.
- `tests/test_hosting_search.py`: `SECOND` and `SECOND_CLIENT` are renamed to names that say what they hold (for example `ANOTHER_URLLIB_IMPORTER` and `ANOTHER_HTTP_CLIENT_IMPORTER`); the rows keep their ids and what they check.

## Acceptance criteria

1. `make_state_directory`, rows of one test:
   - `<tmp>/a/runs` with neither folder present is made, `a` included;
   - an existing `<tmp>/runs` that holds `keep.txt` is left with `keep.txt` and its text;
   - `<tmp>/state` that is a file raises `AgentRuntimeError` whose detail starts `cannot write the state directory <tmp>/state: `, and the file keeps its text.
2. A run of each runtime (rows `claude` and `opencode` of one test) whose state directory exists with mode `0o500` raises `AgentRuntimeError` whose detail starts `cannot write the state directory <state>: `. The stand-in runtime is never called, and the state directory holds no file afterwards. The rows are skipped with root's file rights.
3. A run of each runtime (rows `claude` and `opencode`) whose state directory is missing makes it and completes with `end_reason` `completed`, as before.
4. The row `incomplete-read` of `tests/adapters/test_oauth_token.py` states its expected detail as a literal; `tests/test_hosting_search.py` holds no name `SECOND` or `SECOND_CLIENT`, and its rows keep their ids.
5. `make check` stays green.
6. docs: `docs/project-guide/agents.md`, under the two runtimes: the state directory is made by `agent_launch.make_state_directory`, which both call before they write a run's files. `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, because no behaviour an operator sees changes.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT; touch "$d/state"; uv run python -c "
import sys
from pathlib import Path
from factory.adapters.agent_launch import make_state_directory
from factory.domain.errors import AgentRuntimeError
root = Path(sys.argv[1])
make_state_directory(root / 'a' / 'runs')
print((root / 'a' / 'runs').is_dir())
try:
    make_state_directory(root / 'state')
except AgentRuntimeError as error:
    print(error.detail.startswith(f'cannot write the state directory {root}/state: '))
" "$d"
```
Expect: two lines, `True` and `True`.

```bash
uv run pytest tests/adapters/test_agent_launch_state_directory.py tests/adapters/test_runtime_state_directory_write.py 2>&1 | tail -1
```
Expect: one line that contains `passed` and contains neither `failed` nor `error`.

## Journal

1. 2026-11-01 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: `agent_launch.make_state_directory(state_directory: Path) -> None` is concrete. It sits next to the existing `state_directory_error` (agent_launch.py:319), and its three rules are stated: a missing directory is made with its parents, an existing one is left alone, and an OSError becomes the detail starting `cannot write the state directory <dir>: `. The runtimes' two `_make_state_directory` methods are removed and `run` calls the helper in their place. The two test notes name their files and the rows or names they change.
   - Criteria: each is testable by one test function. Criterion 1 has the passing rows (missing parent, existing folder with its file) and the failing row (a file where the folder should be, whose text is kept). Criterion 2 is the failing side for both runtimes: mode 0o500, the stand-in never called, no file left, skipped as root. Criterion 3 is the passing side for both runtimes. Criterion 4 covers both test notes, each under the human's leave. Criterion 5 is `make check` and criterion 6 is `docs:`, last. One small gap, not worth a question: the Interface says the error is raised "from the OSError", and no criterion tests the cause. The detail text is tested, which is what matters.
   - Smoke test: the first block is runnable. It makes `a/runs`, prints True, then the file case prints True, so two lines as the `Expect:` says. The second block runs pytest without `-q`, and `pyproject.toml` `addopts` already sets `-q`, so `tail -1` gives the summary line with `passed`. Both `Expect:` lines can be checked against the output.
   - Architecture: the helper goes in `factory.adapters.agent_launch`, where CLAUDE.md puts what the runtimes share, and both runtimes already import from that module. This removes a duplicate helper and adds no layer or dependency. The changes to `tests/adapters/test_oauth_token.py` and `tests/test_hosting_search.py` have the human's leave, given in the story.
   - Scope: this is the acceptance-proposed S0013 listed in feature.md, with decision 22's two folded-in notes. The story's Description says the run behaviour, messages and ordering are unchanged. A shared write helper is left to a later story, and nothing is in the feature's Out of scope.
