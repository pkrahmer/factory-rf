# The seal tests leave no folders

## Goal

factory-rf's own test runs filled pytest's temporary root in v1's container: on 2026-10-18 `/tmp/pytest-of-factory` held 10 `garbage-*` and 198 `pytest-*` folders, 5.4 GB, removed by hand as root (the night log, `docs/runs/2026-10-12-overnight/night-log.md`, the rows of 07:08 and 07:37). By 11:10 UTC the same day it held 58 `pytest-*` folders again, 2.4 GB. The human chose a fixture that opens what the seal tests closed (to-do item 17, 2026-10-18); v1 builds it here before the handover. Looking closer (FEATURE decision 1), the folders come from `make mutants`, not from `make test`, and they come in two kinds. (1) `garbage-*`: a mutant of the seal closes `.git` to its own user, the test fails as it should, and pytest's later cleanup cannot remove the folder; it renames it to `garbage-<uuid>` and fails on it at every session after that. (2) `pytest-*` folders whose `.lock` file stays: mutmut stops a mutant's pytest at its time limit, the stopped process never removes its lock, and pytest leaves a locked folder alone for three days. This feature is for whoever runs factory-rf's tests: v1 while it builds v1.1, then v1.1's own instance, the operator's machine and a project's acceptance. When it is done, every test that uses `tmp_path` leaves its folder open to its owner after its teardown, whatever the test or a mutant closed, so pytest's own cleanup removes it. With the human's change 1, a `make mutants` run also leaves no locked folder behind. Done when S0001 is merged and `make check` is green.

## Scope

- A helper `reopen(root)` in a new support module `tests/tmp_path_support.py`, which gives the owner back read, write and search permission on every folder under a root and read and write permission on every other entry, top down, links not followed; and an autouse fixture in `tests/conftest.py` that calls it on `tmp_path` after every test that uses `tmp_path` (S0001).
- A test that runs pytest in a child process with `tests/conftest.py` as a plugin, to show that the fixture opens what a test closed (S0001).
- The project guide's sentence on the fixture and a decision log entry (S0001, its docs criterion).

## Out of scope

- The `pytest-*` folders that stay locked after mutmut stops a run: a stopped process runs no teardown, so no fixture can reach them. They are the human's change 1 to the `Makefile` (decision 7).
- Removing the 58 folders in v1's container now (2.4 GB, from F0016's acceptance): a deletion, the human's OK (decision 9).
- The restores the tests of earlier stories already make (`finally` blocks and fixtures that open `0o000`, `0o300` and `0o555` folders): they stay as they are (decision 6).
- The seal (`GitCli.seal()`, `_close`), its error and every other part of `src/`: no behaviour of the factory changes.
- `pyproject.toml`'s `tmp_path_retention_policy` and `[tool.mutmut]` settings (decision 8).
- The folders `tmp_path_factory` makes for session fixtures (`remote_template`, the `calls` of `tests/adapters/test_shipped_agents_effect.py`): no test closes them.

## Stories

- S0001 — Every test leaves its tmp_path open for removal

One story: the helper, the fixture and their tests are one tester's work of about 150 lines, under `tests/` only (decision 10).

## The human's changes

Checked on 2026-10-18 against `factory/stages.yml`: the tester writes `tests/*`, which holds every change of S0001; the coder (`src/*`, `image/*`, `template/*`, `claude/*`) has nothing to build; the documenter writes `README.md` and `docs/*`. No stage writes `Makefile`, `pyproject.toml`, `factory/stages.yml` or `security/*`. S0001 needs none of them: no dependency, no `Makefile` target, no pipeline change, no `security/*` entry and no `.secrets.baseline` entry.

1. **The `mutants` target runs mutmut under a temporary root of its own** (decision 7), before S0001 or at any time; S0001 does not depend on it and no test reads the target. In factory-rf's `Makefile`, in the recipe of `mutants:`, insert before the line

   ```
   	# An agent's shell command ends after 10 minutes: stop mutmut before that and report what it
   ```

   the four lines

   ```
   	# mutmut stops a mutant's pytest at its time limit, which leaves that run's folder locked for
   	# three days under pytest's root in /tmp: give each run a root of its own and remove it after.
   	temporary=$$(mktemp -d)
   	trap 'chmod -R u+rwX "$$temporary" 2>/dev/null || true; rm -rf "$$temporary" || true' EXIT
   ```

   and in the line after the comment, change its beginning

   ```
   	timeout $(MUTANTS_SECONDS) uv run mutmut run
   ```

   to

   ```
   	TMPDIR="$$temporary" timeout $(MUTANTS_SECONDS) uv run mutmut run
   ```

   leaving the rest of that line as it is. The recipe runs as one `bash -eu -o pipefail` script (`.ONESHELL`), so the trap removes the folder when the recipe ends, after `mutmut results` too, whether mutmut finished, was stopped at `MUTANTS_SECONDS` or failed; the `chmod` also opens what a stopped run left closed. After it, `make mutants FEATURE=F0014` (a feature that changed `git_cli.py`) leaves `/tmp/pytest-of-<user>` as it found it. v1 runs the target from the acceptance branch, so the change counts for the first acceptance after it reaches `main`.

