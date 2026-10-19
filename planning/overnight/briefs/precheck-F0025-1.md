# Brief: pre-check F0025 round 1 with v1.1's own roles (one story)

## Goal

For each story of `F0025-the-project-guide-split-by-domain`, play v1.1's intake exactly (the shipped agent `claude/agents/intake.md` with the story form `factory/story-form.md`), then predict whether the tester, coder, reviewer, documenter, smoke tester or acceptance reviewer (`claude/agents/*.md`) would stop it, and give it one verdict line. The stories were written by the session's drafting agent and have not been checked against v1.1's roles. Also judge the feature's "human's changes" and its decisions, above all: the eight domains and the index; the move by script at the docs stage (can the documenter do it within its write paths and time limit, and does the factory's `check` after the docs stage stay green); `PROJECT_GUIDE` and the wording check over every file in the folder; the 600-line limit checked only once; the list of drafted stories (F0020, F0022, F0023, F0024) whose docs criteria must be reworded, complete and right; every place that names `docs/project-guide.md` (`grep -rn` over the repository) covered by the story or the human's changes; when F0025 is best built (before F0020, after F0020, or before F0023), given the guide's length now and what F0020 adds.

For every test a story names or describes, check it against the built code and the tests that pin it (the git interface's operation-count tests, `tests/application/test_interfaces.py`, the pipeline-definition load tests, the stage-finisher tests, the contract tests, `tests/test_model_configuration.py`, the layer contracts, fixture order, `mypy --strict`, ruff with the project's rules, coverage at 90 %); run every smoke-test command against today's code where it can run before the story, and check that every file it names exists or is made by the story. Run the story's move script and its smoke test on a copy of today's guide.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0025-the-project-guide-split-by-domain/feature.md` and the story under `backlog/`.
- The brief the drafter worked from: `planning/overnight/briefs/draft-F0025.md`; the plan's step 8 and "The project guide split by domain" in `planning/overnight/restructure-after-f0011.md`.
- v1.1's roles and forms: `claude/agents/*.md` (above all `documenter.md` and its lesson on splitting), `factory/story-form.md`, `factory/feature-form.md`, `factory/pipeline.yml`, `CLAUDE.md`, `Makefile`.
- The code and tests the story touches: `src/factory/domain/documents.py`, `src/factory/entry/check_documents.py`, `tests/entry/test_check_documents.py` and the other document-check tests, `docs/project-guide.md`.
- F0020, F0022, F0023 and F0024 (drafted): their docs criteria and Scope bullets.

## Check in particular

- The size: the story fits one coder's and one documenter's run within their time limits and a few dollars.
- Every behaviour the Interface or a decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; every earlier test the story changes is named with its leave.
- Each file a stage must write is inside that role's write paths in `factory/pipeline.yml` (the new folder under `docs/` included); what is not is a human's change, with its order.

## Output

One file per story, `F0025-S0001-1.md`, and `F0025-feature-1.md` for the feature, its human's changes and decisions, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1.1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands at all. No network calls. No file other than your outputs. Do not change the stories or `feature.md`. Do not start sub-agents. No paid model call of your own. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in the temporary folder `C:/Users/pasca/AppData/Local/Temp/f25pre` and nowhere else, and remove it when done (if a removal is refused, say so). `factory-check-story` imports the Landlock adapter, which fails on Windows: stub it in that temporary folder, or run smoke tests and checks that need Linux in a throwaway container of v1.1's image (`docker run --rm --entrypoint /bin/sh -v <a copy of the repository in the temporary folder>:/src factory-self-factory -c '...'`, `MSYS_NO_PATHCONV=1` first), never in the running instance `factory-self-factory-1`, which is building; mount no instance volume and no secret, and never read a token or key file.

## Reply

Per story its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; anything wrong with the human's changes or the decisions.
