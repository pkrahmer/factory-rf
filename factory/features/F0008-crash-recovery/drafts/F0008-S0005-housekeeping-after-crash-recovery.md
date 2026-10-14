# Housekeeping after crash recovery

<!-- proposed by feature acceptance of 2026-10-14; refine before promoting -->

## Assignment (as of log entry 1)

Repair what the feature acceptance of F0008 found that the four stories left behind. There are two parts.

**The documentation.**

- `docs/project-guide.md` still says that `build_handlers` registers every kind except `expired`, which contradicts the code and the guide's own `NOT_YET_HANDLED` paragraph.
- `README.md` and the operator guide's opening paragraph list what is built without crash recovery.
- The stale-branch rule for an id in both `backlog/` and `done/` is stated only in a code comment.
- The kill-points section still promises F0008's recovery tests as future work.

**The untested sides of `delete_stale_branches` and of its step in `Tick.run`.** No test pins any of these three, which the hand mutation pass showed:

- An id whose story file is in both `backlog/` and `done/` is logged as done.
- A tick that ends at the stop `checkout_restore_failed` deletes nothing; only the stop `pipeline_definition_invalid` is tested today.
- An `"unreachable"` deletion is logged and tried again, as a `"rejected"` one is.

The code already behaves as the criteria say. The tester writes the tests, and the coder expects to change nothing in `src/`. If a test fails, the code is wrong and the coder fixes it within the Interface below.

## Interface

No new or changed names. The behaviour pinned is that of `delete_stale_branches(boundaries) -> list[str]` in `src/factory/application/recovery.py` and step 4 of `Tick.run` in `src/factory/application/tick.py`, as F0008-S0004 built them:

- An id is stale when its story file is in `backlog/` or `done/` on `origin/main` and no story file of the id is in `in-progress/`. When the id has files in both `backlog/` and `done/`, the log line of its deleted branch ends with `its story is done`.
- A deletion outcome other than `"pushed"`, `"rejected"` and `"unreachable"` alike, writes `could not delete stale branch <name>: <outcome>`. The name is not in the result, and the next call tries again.
- `Tick.run` calls `delete_stale_branches` only after the fetch, the load and the restore have succeeded. A repository stop of any of them, `checkout_restore_failed` included, ends the tick before the cleanup.

Tests: `tests/application/test_stale_branches.py` and `tests/application/test_tick_stale_branch.py`, both grown, with their existing fixtures.

- The restore stop is made as `tests/application/test_tick.py::test_a_failed_restore_is_a_repository_stop_cleared_by_the_next_tick` makes it: an unwritable directory with a file in the checkout, under the same `skipif` for root.
- The unreachable remote is made as `tests/adapters/test_git_cli_branches.py::test_delete_remote_branch_on_a_removed_remote_is_unreachable` makes it, with `shutil.rmtree(remote)` after the branch is pushed and fetched.

## Acceptance criteria

1. With the story file of id `F0001-S0002` both in `backlog/` and in `done/` on `origin/main`, none in `in-progress/`, and its branch `work-item/F0001-S0002` on the remote, `delete_stale_branches` returns `["work-item/F0001-S0002"]`. Exactly one log line names that branch, and it ends with `deleted stale branch work-item/F0001-S0002: its story is done`.
2. With a stale branch on the remote and the remote directory removed after the fetch, `delete_stale_branches` returns `[]`, and the log has a line ending with `could not delete stale branch <name>: unreachable`.
3. A tick that ends at the stop `checkout_restore_failed` deletes no stale branch. With a story in `backlog/` and its branch pushed, `Tick.run` returns `TickOutcome(stopped="checkout_restore_failed")`, and `origin`'s branch is at the commit it had before the tick. The next tick, after the directory is made writable again, deletes the branch (both sides in one test).
4. The existing test of a tick ending at `pipeline_definition_invalid` still holds: that stop deletes nothing either.
5. make check stays green.
6. docs:
   - `docs/project-guide.md`'s paragraph on the event kinds says that `build_handlers` registers every kind except `acceptance_due` (F0009), with no mention of `expired` as unregistered.
   - "The stale branch" states that an id with files in both `backlog/` and `done/` is logged as done.
   - The kill-points section says that F0008's recovery tests arm `BEFORE_PUSH` and that F0011 covers all four points.
   - `README.md`'s first paragraph and `docs/operator-guide.md`'s opening paragraph each add one sentence: a restart reruns a dead stage, an expired lease of another instance is taken over, the crash cap asks the human, and the tick deletes a stale branch.

## Demo

```bash
grep -n "every kind except" docs/project-guide.md
```
Expect: one line, saying that `build_handlers` registers every kind except `acceptance_due`. The line does not contain `expired`.

```bash
grep -c -i "crash" README.md
```
Expect: a number of at least 1.

```bash
uv run pytest --no-header -p no:cacheprovider tests/application/test_stale_branches.py tests/application/test_tick_stale_branch.py
```
Expect: the last line is `<n> passed in <time>` with n at least 20, three more than the 17 these modules ran before this story (as root the restore test is skipped: `<n> passed, 1 skipped in <time>` with n at least 19).

## Log (append only)

1. 2026-10-14 human: created.
