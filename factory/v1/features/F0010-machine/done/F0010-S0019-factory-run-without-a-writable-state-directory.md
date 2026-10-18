---
stage: done
pr: 137
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# factory-run without a writable state directory

<!-- proposed by feature acceptance of 2026-10-16; refine before promoting -->

## Assignment (as of log entry 1)

F0010-S0004 promised that an invalid environment ends `factory-run` "with status 2, a time-stamped line and a machine stop, never with a traceback". That holds in the image, where `/state` belongs to the factory's user. It does not hold where the state directory cannot be written. The feature acceptance ran `env -i PATH="$PATH" HOME="$HOME" uv run factory-run` on a machine without `/state`. `_stop_the_machine` raised `PermissionError: [Errno 13] Permission denied: '/state'` from `TimestampedFactoryLog.line`, Python printed two chained tracebacks, and the process ended with status 1.

That is the README's own getting-started path: "with an invalid environment it ends with status 2 and a machine stop". In the container, the same thing happens when a `state` volume is mounted read-only or with the wrong owner. The operator then sees a traceback where the stop's text should be, and an exit status of 1 that the entrypoint does not tell apart from a crash.

This story keeps status 2 and a readable message when the stop cannot be written. Every other path of `main` stays as it is.

## Interface

`src/factory/entry/run.py`, `main(environ=None, *, runner=None, state_directory=STATE_DIRECTORY, clock=None) -> int` keeps its signature. What changes is the handling of `SettingsInvalid`:

- `main` writes the stop with `_stop_the_machine(error, state_directory, clock)`, as today.
- When that raises `OSError`, `main` catches it and writes two lines to standard error: `factory-run: settings invalid: <error>`, then `factory-run: cannot write the machine stop: <type name>: <message>`. Then it returns 2.
- The first line is written only in this case. When the stop is written, the output stays what it is today.
- An `OSError` from `run(settings)` itself is not caught here; it is not a settings fault.

No new public name.

Tests: in `tests/entry/test_run.py`, with its `environment` fixture and `_main_without_instance` (an environment with `FACTORY_REPOSITORY_URL` and the image identity file, without `FACTORY_INSTANCE`), and `capsys` for standard error. Criterion 4's runner is a function of the test that raises `OSError`; `Runner` stays as it is.

## Acceptance criteria

1. With an environment that lacks `FACTORY_INSTANCE`, and a `state_directory` that cannot be created (`tmp_path / "file" / "state"`, where `tmp_path / "file"` is a regular file), `main` returns 2, raises nothing and starts no runner.
2. In the case of criterion 1, standard error holds the line `factory-run: settings invalid: FACTORY_INSTANCE: missing`, followed by a line that starts with `factory-run: cannot write the machine stop: ` and names the `OSError`'s type (`NotADirectoryError` or `FileNotFoundError`).
3. With the same environment and a writable `state_directory`, `main` returns 2, writes the time-stamped log line and the machine stop as before, and writes nothing to standard error. The two sides of criteria 1 to 3 are rows of one parametrized test.
4. A runner that raises `OSError` for a valid environment still lets the `OSError` out of `main`.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, "When the process refuses to start", says that when the state directory cannot be written, `factory-run` still ends with status 2: the time-stamped line reaches standard output, the two lines go to standard error and no stop is written, and the operator should check the `state` volume's owner and mode. `README.md`'s sentence on status 2 says the same in short: status 2 with a machine stop, or with the two lines on standard error when the state directory cannot be written.

## Demo

```bash
env -i PATH="$PATH" HOME="$HOME" uv run python -c "from pathlib import Path; import tempfile; from factory.entry.run import main; f = Path(tempfile.mkdtemp()) / 'file'; f.write_text(''); print('status', main({}, state_directory=f / 'state'))"
```
Expect: the time-stamped line `<stamp> settings invalid: FACTORY_REPOSITORY_URL: missing` on standard output, two lines on standard error, `factory-run: settings invalid: FACTORY_REPOSITORY_URL: missing` and `factory-run: cannot write the machine stop: NotADirectoryError: [Errno 20] Not a directory: '<tmp>/file/state'`, then `status 2`, and no `Traceback`.

```bash
d=$(mktemp -d); uv run python -c "from pathlib import Path; from factory.entry.run import main; print('status', main({}, state_directory=Path('$d')))"; uv run factory-health --state-directory "$d"; echo "exit=$?"
```
Expect: `<stamp> settings invalid: FACTORY_REPOSITORY_URL: missing`, then `status 2`, then one line `preflight_failed (machine): FACTORY_REPOSITORY_URL: missing (since <stamp>)`, then `exit=1`.

