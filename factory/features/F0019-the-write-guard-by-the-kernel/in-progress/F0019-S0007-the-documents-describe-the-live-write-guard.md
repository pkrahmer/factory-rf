---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 227
comments_read: []
handed_over: null
claim:
  instance: self
  stage: tests
  started_at: '2026-10-18T19:10:31.304057Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-10-18T19:09:49.241217Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-10-18T19:09:49.246877Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-10-18T19:10:11.438468Z'
  stage: intake
  run: a6162620299f48c7a53788148423930e
- number: 4
  speaker: factory
  kind: started
  at: '2026-10-18T19:10:31.304057Z'
  stage: tests
---

# The documents describe the live write guard

<!-- proposed by feature acceptance of 2026-10-18; refine before starting -->

## Description

F0019's acceptance read the documents as a whole after the guard went live and found five passages that are stale or missing. `README.md:12` says "Six commands exist" and names seven; the count was not raised when `factory-confine` was added. `README.md:12` and `docs/operator-guide.md:3` say `factory-confine` starts every agent run "once the runtime uses it", which it has done since S0004. `docs/operator-guide.md:706` begins "Once the kernel's write guard is live", and the guard is live now (`factory/pipeline.yml` holds the `tool_paths`). The operator guide does not warn that a project made from `template/`, or the todo demo, writes `.coverage` and `.licenses-requirements.txt` at the checkout's root and names no `tool_paths`. The kernel refuses both root files, so such a project's `make check` fails under the guard until its `Makefile`, its coverage settings and its pipeline definition are changed (F0019's decision 17). Last, `docs/project-guide.md` does not describe the preflight item's function `confinement_item`. This story makes the five passages true. It is documentation only: the tester and the coder change nothing, and the template and the demo themselves stay as they are.

## Interface

None: no module under `src/factory/`, no test, no image, template or agent file changes. The documenter changes `README.md`, `docs/operator-guide.md` and `docs/project-guide.md`.

## Acceptance criteria

1. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes; the tester and the coder each end with an entry saying so.
2. `make check` stays green.
3. docs:
   - `README.md`: the sentence that counts the commands says "Seven commands exist" and still names all seven. Its clause about `factory-confine` drops ", once the runtime uses it".
   - `docs/operator-guide.md`: the opening paragraph drops "once the runtime uses it" from its clause about `factory-confine`. The paragraph after the `tool_paths` example begins "An agent run can write only its stage's write paths and these folders" instead of "Once the kernel's write guard is live, an agent run can write only ...". After that paragraph, a new paragraph says what a project made from `template/` or the todo demo needs before it runs under the guard. Its `Makefile`'s `licenses` recipe writes `.licenses-requirements.txt`, and coverage writes `.coverage`, both at the checkout's root, where the kernel allows no write. The fix is to move both into a tool path folder, as this repository did into `.reports/` (`data_file` under `[tool.coverage.run]`, the `licenses` recipe), and to name the project's `tool_paths` in its pipeline definition. Until then, its `make check` ends with `Permission denied`.
   - `docs/project-guide.md`, section *The kernel's write guard*: one paragraph on `confinement_item(abi, environment, find)` (`factory.application.preflight`). It covers the item `confinement`, its two faults (the kernel's first, joined by `; `) and the advice text, and says that the wiring passes `abi_version` and a search on the agent run's `PATH`.
   - No other passage changes. `python -m factory.entry.check_documents` prints `documents ok`.

## Smoke test

```bash
grep -c "once the runtime uses it" README.md docs/operator-guide.md
```
Expect: `README.md:0` and `docs/operator-guide.md:0`

```bash
grep -c "Seven commands exist" README.md; grep -c "Once the kernel's write guard is live" docs/operator-guide.md
```
Expect: `1`, then `0`

```bash
grep -c "licenses-requirements.txt" docs/operator-guide.md; grep -c "confinement_item(abi, environment, find)" docs/project-guide.md
```
Expect: a number of at least `1`, then `1`

```bash
uv run python -m factory.entry.check_documents
```
Expect: `documents ok`

## Journal

1. 2026-10-18 human: created.
2. factory: started intake as self.
3. intake: accepted
   Interface: "None" is stated and fits a documents-only story. It names the three documents the documenter changes. `confinement_item(abi, environment, find)` exists in `src/factory/application/preflight.py:184`, so the project-guide paragraph has a real function to describe.
   Criteria: each docs bullet is checkable by one grep or by `check_documents`. They are the "Seven commands exist" count, the dropped "once the runtime uses it" in two files, the reworded `tool_paths` paragraph, the new template/demo paragraph, and the `confinement_item` paragraph. The Interface states no rule with a failing side, so there is none to cover.
   Smoke test: four commands. The greps are runnable, and `grep -c` over two files prints `file:count`, which matches the first Expect line. Every Expect line has a concrete value, and the last is `documents ok`.
   Architecture: documents only, so the layering is not touched. The `confinement_item` paragraph correctly places it in `factory.application.preflight`, with the wiring passing `abi_version` and a search on the agent run's PATH.
   Scope: F0019's acceptance proposed the story. It is documentation for the feature, and `feature.md` lists the three documents under Scope. The template and demo stay untouched, as its Out of scope and decision 17 say.
4. factory: started tests as self.
