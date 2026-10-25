# The probe's descriptions name no removed layer

<!-- proposed by feature acceptance of 2026-10-25; refine before starting -->

## Description

Two passages still describe the preflight's `agent-run-probe` with a layer that F0044 removed. The first is `docs/operator-guide.md`, *The probe of the agent run*, which says the probe runs "with the agent run's environment and a guard that gives no write path". The write guard went with F0044-S0001 and S0002. `GuardSettings` is now `WritePathSettings` (F0044-S0012), and `AgentRunRequest` carries no write-path settings at all. The probe's request (`factory.application.preflight._probe_request`) holds the agent, the prompt, the decision `question`, the time limit, the working directory and the environment, and nothing is taken from the dataset after the run. The second is `docs/project-guide/stage-environment.md`, *Who calls what*, whose bullet on `agent_run_probe_item` ends "The probe reports no fault for a nested repository the run leaves". The search for nested repositories went with F0044-S0006, so the sentence denies a check that no longer exists anywhere. S0012's documenter noticed the first passage and left it (journal entry 19), because it was outside S0012's names. An operator who reads the probe's paragraph looks for a guard that is not there. This story makes both passages say what the probe does now: it runs on the dataset prepared for `main`, and the factory takes nothing from it, so nothing the probe's run writes reaches the checkout, and the next stage's rollback discards it. Nothing else changes. The probe, its request and its faults behave as they do today.

## Interface

None: nothing changes under `src/factory/`, in any test, or under `vm/`, `template/` or `claude/`. The documenter changes one sentence of `docs/operator-guide.md` and one bullet of `docs/project-guide/stage-environment.md`. No test reads the documents; the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs: `docs/operator-guide.md`, *The probe of the agent run*: the paragraph that begins `` `agent-run-probe` runs the agent runtime once`` names no guard. In its place it says that the probe's run takes nothing from the dataset, so nothing it writes reaches the checkout. The documenter checks this against `agent_run_probe_item` and `_probe_request` in `factory.application.preflight`, and the rest of the paragraph stays as it is. `docs/project-guide/stage-environment.md`, *Who calls what*: the bullet that begins `` - `agent_run_probe_item` `` names no nested repository and says that the probe calls no `take`. `README.md` and `docs/decisions.md`: none. `make documents` ends with `documents ok`.

## Smoke test

```bash
awk '/^`agent-run-probe` runs the agent runtime once/' docs/operator-guide.md | grep -ciE 'guard' || true
```
Expect: `0`

```bash
awk '/^- `agent_run_probe_item`/' docs/project-guide/stage-environment.md | grep -ciE 'nested' || true
```
Expect: `0`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal
