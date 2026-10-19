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
  started_at: '2026-10-19T20:29:37.317717Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T20:29:37.310835Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T20:29:37.317717Z'
  stage: intake
---

# The documents name a nested skills folder and the upgrade of a reused agent home

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

F0022's acceptance read the documents as a whole and found four passages that leave out what the feature itself recorded. (1) `docs/operator-guide.md`, *A project's own skills*, says "`.claude/*` is a protected path that no stage writes". That holds only for the root folder. The feature's decision 12 leaves open that a stage may write a `.claude/skills/` in a subfolder inside its write paths (`src/.claude/skills/...`), and that later runs may load it if Claude Code finds nested skills. An operator reading the guide would think every skill is the human's. (2) The guide does not say what the human's change 1 of the feature says. After the first image with the new entrypoint, a `skills/` or `commands/` folder that an earlier agent run made in a reused `claude-home` volume, without group write, cannot be removed by `factory`. The entrypoint then stops under `set -e`, and the instance restarts with `rm: cannot remove ...` in its log. (3) `docs/decisions.md`, the entry *The agents load a project's skills, and the agent's home gets none*, says neither that it supersedes the word "skills" in the open point of the F0012-S0025 entry, nor what decision 12 left open. (4) `docs/project-guide/agents.md` ends *The seven agents* with "To change what an agent is told, edit its file under `claude/agents/`; there is no other copy". That passage is about the shipped agents, but since S0001 a project may carry its own copy. The story changes documents only.

## Interface

None: no module under `src/factory/`, no test, no image, template, demo or agent file changes. The documenter changes `docs/operator-guide.md`, `docs/decisions.md` and `docs/project-guide/agents.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *A project's own skills*, second paragraph: after the sentence on `.claude/*`, a sentence that the protection covers the repository's root `.claude/` only. A stage may write a `.claude/skills/` inside its own write paths (for example `src/.claude/skills/`). Whether Claude Code loads such a nested folder is not known (the feature's proof run looks), and the review and the human's merge see it in the diff. `docs/operator-guide.md`, *The agent runs as a second user*, the paragraph on the agent's home, after its sentence on a `claude-home` volume made by an earlier image: on such a volume a `skills/` or `commands/` folder an agent run made without group write cannot be removed by the entrypoint. The instance then restarts with `rm: cannot remove ...` in `docker logs`. The fix is to remove both folders as root through the volume (`docker run --rm -u root -v factory-<instance>_claude-home:/h alpine rm -rf /h/skills /h/commands`, for example `factory-self_claude-home`) and start the instance again. `docs/decisions.md`, the entry *The agents load a project's skills, and the agent's home gets none*: its `Open:` bullet adds the nested `.claude/skills/` of decision 12, with `src/.claude/skills/` as its example. A sentence says the entry supersedes "skills" in the open point of the entry dated 2026-10-17 (F0012-S0025). `docs/project-guide/agents.md`, *The seven agents*: "there is no other copy" becomes "there is no other copy of a shipped agent", followed by a sentence that a project's own agent is its file under `factory/agents/` on `origin/main` (see *A project's own agents*). No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
sed -n "/^### A project's own skills/,/^### /p" docs/operator-guide.md | grep -c 'src/.claude/skills'
```
Expect: `1`

```bash
grep -c 'rm: cannot remove' docs/operator-guide.md
```
Expect: `1`

```bash
sed -n "/^## The agents load a project's skills/,/^## /p" docs/decisions.md | grep -c 'src/.claude/skills'
```
Expect: `1`

```bash
grep -c 'there is no other copy of a shipped agent' docs/project-guide/agents.md
```
Expect: `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
