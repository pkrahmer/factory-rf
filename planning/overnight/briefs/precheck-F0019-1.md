# Brief: pre-check F0019 round 1 with v1.1's own roles (six stories)

## Goal

For each story of `F0019-the-write-guard-by-the-kernel`, play v1.1's intake exactly (the shipped agent `claude/agents/intake.md` with the story form `factory/story-form.md`), then predict whether the tester, coder, reviewer, documenter, smoke tester or acceptance reviewer (`claude/agents/*.md`) would stop it, and give it one verdict line. The stories were written by the session's drafting agent and have not been checked against v1.1's roles; v1.1 builds this repository since the handover (`3bcee441`), and its first feature (F0018) showed that its intake asks when a story touches something its feature's Scope does not name. Also judge the feature's six "human's changes" (exact lines, the story each must come before, whether one is missing or wrong) and its decisions, above all 12 (the factory stops without Landlock), 3 (a file rule writes in place only) and the `CLAUDE_CONFIG_DIR` assumption.

For every test a story names or describes, check it against the built code and the tests that pin it (structural tests such as `tests/test_process_search.py`, `tests/test_wrapper_search.py`, `tests/test_claude_files.py`, `tests/test_claude_agent_texts.py`, `tests/test_model_configuration.py`, the pipeline-definition loader's rules, fixture order, `mypy --strict`, ruff with the project's rules, coverage at 90 %); run every smoke-test command against today's code where it can run before the story, and check that every file it names exists or is made by the story. Check the Landlock facts against the kernel's documented interface (the three system calls, their numbers on x86_64 and aarch64, the access-right bits per ABI version 1 to 7, the `landlock_create_ruleset` version query, `PR_SET_NO_NEW_PRIVS`), and whether a confined process can run `sudo`, which the runtime's command line uses (`no_new_privs` forbids gaining privileges): that ordering question may decide the design.

## Inputs (read these; nothing else unless a step needs a named source file)

- The feature: `C:/Dev/Projects/factory-rf/planning/overnight/stories/F0019-the-write-guard-by-the-kernel/feature.md` and the six stories under `backlog/`.
- The design: `planning/overnight/write-guard-landlock-2026-10-17.md`; the brief the drafter worked from: `planning/overnight/briefs/draft-F0019.md`.
- v1.1's roles and forms: `claude/agents/*.md`, `factory/story-form.md`, `factory/feature-form.md`, `factory/pipeline.yml`, `CLAUDE.md`, `pyproject.toml`, `Makefile`.
- The code and tests each story touches: `src/factory/adapters/claude_runtime.py`, `src/factory/adapters/process.py`, `src/factory/entry/guard.py`, the preflight and its items, the pipeline definition model and loader, `GuardSettings`, the wiring, `image/Dockerfile`, `image/entrypoint.sh`, and the test modules each story extends or changes.
- How F0018 went: `factory/features/F0018-the-documents-name-the-handover/` (its stories and acceptances in `done/`).

## Check in particular

- The order of `sudo`, `timeout`, `env -i`, the login shell and the wrapper on the runtime's command line: Landlock sets `no_new_privs`, so the wrapper must restrict itself after `sudo` has switched to the agent user, never before. Say whether S0004's order is right.
- Every behaviour the Interface or a decision states has its own criterion, on both sides; the sides of one rule are rows of one parametrized test; a story that changes another story's tests beyond the standing leave names them, and `feature.md` gives the leave.
- Each file a stage must write is inside that role's write paths in `factory/pipeline.yml`; what is not is a human's change, with its order. Change 5 (`tool_paths` in `pipeline.yml` only after the image holds S0003's code) and its sequence.
- Each story fits a coder's 40-minute `time_limit` within a 60-minute lease and a few dollars.

## Output

One file per story, `F0019-S000N-1.md` (N from 1 to 6), and `F0019-feature-1.md` for the feature, its human's changes and decisions, in `C:/Dev/Projects/factory-rf/planning/overnight/precheck/`. Each holds the intake outcome exactly as v1.1's intake would end; the predicted later stops by role; the points for the human with recommended answers; a `## Verdict` line followed by the exact replacement text for each refusal and each recommended edit.

## Not

- No git commands at all, not even read-only ones. No network calls. No file other than your outputs. Do not change the stories or `feature.md`. Do not start sub-agents. Run Python only through `uv run --project C:/Dev/Projects/factory-rf`, in a temporary folder outside the repository, and remove everything you create (if a removal is refused, say so; do not ask anyone to do it for you). You may run read-only commands in v1.1's container (`docker exec factory-self-factory-1 <command>`, `MSYS_NO_PATHCONV=1` first), for example to read the kernel's Landlock ABI; change nothing there and never read a token file.

## Reply

Per story its verdict line; for each refusal or edit its fix in one line; the points for the human with recommended answers; anything wrong with the human's changes or the decisions.
