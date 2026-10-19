---
stage: review
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 270
comments_read: []
handed_over: null
claim:
  instance: self
  stage: review
  started_at: '2026-10-19T16:16:45.733708Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T16:03:19.209860Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T16:03:19.217267Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-19T16:03:49.285388Z'
  stage: intake
  run: f37bae43a31f443c92a9422bc7018bf2
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-19T16:04:09.532042Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-19T16:07:13.717187Z'
  stage: tests
  run: f4f21d4b5bf445efa9acafec9ec94443
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-19T16:07:34.441159Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-19T16:10:05.817255Z'
  stage: doing
  run: 4ad2dbfae0244e05aa515e30298a8a5d
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-19T16:10:26.639579Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-19T16:11:19.938508Z'
  stage: review
  run: d1547e556c6d41189df56d4e7351ab13
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-19T16:11:41.144234Z'
  stage: doing
- number: 11
  speaker: coder
  kind: result
  at: '2026-10-19T16:11:55.896688Z'
  stage: doing
  run: 38f65ea4b8ff4ffeab254b82c2f0b97c
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-19T16:12:16.391069Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-10-19T16:14:10.224150Z'
  stage: tests
  run: 0c5b5e7743da4a44b91456729b6bf827
- number: 14
  speaker: factory
  kind: started
  at: '2026-10-19T16:14:31.370248Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-10-19T16:16:25.131813Z'
  stage: doing
  run: cc3542f2918547f6b8be58afb2c8deac
- number: 16
  speaker: factory
  kind: started
  at: '2026-10-19T16:16:45.733708Z'
  stage: review
---

# `check_mutants` reports a mutation run of chosen modules and names what is left to run

## Description

`make mutants` ends today with mutmut's own listing of every survivor in `mutants/`, earlier features' modules included, and with no line that says how far the run got. The factory reads only that last line, and the acceptance reviewer works out the score by hand. Before the human's `mutants` recipe can run per story (the feature's change 1), it needs one command that reads mutmut's results and answers two questions for a list of modules. First, the report: the survivors of those modules, and one last line that counts every status and says `partial` while a mutant is not checked, with exit status 1 then and 0 when the run is complete. Second, the names to run again: the mutants of those modules that are not killed, plus a pattern for a module that has no mutant yet. This story adds the pure rules in `factory.domain.mutants` and the command `python -m factory.entry.check_mutants`. It also moves `check_duplicates`'s way of reading a text file into `factory.entry.inputs`, so that both commands read their files one way. It runs no mutmut: it reads the text that `mutmut results --all true` prints. The `Makefile`, `CLAUDE.md` and the pipeline definition are the human's changes after this story.

## Interface

`factory.domain.mutants` (`domain`, new):

```python
MutantStatus = Literal[
    "killed",
    "survived",
    "timeout",
    "suspicious",
    "no tests",
    "skipped",
    "segfault",
    "caught by type check",
    "check was interrupted by user",
    "not checked",
]

MutantName = Annotated[str, StringConstraints(pattern=r"^[^\s.:]+(\.[^\s.:]+)+$")]


class MutantResult(BaseModel):
    """One mutant of a mutation run, by mutmut's name for it, and how its run ended."""

    name: MutantName
    status: MutantStatus

    @property
    def module(self) -> str: ...


class MutationReport(BaseModel):
    """What a mutation run of some modules printed for the reader, and whether it is complete."""

    lines: list[str]
    partial: bool


def parse_results(text: str) -> list[MutantResult]: ...
def mutation_report(
    results: Sequence[MutantResult], modules: Sequence[str], *, stopped_after: int | None
) -> MutationReport: ...
def rerun_names(results: Sequence[MutantResult], modules: Sequence[str]) -> list[str]: ...
```

