---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 233
comments_read: []
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T20:37:14.085991Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T20:37:14.090747Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T20:37:33.638481Z'
  stage: intake
  run: 8fb816ce160042119d7fb33b78b84cad
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T20:37:53.405668Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T20:41:07.114164Z'
  stage: tests
  run: 6e76e23795d64ee9bc45f5b3a8b1a27f
---

# The guard's refusals before its irreversible calls run in the test process

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

F0019's second `make mutants` still shows mutants that no test in the test process reaches: 144 in `factory.adapters.landlock` with no test at all, 15 survivors in `factory.entry.confine` and 4 in `factory.adapters.process.replace_process`. S0009 brought `factory-confine`'s steps into the test process with `restrict` and `replace` injected. But every row that checks a refused rule path runs in a child process (`tests/adapters/test_landlock.py`). The same holds for the wrapper's own defaults, its existing-folder and folder-fault paths and the text of an unreadable rules file. So the following would go unnoticed:
- `landlock._check_path` dropped or inverted;
- `main`'s defaults (`sys.argv[1:]`, `sys.stderr`, `abi_version`, `restrict_writes`, `replace_process`) never used;
- `exist_ok=True` dropped for a folder that already exists;
- the fault of an unreadable rules file replaced by `None`;
- the folder fault's text dropped;
- `replace_process` passing no environment, which searches the factory's own `PATH`;
- its `ValueError` text changed.

Each of these paths ends in a refusal before the first Landlock system call or before the `exec`, so it can run in the test process. Every in-process row names a path that cannot be opened (missing, or a link to a missing target) or a program that cannot run. So even with a check broken, `landlock_add_rule` or the `exec` fails before anything binds the pytest worker. No module under `src/factory/` is expected to change. The child-process tests stay as the check against the real kernel. The system calls themselves (`_create_ruleset`, `_add_rule`, `_restrict_self`) stay child-only (decision 18).

## Interface

No module under `src/factory/` is expected to change. The pinned behaviour:

- `factory.adapters.landlock.restrict_writes(folders, files)` (`adapters`): every path is checked before the first system call, folders first, each list in its order. A missing path is `cannot open <path>: No such file or directory`, a link (also one to a missing target) is `<path> is a symbolic link`, a file among the folders is `<path> is not a folder`, a folder among the files is `<path> is a folder`. The first failing path names the `ConfinementError`.
- `factory.adapters.process.replace_process(argv, env)` (`adapters`): an empty `argv` raises `ValueError("replace_process needs a program to start")`. The program is searched on the `PATH` of `env`, not on the process's own.
- `factory.entry.confine.main(argv=None, *, stderr=None, abi=None, restrict=None, replace=None)` (`entry`): `None` is `sys.argv[1:]`, `sys.stderr`, `abi_version`, `restrict_writes` and `replace_process`, each read at the call. A folder of the rules that already exists is no fault. The fault of an unreadable rules file is the error's text with each line break replaced by one space.

Test modules (new): `tests/adapters/test_landlock_checks.py`, `tests/adapters/test_process_replace_faults.py`, `tests/entry/test_confine_defaults.py`. They call the functions in the test process. `tests/adapters/test_landlock.py`, `tests/adapters/test_process_replace.py`, `tests/entry/test_confine.py` and `tests/entry/test_confine_steps.py` stay unchanged, but for helpers moved under the standing leave of `CLAUDE.md`.

## Acceptance criteria

1. `restrict_writes` in the test process, in a tree with a folder `A`, a file `P/f.txt`, a link `dangling` to a missing path and no `missing`, `missing.txt` or `absent.txt` (rows of one parametrized test; each raises `ConfinementError` with exactly this detail, `<base>` the tree):
   - folders `[missing]`: `cannot open <base>/missing: No such file or directory`.
   - files `[missing.txt]`: `cannot open <base>/missing.txt: No such file or directory`.
   - folders `[P/f.txt, missing]`: `<base>/P/f.txt is not a folder`.
   - files `[A, missing.txt]`: `<base>/A is a folder`.
   - folders `[dangling]`: `<base>/dangling is a symbolic link`.
   - files `[dangling]`: `<base>/dangling is a symbolic link`.
   - folders `[missing]` and files `[missing.txt]`: the folder's text.
   - folders `[missing, absent]`: `missing`'s text. Files `[missing.txt, absent.txt]`: `missing.txt`'s text.
   After each row, a file written by the test process in `<base>/A` succeeds.