## Log (append only)

1. 2026-10-16 human: created.
2. intake: accepted
   - Interface: names `src/factory/entry/run.py` `main` (signature unchanged) and the handling of `OSError` from `_stop_the_machine`: the two exact stderr lines, return 2, no new public name, and an `OSError` from `run(settings)` stays uncaught. The code matches (`main` at run.py, `_stop_the_machine` writes the log line first, then the health store).
   - Criteria: each is testable by one test function. Each rule has both sides: stop unwritable (1, 2), stop writable with an empty stderr (3), and an `OSError` from the runner not caught (4). The two stderr lines of the Interface are covered by criterion 2. Criterion 3 says its rows are one parametrized test.
   - Demo: both commands are runnable. Each `Expect:` line can be checked against the output. The time-stamped line on stdout when the file cannot be written is existing behaviour (`TimestampedFactoryLog.line` writes stdout before opening the file). Criteria 1 to 3 do not assert it, but the docs criterion and the Demo state it. I did not ask about it.
   - Architecture: the change stays in `factory.entry` and touches no other layer. It adds no dependency.
   - Scope: it fits F0010 (the entrypoint's stops, S0004's promise of status 2 with no traceback). Nothing in the feature's "Out of scope" is touched.
3. tester: Added the tests for the criteria to the end of `tests/entry/test_run.py`. I created no new files.
   - criteria 1, 2 and 3: tests/entry/test_run.py::test_main_returns_two_for_invalid_settings_whether_or_not_the_stop_can_be_written. It is one parametrized test with two rows:
     - `writable`: the state directory exists. The test checks that `main` returns 2, starts no runner, writes nothing to stderr, writes the time-stamped log line and records the `preflight_failed` machine stop.
     - `unwritable`: the state directory is `tmp_path/file/state` and `file` is a regular file. The test checks that `main` returns 2, raises nothing and starts no runner. Stderr must hold exactly two lines: `factory-run: settings invalid: FACTORY_INSTANCE: missing`, then `factory-run: cannot write the machine stop: (NotADirectoryError|FileNotFoundError): …`.
   - criterion 4: tests/entry/test_run.py::test_main_lets_an_os_error_of_the_runner_out. The runner is a function inside the test that raises `OSError`. `Runner` is unchanged.
   - criterion 5 (`make check`) and criterion 6 (docs) have no test.

   Every module the tests import already exists, so nothing fails to import.

   `make test` result: one failure, the `unwritable` row of the parametrized test, because `_stop_the_machine` lets its `OSError` out of `main`. The `writable` row and the criterion 4 test pass, since they cover existing behaviour. Coverage stays at 99.5 %.

   `make lint` is green. I skipped the type check, as the stage instructs.

   I did not test that the time-stamped line reaches stdout when the stop cannot be written. No criterion asserts it; only the docs criterion and the Demo state it.

   `make lint`: lint: green
   `make test`: FAILED tests/entry/test_run.py::test_main_returns_two_for_invalid_settings_whether_or_not_the_stop_can_be_written[unwritable]
4. coder: `factory-run` now returns 2 and writes two lines to stderr when the machine stop cannot be written. Commit d763935.
      - Built: in `src/factory/entry/run.py`, `main`'s `SettingsInvalid` branch now calls a new private `_report_the_invalid_settings`. That function calls `_stop_the_machine` unchanged. When the call raises `OSError`, it writes `factory-run: settings invalid: <error>` and then `factory-run: cannot write the machine stop: <type name>: <message>` to `sys.stderr`. `main` returns 2 in both cases. When the stop is written, the output is the same as before. No new public name.
      - Design: the `try` wraps only the stop write, so an `OSError` from `run(settings)` still leaves `main` (criterion 4). I rejected an `except OSError` on `main`'s outer `try`: it would also catch the runner's faults, and those are not settings faults.
      - Time-stamped line: when the state directory cannot be written, it still reaches stdout first, because `TimestampedFactoryLog.line` prints before it opens the file. I left that as it is.
      - Refactor: I read the diff and found nothing to change, so there is no refactor commit.
      - `make check` is green, total coverage 99.54 %.
      - Open: the docs criterion (operator guide, README) is for the documenter stage.

   `make check`: check: green
