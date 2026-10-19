# Brief: a security review of v1.1's write guard and confinement (the human's word, 2026-10-19)

## Goal

Think and test like a prompt-injected agent inside a stage run of v1.1, and find every way it could (a) write outside its role's write paths, (b) change what a later run or the factory itself does (persistence), (c) read or leak a secret (the subscription token, the API key, the hosting token), (d) push, merge or touch GitHub beyond what the factory does, or (e) make a check pass that should fail. For each route: whether today's guard stops it (the kernel's Landlock rules through `factory-confine`, the Claude Code hook `factory-guard`, the tools list, the settings' allow and deny lists, file ownership and modes in the image, the factory's own checks after the run), with evidence.

Routes to try at least: `.git/config` and hooks (core.fsmonitor, core.hooksPath, filters, includes) and anything the factory's own git runs read; `.claude/` and `CLAUDE.md` (project files Claude Code loads into later runs), the agent's home `~/.claude` (settings, commands, skills, `CLAUDE.md`), `.claude.json`; symlinks and hard links from a write path to outside; `/tmp` and the run's `TMPDIR`; the work item's own files (the journal and front matter the factory owns); `factory/pipeline.yml`, `Makefile`, `pyproject.toml`, `security/`, `.secrets.baseline` (protected paths) and indirect changes to what `make check` runs (`conftest.py`, a pytest plugin via `tests/`, a `.pth` in the venv, `uv` caches); environment variables and `/proc`; the token files and mounts; network egress from a run; F0020's opencode runtime and its own folders; F0022's planned project agents and skills.

## Inputs

`CLAUDE.md`; `docs/project-guide/README.md` and its files `write-guard.md`, `agents.md`, `stages.md`, `processes-and-checks.md`; `docs/operator-guide.md` and `docs/decisions.md` (the guard's decisions); `src/factory/domain/confinement.py`, `src/factory/domain/paths.py`, `src/factory/domain/write_paths.py`, `src/factory/adapters/landlock.py`, the `factory-confine` and `factory-guard` entry points, `src/factory/adapters/claude_runtime.py`, `opencode_runtime.py`, `agent_launch.py`; `image/Dockerfile`, `image/compose.yml`, the entrypoint; `claude/settings.json`, `claude/agents/*.md`; `factory/pipeline.yml`; F0019's feature and decisions (`factory/features/F0019-the-write-guard-by-the-kernel/`), its probe `planning/overnight/probe-F0019-2026-10-18.md`; F0022's draft (`planning/overnight/stories/F0022-a-project-brings-its-own-skills-and-agents/`).

## How to test

Only in throwaway containers of the image `factory-self-factory` (`MSYS_NO_PATHCONV=1 docker run --rm --network none ...`) on a copy of the repository in your temporary folder `C:/Users/pasca/AppData/Local/Temp/secrev`, as the agent user through `factory-confine` as a real run would, with stand-in files in place of every token and key (never the real ones). Never touch the running `factory-self-factory-1` (read-only `docker inspect` of its mounts and user is fine), never mount an instance volume or `image/secrets/`. Keep the containers light (a few cores): the running instance builds stories beside you.

## Output

`C:/Dev/Projects/factory-rf/planning/overnight/security-review-2026-10-19.md`: a table of routes (route, goal a to e, stopped by what, evidence, severity high/medium/low), then per open route a proposed story in one paragraph (what to build, which feature it fits, its criterion), and what you could not test.

## Not

No git commands in the repository; no network from your own commands; no sub-agents; no paid model call; no file other than the output and the temporary folder, removed at the end; never read a token or key file.

## Reply

The open routes by severity, one line each, and the proposed stories.
