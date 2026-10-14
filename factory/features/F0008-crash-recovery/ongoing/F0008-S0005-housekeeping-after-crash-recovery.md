---
stage: tests
pr: 100
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# Housekeeping after crash recovery

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

Repair what the feature acceptance of F0008 found that the four stories left behind. There are two parts.

**The documentation.**

- `docs/project-guide.md` still says that `build_handlers` registers every kind except `expired`, which contradicts the code and the guide's own `NOT_YET_HANDLED` paragraph.
- `README.md` and the operator guide's opening paragraph list what is built without crash recovery.
- The stale-branch rule for an id in both `backlog/` and `done/` is stated only in a code comment.
- The kill-points section still promises F0008's recovery tests as future work.

**The untested sides of `delete_stale_branches` and of its step in `Tick.run`.** No test pins any of these four (the hand mutation pass showed the first two):

- An id whose story file is in both `backlog/` and `done/` is logged as done.
- A tick that ends at the stop `checkout_restore_failed` deletes nothing; only the stop `pipeline_definition_invalid` is tested today.
- An `"unreachable"` deletion is logged and tried again, as a `"rejected"` one is.
- A tick that ends at the stop `fetch_failed` tries no deletion.

The code already behaves as the criteria say. The tester writes the tests, and the coder expects to change nothing in `src/`. If a test fails, the code is wrong and the coder fixes it within the Interface below.

## Interface

No new or changed names. The behaviour pinned is that of `delete_stale_branches(boundaries) -> list[str]` in `src/factory/application/recovery.py` and step 4 of `Tick.run` in `src/factory/application/tick.py`, as F0008-S0004 built them:

- An id is stale when its story file is in `backlog/` or `done/` on `origin/main` and no story file of the id is in `in-progress/`. When the id has files in both `backlog/` and `done/`, the log line of its deleted branch ends with `its story is done`.
- A deletion outcome other than `"pushed"`, `"rejected"` and `"unreachable"` alike, writes `could not delete stale branch <name>: <outcome>`. The name is not in the result, and the next call tries again.
- `Tick.run` calls `delete_stale_branches` only after the fetch, the load and the restore have succeeded. A repository stop of any of them, `checkout_restore_failed` included, ends the tick before the cleanup.

Tests: `tests/application/test_stale_branches.py` and `tests/application/test_tick_stale_branch.py`, both grown with new test functions and the imports they need (`os` for the root `skipif`), with their existing fixtures and helpers. No existing test function, fixture or helper of either module changes.

- A tick test that must get past the load (criteria 3 and 4) first installs the agent files, as the `discarded` fixture does: `install_agents(agent_home, _definition(boundaries).roles)`. Without them the load stops the tick at `pipeline_definition_invalid` before the stop under test, which is how the existing test of criterion 5 reaches its stop.
- The restore stop is made as `tests/application/test_tick.py::test_a_failed_restore_is_a_repository_stop_cleared_by_the_next_tick` makes it: an unwritable directory with a file in the checkout (`boundaries.checkout / "locked"`, `chmod(0o555)`, set back to `0o755` in a `finally`), under the same `skipif` for root.
- The unreachable remote (criteria 2 and 4) is made by moving the remote directory away after the branch is pushed and fetched (`remote.rename(tmp_path / "away.git")`) and moving it back for the call or tick that deletes, as `test_tick.py`'s fetch-stop tests do. Git answers a moved remote as it answers a removed one (`"unreachable"`; see `tests/adapters/test_git_cli_branches.py::test_delete_remote_branch_on_a_removed_remote_is_unreachable`).

## Acceptance criteria

