---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 244
comments_read: []
handed_over: null
claim:
  instance: self
  stage: doing
  started_at: '2026-10-19T01:30:28.940427Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T01:24:43.423550Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T01:24:43.429631Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T01:24:58.116177Z'
  stage: intake
  run: 1802a9d117d044308a864cb8b6177189
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T01:25:18.039726Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T01:27:11.944532Z'
  stage: tests
  run: 9f8e675a9d28491c976891198d6f77ce
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T01:27:32.458691Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T01:29:18.986883Z'
  stage: doing
  run: 921cb51f26354f1bb012dc0a2d47bbfc
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T01:29:39.074912Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T01:30:08.365494Z'
  stage: review
  run: 6023e6b28b82414897d5898b20de76a7
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T01:30:28.940427Z'
  stage: doing
---

# The contract command reads its arguments and creates its folder

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0021's acceptance ran `make mutants` over the feature's modules. Two behaviours of `factory.entry.contract`, the command that regenerates the records contract, survived their mutants, because no test reaches them. First, the command as `python -m factory.entry.contract` runs it: `main()` without `argv` reads the arguments from `sys.argv[1:]`, and the tests always pass `argv`, so reading `sys.argv[2:]`, or ignoring `sys.argv` altogether, goes unnoticed. Second, `write_contract` creates a folder whose parent is missing (`mkdir(parents=True)`), and no test writes into such a folder. This story pins both, for the coder of a later story who regenerates the schemas and for a reader who writes them into a folder of their own. The code is expected to pass as it is. No behaviour changes, and the schemas, their version and the other criteria of the contract stay as they are.

## Interface

No module under `src/factory/` changes. The behaviour pinned is that of `factory.entry.contract` (`entry`):

```python
def write_contract(folder: Path) -> list[Path]: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

- `main()` called without `argv` takes its arguments from `sys.argv[1:]`. One argument is the folder, none means `CONTRACT_FOLDER`, and two or more print the usage line to standard error and return 2.
- `write_contract(folder)` creates `folder` together with every missing parent folder.

Test module (new): `tests/entry/test_contract_arguments.py`. Its tests set `sys.argv` with `monkeypatch.setattr` and patch `CONTRACT_FOLDER` into `tmp_path` in every row, as `tests/entry/test_contract.py` does, so no row writes into the real folder. No earlier test changes.

## Acceptance criteria

1. `main()` without `argv`, with `sys.argv` set as follows (rows of one parametrized test):
   - `["contract", "<tmp_path>/given"]`: returns 0, prints `contract: 5 schemas written`, and writes the five schemas into `<tmp_path>/given`; the patched `CONTRACT_FOLDER` stays empty;
   - `["contract"]`: returns 0 and writes the five schemas into the patched `CONTRACT_FOLDER`;
   - `["contract", "a", "b"]`: returns 2, prints `usage: python -m factory.entry.contract [<folder>]` to standard error, and writes nothing.
2. `write_contract(<tmp_path>/a/b)`, where neither `a` nor `b` exists, returns the five paths under `<tmp_path>/a/b` in `CONTRACT` order, and each file exists. With `a` existing and `b` missing, the result is the same (rows of one parametrized test).
3. `make check` stays green.
4. docs: none. The operator guide's "The records contract" already says `uv run python -m factory.entry.contract [<folder>]` and what it prints, and this story changes no behaviour.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
uv run -q python -m factory.entry.contract "$d/a/b" && ls "$d/a/b" | wc -l
```

Expect: two lines, `contract: 5 schemas written` and `5`.

```bash
uv run -q python -m factory.entry.contract one two; echo "status $?"
```

