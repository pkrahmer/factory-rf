---
stage: review
pr: 19
blocked: null
comments_seen: 0
round: 0
attempts: 0
---
# The boundaries' open failing sides: tests for behaviour already built

<!-- proposed by feature acceptance of 2026-10-13; refine before promoting -->

## Assignment (as of log entry 1)

The stories of F0001 named four behaviours that the code already has, and that the documentation partly states, but that no test checks. Each was an "open, not a finding" in a log:

- the make class refuses a command name with a trailing newline (S0007, fixed with `fullmatch` in review, never tested);
- `move` refuses an unsafe *source* (S0013, only the destination is tested);
- `status()` lists an unmerged path as `"modified"` (S0011, documented in the project guide, uncovered line in `git_cli.py`);
- the fake hosting service refuses to delete a comment that belongs to another pull request (S0014).

The project has no mutation testing (`docs/decisions.md`), so these lines would survive a change unnoticed. This story writes their tests. No code change is expected: if a test fails, that is a finding for the coder. Whether unmerged paths should get their own kind is a product question left open by the feature acceptance. This story pins the documented behaviour, and changing it would be a story of its own.

Covers R9, R10 and R11 (the failing sides of their rules).

## Interface

No change. The behaviours, as already built:

- `MakeProjectCommands.run(command, *, time_limit)`: a `command` that does not fully match `^[a-z][a-z0-9-]*$` raises `ProjectCommandError` before anything is started (`src/factory/adapters/make_commands.py`).
- `GitCli.move(source, destination)`: `check_repository_path` runs on both arguments before any folder is created (`src/factory/adapters/git_cli.py`).
- `GitCli.status()`: a path with an unmerged entry (porcelain v2 `u`) is listed once, as `"modified"`.
- `FakeHostingService.delete_comment(number, comment_id)`: a `comment_id` that is not a comment of pull request `number` raises `HostingServiceError`, also when it is a comment of another pull request.

Tests:

- `tests/adapters/test_make_commands.py`
- `tests/adapters/test_git_cli_restoring.py`
- `tests/adapters/test_git_cli_history.py`
- `tests/adapters/test_fake_hosting.py`

The tests use the existing fixtures. The unmerged state is made with a plain `git merge` through `run_process`, with an isolated environment as `test_committed_at_is_the_committer_date_in_utc` builds it, because `run_git` asserts exit 0 (a conflicting merge exits 1) and `GitCli.merge` aborts a conflict. Each criterion gets a new test function; no existing parametrization is extended.

## Acceptance criteria

1. `MakeProjectCommands.run("check\n", time_limit=…)` raises `ProjectCommandError`, and a Makefile recipe that would write a marker file has not run.
2. `move("../x.txt", "b.txt")` and `move(<absolute path outside the checkout>, "b.txt")` raise `ValueError`; the checkout's status is unchanged and nothing appears outside it.
3. After a conflicting `git merge` left in progress (run with plain git), `status()` lists the conflicting path exactly once, as `"modified"`.
4. With two pull requests on the fake, `delete_comment(first, <id of a comment on the second>)` raises `HostingServiceError`, and the comments of both pull requests are unchanged.
5. make check stays green.
6. docs: the table of the fake's test operations in `docs/project-guide.md` says that `delete_comment` counts the id of another pull request's comment as unknown; the other three behaviours are already documented.

## Demo

```bash
uv run pytest --no-header -p no:cacheprovider tests/adapters/test_make_commands.py tests/adapters/test_git_cli_restoring.py tests/adapters/test_git_cli_history.py tests/adapters/test_fake_hosting.py
```
Expect: the last line reads `<n> passed in <t>s`, with no `failed`, `error` or `skipped` count.

## Log (append only)

