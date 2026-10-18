---
stage: smoke-test
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 229
comments_read: []
handed_over: null
claim:
  instance: self
  stage: smoke-test
  started_at: '2026-10-18T19:43:37.314865Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T19:35:34.681665Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T19:35:34.686997Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T19:35:51.725051Z'
  stage: intake
  run: c1ace8f91b6048f88a055ef175a0dc58
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T19:36:11.594575Z'
  stage: tests
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T19:38:31.251108Z'
  stage: tests
  run: d3c4bffad1994515a8ac07399a64c3b2
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-18T19:38:51.427202Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-18T19:41:06.174485Z'
  stage: doing
  run: f43a412ab89343a58a361b4481305b8c
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-18T19:41:26.434410Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-18T19:41:56.522818Z'
  stage: review
  run: b8b72b47a87e47b4b35d24d965cf52b5
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-18T19:42:16.509322Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-18T19:43:17.396215Z'
  stage: docs
  run: 792ead386ee542458c0e8aa3da8e53ee
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-18T19:43:37.314865Z'
  stage: smoke-test
---

# factory-confine's steps run in the test process

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

F0019's `make mutants` left 36 survivors in `src/factory/entry/confine.py`, and its coverage is 78 %. Every row that reaches the restriction or the `exec` runs `factory-confine` in a child process that imports the unmutated package, as decision 18 foresaw. So mutmut and coverage never see steps 3 to 6. Breaking any of the following would go unnoticed:
- dropping the run's folders and its own temporary folder from the rules (`restrict_writes(None, rules.files)`);
- dropping the temporary folder's `0700` mode;
- dropping `parents=True`;
- refusing a one-word command (`len(arguments) <= 4`);
- dropping `TMPDIR` from the command's environment.

This story lets the test process run those steps with the two irreversible calls injected, the same way `main` already takes `abi`. `main` gains `restrict` and `replace`, which default to `restrict_writes` and `replace_process`, and the new in-process tests pass recorders. The existing child-process tests stay as the check against the real kernel. `factory.adapters.landlock` and `replace_process` stay child-only: their own calls cannot be undone in the test process. The wrapper's behaviour, texts and exit status do not change.

## Interface

`factory.entry.confine` (`entry`):

```python
def main(
    argv: Sequence[str] | None = None,
    *,
    stderr: TextIO | None = None,
    abi: Callable[[], int] | None = None,
    restrict: Callable[[Sequence[Path], Sequence[Path]], None] | None = None,
    replace: Callable[[Sequence[str], Mapping[str, str]], NoReturn] | None = None,
) -> int:
    """Confine this process's writes to the rules, then become the command; 1 when it cannot."""
```

- `restrict` `None` is `factory.adapters.landlock.restrict_writes`. `replace` `None` is `factory.adapters.process.replace_process`. The console script and `python -m factory.entry.confine` pass neither.
- The steps and their texts are unchanged (`docs/project-guide.md`, *The start wrapper*). `restrict` is called once, with `[*rules.folders, rules.temporary_directory]` and `rules.files` in their order, after every folder and the temporary folder exist and before `replace`. A `ConfinementError` from it is `factory-confine: <detail>`, and `replace` is never called.
- `replace` is called once, with the command and `{**os.environ, "TMPDIR": <temporary_directory>}`. An `OSError` from it is `factory-confine: cannot start <command>: <reason>`.

Test module (new): `tests/entry/test_confine_steps.py`. It calls `main` in-process with a recording `restrict` and a `replace` that records and raises a test-local exception. `tests/entry/test_confine.py` is unchanged.

## Acceptance criteria

1. With rules of a missing folder `<tmp>/a/b`, an existing file `<tmp>/f`, a missing temporary folder `<tmp>/t`, and the command `prog x`, `restrict` receives exactly `([<tmp>/a/b, <tmp>/t], [<tmp>/f])`. At that call `<tmp>/a/b` exists, and `<tmp>/t` exists with permission bits `0o700`.
2. In the same run, `replace` receives `["prog", "x"]` and an environment equal to the test process's environment plus `TMPDIR=<tmp>/t`. It is called after `restrict`, and `restrict` is called once.
3. Argument count (rows of one parametrized test): `--rules <file> -- prog`, the four-argument form, reaches `replace` with `["prog"]`. `--rules <file> --`, three arguments, writes the usage line, returns 1 and calls neither `restrict` nor `replace`.
4. Faults that stop the wrapper (rows of one parametrized test):
   - A `restrict` that raises `ConfinementError("<tmp>/l is a symbolic link")` gives exactly `factory-confine: <tmp>/l is a symbolic link\n` on the given `stderr`, returns 1 and never calls `replace`.
   - A `replace` that raises `OSError(errno.ENOENT, "No such file or directory")` gives `factory-confine: cannot start prog: No such file or directory\n` and returns 1.
