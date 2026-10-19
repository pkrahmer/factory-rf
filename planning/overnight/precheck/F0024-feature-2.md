# Pre-check F0024, round 2: the feature after its edits

Round 1's edits A to F are all in `feature.md`: the `Filtered for specific mutants, but nothing matches` line with its paragraph, the KILL that does not reach mutmut, the exit-status wording in the Goal and in the `CLAUDE.md` block, "only kills leave the list", the cost of the full stats run (also in S0003's docs criterion), and the two limits of "the latest run of each module". The human's answers are in decision 18. The stories' own results are in `F0024-S0001-2.md`, `F0024-S0002-2.md` and `F0024-S0003-2.md`.

## Against today's `main`

- Change 1's anchors exist. The `Makefile` comment line `# Mutation testing of the modules under src/factory that one feature's commits changed:` is at line 95 and the `mutants` recipe ends the file at line 116. The `CLAUDE.md` part from `` `make mutants FEATURE=<feature id>` runs mutmut `` to `which read the source it rewrites.` exists once. No test reads the root `Makefile` or that bullet: `tests/test_claude_files.py` pins the template's `CLAUDE.md`.
- Change 2: `factory/pipeline.yml` still has `check` 15, `duplicates` 5 with the same comment, and `doing` with `reports: [duplicates]`. F0023's change 1 rewrites the block first, and change 2's edits fit what it leaves. The leases come to doing 60 of 60, docs 53 of 60 and tests 55.
- Records contract `"1.2"`: no story of F0024 touches it. Protected paths: every story stays in `src/*`, `claude/*`, `tests/*` and `docs/*`. The `Makefile`, `CLAUDE.md` and `factory/pipeline.yml` are the human's changes.
- The guide is split (F0025). Every docs criterion names `docs/project-guide/processes-and-checks.md` and sections that exist in it (147 lines, far from the 600-line split rule). Round 1's point 7, the guide's length, is settled.
- F0023 is not merged yet, so S0002 still waits for F0023-S0002's `command_line`, as decision 16 says. F0020's remaining story (S0009, deferred), F0022 and F0026 touch neither `checks.py`, the command lines, the two `## Role` texts nor the recipe.

## Findings

No contradiction between the decisions and the stories, no number referred to that has since changed, and no Interface sentence that disagrees with its criteria. What is left is in the stories' files:

- S0001: three clauses without a criterion. Intake would ask about them (edits 1 and 2 there). Two optional rows, and one optional docs addition: the stray `.git` paragraphs and the index line.
- S0003: the docs criterion gives a report time above the report's own limit, and the repair command in one instance's form (edits 1 and 2 there).

## Verdict

The feature is ready to build once F0023 is merged and with S0001's edits 1 and 2. S0003's docs edits 1 and 2 are wanted before its docs stage. S0002 needs no edit. No change to `feature.md` itself.
