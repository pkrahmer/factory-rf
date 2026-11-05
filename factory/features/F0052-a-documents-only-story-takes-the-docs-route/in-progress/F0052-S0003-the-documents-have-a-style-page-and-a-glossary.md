---
stage: review
blocked: question
round: 0
attempts: 1
crashes: 0
pull_request: 574
comments_read: [6671915202]
handed_over: null
claim: null
journal:
- number: 1
  speaker: human
  kind: created
  at: '2026-11-05T23:01:53.344731Z'
  stage: intake
- number: 2
  speaker: factory
  kind: started
  at: '2026-11-05T23:01:53.351464Z'
  stage: intake
- number: 3
  speaker: intake
  kind: result
  at: '2026-11-05T23:02:10.005208Z'
  stage: intake
  run: 4faa5f9a78d545808b9ecdeb60ad8887
- number: 4
  speaker: factory
  kind: started
  at: '2026-11-05T23:02:14.880601Z'
  stage: docs-only
- number: 5
  speaker: documenter
  kind: result
  at: '2026-11-05T23:05:41.551287Z'
  stage: docs-only
  run: ee04e77905884528ac7e9d5eb6c8c563
- number: 6
  speaker: factory
  kind: stall
  at: '2026-11-05T23:05:41.715767Z'
  stage: docs-only
  run: ee04e77905884528ac7e9d5eb6c8c563
  reason: check_red
- number: 7
  speaker: factory
  kind: started
  at: '2026-11-05T23:05:49.149810Z'
  stage: docs-only
- number: 8
  speaker: documenter
  kind: result
  at: '2026-11-05T23:06:09.347516Z'
  stage: docs-only
  run: 1fdc345f7d3847e19fe8c05af69ec58c
- number: 9
  speaker: factory
  kind: started
  at: '2026-11-05T23:06:14.952388Z'
  stage: tests
- number: 10
  speaker: tester
  kind: question
  at: '2026-11-05T23:06:48.521870Z'
  stage: tests
  run: b49421db46c74097b301e016c52e2b1e
  blocked: question
- number: 11
  speaker: human
  kind: comment
  at: '2026-11-05T23:10:40.903257Z'
  stage: tests
- number: 12
  speaker: factory
  kind: started
  at: '2026-11-05T23:10:43.942868Z'
  stage: tests
- number: 13
  speaker: tester
  kind: result
  at: '2026-11-05T23:11:12.784336Z'
  stage: tests
  run: 14e25114c0ed422e8f780409ee9415b1
- number: 14
  speaker: factory
  kind: started
  at: '2026-11-05T23:11:18.336304Z'
  stage: doing
- number: 15
  speaker: coder
  kind: result
  at: '2026-11-05T23:16:34.738773Z'
  stage: doing
  run: d7de45b2c6cf4d218accf48a4f0dca12
- number: 16
  speaker: factory
  kind: started
  at: '2026-11-05T23:16:40.079968Z'
  stage: review
- number: 17
  speaker: reviewer
  kind: question
  at: '2026-11-05T23:18:22.453798Z'
  stage: review
  run: a3940524d522498b90687b953693d325
  blocked: question
---

# The documents have a style page and a glossary

## Description

The documenter and the reviewer need one written standard for how the documents read. The human chose it on 2026-11-05 (`planning/doc-style-drafts.md`, with samples in `planning/doc-style-samples.md`): seven rules for every document, numbered steps for the operator guide, "idea first, then the API" for the project guide, and "what it is for, then try it" for the README. This story writes that standard into the repository as `docs/project-guide/style.md`, and the glossary that its third rule needs as `docs/project-guide/glossary.md`: each word the factory gives its own meaning, explained once in plain words. The project guide's index names both. It is the first story on the docs route, and it rewrites no other document.

## Interface

