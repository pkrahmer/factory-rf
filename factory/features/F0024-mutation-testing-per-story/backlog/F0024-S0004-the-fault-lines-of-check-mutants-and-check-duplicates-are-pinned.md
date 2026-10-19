# The fault lines of `check-mutants` and `check-duplicates` are pinned

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

The two report commands of the factory, `python -m factory.entry.check_mutants` and `python -m factory.entry.check_duplicates`, end a fault with one line on standard error that an operator reads in a report's journal line or a run by hand. F0024-S0001's Interface states two rules about that line that no test notices breaking: the program name is `check-mutants` (and `check-duplicates`), and a pylint or vulture text that `check_duplicates` cannot parse is reported "with the parser's own message". `--stopped-after`'s two refusals also carry a reason (`not an integer: 'soon'`, `must be at least 1, not 0`), and the tests check only the exit status 2. F0024's acceptance found these as surviving mutants: `prog=None` in both parsers, `ArgumentTypeError(None)` for both reasons, and `UnreadableInput(None)` or `UnreadableInput(str(None))` in `check_duplicates._findings`. This story pins those texts with tests and changes no code. The equivalent survivors of the same modules (`encoding="UTF-8"` or `None` in `read_input` and `_write_baseline`, `argv is None` short-circuited in both `main`s, `partition` for `rpartition` in `_parse_line`) stay as they are: no test can tell them apart in a UTF-8 container.

## Interface

No module under `src/factory/` changes. The texts the tests pin, as the code prints them today:

```text
check-mutants: error: argument --stopped-after: not an integer: 'soon'
check-mutants: error: argument --stopped-after: must be at least 1, not 0
check-duplicates: vulture line 1 is not in vulture's form: 'oops'
check-duplicates: pylint output is not JSON: <json's own reason>
```

- `factory.entry.check_mutants.main` (`entry`): argparse's usage line on standard error starts `usage: check-mutants ` for every refusal it makes, whatever `sys.argv[0]` is. `--stopped-after soon` ends with the last line of standard error `check-mutants: error: argument --stopped-after: not an integer: 'soon'`, and `--stopped-after 0` with `check-mutants: error: argument --stopped-after: must be at least 1, not 0`; `--stopped-after 1` is accepted (F0024-S0001's tests already show it).
- `factory.entry.check_duplicates.main` (`entry`): argparse's usage line starts `usage: check-duplicates `. A vulture text `oops\n` gives standard error exactly `check-duplicates: vulture line 1 is not in vulture's form: 'oops'\n`; a pylint text `not json` gives one line that starts `check-duplicates: pylint output is not JSON: `.

Tests (the tester writes them): `tests/entry/test_check_mutants_faults.py` and `tests/entry/test_check_duplicates_faults.py`, new modules. Each sets `sys.argv` through `monkeypatch` to `["some-other-name"]` before it calls `main` with a list of arguments, so that argparse's default program name would differ. The second needs the `inputs` fixture, `Inputs`, `_arguments` and the constants of `tests/entry/test_check_duplicates.py`; the standing leave of `CLAUDE.md` (*Tests*) lets the tester move them to one shared place under `tests/` and change that earlier module to use them from there, every test keeping its name and its checks. No other earlier test changes.

## Acceptance criteria

1. `check_mutants` refusals (rows of one parametrized test, `sys.argv` set to `["some-other-name"]`, a results file in `tmp_path` holding one killed mutant of `factory.domain.a`): `--stopped-after soon` ends with `SystemExit` code 2, its standard error starts `usage: check-mutants ` and its last line is `check-mutants: error: argument --stopped-after: not an integer: 'soon'`. `--stopped-after 0` ends with code 2, the same start, and the last line `check-mutants: error: argument --stopped-after: must be at least 1, not 0`. No module ends with code 2 and standard error starting `usage: check-mutants `. `--stopped-after 1` returns 1 and prints nothing to standard error.
2. `check_duplicates` parse faults (rows of one parametrized test): a vulture file holding `oops\n` returns 2, prints nothing to standard output and exactly `check-duplicates: vulture line 1 is not in vulture's form: 'oops'\n` to standard error. A pylint file holding `not json` returns 2 and prints one line to standard error that starts `check-duplicates: pylint output is not JSON: `. Valid inputs with a baseline of both keys return 0 and print nothing to standard error.
3. `check_duplicates` program name (rows of one parametrized test, `sys.argv` set to `["some-other-name"]`): no argument, and the two inputs without `--baseline`, each end with `SystemExit` code 2 and standard error starting `usage: check-duplicates `.
4. Every test of `tests/entry/test_check_mutants.py`, `tests/entry/test_check_duplicates.py` and `tests/entry/test_inputs.py` passes, with its name and its checks unchanged.
5. `make check` stays green.
6. docs: none. `docs/project-guide/processes-and-checks.md` already states each text (*The duplicates report*, *The report of a mutation run*, *Exit statuses*); the documenter checks that it still does.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
printf '    factory.domain.a.x_f__mutmut_1: killed\n' > "$d/results.txt"
uv run -q python -m factory.entry.check_mutants --stopped-after soon "$d/results.txt" factory.domain.a 2>&1 | tail -n 1; echo "exit ${PIPESTATUS[0]}"
uv run -q python -m factory.entry.check_mutants --stopped-after 0 "$d/results.txt" factory.domain.a 2>&1 | tail -n 1
printf '[]' > "$d/pylint.json"; printf 'oops\n' > "$d/vulture.txt"; : > "$d/baseline.txt"
uv run -q python -m factory.entry.check_duplicates "$d/pylint.json" "$d/vulture.txt" --baseline "$d/baseline.txt"; echo "exit $?"
```

Expect: five lines, `check-mutants: error: argument --stopped-after: not an integer: 'soon'`, `exit 2`, `check-mutants: error: argument --stopped-after: must be at least 1, not 0`, `check-duplicates: vulture line 1 is not in vulture's form: 'oops'`, `exit 2`

## Journal

Empty in the backlog. The factory writes entry 1 when the story starts.
