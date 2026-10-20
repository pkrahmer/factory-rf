---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-20T04:25:41.942833Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-20T04:25:41.935774Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-20T04:25:41.942833Z'
  stage: intake
---

# The project guide names the shared test helpers

<!-- proposed by feature acceptance of 2026-10-20; refine before starting -->

## Description

A tester who writes a new test module has to find the helpers the earlier tests share before it writes its own, or the reviewer counts a copy as a finding (`CLAUDE.md`, *Tests*). In F0028 that happened in three of nine stories: S0001 copied `_raising` of `tests/domain/test_settings.py`, S0002 copied `FORM`, `SMOKE` and `TICKS`, and S0009 copied the opencode login hint of `tests/application/test_agent_run_probe_opencode.py`. Each cost a review round and four more runs. The shared helpers live in 35 modules at the root of `tests/` besides `conftest.py` (`acceptance_support.py` to `write_path_support.py`, with `acceptance_walk.py`, `document_texts.py`, `human_clone.py`, `observing_runtime.py`, `run_process_recorder.py`, `shipped_agents.py` and `source_search.py`), and F0028 added three of them (`acceptance_support.py`, `evaluation_support.py`, `tick_support.py`) and grew two (`settings_support.py`, `probe_support.py`). The project guide names eleven of them, each where its domain needs it, and has no list a tester can read first. This story is for the tester and the reviewer: it adds that list to the guide. The code, the tests and the other documents stay as they are. It changes no behaviour, so it has no criterion of its own beyond the two closing ones; keeping the list current as modules are added is left to the documenter of each later story.

## Interface

No module under `src/factory/` changes, and the tester writes no test module. The reference the documenter checks against is the set of modules `tests/*.py` whose name does not start with `test_`, and each module's docstring and public names.

## Acceptance criteria

1. `make check` stays green.
2. docs: the project guide's index, `docs/project-guide/README.md`, gets a section *Shared test helpers*, named in its *The files* line for `README.md`. It says that the helpers that more than one test module uses live in modules at the root of `tests/` (fixtures in `tests/conftest.py`), and that a test module imports them from there, as `CLAUDE.md`'s standing leave to move a shared test helper intends, and that a story that adds such a module names it in this list through its docs criterion. It then names every module `tests/*.py` whose name does not start with `test_`, `conftest.py` included, each with one line on what it holds (for example `tick_support.py`: `handlers_of` and `Failing`, the tick's handler factory and a handler that records each event and raises the error it is given, `ValueError("boom")` by default). `README.md`, `docs/operator-guide.md` and `docs/decisions.md`: none, because nothing an operator runs or decides changes.

## Smoke test

```bash
missing=0
for f in tests/*.py; do n=$(basename "$f"); case "$n" in test_*) continue;; esac; grep -qF -e "$n" docs/project-guide/README.md || { echo "missing: $n"; missing=$((missing+1)); }; done
echo "$missing"
```
Expect: `0` (every shared helper module at the root of `tests/` is named in the guide's index)

```bash
grep -c -F '## Shared test helpers' docs/project-guide/README.md
```
Expect: `1`

## Journal

1. 2026-10-20 human: created.
2. factory: started intake as self.