1. With the story file of id `F0001-S0002` both in `backlog/` and in `done/` on `origin/main`, none in `in-progress/`, and its branch `work-item/F0001-S0002` on the remote, `delete_stale_branches` returns `["work-item/F0001-S0002"]`. Exactly one log line names that branch, and it ends with `deleted stale branch work-item/F0001-S0002: its story is done`.
2. With a stale branch on the remote and the remote directory moved away after the fetch, `delete_stale_branches` returns `[]`, and the log has a line ending with `could not delete stale branch <name>: unreachable`. A second call while the directory is away also returns `[]` and writes a second such line. After the directory is moved back, the next call returns `[<name>]` and the branch is gone from the remote (all in one test).
3. A tick that ends at the stop `checkout_restore_failed` deletes no stale branch. With a story in `backlog/` and its branch pushed, `Tick.run` returns `TickOutcome(stopped="checkout_restore_failed")`, and `origin`'s branch is at the commit it had before the tick. The next tick, after the directory is made writable again, deletes the branch (both sides in one test).
4. A tick that ends at the stop `fetch_failed` tries no deletion. With a story in `backlog/`, its branch pushed and fetched, and the remote directory then moved away, `Tick.run` returns `TickOutcome(stopped="fetch_failed")` and the factory log holds no line containing `stale branch`. The next tick, after the directory is moved back, deletes the branch (both sides in one test).
5. The existing test of a tick ending at `pipeline_definition_invalid` still holds: that stop deletes nothing either.
6. make check stays green.
7. docs:
   - `docs/project-guide.md`'s paragraph on the event kinds says that `build_handlers` registers every kind except `acceptance_due` (F0009), with no mention of `expired` as unregistered.
   - "The stale branch" states that an id with files in both `backlog/` and `done/` is logged as done.
   - The kill-points section says that F0008's tests arm `BEFORE_PUSH` (`tests/application/test_recovery_crash.py`, a kill before the crash commit's push) and `AFTER_PUSH` (`tests/application/test_tick_stale_branch.py`, a discard killed after its push), and that F0011 covers all four points.
   - `README.md`'s first paragraph and `docs/operator-guide.md`'s opening paragraph each add one sentence: a restart reruns a dead stage, an expired lease of another instance is taken over, the crash cap asks the human, and the tick deletes a stale branch.

## Demo

```bash
grep -no 'registers every kind except[^;.(]*' docs/project-guide.md
```
Expect: one line, `<n>:registers every kind except` followed by `acceptance_due` as the only kind named (a short clause after it, such as "which belongs to F0009", is fine). The line does not contain `expired`.

```bash
grep -c -i "crash" README.md
```
Expect: a number of at least 1.

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_stale_branches.py tests/application/test_tick_stale_branch.py
```
Expect: the last line is `<n> passed in <time>` with n at least 21, four more than the 17 these modules ran before this story (as root the restore test is skipped: `<n> passed, 1 skipped in <time>` with n at least 20).

## Log (append only)

1. 2026-10-14 human: created.
2. intake: accepted
   - Interface: no new names; it points at `delete_stale_branches(boundaries) -> list[str]` in `src/factory/application/recovery.py` and step 4 of `Tick.run`. It names the two test modules, the fixtures and helpers to reuse, and how to make the restore stop and the unreachable remote. Each behaviour it states has a criterion: both-folders is criterion 1, the "could not delete" line is criterion 2, and the ordering of the cleanup after the stops is criteria 3 to 5.
   - Criteria: criteria 1 to 5 are each one test function with a concrete setup and checkable results, and 3 and 4 name both sides in one test. Each stated rule has its failing side: the cleanup is deleted or skipped depending on the stop. The "rejected" outcome and the `pipeline_definition_invalid` stop are already tested. Criteria 6 and 7 are the closing ones, and the docs criterion lists four checkable items.
   - Demo: the three commands are runnable, and each `Expect:` line is checkable. The grep expects a line without `expired`, and the pytest count is given for root and non-root.
   - Architecture: tests only, plus docs. `src/` is expected to stay unchanged, and the layers are untouched.
   - Scope: this is the housekeeping from F0008's feature acceptance, and decision 20 of `FEATURE.md` covers growing S0004's test modules. Nothing in it is in "Out of scope".
