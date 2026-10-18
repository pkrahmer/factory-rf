# Brief: pre-check F0020 round 1 with v1.1's own roles (nine stories)

## Goal

For each story of `F0020-opencode-as-a-second-agent-runtime`, play v1.1's intake exactly (the shipped agent `claude/agents/intake.md` with the story form `factory/story-form.md`), then predict whether the tester, coder, reviewer, documenter, smoke tester or acceptance reviewer (`claude/agents/*.md`) would stop it, and give it one verdict line. The stories were written by the session's drafting agent and have not been checked against v1.1's roles. Also judge the feature's "human's changes" (exact lines, the story each must come before, whether one is missing or wrong) and its decisions, above all: the runtime per instance, the result block parsed from opencode's text, the spend-limit end reason with its wait and resume outside the caps (the human's requirement 8 in the brief), the claim held while waiting, and the throttle.

For every test a story names or describes, check it against the built code and the tests that pin it (structural tests such as `tests/test_process_search.py`, `tests/test_wrapper_search.py`, `tests/test_claude_files.py`, `tests/test_claude_agent_texts.py`, `tests/test_model_configuration.py`, `tests/test_compose.py`, the layer contracts, fixture order, `mypy --strict`, ruff with the project's rules, coverage at 90 %); run every smoke-test command against today's code where it can run before the story, and check that every file it names exists or is made by the story. Check the opencode facts against `planning/overnight/opencode-probe-2026-10-17.md` and say which a story assumes beyond the probe.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0020-opencode-as-a-second-agent-runtime/feature.md` and the nine stories under `backlog/`.
- The brief the drafter worked from: `planning/overnight/briefs/draft-F0020.md`; the probe: `planning/overnight/opencode-probe-2026-10-17.md`.
- v1.1's roles and forms: `claude/agents/*.md`, `factory/story-form.md`, `factory/feature-form.md`, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml`, `Makefile`.
- The code and tests each story touches: `src/factory/adapters/claude_runtime.py`, `src/factory/adapters/process.py`, `src/factory/application/agent_runtime.py`, `src/factory/application/sealed_runs.py`, `src/factory/application/stage.py`, `src/factory/application/stalls.py`, `src/factory/domain/agent_runs.py`, the preflight and its items, the wiring, `image/Dockerfile`, `image/compose.yml`, and the test modules each story extends or changes.
- How F0019 went: `factory/features/F0019-the-write-guard-by-the-kernel/` (`feature.md`, the journals in `done/`: what the intake asked, where reviews went to the round cap, the crash from `mutants/seed`).

## Check in particular

- The order and sizing: each story fits a coder's 40-minute `time_limit` within a 60-minute lease and a few dollars; a story that moves shared code (S0002) changes no behaviour and no earlier test beyond the standing leave.
- The human's change 1 (an empty key file before S0001 is merged, or Compose refuses to start): is it needed, is there a way without it (for example a Compose bind that tolerates a missing file, or a folder mount), and is the order safe for the running instance `self`?
- The spend-limit wait: the claim held while waiting against the lease (does a wait of 10 minutes or more outlive a 60-minute lease, renewed or not?), the stall reason past the ceiling, and that waits count toward no attempt and no cap.
- Every behaviour the Interface or a decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; a story that changes another story's tests beyond the standing leave names them, and `feature.md` gives the leave.
- Each file a stage must write is inside that role's write paths in `factory/pipeline.yml`; what is not is a human's change, with its order.
- The gap the drafter reported: the agent run's environment carries no gateway base URL, so neither runtime can reach a gateway that needs its own address. Recommend whether it belongs in F0020 (the human's work needs it) and as which story.

## Output

One file per story, `F0020-S000N-1.md` (N from 1 to 9), and `F0020-feature-1.md` for the feature, its human's changes and decisions, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1.1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands at all. No network calls. No file other than your outputs. Do not change the stories or `feature.md`. Do not start sub-agents. No paid model call of your own. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and remove everything you create (if a removal is refused, say so). `factory-check-story` imports the Landlock adapter, which fails on Windows: run smoke tests and checks that need Linux in a throwaway container of v1.1's image (`docker run --rm --entrypoint /bin/sh -v <a copy of the repository outside it>:/src factory-self-factory -c '...'`, `MSYS_NO_PATHCONV=1` first), never in the running instance `factory-self-factory-1`, which is building; mount no instance volume and no secret, and never read a token or key file.

## Reply

Per story its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; anything wrong with the human's changes or the decisions.
