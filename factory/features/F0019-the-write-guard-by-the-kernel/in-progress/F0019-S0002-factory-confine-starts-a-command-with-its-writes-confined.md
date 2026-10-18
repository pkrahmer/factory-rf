---
stage: doing
blocked: null
round: 1
attempts: 0
crashes: 0
pull_request: 221
comments_read: [6251323783]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T14:43:28.693326Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T14:43:28.699870Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T14:43:52.992737Z'
  stage: intake
  run: cad48beb6b314869ba93ca927c4f1470
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T14:44:12.838261Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T14:49:02.754667Z'
  stage: tests
  run: 2892fb455ef64dcc906d519b1c3bbe33
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-18T14:49:22.854312Z'
  stage: doing
- number: 7
  speaker: coder
  kind: question
  at: '2026-10-18T14:51:28.590007Z'
  stage: doing
  run: bd772f32133f4b0ea5bf2b0cbe30e51b
- number: 8
  speaker: human
  kind: comment
  at: '2026-10-18T14:53:46.253719Z'
  stage: doing
- number: 9
  speaker: factory
  kind: started
  at: '2026-10-18T14:54:03.797155Z'
  stage: doing
- number: 10
  speaker: coder
  kind: result
  at: '2026-10-18T14:54:20.339121Z'
  stage: doing
  run: 6c9127f8efb745268e4ddba292f880dc
- number: 11
  speaker: factory
  kind: started
  at: '2026-10-18T14:54:41.044597Z'
  stage: tests
- number: 12
  speaker: tester
  kind: result
  at: '2026-10-18T14:56:24.022072Z'
  stage: tests
  run: d9d5fdd66bf1449d8760036e6d3f06a0
- number: 13
  speaker: factory
  kind: started
  at: '2026-10-18T14:56:44.205259Z'
  stage: doing
- number: 14
  speaker: coder
  kind: result
  at: '2026-10-18T14:58:46.852762Z'
  stage: doing
  run: 8116ca3895e9449ba2b32ab6fd93499d
- number: 15
  speaker: factory
  kind: started
  at: '2026-10-18T14:59:06.607097Z'
  stage: review
- number: 16
  speaker: reviewer
  kind: result
  at: '2026-10-18T15:00:36.301916Z'
  stage: review
  run: 82e80387197d4f718ebc5ebd8aef5c37
- number: 17
  speaker: factory
  kind: started
  at: '2026-10-18T15:00:56.854893Z'
  stage: doing
- number: 18
  speaker: coder
  kind: result
  at: '2026-10-18T15:01:16.143712Z'
  stage: doing
  run: 1c4f9960192b4b2ebe6f24c20e501429
- number: 19
  speaker: factory
  kind: started
  at: '2026-10-18T15:01:36.150704Z'
  stage: tests
- number: 20
  speaker: tester
  kind: result
  at: '2026-10-18T15:03:31.195086Z'
  stage: tests
  run: 84e26c4f33e249988e003a3b7a65f293
---

# `factory-confine` starts a command with its writes confined

## Description

The kernel's restriction (S0001) must be applied after `sudo` has made the process the agent's user, because Landlock needs `no_new_privs`, which `sudo` itself cannot run under, and before the runtime starts, so that the runtime and everything it starts inherit it. This story builds that step: the wrapper `factory-confine --rules <file> -- <command> [<argument>...]`, a console script (the human's change 1) in `factory.entry.confine`. It reads the rules of one run from a JSON file (the new domain model `Confinement`: folders, files and the run's own temporary folder), checks the kernel's ABI, makes the missing folders of its rules, makes the temporary folder with mode `0700`, restricts its writes to the folders, the files and the temporary folder, sets `TMPDIR` to the temporary folder and replaces itself with the command through `replace_process`, a new function of the one process module (`os.execvpe`), so that the command keeps the wrapper's process and process group. Every fault before the replacement is one line starting `factory-confine:` on standard error and exit status 1, and the command never starts (fail closed, feature decision 5). Nothing starts the wrapper yet: the runtime does in S0004. The hook and the undo stay as they are.

## Interface

