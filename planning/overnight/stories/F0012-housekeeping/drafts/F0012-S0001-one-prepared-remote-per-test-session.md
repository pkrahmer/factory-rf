# One prepared remote per test session

## Assignment (as of log entry 1)

`make test` is 88 % of `make check`, and 48 s of its 148 s of test time are fixtures' setup, mostly a real git remote built for each test: `make_remote` in `tests/git_support.py` runs six git processes (a seed repository, its commit, a bare repository, a push) every time the `remote` fixture or `build_world` is used. This story builds that remote once per test session (once per pytest-xdist worker, after the human's change H1) and gives each test a copy of the whole folder, seed and bare repository alike, so every test still starts from the same layout and what it pushes stays its own. It is test support only: the tester writes it under `tests/`, and the coder expects to change nothing under `src/`. What any existing test asserts does not change; the human's leave covers the three helper files (FEATURE decision 32).

## Interface

`tests/git_support.py` gains one function; `make_remote` does not change:

```python
def copy_remote(template: Path, root: Path) -> Path:
    """Copy the folder `template`, which `make_remote` filled, into `root`; return `root / "remote.git"`."""
```

- `template` is the `root` an earlier `make_remote(template)` call filled: it holds `seed/` and `remote.git/`.
- `root` is created when missing (with its parents); a `root` that already holds `seed` or `remote.git` is refused with `FileExistsError`, and nothing is copied.
- Symbolic links are copied as links. No git process runs.

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

Tests: a new module `tests/test_git_support.py`, with real git in `tmp_path` and the helpers `run_git`, `remote_commit`, `clone` and `REMOTE_FILES` of `tests/git_support.py`.

## Acceptance criteria

1. `copy_remote(template, root)` returns `root / "remote.git"`, a bare repository whose `main` is the commit the template's `remote.git` holds as `main`, and `root / "seed"` exists.
2. A clone of the copy holds on `main` exactly the files of `REMOTE_FILES` with their texts.
3. A commit pushed to `main` of the copy leaves the template's `main` at the commit it had, and a commit pushed to the template's `main` leaves the copy's `main` at the commit it had.
4. `copy_remote` into a `root` that does not exist yet (two levels deep) creates it; into a `root` that already holds `remote.git`, or `seed`, it raises `FileExistsError` and leaves that folder as it was. The three cases are rows of one parametrized test.
5. The `remote` fixture's path is `tmp_path / "origin" / "remote.git"`, it is not inside the `remote_template` folder, and its `main` is the template's `main` commit.
6. `build_world(root, template=template)` builds a world whose remote's `main` is the template's `main` commit; `build_world(root)` without a template still builds a world whose remote holds `REMOTE_FILES` on `main`.
7. `make check` stays green.
8. docs: the project guide's paragraph on the `remote` fixture (section *The git wrapper*) says that the remote is built once per session and copied for each test, and that a test needing a remote of its own layout builds it with `make_remote`. No other document changes.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_git_support.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

```bash
uv run pytest --no-header -p no:cacheprovider -q tests/adapters/test_git_cli_writing.py tests/test_kill_points.py 2>&1 | tail -1
```
Expect: one line that reports `passed` and neither `failed` nor `error`.

## Log (append only)

1. 2026-10-17 human: created.
