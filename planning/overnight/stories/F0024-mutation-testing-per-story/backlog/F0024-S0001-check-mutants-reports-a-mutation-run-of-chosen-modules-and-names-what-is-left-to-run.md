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
12. `make check` stays green.
13. docs: `docs/project-guide/processes-and-checks.md`, *Mutation testing*: a new subsection *The report of a mutation run* for `factory.domain.mutants` and `python -m factory.entry.check_mutants`. It gives the input (what `mutmut results --all true` prints), the module of a mutant, the lines and the last line with an example, when a report is partial and its exit statuses 0, 1 and 2, what `--names` prints and why a module without a mutant gives a pattern, and that the recipe of `make mutants` calls it (the human's change after this story). *The duplicates report* (same file): one sentence that `check_duplicates` reads its files through `factory.entry.inputs.read_input`. `docs/decisions.md`: an entry *A mutation run's report is a line of its own, and a partial run is never complete*, dated with the story, with the feature's decisions 2, 3 and 8 and the rejected alternatives: a fourth check status, mutmut's own listing as the last line, and the survivors of every module in the report.

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
