# Brief: pre-check the todo demo draft against v1.1's own pipeline

## Goal

The staging folder `C:\Dev\Projects\factory-rf\planning\overnight\demo\` holds a draft of `demo/` with the todo demo (plan step 3), written by a drafting agent from `planning\overnight\briefs\draft-demo-todo-service.md`. v1.1, not v1, will build it in the shakedown run (step 4) and the baseline run (step 10). Predict, story by story, whether v1.1's pipeline builds it first-pass, and whether the demo passes F0012-S0023's demo check once it is committed into `demo/`.

## Inputs

- The draft: everything under `planning\overnight\demo\`, its `todo-service\NOTES.md` first (the drafter's choices "taken for the human, to confirm" and the commands it ran).
- The brief it was written from, and the plan sections it names.
- v1.1's pipeline as it will be after F0012: `template\factory\pipeline.yml` and the demo's own `project\factory\pipeline.yml` (stages, roles, write paths, budgets, time limits, checks, reports), the shipped agents `claude\agents\*.md` (their rules and `## Lessons`, plus what F0012-S0011 and S0028 add), `claude\settings.json`, `template\CLAUDE.md`, and the code that reads work items and runs stages (`src\factory\`; the project guide's sections on work items, the form check of a story, the stages and the feature acceptance).
- F0012's drafts that change what v1.1 does before the demo runs: `factory\features\F0012-housekeeping\drafts\` (S0023 the demo check, S0029 the template `Makefile`, S0030 the commit subjects, S0012/S0013 target times and command records, S0016 the disk record, S0024 the kill under `sudo`) and FEATURE.md's decisions.
- v1's original for comparison: `C:\Dev\Projects\factory\demo\` and what run 4 recorded there.

## Check in particular

- Each story as v1.1's intake, tester, coder, reviewer, documenter, demo stage and acceptance reviewer would read it: every behaviour its own criterion, both sides of each rule as rows of one parametrized test, test data valid under the code the earlier stories build, every Demo `Expect:` met exactly by the built code, no doubled `-q`, within the budgets and the lease of the demo's `pipeline.yml`.
- Each file a stage must write lies inside that stage's write paths in the demo's `pipeline.yml`.
- `make check` green on the empty project, and every target the pipeline calls exists with the output the pipeline reads (the last line of a report such as `duplicates`; `make mutants` finding a feature's modules from v1.1's commit subjects after S0030 and the acceptance branch form `work-item/<id>-A<nnnn>`).
- The demo check of S0023, clause by clause, against the tree: name each finding it would print.
- Each of the drafter's sixteen choices: agree, or give the better answer with the reason. Divergences from F0012-S0029's template `Makefile` (for example `make test` accepting "no tests collected") are either fixed in the demo or carried back into S0029 as an edit; say which.
- Run what can run, in temporary directories that remove themselves (copy `project\` out first): `make check` there, the pipeline reader, today's story check. Report the last lines.

## Output

`C:\Dev\Projects\factory-rf\planning\overnight\precheck\demo-todo-service-1.md`: per story the predicted outcome by role; the demo check's findings; the human's points with recommended answers; a `## Verdict` line, then the exact replacement text for each required and each recommended edit (file, old text, new text).

## Not

- No git commands. No file other than the output. Do not change the draft.

## Reply

Per story its verdict line; each required edit in one line; the points for the human with recommended answers.

Model: opus.
