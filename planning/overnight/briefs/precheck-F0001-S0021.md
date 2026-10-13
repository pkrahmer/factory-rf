# Brief: pre-check F0001-S0021 with v1's own roles

## Goal

Play v1's intake exactly on the draft `F0001-S0021`, then predict whether the tester, coder, reviewer, documenter or demo stage would stop it, and give it one verdict line. The third feature acceptance wrote this draft; it has not been checked against v1's roles or the real code. The human chose option A (both parts) on 2026-10-13; the draft says so (FEATURE.md decision 23).

## Inputs (read these; nothing else unless a step needs a named source file)

- The draft: `C:\Dev\Projects\factory-rf\factory\features\F0001-boundaries\drafts\F0001-S0021-remote-branch-operations-name-branches-only.md`, and the feature's `FEATURE.md` and `ACCEPTANCE.md` beside `drafts\`.
- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\`: `factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo` (each `<name>\SKILL.md`), and the agent files `C:\Dev\Projects\factory\claude\agents\*.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory\TICKET.md`, `docs\project-guide.md`, `docs\decisions.md`.
- The code and tests the story changes: `src\factory\domain\git.py`, `src\factory\adapters\git_cli.py`, `tests\conftest.py`, `tests\git_support.py`, `tests\domain\test_git.py`, `tests\adapters\test_git_cli_arguments.py`, `tests\adapters\test_git_cli_branches.py`, and the archived `done\F0001-S0015-git-option-like-arguments.md` and `done\F0001-S0020-push-refspec-arguments.md` with their logs (the stories this one extends).

## Check in particular

- The lesson of S0016 and S0020: every behaviour the Assignment, the Interface or a FEATURE.md decision states needs a criterion, on both sides of each rule.
- Each of criterion 1's refused values against `git check-ref-format --branch` (run it), and each of criterion 3's accepted values likewise; any value where the draft and git disagree.
- Criterion 2's `"x*y"`: S0020's code refuses any `*` already, so is this criterion already met (fine), or does it claim a change?
- Part 2 against today's code: does `push` of `refs/heads/<branch>` with `--set-upstream` still set the upstream to `origin/<branch>` (criterion 8), and does `ALREADY_DELETED_MARKER` still match git's message for `--delete refs/heads/<branch>` of a gone branch (the "already gone is `pushed`" rule)? Does the removal of the stale `origin/<branch>` still happen (criterion 9)? Run these against real git in a temporary directory with `LC_ALL=C`.
- Criterion 6's `GitError`: what does `git push origin refs/heads/v1` print and exit with when only a tag `v1` exists, and does `GitCli.push` turn that into `GitError` or into `"rejected"` / `"unreachable"` today?
- Do existing tests another story wrote need to change (a "Not without asking" item), for example tests that assert the exact argv of a push or delete through a stand-in executable?
- The Demo: run it against today's code in a temporary directory outside the repository, and say what it prints today and what it will print once the story is built; the `Expect:` line must be met exactly.
- Nothing needs a write outside the coder's and tester's write paths; every criterion is one behaviour testable without a further decision; at most 26 criteria.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0001-S0021-1.md` with the intake outcome exactly as v1's intake would end (`question` with numbered questions, or `accepted` with one line per check of `stage-intake` steps 2 to 4), the predicted later stops by role, each with its reason or "none", and last a `## Verdict` line: `F0001-S0021: pass` or `F0001-S0021: predicted refusal (<category>): <reason>`, followed by the shortest fix for each refusal as exact replacement text for the draft.

## Not

- No git commands. No file other than the output. Do not change the draft.

## Reply

The `## Verdict` line, and for each refusal or recommended edit its exact replacement text.

Model: opus.
