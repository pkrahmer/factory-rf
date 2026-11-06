---
stage: docs-review
blocked: null
round: 1
attempts: 1
crashes: 0
pull_request: 580
comments_read: []
handed_over: null
claim:
  instance: vm
  stage: docs-review
  started_at: '2026-11-06T01:11:44.039583Z'
  lease_duration: 60
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-06T01:04:23.755626Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-06T01:04:23.762263Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-06T01:04:39.265523Z'
  stage: intake
  run: 77da8bd4626f4feab22947f9ebb9f5f1
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-06T01:04:44.431481Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-06T01:07:26.449545Z'
  stage: docs-only
  run: 72aaf13cd7104c129d4150af504c851a
- number: 6
  speaker: factory
  kind: stall
  at: '2026-11-06T01:07:26.607096Z'
  stage: docs-only
  run: 72aaf13cd7104c129d4150af504c851a
  reason: check_red
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-06T01:07:33.823330Z'
  stage: docs-only
- number: 8
  speaker: documenter
  kind: result
  at: '2026-11-06T01:10:21.971090Z'
  stage: docs-only
  run: 922bcf2cba2142b694824d32a953cf4b
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-06T01:10:27.291030Z'
  stage: docs-review
- number: 10
  speaker: reviewer
  kind: result
  at: '2026-11-06T01:11:13.931470Z'
  stage: docs-review
  run: d9b944b8a72d411b9acd389d28f9e4da
- number: 11
  speaker: factory
  kind: started
  at: '2026-11-06T01:11:20.240803Z'
  stage: docs-only
- number: 12
  speaker: documenter
  kind: result
  at: '2026-11-06T01:11:39.035056Z'
  stage: docs-only
  run: 7246e4c871d146449d233f1781bd13da
- number: 13
  speaker: factory
  kind: started
  at: '2026-11-06T01:11:44.039583Z'
  stage: docs-review
---

# The project guide names the headings a check still requires

## Description

`docs/project-guide/README.md`, *The files*, says that the guard `tests/guards/test_project_guide_files.py` requires every page to be named in that section and every area to have its page, "and that headings are free". That is true of the two guide guards since their heading tables went, but not of the guides as a whole. The guard finds the index's pages under the heading `## The files` itself, so renaming it leaves every page unnamed. The document check (`make documents`, `factory.shared.domain.documents`) requires the sections *Kill points* and *Fault-injection paths* in this index, *Install* and *Configuration* in `docs/operator-guide/install.md` and *The stops* in `docs/operator-guide/stops.md`. It also exempts a section *Replaced from v1* from its search for v1 words. And `operator/vm/setup.sh` points to *The machine* and *The rebuild after a merge* in `docs/operator-guide/machine.md`, a file the documenter may not change. A documenter of the next feature's rewrite who trusts "headings are free" renames one of them, and the check or a dangling pointer sends the story off the docs route. This story makes the sentence say which headings stay. It changes only that section; the code and the checks stay as they are.

## Interface