Expect: `usage: python -m factory.entry.contract [<folder>]` on standard error, then `status 2`.

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names `factory.entry.contract.write_contract(folder: Path) -> list[Path]` and `main(argv: Sequence[str] | None = None) -> int`. Both match the code (`src/factory/entry/contract.py`). No source change is planned, and each stated behaviour is pinned by a criterion: `sys.argv[1:]` by criterion 1, `mkdir(parents=True)` by criterion 2.
   Criteria: each is testable by one parametrized test function. Criterion 1 covers one argument, none, and two or more, which is the failing side with usage on stderr and status 2. Criterion 2 covers both parent-missing cases and the result order. Criteria 3 and 4 are the closing ones.
   Smoke test: both blocks are runnable `uv run -q python -m factory.entry.contract` commands. Each `Expect:` line is checkable: the output line plus `5`, and the usage line plus `status 2`.
   Architecture: tests only, under `tests/entry/`, in the layer that mirrors `factory.entry`. No module under `src/` changes.
   Scope: it fits F0021's contract command (S0006). It is a pin proposed by the acceptance's mutants run and is not in "Out of scope". It adds a new test module and changes no earlier test.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 and 2 in a new module, `tests/entry/test_contract_arguments.py`. No earlier test changed.
   criterion 1: tests/entry/test_contract_arguments.py::test_main_without_argv_reads_the_arguments_after_the_program_name (three rows: `folder`, `no-folder`, `two-arguments`)
   criterion 2: tests/entry/test_contract_arguments.py::test_write_contract_creates_the_folder_and_its_missing_parents (two rows: `no-parent`, `parent-exists`)
   criterion 3: `make check` is the factory's gate; no test of its own.
   criterion 4: docs: none; nothing to test.
   How the tests are set up: every row patches `CONTRACT_FOLDER` to `<tmp_path>/default`, creates that folder empty first so that "stays empty" can be checked literally, and sets `sys.argv` with `monkeypatch.setattr`. Every row also moves the working directory into `tmp_path` (`monkeypatch.chdir`). That way the row with the relative arguments `a b` cannot write outside `tmp_path`, and the test can check that it writes no file and creates neither `a` nor `b`.
   The tests are not red: `make test` ended `test: green (37.5 s)`. This is expected, because the story pins behaviour that already exists ("The code is expected to pass as it is") and no source changes. The test runner could import every module. `make lint` is green.

   `lint`: lint: green (0.0 s)
   `test`: test: green (37.2 s)
6. factory: started doing as self.
7. coder: Built nothing. The story pins behaviour that already exists, and the tester's new module `tests/entry/test_contract_arguments.py` was already green against `src/factory/entry/contract.py` as it is. I ran `make check` and it ended `check: green`, with `test: green (39.6 s)`. My diff against `main` has no source change, so there was nothing to refactor.
   Main choice: leave `src/factory/entry/contract.py` unchanged, because the Interface says no module under `src/factory/` changes and the code already meets both criteria. I rejected touching it, for example a coverage-driven edit to the one uncovered line, because that would be a change the story's scope does not allow.
   Noticed, not touched: `src/factory/entry/contract.py:41` is still the one uncovered line in coverage. It is presumably the module's `__main__` guard, which only the smoke test's `python -m` run reaches.
   The journal changed nothing in the meaning of the task, so `## Description` stays as it is.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'`, which adds only `tests/entry/test_contract_arguments.py`, against the work item and `src/factory/entry/contract.py`. Criteria 1 and 2 are each covered by one parametrized test. The tests check what their criteria say. The rows kill the mutants named in the Description (`sys.argv[2:]`, ignoring `sys.argv`, no `parents=True`). The "two or more" limit is tested at two arguments, and its other side at one argument. The coder's `make check` was green (journal entry 7). Groups 1 to 3 pass. The finding below falls under group 4. It is round 0, so a point about a copied test helper still sends the work item back.

   1. `tests/entry/test_contract_arguments.py:15-26`: this is a second copy of helpers from `tests/entry/test_contract.py:23-24,79-84`. The constants `WRITTEN` and `USAGE` are copied word for word, and the row dataclass `_ArgvRow` has the same fields as `_MainRow` (`written`, `out`, `err`, `code`, and a `Callable[[Path], list[str]]` argument field). Fix: under the standing leave in CLAUDE.md, the tester moves `WRITTEN`, `USAGE` and the row dataclass to one shared module at the `tests/` root. Both modules then import them from there, and every earlier test in `tests/entry/test_contract.py` keeps its name and what it checks.

   Earlier tests: none. `git diff --name-status main...HEAD` lists no test file with a status other than `A`.
10. factory: started doing as self.
