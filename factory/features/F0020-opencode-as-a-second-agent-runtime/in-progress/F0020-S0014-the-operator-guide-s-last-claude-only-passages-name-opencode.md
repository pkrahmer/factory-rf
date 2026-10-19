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
  started_at: '2026-10-19T23:13:01.492494Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-19T23:13:01.486862Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-19T23:13:01.492494Z'
  stage: intake
---

# The operator guide's last Claude-only passages name opencode

<!-- proposed by feature acceptance of 2026-10-19; refine before starting -->

## Description

S0011 fixed six passages of `docs/operator-guide.md` that spoke of the agent runtime as if Claude Code were the only one. Its documenter saw three more and left them, because the story did not name them, and nobody owns them now. An operator who reads them for an opencode instance gets a half-true picture:

- The guide's opening paragraph lists among the built parts "the `claude -p` runtime" and not the opencode runtime.
- *The agent runs as a second user* says that with `FACTORY_AGENT_USER=agent` "the runtime does not start `claude` itself" and shows a chain that ends in `claude ...`. Under opencode the same chain (`sudo`, `timeout`, `env -i`, `factory-confine`, the login shell) starts `opencode run ...`, and the section does not say so.
- *`factory-guard` on the agent run's `PATH`* says that the runtime registers the guard as a Claude Code hook. It does not say that an opencode run registers no hook, while the preflight's item `agent-environment` still checks that the command is on the `PATH` under either runtime.

This story corrects these three passages. It changes no code and no test, and adds no new section.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `docs/operator-guide.md` only.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes. The tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`:
   - The opening paragraph names "the `claude -p` and `opencode run` runtimes" where it now names "the `claude -p` runtime".
   - *The agent runs as a second user*: after the sentence that shows the `sudo` chain, one sentence says that under opencode the same chain starts the opencode executable (`FACTORY_OPENCODE`) with `run` and its arguments in place of `claude` (see "Running on opencode"). The documenter checks the words against `docs/project-guide/agents.md` (*The opencode runtime*). The sentence on the `claude` login in `~/.claude` says it concerns Claude Code.
   - *`factory-guard` on the agent run's `PATH`*: one sentence says that an opencode run registers no hook (see "What differs from Claude Code"), and that the item `agent-environment` checks the command on the `PATH` under either runtime. The documenter checks this against `agent_environment_item` (`factory.application.preflight`) and `machine_extras` (`factory.entry.wiring`), which adds the item whatever the runtime.
   - No other passage changes. `uv run python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c 'the `claude -p` runtime,' docs/operator-guide.md; sed -n '/^### The agent runs as a second user/,/^### The kernel refuses every other write/p' docs/operator-guide.md | grep -c opencode
```
Expect: `0`, then a number of at least `1`

```bash
sed -n '/^### `factory-guard` on the agent run/,/^### A provider/p' docs/operator-guide.md | grep -c opencode
```
Expect: a number of at least `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-19 human: created.
2. factory: started intake as self.
