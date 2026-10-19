# Brief: pre-check F0026 round 1 with v1.1's own roles (one story)

## Goal

For each story of `F0026-the-board-shows-only-real-crashes-and-a-flaky-test-is-fixed`, play v1.1's intake exactly (the shipped agent `claude/agents/intake.md` with the story form `factory/story-form.md`), then predict whether the tester, coder, reviewer, documenter, smoke tester or acceptance reviewer (`claude/agents/*.md`) would stop it, and give it one verdict line. The stories were written by the session's drafting agent and have not been checked against v1.1's roles. Also judge the feature's "human's changes" and its decisions, above all: the cause it names for the false `crash:` event (`factory-watch` as a second process of the same instance; `claim_status` gives `own`, the evaluation turns `own` into `crash`): reproduce it and the fix in a throwaway container; that the tick's own judgement stays unchanged and a crashed instance's claim is still rerun at once after a restart; that a real crash still shows on the board (at the latest at its lease's end); decision 4 (a provider-limit wait past the lease after F0020-S0007); the leave for `tests/test_claim_ownership.py`; the `CLAUDE.md` bullet of change 1; whether the drafter's finding of no cause for the flaky test is sound.

For every test a story names or describes, check it against the built code and the tests that pin it (the git interface's operation-count tests, `tests/application/test_interfaces.py`, the pipeline-definition load tests, the stage-finisher tests, the contract tests, `tests/test_model_configuration.py`, the layer contracts, fixture order, `mypy --strict`, ruff with the project's rules, coverage at 90 %); run every smoke-test command against today's code where it can run before the story, and check that every file it names exists or is made by the story. Run both smoke tests against today's code and against a prototype of the story, in throwaway containers.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0026-the-board-shows-only-real-crashes-and-a-flaky-test-is-fixed/feature.md` and the story under `backlog/`.
- The brief the drafter worked from: `planning/overnight/briefs/draft-F0026.md`.
- v1.1's roles and forms: `claude/agents/*.md`, `factory/story-form.md`, `factory/feature-form.md`, `factory/pipeline.yml`, `CLAUDE.md`.
- The code and tests the story touches: `factory-watch`'s module (from the console script in `pyproject.toml`), `src/factory/domain/lease.py`, `src/factory/domain/evaluation.py`, the claim service and the watcher in `src/factory/application/`, `tests/test_claim_ownership.py` and the watcher's and lease's tests.
- F0020's stories still to build (S0006 to S0008 under `factory/features/F0020-opencode-as-a-second-agent-runtime/backlog/`), above all S0007's waits: say where F0026 touches them.

## Check in particular

- The size: the story fits one coder's and one documenter's run within their time limits and a few dollars.
- Every behaviour the Interface or a decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; every earlier test the story changes is named with its leave.
- Each file a stage must write is inside that role's write paths in `factory/pipeline.yml` ; what is not is a human's change, with its order.

## Output

One file per story, `F0026-S0001-1.md`, and `F0026-feature-1.md` for the feature, its human's changes and decisions, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1.1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands at all. No network calls. No file other than your outputs. Do not change the stories or `feature.md`. Do not start sub-agents. No paid model call of your own. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in the temporary folder `C:/Users/pasca/AppData/Local/Temp/f26pre` and nowhere else, and remove it when done (if a removal is refused, say so). `factory-check-story` imports the Landlock adapter, which fails on Windows: stub it in that temporary folder, or run smoke tests and checks that need Linux in a throwaway container of v1.1's image (`docker run --rm --entrypoint /bin/sh -v <a copy of the repository in the temporary folder>:/src factory-self-factory -c '...'`, `MSYS_NO_PATHCONV=1` first), never in the running instance `factory-self-factory-1`, which is building; mount no instance volume and no secret, and never read a token or key file.

## Reply

Per story its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; anything wrong with the human's changes or the decisions.