2. `replace_process` in the test process (rows of one parametrized test):
   - `argv` `[]`: `ValueError` with exactly `replace_process needs a program to start`.
   - `argv` `["factory-test-prog"]`, with `env` `{"PATH": <tmp>/bin}` where `<tmp>/bin/factory-test-prog` is a file without the execute bit, and no such program on the test process's `PATH`: `PermissionError`.
   - The same `argv` with `env` `{"PATH": <tmp>/empty}`: `FileNotFoundError`.
3. `main`'s defaults (rows of one parametrized test, each with `capsys` reading standard error):
   - `argv` `None`, with `sys.argv` `["factory-confine", "--rules", <missing file>, "--", "prog"]` (`monkeypatch`) and `stderr` `None`: returns 1, and standard error is `factory-confine: cannot read the rules <missing file>: [Errno 2] No such file or directory: '<missing file>'\n`.
   - `argv` `None`, with `sys.argv` `["factory-confine"]`: returns 1, and standard error is the usage line.
   - `abi` `None`, with valid rules and `restrict` and `replace` injected: `restrict` is called once (the kernel's own ABI is 3 or higher).
   - `restrict` `None`, with rules whose files are `[<tmp>/missing.txt]` and `replace` injected: returns 1, standard error is `factory-confine: cannot open <tmp>/missing.txt: No such file or directory\n`, and `replace` is never called.
   - `replace` `None`, with `restrict` injected and the command `[<tmp>/no-such-program]`: returns 1, and standard error is `factory-confine: cannot start <tmp>/no-such-program: No such file or directory\n`.
4. The wrapper's folders, in the test process with `restrict` and `replace` injected (rows of one parametrized test):
   - A folder of the rules that already exists, `<tmp>/A`: `restrict` gets it, and nothing is written to `stderr`.
   - A folder `<tmp>/f/sub`, where `<tmp>/f` is a file: returns 1, `stderr` is exactly `factory-confine: cannot make the folder <tmp>/f/sub: Not a directory\n`, and `restrict` is never called.
5. An unreadable rules file, in the test process (rows of one parametrized test):
   - A missing file: the line is exactly `factory-confine: cannot read the rules <file>: [Errno 2] No such file or directory: '<file>'\n`.
   - A file holding `not json`: the line is `factory-confine: cannot read the rules <file>: ` followed by the text of the `ValidationError` that `Confinement.model_validate_json("not json\n")` raises, each line break replaced by one space, then `\n`.
6. `make check` stays green.
7. docs:
   - `docs/project-guide.md`, *The kernel's write guard*: the paragraph on its tests says that the refusals before the first system call also run in the test process, with a path that cannot be opened in every row, and that the system calls themselves run only in child processes.
   - *The start wrapper*: its tests paragraph names the in-process rows for the defaults, the folders and the rules file's fault.
   - No other document changes.

## Smoke test

```bash
uv run -q python -c '
import tempfile
from pathlib import Path
from factory.adapters.landlock import restrict_writes
from factory.domain.errors import ConfinementError
with tempfile.TemporaryDirectory() as d:
    base = Path(d); (base / "dangling").symlink_to(base / "nowhere")
    try:
        restrict_writes([base / "dangling"], [])
    except ConfinementError as error:
        print(str(error).replace(d, "<base>"))
    (base / "after.txt").write_text("x"); print("still writes")
'
```
Expect: `<base>/dangling is a symbolic link`, then `still writes`

```bash
uv run -q python -c '
from factory.adapters.process import replace_process
try:
    replace_process([], {})
except ValueError as error:
    print(error)
'
```
Expect: `replace_process needs a program to start`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   - Interface: names concrete functions and signatures (`restrict_writes`, `replace_process`, `confine.main` with its keyword parameters) and three new test modules. It states that no `src/factory/` module changes, and that matches the criteria, which only pin behaviour already there.
   - Criteria: each one fits a parametrized test with exact strings. Every Interface rule has both sides. The check order has rows: folders before files, and each list in its order. Each of the four fault texts has a row. The `argv` empty / `PATH`-of-`env` clauses are covered by the PermissionError and FileNotFoundError rows. Every `main` default has a row. An existing folder (no fault) and an unmakeable folder (fault) both have rows. The rules-file fault has rows for a missing file and for invalid JSON. The usage line is the existing `_USAGE` in `src/factory/entry/confine.py`, so the tester can read it.
   - Smoke test: both commands run as written. Their `Expect:` lines are exact output: the `<base>`-substituted refusal text then `still writes`, and the `ValueError` text.
   - Architecture: tests only, in the layer-mirroring folders (`tests/adapters`, `tests/entry`). The system calls stay child-only, as decision 18 says. The tests need no change to an earlier test beyond the standing leave for shared helpers.
   - Scope: the story stays inside F0019's testing of the guard and is consistent with decisions 18 and 22. Nothing in it falls under the feature's Out of scope list.
4. factory: started tests as self.
5. tester: Wrote the in-process tests for the guard's refusals. All of them pass now, because they pin behaviour that already exists and no module under `src/factory/` is expected to change. So there are no red tests for the coder this time. The coder's task is to keep `make check` green, including `make types` over the new tests. I did not run that in this stage.

   - criterion 1: tests/adapters/test_landlock_checks.py::test_a_path_that_cannot_be_ruled_is_refused_and_restricts_nothing (nine rows: missing folder, missing file, file among folders, folder among files, dangling link as folder and as file, folders before files, folders in order, files in order; each checks `ConfinementError.detail` exactly, then writes `<base>/A/after.txt` in the test process)
   - criterion 2: tests/adapters/test_process_replace_faults.py::test_replace_process_refuses_in_the_test_process_on_the_path_of_env (rows: empty argv gives ValueError with the exact text; `factory-test-prog` without the execute bit on env's PATH gives PermissionError; an empty folder on env's PATH gives FileNotFoundError; each row asserts the program is not on the test process's own PATH)
   - criterion 3: tests/entry/test_confine_defaults.py::test_main_left_its_defaults_uses_sys_argv_sys_stderr_and_the_adapters (rows argv, argv-usage, abi, restrict, replace; capsys reads stderr, every row leaves `stderr` None. The abi row has replace raise ENOENT and checks calls == ["restrict", "replace"], so restrict ran once.)
   - criterion 4: tests/entry/test_confine_defaults.py::test_a_folder_of_the_rules_that_exists_is_no_fault_and_one_under_a_file_stops_the_wrapper (rows existing-folder, under-a-file)
   - criterion 5: tests/entry/test_confine_defaults.py::test_rules_that_cannot_be_read_are_one_line_with_the_errors_text (rows missing, not-json; the not-json row computes the expected text from `Confinement.model_validate_json("not json\n")` with each "\n" replaced by one space)
   - criteria 6 and 7: not tested here (`make check`, docs).

   Files created: tests/adapters/test_landlock_checks.py, tests/adapters/test_process_replace_faults.py, tests/entry/test_confine_defaults.py.

   I moved shared helpers under the standing leave in CLAUDE.md (*Tests*). The new tests would otherwise copy them. `USAGE`, `Replaced` and `Steps` came from tests/entry/test_confine_steps.py. `_rules` came from tests/entry/test_confine.py and is now `write_rules`, and `USAGE` was also a copy there. All of them now live in tests/confine_support.py. Earlier test files changed: tests/entry/test_confine_steps.py and tests/entry/test_confine.py. Only their imports and the helper's name changed; every test keeps its name and checks the same thing.

   Modules the test run could not import: none. `make test`: test: green. `make lint`: green.

   `lint`: lint: green (0.0 s)
   `test`: test: green (42.6 s)
