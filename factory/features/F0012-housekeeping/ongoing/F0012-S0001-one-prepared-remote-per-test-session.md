---
stage: tests
pr: 153
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# One prepared remote per test session

## Assignment (as of log entry 1)

`make test` is 88 % of `make check`, and 48 s of its 148 s of test time are fixtures' setup, mostly a real git remote built for each test: `make_remote` in `tests/git_support.py` runs six git processes (a seed repository, its commit, a bare repository, a push) every time the `remote` fixture or `build_world` is used. This story builds that remote once per test session (once per pytest-xdist worker, after the human's change H1) and gives each test a copy of the whole folder, seed and bare repository alike, so every test still starts from the same layout and what it pushes stays its own. It is test support only: the tester writes the helper, the fixtures and the new tests under `tests/`, so its tests pass at the tests stage, and the coder expects to change nothing under `src/` and only confirms `make check`. What any existing test asserts does not change; the human's leave covers the three helper files (FEATURE decision 32).

## Interface

`tests/git_support.py` gains one function; `make_remote` does not change:

```python
def copy_remote(template: Path, root: Path) -> Path:
    """Copy the folder `template`, which `make_remote` filled, into `root`; return `root / "remote.git"`."""
```

- `template` is the `root` an earlier `make_remote(template)` call filled: it holds `seed/` and `remote.git/`.
- `root` is created when missing (with its parents), and an existing `root` that holds neither is used as it is; a `root` that already holds `seed` or `remote.git` is refused with `FileExistsError`, and neither folder is copied.
- It copies files only: no git process runs, so it works with no `git` on the `PATH`.

`tests/conftest.py`:

```python
@pytest.fixture(scope="session")
def remote_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return the folder of one remote made per session, which each test's remote copies."""
    # make_remote(tmp_path_factory.mktemp("remote-template")).parent

@pytest.fixture
def remote(tmp_path: Path, remote_template: Path) -> Path:
    # copy_remote(remote_template, tmp_path / "origin")   (was: make_remote(tmp_path / "origin"))

@pytest.fixture
def world(tmp_path: Path, remote_template: Path) -> World:
    # build_world(tmp_path, template=remote_template)
```

`tests/proof_support.py`: `build_world(root: Path, *, template: Path | None = None) -> World`. With a `template`, its remote is `copy_remote(template, root / "origin")`; without one, `make_remote(root / "origin")` as today, so `run_case` and the acceptance scripts outside pytest still work.

Tests: a new module `tests/test_git_support.py`, with real git in `tmp_path` and the helpers `run_git`, `remote_commit`, `clone`, `make_remote` and `REMOTE_FILES` of `tests/git_support.py`; criterion 6 reads the `remote` and `remote_template` fixtures, every other criterion builds its own template with `make_remote`.

## Acceptance criteria

1. `copy_remote(template, root)` returns `root / "remote.git"`, a bare repository whose `main` is the commit the template's `remote.git` holds as `main`, and `root / "seed"` exists.
2. A clone of the copy holds on `main` exactly the files of `REMOTE_FILES` with their texts.
3. With a template made in the test by `make_remote(tmp_path / "template")` (never the session's `remote_template`): a commit pushed to `main` of the copy leaves the template's `main` at the commit it had, and a commit pushed to the template's `main` leaves the copy's `main` at the commit it had.
4. `copy_remote` into a `root` that does not exist yet (two levels deep) creates it, and into an existing empty `root` it copies as well; into a `root` that already holds `remote.git`, or `seed`, it raises `FileExistsError`, leaves that folder as it was and does not create the other one. The four cases are rows of one parametrized test.
5. With `PATH` set to an empty folder (`monkeypatch`), `copy_remote` still returns the copy; with `PATH` restored, the copy's `main` is the template's `main` commit.
6. The `remote` fixture's path is `tmp_path / "origin" / "remote.git"`, it is not inside the `remote_template` folder, and its `main` is the template's `main` commit.
7. `build_world(root, template=template)` builds a world whose remote's `main` is the template's `main` commit; `build_world(root)` without a template still builds a world whose remote holds `REMOTE_FILES` on `main`.
8. `make check` stays green.
9. docs: the project guide's paragraph on the `remote` fixture (section *The git wrapper*) says that the remote is built once per session (once per worker) and copied for each test with `copy_remote`, and that a test needing a remote of its own layout builds it with `make_remote`; the sentence on the `world` fixture (section *Kill points*, *The kill-point cases*) says it builds the world on a copy of that remote. No other document changes, and `python -m factory.entry.check_documents` still prints `documents ok`.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_git_support.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

```bash
uv run pytest --no-header -p no:cacheprovider tests/adapters/test_git_cli_writing.py tests/test_kill_points.py 2>&1 | tail -1
```
Expect: one line that reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-17 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`copy_remote` in `tests/git_support.py`, fixtures `remote_template`, `remote` and `world` in `tests/conftest.py`, `build_world(root, *, template=None)` in `tests/proof_support.py`), and the new test module. Each behaviour in it is stated precisely: the return value, root creation, the refusal with `FileExistsError`, and no git process.
   - Criteria: criteria 1 to 7 are each testable by one test function. Criterion 4 is one parametrized test with both sides of the rule: the two accepted roots, a missing one and an empty one, and the two refused roots, one holding `seed` and one holding `remote.git`. The refused rows also check that nothing is created. Criterion 5 covers the no-git rule. Criteria 3 and 6 pin the independence of the copy and its location. Criterion 7 covers both sides of the `template` parameter. Criteria 8 and 9 are the closing `make check` and docs criteria.
   - Demo: both commands are runnable. Each Expect line names an output that can be checked: the last line `<n> passed` with no failed, error or skipped count, and one line reporting `passed` with no `failed` or `error`.
   - Architecture: test support under `tests/` only, with nothing under `src/`. It follows CLAUDE.md: real git, no faked git, and fixtures in `tests/conftest.py`.
   - Scope: it matches FEATURE.md item 1.1 ("one prepared git remote copied per test (S0001)"). Decision 32 grants the leave to change the three helper files. Nothing in "Out of scope" is touched.