1. 2026-10-13 feature acceptance: proposed; the human refines and promotes.
2. intake: accepted
   - Interface: no change; it names concrete modules and signatures (`MakeProjectCommands.run`, `GitCli.move`, `GitCli.status`, `FakeHostingService.delete_comment`) and the four test files. It also says how the unmerged state is made (plain `git merge` through `run_process` with an isolated environment).
   - Criteria: each is testable by one function. Every behaviour the Interface states has one: the trailing-newline refusal (1), the unsafe source of `move` (2), the unmerged path listed once as "modified" (3), the comment of another pull request refused (4). Each rule has its failing side, since the story exists to test those sides. Criterion 1 also checks that the marker recipe did not run, and criteria 2 and 4 check that nothing changed.
   - Demo: one runnable pytest command over the four named files. Its Expect line is checkable (the last line reads `<n> passed`, with no failed, error or skipped count).
   - Architecture: tests only, in the adapters layer, using real git and the fake hosting service as CLAUDE.md prescribes. No dependency, no change to `factory/`.
   - Scope: inside F0001. FEATURE.md's decision 21 keeps an unmerged path as "modified", so criterion 3 pins documented behaviour. Nothing is in Out of scope.
3. tester: wrote one new test function for each of criteria 1–4. No existing parametrization was extended.
   - criterion 1: tests/adapters/test_make_commands.py::test_command_name_with_a_trailing_newline_is_refused_before_starting. `run("check\n")` raises `ProjectCommandError`, and the marker file from the `touch` recipe does not exist afterwards.
   - criterion 2: tests/adapters/test_git_cli_restoring.py::test_move_refuses_an_unsafe_source_and_changes_nothing, run for two sources: `../x.txt` and an absolute path `tmp_path/outside/x.txt`. Both files exist outside the checkout, so a refusal cannot come from a missing file. The test checks for `ValueError`, that `git status --porcelain` is unchanged, that the file list under `tmp_path` is unchanged, and that `b.txt` keeps its content.
   - criterion 3: tests/adapters/test_git_cli_history.py::test_status_lists_a_path_left_unmerged_by_a_conflicting_merge_once_as_modified. The conflict is made with a plain `git merge` through `run_process`, using the isolated environment that `test_committed_at_is_the_committer_date_in_utc` builds. The test checks that the merge exits 1 and that `ls-files --unmerged` is not empty, then that `status().changes == [("file.txt", "modified")]`.
   - criterion 4: tests/adapters/test_fake_hosting.py::test_delete_comment_refuses_a_comment_of_another_pull_request. With two pull requests, `delete_comment(first, <id of a comment on the second>)` raises `HostingServiceError`, and `list_comments` of both pull requests is unchanged.
   - criteria 5 and 6 are for the coder's `make check` and for the documenter.
   Files changed: the four test files named above; no new files. Every module imported fine.
   `make test` is green and the four new tests pass on the first run. That is expected, because the story pins behaviour that is already built (the Assignment expects no code change). Nothing failed, so there is no finding for the coder. The coder only needs to confirm that `make check`, including mypy, is green. `make lint` is green.

   `make lint`: lint: green
   `make test`: test: green
4. coder: no code change. The story pins behaviour that is already built, and the tester's four new tests pass against the code as it stands:
      - tests/adapters/test_make_commands.py::test_command_name_with_a_trailing_newline_is_refused_before_starting
      - tests/adapters/test_git_cli_restoring.py::test_move_refuses_an_unsafe_source_and_changes_nothing
      - tests/adapters/test_git_cli_history.py::test_status_lists_a_path_left_unmerged_by_a_conflicting_merge_once_as_modified
      - tests/adapters/test_fake_hosting.py::test_delete_comment_refuses_a_comment_of_another_pull_request
      I ran `make check` and it is green: lint, types (mypy --strict over the new tests), layers, sast, secrets, licenses, and test at 99.49 % coverage. The unmerged branch `u` in `_status_entry` (src/factory/adapters/git_cli.py) is now covered. I made no commits and did no refactor, because this branch has no coder diff to clean up. Criterion 6 (the `delete_comment` row in docs/project-guide.md) is for the documenter.
      Noticed, not touched: the report still lists two uncovered spots in git_cli.py. One is line 122, the final `return None` in `_status_entry` for an entry kind that is neither `?`, `1` nor `u` (with renames off, git writes no `2` entries). The other is the partial branch 67->69 in `_commits_in_log`. claude_runtime.py has uncovered lines 360 and 381-382. Each is outside this story.

   `make check`: check: green