- Both models are frozen and forbid unknown keys. `MutantResult` refuses a name without a dot, with an empty dotted part, or with whitespace or a colon in it. It refuses a status outside the ten.
- `module` is the name without its last dotted part: `factory.application.stage.xǁStageRunnerǁrun__mutmut_3` gives `factory.application.stage`.
- `parse_results`: every line is taken without its leading and trailing whitespace, and a blank line is skipped. The other lines are split at their last `": "` into name and status, in their order. A line without `": "`, or one whose name or status `MutantResult` refuses, raises `ValueError` with the message `not a result line of mutmut: <the stripped line, as repr>`.
- Of `results`, `mutation_report` and `rerun_names` take only those whose `module` equals one of `modules`, in the order of `results`. A module given twice counts once.
- `mutation_report`: `lines` holds one line `<name>: <status>` for each chosen result whose status is `survived`, `timeout`, `suspicious` or `segfault`, in order. Then comes the last line, `mutants: <killed> killed, <survived> survived, <timeout> timed out, <no tests> without tests, <not checked> not checked, <other> other of <total> mutant(s) in <m> module(s)`. `<other>` counts `suspicious`, `skipped`, `segfault`, `caught by type check` and `check was interrupted by user`, `<total>` the chosen results and `<m>` the distinct `modules`. `partial` is true when `stopped_after` is not `None` or a chosen result is `not checked`. A partial last line has `partial, ` right after `mutants: `. When `stopped_after` is set, the last line ends with ` (stopped after <stopped_after> s)`. A `stopped_after` below 1 raises `ValueError` with the message `stopped_after must be at least 1, not <value>`; 1 is accepted.
- `rerun_names`: the names of the chosen results whose status is neither `killed` nor `caught by type check`, in order. Then, for each distinct module of `modules` in its given order with no chosen result, the pattern `<module>.*`.

`factory.entry.inputs` (`entry`, new):

```python
class UnreadableInput(Exception):
    """A command's input file that cannot be read as UTF-8 text."""


def read_input(path: Path) -> str: ...
```

- `read_input` returns the file's text read as UTF-8. An `OSError` or a `UnicodeDecodeError` raises `UnreadableInput` with the message `cannot read <path>: <error>`, chained from it.
- `factory.entry.check_duplicates` reads its three files through `read_input` and catches `UnreadableInput` where it caught `_UnreadableError`. Its `_read` and `_UnreadableError` are removed; a pylint or vulture text it cannot parse raises `UnreadableInput` with the parser's own message. A parse fault still gives its own message, so its output, its exit statuses and its tests stay exactly as they are.

`factory.entry.check_mutants` (`entry`, new):

```python
def main(argv: Sequence[str] | None = None) -> int: ...
```

- Arguments: `results` (the path of a file holding what `mutmut results --all true` printed), then one or more `modules` (dotted module names), then either `--stopped-after <seconds>` (an integer of at least 1) or `--names`, never both. `argv` `None` reads `sys.argv[1:]`. The program name is `check-mutants`. The module runs as `python -m factory.entry.check_mutants` (`raise SystemExit(main())`).
- Without `--names`: each line of `mutation_report(...).lines` printed to standard output, and 1 returned when the report is partial, 0 otherwise.
- `--names`: each name of `rerun_names` printed on a line of its own, nothing else, and 0 returned.
- An unreadable file, or a line `parse_results` refuses, prints one line `check-mutants: <message>` to standard error, nothing to standard output, and returns 2. A missing `modules` argument, `--stopped-after 0`, a `--stopped-after` that is not an integer, and `--names` together with `--stopped-after` end through argparse with exit status 2.

Tests (the tester writes them): `tests/domain/test_mutants.py`, `tests/entry/test_inputs.py`, `tests/entry/test_check_mutants.py` (calling `main` with a list of arguments, with result files written into `tmp_path`, and `capsys`). No test starts mutmut or a child process. `tests/entry/test_check_duplicates.py` passes unchanged, and no earlier test changes.

## Acceptance criteria

