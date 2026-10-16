---
stage: doing
pr: 127
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The probe on the main branch and a stamp keyed to the image

## Assignment (as of log entry 1)

Give the preflight its memory and its probe. `Preflight` runs the machine's items of the previous story only when the image build changed since the last pass, and it probes the code by running the project's `lint` command on the main branch, never on a work item's branch, only when the main branch has moved since the last pass; a main branch that failed the lint is remembered, so that an idle tick runs no project command even while the human has not yet pushed a fix. A machine that fails is a machine stop, a main branch that fails the lint is a repository stop, and `Preflight.run` returns the reason of the stop it raised, or `None` when it passed. No timer expires the stamp. This covers ST4.1, ST4.3 and ST4.5, and keeps kept thing 16 (an idle tick does not run the project's commands) and kept thing 18. The probe uses a constant `time_limit` of 10 minutes, the default of every project command, so that `Preflight` needs no pipeline definition and its memory does not depend on one; the stop for a main branch that fails is reported through the stop service of F0003, whose health status the container's health check reads. The next story puts the preflight into the tick, in the right place, and into `build_tick`.

## Interface

`src/factory/domain/preflight.py` (extends the module)

```python
class PreflightStamp(BaseModel):              # frozen, extra="forbid"
    image: str | None                         # the image identity the machine items passed on
    main_probed: CommitId | None = None       # the commit of origin/main whose lint passed
    main_failed: CommitId | None = None       # the commit of origin/main whose lint failed
```

`src/factory/application/preflight.py` (extends the module)

```python
PROBE_COMMAND = "lint"
PROBE_TIME_LIMIT = timedelta(minutes=10)

class PreflightStampStore(ABC):
    @abstractmethod
    def read(self) -> PreflightStamp | None: ...          # missing or unreadable: None (a cache)
    @abstractmethod
    def write(self, stamp: PreflightStamp) -> None: ...

class Preflight:
    def __init__(
        self,
        boundaries: Boundaries,
        checks: MachineChecks,
        stamps: PreflightStampStore,
        stops: StopService,
        image: str | None,
    ) -> None: ...
    def run(self) -> RepositoryStopReason | None: ...     # None: passed; else the reason of the stop it raised
```

`src/factory/adapters/preflight_stamp_file.py`

```python
class JsonPreflightStampFile(PreflightStampStore):
    def __init__(self, path: Path) -> None: ...
```

Rules for `Preflight.run`:

- Machine items. When `image` is not `None` and the stored stamp's `image` equals it, the machine items are skipped. Otherwise `checks.run()` runs. A failed report is raised as `machine_stop(report, at=boundaries.clock.now())` through `stops.raise_stop`, the stamp is not written, and `run` returns `"preflight_failed"` without probing. A passed report writes `PreflightStamp(image=image, main_probed=None, main_failed=None)`: a new build forgets what was probed.
- Probe. `main = git.resolve("origin/main")`; when it is `None` there is nothing to probe and `run` ends as passed. When the stamp's `main_failed` equals `main` the probe is not repeated: the stop `main_branch_failing` is kept as it is (raised again with the detail `lint is red on main at <first 12 characters of main> (probed earlier)` only when the health status holds none) and `run` returns `"main_branch_failing"`. When the stamp's `main_probed` equals `main` the probe is skipped, the stop `main_branch_failing` is cleared and `run` ends as passed. Otherwise the probe runs `git.checkout("main", start_point="origin/main")`, `git.reset_to("origin/main")` and `project_commands.run("lint", time_limit=PROBE_TIME_LIMIT)`.
- A probe whose result is `passed` clears `main_branch_failing`, writes the stamp with `main_probed=main` and `main_failed=None`, and ends as passed.
- A probe whose result is not `passed` (red, or the `time_limit` reached) raises `RepositoryStop(scope="repository", reason="main_branch_failing", detail="lint is red on main at <first 12 characters of main>: <the result's last_line>")` (for the `time_limit` case the detail says `lint reached its time_limit on main at <first 12 characters of main>`), writes the stamp with `main_failed=main` and `main_probed=None`, and returns `"main_branch_failing"`.
- A `ProjectCommandError` or a `GitError` while probing raises `RepositoryStop(scope="machine", reason="preflight_failed", detail="the probe on main could not run: <message>")` and returns `"preflight_failed"`; the stamp is not changed.
- Ending as passed, or with `"main_branch_failing"`, means the machine's items have passed or been skipped: `run` then clears the stop `preflight_failed` (a settings fault that the operator has fixed leaves no stop behind, and a valid stamp does not keep one alive).
- No timer is involved: `Preflight` compares no times (the clock is read only for the `at` of a stop) and the stamp holds no time.
- `PreflightStamp`'s commit fields are `CommitId`s (40 lowercase hexadecimal digits). `JsonPreflightStampFile.read` returns `None` for a missing file, for a file that is not a valid stamp, and so for one whose commit breaks the pattern; `write` replaces the file with one JSON object holding the three fields, atomically, through the same module function as `JsonHealthStatusFile.write`, extracted from it (`CLAUDE.md`: a second copy of an existing helper is a finding).

