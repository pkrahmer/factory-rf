# Brief: pre-check F0001-S0019 with v1's own roles

## Goal

Play v1's intake exactly on the story `F0001-S0019`, then predict whether the tester, coder, reviewer, documenter or demo stage would stop it, and give it one verdict line.

## Inputs (read these; nothing else unless a step needs a named source file)

- The story: `C:\Dev\Projects\factory-rf\factory\features\F0001-boundaries\drafts\F0001-S0019-interfaces-as-abstract-base-classes.md`, and its feature's `FEATURE.md` beside `drafts\`.
- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\`: `factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo` (each `<name>\SKILL.md`), and the agent files `C:\Dev\Projects\factory\claude\agents\*.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md`, `pyproject.toml`, `Makefile`, `factory\stages.yml`, `factory\TICKET.md`, `docs\project-guide.md`, `docs\decisions.md`.
- The code and tests the story changes, to check that its criteria can be met as written: `src\factory\application\{git,hosting,project_commands,agent_runtime}.py`, `src\factory\adapters\{git_cli,pygithub_hosting,fake_hosting,make_commands,claude_runtime,fake_agent_runtime}.py`, `tests\application\test_git_protocol.py`, `tests\application\test_hosting_protocol.py`, `tests\test_hosting_fake_search.py`, `tests\conftest.py`, and the six "without inheriting" tests (search `tests\adapters` for `__mro__`).
- The form check's result: `factory-check-story` reported no findings for this draft (exit 0) in v1's container.

## Output

One file: `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0001-S0019-1.md` with the intake outcome exactly as v1's intake would end (`question` with numbered questions, or `accepted` with one line per check of `stage-intake` steps 2 to 4), then the predicted later stops by role, each with its reason or "none", and last a `## Verdict` line: `F0001-S0019: pass` or `F0001-S0019: predicted refusal (<category>): <reason>`.

Check in particular, against the real code: mypy `--strict` and ruff (D rules, B024/B027 for abstract classes) accept a docstring-only abstract method; `inspect.getmembers(X, callable)` on an ABC still yields exactly the operations the two protocol tests pin; a dataclass (`FakeHostingService`) can inherit an ABC; the fixtures named in criteria 9, 10 and 12 exist under those names; the Demo commands run in v1's container as written and print exactly their `Expect:` lines once the story is built; nothing needs a write outside the coder's and tester's write paths or a "Not without asking" item.

## Not

- No git commands. No file other than the output. Do not change the story.

## Reply

The `## Verdict` line and, for a refusal, the shortest fix.

Model: opus.
