# Brief: pre-check F0001-S0020 with v1's own roles

## Goal

Play v1's intake exactly on the draft `F0001-S0020`, then predict whether the tester, coder, reviewer, documenter or demo stage would stop it, and give it one verdict line. The second feature acceptance wrote this draft; it has not been checked against v1's roles or the real code. The human chose option (a), refusal with `ValueError`, on 2026-10-13; the draft will say so (FEATURE.md decision 22) before it starts, so do not count its "Open for the human" paragraph as a question.

## Inputs (read these; nothing else unless a step needs a named source file)

- The draft: `C:\Dev\Projects\factory-rf\factory\features\F0001-boundaries\drafts\F0001-S0020-push-refspec-arguments.md`, and the feature's `FEATURE.md` and `ACCEPTANCE.md` beside `drafts\`.
- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\`: `factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo` (each `<name>\SKILL.md`), and the agent files `C:\Dev\Projects\factory\claude\agents\*.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory\TICKET.md`, `docs\project-guide.md`, `docs\decisions.md`.
- The code and tests the story changes: `src\factory\domain\git.py`, `src\factory\adapters\git_cli.py`, `tests\conftest.py`, `tests\git_support.py`, `tests\domain\test_git.py`, `tests\adapters\test_git_cli_arguments.py`, and the archived `done\F0001-S0015-git-option-like-arguments.md` with its log (the story this one extends).

## Check in particular

- The lesson of S0016: every behaviour the Assignment, the Interface or a FEATURE.md decision states needs a criterion, on both sides of each rule. Check `delete_remote_branch("+main")`'s current `"pushed"` and the "no other operation changes" line.
- Criterion 7: can a local branch named `a+b` be created through `GitCli.checkout("a+b", start_point=…)` and pushed, and does `remote_branches()` or plain git show it as `a+b`?
- Criterion 1 and 2 against the existing tests of `check_git_argument`: does adding `check_branch_name` force a change to a test another story wrote (a "Not without asking" item)?
- The Demo: run it against today's code in a temporary directory outside the repository (the identity default, `remote_branches()`'s field `name`, the `log` result's `subject`), and say what it prints today and what it will print once the story is built; the `Expect:` line must be met exactly.
- Nothing needs a write outside the coder's and tester's write paths or a "Not without asking" item; every criterion is one behaviour testable without a further decision.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0001-S0020-1.md` with the intake outcome exactly as v1's intake would end (`question` with numbered questions, or `accepted` with one line per check of `stage-intake` steps 2 to 4), the predicted later stops by role, each with its reason or "none", and last a `## Verdict` line: `F0001-S0020: pass` or `F0001-S0020: predicted refusal (<category>): <reason>`, followed by the shortest fix for each refusal as exact replacement text for the draft.

## Not

- No git commands. No file other than the output. Do not change the draft.

## Reply

The `## Verdict` line, and for each refusal or recommended edit its exact replacement text.

Model: opus.
