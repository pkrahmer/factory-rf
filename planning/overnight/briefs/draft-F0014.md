# Brief: draft F0014, the first start's findings, for v1 to build

## Goal

Write the feature `F0014-the-first-start-findings` and its stories so that v1 can fix, before the shakedown run (plan step 4), the faults the first start of v1.1 found on 2026-10-17 under Docker Desktop and Podman.

## Inputs (read these first)

- The findings: `C:/Dev/Projects/factory-rf/planning/overnight/first-start-checklist.md`, section "Results" (faults 1 to 4, what held).
- The plan: `C:/Dev/Projects/factory-rf/planning/overnight/restructure-after-f0011.md`, steps 2 and 4.
- The image and its tests: `image/Dockerfile`, `image/compose.yml`, `image/entrypoint.sh`, `image/git-credential-factory`, `tests/test_image*.py`, `tests/test_compose*.py`, `tests/test_agent_home_ownership.py`, `tests/test_token_folder.py`; the git wrapper and its environment (`src/factory/adapters/git_cli.py`, `src/factory/entry/wiring.py`, `GIT_CONFIG_*`); the agent runtime and its environment allow list (`src/factory/domain/agent_runs.py` `ALLOWED_ENVIRONMENT_NAMES` and `scrub_environment`, `src/factory/adapters/claude_runtime.py`); the preflight (`src/factory/application/preflight.py`, the token-file and agent-run-probe items); the operator guide's parts on the agent user, the login, the token and the container runtimes. All paths are under `C:/Dev/Projects/factory-rf/`.
- The forms and rules v1 applies: `factory/TICKET.md`, `factory/FEATURE.md`, `factory/stages.yml` (write paths: the coder writes `src/*`, `image/*`, `template/*`, `claude/*`; the tester `tests/*`; the documenter `README.md` and `docs/*`); v1's role files under `C:/Dev/Projects/factory/claude/skills/`; `CLAUDE.md`; `planning/lessons-for-the-skills.md` (note the row on detect-secrets: give secret-like values as prose).
- How a feature and its stories look when they pass: `factory/features/F0013-podman-and-the-token/FEATURE.md` and its stories in `done/`.

## The content (the human's answers, 2026-10-17)

1. The agent can use git in the shared checkout: a root-owned, agent-read-only `/etc/gitconfig` in the image with `safe.directory` for the checkout (the factory's own git keeps `GIT_CONFIG_NOSYSTEM=1` and is the owner, so it needs none). A test of the image file; the real run is observed in step 4.
2. The factory's own git never runs hooks: `core.hooksPath` set to an empty or null path in the factory's git environment (beside `credential.helper` and `core.sharedRepository` in `wiring.py`), so a hook an agent writes into `.git/hooks` never runs as `factory`. Tested with a real hook in a real repository that must not run.
3. Every credential is injected from outside; no interactive login on any instance: the Claude token made once with `claude setup-token`, kept on the host as `image/secrets/claude-token`, mounted read-only where the agent user may read it (it is the agent's own login, as its login file is today), and handed to each agent run only, as `CLAUDE_CODE_OAUTH_TOKEN`, through the runtime's environment (the allow list gains that one name only for agent runs; the factory's own processes and the project commands never get it). The preflight's probe names the token file when it fails; without the file the manual login still works. Optionally the same for an API key: say whether it fits, otherwise leave it out of scope with the reason.
4. The guide: an agent-made folder is `2775`; where the login lives; `claude setup-token` replaces "log in once as agent"; under Podman on Windows a shell may not see the saved connection (`--url` and `--identity`, `podman system connection list`).

## Rules for the split

- One story is one coder's work within $4 and a 60-minute lease. Documentation-only items may be one story whose coder changes nothing and whose docs criterion carries the text.
- Every behaviour has its own criterion; both sides of every rule as rows of one parametrized test; test data valid under the built code; a Demo's `Expect:` met exactly by the built code, no doubled `-q`.
- What lies outside every write path (`Makefile`, `pyproject.toml`, `factory/stages.yml`, `security/*`) is "The human's change before S000N" in FEATURE.md, with exact lines.
- A story that changes tests another story wrote names them, and FEATURE.md gives the leave as a decision.
- No word of `GLOSSARY_FORBIDDEN` outside a `## Replaced from v1` section in the documents. No secret-like key with a value in a story's text (detect-secrets scans it): give such values as prose.

## Write

`C:/Dev/Projects/factory-rf/planning/overnight/stories/F0014-the-first-start-findings/FEATURE.md` (Goal, Scope, Out of scope, Stories in build order, the human's changes, Decisions taken for the human with their source) and the stories under its `drafts/` as `F0014-S000N-<slug>.md`.

## Not

No git commands. No file outside `planning/overnight/stories/F0014-the-first-start-findings/`.

## Reply

The stories with one line each, the human's changes, the decisions you took for the human, and anything you could not place.

Model: opus.