1. `parse_results` (rows of one parametrized test): the text `"    factory.domain.a.x_f__mutmut_1: killed\n\n    factory.domain.a.xǁCǁm__mutmut_2: not checked\n"` gives two results, in that order, with those names and statuses. `""` gives `[]`. A line holding each of the ten statuses gives that status (ten rows). The lines `factory.domain.a.x_f__mutmut_1 killed`, `factory.domain.a.x_f__mutmut_1: dead`, `x_f__mutmut_1: killed`, `factory..x_f__mutmut_1: killed`, `factory.domain.a b.x_f__mutmut_1: killed` (whitespace in the name), `factory.domain:a.x_f__mutmut_1: killed` (a colon in the name) and `Warning: 3 files changed` each raise `ValueError`, and its message is `not a result line of mutmut: ` followed by the stripped line's repr.
2. `MutantResult.module` (rows of one parametrized test): `factory.application.stage.xǁStageRunnerǁrun__mutmut_3` gives `factory.application.stage`, `factory.entry.guard.x_main__mutmut_1` gives `factory.entry.guard`, and `a.b` gives `a`.
3. `mutation_report`, the lines (one test). The results are `factory.domain.a` with one each of `killed`, `segfault`, `survived`, `timeout`, `no tests`, `suspicious`, `skipped`, `caught by type check` and `check was interrupted by user`, in that order, and `factory.domain.b` with one `survived`. With modules `["factory.domain.a"]` and no stop, `lines` is exactly the four lines of `a`'s `segfault`, `survived`, `timeout` and `suspicious` mutants, in that order (the order of the results, not of the statuses), then `mutants: 1 killed, 1 survived, 1 timed out, 1 without tests, 0 not checked, 5 other of 9 mutant(s) in 1 module(s)`, and `partial` is false.
4. `mutation_report`, complete and partial (rows of one parametrized test, on results of `factory.domain.a` and `factory.domain.b`, with modules `["factory.domain.a", "factory.domain.b"]` unless a row names others). All of them killed or survived, with no stop: not partial, and the last line starts `mutants: ` followed by a digit. One of them `not checked`: partial, and the last line starts `mutants: partial, ` and counts `1 not checked`. All of them killed with `stopped_after=540`: partial, and the last line ends ` (stopped after 540 s)`. Modules `["factory.domain.c"]`, which no result has: not partial, and the last line is `mutants: 0 killed, 0 survived, 0 timed out, 0 without tests, 0 not checked, 0 other of 0 mutant(s) in 1 module(s)`. Modules `["factory.domain.a", "factory.domain.a"]` count `in 1 module(s)`. With modules `["factory.domain.a"]`, results holding two killed mutants of `factory.domain.a` and one `not checked` mutant each of `factory.domain.b` and `factory.domain.ab`: not partial, and the last line is `mutants: 2 killed, 0 survived, 0 timed out, 0 without tests, 0 not checked, 0 other of 2 mutant(s) in 1 module(s)`.
5. `mutation_report` with `stopped_after=0` raises `ValueError` with the message `stopped_after must be at least 1, not 0`, and with `stopped_after=1` it returns a partial report whose last line ends ` (stopped after 1 s)` (rows of one parametrized test).
6. `rerun_names` (rows of one parametrized test). For modules `["factory.domain.a", "factory.domain.c"]` on results of `factory.domain.a` (one each of `killed`, `survived`, `not checked`, `no tests`, `caught by type check`, in that order) and `factory.domain.b` (one `survived`), it gives exactly the names of `a`'s `survived`, `not checked` and `no tests` mutants, in that order, then `factory.domain.c.*`. On results where every mutant of `factory.domain.a` is killed, modules `["factory.domain.a"]` give `[]`. Modules `["factory.domain.a", "factory.domain.c", "factory.domain.c"]` on the first row's results give the same list, with `factory.domain.c.*` once. On results of `factory.domain.a` with one mutant of each of the ten statuses, in the order of `MutantStatus`, modules `["factory.domain.a"]` give the eight names of all but the `killed` and `caught by type check` ones, in that order. Modules `["factory.domain.d", "factory.domain.a", "factory.domain.c"]` on the first row's results give `a`'s three names, then `factory.domain.d.*`, then `factory.domain.c.*`.
7. `read_input` (rows of one parametrized test): a UTF-8 file gives its text. A missing file raises `UnreadableInput` whose message starts `cannot read <path>: `. A file holding the bytes `b"\xff\xfe"` raises `UnreadableInput` whose message starts the same way.
8. `check_mutants` without `--names` (rows of one parametrized test, a results file in `tmp_path`): a complete run prints the report's lines and returns 0. A run with a `not checked` mutant returns 1 and prints a last line starting `mutants: partial, `. `--stopped-after 540` on a complete run returns 1 and prints a last line ending ` (stopped after 540 s)`. Called as `main()` with `sys.argv` set to `["check-mutants", <the complete run's file>, "factory.domain.a"]` (`monkeypatch`), it returns 0 and prints the same lines as with that list.
9. `check_mutants --names` prints exactly the names of criterion 6's first row, one per line, and returns 0, also when the results hold a `not checked` mutant.
10. The faults of `check_mutants` (rows of one parametrized test): a results path that does not exist returns 2, prints nothing to standard output, and prints one line to standard error that starts `check-mutants: cannot read `. A results file holding `garbage` returns 2 and prints `check-mutants: not a result line of mutmut: 'garbage'` to standard error. `--names` with a results path that does not exist also returns 2 and prints one line to standard error that starts `check-mutants: cannot read `, and nothing to standard output. No module, `--stopped-after 0`, `--stopped-after soon`, and `--names --stopped-after 540` each end with `SystemExit` with code 2.
11. `check_duplicates` still reads its files and reports an unreadable one as before: every test of `tests/entry/test_check_duplicates.py` passes unchanged, and `factory.entry.check_duplicates` no longer defines `_read`.
12. `read_input`'s `UnreadableInput` is chained from the error it reports (rows of one parametrized test): for a missing file its `__cause__` is a `FileNotFoundError`, and for a file holding `b"\xff\xfe"` its `__cause__` is a `UnicodeDecodeError`.
13. `make check` stays green.
14. docs: `docs/project-guide/processes-and-checks.md`, *Mutation testing*: a new subsection *The report of a mutation run* for `factory.domain.mutants` and `python -m factory.entry.check_mutants`. It gives the input (what `mutmut results --all true` prints), the module of a mutant, the lines and the last line with an example, when a report is partial and its exit statuses 0, 1 and 2, what `--names` prints and why a module without a mutant gives a pattern, and that the recipe of `make mutants` calls it (the human's change after this story). *The duplicates report* (same file): one sentence that `check_duplicates` reads its files through `factory.entry.inputs.read_input`. `docs/decisions.md`: an entry *A mutation run's report is a line of its own, and a partial run is never complete*, dated with the story, with the feature's decisions 2, 3 and 8 and the rejected alternatives: a fourth check status, mutmut's own listing as the last line, and the survivors of every module in the report.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf '    factory.domain.a.x_f__mutmut_1: killed\n    factory.domain.a.x_f__mutmut_2: survived\n    factory.domain.a.x_g__mutmut_1: not checked\n    factory.domain.b.x_h__mutmut_1: survived\n' > "$d/results.txt"
uv run -q python -m factory.entry.check_mutants "$d/results.txt" factory.domain.a; echo "exit $?"
```
Expect: three lines, `factory.domain.a.x_f__mutmut_2: survived`, `mutants: partial, 1 killed, 1 survived, 0 timed out, 0 without tests, 1 not checked, 0 other of 3 mutant(s) in 1 module(s)`, `exit 1`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf '    factory.domain.a.x_f__mutmut_1: killed\n    factory.domain.a.x_f__mutmut_2: survived\n    factory.domain.a.x_g__mutmut_1: not checked\n' > "$d/results.txt"
uv run -q python -m factory.entry.check_mutants --names "$d/results.txt" factory.domain.a factory.domain.c; echo "exit $?"
```
Expect: four lines, `factory.domain.a.x_f__mutmut_2`, `factory.domain.a.x_g__mutmut_1`, `factory.domain.c.*`, `exit 0`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf '    factory.domain.a.x_f__mutmut_1: killed\n' > "$d/results.txt"
uv run -q python -m factory.entry.check_mutants --stopped-after 540 "$d/results.txt" factory.domain.a; echo "exit $?"
uv run -q python -m factory.entry.check_mutants "$d/missing.txt" factory.domain.a 2> "$d/error.txt"; echo "exit $?"
cut -c1-26 "$d/error.txt"
```
Expect: four lines, `mutants: partial, 1 killed, 0 survived, 0 timed out, 0 without tests, 0 not checked, 0 other of 1 mutant(s) in 1 module(s) (stopped after 540 s)`, `exit 1`, `exit 2`, `check-mutants: cannot read`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
1. 2026-10-19 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`factory.domain.mutants`, `factory.entry.inputs`, `factory.entry.check_mutants`, the `check_duplicates` change). The Pydantic models, the ten statuses, the name pattern and every message text are spelled out. Nothing is left for the coder to choose.
   Criteria: each can be tested by one test function. Every rule has its failing side: the name and status refusals and the `ValueError` message (1), `stopped_after` 0 and 1 (5), a missing file, bad bytes and `garbage` (7, 10), the argparse refusals (10), and an unreadable file with `--names` (10). Every Interface comment on behaviour has a criterion: the module of a mutant (2), the line order and the counts (3), partial, stop suffix and distinct modules (4), the prefix match against `factory.domain.ab` (4), and the rerun order, the pattern and a pattern given twice (6). Two small gaps are not worth a question. `UnreadableInput` being chained from the `OSError` has no assertion. A parse fault with `--names` has no row, but it runs the same code path as the row without `--names`.
   Smoke test: three runnable blocks that use only `mktemp` and `uv run -q python -m`. Each `Expect:` names exact lines and exit codes. I counted `cut -c1-26` and it yields `check-mutants: cannot read`.
   Architecture: the pure rules are in `domain`, with no I/O. The file reading and the argument parsing are in `entry`. `check_duplicates` and the new command share one reader, as `CLAUDE.md` asks (no second copy). The story adds no dependency and no wrapper.
   Scope: it matches the feature's S0001 scope exactly. The `Makefile`, `CLAUDE.md` and the pipeline definition are left to the human. No earlier test changes (`test_check_duplicates.py` passes unchanged), and the docs criterion covers the feature's decisions 2, 3 and 8.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 11 from the Interface. Criteria 12 and 13 have no test of their own: 12 is `make check` and 13 is the documenter's.

   - criterion 1: tests/domain/test_mutants.py::test_result_lines_are_read_in_their_order (two lines with a blank one between, empty text, one row per status) and tests/domain/test_mutants.py::test_a_line_that_is_no_result_is_refused (the seven refused lines, checking the exact message)
   - criterion 2: tests/domain/test_mutants.py::test_the_module_of_a_mutant_is_its_name_without_the_last_part
   - criterion 3: tests/domain/test_mutants.py::test_the_report_lists_the_open_mutants_of_the_chosen_modules_and_counts_them
   - criterion 4: tests/domain/test_mutants.py::test_a_report_is_partial_while_a_mutant_is_not_checked_or_the_run_stopped (six rows: complete, not-checked, stopped, no-result-of-the-module, module-given-twice, other-modules-left-out with `factory.domain.ab`)
   - criterion 5: tests/domain/test_mutants.py::test_stopped_after_is_at_least_one_second (rows 0 and 1)
   - criterion 6: tests/domain/test_mutants.py::test_the_names_to_run_again_are_the_unkilled_mutants_and_modules_without_one (five rows)
   - criterion 7: tests/entry/test_inputs.py::test_an_input_is_read_as_utf_8_or_reported_unreadable (utf-8, missing, `b"\xff\xfe"`)
   - criterion 8: tests/entry/test_check_mutants.py::test_the_report_is_printed_and_a_partial_run_fails (complete, not-checked, `--stopped-after 540`, `sys.argv` through monkeypatch; plus a `--stopped-after 1` row so the accepted side of "at least 1" is tested too, since CLAUDE.md asks for both sides of every limit)
   - criterion 9: tests/entry/test_check_mutants.py::test_names_prints_the_mutants_to_run_again_and_succeeds (the results hold a `not checked` mutant)
   - criterion 10: tests/entry/test_check_mutants.py::test_a_fault_ends_with_status_2 (missing file, `garbage`, `--names` with a missing file, no module, `--stopped-after 0`, `--stopped-after soon`, `--names --stopped-after 540`)
   - criterion 11: tests/entry/test_inputs.py::test_check_duplicates_has_no_reader_of_its_own. tests/entry/test_check_duplicates.py is untouched and covers the rest.

   Files created: tests/domain/test_mutants.py, tests/entry/test_inputs.py, tests/entry/test_check_mutants.py. No earlier test file was changed.

   Modules the test run could not import: `factory.domain.mutants`, `factory.entry.inputs`, `factory.entry.check_mutants`. All three new test modules stop at collection with ImportError; that is the expected red. `make lint` is green. I did not run the type check, as this stage says.

   In the CLI tests, options come before the results path, as in the smoke test. No criterion needed interpreting, so there is no open question.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/entry/test_inputs.py - ImportError while importing test module '/...
