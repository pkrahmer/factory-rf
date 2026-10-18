---
stage: done
pr: 153
blocked: null
comments_seen: 1
round: 0
attempts: 1
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
3. tester: I wrote the helper, the fixtures and the tests, all under `tests/`. The suite is green, not red: the story is test support only, so the code the tests exercise lives in `tests/` and is already there. `make test` passes in 34.8 s with 99.53 % coverage. `make lint` and `make types` are green too.
   - Helper: `tests/git_support.py::copy_remote(template, root)`. It first refuses a `root` that holds `seed` or `remote.git` with `FileExistsError`, before it creates or copies anything. Then it runs `mkdir(parents=True, exist_ok=True)` and `shutil.copytree(..., symlinks=True)` on `seed/` and `remote.git/`. No git process runs.
   - Fixtures in `tests/conftest.py`:
     - new session-scoped `remote_template`, which is `make_remote(tmp_path_factory.mktemp("remote-template")).parent`;
     - `remote` is now `copy_remote(remote_template, tmp_path / "origin")`;
     - `world` is now `build_world(tmp_path, template=remote_template)`.
   - `tests/proof_support.py::build_world(root, *, template=None)` copies the template when one is given and calls `make_remote` otherwise.
   - New module `tests/test_git_support.py`. Every test except the `remote` fixture test uses its own `template` fixture, built with `make_remote(tmp_path / "template")`, and pushes are real git. I did not use `commit_all`; the commit in `_push_commit` uses `run_git`.

   Criterion → test:
   - criterion 1: tests/test_git_support.py::test_copy_is_a_bare_remote_at_the_templates_main
   - criterion 2: tests/test_git_support.py::test_clone_of_the_copy_holds_exactly_the_remote_files
   - criterion 3: tests/test_git_support.py::test_push_to_the_copy_leaves_the_template_alone and ::test_push_to_the_template_leaves_the_copy_alone (one test per direction)
   - criterion 4: tests/test_git_support.py::test_copy_creates_its_root_and_refuses_one_already_filled. Four rows: a root two levels deep that does not exist, an empty root, a root holding `remote.git`, a root holding `seed`. The refused rows check that the existing folder keeps only its marker file and the other folder is not created.
   - criterion 5: tests/test_git_support.py::test_copy_runs_no_git (`PATH` is an empty folder inside `monkeypatch.context()`, and `main` is checked after `PATH` is restored)
   - criterion 6: tests/test_git_support.py::test_remote_fixture_is_a_copy_of_the_session_template
   - criterion 7: tests/test_git_support.py::test_world_with_a_template_copies_its_remote and ::test_world_without_a_template_makes_its_own_remote
   - criteria 8 and 9 have no tests: 8 is the `make check` gate and 9 is for the documenter.

   Rejected: a parametrized test for criterion 7. Its two sides assert different things (the template's commit versus `REMOTE_FILES`), so they are two functions.

   Files: created `tests/test_git_support.py`; changed `tests/git_support.py`, `tests/conftest.py` and `tests/proof_support.py`.

   Unimportable modules: none.

   Open for the coder: nothing under `src/` is expected to change; confirm `make check`.

   `make lint`: lint: green (0.0 s)
   `make test`: test: green (32.5 s)
4. coder: I confirmed `make check` and changed nothing. As the Assignment and the tester's entry expected, the story is test support only. The tester's work holds all of it:
   - `copy_remote` in `tests/git_support.py`;
   - the `remote_template`, `remote` and `world` fixtures in `tests/conftest.py`;
   - `build_world(root, *, template=None)` in `tests/proof_support.py`;
   - the new tests in `tests/test_git_support.py`.

   Nothing under `src/` needs to change for any criterion, so I made no commit.

   Refactor step: `git diff main...HEAD -- . ':!factory' ':!tests'` is empty, so there is nothing of mine to clean up. The coder does not edit the test helpers.

   `make check`: check: green (test: green (34.6 s), coverage 99.53 %).

   Open: criterion 9 (the project guide's paragraphs on the `remote` and `world` fixtures) is for the documenter.

   `make check`: check: green
5. reviewer: no findings.
      - Acceptance criteria: each of criteria 1 to 7 maps to a test in `tests/test_git_support.py` that checks what the criterion says.
        - Criterion 1 checks the return path, that the copy is bare, that its `main` equals the template's, and that `seed/` exists.
        - Criterion 2 compares a clone's files with `REMOTE_FILES`, skipping `.git`.
        - Criterion 3 checks independence both ways, against a template the test makes itself.
        - Criterion 4 is one parametrized test with four rows: a missing root two levels deep, an empty root, a root holding `remote.git`, and a root holding `seed`. The refused rows check that the folder already there keeps only its marker and that the other folder is not created.
        - Criterion 5 sets `PATH` to an empty folder inside `monkeypatch.context()` and checks `main` after `PATH` is restored.
        - Criterion 6 checks the fixture's path, that it is outside the template, and its commit.
        - Criterion 7 has one test for each side of `template`.
        - The coder's entry reports `make check` green.
      - Behaviour: `copy_remote` (`tests/git_support.py:126`) refuses with `FileExistsError` before it creates anything, so a refused root gets nothing new. It copies with `shutil.copytree(..., symlinks=True)` only, so no git process runs.
      - Session template: the copied `seed` has no remote configured, because `make_remote` pushes to an explicit path. So a copy points at nothing in the session template, and no test writes to `remote_template` itself (it is read only in `tests/conftest.py` and in the criterion 6 test).
      - Architecture: nothing under `src/` changes, and git is not faked. The new fixture is in `tests/conftest.py` and the new test module sits at the `tests/` root, as CLAUDE.md asks for a module outside the layers.
      - Security: none of the four changed files adds a secret, a suppression marker or a string-built command.
      - Quality: the names say what things are and the docstrings are present.
      - Considered and not raised: the criterion 4 test decides whether to create the root by checking the row's string `"missing/two-deep"` instead of a row parameter. It reads clearly enough and is not wrong.
      - Ticket hygiene: the Assignment matches what was built, and the tester's entry explains the rejected parametrization of criterion 7.
      - Open for the documenter: criterion 9, the project guide's paragraphs on the `remote` fixture (*The git wrapper*) and the `world` fixture (*Kill points*, *The kill-point cases*).
6. documenter: criterion 9 done, no findings.
   - Changed `docs/project-guide.md`, section *The git wrapper*: the `remote` fixture paragraph now says `make_remote` builds the remote once per session (once per worker, as `remote_template`). Each test gets a copy of the whole folder (seed and bare repository) from `copy_remote(template, root)`, which runs no git process. A test that needs a remote of its own layout builds it with `make_remote`.
   - Changed `docs/project-guide.md`, section *Kill points*, *The kill-point cases*: the `world` fixture sentence now says it returns `build_world(tmp_path, template=remote_template)`, the world on a copy of that remote. It also says `build_world(root)` without a template makes its own remote.
   - Ran `python -m factory.entry.check_documents`: it prints `documents ok`. I ran no `make check`, since only a document changed.
   - Cross-read: the diff touches only `tests/`, with nothing under `src/`. A grep of `docs/` and the README for `make_remote`, `remote` fixture and `world` fixture found no other mention. README and `docs/operator-guide.md` do not describe test fixtures, so they stay current.
   - Stale but unrelated: none seen.
7. stage docs stalled: `make check` is red after the stage:
   src/factory/domain/board.py                        55      0      4      1    98%   72->70
   src/factory/entry/check_documents.py               26      1      8      1    94%   37
   src/factory/entry/check_story.py                   80      1     18      1    98%   131
   src/factory/entry/guard.py                         37      1     10      1    96%   56
   src/factory/entry/health.py                        28      1      6      1    94%   42
   src/factory/entry/run.py                           65      1      2      1    97%   158
   src/factory/entry/watch.py                         52      1      6      2    95%   76->83, 87
   -------------------------------------------------------------------------------------------
   TOTAL                                            6584     18   1292     19    99%

   93 files skipped due to complete coverage.
   Required test coverage of 90.0% reached. Total coverage: 99.53%
   =========================== short test summary info ============================
   FAILED tests/adapters/test_make_commands.py::test_command_reaching_its_time_limit_is_killed
   make: *** [Makefile:74: test] Error 1; partial work committed
8. documenter: documenter, round 0 rerun after the stall in entry 7. Criterion 9 stays as entry 6 wrote it, and I changed no file this run.
   - `docs/project-guide.md` (*The git wrapper*, *The kill-point cases*) still has the `remote` and `world` fixture text from entry 6. `python -m factory.entry.check_documents` prints `documents ok`.
   - The stall was `tests/adapters/test_make_commands.py::test_command_reaching_its_time_limit_is_killed`. That test failed once in the full parallel run. It has nothing to do with this story, which touches only `tests/conftest.py`, `tests/git_support.py`, `tests/proof_support.py` and `tests/test_git_support.py`. I ran the module on its own and all 26 tests pass. It looks timing-sensitive under load. This is a note, not a finding, and I changed nothing. Coverage was 99.53 % and nothing else failed.
   - Cross-read: the README and `docs/operator-guide.md` do not describe test fixtures, so they are current.
   - I ran no `make check`, since I changed no file outside the documents. The factory's run after this stage is the gate.
   - Stale but unrelated: none seen.

   `make check`: check: green
9. demo: I ran both demo commands from the repository root exactly as written. Both met their `Expect:` lines, and I have no findings.

   1. `uv run pytest --no-header -p no:cacheprovider tests/test_git_support.py`
   ```
   ............                                                             [100%]
   12 passed in 1.11s
   ```
   Met. The last line reads `12 passed in 1.11s`, with no `failed`, `error` or `skipped` count.

   2. `uv run pytest --no-header -p no:cacheprovider tests/adapters/test_git_cli_writing.py tests/test_kill_points.py 2>&1 | tail -1`
   ```
   81 passed in 46.33s
   ```
   Met. The one line reports `passed`, with no `failed` or `error`. These two modules use the `remote` and `world` fixtures, which now copy the session's remote. All of their tests pass unchanged.

   Acceptance criteria re-read:
   - Criteria 1 to 7 are the 12 tests in `tests/test_git_support.py`. They passed, and the demo contradicts none of them.
   - Criterion 8: the demo does not touch `make check`; the factory runs it as the gate.
   - Criterion 9: the documenter covered it in entries 6 and 8, and nothing in the demo goes against it.

   Open: none.
10. done (pull request merged); cost: 7 runs, 5.1 min, 39 turns, 150k tokens in (495k more from cache), 14k out, $1.29