- `docs/project-guide/style.md` (new): the seven rules for all documents; a section per document (operator guide, project guide, README) with its reader, its rules and one example in the chosen style; as in `planning/doc-style-drafts.md`, in the page's own words. One more rule for all documents (the human, 2026-11-05): a file of the repository is linked by a relative link, such as `[process.py](../../src/factory/shared/adapters/process.py)`, never by a GitHub URL and never to a line (`#L42`); a code block holds no links, so the file it shows is linked once above it.
- `docs/project-guide/glossary.md` (new): one entry per factory word, at least: work item, feature, story, acceptance, stage, role, journal, backlog, approval, pipeline definition, write paths, project command, dataset, base, take, stage environment, stall, stop, crash, lease, claim, round, round cap, attempts cap, cost record, instance, tick. Each entry is one to three plain sentences, sorted alphabetically.
- `docs/project-guide/README.md`, *The files*: one line each for `style.md` and `glossary.md`.
- No code, no test, no agent file changes.

## Acceptance criteria

1. `docs/project-guide/style.md` holds the seven common rules, the rule on relative links to files and the three document sections, each with its reader, its rules and an example.
2. `docs/project-guide/glossary.md` holds an entry for every word the Interface lists, alphabetically, each of at most three sentences.
3. `docs/project-guide/README.md` names both files in *The files*.
4. The two new pages follow their own rules: no feature or story ID, no version history, no sentence of more than about 25 words (the reviewer judges).
5. `make documents` prints `documents ok`.
6. `make check` stays green.
7. docs: as criteria 1 to 3. `README.md` and the operator guide: none; their rewrite is the next feature. `docs/decisions.md`: an entry for the choice of style, naming the human's choice of 2026-11-05.

## Smoke test

```bash
test -f docs/project-guide/style.md && test -f docs/project-guide/glossary.md && echo both
```
Expect: `both`

```bash
grep -c "style.md\|glossary.md" docs/project-guide/README.md | awk '{print ($1 >= 2) ? "named" : "missing"}'
```
Expect: `named`

## Journal

1. 2026-11-05 human: created.
2. factory: started intake as vm.
3. intake: accepted
   - Interface: names concrete paths only (`docs/project-guide/style.md` and `glossary.md` new, the `README.md` index lines); no code, so no signatures are needed. The glossary lists the required words, sorted alphabetically. The source drafts exist in `planning/`.
   - Criteria: each is checkable by reading the files or running a command. 1 covers the seven rules, the relative-link rule and the three sections with reader, rules and example. 2 covers the entries, alphabetical order and the three-sentence limit. 3 covers the index. 4 covers the pages' own rules (the reviewer judges length). 5 and 6 are commands. 7 is the docs criterion. The relative-link rule has its criterion in 1.
   - Smoke test: both commands are runnable (`test -f`, `grep -c` piped to awk), and each Expect line (`both`, `named`) is exact. No pytest is involved.
   - Architecture: every changed path is a document under `docs/`, which the documenter may write. Nothing outside the doc areas is touched, and `planning/` is only read.
   - Scope: within the feature's S0003 scope. The rewrite of the guides and the README stays out, as the feature requires.
   Route: docs-only, because every path the Interface changes is one the documenter may write.
4. factory: started docs-only as vm.
5. documenter: Wrote the style page and the glossary, and added both to the project guide's index. `make documents` prints `documents ok`. I did not run `make check`, because I changed only documents.

   Files changed:
   - `docs/project-guide/style.md` (new): rules 1 to 7 from `planning/doc-style-drafts.md`, in the page's own words. Rule 8 is the human's rule on relative links, with no GitHub URLs, no `#L42` and one link above a code block. Then one section each for the operator guide, the project guide and the README, with reader, rules and the chosen example. The take example's closing "See also" now links `pipeline.md`, so the example follows rule 8.
   - `docs/project-guide/glossary.md` (new): 27 entries, sorted alphabetically, one to two sentences each. They cover every word the Interface lists, plus `feature`, `story` and `role`, which it names too. Wording of `stall`, `crash`, `lease`, `claim`, `stop` and `cost record` follows `docs/operator-guide/stops.md` and the decision log.
   - `docs/project-guide/README.md`: one line each for `style.md` and `glossary.md` in *The files*, ahead of `shared.md`.
   - `docs/decisions.md`: a new last entry, "The documents follow one style page and one glossary", naming the human's choice of 2026-11-05. The story names no rejected option for it, so the entry has no "Rejected" line.

   Cross-read and found current for this story: `docs/project-guide/README.md` (index structure and the *The files* format) and the last entry of `docs/decisions.md`. I did not cross-read the other area files or the operator guide. Per the story, no other document is rewritten.

   Open for the reviewer:
   - The drafts in `planning/doc-style-drafts.md` have rules 8 to 10 (facts from the code, keep the detail in a *Reference* section, examples run and show where). The story asks for seven common rules plus the link rule, so I left those three out. Say if they should go in.
   - I did not measure sentence length by tool. I wrote to about 25 words.

   Stale text seen, not touched: the header comments of `factory/pipeline.yml` and some older `docs/decisions.md` entries use version names (v1, v1.1). Those are outside this story's paths and, for the pipeline definition, outside my write paths.