5. reviewer: no findings.
      - Criteria: in `tests/entry/test_run.py`, the parametrized test `test_main_returns_two_for_invalid_settings_whether_or_not_the_stop_can_be_written` covers criteria 1 to 3 as two rows of one test. The `unwritable` row uses `tmp_path/file/state`. It checks that `main` returns 2, raises nothing and starts no runner (`runner.calls == []`). It checks that stderr holds exactly the two lines, each matched with `fullmatch`; the second must name `NotADirectoryError|FileNotFoundError`. The `writable` row checks status 2, an empty stderr, the time-stamped log line and the `preflight_failed` machine stop. `test_main_lets_an_os_error_of_the_runner_out` covers criterion 4: the runner is a local function, the environment is valid and `Runner` is unchanged. The coder's entry records `make check` green, coverage 99.54 %.
      - Interface: in `src/factory/entry/run.py`, the `try` in `_report_the_invalid_settings` wraps only `_stop_the_machine`, so a runner's `OSError` still leaves `main`. Both stderr lines are written only on `OSError`. The signature of `main` is unchanged and the new helper is private, so there is no new public name.
      - Architecture: the change stays in `factory.entry`. It adds no dependency and no suppression marker.
      - Security: nothing new. The second stderr line carries the `OSError`'s own message (the state path). The Interface asks for that, and the operator needs it.
      - Quality: the names say what things do. The comment explains why stderr is used. I found no second copy of an existing helper: the other modules under `entry` write to stderr with a plain `print` too.
      - Hygiene: the coder's entry names the main decision and the rejected outer `except OSError`. The Assignment matches the code. Criterion 6 (the docs) still describes what the documenter must write.
6. documenter: no findings. The code matches the Interface.
   - `docs/operator-guide.md`, "When the process refuses to start": added that when the state directory cannot be written (a `state` volume that is read-only or has the wrong owner), `factory-run` still ends with status 2. The time-stamped line reaches standard output, the two `factory-run:` lines go to standard error, no stop is written, and the operator should check the volume's owner and mode.
   - `README.md`: the sentence on status 2 now says "a machine stop, or two lines on standard error when the state directory cannot be written".
   - Cross-read: the operator guide's section on refusing to start and the README's getting-started paragraph, both against the diff to `src/factory/entry/run.py`. Nothing else was stale.
   - I did not run the Demo commands in this stage.
   - Unrelated, not touched: none.
   - `make check` is green.

   `make check`: check: green
7. demo: I ran both Demo commands from the repository root. There are no findings.

   1. Unwritable state directory, run with an empty environment (`env -i`):
   ```
   2026-10-16T17:33:00Z settings invalid: FACTORY_REPOSITORY_URL: missing
   factory-run: settings invalid: FACTORY_REPOSITORY_URL: missing
   factory-run: cannot write the machine stop: NotADirectoryError: [Errno 20] Not a directory: '/tmp/tmp_snzw0nv/file/state'
   status 2
   ```
   Met. I ran it a second time with `2>/dev/null` to check where each line goes. Only the time-stamped line and `status 2` were left, so that line is on standard output and the two `factory-run:` lines are on standard error. There was no `Traceback`, and the process exited with status 0 because `print` returned normally.

   2. Writable state directory, followed by `factory-health`:
   ```
   2026-10-16T17:33:00Z settings invalid: FACTORY_REPOSITORY_URL: missing
   status 2
   preflight_failed (machine): FACTORY_REPOSITORY_URL: missing (since 2026-10-16T17:33:00Z)
   exit=1
   ```
   Met. The writable path behaves as it did before: the machine stop is written and `factory-health` reports it.

   Criteria cross-read:
   - Criteria 1 and 2: command 1 returns 2 with the two stderr lines. The demo uses `FACTORY_REPOSITORY_URL` rather than `FACTORY_INSTANCE`; that is the same rule.
   - Criterion 3: command 2 writes the time-stamped line and the stop, and nothing appeared on stderr.
   - Criterion 4 is not exercised by the demo and nothing here contradicts it.
   - Criterion 6: I checked the text, without running anything. `README.md:12` and `docs/operator-guide.md:38` both describe the two-line stderr case with status 2, and the operator guide also says to check the `state` volume's owner and mode.

   Open: nothing.
8. done (pull request merged); cost: 6 runs, 19.7 min, 34 turns, 113k tokens in (399k more from cache), 9k out, $1.26
