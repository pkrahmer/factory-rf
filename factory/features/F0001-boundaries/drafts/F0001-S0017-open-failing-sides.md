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

The tests use the existing fixtures. The unmerged state is made with plain `git merge` through `run_git`, because `GitCli.merge` aborts a conflict.

## Acceptance criteria

1. `MakeProjectCommands.run("check\n", time_limit=…)` raises `ProjectCommandError`, and a Makefile recipe that would write a marker file has not run.
2. `move("../x.txt", "b.txt")` and `move(<absolute path outside the checkout>, "b.txt")` raise `ValueError`; the checkout's status is unchanged and nothing appears outside it.
3. After a conflicting `git merge` left in progress (run with plain git), `status()` lists the conflicting path exactly once, as `"modified"`.
4. With two pull requests on the fake, `delete_comment(first, <id of a comment on the second>)` raises `HostingServiceError`, and the comments of both pull requests are unchanged.
5. make check stays green.
6. docs: none. Every behaviour is already in `docs/project-guide.md`, except the cross-pull-request case of `delete_comment`. The documenter adds "an id of another pull request's comment counts as unknown" to the fake's table.

## Demo

```bash
uv run pytest -q --no-header -p no:cacheprovider tests/adapters/test_make_commands.py tests/adapters/test_git_cli_restoring.py tests/adapters/test_git_cli_history.py tests/adapters/test_fake_hosting.py
```
Expect: the summary line reports only passed tests, and no failure or error.

## Log (append only)

1. 2026-10-13 feature acceptance: proposed; the human refines and promotes.