6. factory: started doing as self.
7. coder: Built the mutation report rules, the shared input reader and the `check_mutants` command, as described in the Interface. `make check` is green: lint, types, layers, sast, secrets, licenses and test, ending with `check: green`. The tester's new tests pass, and so does `tests/entry/test_check_duplicates.py`, unchanged.

   - `src/factory/domain/mutants.py` (new). It holds `MutantStatus`, `MutantName`, the two models `MutantResult` (with its `module` property) and `MutationReport`, and the functions `parse_results`, `mutation_report` and `rerun_names`.
     - `parse_results` strips each line, skips blank lines and splits at the last `": "`. It refuses a line in two cases: when there is no `": "`, and when pydantic rejects the name or status. A rejection is caught as `ValidationError` and raised again as the `ValueError` with the Interface's message, chained from it.
     - The three status sets are module constants: the ones the report lists, the ones counted as `other`, and the ones `rerun_names` treats as done.
     - `_chosen` keeps the results whose module is in `modules`. It compares whole module names, so `factory.domain.ab` is not taken for `factory.domain.a`.
     - `partial` is computed once and passed to `_last_line`.
   - `src/factory/entry/inputs.py` (new). It holds `UnreadableInput` and `read_input`.
   - `src/factory/entry/check_mutants.py` (new). It uses argparse with `results`, `modules` (`nargs="+"`), and a mutually exclusive group of `--stopped-after` and `--names`. `--stopped-after` uses its own type function, so 0 and non-integers end through argparse with status 2. Both an `UnreadableInput` and a parse `ValueError` print `check-mutants: <message>` to standard error and return 2.
   - `src/factory/entry/check_duplicates.py`. I removed `_UnreadableError` and `_read`; it now reads through `read_input` and catches `UnreadableInput`. A parser fault is raised again as `UnreadableInput` with the parser's own message, so the output is unchanged.

   Main choice: I checked `--stopped-after` in an argparse type function, so a bad value is refused before any file is read and exits 2 the way the criteria ask. `mutation_report` keeps its own `ValueError` for callers that do not come through the command line. The alternative I rejected was letting the domain's `ValueError` reach `main`'s fault handler. That would have printed a `check-mutants:` line and returned 2 instead of ending through argparse, and criterion 10 asks for the argparse ending.

   Refactor: I made one pass over my own diff. I removed the second computation of `partial`, which had been worked out in both `mutation_report` and `_last_line`, and let ruff format the result. Nothing else needed changing.

   I did not run the smoke-test blocks: the permission system denied the command (it held an `rm -rf` of the temporary folder). `make duplicates` was not run either.

   Noticed but not touched: `docs/` (the documenter writes criterion 13), and the `Makefile`, `CLAUDE.md` and the pipeline definition, which are the human's changes after this story.

   `check`: check: green
   `duplicates`: duplicates: 5 new, 33 known, 3 gone
