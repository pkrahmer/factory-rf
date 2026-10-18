# Brief: pre-check F0021 round 1 with v1.1's own roles (four stories)

## Goal

For each story of `F0021-the-factory-records-what-the-human-did`, play v1.1's intake exactly (the shipped agent `claude/agents/intake.md` with the story form `factory/story-form.md`), then predict whether the tester, coder, reviewer, documenter, smoke tester or acceptance reviewer (`claude/agents/*.md`) would stop it, and give it one verdict line. The stories were written by the session's drafting agent and have not been checked against v1.1's roles. Also judge the feature's "human's changes" and its decisions, above all: machine stops recorded in `factory/stops.jsonl` on `main` (a commit per stop event; its effect on the stories' branches, on `make secrets` and on the archive commits), the causes on the journal records, the reviewer's new rules (from round 1 on, test-quality points go forward as notes; the reviewer may add a criterion that needs no code change), and the records contract (generated schemas under `src/factory/contract/`, the version rule, `additionalProperties: false` against readers that ignore unknown fields).

For every test a story names or describes, check it against the built code and the tests that pin it (structural tests such as `tests/test_process_search.py`, `tests/test_wrapper_search.py`, `tests/test_claude_files.py`, `tests/test_claude_agent_texts.py`, `tests/test_model_configuration.py`, `tests/test_compose.py`, the layer contracts, fixture order, `mypy --strict`, ruff with the project's rules, coverage at 90 %); run every smoke-test command against today's code where it can run before the story, and check that every file it names exists or is made by the story.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0021-the-factory-records-what-the-human-did/feature.md` and the four stories under `backlog/`.
- The brief the drafter worked from: `planning/overnight/briefs/draft-F0021.md`.
- v1.1's roles and forms: `claude/agents/*.md`, `factory/story-form.md`, `factory/feature-form.md`, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml`, `Makefile`.
- The code and tests each story touches: `src/factory/domain/journal.py`, `src/factory/domain/work_item.py`, the handlers under `src/factory/application/handlers/`, `src/factory/application/stage.py`, `stalls.py`, `recovery.py`, `stops.py`, `machine.py`, `costs.py`, `acceptance.py`, `acceptance_reading.py`, `src/factory/adapters/claude_runtime.py` (`permission_denials`), the hosting and git wrappers the stop records use, `claude/agents/reviewer.md`, `docs/operator-guide.md`, and the test modules each story extends or changes.
- How F0019 went: `factory/features/F0019-the-write-guard-by-the-kernel/` (`feature.md`, the journals in `done/`: what the intake asked, where reviews went to the round cap, the crash from `mutants/seed`).

## Check in particular

- The order and sizing: each story fits a coder's 40-minute `time_limit` within a 60-minute lease and a few dollars. F0020 (opencode, `planning/overnight/stories/F0020-*/`) is built after F0021: say where the two features touch the same code (the run record, the stall reasons, `permission_denials`) and whether F0020's stories need a note.
- Every behaviour the Interface or a decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; a story that changes another story's tests beyond the standing leave names them, and `feature.md` gives the leave.
- Each file a stage must write is inside that role's write paths in `factory/pipeline.yml`; what is not is a human's change, with its order. The human's change for `[tool.mutmut]` is already on `main`.
- The commits the factory itself makes on `main` for the stop records: do they collide with the factory's other pushes, with a running story's merge of `main`, or with the rule never to push between a merge and its archive?

## Output

One file per story, `F0021-S000N-1.md` (N from 1 to 4), and `F0021-feature-1.md` for the feature, its human's changes and decisions, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1.1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands at all. No network calls. No file other than your outputs. Do not change the stories or `feature.md`. Do not start sub-agents. No paid model call of your own. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and remove everything you create (if a removal is refused, say so). `factory-check-story` imports the Landlock adapter, which fails on Windows: run smoke tests and checks that need Linux in a throwaway container of v1.1's image (`docker run --rm --entrypoint /bin/sh -v <a copy of the repository outside it>:/src factory-self-factory -c '...'`, `MSYS_NO_PATHCONV=1` first), never in the running instance `factory-self-factory-1`, which is building; mount no instance volume and no secret, and never read a token or key file.

## Reply

Per story its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; anything wrong with the human's changes or the decisions.
