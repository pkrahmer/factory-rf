# Brief: pre-check F0001-S0022 with v1's own roles

## Goal

Play v1's intake exactly on the draft `F0001-S0022`, then predict whether the tester, coder, reviewer, documenter or demo stage would stop it, and give it one verdict line. The human (the session) wrote this draft from questionnaire 1's Q27 (FEATURE.md decision 24); it has not been checked against v1's roles or the real code.

## Inputs (read these; nothing else unless a step needs a named source file)

- The draft: `C:\Dev\Projects\factory-rf\factory\features\F0001-boundaries\drafts\F0001-S0022-housekeeping-after-boundaries.md`, and the feature's `FEATURE.md` and `ACCEPTANCE.md` beside `drafts\`.
- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\`: `factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo` (each `<name>\SKILL.md`), and the agent files `C:\Dev\Projects\factory\claude\agents\*.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory\TICKET.md`, `docs\project-guide.md`, `docs\decisions.md`.
- The code and tests the story changes: `src\factory\domain\git.py`, `src\factory\adapters\git_cli.py`, `tests\conftest.py`, `tests\git_support.py`, `tests\domain\test_git.py`, `tests\adapters\test_git_cli_arguments.py`, `tests\adapters\test_git_cli_branches.py`, and the archived `done\F0001-S0015-git-option-like-arguments.md` and `done\F0001-S0020-push-refspec-arguments.md` with their logs (the stories this one extends).

## Check in particular

- The lesson of S0016, S0020 and S0021: every behaviour the Assignment, the Interface or a FEATURE.md decision states needs a criterion, on both sides of each rule.
- Item 3: list every place in `src/factory/adapters/git_cli.py` where an argument is checked more than once within one public call today (follow `resolve`, `_resolve_or_raise`, `is_ancestor`, `delete_branch`, `merge`, `reset_to`, `revert_paths`, `push`, `delete_remote_branch`), and say whether criterion 4's four cases cover them all, and whether criterion 4's expected count of exactly one holds once built (for example, does `merge` check `"HEAD"` too, and would that count?).
- Criterion 4's monkeypatch: does wrapping `factory.adapters.git_cli.check_git_argument` count the calls that `GitCli` makes (the name is looked up at call time), and is this "mocking the code under test" under `CLAUDE.md`'s test rules?
- Criteria 1–3: `RemoteBranch`'s field `commit` type, whether `"a" * 40` is valid for it, and whether any code or test sets a `RemoteBranch` field after construction or passes extra fields (which `frozen`/`extra="forbid"` would break).
- Criterion 6 against `check_branch_name`'s code; criterion 7 as a search test (`CLAUDE.md` places a module outside the layers at the `tests/` root).
- The renames: which files or docs name the two old test modules (grep the repository), and whether the coverage, import-linter or any config names them.
- The Demo: run it against today's code in a temporary directory outside the repository (from the repository root it uses `uv run` and `ls`), and say what it prints today and once built; the `Expect:` line must be met exactly. Mind the shell: the escape \x10 inside the double-quoted `python -c` string.
- Nothing needs a write outside the coder's, tester's and documenter's write paths; every criterion is one behaviour testable without a further decision.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0001-S0022-1.md` with the intake outcome exactly as v1's intake would end (`question` with numbered questions, or `accepted` with one line per check of `stage-intake` steps 2 to 4), the predicted later stops by role, each with its reason or "none", and last a `## Verdict` line: `F0001-S0022: pass` or `F0001-S0022: predicted refusal (<category>): <reason>`, followed by the shortest fix for each refusal as exact replacement text for the draft.

## Not

- No git commands. No file other than the output. Do not change the draft.

## Reply

The `## Verdict` line, and for each refusal or recommended edit its exact replacement text.

Model: opus.
