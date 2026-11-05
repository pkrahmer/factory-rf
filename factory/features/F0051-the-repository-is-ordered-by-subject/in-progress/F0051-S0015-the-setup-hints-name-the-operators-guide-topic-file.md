---
stage: doing
blocked: null
round: 0
attempts: 0
crashes: 0
pull_request: 570
comments_read: [6656020506, 6656185279]
handed_over: null
claim: null
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
- number: 8
  speaker: tester
  kind: result
  at: '2026-11-05T10:49:20.547304Z'
  stage: tests
  run: 219d88d9942b409599def49137913349
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T10:49:25.780323Z'
  stage: doing
- number: 10
  speaker: coder
  kind: question
  at: '2026-11-05T10:50:08.832030Z'
  stage: doing
  run: 0f952c42fa85402484c6a8d4175b66a9
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-05T10:56:03.472408Z'
  stage: doing
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T10:56:06.034047Z'
  stage: doing
- number: 13
  speaker: coder
  kind: result
  at: '2026-11-05T10:58:35.242606Z'
  stage: doing
  run: 48e5280b462d4c52a03e0fbaaede925d
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-05T10:58:40.878516Z'
  stage: tests
- number: 15
  speaker: tester
  kind: result
  at: '2026-11-05T10:59:06.329599Z'
  stage: tests
  run: 2737d5bc6cbe42c8b5cb8a0d3fb9d216
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
8. tester: Tests written from the Interface and the criteria. The two earlier tests changed only their expected strings, under the human's leave in `feature.md` ("At S0015's start", journal entry 4).

   criterion 1: tests/vm/test_vm_setup_install_hint.py::test_a_differing_installed_file_names_the_operators_own_copy (rows `tools`, `service`; `HINTS` now ends with `(docs/operator-guide/machine.md, "The rebuild after a merge")`). It checks the hint appears once in its step and goes to stderr. The absence of `(operator guide, ` is tests/guards/test_operator_guide_pointers_search.py::test_the_setup_script_holds_no_old_pointer[(operator guide, ]
   criterion 2: tests/guards/test_operator_guide_pointers_search.py::test_the_closing_line_names_the_machine_topic_file (the one `setup: done: ` line is exactly the new `printf ... "$instance"`), plus test_the_setup_script_holds_no_old_pointer[see the operator guide, ], plus tests/vm/test_vm_setup_text.py::test_the_refusals_modes_and_rerun_guards_are_in_their_steps[done-line] (its expected string is now `see "The machine" in docs/operator-guide/machine.md`)
   criterion 3, files as they are after the story: tests/guards/test_operator_guide_pointers_search.py::test_every_mention_of_the_operator_guide_names_its_path
   criterion 3, made-up lines (caught / topic file not caught / index file not caught): tests/guards/test_operator_guide_pointers_search.py::test_a_mention_without_a_path_is_caught (rows `no-path`, `topic-file`, `index-file`)
   criterion 3, every named file exists: tests/guards/test_operator_guide_pointers_search.py::test_every_named_topic_file_exists
   criterion 4 (`make check`) and criterion 5 (docs): no test, as usual.

   How the search works: it reads every UTF-8 text file under `operator/vm/` and `operator/skill/`, and the match is case-sensitive on `operator guide`. A line counts as having a path when it contains `docs/operator-guide/`. The existence check reads `docs/operator-guide/<name>.md` from those lines and needs at least one such name.

   Files created: tests/guards/test_operator_guide_pointers_search.py. Earlier test files changed under the leave: tests/vm/test_vm_setup_install_hint.py (`HINTS`) and tests/vm/test_vm_setup_text.py (row `done-line`).

   One run of `uv run pytest -q` over the three files: the new texts are missing from `operator/vm/setup.sh` and `approving.md`, so the tests fail with wrong results. There were no collection errors, and every module imported (the tests read only text files). The last five lines showed the old-pointer, closing-line, `tools`/`service` hint and `done-line` failures. `make lint`: green.

   `lint`: lint: green (0.2 s)
9. factory: started doing as vm.
10. coder: I changed the four lines exactly as the Interface gives them, but `make check` is red because of two faults in the new test `tests/guards/test_operator_guide_pointers_search.py`. I may not edit tests, so this is a question.

    Built (in the working tree):
    - `operator/vm/setup.sh`:
      - lines 405 and 453: each hint now ends with `(docs/operator-guide/machine.md, "The rebuild after a merge")` and still goes to stderr.
      - line 476: `see "The machine" in docs/operator-guide/machine.md`.
    - `operator/skill/kumpel/references/approving.md:25`: "on a VM the rebuild of `docs/operator-guide/machine.md`, *The rebuild after a merge*".

    Passing: `tests/vm/test_vm_setup_install_hint.py`, `tests/vm/test_vm_setup_text.py`, and every test in the new module except one.

    The two faults:
    1. `test_every_named_topic_file_exists` asserts `named != set()`. It collects topic-file names only from lines that contain `operator guide`. None of the Interface's new texts contains `operator guide`, and after the change no line under `operator/vm/` or `operator/skill/` does (`grep -rn "operator guide" operator/vm operator/skill` prints nothing). So the set is always empty, and the test fails against the texts the Interface prescribes. The failure: `tests/guards/test_operator_guide_pointers_search.py:64: E assert set() != set()`. Criterion 3's last row ("every `docs/operator-guide/<name>.md` that such a line names exists") holds trivially when no such line exists; the criterion does not ask for at least one.
    2. `make types` fails on the same file: `tests/guards/test_operator_guide_pointers_search.py:24: error: Need type annotation for "found" [var-annotated]`. `make check` stops there.

    Options:
    - (a) The tester fixes the test (my choice):
      - collect names from every searched line that holds `docs/operator-guide/` (the new lines all do, so the set is not empty), or drop the `named != set()` assertion;
      - annotate `found: list[tuple[Path, str]] = []`.
    - (b) Change the Interface so the new texts keep the words "operator guide" (for example `(operator guide docs/operator-guide/machine.md, ...)`). I would not do this: it changes the wording the human approved.

    With (a), I would go on with no code change and end with `tests`.

    Main choice: I copied the Interface's texts as given, with no other wording. Not touched: the docs (`docs/operator-guide/machine.md` lines 284, 295 and 296) belong to the docs stage. No refactor was needed.
11. 2026-11-05 human: Answer of the human:

    **(a).** Leave for the tester, in its own new test `tests/guards/test_operator_guide_pointers_search.py`: collect the topic-file names from every searched line that holds `docs/operator-guide/` (keep the `named != set()` assertion, so the test cannot pass vacuously), and annotate `found: list[tuple[Path, str]] = []`. The Interface's texts stay as approved. Then end with `tests`.
12. factory: started doing as vm.
13. coder: The human's answer (entry 11, option (a)) asks for a test change. I changed no code. The tester should make this change in `tests/guards/test_operator_guide_pointers_search.py`:
    - `test_every_named_topic_file_exists` collects the topic-file names from every searched line under `operator/vm/` and `operator/skill/` that holds `docs/operator-guide/`, not only from lines that say `operator guide`. It keeps the `named != set()` assertion.
    - The list on line 24 gets an annotation: `found: list[tuple[Path, str]] = []`.

    State on the branch: the four texts from the Interface are already committed. They are in `operator/vm/setup.sh` (the `tools` and `service` hints and the `setup: done:` line) and in `operator/skill/kumpel/references/approving.md`.

    `make test` this round: every test passed except `test_every_named_topic_file_exists`. It failed at `tests/guards/test_operator_guide_pointers_search.py:64: E assert set() != set()`. That is the fault the human's answer addresses. After the tester's change, the doing stage should only need to run `make check`. The docs criterion (`docs/operator-guide/machine.md`, lines 284, 295 and 296) is the docs stage's work, and I did not touch it.
14. factory: started tests as vm.
15. tester: I made the test change the human approved in entry 11 (option (a)), which the coder passed on in entry 13. Both edits are in `tests/guards/test_operator_guide_pointers_search.py`, a test this story wrote:
    - `test_every_named_topic_file_exists` now collects topic-file names from every searched line under `operator/vm/` and `operator/skill/` that holds `docs/operator-guide/<name>.md`. Before, it looked only at lines that also say `operator guide`. None of the Interface's new texts say `operator guide`, so the set was always empty. I kept the `named != set()` assertion, so the test cannot pass when no file is named. A line counts if the `TOPIC_FILE` pattern matches it, which only happens when the line holds `docs/operator-guide/`.
    - `_searched_lines` now declares `found: list[tuple[Path, str]] = []`, which fixes the `var-annotated` error that `make types` reported.

    The test names and what each one checks stay the same. The mapping from criteria to tests is unchanged from entry 8.

    Files changed: tests/guards/test_operator_guide_pointers_search.py. No files created. Every module imported.

    I ran `uv run pytest -q tests/guards/test_operator_guide_pointers_search.py` once: all 8 tests passed. `make lint`: green (0.1 s). I did not run the type check in this stage; the coder's `make check` covers it.

    `lint`: lint: green (0.1 s)
