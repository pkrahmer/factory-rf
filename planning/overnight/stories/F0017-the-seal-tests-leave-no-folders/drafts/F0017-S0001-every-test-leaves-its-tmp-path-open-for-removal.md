# Every test leaves its tmp_path open for removal

## Assignment (as of log entry 1)

pytest keeps the base folders of its last three sessions under `/tmp/pytest-of-<user>` and removes older ones at the start of a later session: it renames such a folder to `garbage-<uuid>` and removes it. A folder whose owner has lost the read or the search bit is one pytest cannot remove: its removal handler adds read and write bits only after a failed `unlink` or `rmdir`, never after a folder it could not open, so the `garbage-*` folder stays and every later session fails on it again. On 2026-10-18 v1's container held 10 `garbage-*` and 198 `pytest-*` folders, 5.4 GB, removed by hand as root (the night log, 07:37).

The seal itself closes nothing for its owner: `GitCli.seal()` takes only the group's and others' write bits. What closes `.git` is the mutant `make mutants` makes of `_close` in `src/factory/adapters/git_cli.py` when it drops the `~` of `stat.S_IMODE(mode) & ~SHARED_WRITE`: a `.git` at `0o2775` becomes `0o020`, a folder in it at `0o777` becomes `0o022`, closed to the test user. Every test that seals a `.git` (or an entry in it) with a group or others write bit then fails, as it should, and leaves that folder behind: the seal tests of F0014-S0006 (`tests/adapters/test_git_cli_seal.py`, the rows `git-folder` and `folder-inside`) and of S0009 and S0010 (`tests/application/test_sealed_runs.py`, `tests/application/test_checkout_preparer_seal.py`, `tests/application/test_nested_repositories.py`), and, where the checkout's `.git` is group-writable (umask `002` in v1.1's image), every test whose stage run seals its checkout. The tests that close a folder on purpose (`0o000`, `0o300`, `0o555`) open it again in a `finally` or a fixture, so under the built code a `make test` leaves nothing behind (FEATURE decision 1).

This story adds one fixture to `tests/conftest.py`, used by every test without being named: after each test that uses `tmp_path`, and after every other fixture of that test has been torn down, it gives the test user back read, write and search permission on every folder under `tmp_path` and read and write permission on every other entry, so pytest's own cleanup can remove the folder. The work is a helper in a new support module, tested on its own; a second test runs pytest in a child process to show that the fixture of `tests/conftest.py` does it. No `sudo` and no second user are needed: every entry under `tmp_path` belongs to the test user, who may change the mode of any of its own entries once the folders above them are searchable, and the walk opens each folder before it lists it (FEATURE decision 4). The tests of earlier stories keep what they check; only `tests/conftest.py` gains an import and the fixture (FEATURE decision 6). Every change is the tester's, under `tests/`; the coder has nothing to build.

The folders that mutmut's killed runs leave locked for three days are not this story's: a killed process runs no teardown. They are the human's change 1 to the `Makefile` (FEATURE decision 7).

## Interface

New module `tests/tmp_path_support.py` (standard library only):

- `reopen(root: Path) -> None`. Gives the owner read, write and search permission on `root` and on every folder below it (the old mode with `stat.S_IRWXU` added) and read and write permission on every other entry (the old mode with `stat.S_IRUSR | stat.S_IWUSR` added). Every other bit stays as it was, the setgid bit and the group's and others' bits included. Top down: a folder is changed before it is listed, so a folder closed to its owner is opened before the walk enters it (`os.walk(root, followlinks=False)` after changing `root`, each folder of a listing changed before the walk descends into it). A symbolic link is left as it is: neither the link nor its target is changed, and the walk does not enter it. A `root` that does not exist (`os.path.lexists`) is no error and changes nothing. No error is caught.

`tests/conftest.py`, one new fixture and the import of `reopen` from `tmp_path_support`; no existing fixture changes:

```python
@pytest.fixture(autouse=True)
def reopened_tmp_path(request: pytest.FixtureRequest) -> Iterator[None]:
    """After a test that uses `tmp_path`, give its owner back every folder and file under it."""
```

- When `"tmp_path"` is in `request.fixturenames` (the test or any fixture it uses asks for it), the fixture takes `request.getfixturevalue("tmp_path")` before it yields and calls `reopen` on it after the test. Being autouse, it is set up before the test's other fixtures and torn down after them, so it runs after every `finally` and fixture teardown of the test, and before pytest's own `tmp_path` teardown removes the folder of a passed test (`tmp_path_retention_policy = "failed"`).
- For a test that does not use `tmp_path` it creates no folder and does nothing.

Tests: new module `tests/test_tmp_path_reopening.py`, with `TESTS = Path(__file__).parent`.