Tests: `tests/domain/test_preflight_stamp.py`, `tests/application/test_preflight_run.py` (`Preflight` on the `remote`, `checkout`, `human`, `hosting` and `agent_runtime` fixtures with a real `MakeProjectCommands` and the real `StopService`; the remote's `main` gets a `Makefile` whose target `lint` is `test ! -f BROKEN`, and a file named `BROKEN` makes it red; the pipeline's agents are installed with `install_agents`), `tests/adapters/test_preflight_stamp_file.py`, `tests/test_atomic_replace_search.py` (the search, with `ast`). The machine items are counted through a `which` stub that records its calls. A `ProjectCommands` double that inherits the interface raises `ProjectCommandError` or answers `time_limit`, and records the command and the `time_limit` it was given.

## Acceptance criteria

1. With the checkout on a work item's branch whose `lint` fails (a file `BROKEN` on that branch only) and an `origin/main` whose `lint` passes, `Preflight.run()` returns `None`, and afterwards the checkout is on `main` at `origin/main` (ST4.1: a lint failure on the work item's branch does not fail the preflight).
2. With an `origin/main` whose `lint` fails, `run()` returns `"main_branch_failing"` and the health status holds exactly one stop: scope `repository`, reason `main_branch_failing` and the detail `lint is red on main at <first 12 characters of origin/main>: <last line>`, where `<last line>` is the `last_line` of `MakeProjectCommands(<the checkout>).run("lint", time_limit=PROBE_TIME_LIMIT)` on that commit (ST4.1 and ST4.5: a main branch that fails the lint is a reported stop).
3. After the human fixes `main` and pushes, the next `run()` returns `None` and the stop `main_branch_failing` is gone from the health status.
4. When a machine item fails (`which` answers `None` for `make`), `run()` returns `"preflight_failed"`, the health status holds one stop with scope `machine` and reason `preflight_failed` whose detail contains `tool:make`, and `lint` was not run.
5. A `ProjectCommandError("lint", "make not found")` raised by the probe leaves one stop with scope `machine`, reason `preflight_failed` and the detail `the probe on main could not run: project command lint failed: make not found` (the error's message), and `run()` returns `"preflight_failed"`; the stored stamp is the one stored before.
6. A probe whose `lint` reaches its `time_limit` leaves the stop `main_branch_failing` with the detail `lint reached its time_limit on main at <first 12 characters of origin/main>` and `run()` returns `"main_branch_failing"`.
7. While the image is unchanged the machine items run once, however much time passes: two `run()` calls with the same non-`None` image, the test's clock advanced by 90 days in between, call `which` for each tool once, not twice (ST4.3: no timer expires the stamp).
8. A different image identity runs the machine items again and the stamp then holds the new identity.
9. A different image identity also probes the main branch again, although `origin/main` did not move.
10. With `image=None` the machine items run on every `run()`.
11. A failed machine report writes no stamp, so the next `run()` runs the machine items again; when they pass, the stop `preflight_failed` is gone.
12. The probe does not repeat for an `origin/main` that already passed: two `run()` calls run `lint` once, and after the human pushes a new commit to `main` the third call runs it again (all calls with the same non-`None` image).
13. A red `origin/main` is probed once: two `run()` calls run `lint` once, both return `"main_branch_failing"`, and the stop in the health status is the first call's, with the same detail (both calls with the same non-`None` image).
14. When the health status no longer holds the stop of a red `origin/main` that was probed earlier (the file was deleted), the next `run()` raises it again with the detail `lint is red on main at <first 12 characters of origin/main> (probed earlier)`, and `lint` is not run again (both calls with the same non-`None` image).
15. A standing `preflight_failed` stop (for example the settings fault of the run story) is cleared by a `run()` that skips the machine items because the stamp is valid and ends as passed (both calls with the same non-`None` image).
16. With no `origin/main` (a checkout of a remote without any commit), `run()` runs no `lint` and returns `None` once the machine items pass.
17. With the checkout's directory deleted after its clone, the probe's `git.resolve` raises `GitError`: `run()` leaves one stop with scope `machine`, reason `preflight_failed` and a detail that starts `the probe on main could not run`, returns `"preflight_failed"`, and the stored stamp is the one stored before.
18. A standing `preflight_failed` stop is cleared also by a `run()` that returns `"main_branch_failing"`.
19. The probe runs `lint` with the `time_limit` of 10 minutes: a `ProjectCommands` double that inherits the interface records the command `lint` and the limit `PROBE_TIME_LIMIT`.
20. When the stamp's `main_probed` equals `origin/main` and the health status holds a `main_branch_failing` stop (written by the test), `run()` runs no `lint`, returns `None` and the stop is gone.
21. `PreflightStamp` refuses an unknown key and an assignment to a field; `main_probed` and `main_failed` accept `"a" * 40` and `None` and refuse `"a" * 39`, `"A" * 40` and `"g" * 40`, all with `ValidationError`.
22. `JsonPreflightStampFile` reads back a stamp it wrote: `PreflightStamp(image="build-7", main_probed=<40 hexadecimal digits>, main_failed=None)`, and `read` returns `None` for a missing file, for a file that holds text which is not a stamp and for a file whose `main_probed` breaks the pattern; the file `write` leaves holds one JSON object whose keys are exactly `image`, `main_probed` and `main_failed`, a `None` written as `null`.
23. `JsonPreflightStampFile.write` and `JsonHealthStatusFile.write` replace their files through one module function: a search with `ast` over `src/factory` finds exactly one call of `os.replace`, and after a `write` the directory of the stamp file holds no file but `preflight-stamp.json`.
24. make check stays green.
25. docs: `docs/operator-guide.md` explains that the machine items are skipped while the image build is unchanged and the probe repeats only when `main` moves, that a red `main` is probed once and its stop stands until a fix is pushed, the file `preflight-stamp.json` in the state directory and that deleting it only costs one more run, and for the stops `main_branch_failing` and `preflight_failed` what the operator does; `docs/decisions.md` records why the stamp is keyed to the image build and not to a timer, why the probe runs `lint` on the main branch only, why its `time_limit` is a constant (the preflight needs no pipeline definition) and why a red `main` is remembered.

## Demo

```bash
uv run python -c "
import tempfile, pathlib
from factory.adapters.preflight_stamp_file import JsonPreflightStampFile
from factory.domain.preflight import PreflightStamp
d = pathlib.Path(tempfile.mkdtemp())
store = JsonPreflightStampFile(d / 'preflight-stamp.json')
print(store.read())
store.write(PreflightStamp(image='build-7', main_probed='a' * 40))
stamp = store.read()
print(stamp.image, stamp.main_probed[:7], stamp.main_failed)
(d / 'preflight-stamp.json').write_text('not a stamp')
print(store.read())
"
```
Expect: three lines, `None`, `build-7 aaaaaaa None` and `None`.

```bash
uv run python -c "
from factory.application.preflight import PROBE_COMMAND, PROBE_TIME_LIMIT
print(PROBE_COMMAND, PROBE_TIME_LIMIT.total_seconds())
"
```
Expect: one line, `lint 600.0`.

## Log (append only)

1. 2026-10-12 human: created.
2. intake: accepted
   - Interface: names concrete modules and signatures (`factory.domain.preflight.PreflightStamp`, `factory.application.preflight` with `PROBE_COMMAND`, `PROBE_TIME_LIMIT`, `PreflightStampStore` and `Preflight.__init__/run`, and `factory.adapters.preflight_stamp_file.JsonPreflightStampFile`). The rules for `run` give the order, the details and the return values.
   - Criteria: each can be tested by one test function. Every behaviour in the Interface has a criterion. The probe's checkout and reset are covered by 1, the commit-id pattern by 21 and 22, and the atomic write and the single `os.replace` by 23. Each rule has both sides. A passing branch is criterion 1 and 3, a red main is 2, 13 and 14, and a failing machine item is 4 and 11. A probe error is 5 and 17, a time_limit is 6, and no `origin/main` is 16. `image=None` is 10, and a changed image is 8 and 9. An unchanged image or commit is 7, 12 and 20, and the clearing of `preflight_failed` is 15 and 18. A stamp that does not validate is 21 and 22. The `PROBE_TIME_LIMIT` limit is 19.
   - Demo: both blocks are runnable. Each `Expect:` line is checkable: `None`, `build-7 aaaaaaa None`, `None`, and `lint 600.0`.
   - Architecture: the store interface is an ABC in application, the file implementation is in adapters, the stamp DTO is in domain, and the layer order holds. `Preflight` reaches git and the project commands only through `Boundaries`, and the stop service is the existing F0003 one. The Interface reuses the existing atomic-write helper instead of copying it.
   - Scope: the story is within F0010's scope ("The probe and the stamp", ST4.1, ST4.3, ST4.5) and matches decisions 13 and 14 of the feature. It touches nothing in the Out of scope list.
3. tester: I wrote red tests for criteria 1–23 from the Interface and the criteria. `make lint` is green. `make test` stops at collection on purpose because the modules under test do not exist yet.

   Criterion → test:
   - criterion 1: tests/application/test_preflight_run.py::test_a_red_lint_on_a_work_items_branch_does_not_fail_and_the_probe_ends_on_main
   - criterion 2: tests/application/test_preflight_run.py::test_a_red_main_is_one_repository_stop_naming_the_commit_and_the_last_line
   - criterion 3: tests/application/test_preflight_run.py::test_a_fix_pushed_to_main_clears_the_stop_of_the_red_main
   - criterion 4: tests/application/test_preflight_run.py::test_a_failed_machine_item_is_a_machine_stop_and_no_lint_runs
   - criterion 5: tests/application/test_preflight_run.py::test_a_probe_that_cannot_start_is_a_machine_stop_and_leaves_the_stamp
   - criterion 6: tests/application/test_preflight_run.py::test_a_probe_that_reaches_its_time_limit_is_the_stop_of_a_failing_main
   - criterion 7: tests/application/test_preflight_run.py::test_an_unchanged_image_runs_the_machine_items_once_however_much_time_passes
   - criterion 8: tests/application/test_preflight_run.py::test_a_new_image_runs_the_machine_items_again_and_is_stamped
   - criterion 9: tests/application/test_preflight_run.py::test_a_new_image_probes_the_unmoved_main_again
   - criterion 10: tests/application/test_preflight_run.py::test_without_an_image_identity_the_machine_items_run_every_time
   - criterion 11: tests/application/test_preflight_run.py::test_a_failed_machine_report_writes_no_stamp_and_its_stop_goes_once_they_pass
   - criterion 12: tests/application/test_preflight_run.py::test_a_main_that_passed_is_probed_again_only_when_it_moves
   - criterion 13: tests/application/test_preflight_run.py::test_a_red_main_is_probed_once_and_its_stop_stays_the_first_ones
   - criterion 14: tests/application/test_preflight_run.py::test_a_lost_stop_of_a_red_main_is_raised_again_without_probing
   - criterion 15: tests/application/test_preflight_run.py::test_a_valid_stamp_clears_a_standing_preflight_stop
   - criterion 16: tests/application/test_preflight_run.py::test_without_an_origin_main_no_lint_runs_and_the_preflight_passes
   - criterion 17: tests/application/test_preflight_run.py::test_a_git_error_while_probing_is_a_machine_stop_and_leaves_the_stamp
   - criterion 18: tests/application/test_preflight_run.py::test_a_red_main_also_clears_a_standing_preflight_stop
   - criterion 19: tests/application/test_preflight_run.py::test_the_probe_runs_lint_with_a_time_limit_of_ten_minutes
   - criterion 20: tests/application/test_preflight_run.py::test_a_main_probed_before_is_not_probed_again_and_its_stale_stop_goes
   - criterion 21: tests/domain/test_preflight_stamp.py::test_the_stamp_refuses_an_unknown_key, ::test_the_stamp_refuses_an_assignment_to_a_field, ::test_the_commit_fields_hold_a_commit_id_or_none (parametrized: both fields × "a"*40, None, "a"*39, "A"*40, "g"*40)
   - criterion 22: tests/adapters/test_preflight_stamp_file.py::test_a_written_stamp_reads_back_as_one_json_object_of_three_keys, ::test_a_missing_or_invalid_file_reads_as_no_stamp (parametrized: missing, not a stamp, commit breaks the pattern)
   - criterion 23: tests/test_atomic_replace_search.py::test_exactly_one_call_of_os_replace_exists_in_the_package and tests/adapters/test_preflight_stamp_file.py::test_a_write_leaves_no_file_but_the_stamp_in_its_directory

   Files created: tests/application/test_preflight_run.py, tests/domain/test_preflight_stamp.py, tests/adapters/test_preflight_stamp_file.py, tests/test_atomic_replace_search.py.

   Modules and names the test runner could not import: factory.adapters.preflight_stamp_file (JsonPreflightStampFile), and the new names `PreflightStamp` in factory.domain.preflight and `Preflight`, `PROBE_COMMAND`, `PROBE_TIME_LIMIT` in factory.application.preflight. Collection errors in the three files above.

   Notes for the coder:
   - The search test in tests/test_atomic_replace_search.py already passes, because today there is only the one `os.replace` in health_file.py. It guards against a second copy; it is not red now.
   - How the run tests are built: a `Rig` fixture on the `remote`, `checkout`, `human`, `hosting`, `agent_runtime` and `clock` fixtures, with agents installed through `install_agents`. The settings pin "fake", the fake runtime's default version.
   - The remote's `main` gets the Makefile `lint:\n\ttest ! -f BROKEN\n`, and the test fetches the checkout after every push to `main`. So `Preflight` itself is expected not to fetch.
   - `lint` runs are counted by `RecordingCommands`, which inherits `ProjectCommands` and delegates to a real `MakeProjectCommands` on the checkout. For criteria 5, 6 and 19 it raises the error or answers a `time_limit` or passed result instead.
   - Criteria 5 and 17 store `PreflightStamp(image=IMAGE, main_probed="a"*40)` first and run with the same image. That way the machine items are skipped and "the stored stamp is the one stored before" can be checked.
   - Criterion 16 uses an empty bare remote cloned into `tmp_path/empty-checkout`. `git.resolve("origin/main")` must return `None` there, not raise.
   - Criterion 3: the human's fix removes `BROKEN` with `git rm` in the human clone, then commits and pushes.

   Nothing is open.

   `make lint`: lint: green
   `make test`: !!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
