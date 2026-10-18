# Brief: draft F0020, opencode as the second agent runtime (plan step 5b), for v1.1 to build

## Goal

Write the feature `F0020-opencode-as-a-second-agent-runtime` and its stories so that v1.1, which builds this repository itself, can build plan step 5b: opencode as a second implementation of the agent-runtime interface (R12), selectable per instance, under the kernel's write guard of F0019 (no opencode plugin for the guard), tested for real by a run of the todo demo through the API.

The first story is fixed by the human (2026-10-18): **the agent runs can log in with an API key.** The compose file mounts `image/secrets/anthropic-api-key` when it exists. The Claude Code runtime then hands that file's contents to the run as `ANTHROPIC_API_KEY` instead of the token file's `CLAUDE_CODE_OAUTH_TOKEN`. Each run's cost record says which login it used. The preflight names the login in force. It is built on the subscription; after it, the human places the key file and the rest of F0020 runs on the API. opencode needs this key anyway: make the key-file reading shared, so that the opencode runtime reuses it.

Write it against v1.1's forms (`factory/feature-form.md`, `factory/story-form.md`) and v1.1's shipped agents (`claude/agents/*.md`), not v1's (`factory/v1/` is history).

## Inputs (read these first)

- The probe: `planning/overnight/opencode-probe-2026-10-17.md` (opencode-ai 1.19.3: `opencode run --format json`, stdin must be closed, the JSON events and where cost, tokens and time sit, sessions and resume, permissions, no budget flag, no schema flag, the snapshot repository in the home). They are one version's facts on one machine: name in the feature what a story's tester can check with a stand-in, and what only the real todo-demo run shows.
- The plan: `planning/overnight/restructure-after-f0011.md`, steps 5a, 5b (with its paragraph "The API key first") and 6 to 10.
- F0019, the guard this runtime runs under: `factory/features/F0019-the-write-guard-by-the-kernel/feature.md` (its decisions, above all 5, 8, 9, 11, 13, 16 and 17) and its stories in `done/`. Decision 16's cross-check of the hook runs during this feature's build; the hook belongs to Claude Code and has no opencode counterpart.
- v1.1's runtime code and its tests: `src/factory/application/agent_runtime.py` (the interface), `src/factory/domain/agent_runs.py` (the DTOs), `src/factory/adapters/claude_runtime.py` (the command line, the login file, the confinement, the budget stop and resume, the decision as structured output, the cost record), `src/factory/adapters/process.py`, `src/factory/entry/wiring.py`, the preflight and its items (`src/factory/application/preflight.py`), the cost records (`src/factory/application/costs.py`), the image (`image/Dockerfile`, `image/entrypoint.sh`, `image/compose.yml`, `image/secrets/`), the agent files (`claude/agents/*.md`, `claude/settings.json`), and the tests that pin each (search `tests/`).
- The forms and rules: `factory/pipeline.yml` (write paths per role, time limits, leases, `tool_paths`), `factory/story-form.md`, `factory/feature-form.md`, `claude/agents/*.md` (above all intake, tester, coder, reviewer), `CLAUDE.md` (Architecture: R5, R6, R12, the one process module; Tests; Not without asking), `docs/project-guide.md`, `docs/operator-guide.md` and `docs/decisions.md` where they touch the runtime, the login, the preflight and the image.
- How v1.1's own features went: `factory/features/F0019-the-write-guard-by-the-kernel/` (the journals in `done/` show what the intake, the reviewer and the round cap asked about: helpers copied between test modules, criteria the reviewer wanted added, earlier tests changed without a named leave, a stage that needed a human's leave for a lint marker). Prevent those in the drafts.

## The content

1. The API-key login (the first story, as above). The key never reaches the command line, a log, a journal, a cost record or the factory's own environment; it is read from the file at each run, like the token file. Without the key file nothing changes.
2. The opencode runtime: the call (`opencode run --format json`, stdin closed, the model, the agent, the prompt), through `factory-confine` like every run, under `sudo` as the agent user like the Claude Code runtime; the parsing of its JSON events into the run's result (cost and tokens summed over `step_finish`, model time, turns, refused tool calls); the decision and entry the stage needs, without a schema flag (say how: a fixed final block the agent file asks for, parsed strictly, its absence a run without a usable reply).
3. The budget: the factory sums the cost while the run streams and stops the run when it passes the budget, then resumes by session with the remaining share, as the Claude Code runtime does with its own budget flag. Say what can be tested with a stand-in.
4. The agent files: opencode's agent format generated from, or kept beside, `claude/agents/*.md`, so that one source holds the pipeline's rules (R14 and the others). Say which, and why.
5. Choosing the runtime: recommend how an instance (or a role) picks its runtime, as a decision for the human: an operator setting per instance is the simplest; per role allows mixing. The preflight's items for opencode (the binary on the agent run's `PATH`, its pinned version, the key file present, an agent-run probe).
6. The image: opencode installed and pinned (npm `opencode-ai` at an exact version, or its binary), and what it writes in the agent's home (the snapshot repository, about 165 MB after four runs in the probe): a tool path, a cache to clean, or a setting that turns it off.
7. The real test (the last story or the acceptance's smoke test): the todo demo built by an instance on opencode through the API. Before that, F0019's decision 17: the template's and the demo's `Makefile` must move `.coverage` and `.licenses-requirements.txt` off the checkout's root, and their pipeline definitions must name their `tool_paths`. Say which story does it, or put it under the human's changes.

## Rules for the split

- One story is one coder's work within its role's `time_limit` (40 minutes, see `factory/pipeline.yml`) and a budget of a few dollars; size them so. About six to eight stories.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a smoke test's `Expect:` met exactly by the built code; every file a smoke test or a test names exists or is made by the story. The smoke test runs in v1.1's container (Linux, as the factory user, umask 002; tests run under the `Makefile`'s umask 022) and under the kernel's write guard; it never makes a paid call (stand-ins for `opencode` and `claude`).
- A story that changes tests another story wrote, beyond the standing leave in `CLAUDE.md`, names them in its Interface, and `feature.md` gives the leave as a decision.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/`, `security/`, `CLAUDE.md`, `.secrets.baseline`) is under *The human's changes* in `feature.md`, with exact lines and the story it must come before. So is anything only the human may do: placing the key file, removing it afterwards, rebuilding the instance.
- No secret-like key with a value in a story's text, no 32-character hex value, and no example that looks like an API key (`make secrets` scans the stories).

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0020-opencode-as-a-second-agent-runtime/feature.md` (in the sections of `factory/feature-form.md`) and the stories under its `backlog/` as `F0020-S000N-<slug>.md` (in the sections of `factory/story-form.md`). Check each story with `uv run factory-check-story <path>` from `/tmp/api-rf` on a temporary copy laid out as `factory/features/F0020-.../backlog/` beside a copy of `factory/story-form.md` (the check reads the form from `factory/` of the current folder); every line must end in `: ok`.

## Not

No git commands. No file outside `planning/overnight/stories/F0020-opencode-as-a-second-agent-runtime/`. Do not start sub-agents. Make no paid call of your own (no `opencode`, no `claude`). Remove every temporary folder you create.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human (the runtime choice above all), how each part is tested, what only the real todo-demo run can show, and anything you could not place.
