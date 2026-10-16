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

## Acceptance criteria

1. With an environment that lacks `FACTORY_INSTANCE`, and a `state_directory` that cannot be created (`tmp_path / "file" / "state"`, where `tmp_path / "file"` is a regular file), `main` returns 2, raises nothing and starts no runner.
2. In the case of criterion 1, standard error holds the line `factory-run: settings invalid: FACTORY_INSTANCE: missing`, followed by a line that starts with `factory-run: cannot write the machine stop: ` and names the `OSError`'s type (`NotADirectoryError` or `FileNotFoundError`).
3. With the same environment and a writable `state_directory`, `main` returns 2. It writes the time-stamped log line and the machine stop as before, and nothing that starts with `factory-run: cannot write the machine stop` reaches standard error. The two sides of criteria 1 to 3 are rows of one parametrized test.
4. A runner that raises `OSError` for a valid environment still lets the `OSError` out of `main`.
5. `make check` stays green.
6. docs: `docs/operator-guide.md`, at the stop for an invalid environment, says that a state directory the factory cannot write ends `factory-run` with status 2 and the two lines on standard error, and that the operator should check the `state` volume's owner and mode. `README.md`'s sentence on status 2 holds without a condition.

## Demo

```bash
env -i PATH="$PATH" HOME="$HOME" uv run python -c "from pathlib import Path; import tempfile; from factory.entry.run import main; f = Path(tempfile.mkdtemp()) / 'file'; f.write_text(''); print('status', main({}, state_directory=f / 'state'))"
```
Expect: two lines on standard error, `factory-run: settings invalid: FACTORY_REPOSITORY_URL: missing` and `factory-run: cannot write the machine stop: NotADirectoryError: ...`, then `status 2`, and no `Traceback`.

```bash
d=$(mktemp -d); uv run python -c "from pathlib import Path; from factory.entry.run import main; print('status', main({}, state_directory=Path('$d')))"; uv run factory-health --state-directory "$d"; echo "exit=$?"
```
Expect: `status 2`, then one `preflight_failed (machine): FACTORY_REPOSITORY_URL: missing (since ...)` line, then `exit=1`.

## Log (append only)

1. 2026-10-16 human: created.