## Decisions taken for the human

Product decisions taken while writing the story, for the human to review in one place. Each names where it was taken. Source of all: the drafting brief `planning/overnight/briefs/draft-F0017.md` (the session's proposal, chosen by the human on 2026-10-18 as to-do item 17), the night log's rows of 2026-10-18 07:08 and 07:37, and what the drafting agent found on 2026-10-18 at about 11:10 UTC in v1's container (read only) and in the installed pytest 9.1.1, pytest-xdist 3.8.0 and mutmut 3.8.0.

1. **Which tests leave folders, and why.** (Feature, S0001)
   - Under the built code, `make test` leaves nothing pytest cannot remove. `GitCli.seal()` only takes the group's and others' write bits; the owner keeps read, write and search. Every test that closes a folder for its owner on purpose opens it again: `test_seal_refuses_a_folder_inside_that_it_cannot_list_and_names_it` (`0o300`) and `test_discard_that_cannot_remove_a_file_is_a_git_error` (`0o555`) in a `finally`, `tests/adapters/test_git_cli_nested.py` (`closed` `0o000`, `locked` `0o555`) in its `directory` fixture, `tests/application/test_nested_repositories.py` in its `reopen` fixture, `tests/application/test_checkout_preparer_seal.py`, `tests/application/test_tick.py` and `tests/application/test_tick_stale_branch.py` in a `finally`. In v1's container at 11:10 UTC, none of the 58 folders held an entry that is not `factory`'s or a folder without the owner's read, write or search bit.
   - The `garbage-*` folders: `make mutants` over `src/factory/adapters/git_cli.py` (F0014's acceptance, and every later feature that changes it) makes a mutant that drops the `~` in `_close` (`stat.S_IMODE(mode) & ~SHARED_WRITE` becomes `& SHARED_WRITE`; mutmut's `operator_remove_unary_ops`). The seal then sets a `.git` at `0o2775` to `0o020` and a folder in it at `0o777` to `0o022`: no read, no search, no write for the owner. The tests that seal such a `.git` or entry fail, as they should: `tests/adapters/test_git_cli_seal.py` (F0014-S0006, rows `git-folder` and `folder-inside`), `tests/application/test_sealed_runs.py` (S0009, its `0o2775` folder), `tests/application/test_checkout_preparer_seal.py` (S0006 and S0010, its `0o2775` folders), `tests/application/test_nested_repositories.py` (S0010, `0o2775`), and under the umask `002` of v1.1's image every test whose stage run seals a checkout (git makes `.git` group-writable there). pytest keeps a failed test's folder (`tmp_path_retention_policy = "failed"`); a later session renames it to `garbage-<uuid>` and calls its `rm_rf`, whose handler adds read and write bits only after a failed `unlink` or `rmdir`, never after a folder it could not open (`os.open`). So the folder stays, and every later session fails on it again.
   - The `pytest-*` folders: every one of the 58 held its `.lock` file and only the tests of one mutant (the fault-path world tests `agent-run-dies`, `agent-run-tick`, `commit-push`, `container`), dated 09:17 to 09:46 UTC, which is F0016's acceptance running `make mutants` over `stage.py` (11:12 to 11:58 local). mutmut runs each mutant's tests in a forked process under a time limit and stops it with `SIGXCPU` (and `timeout $(MUTANTS_SECONDS)` stops mutmut itself); a stopped pytest never closes its exit stack, so its lock stays, and pytest removes a locked folder only when the lock is older than three days (`LOCK_TIMEOUT`). They are removable, not closed. The 198 of 07:37 were most likely the same kind; they were removed before anyone looked.
   - Under which user: in v1's container every stage and `make test` run as `factory` (uid 1000), the only user, umask `0022`; the folder is `/tmp/pytest-of-factory`. In v1.1's image the factory's project commands run as `factory` (uid 1000) and the agents' own runs as `agent` (uid 1001), both in the group `factory-work`, under umask `002`; each has its own `/tmp/pytest-of-<user>`. Neither is root, so the tests marked to skip for root run.
2. **A fixture for every test that uses `tmp_path`, not for the seal tests alone.** The mutant closes `.git` in any test that seals, which under umask `002` is every stage-run test, and a list of the tests that seal would go stale with the next story. An autouse fixture needs no test to name it. Its cost is one walk of each test's `tmp_path` after the test. (S0001)
   - Rejected: a fixture used by the seal test modules only. It misses the stage-run tests, and the next sealing test.
   - Rejected: each test seals a copy it owns. The test already owns its `.git`; the copy would be just as closed, and every seal test would change.
3. **The work in a helper of a support module, the fixture thin.** `reopen(root)` in `tests/tmp_path_support.py` is tested directly, row by row; the fixture in `tests/conftest.py` only decides when to call it. The wiring is tested by running pytest in a child process with `-p conftest` (the real `tests/conftest.py` as a plugin, its folder on `PYTHONPATH`), once with and once without the plugin, so the test shows both that the fixture opens the folders and that without it they stay closed. The drafting agent checked on the host that `-p conftest` loads such a module's autouse fixture, that `request.fixturenames` holds `tmp_path` when only a fixture of the test asks for it, and that the autouse fixture's teardown runs after the other fixture's. (S0001)
   - Rejected: pytest's `pytester` plugin. Loading the real `tests/conftest.py` into its inner session clashes with the inner conftest module name; the child process is simpler and uses `run_process` as other tests do.
   - Rejected: a structural test that reads `tests/conftest.py`. It would hold the text, not that the fixture runs after the test's teardowns.
4. **No `sudo`, no second user, no root.** Every entry under `tmp_path` belongs to the test user: the tests that need another user fake it (`monkeypatch` of `os.geteuid` in `tests/adapters/test_git_cli_seal.py`). A user may change the mode of any entry of its own whatever that mode is, once it can reach it; the walk changes each folder before it lists it, so it reaches every entry. As root everything is removable anyway, and the fixture does the same. No error is caught: an entry the test user cannot change would fail the test's teardown with its path, which no test of today can make. (S0001)
5. **What `reopen` changes.** It adds `S_IRWXU` to folders and `S_IRUSR | S_IWUSR` to every other entry, and keeps every other bit (the setgid bit, the group's and others' bits), so a test that reads a mode after its own teardown, or a kept failed folder, still shows what the test left, with the owner's bits added. It does not follow or change a symbolic link: a test may link to a folder outside its `tmp_path` (`tests/adapters/test_git_cli_seal.py` links to a file beside the checkout, `tests/adapters/test_git_cli_nested.py` to the checkout's parent). A missing root is no error, for a test that removes its own `tmp_path`. (S0001)
6. **Earlier stories' tests stay as they are; the leave for `tests/conftest.py`.** The `finally` blocks and fixtures that open `0o000`, `0o300` and `0o555` folders are redundant once the fixture is in place, but they are other stories' tests and harmless; removing them would change what those tests show for no gain. The human's leave (taken by the session for the human, to confirm): `tests/conftest.py` (written and extended by many earlier stories) gains the import `from tmp_path_support import reopen` and the fixture `reopened_tmp_path`; no existing fixture, import or constant there changes. No other earlier test changes. (S0001)
7. **The locked `pytest-*` folders: a temporary root per `make mutants` run** (the human's change 1). `TMPDIR` points mutmut, and with it every pytest it starts, at a folder made by `mktemp -d`; the recipe's `EXIT` trap opens and removes it. It reaches what no fixture can: a stopped process, its lock and anything it left closed. It is outside every write path, so it is the human's. (Feature)
   - Rejected: `-o tmp_path_retention_policy=none` in `[tool.mutmut] pytest_add_cli_args`. With `keep` 0 pytest makes no lock, and each run's cleanup removes every numbered folder it finds, those of the other mutmut workers still running included.
   - Rejected: `--basetemp` for mutmut's runs. Each run removes the given folder at its start, so parallel workers would remove each other's.
   - Rejected: a sweep of `/tmp/pytest-of-<user>` at the start of each session (a `conftest.py` hook). It works on files outside `tmp_path`, and it cannot tell a stopped run's locked folder from a running session's.
   - Rejected: `PYTEST_DEBUG_TEMPROOT` in place of `TMPDIR`. It is pytest's debug variable, not a documented setting; `TMPDIR` is what `tempfile.gettempdir()` reads, for pytest and for the tests that ask it.
8. **`pyproject.toml` stays as it is.** `tmp_path_retention_policy = "failed"` (since 2026-10-16, the disk) is right: a passed test's folder goes at once, and with the fixture a failed one is removable later. (Feature)
9. **The leftovers now.** The 58 folders in v1's container (2.4 GB) are removable as `factory`; pytest removes them itself at the first session after their locks turn three days old (from about 2026-10-21 09:46 UTC). Removing them sooner is a deletion, for the human's OK. A `garbage-*` folder made before S0001 stays until it is removed by hand. (Feature)
10. **One story.** The helper, the fixture and four tests are one tester's work under `tests/`, well inside $4 and a 60-minute lease; the coder has nothing to build, as in F0014-S0011, and the new tests pass from the tests stage on. The `Makefile` change cannot be a story: no stage writes the `Makefile`. (Feature)