5. An ABI below 3 calls neither `restrict` nor `replace`, and makes neither `<tmp>/a/b` nor `<tmp>/t`.
6. `restrict` and `replace` left `None` are the adapters' functions: a source check of `factory.entry.confine` finds them as the defaults, and the console script's existing child-process tests still pass unchanged.
7. `make check` stays green.
8. docs: `docs/project-guide.md`, section *The start wrapper*: the paragraph on its tests says that the rows up to step 6 also run in-process with `restrict` and `replace` injected, and that the child-process rows check the real kernel. No other document changes.

## Smoke test

```bash
uv run -q python -c '
import io, json, sys, tempfile
from pathlib import Path
from factory.entry.confine import main
class Replaced(Exception): pass
calls = []
def replace(argv, env):
    calls.append(("replace", list(argv), env["TMPDIR"]))
    raise Replaced
with tempfile.TemporaryDirectory() as d:
    tmp = Path(d)
    rules = tmp / "rules.json"
    rules.write_text(json.dumps({"folders": [str(tmp / "a" / "b")], "files": [], "temporary_directory": str(tmp / "t")}))
    try:
        main(["--rules", str(rules), "--", "prog"], stderr=io.StringIO(), abi=lambda: 7, restrict=lambda folders, files: calls.append(("restrict", [p.name for p in folders])), replace=replace)
    except Replaced:
        pass
    print(calls[0], (calls[1][0], calls[1][1], Path(calls[1][2]).name), oct((tmp / "t").stat().st_mode & 0o777))
'
```
Expect: `('restrict', ['b', 't']) ('replace', ['prog'], 't') 0o700`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: `factory.entry.confine.main` gains keyword-only `restrict` and `replace`, with exact types and `None` defaults. These are the adapters' `restrict_writes` and `replace_process`, which `src/factory/entry/confine.py` already imports. The call order, arguments and error texts match the code as it stands (lines 61-75), so the change is small and concrete.
   Criteria: each is testable by one test function or one parametrized test. Criterion 1 covers the folder/file/temporary split, the `0700` mode and `parents=True`. Criterion 2 covers the command, the `TMPDIR` environment and the call order and count. Criterion 3 has both argument-count sides: 4 arguments pass and 3 fail, with the usage line. Criterion 4 has both fault rows, with exact texts. Criterion 5 covers an ABI below 3. Criterion 6 is a source check of the defaults. Every Interface rule has a criterion for its failing side. The usage text is the existing `_USAGE` constant, which the story leaves unchanged.
   Smoke test: it is runnable as written, using `uv run -q python -c`, with `abi`, `restrict` and `replace` all injected, so nothing restricts the shell. The `Expect:` line is a single printed line that can be compared exactly.
   Architecture: the change stays in `factory.entry`, which already imports the two adapters directly (decision 19). The new test module goes in `tests/entry/`, as `CLAUDE.md` says. `tests/entry/test_confine.py` is left unchanged, so no leave is needed for another story's test.
   Scope: this is within F0019 as a follow-up from its acceptance. It is not under "Out of scope", and it only makes steps 3 to 6 visible to coverage and mutation testing. The docs criterion touches only `docs/project-guide.md`.
4. factory: started tests as self.
5. tester: Wrote the in-process tests for `factory.entry.confine.main`. They pass a `Steps` recorder for `restrict` and `replace`. When the recorder records `restrict` it also snapshots the watched folders' modes. When it records `replace` it raises the test-local `Replaced`, or the fault a row sets.
   criterion 1: tests/entry/test_confine_steps.py::test_restrict_gets_the_folders_the_temporary_folder_and_the_files_once_they_exist
   criterion 2: tests/entry/test_confine_steps.py::test_replace_gets_the_command_and_the_environment_with_tmpdir_after_restrict
   criterion 3: tests/entry/test_confine_steps.py::test_four_arguments_reach_the_command_and_three_print_the_usage (rows four-arguments, three-arguments)
   criterion 4: tests/entry/test_confine_steps.py::test_a_fault_of_restrict_or_replace_stops_the_wrapper_with_one_line (rows restrict, replace)
   criterion 5: tests/entry/test_confine_steps.py::test_a_kernel_below_abi_3_makes_no_folder_and_calls_neither_step (rows ABI 0 and 2 refused, ABI 3 accepted for the other side of the limit)
   criterion 6: tests/entry/test_confine_steps.py::test_restrict_and_replace_left_none_are_the_adapters_functions. It checks that the module imports `restrict_writes` from `factory.adapters.landlock` and `replace_process` from `factory.adapters.process`. It checks that both new parameters default to `None`. It also checks that `main` holds `restrict_writes if restrict is None else restrict` and the matching expression for `replace`, the way `main` already takes `abi`. The child-process half of the criterion is the unchanged tests/entry/test_confine.py.
   criteria 7 and 8: no test; they are `make check` and the docs stage.
   Files created: tests/entry/test_confine_steps.py. No earlier test file changed.
   `make test` fails as intended on the new module only. Every one of its tests fails because `main` does not take `restrict` or `replace` yet (a TypeError for an unexpected keyword argument). The test runner could import every module. `make lint` is green. I skipped the type check, as the stage says.

   `lint`: lint: green (0.0 s)
   `test`: FAILED tests/entry/test_confine_steps.py::test_restrict_and_replace_left_none_are_the_adapters_functions