8. factory: started review as self.
9. reviewer: Reviewed `git diff main...HEAD -- . ':!factory'` (src/factory/domain/mutants.py, src/factory/entry/inputs.py, src/factory/entry/check_mutants.py, src/factory/entry/check_duplicates.py and the three new test files) against the work item. Group 1 (acceptance criteria) fails, so I stopped there. The code itself matches the Interface: the domain has no I/O, `_chosen` compares whole module names, and `--stopped-after` is refused through argparse. The coder's journal entry records `make check` green.

   1. tests/domain/test_mutants.py `test_result_lines_are_read_in_their_order` and `test_a_line_that_is_no_result_is_refused`: criterion 1 asks for "rows of one parametrized test", but the accepted lines and the refused lines of `parse_results` are two separate test functions. Fix: merge them into one parametrized test where each row expects either the results or the `ValueError` message.
   2. criterion 12 added: it needs its test. The Interface says `read_input` raises `UnreadableInput` "chained from" the `OSError` or `UnicodeDecodeError`, and no criterion or test checked that (intake noted the gap). The new criterion 12 says that `__cause__` is a `FileNotFoundError` for a missing file and a `UnicodeDecodeError` for `b"\xff\xfe"`. Pinning it needs no change under `src/` (src/factory/entry/inputs.py already chains with `from error`). The two closing criteria are now 13 (`make check`) and 14 (docs).

   Rejected as findings: the stopped-after 1 and 0 sides in tests/entry/test_check_mutants.py are in two functions. I left that out because criteria 8 and 10 group the command's rows by outcome, and the domain test checks both sides in one parametrized test. The missing `--names` row for a parse fault runs the same `try` in `main` as the row without `--names`. I found no copied test helper.

   Earlier tests: none. Every test file the diff touches has status `A`, and tests/entry/test_check_duplicates.py is unchanged.