`factory.domain.agent_runs` (`domain`):

```python
CONFINE_COMMAND = "factory-confine"
```

`factory.domain.confinement` (`domain`):

```python
class Confinement(BaseModel):
    """The writes one agent run may make: folders, single files and its own temporary folder."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folders: list[AbsolutePath]
    files: list[AbsolutePath]
    temporary_directory: AbsolutePath
```

- `AbsolutePath` is the one of `factory.domain.agent_runs`: a relative path in any field is a `ValidationError`.

`factory.adapters.process` (`adapters`):

```python
def replace_process(argv: Sequence[str], env: Mapping[str, str]) -> NoReturn:
    """Replace this process with `argv`, its program found on the `PATH` of `env`."""
```

- It calls `os.execvpe(argv[0], list(argv), dict(env))`, the one `exec` of the package, with `# noqa: S606  # nosec B606` on that line (the human's change 2) and no other marker. An empty `argv` raises `ValueError`; a program that cannot be started raises the `OSError` of `os.execvpe` (`FileNotFoundError` for one not on the `PATH`), and the process is then not replaced.

`factory.entry.confine` (`entry`, new module; the console script `factory-confine`):

```python
def main(
    argv: Sequence[str] | None = None,
    *,
    stderr: TextIO | None = None,
    abi: Callable[[], int] | None = None,
) -> int:
    """Confine this process's writes to the rules, then become the command; 1 when it cannot."""
```

- `argv` defaults to `sys.argv[1:]`, `stderr` to `sys.stderr`, `abi` to `factory.adapters.landlock.abi_version`. The module ends with `if __name__ == "__main__": raise SystemExit(main())`.
- The arguments must be exactly `--rules`, a file, `--`, and at least one word of the command; anything else writes `factory-confine: usage: factory-confine --rules <file> -- <command> [<argument>...]` and returns 1.
- The steps, in this order; each fault writes one line and returns 1, and no later step runs:
  1. The rules: the file read as UTF-8 and validated as `Confinement`; an `OSError`, a `UnicodeDecodeError` or a `ValidationError` is `f"factory-confine: cannot read the rules {file}: {fault}"`, the fault a single line (the error's text with line breaks replaced by spaces).
  2. The ABI: `abi_fault(abi())` from `factory.domain.confinement`; a fault is `f"factory-confine: {fault}"`.
  3. Every path of `folders` that does not exist is made with its parents (`Path.mkdir(parents=True, exist_ok=True)`); an `OSError` is `f"factory-confine: cannot make the folder {path}: {error.strerror}"`.
  4. The temporary folder is made with `os.mkdir(path, 0o700)`, never with `exist_ok`; an `OSError`, `FileExistsError` among them, is `f"factory-confine: cannot make the temporary folder {path}: {error.strerror}"`.
  5. `restrict_writes([*folders, temporary_directory], files)`; a `ConfinementError` is `f"factory-confine: {error.detail}"`.
  6. `replace_process(command, {**os.environ, "TMPDIR": str(temporary_directory)})`; an `OSError` is `f"factory-confine: cannot start {command[0]}: {error.strerror}"`.
- On success `main` does not return: the command's exit status, output and environment are its own, with `TMPDIR` set and every other variable as the wrapper had it.

Tests (the tester writes them): `tests/domain/test_confinement_model.py`, `tests/adapters/test_process_replace.py`, `tests/entry/test_confine.py`. A row that reaches step 5 or 6 starts the wrapper in a child process (`sys.executable -m factory.entry.confine ...`, or the installed `factory-confine`), never in the pytest worker; a row that ends at steps 1 to 4 may call `main` in-process with `abi` injected and `stderr` an `io.StringIO`. A test of `replace_process` that succeeds runs it in a child. Changed under the feature's decision 7, by the tester only: `tests/test_process_search.py` (the tests `test_no_module_uses_another_route_to_a_process` and `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper`) and `tests/test_wrapper_search.py` (the test `test_only_the_three_wrappers_import_the_process_module`).

## Acceptance criteria

1. A `Confinement` with absolute paths in all three fields validates; one with a relative path in `folders`, in `files` or in `temporary_directory` raises `ValidationError` (rows of one parametrized test).
2. `replace_process(["sh", "-c", "echo $X; exit 7"], {"X": "replaced", "PATH": "/usr/bin:/bin"})` in a child process prints `replaced` and the child exits 7; in-process, `replace_process(["no-such-program"], {"PATH": str(tmp_path)})` raises `FileNotFoundError` and `replace_process([], {"PATH": "/usr/bin:/bin"})` raises `ValueError`, and the test goes on (rows of one parametrized test).
3. A command started through the wrapper with rules of a folder A, an existing file F in a folder P and a temporary folder T under `tmp_path`, each attempt a row of one parametrized test (`sh -c <attempt>` as the command, one child per row): a new file in A exits 0; an append to F exits 0; a new file in `$TMPDIR` exits 0; a new file in P exits non-zero with `Permission denied` on its standard error; a new file in `tmp_path` exits non-zero with `Permission denied`; a process the command starts (`sh -c 'sh -c "echo x > <tmp_path>/c"'`) cannot create `<tmp_path>/c`.
4. The command sees `TMPDIR` equal to T, T is a folder of mode `0o700` while it runs, and a variable set for the wrapper (`EXTRA=kept`) reaches it unchanged.
5. The wrapper's exit status and standard output are the command's: `sh -c 'echo out; exit 7'` through the wrapper prints `out` and exits 7.
6. A folder of the rules that does not exist is made with its parents before the command starts, and one that cannot be made stops the wrapper (rows of one parametrized test, one child per row): with the folder `tmp_path/new/deeper`, the command writes a new file in it and exits 0, and a command that writes a new file in `tmp_path/new` exits non-zero with `Permission denied`; with the folder `<tmp_path>/f/sub`, where `f` is a file, the wrapper exits 1 with `factory-confine: cannot make the folder <tmp_path>/f/sub: Not a directory`, the command does not run and the temporary folder is not made.
7. Each of these argument lists makes `main` return 1 and write exactly `factory-confine: usage: factory-confine --rules <file> -- <command> [<argument>...]` plus a line break, and the command (`touch <tmp_path>/ran`, where one is given) does not run: `[]`, `["--rules"]`, `["--rules", f]`, `["--rules", f, "--"]`, `["--", "touch", m]`, `["--rules", f, "touch", m]`, `["--settings", f, "--", "touch", m]` (rows of one parametrized test).
8. A rules file that does not exist, one that is not UTF-8 (the bytes `b"\xff\n"`), one that is not JSON, one that is JSON with a relative path, and one with an unknown key each make `main` return 1 with one line that starts `factory-confine: cannot read the rules <file>: `, and the temporary folder is not made (rows of one parametrized test).
9. With `abi` returning 0 or 2, `main` returns 1 and writes `factory-confine: the kernel offers Landlock ABI 0, the write guard needs ABI 3 or higher` or `... ABI 2, ...` respectively, and neither the missing folders nor the temporary folder are made (rows of one parametrized test); with the kernel's real ABI (7 in v1.1's container) the wrapper started in a child runs its command (criterion 3).
10. A temporary folder that already exists, as a folder or as a symbolic link, makes `main` return 1 with `factory-confine: cannot make the temporary folder <T>: File exists`, and the command does not run (rows of one parametrized test).
11. In a child, rules naming a file of `files` that does not exist make the wrapper exit 1 with `factory-confine: cannot open <path>: No such file or directory` and rules naming a symbolic link in `folders` with `factory-confine: <path> is a symbolic link`; the command does not run (rows of one parametrized test).
12. In a child, the command `no-such-program` makes the wrapper exit 1 with `factory-confine: cannot start no-such-program: No such file or directory`.
13. The console script `factory-confine` is installed beside `sys.executable`, and started without arguments it exits 1 with the usage line on its standard error.
14. The structural tests hold with the leave of the feature's decision 7: the only route to a process outside `subprocess.Popen` is `os.execvpe` in `factory.adapters.process`; the only suppression markers of the package are the four of the process module and `noqa: S606` with `nosec B606` on its one `os.execvpe` line; the modules that import `factory.adapters.process` are `factory.adapters.git_cli`, `factory.adapters.make_commands`, `factory.adapters.claude_runtime` and `factory.entry.confine`.
15. `make check` stays green.
16. docs: `docs/project-guide.md`, section *Starting a process*, names `replace_process` as the one `exec` and why (the wrapper becomes the runtime, so `timeout`'s and the factory's kills of the process group still reach it), and its paragraph on `tests/test_process_search.py` names `os.execvpe` in `process.py` as the one exception and the six markers there, and a new section *The start wrapper* after *The kernel's write guard* describes `factory-confine`: its arguments, the rules file (`Confinement`), its six steps in order, the fault lines and exit status 1, that the command never starts after a fault, and `TMPDIR`. `README.md`'s list of commands and `docs/operator-guide.md`'s list of commands name `factory-confine` beside `factory-guard` as one the agent runtime runs (it starts every agent run once the runtime uses it, S0004). `docs/decisions.md` gets an entry *factory-confine replaces itself with the runtime*, dated 2026-10-18 (F0019-S0002), with the reasons of the feature's decision 5 and the widened exception in `CLAUDE.md`.

## Smoke test

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/allowed" "$d/other"
printf '{"folders": ["%s/allowed"], "files": [], "temporary_directory": "%s/run"}\n' "$d" "$d" > "$d/rules.json"
uv run -q factory-confine --rules "$d/rules.json" -- sh -c '
echo a > "$1/allowed/a.txt" && echo "allowed written"
out=$( { echo b > "$1/other/b.txt"; } 2>&1 ) || case "$out" in *"Permission denied"*) echo "other refused" ;; esac
[ "$TMPDIR" = "$1/run" ] && [ -d "$TMPDIR" ] && echo "own temporary folder"
' sh "$d"
```
Expect: three lines, `allowed written`, `other refused` and `own temporary folder`

```bash
uv run -q factory-confine -- true 2>&1; echo "status $?"
```
Expect: two lines, `factory-confine: usage: factory-confine --rules <file> -- <command> [<argument>...]` and then `status 1`

```bash
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
mkdir "$d/run"
printf '{"folders": [], "files": [], "temporary_directory": "%s/run"}\n' "$d" > "$d/rules.json"
uv run -q factory-confine --rules "$d/rules.json" -- echo started 2>&1 | sed "s|$d|<d>|g"
```
Expect: `factory-confine: cannot make the temporary folder <d>/run: File exists`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: names concrete modules and signatures (`factory.domain.agent_runs.CONFINE_COMMAND`, `factory.domain.confinement.Confinement`, `factory.adapters.process.replace_process`, `factory.entry.confine.main`). The pieces it builds on exist as described: `AbsolutePath` in `agent_runs`, `abi_fault`, `ConfinementError.detail`, `abi_version` and `restrict_writes` with the "cannot open" and "is a symbolic link" texts, and the `factory-confine` script line in `pyproject.toml` and the widened `CLAUDE.md` exception (the human's changes 1 and 2).
   Criteria: each is testable by one parametrized test function. Every Interface clause has a criterion on both sides: usage (7), rules file faults (8), ABI (9), folder creation and its failure (6), temporary folder with `0700` and `FileExistsError` (4, 10), `ConfinementError` (11), `OSError` on start (12), `replace_process` success, `FileNotFoundError` and `ValueError` (2), and exit status, output and `TMPDIR` (4, 5). The step order is pinned by the "not made" clauses in 8 and 9.
   Smoke test: three runnable blocks. Each `Expect:` line can be checked against the output.
   Architecture: the model is in domain, `replace_process` in the one process module, and the wrapper in entry, which imports adapters and domain. This is consistent with the layers and wrapper rules, and the structural-test changes are covered by criterion 14 and decision 7.
   Scope: within F0019 S0002's scope list. Nothing from Out of scope is touched. The runtime wiring is left to S0004.
4. factory: started tests as self.
5. tester: Wrote the tests for criteria 1 to 14. Rows that reach step 5 or 6 start the wrapper in a child (`sys.executable -m factory.entry.confine`). Rows that end at steps 1 to 4 call `main` in-process with `abi` injected and `stderr` set to a `StringIO`. The usage and rules-file rows inject ABI 0, so a wrapper that wrongly goes on still stops before it restricts the pytest worker.

   criterion 1: tests/domain/test_confinement_model.py::test_a_relative_path_in_any_field_is_refused
   criterion 2: tests/adapters/test_process_replace.py::test_replace_process_becomes_the_command_with_the_given_environment (child, prints `replaced`, exits 7) and ::test_replace_process_that_cannot_start_raises_and_this_process_goes_on (in-process rows `FileNotFoundError` and `ValueError`)
   criterion 3: tests/entry/test_confine.py::test_the_command_writes_only_within_the_rules
   criterion 4: tests/entry/test_confine.py::test_the_command_gets_its_own_temporary_folder_and_the_wrapper_environment
   criterion 5: tests/entry/test_confine.py::test_the_wrapper_exits_and_prints_as_the_command
   criterion 6: tests/entry/test_confine.py::test_a_missing_folder_of_the_rules_is_made_or_stops_the_wrapper
   criterion 7: tests/entry/test_confine.py::test_wrong_arguments_print_the_usage_and_return_1
   criterion 8: tests/entry/test_confine.py::test_rules_that_cannot_be_read_return_1_with_one_line
   criterion 9: tests/entry/test_confine.py::test_a_kernel_below_abi_3_stops_the_wrapper_before_any_folder_is_made (ABI 0 and 2); the real-ABI half is covered by the criterion 3 test
   criterion 10: tests/entry/test_confine.py::test_an_existing_temporary_folder_stops_the_wrapper
   criterion 11: tests/entry/test_confine.py::test_a_rule_the_kernel_cannot_take_stops_the_wrapper
   criterion 12: tests/entry/test_confine.py::test_a_command_that_cannot_start_stops_the_wrapper
   criterion 13: tests/entry/test_confine.py::test_the_console_script_beside_the_interpreter_prints_the_usage
   criterion 14: tests/test_process_search.py::test_no_module_uses_another_route_to_a_process and ::test_the_only_suppression_markers_are_the_four_in_the_process_wrapper; tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module

   Files created: tests/domain/test_confinement_model.py, tests/adapters/test_process_replace.py, tests/entry/test_confine.py.

   Earlier test files changed under the leave of the feature's decision 7, which the Interface names:
   - tests/test_process_search.py: the expected routes are now `{"factory.adapters.process": {"os.execvpe"}}`, and the expected markers add `noqa: S606`/`nosec B606` on the `os.execvpe(` line.
   - tests/test_wrapper_search.py: `factory.entry.confine` is added to the importers.

   All test names are unchanged.

   The test run could not import `factory.domain.confinement.Confinement`, `factory.adapters.process.replace_process` or `factory.entry.confine`, so the three new modules fail at collection. The structural tests fail, as they should until the code exists. `make lint` is green.

   Not tested, because no criterion names it: the constant `CONFINE_COMMAND` in `factory.domain.agent_runs`.

   Open: nothing.

   `lint`: lint: green (0.0 s)
   `test`: ERROR tests/entry/test_confine.py - ImportError while importing test module '...
6. factory: started doing as self.
7. coder: Two tests contradict each other, so `make check` cannot go green. Which one should change?

   - `tests/test_wrapper_search.py::test_only_the_three_wrappers_import_the_process_module` was changed by the tester under decision 7. Criterion 14 and the Interface back it. It requires `factory.entry.confine` to import `factory.adapters.process` directly.
   - `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` is an earlier story's test. It requires that `factory.entry.wiring` is the only entry module importing anything from `factory.adapters`. So `factory.entry.confine` must not import `factory.adapters.process` or `factory.adapters.landlock`.

   No import layout satisfies both. Decision 7 gave leave to change only `tests/test_process_search.py` and `tests/test_wrapper_search.py`, not `tests/test_wiring.py`.

   Options:
   A) The tester widens `test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` to expect `{"factory.entry.wiring", "factory.entry.confine"}`. The start wrapper then imports `landlock` and `process` directly, as the Interface and criterion 14 say. Its justification: the wrapper picks no adapter behind an interface. It is itself the process-level step before `exec`.
   B) `factory.entry.confine` takes `abi_version`, `restrict_writes` and `replace_process` through `factory.entry.wiring`, as `factory.entry.guard` takes `judge` and `read_guard_settings`. The tester changes `test_only_the_three_wrappers_import_the_process_module` to expect `factory.entry.wiring` in place of `factory.entry.confine`, and criterion 14 changes with it. This follows the guard's precedent and the "nothing else wires" rule in `CLAUDE.md`. But it makes the wiring module an importer of the process module.

   I would choose A. It keeps criterion 14 and the Interface as written, and changes one line of one test. After your answer I end with `tests` and name that change.

   Where I stopped: the implementation is complete in the working tree, following option A's layout. The three new test files, `tests/test_process_search.py` and `tests/test_wrapper_search.py` all pass. `make lint`, `make types`, `make layers`, `make sast`, `make secrets` and `make licenses` are green. `make test` fails only on the `test_wiring` test above.

   What I built:
   - `src/factory/domain/agent_runs.py`: `CONFINE_COMMAND`.
   - `src/factory/domain/confinement.py`: the model `Confinement`, using the `AbsolutePath` of `agent_runs`.
   - `src/factory/adapters/process.py`: `replace_process`. An empty `argv` raises `ValueError` before `os.execvpe`. Without that check, `argv[0]` would raise `IndexError`. The one marker line is `# noqa: S606  # nosec B606`.
   - `src/factory/entry/confine.py`: `main`, with the six steps in order.

   Main choice: each fault raises a private `_Stop` exception that carries its line, and `main` writes it once and returns 1. I rejected returning a status code from every step, which would repeat the write-and-return at each of the six faults.

   Not touched: `src/factory/entry/confine.py` has 78% coverage, because the rows that reach steps 5 and 6 run in a child that coverage does not follow. The total coverage is still 98.6%.

   No refactor pass yet; it waits until `make check` is green.
8. 2026-10-18 human: A. You have my leave: the tester widens `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` to expect `{"factory.entry.wiring", "factory.entry.confine"}`, that one line and nothing else. The start wrapper imports `factory.adapters.landlock` and `factory.adapters.process` directly, as the Interface and criterion 14 say: it picks no adapter behind an interface; it is the process-level step before `exec`. Recorded as feature decision 19 (on main). End with `tests` naming that change.
9. factory: started doing as self.
10. coder: The human chose A in entry 8, so this goes to the tester for one change. In `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`, change the line `assert importers == {"factory.entry.wiring"}` to `assert importers == {"factory.entry.wiring", "factory.entry.confine"}`. Change that one line and nothing else.

    What I built is already committed on the branch, as entry 7 describes:
    - `src/factory/domain/agent_runs.py`: `CONFINE_COMMAND`.
    - `src/factory/domain/confinement.py`: the model `Confinement`.
    - `src/factory/adapters/process.py`: `replace_process`, with the one `# noqa: S606  # nosec B606` line.
    - `src/factory/entry/confine.py`: `main`, which runs the six steps in order. `confine` imports `factory.adapters.landlock` and `factory.adapters.process` directly, as the human's answer allows.

    Main choice: each fault raises a private `_Stop` exception that carries its line, and `main` writes that line once and returns 1. I rejected having every step return a status, which would repeat the write-and-return at each of the six faults.

    Open: when the tester sends the work item back, the next doing run checks that `make check` is green and does the refactor pass. Neither has happened yet; this run changed no code.

    Noticed, not touched: `src/factory/entry/confine.py` is at 78% coverage, because the rows that reach steps 5 and 6 run in a child process that coverage does not follow. Total coverage stays above 90%.
11. factory: started tests as self.
12. tester: I made the one test change the human approved in entry 8 and the coder named in entry 10. In `tests/entry/test_wiring.py::test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer` (line 21), `assert importers == {"factory.entry.wiring"}` is now `assert importers == {"factory.entry.wiring", "factory.entry.confine"}`. The reason: the start wrapper imports `factory.adapters.landlock` and `factory.adapters.process` directly (feature decision 19).

    Nothing else changed: no other line, no test name and no other file. I created no files.

    I ran `make test` once and it was green, with total coverage at 98.64%. The run could import every module.

    Open: the coder's refactor pass and `make check`.

    `lint`: lint: green (0.0 s)
    `test`: test: green (43.3 s)
13. factory: started doing as self.
14. coder: `make check` is green: 98.64% total coverage, ending in `check: green`. In this run I checked the build and did the one refactor pass the earlier runs still owed. I changed no code: the diff against `main` reads cleanly, with no unclear name, no duplication and no dead code.

    What I built, committed on the branch since entry 7:
    - `src/factory/domain/agent_runs.py`: the constant `CONFINE_COMMAND`.
    - `src/factory/domain/confinement.py`: the model `Confinement` (folders, files, temporary directory), using the `AbsolutePath` of `agent_runs`.
    - `src/factory/adapters/process.py`: `replace_process`. It raises `ValueError` on an empty `argv` before calling `os.execvpe`; otherwise `argv[0]` would raise `IndexError`. Its exec line carries the only marker, `# noqa: S606  # nosec B606`.
    - `src/factory/entry/confine.py`: `main` with the six steps in the order the Interface gives (arguments, rules, ABI, folders, the temporary folder with mode `0o700` and no `exist_ok`, `restrict_writes`, then `replace_process` with `TMPDIR` set). It imports `factory.adapters.landlock` and `factory.adapters.process` directly, as the human allowed in entry 8 (feature decision 19).

    Main choice: each fault raises a private `_Stop` exception that carries its line, and `main` writes that line once and returns 1. I rejected having every step return a status, which would repeat the write-and-return at each of the six faults.

    What the journal changed: the human's answer in entry 8 changed only `tests/entry/test_wiring.py`, through the tester. The task's meaning is the same, so I left `## Description` as it is.

    Noticed, not touched: `src/factory/entry/confine.py` is at 78% coverage and `src/factory/adapters/landlock.py` at 35%. The tests that reach the restriction and the exec run in a child process, and coverage does not follow it there. The total is still above 90%.

    `check`: check: green
    `duplicates`: duplicates: 1 new, 36 known, 3 gone
15. factory: started review as self.
16. reviewer: 1. `tests/adapters/test_process_replace.py:17` and `:32`: criterion 2 ends with "(rows of one parametrized test)", but its success side (the child prints `replaced` and exits 7) is in its own test function, `test_replace_process_becomes_the_command_with_the_given_environment`. The two refused sides (`FileNotFoundError` and `ValueError`) are rows of a second function, so the sides of `replace_process`'s one rule are split across two functions. Fix: the coder ends with `tests`, and the tester merges the two into one parametrized test with three rows. The success row runs in a child; the two refused rows run in-process and the test goes on afterwards.

    What I checked: every criterion from 1 to 14 against its test, and every failing side of the Interface. That covers the usage rows, the rules-file faults (including the check that the fault is one line), the ABI, the folder and temporary-folder faults, `ConfinementError`, and the `OSError` when the command cannot start. They all exist and test what their criterion says. The ABI boundary at 3 is also tested on both sides in `tests/domain/test_confinement_abi.py`. The architecture holds: `factory.entry.confine` imports the adapters directly, which feature decision 19 (entry 8) allows. On security, the only new markers are `# noqa: S606  # nosec B606` on the one `os.execvpe` line in `src/factory/adapters/process.py`, which is the exception `CLAUDE.md` allows; the `# noqa: S603` in the tests carries a reason beside it, as earlier tests do. The code matches the six steps in order. Entry 14 records `make check` green.

    Not a finding: `make duplicates` reports one new dead-code record, the unused `CONFINE_COMMAND` in `src/factory/domain/agent_runs.py:27`. The Interface asks for it, and S0004 uses it.

    Earlier tests:
    - `tests/test_process_search.py`: covered by the human's leave. The story names `test_no_module_uses_another_route_to_a_process` and `test_the_only_suppression_markers_are_the_four_in_the_process_wrapper` under feature decision 7, and the change stays inside those two tests.
    - `tests/test_wrapper_search.py`: covered by the human's leave. The story names `test_only_the_three_wrappers_import_the_process_module` under feature decision 7; the change adds one importer.
    - `tests/entry/test_wiring.py`: covered by the human's leave, the answer in journal entry 8. It is the one-line change to `test_only_the_wiring_imports_from_the_adapters_in_the_entry_layer`.
17. factory: started doing as self.
18. coder: Round 1 has one review finding (entry 16), and it is a change to a test, so this goes to the tester.

    The change: in `tests/adapters/test_process_replace.py`, merge `test_replace_process_becomes_the_command_with_the_given_environment` (line 17) and `test_replace_process_that_cannot_start_raises_and_this_process_goes_on` (line 32) into one parametrized test with three rows:
    - The success row runs `CHILD` in a child through `sys.executable -c` and expects `("replaced\n", 7)` as stdout and exit status.
    - The `not-on-the-path` row calls `replace_process(["no-such-program"], {"PATH": str(tmp_path)})` in-process and expects `FileNotFoundError`; the test goes on afterwards.
    - The `empty-argv` row calls `replace_process([], {"PATH": "/usr/bin:/bin"})` in-process and expects `ValueError`; the test goes on afterwards.

    Nothing else changes. This test module belongs to this story (the tester wrote it in entry 5), so the merge does not need the human's leave.

    I changed no code in this run. What I built is already committed on the branch, as entry 14 describes:
    - `src/factory/domain/agent_runs.py`: `CONFINE_COMMAND`
    - `src/factory/domain/confinement.py`: `Confinement`
    - `src/factory/adapters/process.py`: `replace_process`
    - `src/factory/entry/confine.py`: `main`, which runs the six steps in order

    Main choice (unchanged from entry 14): each fault raises a private `_Stop` that carries its line, and `main` writes that line once and returns 1. I rejected having each step return a status, because that would repeat the write-and-return at all six faults.

    Open: when the tester sends the work item back, the next doing run confirms `make check` is green after the merge. No source change is expected.

    Noticed, not touched (as in entry 14): coverage is 78% for `src/factory/entry/confine.py` and 35% for `src/factory/adapters/landlock.py`, because the rows that restrict and exec run in a child that coverage does not follow. `CONFINE_COMMAND` is still unused until S0004, and `make duplicates` reports it as a new dead-code record.
19. factory: started tests as self.
20. tester: I made the one test change from the review finding in entry 16, as the coder named it in entry 18. In `tests/adapters/test_process_replace.py`, I merged `test_replace_process_becomes_the_command_with_the_given_environment` and `test_replace_process_that_cannot_start_raises_and_this_process_goes_on` into one parametrized test, `test_replace_process_becomes_the_command_or_raises_and_this_process_goes_on`. It has three rows:
    - `becomes-the-command`: runs `CHILD` in a child through `sys.executable -c` and expects `("replaced\n", 7)` as stdout and exit status.
    - `not-on-the-path`: calls `replace_process(["no-such-program"], {"PATH": str(tmp_path)})` in-process, expects `FileNotFoundError`, then checks that the test goes on.
    - `empty-argv`: calls `replace_process([], {"PATH": "/usr/bin:/bin"})` in-process, expects `ValueError`, then checks that the test goes on.

    Each row checks exactly what the two earlier functions checked; `CHILD` is unchanged. This module belongs to this story, so no leave was needed. I changed no other test or file and created no files.

    Criterion 2 now maps to `tests/adapters/test_process_replace.py::test_replace_process_becomes_the_command_or_raises_and_this_process_goes_on`. The other criteria's mappings are unchanged.

    `make lint` is green. I ran `make test` once and it was green, with total coverage at 98.64%. The run could import every module.

    Open: the coder's next doing run confirms `make check` is green, which includes the type check of this test.

    `lint`: lint: green (0.0 s)
    `test`: test: green (43.2 s)