- `test_reopen_gives_the_owner_back_every_folder_and_entry_and_keeps_every_other_bit`, parametrized over (arrange, expected) rows. Each row builds a tree at `tree = tmp_path / "tree"` and sets every mode it names with `chmod` (innermost first), whatever the umask; `expected` maps each path relative to `tree` (`"."` for `tree` itself) to its mode after `reopen(tree)`, read with `stat.S_IMODE(path.lstat().st_mode)`. After the modes, `shutil.rmtree(tree)` runs and `tree` no longer exists.
  - `sealed-git-folder`: `tree` `0o755`, `checkout/.git/HEAD` a file `0o644`, `checkout` `0o755`, `checkout/.git` `0o020` (the mutant's seal of a `0o2775` folder). Expected: `.` `0o755`, `checkout` `0o755`, `checkout/.git` `0o720`, `checkout/.git/HEAD` `0o644`.
  - `no-search`: `tree` `0o755`, `folder` `0o600` holding `folder/file` `0o644`. Expected: `folder` `0o700`, `folder/file` `0o644`, `.` `0o755`.
  - `no-read`: `tree` `0o755`, `folder` `0o300` holding `folder/file` `0o644`. Expected: `folder` `0o700`, `folder/file` `0o644`, `.` `0o755`.
  - `no-write`: `tree` `0o755`, `folder` `0o555` holding `folder/file` `0o444` and `folder/sub` `0o555`. Expected: `folder` `0o755`, `folder/file` `0o644`, `folder/sub` `0o755`, `.` `0o755`.
  - `closed-inside-closed`: `tree` `0o755`, `outer/inner/file` with `file` `0o000`, `inner` `0o000`, `outer` `0o000`. Expected: `outer` `0o700`, `outer/inner` `0o700`, `outer/inner/file` `0o600`, `.` `0o755`.
  - `closed-root`: `tree` `0o000` holding `file` `0o644`. Expected: `.` `0o700`, `file` `0o644`.
  - `open-with-setgid`: `tree` `0o755`, `.git` `0o2775` holding `.git/config` `0o664`. Expected: `.git` `0o2775`, `.git/config` `0o664`, `.` `0o755` (nothing changes).
- `test_reopen_leaves_a_symbolic_link_and_its_target_as_they_are`, parametrized over three rows; each makes `tree = tmp_path / "tree"` at `0o755` holding the link `tree/link`, calls `reopen(tree)`, and checks that `tree/link` is still a symbolic link with the same `os.readlink` text and that the target's mode is the one it was given.
  - `link-to-a-folder`: the target is the folder `tmp_path / "outside"` at `0o500`; it stays `0o500`.
  - `link-to-a-file`: the target is the file `tmp_path / "outside.txt"` at `0o400`; it stays `0o400`.
  - `dangling`: the target `tmp_path / "missing"` does not exist; `reopen` raises nothing and the link stays.
- `test_reopen_of_a_missing_root_changes_nothing`: `reopen(tmp_path / "missing")` raises nothing, `tmp_path / "missing"` does not exist after it, and `tmp_path` holds no new entry.
- `test_a_test_that_closes_folders_in_its_tmp_path_leaves_them_open_after_its_teardown`, two rows, `with-conftest` and `without-conftest`. Each writes `inner = tmp_path / "inner"` with `inner / "pytest.ini"` holding `[pytest]\ntmp_path_retention_policy = all\n` and `inner / "test_inner.py"` holding exactly:

  ```python
  from pathlib import Path


  def test_closes_its_tmp_path(tmp_path: Path) -> None:
      git = tmp_path / "checkout" / ".git"
      (git / "objects").mkdir(parents=True)
      (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
      git.chmod(0o020)
      closed = tmp_path / "closed"
      (closed / "inner").mkdir(parents=True)
      closed.chmod(0o000)


  def test_uses_no_tmp_path() -> None:
      assert True
  ```

  It runs, through `run_process` (`factory.adapters.process`), `ProcessRequest(argv=[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-c", str(inner / "pytest.ini"), "--rootdir", str(inner), "--basetemp", str(base), *plugin, str(inner / "test_inner.py")], cwd=inner, env=env, time_limit=timedelta(seconds=120))`, with `base = tmp_path / "base"`, `plugin` `["-p", "conftest"]` for `with-conftest` and `[]` for `without-conftest`, and `env` the test process's environment without the variables whose names start with `PYTEST_`, plus `PYTHONPATH` set to `str(TESTS)`. `-p conftest` loads `tests/conftest.py` as a plugin, so its autouse fixture applies to the inner tests. Then, for both rows: the exit status is `0`, the output names `2 passed`, and `base / "test_uses_no_tmp_path0"` does not exist. `left = base / "test_closes_its_tmp_path0"`: with `with-conftest`, `left / "checkout" / ".git"` is at `0o720` and `left / "closed"` at `0o700`, and `shutil.rmtree(base)` removes `base`; with `without-conftest`, they are still at `0o020` and `0o000` (the outer test's own fixture opens them after it).

No file under `src/`, `image/`, `template/`, `claude/` or `docs/` is changed by the tester; no test of an earlier story changes but `tests/conftest.py` as stated.