10. factory: started doing as self.
11. coder: Round 1: both of the reviewer's findings are test changes, so I changed no code and am handing them to the tester.

    1. Criterion 1: in tests/domain/test_mutants.py, merge `test_result_lines_are_read_in_their_order` and `test_a_line_that_is_no_result_is_refused` into one parametrized test. Each row expects either the parsed results or the `ValueError` message `not a result line of mutmut: <repr>`.
    2. Criterion 12 (the reviewer added it) needs only its test. Add a parametrized test to tests/entry/test_inputs.py: for a missing file, `UnreadableInput.__cause__` is a `FileNotFoundError`; for a file holding `b"\xff\xfe"`, it is a `UnicodeDecodeError`. The code already chains the error (`raise ... from error` in src/factory/entry/inputs.py), so this test should pass with no change under `src/`.

    What I built: nothing new this round. The code from the previous round stays as it is: src/factory/domain/mutants.py, src/factory/entry/inputs.py, src/factory/entry/check_mutants.py and src/factory/entry/check_duplicates.py.

    Main choice: I ended with `tests` and did not touch any code. The alternative I rejected was editing the tests myself, which the coder may never do.

    What the journal changed: criterion 12 was added, and the two closing criteria are now 13 and 14. The Description already says this, so I did not rewrite it. I did not run `make check`, because the working tree has no code change since the green run recorded in entry 7.

    Noticed but not touched: nothing new.
