---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 464
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-10-26T17:47:59.795382Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-26T17:47:17.609681Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-26T17:47:17.615192Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-26T17:47:39.497170Z'
  stage: intake
  run: 939a41bc92234ba09ef3fcb35d7d15d9
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-26T17:47:59.795382Z'
  stage: tests
---

# The feature's documents agree with what was built and with each other

<!-- proposed by feature acceptance of 2026-10-26; refine before starting -->

## Description

The three stories of F0046 each wrote their part of the documents without seeing `feature.md` or the parts the others wrote, and four gaps are left. First, `docs/decisions.md` still says at the end of *A company's provider for opencode* and of *The containers' environment stays closed except for the operator's list* that the other options are "Left to later stories of F0046". Those stories are merged. Second, S0001's docs criterion asked for its decision entry to be written from the feature's decisions 1 to 5 and 9, but the documenter could not read `feature.md`. The entry has no decision 1 (the option is off by default, and with it unset the run's configuration file is byte-identical) and no decision 9 (no test runs the real opencode; the preflight's `agent-run-probe` on the machine shows whether the pinned opencode accepts the provider block). Third, the operator guide's *A company's provider* does not tell the operator where to see that the provider works. Fourth, *The environment file* and *Behind a proxy* do not say that every name in `factory.local.env` also reaches the factory's own process. The unit sets these names for the whole service, so a proxy put there for the containers is in the factory's own environment too. This story closes those four gaps in the two documents. Unchanged: the code, the tests, `vm/`, `README.md`, the project guide, and every other sentence of the two documents. Left to the human: whether the factory's own hosting client and git need the company's CA on the host. This story states only what reaches the process.

## Interface

None: nothing changes under `src/factory/`, in any test, or under `vm/`, `template/` or `claude/`. The documenter changes `docs/decisions.md` and `docs/operator-guide.md` only. No test reads the documents: the smoke test and `make documents` check the docs criterion.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `vm/`, `template/` or `claude/` changes, and the tester and the coder each end with an entry that says so.
2. `make check` stays green.
3. docs: the smoke test and `make documents` check these, and no test does:
   - `docs/decisions.md`: no line contains `Left to later stories of F0046`.
   - `docs/decisions.md`, *A company's provider for opencode*: a bullet on the default. With `FACTORY_OPENCODE_PROVIDER_FILE` unset, the run's configuration file is byte-identical to the one written before the setting existed. A bullet on how the provider is shown to work. No test runs the real opencode. The preflight's `agent-run-probe` shows on the machine whether the pinned opencode accepts the provider block.
   - `docs/operator-guide.md`, *A company's provider*: one sentence that names the preflight's `agent-run-probe` as the place where the operator sees whether the pinned opencode accepts the provider file and reaches the proxy. The sentence refers to *The probe of the agent run* for when the probe runs.
   - `docs/operator-guide.md`, *The environment file*: one sentence that says every name in `factory.local.env` is in the factory process's own environment, because the unit sets it for the service. `FACTORY_CONTAINER_ENV` then chooses which of these names the containers also get. *Behind a proxy* points to that sentence.
   - No other section of the two documents changes, and `make documents` ends with `documents ok`.

## Smoke test

```bash
grep -c 'Left to later stories of F0046' docs/decisions.md
```
Expect: `0`

```bash
awk '/^### A company.s provider$/{on=1; next} /^##/{on=0} on' docs/operator-guide.md | grep -c -F 'agent-run-probe'
awk '/^## A company.s provider for opencode$/{on=1; next} /^## /{on=0} on' docs/decisions.md | grep -c -F 'agent-run-probe'
```
Expect: two lines, each a number of at least `1`

```bash
make documents 2>&1 | tail -n 1
```
Expect: `documents ok`

## Journal

1. 2026-10-26 human: created.
2. factory: started intake as vm.
3. intake: accepted
   Interface: "None" is stated and fits the story. Nothing changes under src/, tests/, vm/, template/ or claude/, and only docs/decisions.md and docs/operator-guide.md are named. There are no signatures or behaviours to pin.
   Criteria: all four gaps in the Description have a docs bullet. The "Left to later stories of F0046" lines exist at docs/decisions.md:1161 and :1173. The decision 1 and decision 9 bullets, the agent-run-probe sentence and the factory.local.env sentence each have one. Criterion 1 covers the "nothing else changes" side. The story adds no rule with a failing side, because it states no limit, validation or rejected input, so none is missing. No test reads the documents; the docs criterion is checked by the smoke test and `make documents`.
   Smoke test: the commands are runnable. The target sections exist: `### A company's provider` (operator-guide:289), `## A company's provider for opencode` (decisions:1149), *The environment file* (:442), *Behind a proxy* (:206) and *The probe of the agent run* (:748). Each Expect line is checkable: `0`, two numbers of at least 1, and `documents ok`. The story's smoke test runs no pytest, so the `-q` rule does not apply.
   Architecture: the story touches documents only and leaves the layers alone. The documenter's write paths (README.md and docs/*) cover both files.
   Scope: it fits F0046. feature.md lists S0005 as "from A0001". Its Out of scope items (a base_url, a secret store, any company value) are not touched, and the CA-on-host question is left to the human.
4. factory: started tests as vm.
