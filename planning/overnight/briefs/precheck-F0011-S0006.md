# Brief: pre-check F0011-S0006 with v1's own roles

## Goal

Play v1's intake exactly on the draft `F0011-S0006-document-check-and-stop-limits-pinned-in-full`, then predict whether the tester, coder, reviewer, documenter, demo stage or acceptor would stop it, and give it one verdict line. F0011's feature acceptance wrote it from four mutation survivors; it has not been checked against v1's roles or the real code.

## Inputs (read these; nothing else unless a step needs a named source file)

- The draft: `C:\Dev\Projects\factory-rf\factory\features\F0011-proof-and-documents\drafts\F0011-S0006-document-check-and-stop-limits-pinned-in-full.md`, the feature's `FEATURE.md` (decisions 1 to 21) and `ACCEPTANCE.md` beside `drafts\`.
- The human may be away. Any point the draft leaves "for the human" is answered with the draft's recommendation or yours; list each with the answer you recommend.
- v1's role files, verbatim, under `C:\Dev\Projects\factory\claude\skills\` (`factory-rules`, `stage-intake`, `role-tester`, `stage-tests`, `role-coder`, `stage-doing`, `role-reviewer`, `stage-review`, `role-documenter`, `stage-docs`, `stage-demo`, each `<name>\SKILL.md`) and `C:\Dev\Projects\factory\claude\agents\*.md`.
- `C:\Dev\Projects\factory-rf\CLAUDE.md` (its newest Tests rules included), `pyproject.toml`, `Makefile`, `factory\stages.yml`, `factory\TICKET.md`, `planning\lessons-for-the-skills.md`.
- The code and tests the story touches: at least `src\factory\domain\documents.py`, `src\factory\domain\stop_table.py`, `src\factory\domain\kill_point_cases.py`, `src\factory\domain\fault_paths.py`, and their tests under `tests\` (`tests\domain\test_documents.py`, `tests\domain\test_stop_table.py`, `tests\domain\test_kill_point_cases.py`, `tests\domain\test_fault_paths*.py`, `tests\test_fault_path_names.py`), with `tests\conftest.py` and `tests\proof_support.py`.

## Check in particular

- The lessons: every behaviour the Assignment, the Interface or a decision states has its own criterion, on both sides; every limit tested on both sides, the sides of one rule as rows of one parametrized test; test data and helpers valid under the built code; shared helpers reused, no second copy; criteria pass `mypy --strict`, ruff, semgrep and detect-secrets; each Demo's `Expect:` met exactly.
- Which tests written by S0001 to S0005 the story changes or replaces (the row rules "over every case, path and stop rather than one example each"). Name each test and give the leave text for a new FEATURE decision 22 if one is needed, in the form of decisions 20 and 21.
- The `fullmatch` change to `StopRow`'s limit pattern: name every caller and test it could break.
- `REPLACED_PHRASES` pinned exactly: it must not break decision 21's exemption in `tests/entry/test_watch.py`.
- Run the Demo against today's code in a temporary directory outside the repository with `uv run --project C:\Dev\Projects\factory-rf python ...` and say what it prints before the story is built.
- Size: fits the coder's $4 with one resume and a 60-minute lease.

## Output

One file, `C:\Dev\Projects\factory-rf\planning\overnight\precheck\F0011-S0006-1.md`: the intake outcome exactly as v1's intake would end, the predicted later stops by role, the points for the human with recommended answers, a `## Verdict` line, and the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands. No file other than the output. Do not change the draft.

## Reply

The verdict line, the points for the human with their recommended answers, the leave text for decision 22 if needed, and for each refusal or edit its fix in one line.

Model: opus.