12. factory: started tests as self.
13. tester: I made the two test changes listed in the coder's entry 11: the reviewer's finding 1 and the test for the new criterion 12. I did not touch any code under `src/`.

    - criterion 1: tests/domain/test_mutants.py::test_result_lines_are_read_in_their_order_and_other_lines_are_refused. This replaces `test_result_lines_are_read_in_their_order` and `test_a_line_that_is_no_result_is_refused`, merged into one parametrized test. It keeps the same rows: two lines with a blank line between, empty text, one row per status, and the seven refused lines. A refused row expects the `ValueError` with the exact message `not a result line of mutmut: <repr>`.
    - criterion 12: tests/entry/test_inputs.py::test_an_unreadable_input_is_chained_from_the_error_it_reports. It has two rows. For a missing file, `__cause__` is a `FileNotFoundError`. For a file holding `b"\xff\xfe"`, it is a `UnicodeDecodeError`.

    All other tests and the mapping in entry 5 are unchanged.

    Files changed: tests/domain/test_mutants.py and tests/entry/test_inputs.py, both written by this story. I created no new files and changed no earlier test file.

    Every module imported. `make test` is green. That is expected, because the code already existed and already chains the error (`from error` in src/factory/entry/inputs.py). `make lint` is green.

    `lint`: lint: green (0.0 s)
    `test`: test: green (43.7 s)
14. factory: started doing as self.
15. coder: Round 1, after the tester's entry 13. I changed no code this round. The tester made both of the reviewer's findings: the merged parametrized test for criterion 1 in tests/domain/test_mutants.py, and the chaining test for criterion 12 in tests/entry/test_inputs.py. Both pass against the code from entry 7. I ran `make check` in the foreground and it ended `check: green`, with `test: green (44.0 s)` and total coverage at 99.07 %.

    What I built (unchanged since entry 7): src/factory/domain/mutants.py, src/factory/entry/inputs.py and src/factory/entry/check_mutants.py, plus src/factory/entry/check_duplicates.py, which now reads its files through `read_input`.

    Main choice (from entry 7, still holds): `--stopped-after` is checked by an argparse type function. A value of 0 or a non-integer therefore ends through argparse with status 2, which criterion 10 asks for. The alternative I rejected was letting the domain's `ValueError` from `mutation_report` reach `main`'s fault handler. That would print a `check-mutants:` line instead. The domain keeps its own check for callers that do not come through the command line.

    Refactor: I read `git diff main -- src/factory` again and found nothing to change. The three status sets are constants, `partial` is computed once, and there is no duplicated reader now that `check_duplicates` uses `read_input`.

    What the journal changed: criterion 12 was added and the closing criteria were renumbered (entry 9). The Description is still accurate, so I did not rewrite it.

    Noticed but not touched: the docs for criterion 14 are the documenter's work. The `Makefile`, `CLAUDE.md` and the pipeline definition are the human's changes after this story. I did not run the smoke-test blocks this round.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 33 known, 3 gone
16. factory: started review as self.