6. factory: started doing as self.
7. coder: Built: `src/factory/entry/confine.py`. `main` now takes two keyword-only arguments, `restrict` and `replace`, typed by the private aliases `_Restrict` and `_Replace`. When they are `None` they default to `restrict_writes` and `replace_process`, using the same `<default> if x is None else x` form as `abi`. `main` passes them to `_confine_and_start`, which calls them where it used to call the adapters directly. The steps, their order, the texts and the exit status are unchanged. The console script and `python -m` pass neither argument.

   Main choice: I pass the two callables as plain parameters to `_confine_and_start`, next to `abi`. I rejected bundling the three injected steps into a small frozen dataclass: for three callables in one private function it adds a type without making anything clearer. To keep the line short, I moved `_read_rules(rules_file)` out of the call into a local `rules`.

   Checks: all six new tests in `tests/entry/test_confine_steps.py` pass, and `tests/entry/test_confine.py` is untouched and green. `make check` is green, and coverage of `confine.py` rose from 78 % to 95 %. The story's smoke test prints exactly `('restrict', ['b', 't']) ('replace', ['prog'], 't') 0o700`.

   Refactor: I read the diff and nothing needed changing.

   Description: the journal did not change the meaning of the task, so I did not rewrite it.

   Noticed but did not touch:
   - Three lines of `confine.py` are still not covered: 97-98 (the `mkdir` fault in `_make_folders`) and 110 (`if __name__ == "__main__"`). The story does not ask for them.
   - I did not run `make duplicates` or `make mutants`.

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings

   Reviewed `git diff main...HEAD -- . ':!factory'`, which changes `src/factory/entry/confine.py` and adds `tests/entry/test_confine_steps.py`. I read both against the criteria and the Interface.
   - Acceptance: every criterion from 1 to 6 has a test, and each test checks what its criterion says.
     - Criterion 1 checks the exact `restrict` arguments, that `a/b` exists at the call, and that `t` has mode `0o700`.
     - Criterion 2 checks the call order, that each step is called once, and the command and environment with `TMPDIR`.
     - Criterion 3 has both sides of the argument count, 4 and 3, as rows of one parametrized test.
     - Criterion 4 has both fault rows, with exact texts. In the `restrict` row, `replace` is never called.
     - Criterion 5 has ABI 0 and 2 refused and 3 accepted, so both sides of the limit are covered, and it checks that no folder is made.
     - Criterion 6 is the AST and signature check of the defaults. `tests/entry/test_confine.py` is untouched.
     - The coder's journal entry 7 shows `make check` green.
   - Every check that the five mutations in the Description would break is pinned: the rules split, mode `0700`, `parents=True` (`a/b` must exist), the 4-argument boundary, and `TMPDIR`.
   - Architecture: the change stays in `factory.entry`. The adapters stay the defaults through the same `<default> if x is None else x` form as `abi`.
   - Security: no suppression markers. Nothing in the security group was touched.
   - Quality: the private aliases `_Restrict` and `_Replace` follow the module-level `Callable` alias idiom already used in `tick.py`, `comments.py` and `evaluation.py`. There is no dead code and no copied helper. `make duplicates` reports 0 new.
   - Hygiene: journal entry 7 names the main choice (plain parameters) and the rejected alternative (a dataclass bundling the steps). The Description matches what was built. Criterion 8 still describes the docs change.

   Earlier tests: none. The diff only adds `tests/entry/test_confine_steps.py`, and no test file on `main` is changed, renamed or deleted.
10. factory: started docs as self.
11. documenter: Changed `docs/project-guide.md` only, in the section *The start wrapper*:
    - *The six steps*: the `main` signature now shows `restrict=None, replace=None`. It says they are for tests, that `None` means `restrict_writes` and `replace_process`, and that the console script passes neither.
    - *Tests*: the paragraph says the child-process rows in `tests/entry/test_confine.py` check the real kernel. It says `tests/entry/test_confine_steps.py` runs the steps up to step 6 in-process with recorders injected, so coverage and mutation testing see them.

    I wrote only prose and ran no example. The diff matches the Interface: the defaults, the `<default> if x is None else x` form, and unchanged texts and order. I found no contradiction between the code and the Interface, so there are no findings. I did not run `make check`, because only a document changed; the factory runs it.

    Cross-read and found current: steps 3 to 6 of the six-steps list (their texts and order are unchanged), *What the command gets*, `README.md`, `docs/operator-guide.md` (its `factory-confine` passages), and `docs/decisions.md` (entry on the wrapper).

    Stale text that is not this story's, left alone: the first paragraph of *The start wrapper* ends with "Nothing starts it yet: the runtime will." Later entries (F0019-S0004, and the operator guide) say the runtime now starts every agent run through it.

    `check`: check: green
    `documents`: documents ok
12. factory: started smoke-test as self.
