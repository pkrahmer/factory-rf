---
stage: tests
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 570
comments_read: [6656020506]
handed_over: null
claim:
  instance: vm
  stage: tests
  started_at: '2026-11-05T10:48:18.620340Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T10:39:36.364853Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T10:39:36.372134Z'
  stage: intake
- number: 3
  speaker: intake
  kind: question
  at: '2026-11-05T10:40:01.129317Z'
  stage: intake
  run: f07e02d197cd46e69df3d30b220325e6
  blocked: question
- number: 4
  speaker: human
  kind: comment
  at: '2026-11-05T10:47:57.580161Z'
  stage: intake
- number: 5
  speaker: factory
  kind: started
  at: '2026-11-05T10:48:00.089047Z'
  stage: intake
- number: 6
  speaker: intake
  kind: result
  at: '2026-11-05T10:48:13.403469Z'
  stage: intake
  run: 032c998b2dea4513a95e5fe323661a29
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T10:48:18.620340Z'
  stage: tests
---

# The setup's hints name the operator guide's topic file
<!-- proposed by feature acceptance of 2026-11-05; refine before starting -->

## Description

F0051-S0010 split the operator guide into a folder of topic files. Three lines that `operator/vm/setup.sh` prints still send the operator to "the operator guide" with a section name and no file, as if the guide were still one file. These are the two hints for an installed file that differs from the checkout, and the closing `setup: done:` line. The skill's approving reference (`operator/skill/kumpel/references/approving.md`) names "the operator guide's rebuild" the same way. An operator who reads such a line now has to search eleven files. This story makes each of these four places name `docs/operator-guide/machine.md`, which holds both sections, *The machine* and *The rebuild after a merge*. The setup's steps, its exit statuses and the rest of its wording stay as they are. Three things are left out. The docstring of `src/factory/entry/wiring.py:746` ("in the operator guide's order") is not an operator's text. `docs/operator-playbook.md:82`, `demo/todo-service/README.md` and the `Makefile`'s `make mutants` example are the human's files. The two tests that pin the old hint texts are changes to tests other stories wrote, so they need the human's leave in `feature.md`.

## Interface

`operator/vm/setup.sh` (the operator's VM script), three lines:

- The `tools` step's hint ends with `(docs/operator-guide/machine.md, "The rebuild after a merge")` in place of `(operator guide, "The rebuild after a merge")`. The `service` step's hint ends the same way. Both stay on stderr (`>&2`).
- The last line reads `setup: done: build the stage image and start factory@<instance>; see "The machine" in docs/operator-guide/machine.md`.

`operator/skill/kumpel/references/approving.md`, *After a merge*: "on a VM the operator guide's rebuild" becomes "on a VM the rebuild of `docs/operator-guide/machine.md`, *The rebuild after a merge*".

The tests that pin the old texts change only their expected strings, with the leave the human gives in `feature.md`:

- `tests/vm/test_vm_setup_install_hint.py` (`HINTS`)
- `tests/vm/test_vm_setup_text.py`, the row `done-line`

New test module: `tests/guards/test_operator_guide_pointers_search.py` (criterion 3).

## Acceptance criteria

1. Each of the two differing-file hints (rows `tools` and `service`) ends with `(docs/operator-guide/machine.md, "The rebuild after a merge")`, appears exactly once in its step, and goes to stderr. No line of `operator/vm/setup.sh` holds `(operator guide, `.
2. The closing line of `operator/vm/setup.sh` is printed as `setup: done: build the stage image and start factory@%s; see "The machine" in docs/operator-guide/machine.md`. No line of the script holds `see the operator guide, `.
3. No line of a file under `operator/vm/` or `operator/skill/` that says `operator guide` lacks a path under `docs/operator-guide/` on the same line. Rows:
   - The files as they are after the story give an empty list.
   - The made-up line `see the operator guide, "The machine"` is caught.
   - The made-up line `see "The machine" in docs/operator-guide/machine.md` is not caught.
   - The made-up line `the operator guide (docs/operator-guide/README.md)` is not caught.
   - Every `docs/operator-guide/<name>.md` that such a line names exists.
4. `make check` stays green.
5. docs: `docs/operator-guide/machine.md` quotes the three new lines word for word, where it now quotes the old ones (lines 284, 295 and 296). The project guide's `operator.md`: none, because the script's layout does not change. `README.md` and `docs/decisions.md`: none, because no decision changes.

## Smoke test

```bash
grep -c 'docs/operator-guide/machine.md, "The rebuild after a merge")' operator/vm/setup.sh
```
Expect: `2`

```bash
grep -c 'operator guide, "' operator/vm/setup.sh
```
Expect: `0`

```bash
grep -c 'docs/operator-guide/machine.md' operator/skill/kumpel/references/approving.md
```
Expect: `1`

```bash
uv run pytest tests/vm/test_vm_setup_install_hint.py tests/guards/test_operator_guide_pointers_search.py 2>&1 | tail -1 | grep -c passed
```
Expect: `1`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: 1. The story changes two tests that other stories wrote: `tests/vm/test_vm_setup_install_hint.py` (`HINTS`) and `tests/vm/test_vm_setup_text.py` (row `done-line`). Its Description and Interface say the human's leave in `feature.md` is needed. `feature.md`'s *The human's changes* has no such leave for S0015. It has one for S0014 only, and decision 5 covers only the modules a move story moves. Without the leave, the tester cannot change those expected strings. Options: (a) you add to `feature.md` a line "At S0015's start: a leave for its tester: `tests/vm/test_vm_setup_install_hint.py` (`HINTS`) and `tests/vm/test_vm_setup_text.py` (row `done-line`) may change their expected strings to the new texts, nothing else; each test keeps its name and what it checks"; or (b) you answer here that this entry is the leave. I would choose (a). Everything else checks out; I am asking only about this. Interface: concrete files and exact lines. Criteria: testable, each rule has a failing-side row, including the made-up line that is caught. Smoke test: runnable, and `Expect:` lines are checkable. The pytest command correctly passes no `-q`, because `addopts` already sets it. Architecture and scope: fit, and the left-out items are named.
4. 2026-11-05 human: Answer of the human:

   **(a).** `feature.md` on `main` now has your line under *The human's changes*: "At S0015's start: a leave for its tester: `tests/vm/test_vm_setup_install_hint.py` (`HINTS`) and `tests/vm/test_vm_setup_text.py` (row `done-line`) may change their expected strings to the new texts, nothing else; each test keeps its name and what it checks." Go on.
5. factory: started intake as vm.
6. intake: accepted
   Interface: names concrete files and exact lines (`operator/vm/setup.sh` tools and service hints, the closing line, `approving.md` *After a merge*), and the two tests that change with the exact files, `HINTS` and row `done-line`.
   Criteria: each is testable by one test function. Every rule has a failing side. The old hint and the old done-line must be absent, and criterion 3 has a row where the made-up line is caught and rows where it is not caught. The leave for the two tests that other stories wrote is now in `feature.md`, under *The human's changes*, "At S0015's start". It comes from the human's answer in journal entry 4, so the story needed no edit.
   Smoke test: the four commands are runnable. Every `Expect:` is a count or a "passed" match that the output can be checked against. The pytest command passes no `-q`, because `addopts` already sets it.
   Architecture: the change touches the operator's VM script, the skill reference and one guard test, and no `src/factory` layer. The tests go in `tests/guards/`, which is where `CLAUDE.md` puts them.
   Scope: within F0051, where S0015 is listed. The left-out items (`wiring.py` docstring, the playbook, the demo README, the Makefile example) are named in the Description.
7. factory: started tests as vm.