6. factory: Stage docs-only stalled (attempt 1 of 2): a check is red after the stage: `check`
   src/factory/watching/application/transcripts.py         61      2     10      0    97%   91-92
   src/factory/watching/domain/board.py                    55      0      4      1    98%   77->75
   src/factory/watching/domain/machine.py                  52      3     18      5    89%   44->42, 47, 59, 77->75, 79
   src/factory/watching/domain/transcripts.py              10      2      0      0    80%   20-21
   src/factory/work/application/acceptance_reading.py     132      1     46      1    99%   239
   src/factory/work/application/work_items.py              90      2     24      2    96%   133, 169
   src/factory/work/domain/acceptance.py                  186      1     46      1    99%   356
   ------------------------------------------------------------------------------------------------
   TOTAL                                                10644     49   2122     46    99%

   154 files skipped due to complete coverage.
   Required test coverage of 90.0% reached. Total coverage: 99.26%
   ======================================================================================= short test summary info ========================================================================================
   FAILED tests/guards/test_project_guide_files.py::test_the_guide_holds_the_index_operator_and_the_seven_area_files - AssertionError: assert ['README.md',...ator.md', ...] == ['README.md',...line.md'...
   make: *** [Makefile:89: test] Error 1
7. factory: started docs-only as vm.
8. documenter: The story needs one test change, so I end with `tests`. The documents from the first round stay as they are; I changed nothing this round.

   Why: the first docs round made `make check` red. The guard `tests/guards/test_project_guide_files.py::test_the_guide_holds_the_index_operator_and_the_seven_area_files` (line 214) compares the exact file list of `docs/project-guide/` with `README.md`, `operator.md` and the seven area files. The story asks for two new files there, `style.md` and `glossary.md`, so that guard must fail until it is changed.

   Change for the tester:
   - In that test, the expected list becomes `sorted(("README.md", *NAMED_FILES, "style.md", "glossary.md"))`. Define `("style.md", "glossary.md")` as a new constant next to `NAMED_FILES`; the tuple name is the tester's choice.
   - Keep `NAMED_FILES` as it is, with `style.md` and `glossary.md` out of it. `test_the_index_names_each_file_with_a_sentence` expects each name in `NAMED_FILES` to open an index line of the form ``- `name` ... .``. My two new index lines already have that form, so adding them to `NAMED_FILES` would also do. In that case the test's name and the first test's expected list follow from it.
   - Check that no other test in `tests/guards/test_project_guide_files.py` fails because of the two new files. I did not run the guard again, because I changed no file this round.

   Files changed in the first docs round (journal entry 5), still in the working tree: `docs/project-guide/style.md` (new), `docs/project-guide/glossary.md` (new), `docs/project-guide/README.md` (two index lines) and `docs/decisions.md` (a last entry, with no "Rejected" line because the story names none).

   Open from entry 5: the drafts' rules 8 to 10 are left out, since the story asks for seven rules plus the link rule. Sentence length was not measured by tool.

   Stale text noticed, not mine to fix: version names in the header comments of `factory/pipeline.yml` and in older `docs/decisions.md` entries.
9. factory: started tests as vm.
10. tester: I stopped before writing any test. I need the human's word on two points.

    1. An existing guard must change, and I may not change it without your leave. `tests/guards/test_project_guide_files.py::test_the_guide_holds_the_index_operator_and_the_seven_area_files` (written by F0051's stories) expects `docs/project-guide/` to hold exactly `README.md`, `operator.md` and the seven area files. With `style.md` and `glossary.md` there, it fails and keeps `make check` red. This is a change to another story's test, not a move of a shared helper, so the standing leave does not cover it. The prompt did not give me the approved-change mode either. Options:
       - (a) Add `"style.md", "glossary.md"` to `NAMED_FILES`. The existing `test_the_index_names_each_file_with_a_sentence` then also checks both index lines, which is criterion 3. Rename the first test to `test_the_guide_holds_the_index_and_its_named_files` so its name stays true.
       - (b) What the documenter proposed: keep `NAMED_FILES` and add a new constant `GUIDE_PAGES = ("style.md", "glossary.md")`. The expected list becomes `sorted(("README.md", *NAMED_FILES, *GUIDE_PAGES))`, and the test keeps its now inaccurate name.
       - My choice: (a).

    2. Should the tests stage write tests for this story at all? The Interface says "No code, no test, no agent file changes", but my role writes one test per criterion. Options:
       - (i) No new tests. Criteria 1 to 4 are judged by the reviewer, and 5 and 6 are factory checks. The only test work is the guard change in point 1.
       - (ii) A new `tests/guards/test_style_and_glossary.py` with these checks:
         - the glossary has a `- **word**:` entry for each of the 27 listed words;
         - its entries are sorted;
         - each entry has one to three sentences (a parametrized test with rows at 1, 3 and a refused 4);
         - `style.md` has a numbered list of eight rules under "Rules for all documents";
         - `style.md` has the sections "The operator guide", "The project guide" and "The README".
         This fixes formats the story leaves open, such as the entry markup, the rule numbering, the section names, and what counts as a sentence. That is why I am asking and not choosing.
       - My choice: (i), with change (a) from point 1, because the Interface rules out tests.

    Files created: none. The test run was not started, so no module failed to import. No other open points.
11. 2026-11-05 human: 1. (a), with the human's leave: the tester adds `"style.md", "glossary.md"` to `NAMED_FILES` in `tests/guards/test_project_guide_files.py` and renames the first test to `test_the_guide_holds_the_index_and_its_named_files`. The index test then checks both index lines.

    2. (i): no new tests. The Interface rules out tests, and the formats of the style page and the glossary stay the documenter's to choose. The guard change of point 1 is the only test work. The reviewer judges criteria 1 to 4, and `make documents` and `make secrets` cover 5 and 6.
12. factory: started tests as vm.
13. tester: I made the one test change the human approved in entry 11: option (a) for point 1 and option (i) for point 2.

    Changed (an earlier story's test, with the human's leave in entry 11):
    - `tests/guards/test_project_guide_files.py`: `NAMED_FILES` is now `(*AREA_FILES, "operator.md", "style.md", "glossary.md")`.
    - In the same file, `test_the_guide_holds_the_index_operator_and_the_seven_area_files` is renamed to `test_the_guide_holds_the_index_and_its_named_files`. Its check is unchanged: the guide folder holds exactly `README.md` and the named files.
    - Because of this change, `test_the_index_names_each_file_with_a_sentence` now also checks the index lines for `style.md` and `glossary.md`.

    Criterion → test:
    - criterion 3: `tests/guards/test_project_guide_files.py::test_the_index_names_each_file_with_a_sentence` (the `style.md` and `glossary.md` rows) and `::test_the_guide_holds_the_index_and_its_named_files`.
    - criteria 1, 2 and 4: no test, by the human's answer (i). The reviewer judges them, and the formats stay the documenter's to choose.
    - criteria 5 and 6: no test. The factory's checks (`make documents`, `make check`) cover them.

    Files created: none. Every module was imported; nothing failed to import.

    Results:
    - `uv run pytest -q tests/guards/test_project_guide_files.py`: all pass. These tests are not red, because the documents are already on the branch.
    - `make lint`: green.

    Nothing is left for the coder to implement: the documents are in place, so `make check` should be green with this change. I did not run `make check` myself.

    `lint`: lint: green (0.1 s)
14. factory: started doing as vm.
15. coder: I built nothing, because there was nothing to build. The story is documents only, and its Interface rules out code, tests and agent file changes. The documenter wrote the documents in entry 5: `docs/project-guide/style.md`, `docs/project-guide/glossary.md`, the two index lines in `docs/project-guide/README.md` and the last entry in `docs/decisions.md`. The tester changed the guard in `tests/guards/test_project_guide_files.py` in entry 13, with the human's leave in entry 11. All of these are already on the branch. My working tree was clean at the start (`git status --short` printed nothing), and I changed no file.

    Main choice: I changed no code and only confirmed the branch is green. `make check` ends with `test: green (140.8 s)` and `check: green`, at 99.26 % coverage. I rejected touching the documents or adding code: the documents are the documenter's to write, and the Interface says no code. Refactor step: there is no diff of mine to refactor.

    The journal did not change what the task means. Entry 11 settled only the guard change and that no new tests are written, so the Description stays as it is.

    Seen but not touched:
    - The open points from entries 5 and 8 are still for the reviewer to decide. The drafts' rules 8 to 10 were left out of the style page, and no tool measured sentence length.
    - The pipeline definition's header comments and older decision-log entries still use version names.

    `check`: check: green
    `duplicates`: duplicates: 5 new, 40 known, 3 gone
16. factory: started review as vm.
17. reviewer: Review, round 0. I reviewed `git diff main...HEAD -- . ':!factory'` and the work item. The diff has the two new pages, the two index lines, the decision-log entry and the guard change. I checked the facts against the code: `TakeService.take`'s signature, `Snapshots.changed_paths`, `operator/vm/setup.sh`'s flags, `FACTORY_INSTANCE`, the stall reasons, and the `StageEnvironment` operations. I also compared the pages with `planning/doc-style-drafts.md`.

    What holds:
    - The glossary has all 27 words, sorted, each in one or two sentences.
    - `style.md` has the seven rules, the link rule and the three sections, each with its reader, its rules and an example.
    - I found no feature or story ID and no version name in either page.
    - The documenter left out the drafts' rules 8 to 10 because the Interface asks for seven rules plus the link rule. I agree.
    - The factory's `make check` after the coder was green (entry 15).

    Findings:
    1. `docs/project-guide/glossary.md`, entries `stall` and `attempts cap`: both say a stall is an agent run that ends without a result. A stall also follows a finished run when the decision is not allowed, the form fails, a check is red or a merge conflicts (`StallReason`; `pipeline.md` *Stalls*; this story's entry 6 is a `check_red` stall). Fix: define a stall as a stage that ends without a result the factory can keep, whether the run ended early or its decision, form, checks or merge failed. Define the attempts cap as how many stalls a stage may have before the factory asks.
    2. `docs/project-guide/glossary.md`, entry `journal`: "Each stage and each human answer adds one" leaves out the factory's own entries (started, stall, crash). Fix: say the factory, each stage's agent and the human add entries.
    3. `docs/project-guide/style.md`, the example in *The project guide*: the code block shows `TakeService`'s signature, but no module is named and no relative link sits above the block. That breaks the section's own rule ("the module, the class and its main function") and rule 8 (criteria 1 and 4). Fix: above the block, add one line that links `[take.py](../../src/factory/pipeline/application/take.py)` and names `factory.pipeline.application.take`.
    4. `docs/project-guide/style.md`, *The operator guide*, first paragraph and second bullet: the glossary words "instance" and "stop" are used without a link at first use. That breaks the page's own rule 3 (criterion 4). Fix: link each word to `glossary.md` where it first appears.
    5. `docs/decisions.md`, the new entry's Decision line: one sentence of about 45 words with three parentheses. That breaks rule 2 of the style the entry adopts. Fix: split it into short sentences, one per document, without parentheses.

    Earlier tests:
    - `tests/guards/test_project_guide_files.py`: changed under the human's leave in journal entry 11 (option (a)). The change matches that answer and nothing more: `NAMED_FILES` gains `style.md` and `glossary.md`, and one test is renamed.

    Question: every finding is in `docs/`, and only the documenter may write there (`factory/pipeline.yml`, roles). The coder may not, so `doing` sends the findings to a stage that cannot fix them. Options:
    - (a) I end with `doing`. The coder can only pass or ask again, so the story loses a stage.
    - (b) I end with `docs`, and the documenter fixes findings 1 to 5 there before the smoke test.
    - (c) You fix the five points by hand on the branch, and I pass.

    I would choose (b): it puts the findings in front of the only role that may write them.
