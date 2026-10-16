---
stage: doing
pr: 123
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The watcher reads the instance's settings

## Assignment (as of log entry 1)

Give `factory-watch` its settings. Its `main()` was left by F0006-S0006 at exit status 2 with the line `factory-watch: no instance settings are wired yet`, until the instance settings exist. They exist now: `watch.main` reads the same environment as `factory-run` and builds the boundaries the same way, through `boundaries_from_environment` of the previous story, so that the human's window on the remote looks at the instance that the container runs. An invalid environment and an unreadable token file are written to standard error, never as a traceback, and end with status 2. This story implements R25 for the watcher. F0006-S0006's Assignment announces the change ("F0010-S0001 replaces that line by `read_settings` and `build_boundaries`"). A real container is the morning observation.

## Interface

`src/factory/entry/watch.py` (F0006-S0006's module: `main` changes in one branch)

```python
def main(
    argv: Sequence[str] | None = None,
    *,
    boundaries: Boundaries | None = None,
    instance: Name | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> int: ...
```

Rules:

- `watch.main`, when `boundaries` or `instance` is `None`, no longer writes `factory-watch: no instance settings are wired yet`: it calls `boundaries_from_environment(os.environ)` (the same readers as `main` of `factory.entry.run`) and runs `run_watch` with the boundaries and the settings' instance. A `SettingsInvalid` there is written as `factory-watch: settings invalid: <variable>: <fault>` and a newline to `err`, nothing goes to `out`, and `main` returns 2. A request for `--follow` still exits 2 from the argument parser first (F0006-S0006).

Tests: `tests/entry/test_watch_settings.py`. F0006-S0006's test of its criterion 20, `tests/entry/test_watch.py::test_main_without_instance_settings_returns_2` (`main([])` with no boundaries returns 2 and writes the line `no instance settings are wired yet`), states the opposite of this story and is replaced by criteria 1 and 2 below. The tester deletes that one test function and the module constant `NOT_WIRED`, which only that test uses, in the tests stage (the coder's write paths hold no test), with the human's word of `FEATURE.md` decision 28, and changes nothing else in the file. The tests set the environment through `monkeypatch` and put the token file and the image id file into `tmp_path`.

## Acceptance criteria

1. `watch.main([])` with `FACTORY_REPOSITORY_URL` set and `FACTORY_INSTANCE` removed through `monkeypatch` returns 2, writes `factory-watch: settings invalid: FACTORY_INSTANCE: ` followed by the fault to `err` and nothing to `out`; the same holds when only `instance` is `None` and the `boundaries` fixture is given (two cases).
2. `watch.main([])` with a valid environment whose token file is missing returns 2 and its line names `FACTORY_TOKEN_FILE`.
3. `watch.main([])` with a valid environment (`FACTORY_REPOSITORY_URL=https://github.com/owner/project.git`, `FACTORY_INSTANCE`, and a token file and an image id file in `tmp_path`, set through `monkeypatch`) gets past the settings: it writes no `settings invalid` line to `err`, and it raises `GitError`, because the fixed checkout `/work/checkout` holds no clone (the test skips when `/work/checkout/.git` exists).
4. make check stays green.
5. docs: `docs/operator-guide.md` says that `factory-watch` reads the same environment as `factory-run`, and that with an invalid environment or an unreadable token file it prints `factory-watch: settings invalid: <variable>: <fault>` to standard error and exits with status 2.

## Demo

```bash
uv run python -c "
import io
from factory.entry.watch import main
out, err = io.StringIO(), io.StringIO()
print(main([], out=out, err=err))
print(repr(out.getvalue()))
print(err.getvalue().startswith('factory-watch: settings invalid: FACTORY_REPOSITORY_URL: '))
"
```
Expect: three lines, `2`, `''` and `True`: with no repository URL in the environment the watcher refuses at the first setting and writes nothing to standard output.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: `watch.main` signature is concrete (`src/factory/entry/watch.py`), the rule names `boundaries_from_environment(os.environ)`, `run_watch`, the exact stderr line, nothing on `out`, status 2, and the `--follow` parser exit kept. The removal of the old test and `NOT_WIRED` is covered by decision 28.
   - Criteria: each is testable by one test function. The failing sides are covered: the invalid environment (1, both cases), the unreadable token file (2) and the passing side (3, with the `GitError` from the empty fixed checkout and a skip when it exists). Criteria 4 and 5 close the list as required.
   - Demo: runnable as written; its Expect line (`2`, `''`, `True`) can be checked against the output.
   - Architecture: `entry` uses the previous story's `boundaries_from_environment`, as `factory.entry.run` does. Nothing is wired outside `factory.entry`.
   - Scope: within F0010 ("`factory-watch` reading the same settings"); nothing falls under Out of scope.
3. tester: Tests written for the watcher reading the instance's settings.

   - criterion 1: tests/entry/test_watch_settings.py::test_an_environment_without_an_instance_is_refused_with_a_line (parametrized: `nothing-given` with `boundaries=None, instance=None`; `boundaries` with the `boundaries` fixture and `instance=None`). Sets `FACTORY_REPOSITORY_URL` and removes `FACTORY_INSTANCE` through monkeypatch. Checks status 2, exactly one line on `err` starting `factory-watch: settings invalid: FACTORY_INSTANCE: ` with a non-blank fault, and nothing on `out`.
   - criterion 2: tests/entry/test_watch_settings.py::test_a_missing_token_file_is_refused_with_a_line_naming_it. Uses a valid environment with `FACTORY_TOKEN_FILE` pointing at a file in `tmp_path` that does not exist. Checks status 2, a line starting `factory-watch: settings invalid: FACTORY_TOKEN_FILE: `, and nothing on `out`.
   - criterion 3: tests/entry/test_watch_settings.py::test_a_valid_environment_gets_past_the_settings_to_the_fixed_checkout. Sets `FACTORY_REPOSITORY_URL=https://github.com/owner/project.git`, `FACTORY_INSTANCE`, and `FACTORY_TOKEN_FILE` and `FACTORY_IMAGE_ID_FILE` pointing at files in `tmp_path`. Expects `GitError` and no `settings invalid` on `err`. It skips when `/work/checkout/.git` exists. Building PyGithub is lazy (`pygithub_service`), so the test makes no network request.
   - criteria 4 and 5: not test-shaped (make check; docs stage).

   Files: created tests/entry/test_watch_settings.py. In tests/entry/test_watch.py I deleted `test_main_without_instance_settings_returns_2` and the constant `NOT_WIRED`, as the Interface and FEATURE.md decision 28 direct. Nothing else in that file changed.

   Red state (`make test`): all four new cases fail on wrong results, with no import errors, because `watch.main` still writes `no instance settings are wired yet`. Every module was imported. `make lint` is green.

   `make lint`: lint: green
   `make test`: FAILED tests/entry/test_watch_settings.py::test_a_valid_environment_gets_past_the_settings_to_the_fixed_checkout
