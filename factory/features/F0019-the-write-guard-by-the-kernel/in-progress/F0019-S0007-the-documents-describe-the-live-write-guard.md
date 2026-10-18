---
stage: approval
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 227
comments_read: []
handed_over: null
claim: null
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
- number: 5
  speaker: tester
  kind: result
  at: '2026-10-18T19:11:23.061205Z'
  stage: tests
  run: 8de3f032009f49d5b9f3f87cb14b815a
- number: 6
  speaker: factory
  kind: started
  at: '2026-10-18T19:11:42.839225Z'
  stage: doing
- number: 7
  speaker: coder
  kind: result
  at: '2026-10-18T19:13:25.116104Z'
  stage: doing
  run: 485c7896a08e4b12be8e1cf96d6eb420
- number: 8
  speaker: factory
  kind: started
  at: '2026-10-18T19:13:45.040066Z'
  stage: review
- number: 9
  speaker: reviewer
  kind: result
  at: '2026-10-18T19:14:04.907241Z'
  stage: review
  run: b35b7aa00aaa4360b4062c331c386c45
- number: 10
  speaker: factory
  kind: started
  at: '2026-10-18T19:14:24.972263Z'
  stage: docs
- number: 11
  speaker: documenter
  kind: result
  at: '2026-10-18T19:15:35.587716Z'
  stage: docs
  run: 82d54191c96a46c5b7f9ddc6a8b60182
- number: 12
  speaker: factory
  kind: started
  at: '2026-10-18T19:15:55.532665Z'
  stage: smoke-test
- number: 13
  speaker: smoke-tester
  kind: result
  at: '2026-10-18T19:16:18.096349Z'
  stage: smoke-test
  run: 8ec0d14b59a54f6bb44e179b15946d38
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
5. tester: No tests written. This story only changes documentation, and its Interface says no module, test, image, template or agent file changes.
   - criterion 1 (nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changes): no test, since the criterion governs the stages and is not code behaviour. This tester stage changed nothing under any of those paths.
   - criterion 2 (`make check` stays green): no test of its own. The factory's checks enforce it.
   - criterion 3 (docs): no test. The documenter writes it, and `python -m factory.entry.check_documents` and the smoke test check it.
   Files created: none. Modules the test run could not import: none, because no new tests exist. `make test` was not run: without new tests there is nothing to see fail, and the factory runs it after this stage. `make lint`: green. Nothing to interpret, so there is no open question.

   `lint`: lint: green (0.0 s)
   `test`: test: green (37.5 s)
6. factory: started doing as self.
7. coder: Built nothing. This story only changes documentation, and its Interface says no module, test, image, template or agent file changes. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed in this stage, which is what criterion 1 asks. The three documents (`README.md`, `docs/operator-guide.md`, `docs/project-guide.md`) belong to the documenter, so I left them alone too.
   Main choice: hand forward with no change. I rejected the alternative of making the docs edits here, because CLAUDE.md gives the docs to the documenter stage and not to the coder.
   Refactor: there is no diff, so there was nothing to refactor. The journal did not change the meaning of the task, so `## Description` is unchanged.
   Noticed but not touched: nothing.
   `make check`: check: green (test: green, total coverage 98.67 %).

   `check`: check: green
   `duplicates`: duplicates: 0 new, 36 known, 3 gone
8. factory: started review as self.
9. reviewer: no findings
   The diff outside `factory/` is empty, which is what criterion 1 asks for a documents-only story. The coder's entry 7 reports the factory's `make check` as green, and `make duplicates` reports 0 new findings. I checked the docs criterion against the code and the documents, and it still describes what the documenter must write. The stale passages are still in place: "Six commands" at `README.md:12`, which names seven; "once the runtime uses it" at `README.md:12` and `docs/operator-guide.md:3`; and "Once the kernel's write guard is live" at `docs/operator-guide.md:706`. `template/Makefile:74` still writes `.licenses-requirements.txt` at the checkout's root. This repository moved both files into `.reports/` (`pyproject.toml:108` `data_file`, `Makefile:66`). `confinement_item(abi, environment, find)` at `src/factory/application/preflight.py:184` joins its kernel and `PATH` faults with `; ` under the item `confinement`. The Description matches what was built, which is nothing outside the documents.
   Earlier tests: the diff changes, renames or deletes no test file that `main` holds.
