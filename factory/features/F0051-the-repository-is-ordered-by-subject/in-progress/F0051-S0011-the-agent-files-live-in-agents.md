# The agent files live in `agents/`

## Description

The factory's agent files and their settings live in `claude/` (`claude/agents/*.md`, `claude/settings.json`), and the image copies them to `/etc/factory/claude`. They are written in Claude Code's format, but the opencode runtime reads them too and translates them per run (the decision of 2026-10-19, F0020-S0004), so the name says one runtime where there are two (F0051 candidates, item 38). This story renames the folder to `agents/` and the image's folder to `/etc/factory/agents`. The format of the files does not change, and `operator/claude/` and `operator/opencode/`, which are the operator's commands for each runtime, keep their names.

## Interface

- `claude/` → `agents/` with `git mv` (`agents/agents/*.md` and `agents/settings.json`).
- `vm/Dockerfile`: the copy and the permissions of the agent files use `agents/` and `/etc/factory/agents`.
- Every place under `src/`, `tests/`, `vm/`, `operator/`, `docs/` and `README.md` that names the folder `claude/` of the agent files, or `/etc/factory/claude`, names the new one; a name of the runtime Claude Code (`claude_runtime`, the `claude` command, `.claude/` in an agent's home) does not change.
- The coder's write path `claude/*` in `factory/pipeline.yml` and the names in `CLAUDE.md` are the human's changes, made at this story's start.

- The tester makes every test change the rename needs in its first run, before the files move: every path and name of the old folders in `tests/`, under the leave of feature decision 5. The coder changes `src/`, the renamed folders and the documents it may write; its write paths do not hold `tests/`, so a test change it makes is dropped.

## Acceptance criteria

1. `claude/` does not exist, and `agents/agents/` holds the same agent files that `claude/agents/` held before (one row per file name).
2. The image built from `vm/Dockerfile` holds the agent files in `/etc/factory/agents/agents/` and none in `/etc/factory/claude` (a test of the Dockerfile's copy and permission lines, as the stage image's tests check them today).
3. The factory finds the agent files at their new place: a stage run in the fake world reads its agent's file from `agents/agents/<role>.md`.
4. No file under `src/`, `tests/`, `vm/`, `operator/`, `docs/` other than `docs/decisions.md`, or `README.md` names `claude/agents/`, `claude/settings.json` or `/etc/factory/claude`.
5. `make check` stays green.
6. docs: the new folder in `README.md`, the operator guide's topic file on the agent files, and the project guide's `agents.md`. `docs/decisions.md`: an entry for the rename with its reason, naming F0051-S0011.

## Smoke test

```bash
test -d claude && echo still there || echo renamed
```
Expect: `renamed`

```bash
test -f agents/settings.json && test -f agents/agents/coder.md && echo found
```
Expect: `found`

```bash
grep -c '/etc/factory/agents' vm/Dockerfile | awk '{print ($1>=1)}'
```
Expect: `1`

## Journal
