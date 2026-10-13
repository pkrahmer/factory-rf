---
stage: demo
pr: 7
blocked: null
comments_seen: 0
round: 1
attempts: 0
---
# The project-commands interface and the make class

## Assignment (as of log entry 1)

Give the factory its one way into a project's build: the `ProjectCommands` interface, whose single operation runs a named command under a `time_limit` and returns a `CheckResult` judged by the exit status alone, and `MakeProjectCommands`, the first implementation, which runs `make <command>` (a Python project's make targets call uv). The result is generic: it carries no layer names, because a project declares its own layers and checks them with a project command of its own. A red command or a command that reached its `time_limit` is a result, not an error; an error is only a command that cannot be started. Covers R11 (the interface and the make class) and R8 (the generic check result); keeps kept thing 8 (a check is its exit status: the factory reads nothing from a command but the exit status, the last line and the tail of the output) and kept thing 17 (the project is reached through its project commands only: a search shows `make` is named in one module). The pipeline uses these results from F0005; the preflight's probe from F0010. The command runs through `run_process` (S0004).

## Interface

`src/factory/domain/checks.py`

```python
OUTPUT_TAIL_LINES = 30
CheckStatus = Literal["passed", "failed", "time_limit"]

class CheckResult(BaseModel):
    command: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]*$")]
    status: CheckStatus
    exit_status: int | None
    duration: timedelta
    last_line: str
    output_tail: str

    @property
    def passed(self) -> bool: ...
```

`src/factory/domain/errors.py` (adds one type)

```python
class ProjectCommandError(BoundaryError):
    command: str
    detail: str
    def __init__(self, command: str, detail: str) -> None: ...
```

`src/factory/application/project_commands.py`

```python
class ProjectCommands(Protocol):
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult: ...
```

`src/factory/adapters/make_commands.py`

```python
class MakeProjectCommands:      # satisfies ProjectCommands structurally, no inheritance
    def __init__(self, directory: Path, kill_points: KillPoints | None = None, *, executable: str = "make") -> None: ...
    def run(self, command: str, *, time_limit: timedelta) -> CheckResult: ...
```

The rules, each with a criterion below:

- `CheckResult.status` is `"passed"` exactly when `exit_status` is 0, `"failed"` exactly when `exit_status` is an integer other than 0, and `"time_limit"` exactly when `exit_status` is `None`. `passed` is true only for `"passed"`. The model is frozen and forbids unknown keys.
- `run(command, time_limit=...)` runs `<executable> --no-print-directory <command>` in `directory` through `run_process` with `merge_stderr=True` and the current environment of the process less `MAKELEVEL`, `MAKEFLAGS` and `MFLAGS`. The two differences keep a run under `make check` (where the tests run inside make, so `MAKELEVEL` is set) from giving different output than a run on its own: an inner make that sees `MAKELEVEL` adds `make[N]: Entering directory` and `Leaving directory` lines to the output. `directory` is where `make` finds the project's Makefile. A `time_limit` of zero or less raises `ValueError`.
- The exit status alone decides: 0 is `"passed"`, any other is `"failed"`, and a command ended by the `time_limit` is `"time_limit"` with `exit_status` `None`. GNU make, not the recipe, sets the exit status: it exits 2 whenever a recipe fails (whatever status the recipe's command had) and when a target is missing, and `exit_status` is that 2. A missing target is a failed command, not an error.
- `output_tail` is the last `OUTPUT_TAIL_LINES` (30) lines of the merged stdout and stderr, in the order written, joined with newlines; fewer lines are all returned.
- `last_line` is the last line of the output that is not blank and does not start with `make:` or `make[` (make's own messages); `""` when there is none. This refines the interface sheet's "last non-blank line" (decision 11 of the feature).
- `duration` is the time the command ran.
- `command` that does not match `^[a-z][a-z0-9-]*$` raises `ProjectCommandError` before anything is started; so does an `executable` that cannot be started (the detail is the operating system's message). The message of the error is `project command <command> failed: <detail>`.
- `kill_points` is accepted so that wiring builds every wrapper the same way; this wrapper reaches no kill point: with all four points armed, `run` returns normally and `reached` is 0 for each.
- No identifier in the three modules contains `layer` (R8), and the string `"make"` appears in no module under `src/factory` other than `factory.adapters.make_commands` (kept 17).

Tests: `tests/domain/test_checks.py`, `tests/domain/test_errors.py` (extended: it gains new tests only, no existing test is changed), `tests/adapters/test_make_commands.py` (each test writes a Makefile into `tmp_path` and runs the class against it; a test that needs a process id has its recipe write it to a file), `tests/test_make_search.py`. A test module assigns `MakeProjectCommands` to a variable annotated `ProjectCommands`, so that mypy checks the fit. The only waiting in the tests is for a command that the `time_limit` kills and for the target of criterion 16, which runs about 0.3 seconds.

## Acceptance criteria

1. `CheckResult` accepts `("passed", 0)`, `("failed", 2)` and `("time_limit", None)` for `status` and `exit_status`, and `passed` is true for the first and false for the other two.
2. `CheckResult` rejects `("passed", 1)`, `("failed", 0)`, `("failed", None)`, `("time_limit", 0)` and `("time_limit", 124)`.
3. `CheckResult.command` accepts `check` and `lint-all` and rejects `Check`, `1x`, `a b`, the empty string and `-f`.
4. `CheckResult` rejects an unknown keyword argument and rejects assignment to a field.
5. The field names of `CheckResult` are exactly `command`, `status`, `exit_status`, `duration`, `last_line` and `output_tail`, and no identifier (name, attribute, argument, class or function name) in `factory.domain.checks`, `factory.application.project_commands` or `factory.adapters.make_commands` contains `layer` (a test parses the three files with `ast`).
6. `run("check", ...)` against a Makefile whose target `check` prints `check: green` and succeeds returns `status == "passed"`, `exit_status == 0`, `command == "check"` and `passed` true.
7. A target that exits with status 2 returns `status == "failed"` and `exit_status == 2`; nothing is raised; a target whose recipe exits with status 3 also gives `exit_status == 2`, because make sets the status.
8. A command whose target does not exist returns `status == "failed"` and `exit_status == 2`; nothing is raised.
9. A target that sleeps 60 seconds, run with `time_limit=timedelta(seconds=1)`, returns `status == "time_limit"` and `exit_status` `None` within 6 seconds, and the `sleep` it started is gone: the recipe writes the `sleep`'s pid (`$!`) to a file, and after the call `os.kill(pid, 0)` raises `ProcessLookupError` or `/proc/<pid>/stat` shows the state `Z`.
10. `run` with `time_limit=timedelta(0)` and with `timedelta(seconds=-1)` raises `ValueError`; with one second it runs.
11. For a target that prints numbered lines `1` to `n`, `output_tail` holds all `n` lines when `n` is 29 and when `n` is 30, the lines `2` to `31` when `n` is 31, and the lines `11` to `40` when `n` is 40.
12. A target that prints `a` to stdout, `b` to stderr and `c` to stdout gives an `output_tail` with the lines `a`, `b`, `c` in that order.
13. `last_line` is the last non-blank line of the output when blank lines follow it.
14. `last_line` is `""` for a target that prints nothing.
15. For a failing target that prints `lint: red` and then make prints `make: *** [Makefile:2: lint] Error 3`, `last_line` is `lint: red`; a line starting with `make[1]:` is skipped in the same way.
16. For a target that runs about 0.3 seconds, `duration` is at least 0.3 seconds and below the time limit.
17. A target that prints `$$PROBE` shows the value of a variable `PROBE` that was set in the test process, so the command runs with the current environment (less the three make variables of criterion 24).
18. With all four kill points armed, `run` returns normally and `reached` is 0 for each point.
19. `run("check; rm -rf x", ...)`, `run("Check", ...)` and `run("-f", ...)` raise `ProjectCommandError` with `command` set, and no process is started (a marker file the target would create does not exist).
20. `MakeProjectCommands(directory, executable="/no/such/make").run("check", time_limit=...)` raises `ProjectCommandError` whose `command` is `check` and whose `detail` is not empty.
21. `ProjectCommandError("check", "boom")` has the message `project command check failed: boom` and is a subclass of `BoundaryError`.
22. The string literal `"make"` occurs in no module of `src/factory` other than `factory.adapters.make_commands`.
23. `MakeProjectCommands` is not a subclass of `ProjectCommands`, and a test module assigns a `MakeProjectCommands` to a variable annotated `ProjectCommands`, so that `make check` (mypy) proves the structural fit.
24. With `MAKELEVEL=1`, `MAKEFLAGS=w` and `MFLAGS=-w` set in the test process, a target that prints `ok` and then `$(MAKELEVEL)` gives an `output_tail` of exactly the lines `ok` and `0`: no line starts with `make[` and none holds `Entering directory` or `Leaving directory`.
25. make check stays green.
26. docs: `docs/project-guide.md` describes the project-commands interface (the single `run` operation, `--no-print-directory` and the removed make variables, the exit status as the only judgment, the tail of 30 lines, the generic result with no layer names) and says how a project declares its own layers check as a project command; `docs/operator-guide.md` notes that the make targets `check`, `lint` and `test` are what the factory calls.

## Demo

```bash
uv run python -c "
import tempfile
from datetime import timedelta
from pathlib import Path
from factory.adapters.make_commands import MakeProjectCommands
root = Path(tempfile.mkdtemp())
(root / 'Makefile').write_text('check:\n\t@echo \"check: green\"\n\nlint:\n\t@echo \"lint: red\"; exit 3\n')
commands = MakeProjectCommands(root)
for name in ('check', 'lint', 'nope'):
    result = commands.run(name, time_limit=timedelta(seconds=30))
    print(name, result.status, result.exit_status, repr(result.last_line))
"
```
Expect: three lines: `check passed 0 'check: green'`, then `lint failed 2 'lint: red'`, then `nope failed 2 ''`: the exit status decides, make (not the recipe's `exit 3`) sets it to 2, and make's own messages are not taken as the last line.

```bash
uv run python -c "
from datetime import timedelta
from pathlib import Path
from factory.adapters.make_commands import MakeProjectCommands
from factory.domain.errors import ProjectCommandError
try:
    MakeProjectCommands(Path('.')).run('Check; ls', time_limit=timedelta(seconds=5))
except ProjectCommandError as error:
    print(error)
"
```
Expect: one line starting with `project command Check; ls failed:` that names the invalid command name.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`domain/checks.py`, `domain/errors.py`, `application/project_commands.py`, `adapters/make_commands.py`). The command line, the environment handling, the error message and the structural fit are all stated.
   - Criteria: each is testable by one test function (1-4 for the model, 6-18 and 24 for `run`, 19-21 for errors, 22-23 for the structure). Each rule has its failing side: invalid status/exit_status pairs (2), invalid command names (3, 19), a `time_limit` of zero or less (10), a failed or missing target as a result (7, 8), a timeout (9), an executable that cannot be started (20). Each behaviour stated in the Interface has a criterion: the 30-line tail (11), the merged order (12), `last_line` skipping blanks and make's lines (13-15), `duration` (16), the environment (17, 24) and the kill points (18).
   - Demo: both blocks are runnable. Each `Expect:` line is checkable against the printed output.
   - Architecture: the interface is a Protocol in `application`, the implementation is in `adapters` and calls `run_process`, and the result and the error are in `domain`. This fits the four layers and R6/R11.
   - Scope: the story is within the feature's "project-commands interface and the make class (R11), generic check result (R8)". Nothing is in "Out of scope".
3. tester: wrote red tests for every acceptance criterion except 25 and 26 (the check gate and docs).
   - criterion 1: tests/domain/test_checks.py::test_status_matching_the_exit_status_is_accepted (parametrized over the three pairs)
   - criterion 2: tests/domain/test_checks.py::test_status_contradicting_the_exit_status_is_rejected (parametrized over the five pairs)
   - criterion 3: tests/domain/test_checks.py::test_lowercase_command_names_are_accepted and ::test_other_command_names_are_rejected
   - criterion 4: tests/domain/test_checks.py::test_unknown_keys_and_assignment_are_rejected
   - criterion 5: tests/domain/test_checks.py::test_fields_are_exactly_the_generic_six and tests/test_make_search.py::test_no_identifier_in_the_check_modules_names_a_layer (uses `ast` to collect names, attributes, arguments, function and class names and import aliases)
   - criterion 6: tests/adapters/test_make_commands.py::test_succeeding_target_passes
   - criterion 7: tests/adapters/test_make_commands.py::test_failing_recipe_fails_with_the_status_make_sets (recipe exits 2 and 3; both expect 2)
   - criterion 8: tests/adapters/test_make_commands.py::test_missing_target_is_a_failed_command
   - criterion 9: tests/adapters/test_make_commands.py::test_command_reaching_its_time_limit_is_killed (recipe `sleep 60 & echo $$! > pid; wait`)
   - criterion 10: tests/adapters/test_make_commands.py::test_time_limit_of_zero_or_less_is_rejected (expects ValueError whose message matches `time_limit`) and ::test_time_limit_of_one_second_runs
   - criterion 11: tests/adapters/test_make_commands.py::test_output_tail_keeps_the_last_thirty_lines (n = 29, 30, 31, 40, via `seq`)
   - criterion 12: tests/adapters/test_make_commands.py::test_output_tail_merges_stderr_in_the_order_written
   - criterion 13: tests/adapters/test_make_commands.py::test_last_line_skips_trailing_blank_lines
   - criterion 14: tests/adapters/test_make_commands.py::test_last_line_is_empty_without_output
   - criterion 15: tests/adapters/test_make_commands.py::test_last_line_skips_the_lines_make_writes (also checks that make's `Error 3` line is in the tail; the `make[1]:` line is written by the recipe)
   - criterion 16: tests/adapters/test_make_commands.py::test_duration_is_the_time_the_command_ran
   - criterion 17: tests/adapters/test_make_commands.py::test_command_runs_with_the_current_environment
   - criterion 18: tests/adapters/test_make_commands.py::test_run_reaches_no_kill_point
   - criterion 19: tests/adapters/test_make_commands.py::test_invalid_command_name_is_refused_before_starting (parametrized; a marker file stays absent)
   - criterion 20: tests/adapters/test_make_commands.py::test_executable_that_cannot_start_is_an_error
   - criterion 21: tests/domain/test_errors.py::test_project_command_error_names_command_and_detail (new test only; the import list gained `ProjectCommandError`, and no existing test changed)
   - criterion 22: tests/test_make_search.py::test_only_the_make_class_names_make (the set of modules with the `"make"` literal must equal {factory.adapters.make_commands})
   - criterion 23: tests/adapters/test_make_commands.py::test_make_class_fits_the_interface_without_inheriting (annotated assignment for mypy; `ProjectCommands` is not in the MRO)
   - criterion 24: tests/adapters/test_make_commands.py::test_outer_make_variables_do_not_reach_the_command (output_tail lines are exactly `ok`, `0`)
   Interpretation: criteria 11, 12 and 24 compare `output_tail.splitlines()`, so a trailing newline is not judged either way.
   Files created: tests/domain/test_checks.py, tests/adapters/test_make_commands.py, tests/test_make_search.py. File extended: tests/domain/test_errors.py.
   `make test`: collection errors in test_make_commands, test_checks and test_errors, because the modules factory.domain.checks, factory.application.project_commands and factory.adapters.make_commands and the name factory.domain.errors.ProjectCommandError do not exist yet. test_make_search will fail until make_commands.py exists. `make lint` is green.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
4. coder: implemented the project-commands interface and the make class. All tester tests pass without changes, and `make check` is green with 100 % branch coverage.
      - `src/factory/domain/checks.py`: contains `OUTPUT_TAIL_LINES`, `CheckStatus`, `COMMAND_NAME_PATTERN`, `CommandName`, `status_of(exit_status)` and `CheckResult`. `CheckResult` is frozen and forbids unknown keys. An after-validator rejects any status that differs from `status_of(exit_status)`, and `passed` is true only for "passed".
      - `src/factory/domain/errors.py`: adds `ProjectCommandError(BoundaryError)`, whose message is `project command <command> failed: <detail>`.
      - `src/factory/application/project_commands.py`: the `ProjectCommands` Protocol with a single `run` operation.
      - `src/factory/adapters/make_commands.py`: `MakeProjectCommands`. It checks `time_limit` (raises ValueError) and then the command name (raises ProjectCommandError) before starting anything. It then runs `<executable> --no-print-directory <command>` through `run_process` with `merge_stderr=True`, using `os.environ` minus MAKELEVEL, MAKEFLAGS and MFLAGS. An `OSError` at start becomes `ProjectCommandError(command, str(exc))`. The status comes from the exit status only, through `status_of`. `output_tail` is the last 30 lines. `last_line` is the last line that is not blank and does not start with `make:` or `make[`. `kill_points` is stored and never reached.
      Main decision: the status mapping `status_of` lives in the domain, and the adapter reuses it together with the domain's command-name pattern, so the rule and the regex each exist once. Rejected: a second regex and an inline status mapping in the adapter, which would duplicate the model's validation.
      Both demo blocks run and print exactly what their Expect lines say.
      Refactor pass: I read the diff and found nothing to change; the clean-up (sharing the pattern) went into the feature commit. There is therefore no separate refactor commit.
      Not touched: the docs for criterion 26 (`docs/project-guide.md` and `docs/operator-guide.md`) are the documenter's job.

   `make check`: check: green
5. reviewer: one finding, sent back.

   1. `src/factory/adapters/make_commands.py:251`: `_COMMAND_NAME.match(command)` uses Python `re`, where `$` also matches just before a trailing newline. So `run("check\n", ...)` gets past the name check and starts `make --no-print-directory "check\n"`. Only after that does `CheckResult(command="check\n")` fail, because Pydantic's default Rust regex does not let `$` match before a final newline. The caller then gets a raw `ValidationError` after a process was started. The Interface rule says a non-matching command raises `ProjectCommandError` before anything is started, so this breaks it. Fix: use `_COMMAND_NAME.fullmatch(command)`, or anchor the shared pattern with `\Z`, so the adapter and the model accept exactly the same names. Criterion 19 does not test a name with a trailing newline. This is a gap in the story, not the tester's fault: if the human wants a test for it, adding `"check\n"` to the parametrized names of `tests/adapters/test_make_commands.py::test_invalid_command_name_is_refused_before_starting` is a tester change (R9).

   Otherwise the review found no problems:
   - Every criterion from 1 to 24 has a test, and each test checks what its criterion says. The coder's entry reports `make check` green.
   - Layers are correct: the Protocol is in application, the DTO and error in domain, and the make class in adapters through `run_process`.
   - No suppression markers were added.
   - The docstrings are present and say the right things.
6. coder: coder (round 1): fixed the reviewer's one finding in commit 3ad8721.
      - `src/factory/adapters/make_commands.py`: the name check now calls `_COMMAND_NAME.fullmatch(command)` instead of `.match(command)`. Python's `re` lets `$` match just before a final newline, so `"check\n"` used to get past the check, start make, and only then fail inside `CheckResult` with a `ValidationError`. With `fullmatch` the adapter accepts exactly the names the model's pattern accepts. `run("check\n", ...)` now raises `ProjectCommandError` before any process starts. I checked this by hand: the message is `project command check\n failed: invalid command name 'check\\n'`.
      - Main decision: keep the shared `COMMAND_NAME_PATTERN` exactly as the Interface gives it (`^[a-z][a-z0-9-]*$`) and change only the adapter's match call. Rejected: anchoring the pattern with `\Z`, which would make the domain's pattern differ from the one the Interface states.
      - Open: no test covers a name with a trailing newline. As the reviewer noted, adding `"check\n"` to the parametrized names of `tests/adapters/test_make_commands.py::test_invalid_command_name_is_refused_before_starting` would be a tester change if the human wants it.
      - Refactor: a one-line change, so nothing to refactor.

      `make check`: check: green (coverage 100 %)

   `make check`: check: green
7. reviewer: reviewer (round 1, second pass): no findings.
      - The finding from entry 5 is fixed. `src/factory/adapters/make_commands.py` now calls `_COMMAND_NAME.fullmatch(command)`. With fullmatch, `"check\n"` no longer matches `^[a-z][a-z0-9-]*$`, so the adapter accepts the same names as the model's Pydantic pattern and refuses `"check\n"` before `run_process` starts anything.
      - Acceptance criteria: I read each test from 1 to 24 against its criterion, and each one tests what its criterion says.
        - The failing sides are covered: rejected status/exit pairs (2), rejected names (3, 19, with a marker file proving nothing started), a `time_limit` of zero or less (10), an executable that cannot start (20), a timeout with the `sleep` reaped (9), and the tail boundary at 29, 30, 31 and 40 lines (11).
        - The coder's entry reports `make check` green.
        - Still open, as entries 5 and 6 say: no test covers a name with a trailing newline. Only the human can close that, by asking the tester to add `"check\n"` to `test_invalid_command_name_is_refused_before_starting`. It does not block this story.
      - Architecture: `CheckResult`, `status_of` and `ProjectCommandError` are in domain, the `ProjectCommands` Protocol is in application, and `MakeProjectCommands` is in adapters and goes through `run_process`, the one process module. Layers and wrappers (R5, R6, R8, R11) hold. No `dict[str, Any]` crosses a function boundary; `_environment` returns `dict[str, str]`.
      - Security: the command runs from an argv list with no shell, and the name is validated before anything starts. The diff adds no suppression markers and no secrets.
      - Quality: the status mapping and the name pattern each exist once, in the domain, and the adapter reuses them. Docstrings are present and accurate. `kill_points` is stored but never used, which the Interface allows explicitly so that wiring stays uniform.
      - Ticket hygiene: the Assignment matches what was built. Criterion 26 still describes what the documenter must write in `docs/project-guide.md` and `docs/operator-guide.md`.
8. documenter: docs (round 1): wrote the documentation for criterion 26; `make check` is green.
   - `docs/project-guide.md`: added a "Project commands" section. It covers the `ProjectCommands` protocol and its single `run`, `MakeProjectCommands`, `--no-print-directory` and the three removed make variables, the exit status as the only judgment (make sets 2), the 30-line tail, `last_line`, the name check and `ProjectCommandError`, and the generic `CheckResult` with no layer names. It also says how a project declares its own layers check: a make target of its own, which the factory sees only as a `CheckResult`. Also added `ProjectCommandError` to the Errors section.
   - `docs/operator-guide.md`: added a note that the make targets `check`, `lint` and `test` are what the factory calls, how each is judged, and that a missing target counts as failed.
   - Cross-read: README and `docs/decisions.md` have nothing on project commands and needed no change. I checked the rest of the project guide against the diff and found it current.
   - Findings against the code: none. The trailing-newline name is already fixed with `fullmatch`. Still open from entries 5 to 7: no test covers `"check\n"`; only the human can ask for it.
   - Stale text seen but not touched: the operator guide's opening sentence says "Nothing is built yet". It is unrelated to this story.
   - I did not run the doc example, a short snippet of the same call as the demo.

   `make check`: check: green
