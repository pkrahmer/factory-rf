---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 221
comments_read: []
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
