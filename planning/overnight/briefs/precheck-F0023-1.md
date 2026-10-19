# Brief: pre-check F0023 round 1 with v1.1's own roles (two stories)

## Goal

For each story of `F0023-a-known-result-is-not-checked-again`, play v1.1's intake exactly (the shipped agent `claude/agents/intake.md` with the story form `factory/story-form.md`), then predict whether the tester, coder, reviewer, documenter, smoke tester or acceptance reviewer (`claude/agents/*.md`) would stop it, and give it one verdict line. The stories were written by the session's drafting agent and have not been checked against v1.1's roles. Also judge the feature's "human's changes" and its decisions, above all: the key of a known result (command, the tree of the files it reads computed in a temporary index, the pipeline definition's digest, the image id) and what invalidates it; `not_read` declared by the project and empty by default; a failed result never reused and the last run of a key deciding; the separate store `known-results.jsonl` in the state directory; `secrets` as its own docs-stage command in factory-rf; whether a reused check can ever silence a check that should have failed (a file the command reads but `not_read` leaves out, a tool outside the tree such as `uv.lock` resolution or the image's own files).

For every test a story names or describes, check it against the built code and the tests that pin it (the git interface's operation-count tests, `tests/application/test_interfaces.py`, the pipeline-definition load tests, the stage-finisher tests, the contract tests, `tests/test_model_configuration.py`, the layer contracts, fixture order, `mypy --strict`, ruff with the project's rules, coverage at 90 %); run every smoke-test command against today's code where it can run before the story, and check that every file it names exists or is made by the story. Measure `work_tree_id`'s cost on factory-rf's own checkout (a temporary index over the whole tree) in a copy.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0023-a-known-result-is-not-checked-again/feature.md` and the two stories under `backlog/`.
- The brief the drafter worked from: `planning/overnight/briefs/draft-F0023.md`; the plan's step 7 and "The time `make check` takes" in `planning/overnight/restructure-after-f0011.md`.
- v1.1's roles and forms: `claude/agents/*.md`, `factory/story-form.md`, `factory/feature-form.md`, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml`, `Makefile`.
- The code and tests each story touches: the git interface and `GitCli`, the pipeline definition's models and reader, the stage finisher and the project-commands interface, the command records, `boundaries.py`, `wiring.py`, `factory.domain.contract`, and the test modules each story extends or changes.
- F0020 and F0022 (built before F0023): `planning/overnight/stories/F0020-opencode-as-a-second-agent-runtime/`, `planning/overnight/stories/F0022-a-project-brings-its-own-skills-and-agents/`. Say where F0023 touches what they change and whether a story needs a note.

## Check in particular


- The order and sizing: each story fits a coder's 40-minute `time_limit` within a 60-minute lease and a few dollars.
- Every behaviour the Interface or a decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; a story that changes another story's tests beyond the standing leave names them, and `feature.md` gives the leave.
- Each file a stage must write is inside that role's write paths in `factory/pipeline.yml` (`claude/*`, `image/*` included?); what is not is a human's change, with its order.
- The human's change to `factory/pipeline.yml`: every stage still within its lease; the new `secrets` command and `documents`' shorter time limit against the measured times in `/state/records/project-commands.jsonl` (read it from the container, read-only).

## Output

One file per story, `F0023-S000N-1.md` (N 1 and 2), and `F0023-feature-1.md` for the feature, its human's changes and decisions, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1.1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands at all. No network calls. No file other than your outputs. Do not change the stories or `feature.md`. Do not start sub-agents. No paid model call of your own. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in the temporary folder `C:/Users/pasca/AppData/Local/Temp/f23pre` and nowhere else, and remove it when done (if a removal is refused, say so). `factory-check-story` imports the Landlock adapter, which fails on Windows: stub it in that temporary folder, or run smoke tests and checks that need Linux in a throwaway container of v1.1's image (`docker run --rm --entrypoint /bin/sh -v <a copy of the repository in the temporary folder>:/src factory-self-factory -c '...'`, `MSYS_NO_PATHCONV=1` first), never in the running instance `factory-self-factory-1`, which is building; mount no instance volume and no secret, and never read a token or key file.

## Reply

Per story its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; anything wrong with the human's changes or the decisions.