10. factory: started docs as self.
11. documenter: Wrote the five passages the docs criterion names. Changed no code, test, image, template, demo or agent file.
    Files changed:
    - `README.md`: "Six commands exist" is now "Seven commands exist", and ", once the runtime uses it" is gone from the `factory-confine` clause.
    - `docs/operator-guide.md`: the opening paragraph drops "once the runtime uses it" (the clause now ends "confined by the kernel"). The `tool_paths` paragraph now begins "An agent run can write only its stage's write paths and these folders". After it, a new paragraph says a project made from `template/`, or the todo demo, writes `.licenses-requirements.txt` and `.coverage` at the checkout's root, where the kernel allows no write. It says to move both into a tool path folder, as this repository did into `.reports/`, and to name `tool_paths`. Until then `make check` ends with `Permission denied`.
    - `docs/project-guide.md`, *The kernel's write guard*: one paragraph on `confinement_item(abi, environment, find)`. It covers the item `confinement`, its two faults (the kernel's first, joined by `; `), the kernel advice text, and the wiring passing `abi_version` and a search on the agent run's `PATH`. I read this against `src/factory/application/preflight.py` and `src/factory/entry/wiring.py`.
    Checks: `grep` finds no "once the runtime uses it" in either file. `python -m factory.entry.check_documents` prints `documents ok`. I ran no `make check`, because I changed only documents.
    Cross-read and found current: the other passages of the operator guide and the project guide that name `tool_paths` and the kernel's write guard.
    Stale text I saw and did not touch, because the criterion says no other passage changes: `docs/project-guide.md`, *The kernel's write guard*, the line "Nothing starts it yet: the runtime will." This is stale, since the runtime has started every agent run through `factory-confine` since S0004. It needs a small follow-up story.

    `check`: check: green
    `documents`: documents ok
12. factory: started smoke-test as self.
13. smoke-tester: Smoke test: I ran the four commands from the repository root, as written and in order. All four met their `Expect:` line. No findings.

    1. Command `grep -c "once the runtime uses it" README.md docs/operator-guide.md`
    ```
    README.md:0
    docs/operator-guide.md:0
    ```
    Met: the output is `README.md:0` and `docs/operator-guide.md:0`.

    2. Command `grep -c "Seven commands exist" README.md; grep -c "Once the kernel's write guard is live" docs/operator-guide.md`
    ```
    1
    0
    ```
    Met: `1`, then `0`.

    3. Command `grep -c "licenses-requirements.txt" docs/operator-guide.md; grep -c "confinement_item(abi, environment, find)" docs/project-guide.md`
    ```
    1
    1
    ```
    Met: at least `1`, then `1`.

    4. Command `uv run python -m factory.entry.check_documents`
    ```
    documents ok
    ```
    Met.

    Acceptance criteria, read again against the branch:
    - Criterion 1: `git diff --stat origin/main...HEAD` touches only `README.md`, `docs/operator-guide.md`, `docs/project-guide.md` and the work item with its `.costs.jsonl`. Nothing under `src/`, `tests/`, `image/`, `template/`, `demo/` or `claude/` changed. The tester (entry 5) and the coder (entry 7) each said so.
    - Criterion 2: the factory's `make check` was green after the docs stage (entry 11).
    - Criterion 3:
      - `README.md:12` says "Seven commands exist" and still names all seven: factory-run, factory-check-story, factory-bill, factory-watch, factory-health, factory-guard and factory-confine.
      - `docs/operator-guide.md:706` begins "An agent run can write only its stage's write paths and these folders".
      - `docs/operator-guide.md:708` is the new template/demo paragraph. It names `.licenses-requirements.txt` and `.coverage` at the root, the move into `.reports/` (`data_file` under `[tool.coverage.run]`, the `licenses` recipe), naming `tool_paths`, and `Permission denied` until then.
      - `docs/project-guide.md:1337` describes `confinement_item(abi, environment, find)`. It covers the item `confinement`, its two faults (the kernel's first, joined by `; `), the advice text, and the wiring passing `abi_version` and a search on the agent run's `PATH`.
      - The smoke test contradicts no criterion.

    Open, outside this story: the documenter (entry 11) found a stale line in `docs/project-guide.md`, "Nothing starts it yet: the runtime will." This criterion forbids changing other passages, so it needs a follow-up story. It is not a finding here.
