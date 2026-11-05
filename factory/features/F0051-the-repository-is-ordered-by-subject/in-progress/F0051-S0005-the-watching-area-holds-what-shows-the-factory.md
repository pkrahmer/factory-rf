---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 560
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-05T02:49:49.337615Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T02:49:26.540948Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T02:49:26.547377Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T02:49:44.454039Z'
  stage: intake
  run: 32da5479f68a4b7ebcd4d64dac80909f
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T02:49:49.337615Z'
  stage: tests
---

# The watching area holds what shows the factory and what it costs

## Description

F0051 orders `src/factory/` by subject (feature decisions 1 to 3). This story moves the `watching` area: everything that shows what the factory does and what it costs: cost records, bills, the machine measures, human waits, transcripts, the board, the watcher, the factory log and the health file (the human, 2026-11-04). Each of its 17 modules moves from its layer package to the same layer inside `factory.watching`, keeps its name and its content, and is imported from the new path everywhere; nothing stays at the old path, not even a re-export (feature decision 4). The test modules of these modules move with them to `tests/watching/<layer>/` (feature decision 5). No behaviour changes: every test that passed before passes after, with only its import lines and paths changed.

## Interface

New packages, each with an `__init__.py` holding a one-line docstring: `factory.watching`, `factory.watching.domain`, `factory.watching.application`, `factory.watching.adapters`; and the same folders under `tests/watching/`, each with an `__init__.py`.

The moves (old → new), each file moved with `git mv`:

- `factory.domain.bills` → `factory.watching.domain.bills`
- `factory.domain.board` → `factory.watching.domain.board`
- `factory.domain.cost_records` → `factory.watching.domain.cost_records`
- `factory.domain.human_waits` → `factory.watching.domain.human_waits`
- `factory.domain.machine` → `factory.watching.domain.machine`
- `factory.domain.transcripts` → `factory.watching.domain.transcripts`
- `factory.application.board` → `factory.watching.application.board`
- `factory.application.costs` → `factory.watching.application.costs`
- `factory.application.machine` → `factory.watching.application.machine`
- `factory.application.transcripts` → `factory.watching.application.transcripts`
- `factory.application.watcher` → `factory.watching.application.watcher`
- `factory.adapters.cost_records_jsonl` → `factory.watching.adapters.cost_records_jsonl`
- `factory.adapters.machine_files` → `factory.watching.adapters.machine_files`
- `factory.adapters.transcript_files` → `factory.watching.adapters.transcript_files`
- `factory.adapters.record_log_jsonl` → `factory.watching.adapters.record_log_jsonl`
- `factory.adapters.factory_log` → `factory.watching.adapters.factory_log`
- `factory.adapters.health_file` → `factory.watching.adapters.health_file`

- No module under `src/` or `tests/` imports an old path of a moved module, and no file is left at an old path.
- `tests/test_areas.py`: the table `AREAS` gains the row of `watching` with the modules above; nothing else in that module changes.
- A test module under `tests/domain/`, `tests/application/` or `tests/adapters/` moves to `tests/watching/<its layer>/` when every one of its imports from `factory` is a module of the `watching` area or of an area already moved before it and at least one is of `watching`.
- The tester makes every test change the move needs in its first run, before the code moves: it rewrites every import of a moved module under `tests/`, moves the test modules with `git mv`, creates the test packages and changes the guards that pin the old layout, under the leave of feature decision 5. The coder changes only `src/`: its write paths do not hold `tests/`, so a test change it makes is dropped.
- The package docstrings are exactly: `factory.watching`: "The watching area: what shows the factory's work and what it costs."; each layer package: "The watching area's <layer> layer." (with `domain`, `application` or `adapters`).

## Acceptance criteria

1. `AREAS` in `tests/test_areas.py` has this story's area as a key whose modules are exactly those of the table above; and for every module of the table (one row each), `importlib.import_module("factory.watching.<layer>.<name>")` succeeds, and `src/factory/<layer>/<name>.py` does not exist.
2. Every package of the Interface (`factory.watching`, `factory.watching.domain`, `factory.watching.application`, `factory.watching.adapters`) imports and has a docstring.
3. No `.py` file under `src/` or `tests/` imports `factory.<layer>.<name>` of a module of the table, in any form (`import factory.<layer>.<name>`, `from factory.<layer>.<name> import x`, `from factory.<layer> import <name>`; one row per module).
4. No test module left under `tests/domain/`, `tests/application/` or `tests/adapters/` takes all its `factory` imports from `watching` and the areas moved before it.
5. `make check` stays green.
6. docs: every module path of the table that `README.md`, `docs/operator-guide.md` or the project guide under `docs/project-guide/` names is changed to the new path, and `docs/project-guide/README.md`'s section on the code's layout names the area `watching` and what it holds, in one sentence. `docs/decisions.md`: none, because the log is history and keeps the old paths.

## Smoke test

```bash
uv run python -c "import factory.watching.domain.bills as m; print(m.__name__)"
```
Expect: `factory.watching.domain.bills`

```bash
test -e src/factory/domain/bills.py && echo still there || echo moved
```
Expect: `moved`

```bash
uv run pytest tests/test_areas.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: The 17 moves are listed old → new, six in domain, five in application and six in adapters. The four new packages are named and their docstrings are given. The tester's and the coder's tasks are split by write paths. Nothing is missing.
   - Criteria: Each criterion is testable by one parametrized test. Criterion 1 has a row per module and checks the `AREAS` key, the import and the old path's absence, which is the standing answer 8 of the feature. Criterion 3 has a row per module and covers the three import forms, and criterion 4 is the test-move rule. The failing side is covered: the old path no longer exists and nothing imports it. The package docstring wording is not tested, as standing answer 8 says.
   - Smoke test: The three commands are runnable. Each `Expect:` line can be checked against the output. The pytest command passes no `-q`, and `addopts` in `pyproject.toml` sets a single `-q`, so the summary line is printed.
   - Architecture: Each module goes to the same layer inside `factory.watching`, so the layer rule is kept. The moves are made with `git mv`, nothing is re-exported, and the coder changes only `src/`.
   - Scope: The story is the watching area of feature decision 2, with decisions 4 and 5 applied. It changes no behaviour, and nothing in the feature's "Out of scope" is touched.
4. factory: started tests as vm.
