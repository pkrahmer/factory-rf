---
stage: intake
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: null
comments_read: []
handed_over: null
claim:
  instance: self
  stage: intake
  started_at: '2026-10-21T06:58:49.235031Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-21T06:58:49.228286Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-21T06:58:49.235031Z'
  stage: intake
---

# The project guide points to the template's pipeline definition and describes `factory-health`

## Description

Two gaps in the project guide (findings H4 and M5 of the documentation review of 2026-10-20, re-checked on `main` of 2026-10-20). First, `docs/project-guide/agents.md`, *The template*, quotes `template/factory/pipeline.yml` in a YAML block, and the copy has gone stale: it lacks the `tool_paths` line and its comment, which the file has. An agent or an operator who copies the definition from the guide gets one under which every `make check` ends with `Permission denied`, because the kernel allows no write outside the write paths and tool paths. A copy goes stale again with every change of the file, so the block gives way to a pointer and one sentence on what the file holds. Second, every module under `src/factory` is named in the guide's index, `docs/project-guide/README.md`, except four. No guide file describes `factory.entry.health` (the console command `factory-health`, the container's health check). `factory.domain.sessions` (F0030-S0001: one line of the kernel's process table, and what of a session is left to kill) is described in `processes-and-checks.md`, under *Starting a process* (**Killing a session.**), but its index line does not name it. `factory.application.agent_home` (the interface `AgentHome`) and `factory.adapters.agent_home` (`SudoAgentHome`), both F0040-S0004's, are described in `agents.md`, *The fresh home*, but the index line of `agents.md` names only the other three modules of the fresh home. The five other modules the review found missing were added since by F0025-S0004 and F0025-S0005. This story adds one paragraph on `factory-health` to `watching.md`, names it on that file's index line, names `factory.domain.sessions` on the index line of `processes-and-checks.md`, and names the two `agent_home` modules on the index line of `agents.md`. Nothing else changes; a lasting check that keeps the index complete (the review's structural proposal S4) is the human's to decide.

## Interface

None: nothing changes under `src/factory/`, in any test, the image, the template, a demo or an agent file. The documenter changes `docs/project-guide/agents.md`, `docs/project-guide/watching.md` and `docs/project-guide/README.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `docs/project-guide/agents.md`, *The template*, the bullet on `template/factory/pipeline.yml`: the YAML block is removed. In its place the bullet says, in one sentence, that the file holds the three project commands `check`, `lint` and `test` with their `time_limit`s, the `tool_paths` the project's tools may write besides the write paths, the seven roles with their write paths, and the stages; and that the guide does not copy it, so read the file itself. The bullet's other sentences (the stage order, "Copy it to `factory/pipeline.yml` and adjust it", the coder's write path) stay. `agents.md` holds no fenced `yaml` block after the story.
   - `docs/project-guide/watching.md`, *Stops, the clock and the factory log*: one paragraph after the paragraph on `factory.application.machine` describes `factory-health` (`factory.entry.health`, `main(argv=None, *, store=None) -> int`), checked against `src/factory/entry/health.py`: it reads the health status from the health file of the state directory (`--state-directory <path>`, default the image's `/state`), or from the `HealthStatusStore` it is given; it prints `healthy` and returns 0, or prints one line per stop in force, `<reason> (<scope>): <detail> (since <at>)`, and returns 1; a missing health file prints `no health status: <path> is missing` and returns 1.
   - `docs/project-guide/README.md`, *The files*, the `watching.md` line: "It describes ..." gains `factory-health` after `factory-run`, and "It also names ..." gains `factory.entry.health` before `factory.entry.run`, each in backticks. The `processes-and-checks.md` line: "It also names ..." gains `factory.domain.sessions` after `factory.domain.known_results`. The `agents.md` line: "The fresh home (`factory.domain.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home`)" becomes "The fresh home (`factory.domain.agent_home`, `factory.application.agent_home`, `factory.adapters.agent_home`, `factory.adapters.home_files`, `factory.entry.fresh_home`)". No other line of the index changes.
   - After the story every module under `src/factory` (each `.py` file but `__init__.py`, by its dotted name) is named in backticks in the index. `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c '^ *```yaml' docs/project-guide/agents.md || true
grep -c 'tool_paths' docs/project-guide/agents.md
```
Expect: two lines, `0`, then a number of at least `1`

```bash
grep -c -F -e '`factory.entry.health`' -e 'no health status: <path> is missing' docs/project-guide/watching.md
( cd src && for m in $(find factory -name '*.py' ! -name '__init__.py' | sed 's/\.py$//; s#/#.#g' | sort); do grep -q -F "\`$m\`" ../docs/project-guide/README.md || echo "missing: $m"; done ); echo end
```
Expect: a number of at least `1`, then the single line `end` (no module of `src/factory` is missing from the index)

```bash
git diff --name-only origin/main -- src tests image template demo claude | wc -l; git diff --name-only origin/main -- README.md docs
```
Expect: four lines, `0`, then `docs/project-guide/README.md`, `docs/project-guide/agents.md` and `docs/project-guide/watching.md`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-21 human: created.
2. factory: started intake as self.