- `docs/project-guide/README.md`, `## The files`: the sentence on the guard keeps its first half, and "headings are free" becomes: headings are free except these, which keep their names: `## The files` in this index (the guard reads it); *Kill points* and *Fault-injection paths* in this index, *Install* and *Configuration* in `docs/operator-guide/install.md` and *The stops* in `docs/operator-guide/stops.md` (the document check requires them); *Replaced from v1* wherever it stands, which may be removed but not renamed (the document check exempts it from its search for v1 words, and the style page's rules 1 and 7 ask for its removal in the rewrite); and *The machine* and *The rebuild after a merge* in `docs/operator-guide/machine.md` (`operator/vm/setup.sh` names them). The wording and the form are the documenter's, by the style page; a list is allowed.
- No code and no test changes.

## Acceptance criteria

1. `docs/project-guide/README.md`, *The files*, names each of the nine headings of the Interface together with the file it stands in, or with "wherever it stands" for *Replaced from v1* together with "may be removed but not renamed", and the reason it keeps its name: the guard, the document check or the script.
2. The section no longer says that headings are free without these exceptions.
3. Every heading the section names exists today in the file it names: `## The files` and `## Kill points` and `## Fault-injection paths` in `docs/project-guide/README.md`, `## Install` and `## Configuration` in `docs/operator-guide/install.md`, `## The stops` in `docs/operator-guide/stops.md`, and the two headings of `machine.md`.
4. `make documents` prints `documents ok`.
5. `make check` stays green.
6. docs: `docs/project-guide/README.md`, *The files*, as above. `docs/decisions.md`: none, since nothing is decided. `docs/operator-guide/`: none, because the operator does not run the guards.

## Smoke test

```bash
sed -n '/^## The files/,/^## /p' docs/project-guide/README.md | grep -c "Kill points\|Fault-injection paths\|Configuration\|The stops\|Replaced from v1\|The rebuild after a merge"
```
Expect: a number of at least `1`; the section names the headings it keeps.

```bash
make documents 2>&1 | tail -1
```
Expect: `documents ok`

## Journal

1. 2026-11-06 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names one document, `docs/project-guide/README.md` (*The files*, the sentence at line 15 that says "headings are free"), with the nine headings and their files spelled out; no code, no test. The documenter may write it.
   - Criteria: criterion 1 (nine headings, each with its file and reason), criterion 2 (the unqualified "headings are free" is gone), criterion 3 (each named heading exists today; I checked the eight present ones, and *Replaced from v1* has no section now, which the story allows with "wherever it stands" and "may be removed") and criterion 4 (`make documents` prints `documents ok`) are each testable by one check. This is a failing-side rule: criterion 2 covers the old wording being removed. Criterion 5 and the `docs:` criterion close the list.
   - Smoke test: both commands run as written. `make documents` is not pytest, so the `-q` rule does not apply. Each `Expect:` can be checked (a count of at least 1; `documents ok`). The first Expect is weak, since it counts matching lines and not all nine headings, but it is checkable.
   - Architecture: documents only, no layer or area is touched.
   - Scope: within F0052's goal (the docs route and the guide's rewrite). It is the proposed S0007 from the acceptance, and it is not in "Out of scope". Route: docs-only, because the only path the Interface changes is `docs/project-guide/README.md`.
4. factory: started docs-only as vm.
5. documenter: Changed `docs/project-guide/README.md`, *The files*: the sentence "headings are free" now says headings are free except nine that keep their names, as a list with the file and the reason for each. They are `## The files` (the guard), *Kill points* and *Fault-injection paths* here, *Install* and *Configuration* in `install.md` and *The stops* in `stops.md` (the document check), *Replaced from v1* wherever it stands (may be removed, not renamed; the document check exempts it), and *The machine* and *The rebuild after a merge* in `machine.md` (`operator/vm/setup.sh`). I checked that the headings exist: `## The files`, `## Kill points`, `## Fault-injection paths`, `## Install`, `## Configuration`, `## The stops` and `## The machine` are `##` headings, and *The rebuild after a merge* is a `###` heading at line 570 of `machine.md`. *Replaced from v1* has no section in the index, which the story allows; `agents.md` does list one under its sections. `make documents` printed `documents ok`. I did not run `make check`, because I changed only a document. Cross-read: the rest of the index's *The files* section, which is unchanged and consistent with the new text. Stale text I noticed that is not mine to fix: none. No Rejected line was needed, because no `decisions.md` entry was written.
6. factory: Stage docs-only stalled (attempt 1 of 2): a check is red after the stage: `check`
   src/factory/watching/application/transcripts.py         61      2     10      0    97%   91-92
   src/factory/watching/domain/board.py                    55      0      4      1    98%   77->75
   src/factory/watching/domain/machine.py                  52      3     18      5    89%   44->42, 47, 59, 77->75, 79
   src/factory/watching/domain/transcripts.py              10      2      0      0    80%   20-21
   src/factory/work/application/acceptance_reading.py     132      1     46      1    99%   239
   src/factory/work/application/work_items.py              90      2     24      2    96%   133, 169
   src/factory/work/domain/acceptance.py                  195      1     52      1    99%   367
   ------------------------------------------------------------------------------------------------
   TOTAL                                                10651     49   2128     46    99%

   154 files skipped due to complete coverage.
   Required test coverage of 90.0% reached. Total coverage: 99.26%
   ======================================================================================= short test summary info ========================================================================================
   FAILED tests/guards/test_project_guide_files.py::test_the_guide_holds_the_index_and_its_named_files - AssertionError: assert ['missing: ## The files'] == []
   make: *** [Makefile:89: test] Error 1