## Acceptance criteria

1. `reopen` opens a closed tree for its owner: a `.git` at `0o020`, a folder without the search bit (`0o600`), one without the read bit (`0o300`), one without the write bit (`0o555`, with a read-only file and folder in it), a closed folder inside a closed folder with a closed file in it, and a closed root each end with the owner's bits added as the Interface lists, and `shutil.rmtree` then removes the tree. Rows `sealed-git-folder`, `no-search`, `no-read`, `no-write`, `closed-inside-closed` and `closed-root` of `test_reopen_gives_the_owner_back_every_folder_and_entry_and_keeps_every_other_bit`.
2. `reopen` keeps every other bit: an open `.git` at `0o2775` with a file at `0o664` keeps both modes, the setgid bit included, and the group's and others' bits of the closed rows stay as they were (the `.git` at `0o020` ends at `0o720`). Row `open-with-setgid` of the same test, and the expected modes of the other rows.
3. `reopen` does not follow a symbolic link: a link to a folder at `0o500` or to a file at `0o400` outside the tree leaves the target's mode as it was and the link in place, and a dangling link is no error: `test_reopen_leaves_a_symbolic_link_and_its_target_as_they_are`, rows `link-to-a-folder`, `link-to-a-file` and `dangling`.
4. A root that does not exist is no error and nothing is created: `test_reopen_of_a_missing_root_changes_nothing`.
5. The autouse fixture `reopened_tmp_path` of `tests/conftest.py` opens what a test closed in its `tmp_path`, after the test: run in a child pytest with `-p conftest`, a test that leaves a `.git` at `0o020` and a folder at `0o000` leaves them at `0o720` and `0o700`, and the base folder can be removed with `shutil.rmtree`; run without it, they stay at `0o020` and `0o000`. Rows `with-conftest` and `without-conftest` of `test_a_test_that_closes_folders_in_its_tmp_path_leaves_them_open_after_its_teardown`.
6. The fixture creates no folder for a test that does not use `tmp_path`: in both rows of the same test, `base / "test_uses_no_tmp_path0"` does not exist.
7. What must still hold: every test of `tests/adapters/test_git_cli_seal.py`, `tests/adapters/test_git_cli_nested.py`, `tests/application/test_sealed_runs.py`, `tests/application/test_checkout_preparer_seal.py`, `tests/application/test_nested_repositories.py` and `tests/entry/test_git_repository_modes.py` passes with the fixture in place, and checks what it checks today; none of these modules changes. `tests/conftest.py` gains the import of `reopen` and the fixture `reopened_tmp_path`, and every fixture it already holds stays as it is.
8. Every change of this story is under `tests/` and is the tester's: `tests/tmp_path_support.py`, `tests/test_tmp_path_reopening.py` and `tests/conftest.py`. No file under `src/` changes; the coder has nothing to build and commits nothing, and the new tests pass from the tests stage on.
9. `make check` stays green.
10. docs: the project guide's paragraph on tests with real git (the one that begins "Tests use real git") gets a sentence after it: the autouse fixture `reopened_tmp_path` in `tests/conftest.py` calls `reopen(tmp_path)` (`tests/tmp_path_support.py`) after every test that uses `tmp_path`, after the test's own teardowns, giving the owner back read, write and search permission on every folder and read and write on every other entry, links not followed; so a test that closes a folder, or a mutant of the seal that closes `.git`, leaves nothing pytest cannot remove, and a test need not open what it closed for that reason. The decision log gets an entry, "The tests reopen their tmp_path after every test", with the cause (pytest's removal handler does not open a folder it cannot list; the `make mutants` mutant of `_close` that drops the `~` closes `.git` to `0o020`, which left `garbage-*` folders in v1's container), the decision, and the rejected ways: a fixture on the seal tests alone, sealing a copy in each test, `sudo` or a second user, and a sweep of `/tmp/pytest-of-<user>` at the start of a session.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/test_tmp_path_reopening.py tests/adapters/test_git_cli_seal.py tests/adapters/test_git_cli_nested.py tests/application/test_sealed_runs.py tests/application/test_checkout_preparer_seal.py tests/application/test_nested_repositories.py tests/entry/test_git_repository_modes.py
```
Expect: the last line names `<n> passed`, with no `failed`, `error` or `skipped` count.

```bash
uv run python -c "
import shutil, stat, sys, tempfile
from pathlib import Path
sys.path.insert(0, 'tests')
from tmp_path_support import reopen
root = Path(tempfile.mkdtemp())
git = root / 'checkout' / '.git'
(git / 'objects').mkdir(parents=True)
(git / 'HEAD').write_text('ref: refs/heads/main\n', encoding='utf-8')
git.chmod(0o020)
reopen(root)
print(oct(stat.S_IMODE(git.stat().st_mode)))
shutil.rmtree(root)
print(root.exists())
"
```
Expect: two lines: `0o720`, then `False`.

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`.

## Log (append only)

1. 2026-10-18 human: created.