7. factory: started docs-only as vm.
8. documenter: documenter, round 0, second run after the red check in entry 6.

   Changed `docs/project-guide/README.md`, *The files*. The first run's list put `## The files` in backticks at the start of a list item. The guard `tests/guards/test_project_guide_files.py` reads such a line (`- `…` text.`) as an index entry naming a page called "## The files". It then reported that page as missing, which was the red check (`missing: ## The files`). The item now starts with the words "The heading" and the backticked name follows. The other eight headings and their reasons are unchanged from the first run.

   Checks: `uv run pytest -q tests/guards/test_project_guide_files.py` passes, and `make documents` prints `documents ok`. I did not run the whole `make check`; the factory runs it after this stage, and only a document changed.

   Cross-read: the rest of *The files* (the page entries). It is consistent with the new text. Heading existence was checked in the first run.

   Stale text noticed but not touched: none. One thing for the reviewer: a list item in *The files* that starts with a backticked name followed by a sentence is read by the guard as a page entry. The guide does not say so, and this story keeps to its Interface and does not add that.

   No Rejected line was needed; no `decisions.md` entry was written.

   `check`: check: green
   `secrets`: secrets: green (0.4 s)
   `documents`: documents ok
9. factory: started docs-review as vm.
10. reviewer: Reviewed `git diff main...HEAD -- README.md docs operator/README.md`. It changes only `docs/project-guide/README.md`, *The files*. I checked the facts against the code and the writing against `docs/project-guide/style.md`.

    Facts, all true on the branch:
    - `factory.shared.domain.documents` requires *Install*, *Configuration* and *The stops* (`OPERATOR_GUIDE_SECTIONS`) and *Kill points* and *Fault-injection paths* (`PROJECT_GUIDE_SECTIONS`). It exempts *Replaced from v1* (`REPLACED_SECTION`).
    - `tests/support/guide_files_support.py` finds the page entries by the literal line `## The files`.
    - `operator/vm/setup.sh` names "The rebuild after a merge" in two messages (lines 405 and 453) and "The machine" in one (line 476).
    - All eight headings that exist today are where the text puts them. `machine.md` has `## The machine` and `### The rebuild after a merge`. *Replaced from v1* is covered by "wherever it stands".
    - Criteria 1 and 2 are met: all nine headings are named, each with its file and its reason, and the unqualified "headings are free" is gone. Criterion 3 is met. Criterion 4 is met: entry 8 shows `documents ok` and `check: green`.

    Findings:
    1. `docs/project-guide/README.md`, *The files*: the new list of headings that keep their names comes straight before the existing list of pages, with only a blank line between them. Both use `-`. In CommonMark that makes them one list, so the page entries render as more items of the exceptions list, and the page list loses its lead-in. Fix: put one lead-in sentence between the two lists, for example "The pages:" or "The folder holds these pages:". The guard still reads the page entries, because a line that does not start with "- `" is not an index entry for the guard (`INDEX_LINE` in `tests/support/guide_files_support.py`).

    Points I considered and did not raise:
    - Style rule 8 (link a file by a relative link): the new text names `install.md`, `stops.md`, `machine.md` and `setup.sh` as code paths, not links. The rest of the index has no links either, so the diff follows the page's own form.
    - Sentence length: the longest new sentence, in the second bullet, is about 25 words, which is within rule 2.
11. factory: started docs-only as vm.
12. documenter: Round 1, fixing the reviewer's finding 1. Changed `docs/project-guide/README.md`, *The files*: I added the lead-in sentence "The folder holds these pages:" between the list of headings that keep their names and the list of pages. Without it the two `-` lists rendered as one. The guard still reads the page entries, since the lead-in is not an index entry line. Checks: `uv run pytest -q tests/guards/test_project_guide_files.py` passes and `make documents` prints `documents ok`. I did not run `make check`, because I changed only a document. Cross-read: the rest of *The files*, which is unchanged and consistent. Stale text noticed but not touched: none. No Rejected line was needed, because no `decisions.md` entry was written.

    `check`: check: green (not run again: passed on tree 2503ea5b3c55 at 2026-11-06T01:07:59Z)
    `secrets`: secrets: green (0.4 s)
    `documents`: documents ok
13. factory: started docs-review as vm.
